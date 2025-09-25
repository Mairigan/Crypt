import os
from utils.security import security_manager
from dotenv import load_dotenv

load_dotenv()

def setup_wallet():
    """Helper script to encrypt wallet private key"""
    private_key = os.getenv("WALLET_PRIVATE_KEY")
    
    if not private_key:
        print("Please set WALLET_PRIVATE_KEY in your .env file first")
        return
    
    encrypted_key = security_manager.encrypt_data(private_key)
    
    print("Replace the WALLET_PRIVATE_KEY in your .env file with:")
    print(f"WALLET_PRIVATE_KEY={encrypted_key}")
    
    # Securely delete the original from memory
    security_manager.secure_delete(private_key)

if __name__ == "__main__":
    setup_wallet()
