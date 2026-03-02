from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv

load_dotenv()

# Key from .env
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    # Ensure there's a fallback or error out in a real app
    # Generating a random key for development setup
    ENCRYPTION_KEY = Fernet.generate_key().decode()
    
cipher_suite = Fernet(ENCRYPTION_KEY.encode())

def encrypt_token(plain_text: str) -> str:
    """Mã hóa Token trước khi lưu vào Database"""
    if not plain_text: return ""
    return cipher_suite.encrypt(plain_text.encode()).decode()

def decrypt_token(encrypted_text: str) -> str:
    """Giải mã Token khi cần gọi API"""
    if not encrypted_text: return ""
    return cipher_suite.decrypt(encrypted_text.encode()).decode()
