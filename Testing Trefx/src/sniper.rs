use std::sync::Arc;
use std::str::FromStr;

use log::{error, info, warn};
use solana_client::{
    nonblocking::rpc_client::RpcClient,
    rpc_config::RpcTransactionLogsConfig,
};
use solana_sdk::{
    commitment_config::CommitmentConfig,
    pubkey::Pubkey,
    signature::{Keypair, Signer},
};
use tokio::sync::mpsc;
use tokio_stream::wrappers::ReceiverStream;
use tokio_stream::StreamExt;

use crate::config::Config;
use crate::risk_management::RiskManager;
use crate::telegram::TelegramBot;
use crate::utils;

pub struct Sniper {
    config: Arc<Config>,
    rpc_client: Arc<RpcClient>,
    wallet: Arc<Keypair>,
    telegram_bot: Arc<TelegramBot>,
    risk_manager: RiskManager,
}

impl Sniper {
    pub async fn new(config: Arc<Config>, telegram_bot: Arc<TelegramBot>) -> Result<Self, Box<dyn std::error::Error>> {
        // Initialize RPC client
        let rpc_client = Arc::new(RpcClient::new_with_commitment(
            config.solana_rpc_url.clone(),
            CommitmentConfig::confirmed(),
        ));

        // Load wallet
        let wallet = utils::load_keypair_from_env()?;

        // Initialize risk manager
        let risk_manager = RiskManager::new(config.clone(), rpc_client.clone());

        Ok(Self {
            config,
            rpc_client,
            wallet: Arc::new(wallet),
            telegram_bot,
            risk_manager,
        })
    }

    pub async fn start(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        info!("Starting sniper...");
        
        // Subscribe to Raydium program logs
        let (tx, rx) = mpsc::channel(100);
        let stream = ReceiverStream::new(rx);

        // Subscribe to AMM program
        let rpc_client_amm = self.rpc_client.clone();
        let amm_program_id = self.config.raydium_amm_program_id;
        let tx_amm = tx.clone();
        tokio::spawn(async move {
            if let Err(e) = Self::monitor_program_logs(rpc_client_amm, amm_program_id, tx_amm, "AMM").await {
                error!("AMM monitor error: {}", e);
            }
        });

        // Subscribe to CLMM program
        let rpc_client_clmm = self.rpc_client.clone();
        let clmm_program_id = self.config.raydium_clmm_program_id;
        let tx_clmm = tx.clone();
        tokio::spawn(async move {
            if let Err(e) = Self::monitor_program_logs(rpc_client_clmm, clmm_program_id, tx_clmm, "CLMM").await {
                error!("CLMM monitor error: {}", e);
            }
        });

        // Process detected events
        let mut stream = stream;
        while let Some((program_type, log_response)) = stream.next().await {
            if let Err(e) = self.process_logs(program_type, log_response).await {
                error!("Error processing logs: {}", e);
                self.telegram_bot.send_error_alert(&format!("Error processing logs: {}", e)).await?;
            }
        }

        Ok(())
    }

    async fn monitor_program_logs(
        rpc_client: Arc<RpcClient>,
        program_id: Pubkey,
        tx: mpsc::Sender<(String, solana_client::rpc_response::RpcLogsResponse)>,
        program_type: &'static str,
    ) -> Result<(), Box<dyn std::error::Error>> {
        let config = RpcTransactionLogsConfig {
            commitment: Some(CommitmentConfig::confirmed()),
        };
        
        let mut subscription = rpc_client
            .logs_subscribe(
                solana_client::rpc_filter::RpcFilterType::Mentions(vec![program_id.to_string()]),
                config,
            )
            .await?;
        
        info!("Subscribed to {} program logs: {}", program_type, program_id);
        
        while let Some(log_response) = subscription.next().await {
            if let Err(e) = tx.send((program_type.to_string(), log_response)).await {
                error!("Error sending log response: {}", e);
                break;
            }
        }
        
        Ok(())
    }

    async fn process_logs(
        &self,
        program_type: String,
        log_response: solana_client::rpc_response::RpcLogsResponse,
    ) -> Result<(), Box<dyn std::error::Error>> {
        let signature = log_response.signature;
        info!("Processing transaction: {}", signature);
        
        // Get full transaction details
        let tx = self.rpc_client
            .get_transaction(&signature, solana_client::rpc_config::RpcTransactionConfig::default())
            .await?;
        
        // Check if transaction was successful
        if let Some(err) = tx.transaction.meta.as_ref().and_then(|m| m.err.as_ref()) {
            warn!("Transaction failed: {:?}", err);
            return Ok(());
        }
        
        // Parse transaction based on program type
        match program_type.as_str() {
            "AMM" => self.handle_amm_transaction(tx).await,
            "CLMM" => self.handle_clmm_transaction(tx).await,
            _ => Ok(()),
        }
    }

    async fn handle_amm_transaction(
        &self,
        tx: solana_client::rpc_response::RpcTransactionResponse,
    ) -> Result<(), Box<dyn std::error::Error>> {
        // Look for initialize2 instruction (byte 33) in Raydium AMM program
        for instruction in &tx.transaction.message.instructions {
            if let Some(program_id) = tx.transaction.message.account_keys.get(instruction.program_id_index as usize) {
                if program_id.to_string() == self.config.raydium_amm_program_id.to_string() {
                    if let Some(first_byte) = instruction.data.first() {
                        if *first_byte == 33 { // initialize2 instruction
                            info!("Detected AMM pool creation: {}", tx.signature);
                            
                            // Extract pool information
                            let pool_state = tx.transaction.message.account_keys[instruction.accounts[4] as usize];
                            let base_mint = tx.transaction.message.account_keys[instruction.accounts[8] as usize];
                            let quote_mint = tx.transaction.message.account_keys[instruction.accounts[9] as usize];
                            
                            // Process the new pool
                            self.process_new_pool("AMM", base_mint, pool_state, &tx.signature).await?;
                        }
                    }
                }
            }
        }
        
        Ok(())
    }

    async fn handle_clmm_transaction(
        &self,
        tx: solana_client::rpc_response::RpcTransactionResponse,
    ) -> Result<(), Box<dyn std::error::Error>> {
        // Look for open_position instruction in Raydium CLMM program
        for instruction in &tx.transaction.message.instructions {
            if let Some(program_id) = tx.transaction.message.account_keys.get(instruction.program_id_index as usize) {
                if program_id.to_string() == self.config.raydium_clmm_program_id.to_string() {
                    if let Some(first_byte) = instruction.data.first() {
                        if *first_byte == 4 { // open_position instruction
                            info!("Detected CLMM pool activity: {}", tx.signature);
                            
                            // Extract token information
                            let token_mint_a = tx.transaction.message.account_keys[instruction.accounts[8] as usize];
                            
                            // Check if this is a new token
                            if self.risk_manager.is_new_token(&token_mint_a.to_string()).await? {
                                info!("Detected new CLMM token: {}", token_mint_a);
                                self.process_new_pool("CLMM", token_mint_a, Pubkey::default(), &tx.signature).await?;
                            }
                        }
                    }
                }
            }
        }
        
        Ok(())
    }

    async fn process_new_pool(
        &self,
        pool_type: &str,
        token_mint: Pubkey,
        pool_state: Pubkey,
        tx_signature: &str,
    ) -> Result<(), Box<dyn std::error::Error>> {
        // Get token info
        let token_info = self.risk_manager.get_token_info(&token_mint.to_string()).await?;
        
        // Perform risk assessment
        let risk_assessment = self.risk_manager.assess_token_risk(&token_mint.to_string()).await?;
        
        if !risk_assessment.is_safe {
            warn!("Token {} failed risk assessment: {}", token_mint, risk_assessment.reason);
            self.telegram_bot.send_message(&format!("❌ Token {} failed risk assessment: {}", token_mint, risk_assessment.reason)).await?;
            return Ok(());
        }
        
        // Send Telegram alert
        self.telegram_bot.send_snipe_alert(
            &token_info.name.unwrap_or_else(|| "Unknown".to_string()),
            &token_mint.to_string(),
            pool_type,
            risk_assessment.liquidity,
        ).await?;
        
        // Execute trade if conditions are met
        if risk_assessment.liquidity >= self.config.min_liquidity_sol {
            info!("Executing trade for token: {}", token_mint);
            self.execute_trade(&token_mint.to_string(), risk_assessment.liquidity).await?;
        }
        
        Ok(())
    }

    async fn execute_trade(&self, token_mint: &str, liquidity: f64) -> Result<(), Box<dyn std::error::Error>> {
        // Get quote from Jupiter
        let quote = utils::get_jupiter_quote(
            "So11111111111111111111111111111111111111112", // SOL
            token_mint,
            10000000, // 0.01 SOL
            self.config.sniper_slippage_bps,
            &self.config.jupiter_api_url,
        ).await?;
        
        // Simulate transaction if enabled
        if self.config.simulate_transactions {
            let simulation_result = self.risk_manager.simulate_trade(&quote).await?;
            if !simulation_result.success {
                warn!("Trade simulation failed: {:?}", simulation_result.error);
                self.telegram_bot.send_message(&format!("❌ Trade simulation failed: {:?}", simulation_result.error)).await?;
                return Ok(());
            }
        }
        
        // Execute trade
        let swap_result = utils::execute_jupiter_swap(
            &quote,
            &self.wallet,
            self.config.sniper_priority_fee_micro_lamports,
            &self.rpc_client,
        ).await?;
        
        // Send confirmation
        self.telegram_bot.send_trade_confirmation(
            token_mint,
            quote.in_amount as f64 / 1_000_000_000.0, // Convert lamports to SOL
            quote.out_amount as f64 / quote.in_amount as f64, // Price per token
            &swap_result.signature,
        ).await?;
        
        Ok(())
    }
}
