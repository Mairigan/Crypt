import aiohttp
import base64
import json
from config.settings import JUPITER_API_URL

class JupiterService:
    def __init__(self):
        self.base_url = JUPITER_API_URL
    
    async def get_quote(self, input_mint: str, output_mint: str, amount: int, slippage_bps: int) -> dict:
        """Get a quote from Jupiter API"""
        try:
            url = f"{self.base_url}/quote"
            params = {
                "inputMint": input_mint,
                "outputMint": output_mint,
                "amount": amount,
                "slippageBps": slippage_bps
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        print(f"Jupiter API error: {response.status}")
                        return None
        except Exception as e:
            print(f"Error getting Jupiter quote: {e}")
            return None
    
    async def get_swap_transaction(self, quote_response: dict, user_public_key: str) -> dict:
        """Get a swap transaction from Jupiter API"""
        try:
            url = f"{self.base_url}/swap"
            
            payload = {
                "quoteResponse": quote_response,
                "userPublicKey": user_public_key,
                "wrapAndUnwrapSol": True,
                "dynamicComputeUnitLimit": True,
                "dynamicSlippage": True
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        print(f"Jupiter API error: {response.status} - {error_text}")
                        return None
        except Exception as e:
            print(f"Error getting Jupiter swap transaction: {e}")
            return None

# Global instance
jupiter_service = JupiterService()
