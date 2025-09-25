from solana.rpc.core import RPCException
from solana.rpc.commitment import Commitment
from bot.solana_client import solana_client

class TransactionSimulator:
    @staticmethod
    async def simulate_transaction(transaction) -> dict:
        """
        Simulate a transaction to check for potential issues
        Returns a dict with simulation results
        """
        result = {
            "success": False,
            "error": None,
            "logs": [],
            "units_consumed": 0,
            "return_data": None
        }
        
        try:
            # Simulate the transaction
            simulation = await solana_client.http_client.simulate_transaction(
                transaction,
                commitment=Commitment("confirmed"),
                sig_verify=True
            )
            
            if simulation.value and simulation.value.err is None:
                result["success"] = True
                result["logs"] = simulation.value.logs
                
                # Extract compute units consumed
                for log in simulation.value.logs:
                    if "compute units consumed" in log:
                        parts = log.split(" ")
                        if len(parts) >= 4:
                            result["units_consumed"] = int(parts[3])
                
                return result
            else:
                result["error"] = simulation.value.err if simulation.value else "Unknown error"
                return result
                
        except RPCException as e:
            result["error"] = str(e)
            return result
        except Exception as e:
            result["error"] = str(e)
            return result

# Global instance
transaction_simulator = TransactionSimulator()
