import aiohttp
from config.settings import DEXSCREENER_API_URL

class DexScreenerService:
    def __init__(self):
        self.base_url = DEXSCREENER_API_URL
    
    async def get_token_info(self, mint_address: str) -> dict:
        """Get token information from DexScreener"""
        try:
            url = f"{self.base_url}/tokens/{mint_address}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        print(f"DexScreener API error: {response.status}")
                        return None
        except Exception as e:
            print(f"Error getting DexScreener token info: {e}")
            return None
    
    async def get_pair_info(self, pair_address: str) -> dict:
        """Get pair information from DexScreener"""
        try:
            url = f"{self.base_url}/pairs/{pair_address}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        print(f"DexScreener API error: {response.status}")
                        return None
        except Exception as e:
            print(f"Error getting DexScreener pair info: {e}")
            return None

# Global instance
dexscreener_service = DexScreenerService()
