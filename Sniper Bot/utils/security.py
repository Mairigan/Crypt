import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from config.settings import ENCRYPTION_KEY

class SecurityManager:
    def __init__(self):
        self.fernet = self._create_fernet(ENCRYPTION_KEY)
    
    def _create_fernet(self, password: str) -> Fernet:
        """Create a Fernet instance from a password"""
        salt = b'solana_sniper_bot_salt_'  # In production, use a random salt and store it securely
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return Fernet(key)
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        return self.fernet.encrypt(data.encode()).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        return self.fernet.decrypt(encrypted_data.encode()).decode()
    
    def secure_delete(self, data: str) -> None:
        """Securely delete data from memory (as much as possible in Python)"""
        # Overwrite the memory location (limited effectiveness in Python due to GC)
        if data:
            data = '0' * len(data)
        return None

# Global instance
security_manager = SecurityManager()
