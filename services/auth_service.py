# services/auth_service.py
from cryptography.fernet import Fernet
import hashlib
import base64

def generate_crypto_key(name: str, password: str) -> bytes:
    combined = f"{name}{password}".encode()
    digest = hashlib.sha256(combined).digest()
    return base64.urlsafe_b64encode(digest)

def encrypt_token(token: str, name: str, password: str) -> str:
    key = generate_crypto_key(name, password)
    return Fernet(key).encrypt(token.encode()).decode()

def decrypt_token(encrypted_token: str, name: str, password: str) -> str:
    key = generate_crypto_key(name, password)
    return Fernet(key).decrypt(encrypted_token.encode()).decode()