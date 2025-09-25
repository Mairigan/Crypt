import asyncio
import base64
import base58
from solana.rpc.async_api import AsyncClient
from solana.rpc.websocket_api import connect
from solana.rpc.commitment import Commitment
from solana.transaction import Transaction
from solana.publickey import PublicKey
from solana.rpc.types import Signature
from solders.rpc.config import RpcTransactionLogsFilterMode
from solana.rpc.types import TxOpts
from solana.keypair import Keypair
from config.settings import SOLANA_RPC_HTTP_URL, SOLANA_RPC_WS_URL
from utils.security import security_manager

class SolanaClient:
    def __init__(self):
        self.http_client = AsyncClient(SOLANA_RPC_HTTP_URL)
        self.ws_client = None
        self.keypair = self._load_wallet()
        
    def _load_wallet(self):
        """Load wallet from encrypted private key."""
        from config.settings import WALLET_PRIVATE_KEY
        
        if not WALLET_PRIVATE_KEY:
            raise ValueError("Wallet private key not found in environment variables")
        
        try:
            # Decrypt the private key
            decrypted_key = security_manager.decrypt_data(WALLET_PRIVATE_KEY)
            
            # Decode base58 private key
            private_key_bytes = base58.b58decode(decrypted_key)
            return Keypair.from_bytes(private_key_bytes)
        except Exception as e:
            raise ValueError(f"Failed to load wallet: {e}")
    
    async def get_balance(self):
        """Get the wallet balance."""
        try:
            balance = await self.http_client.get_balance(self.keypair.pubkey(), Commitment("confirmed"))
            return balance.value / 10**9  # Convert lamports to SOL
        except Exception as e:
            print(f"Error getting balance: {e}")
            return 0
    
    async def get_token_balance(self, mint_address):
        """Get the balance of a specific token."""
        try:
            # This would need to find the associated token account
            # Implementation depends on your specific needs
            pass
        except Exception as e:
            print(f"Error getting token balance: {e}")
            return 0
    
    async def get_transaction(self, signature):
        """Get transaction details by signature."""
        try:
            transaction = await self.http_client.get_transaction(
                Signature.from_string(signature),
                encoding="json",
                commitment=Commitment("confirmed")
            )
            return transaction.value
        except Exception as e:
            print(f"Error getting transaction: {e}")
            return None
    
    async def send_transaction(self, transaction, max_retries=3):
        """Send a transaction with retry logic."""
        for attempt in range(max_retries):
            try:
                # Sign the transaction
                transaction.sign(self.keypair)
                
                # Send the transaction
                opts = TxOpts(skip_preflight=False, preflight_commitment=Commitment("confirmed"))
                result = await self.http_client.send_transaction(transaction, opts=opts)
                
                if result.value:
                    return result.value
                
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(1)  # Wait before retrying
        
        return None
    
    async def monitor_logs(self, program_id, callback):
        """Monitor logs for a specific program."""
        program_pubkey = PublicKey(program_id)
        
        try:
            async with connect(SOLANA_RPC_WS_URL) as websocket:
                await websocket.logs_subscribe(
                    program_pubkey,
                    commitment=Commitment("confirmed"),
                    filter_=RpcTransactionLogsFilterMode.All
                )
                
                first_resp = await websocket.recv()
                subscription_id = first_resp.result
                
                async for response in websocket:
                    if response.result and hasattr(response.result, 'value'):
                        logs = response.result.value.logs
                        signature = response.result.value.signature
                        await callback(logs, signature)
                        
        except Exception as e:
            print(f"Error monitoring logs: {e}")
            # Reconnect after a delay
            await asyncio.sleep(5)
            await self.monitor_logs(program_id, callback)
    
    async def close(self):
        """Close the HTTP client."""
        await self.http_client.close()

# Global instance
solana_client = SolanaClient()
