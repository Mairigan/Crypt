use std::env;

use log::{error, info};
use solana_client::{
    nonblocking::rpc_client::RpcClient,
    rpc_config::RpcTransactionConfig,
};
use solana_sdk::{
    signature::{Keypair, Signer},
    transaction::Transaction,
};
use backoff::{future::retry, ExponentialBackoff};

pub fn load_keypair_from_env() -> Result<Keypair, Box<dyn std::error::Error>> {
    let keypair_str = env::var("WALLET_PRIVATE_KEY")?;
    let keypair_bytes: Vec<u8> = serde_json::from_str(&keypair_str)?;
    Ok(Keypair::from_bytes(&keypair_bytes)?)
}

pub async fn get_jupiter_quote(
    input_mint: &str,
    output_mint: &str,
    amount: u64,
    slippage_bps: u64,
    jupiter_api_url: &str,
) -> Result<serde_json::Value, Box<dyn std::error::Error>> {
    let url = format!(
        "{}/quote?inputMint={}&outputMint={}&amount={}&slippageBps={}",
        jupiter_api_url, input_mint, output_mint, amount, slippage_bps
    );
    
    let operation = || async {
        let response = reqwest::get(&url).await?;
        if !response.status().is_success() {
            return Err(backoff::Error::transient(
                std::io::Error::new(
                    std::io::ErrorKind::Other,
                    format!("HTTP error: {}", response.status())
                )
            ));
        }
        
        let quote = response.json::<serde_json::Value>().await?;
        Ok(quote)
    };
    
    retry(ExponentialBackoff::default(), operation).await
}

pub async fn execute_jupiter_swap(
    quote: &serde_json::Value,
    wallet: &Keypair,
    priority_fee_micro_lamports: u64,
    rpc_client: &RpcClient,
) -> Result<SwapResult, Box<dyn std::error::Error>> {
    let client = reqwest::Client::new();
    let payload = serde_json::json!({
        "quoteResponse": quote,
        "userPublicKey": wallet.pubkey().to_string(),
        "wrapAndUnwrapSol": true,
        "priorityFeeMicroLamports": priority_fee_micro_lamports,
    });
    
    let operation = || async {
        let response = client
            .post("https://quote-api.jup.ag/v6/swap")
            .json(&payload)
            .send()
            .await?;
        
        if !response.status().is_success() {
            return Err(backoff::Error::transient(
                std::io::Error::new(
                    std::io::ErrorKind::Other,
                    format!("HTTP error: {}", response.status())
                )
            ));
        }
        
        let swap_response = response.json::<serde_json::Value>().await?;
        let swap_transaction: Transaction = serde_json::from_value(swap_response["swapTransaction"].clone())?;
        
        // Sign the transaction
        let signed_transaction = wallet.sign_transaction(&swap_transaction);
        
        // Send the transaction
        let signature = rpc_client
            .send_and_confirm_transaction(&signed_transaction)
            .await?;
        
        Ok(SwapResult {
            signature: signature.to_string(),
            success: true,
        })
    };
    
    retry(ExponentialBackoff::default(), operation).await
}

#[derive(Debug)]
pub struct SwapResult {
    pub signature: String,
    pub success: bool,
}
