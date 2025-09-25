use std::env;

use config::{Config as ConfigBuilder, File, FileFormat};
use serde::Deserialize;
use solana_sdk::pubkey::Pubkey;

#[derive(Debug, Deserialize, Clone)]
pub struct Config {
    // RPC Configuration
    pub solana_rpc_url: String,
    pub solana_wss_url: String,
    
    // Wallet Configuration
    pub wallet_private_key: String,
    
    // Telegram Configuration
    pub telegram_bot_token: String,
    pub telegram_chat_id: String,
    
    // Sniper Configuration
    pub sniper_slippage_bps: u64,
    pub sniper_max_retries: u32,
    pub sniper_priority_fee_micro_lamports: u64,
    
    // Risk Management
    pub max_slippage_bps: u64,
    pub min_liquidity_sol: f64,
    pub check_honeypot: bool,
    pub simulate_transactions: bool,
    
    // Program IDs
    pub raydium_amm_program_id: Pubkey,
    pub raydium_clmm_program_id: Pubkey,
    
    // API URLs
    pub jupiter_api_url: String,
    pub dex_screener_api_url: String,
}

impl Config {
    pub fn load() -> Result<Self, config::ConfigError> {
        let mut builder = ConfigBuilder::builder();
        
        // Load environment variables
        builder = builder.set_default("solana_rpc_url", "https://api.mainnet-beta.solana.com")?;
        builder = builder.set_default("solana_wss_url", "wss://api.mainnet-beta.solana.com")?;
        builder = builder.set_default("sniper_slippage_bps", 500)?;
        builder = builder.set_default("sniper_max_retries", 3)?;
        builder = builder.set_default("sniper_priority_fee_micro_lamports", 1000000)?;
        builder = builder.set_default("max_slippage_bps", 1000)?;
        builder = builder.set_default("min_liquidity_sol", 5.0)?;
        builder = builder.set_default("check_honeypot", true)?;
        builder = builder.set_default("simulate_transactions", true)?;
        builder = builder.set_default("raydium_amm_program_id", "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8")?;
        builder = builder.set_default("raydium_clmm_program_id", "CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK")?;
        builder = builder.set_default("jupiter_api_url", "https://quote-api.jup.ag/v6")?;
        builder = builder.set_default("dex_screener_api_url", "https://api.dexscreener.com/latest/dex")?;
        
        // Load from environment variables
        builder = builder.add_source(config::Environment::with_prefix("SNIPER"));
        
        // Load from config file
        builder = builder.add_source(File::with_name("config.toml").format(FileFormat::Toml).required(false));
        
        let config = builder.build()?;
        
        Ok(Config {
            solana_rpc_url: config.get_string("solana_rpc_url")?,
            solana_wss_url: config.get_string("solana_wss_url")?,
            wallet_private_key: env::var("WALLET_PRIVATE_KEY").map_err(|_| config::ConfigError::NotFound("WALLET_PRIVATE_KEY".to_string()))?,
            telegram_bot_token: env::var("TELEGRAM_BOT_TOKEN").map_err(|_| config::ConfigError::NotFound("TELEGRAM_BOT_TOKEN".to_string()))?,
            telegram_chat_id: env::var("TELEGRAM_CHAT_ID").map_err(|_| config::ConfigError::NotFound("TELEGRAM_CHAT_ID".to_string()))?,
            sniper_slippage_bps: config.get_int("sniper_slippage_bps")? as u64,
            sniper_max_retries: config.get_int("sniper_max_retries")? as u32,
            sniper_priority_fee_micro_lamports: config.get_int("sniper_priority_fee_micro_lamports")? as u64,
            max_slippage_bps: config.get_int("max_slippage_bps")? as u64,
            min_liquidity_sol: config.get_float("min_liquidity_sol")? as f64,
            check_honeypot: config.get_bool("check_honeypot")?,
            simulate_transactions: config.get_bool("simulate_transactions")?,
            raydium_amm_program_id: Pubkey::from_str(&config.get_string("raydium_amm_program_id")?).map_err(|_| config::ConfigError::Message("Invalid raydium_amm_program_id".to_string()))?,
            raydium_clmm_program_id: Pubkey::from_str(&config.get_string("raydium_clmm_program_id")?).map_err(|_| config::ConfigError::Message("Invalid raydium_clmm_program_id".to_string()))?,
            jupiter_api_url: config.get_string("jupiter_api_url")?,
            dex_screener_api_url: config.get_string("dex_screener_api_url")?,
        })
    }
}

