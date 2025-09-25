import aiohttp
import asyncio
from config.settings import DEXSCREENER_API_URL, MIN_LIQUIDITY
from services.dexscreener_service import DexScreenerService

class TokenAnalyzer:
    def __init__(self):
        self.dexscreener_service = DexScreenerService()
    
    async def analyze_token(self, mint_address: str) -> dict:
        """
        Analyze a token for potential risks and opportunities
        Returns a dict with analysis results
        """
        analysis = {
            "mint_address": mint_address,
            "is_valid": False,
            "is_rug": False,
            "liquidity": 0,
            "market_cap": 0,
            "holder_count": 0,
            "lock_status": "unknown",
            "risk_score": 10,  # 0-10, 10 being highest risk
            "warnings": [],
            "opportunities": []
        }
        
        try:
            # Get token info from DexScreener
            token_info = await self.dexscreener_service.get_token_info(mint_address)
            
            if not token_info or "pairs" not in token_info or len(token_info["pairs"]) == 0:
                analysis["warnings"].append("Token not found on DexScreener")
                return analysis
            
            pair = token_info["pairs"][0]
            
            # Check liquidity
            liquidity = float(pair.get("liquidity", {}).get("usd", 0))
            analysis["liquidity"] = liquidity
            
            if liquidity < MIN_LIQUIDITY:
                analysis["warnings"].append(f"Low liquidity: ${liquidity:.2f}")
                analysis["risk_score"] += 2
            
            # Check if locked (simplified check)
            lock_info = pair.get("liquidity", {}).get("lock", {})
            if lock_info and lock_info.get("locked", False):
                analysis["lock_status"] = "locked"
                analysis["opportunities"].append("Liquidity is locked")
                analysis["risk_score"] -= 2
            else:
                analysis["lock_status"] = "unlocked"
                analysis["warnings"].append("Liquidity not locked")
                analysis["risk_score"] += 3
            
            # Check creation time (recent tokens are riskier but also more opportunistic)
            # This would need actual implementation based on available data
            
            # Check if honeypot (simplified)
            if pair.get("honeypot", False):
                analysis["is_rug"] = True
                analysis["warnings"].append("Potential honeypot detected")
                analysis["risk_score"] = 10
            
            # If we passed all checks, mark as valid
            if analysis["risk_score"] <= 6 and liquidity >= MIN_LIQUIDITY:
                analysis["is_valid"] = True
            
            return analysis
            
        except Exception as e:
            print(f"Error analyzing token {mint_address}: {e}")
            analysis["warnings"].append(f"Analysis error: {str(e)}")
            return analysis

# Global instance
token_analyzer = TokenAnalyzer()
