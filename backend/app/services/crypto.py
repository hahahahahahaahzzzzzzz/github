import base64
import hashlib
from cryptography.fernet import Fernet
from app.config import settings

# Derive a valid 32-byte URL-safe base64 key from our app's SECRET_KEY
derived = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
fernet_key = base64.urlsafe_b64encode(derived)
fernet = Fernet(fernet_key)

def encrypt_value(value: str) -> str:
    """
    Encrypts a plaintext string to an encrypted ciphertext block.
    """
    if not value:
        return ""
    return fernet.encrypt(value.encode('utf-8')).decode('utf-8')

def decrypt_value(ciphertext: str) -> str:
    """
    Decrypts an encrypted ciphertext block back to plaintext.
    """
    if not ciphertext:
        return ""
    try:
        return fernet.decrypt(ciphertext.encode('utf-8')).decode('utf-8')
    except Exception:
        # If decryption fails (e.g., key changed or data corrupt), return indicator
        return "[Decryption Failure]"
