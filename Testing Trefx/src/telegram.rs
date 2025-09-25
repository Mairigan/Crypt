use log::{error, info};
use request;
use serde_json::json;
use std::sync::Arc;

use crate::config::Config;

pub struct TelegramBot {
    bot_token: String,
    chat_id: String,
    client: request::Client,
}

impl TelegramBot {
    pub fn new(bot_token: &str, chat_id: &str) -> Self {
        Self {
            bot_token: bot_token.to_string(),
            chat_id: chat_id.to_string(),
            client: request::Client::new(),
        }
    }

    pub async fn send_message(&self, text: &str) -> Result<(), Box<dyn std::error::Error>> {
        let url = format!("https://api.telegram.org/bot{}/sendMessage", self.bot_token);
        
        let response = self.client
            .post(&url)
            .json(&json!({
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "HTML"
            }))
            .send()
            .await?;
        
        if !response.status().is_success() {
            let error_text = response.text().await?;
            error!("Failed to send Telegram message: {}", error_text);
            return Err(Box::new(std::io::Error::new(
                std::io::ErrorKind::Other,
                format!("Telegram API error: {}", error_text)
            )));
        }
        
        info!("Telegram message sent: {}", text);
        Ok(())
    }

    pub async fn send_snipe_alert(
        &self, 
        token_name: &str, 
        token_address: &str, 
        pool_type: &str,
        liquidity: f64
    ) -> Result<(), Box<dyn std::error::Error>> {
        let message = format!(
            "🚀 <b>New Pool Detected!</b>\n\n\
            💎 <b>Token:</b> {}\n\
            🔗 <b>Address:</b> <code>{}</code>\n\
            📊 <b>Pool Type:</b> {}\n\
            💧 <b>Liquidity:</b> {:.2} SOL\n\n\
            <a href=\"https://dexscreener.com/solana/{}\">View on DexScreener</a>",
            token_name, token_address, pool_type, liquidity, token_address
        );
        
        self.send_message(&message).await
    }

    pub async fn send_trade_confirmation(
        &self,
        token_address: &str,
        amount: f64,
        price: f64,
        tx_signature: &str
    ) -> Result<(), Box<dyn std::error::Error>> {
        let message = format!(
            "✅ <b>Trade Executed!</b>\n\n\
            🔗 <b>Token:</b> <code>{}</code>\n\
            💰 <b>Amount:</b> {:.2} SOL\n\
            📈 <b>Price:</b> {:.8} SOL\n\n\
            <a href=\"https://solscan.io/tx/{}\">View Transaction</a>\n\
            <a href=\"https://dexscreener.com/solana/{}\">View on DexScreener</a>",
            token_address, amount, price, tx_signature, token_address
        );
        
        self.send_message(&message).await
    }

    pub async fn send_error_alert(&self, error: &str) -> Result<(), Box<dyn std::error::Error>> {
        let message = format!("❌ <b>Error:</b>\n<code>{}</code>", error);
        self.send_message(&message).await
    }
}
