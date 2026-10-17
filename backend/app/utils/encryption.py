"""
Symmetric Token Encryption using Fernet (AES-128-CBC with HMAC-SHA256).
Ensures OAuth tokens, refresh tokens, and credentials are never stored in plaintext.
"""

import base64
from cryptography.fernet import Fernet
from backend.app.core.config import get_settings

settings = get_settings()


def _get_cipher_suite() -> Fernet:
    key = settings.ENCRYPTION_KEY
    if not key:
        raise ValueError("ENCRYPTION_KEY must be configured in environment variables.")
    # Ensure key is valid bytes
    if isinstance(key, str):
        key_bytes = key.encode("utf-8")
    else:
        key_bytes = key
    return Fernet(key_bytes)


def encrypt_data(plaintext: str) -> str:
    """Encrypt a plaintext string into a safe encrypted ciphertext string."""
    if not plaintext:
        return ""
    cipher = _get_cipher_suite()
    encrypted_bytes = cipher.encrypt(plaintext.encode("utf-8"))
    return encrypted_bytes.decode("utf-8")


def decrypt_data(ciphertext: str) -> str:
    """Decrypt a ciphertext string back into the original plaintext."""
    if not ciphertext:
        return ""
    cipher = _get_cipher_suite()
    decrypted_bytes = cipher.decrypt(ciphertext.encode("utf-8"))
    return decrypted_bytes.decode("utf-8")
