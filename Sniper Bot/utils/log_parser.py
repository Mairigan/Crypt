import re
import base64
import json
from solana.transaction import Transaction
from solana.rpc.core import RPCException
from bot.solana_client import solana_client

class LogParser:
    @staticmethod
    def parse_raydium_amm_logs(logs: list, signature: str) -> dict:
        """
        Parse Raydium AMM logs to extract token information
        Returns dict with mint_address, pool_address, and other details
        """
        result = {
            "mint_address": None,
            "pool_address": None,
            "signature": signature,
            "program": "raydium_amm"
        }
        
        try:
            joined_logs = " ".join(logs)
            
            # Look for mint address in logs
            mint_pattern = r'mint: (\w{32,44})'
            mint_match = re.search(mint_pattern, joined_logs)
            if mint_match:
                result["mint_address"] = mint_match.group(1)
            
            # Look for pool address
            pool_pattern = r'pool: (\w{32,44})'
            pool_match = re.search(pool_pattern, joined_logs)
            if pool_match:
                result["pool_address"] = pool_match.group(1)
            
            # Look for initialization message
            if "initialize2" in joined_logs and "init_pair" in joined_logs:
                result["action"] = "pool_creation"
            
            return result
        except Exception as e:
            print(f"Error parsing Raydium AMM logs: {e}")
            return result
    
    @staticmethod
    def parse_raydium_clmm_logs(logs: list, signature: str) -> dict:
        """
        Parse Raydium CLMM logs to extract token information
        """
        result = {
            "mint_address": None,
            "position_address": None,
            "signature": signature,
            "program": "raydium_clmm"
        }
        
        try:
            joined_logs = " ".join(logs)
            
            # Look for open position events
            if "open_position" in joined_logs:
                result["action"] = "position_opened"
                
                # Try to extract mint address
                mint_pattern = r'mint: (\w{32,44})'
                mint_match = re.search(mint_pattern, joined_logs)
                if mint_match:
                    result["mint_address"] = mint_match.group(1)
            
            return result
        except Exception as e:
            print(f"Error parsing Raydium CLMM logs: {e}")
            return result
    
    @staticmethod
    def parse_pump_fun_logs(logs: list, signature: str) -> dict:
        """
        Parse Pump.fun logs to extract token information
        """
        result = {
            "mint_address": None,
            "signature": signature,
            "program": "pump_fun"
        }
        
        try:
            joined_logs = " ".join(logs)
            
            # Look for token creation
            if "create" in joined_logs and "token" in joined_logs:
                result["action"] = "token_creation"
                
                # Try to extract mint address
                mint_pattern = r'mint: (\w{32,44})'
                mint_match = re.search(mint_pattern, joined_logs)
                if mint_match:
                    result["mint_address"] = mint_match.group(1)
            
            # Look for init_launch (migration to AMM)
            if "init_launch" in joined_logs:
                result["action"] = "migration_initiated"
                
                # Try to extract mint address
                mint_pattern = r'mint: (\w{32,44})'
                mint_match = re.search(mint_pattern, joined_logs)
                if mint_match:
                    result["mint_address"] = mint_match.group(1)
            
            return result
        except Exception as e:
            print(f"Error parsing Pump.fun logs: {e}")
            return result

# Global instance
log_parser = LogParser()
