"""
OS Keychain Token Storage via keyring.
Tokens are stored under service name derived from APP_NAME (KEYRING_SERVICE_NAME = 'mcp-drivers').
Seamlessly bridges existing connections so users are not asked to re-authenticate.
"""

import json
from typing import Optional, Dict, Any
from backend.search.config import KEYRING_SERVICE_NAME
from backend.app.core.logging import logger

try:
    import keyring
except ImportError:
    keyring = None


class KeyringStore:
    def __init__(self, service_name: str = KEYRING_SERVICE_NAME):
        self.service_name = service_name

    def _make_key(self, user_id: str, provider: str) -> str:
        return f"{user_id}:{provider}"

    def set_tokens(self, user_id: str, provider: str, tokens: Dict[str, Any]) -> bool:
        """Stores token dictionary securely in OS keychain."""
        if not keyring:
            logger.warning("Keyring module not installed; skipping keychain storage.")
            return False
        try:
            key = self._make_key(user_id, provider)
            serialized = json.dumps(tokens)
            keyring.set_password(self.service_name, key, serialized)
            return True
        except Exception as e:
            logger.warning(f"Error saving tokens to keyring for {provider}: {e}")
            return False

    def get_tokens(self, user_id: str, provider: str) -> Optional[Dict[str, Any]]:
        """Retrieves token dictionary from OS keychain."""
        if not keyring:
            return None
        try:
            key = self._make_key(user_id, provider)
            raw = keyring.get_password(self.service_name, key)
            if raw:
                return json.loads(raw)
        except Exception as e:
            logger.warning(f"Error reading tokens from keyring for {provider}: {e}")
        return None

    def delete_tokens(self, user_id: str, provider: str) -> bool:
        """Removes tokens from OS keychain."""
        if not keyring:
            return False
        try:
            key = self._make_key(user_id, provider)
            keyring.delete_password(self.service_name, key)
            return True
        except Exception:
            return False


token_store = KeyringStore()
