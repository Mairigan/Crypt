import asyncio
import base64
import time
import aiohttp
# from solders.pubkey import Pubkey  # Removed unused import
from solana.transaction import Transaction
from config.settings import (
    RAYDIUM_AMM_PROGRAM_ID, 
    RAYDIUM_CLMM_PROGRAM_ID, 
    PUMP_FUN_PROGRAM_ID,
    SNIPE_TIMEOUT,
    MAX_SLIPPAGE,
    CHECK_RUG,
    MAX_BUY_AMOUNT
)
from bot.solana_client import solana_client
from services.jupiter_service import jupiter_service
from utils.log_parser import log_parser
from utils.token_analyzer import token_analyzer
from utils.transaction_simulator import transaction_simulator

class SniperBot:
    def __init__(self):
        self.auto_snipe_enabled = False
        self.monitored_tokens = {}
        self.pending_snipes = {}
        
    async def get_status(self):
        """Get bot status information."""
        balance = await solana_client.get_balance()
        status = f"""
        🤖 *Bot Status* 🤖
        
        *Wallet Balance:* {balance:.4f} SOL
        *Auto Snipe:* {'Enabled' if self.auto_snipe_enabled else 'Disabled'}
        *Monitored Tokens:* {len(self.monitored_tokens)}
        *Pending Snipes:* {len(self.pending_snipes)}
        *RPC Connection:* Active
        *Telegram Connection:* Active
        
        Use /help for available commands.
        """
        return status
    
    async def get_balance(self):
        """Get wallet balance."""
        balance = await solana_client.get_balance()
        return f"{balance:.4f} SOL"
    
    async def manual_snipe(self, mint_address, update):
        """Manually snipe a token."""
        try:
            # Get quote from Jupiter
            amount_lamports = int(MAX_BUY_AMOUNT * 10**9)  # Convert SOL to lamports
            quote = await jupiter_service.get_quote(
                "So11111111111111111111111111111111111111112",  # SOL mint
                mint_address,
                amount_lamports,
                int(MAX_SLIPPAGE * 10000)  # Convert to basis points
            )
            
            if not quote:
                await update.message.reply_text("Failed to get quote for this token.")
                return
            
            # Get swap transaction
            swap_transaction = await jupiter_service.get_swap_transaction(
                quote,
                str(solana_client.keypair.pubkey())
            )
            
            if not swap_transaction or 'swapTransaction' not in swap_transaction:
                await update.message.reply_text("Failed to create swap transaction.")
                return
            
            # Decode and send transaction
            transaction_data = base64.b64decode(swap_transaction['swapTransaction'])
            transaction = Transaction.deserialize(transaction_data)
            
            # Simulate transaction first
            simulation = await transaction_simulator.simulate_transaction(transaction)
            if not simulation["success"]:
                await update.message.reply_text(f"❌ Simulation failed: {simulation['error']}")
                return
            
            # Execute the transaction
            result = await solana_client.send_transaction(transaction)
            
            if result:
                signature = result
                explorer_url = f"https://solscan.io/tx/{signature}"
                await update.message.reply_text(
                    f"✅ Successfully sniped {mint_address[:8]}...!\n"
                    f"Transaction: {explorer_url}"
                )
            else:
                await update.message.reply_text("❌ Failed to execute swap transaction.")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error during snipe: {str(e)}")
    
    async def monitor_token(self, mint_address, update):
        """Monitor a token's price."""
        if mint_address in self.monitored_tokens:
            await update.message.reply_text(f"Already monitoring {mint_address[:8]}...")
            return
        
        self.monitored_tokens[mint_address] = {
            "last_price": 0,
            "start_time": time.time(),
            "chat_id": update.effective_chat.id
        }
        
        await update.message.reply_text(f"Started monitoring {mint_address[:8]}...")
        
        # Start monitoring in background
        asyncio.create_task(self._monitor_token_price(mint_address))
    
    async def _monitor_token_price(self, mint_address):
        """Background task to monitor token price."""
        try:
            while mint_address in self.monitored_tokens:
                # Get price from Jupiter
                url = f"https://price.jup.ag/v4/price?ids={mint_address}"
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            if mint_address in data.get('data', {}):
                                price = data['data'][mint_address]['price']
                                
                                # Check if price has changed significantly
                                monitor_data = self.monitored_tokens[mint_address]
                                if monitor_data['last_price'] > 0 and abs(price - monitor_data['last_price']) / max(monitor_data['last_price'], 1e-9) > 0.05:  # 5% change
                                    message = (
                                        f"📈 Price Alert!\n"
                                        f"Token: {mint_address[:8]}...\n"
                                        f"Price: ${price:.8f}\n"
                                        f"Change: {((price - monitor_data['last_price']) / max(monitor_data['last_price'], 1e-9) * 100):.2f}%"
                                    )
                                    
                                    # This would need access to the telegram bot instance
                                    # await self.telegram_bot.send_message(
                                    #     monitor_data['chat_id'],
                                    #     message
                                    # )
                                    print(message)  # For now, just print
                                
                                monitor_data['last_price'] = price
                        
                        await asyncio.sleep(10)  # Check every 10 seconds
                
        except Exception as e:
            print(f"Error monitoring token {mint_address}: {e}")
            if mint_address in self.monitored_tokens:
                del self.monitored_tokens[mint_address]
    
    async def _handle_amm_pool_creation(self, logs, signature):
        """Handle AMM pool creation events."""
        if not self.auto_snipe_enabled:
            return
        
        try:
            # Parse logs
            log_data = log_parser.parse_raydium_amm_logs(logs, signature)
            
            if log_data.get("mint_address") and log_data.get("action") == "pool_creation":
                mint_address = log_data["mint_address"]
                
                # Check if we're already processing this mint
                if mint_address in self.pending_snipes:
                    return
                
                # Add to pending snipes
                self.pending_snipes[mint_address] = {
                    "discovered_at": time.time(),
                    "signature": signature,
                    "program": "raydium_amm"
                }
                
                # Analyze token
                analysis = await token_analyzer.analyze_token(mint_address)
                
                if analysis["is_valid"] and not analysis["is_rug"]:
                    # This is where we would auto-snipe
                    print(f"✅ Valid token found: {mint_address}")
                    # await self.auto_snipe(mint_address, analysis)
                else:
                    print(f"❌ Skipping token {mint_address}: {analysis['warnings']}")
                    del self.pending_snipes[mint_address]
                        
        except Exception as e:
            print(f"Error handling AMM pool creation: {e}")
    
    async def auto_snipe(self, mint_address, analysis):
        """Execute an auto-snipe for a token."""
        try:
            # Similar to manual_snipe but with auto parameters
            amount_lamports = int(MAX_BUY_AMOUNT * 10**9)
            quote = await jupiter_service.get_quote(
                "So11111111111111111111111111111111111111112",
                mint_address,
                amount_lamports,
                int(MAX_SLIPPAGE * 10000)
            )
            
            if not quote:
                print(f"Failed to get quote for {mint_address}")
                return
            
            swap_transaction = await jupiter_service.get_swap_transaction(
                quote,
                str(solana_client.keypair.pubkey())
            )
            
            if not swap_transaction or 'swapTransaction' not in swap_transaction:
                print(f"Failed to create swap transaction for {mint_address}")
                return
            
            transaction_data = base64.b64decode(swap_transaction['swapTransaction'])
            transaction = Transaction.deserialize(transaction_data)
            
            # Simulate transaction first
            simulation = await transaction_simulator.simulate_transaction(transaction)
            if not simulation["success"]:
                print(f"Simulation failed for {mint_address}: {simulation['error']}")
                return
            
            # Execute the transaction
            result = await solana_client.send_transaction(transaction)
            
            if result:
                signature = result
                print(f"✅ Auto-sniped {mint_address[:8]}...! Tx: {signature}")
                # Send Telegram notification
                # await self.telegram_bot.send_message(
                #     TELEGRAM_ADMIN_ID,
                #     f"✅ Auto-sniped {mint_address[:8]}...!\nTx: https://solscan.io/tx/{signature}"
                # )
            else:
                print(f"❌ Failed to execute auto-snipe for {mint_address}")
                
        except Exception as e:
            print(f"❌ Error during auto-snipe: {str(e)}")
        finally:
            # Remove from pending snipes
            if mint_address in self.pending_snipes:
                del self.pending_snipes[mint_address]
    
    async def start_monitoring(self):
        """Start monitoring for new pools."""
        # Monitor Raydium AMM
        asyncio.create_task(
            solana_client.monitor_logs(
                RAYDIUM_AMM_PROGRAM_ID,
                self._handle_amm_pool_creation
            )
        )
        
        # Could add monitoring for other programs here
        # (CLMM, Pump.fun, etc.)
    
    async def close(self):
        """Cleanup resources."""
        await solana_client.close()

# Global instance
sniper_bot = SniperBot()
