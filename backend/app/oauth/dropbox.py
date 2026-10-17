"""Dropbox OAuth 2.0 Flow Handler."""

import urllib.parse
import httpx
from typing import Dict, Any
from backend.app.core.config import get_settings
from backend.app.core.logging import logger

settings = get_settings()

DROPBOX_AUTH_URL = "https://www.dropbox.com/oauth2/authorize"
DROPBOX_TOKEN_URL = "https://api.dropboxapi.com/oauth2/token"


class DropboxOAuthHandler:
    @staticmethod
    def get_authorization_url(state: str) -> str:
        current_settings = get_settings()
        params = {
            "client_id": current_settings.DROPBOX_APP_KEY or "missing_dropbox_app_key",
            "response_type": "code",
            "redirect_uri": current_settings.DROPBOX_REDIRECT_URI,
            "token_access_type": "offline",
            "state": state,
        }
        return f"{DROPBOX_AUTH_URL}?{urllib.parse.urlencode(params)}"

    @staticmethod
    async def exchange_code_for_tokens(code: str) -> Dict[str, Any]:
        current_settings = get_settings()
        data = {
            "code": code,
            "grant_type": "authorization_code",
            "client_id": current_settings.DROPBOX_APP_KEY,
            "client_secret": current_settings.DROPBOX_APP_SECRET,
            "redirect_uri": current_settings.DROPBOX_REDIRECT_URI,
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(DROPBOX_TOKEN_URL, data=data)
            if resp.status_code != 200:
                logger.error(f"Dropbox token exchange failed: {resp.text}")
                raise RuntimeError(f"Failed to exchange Dropbox OAuth code: {resp.text}")
            tokens = resp.json()

            # Retrieve user display email
            email = "Dropbox Account"
            if tokens.get("access_token"):
                try:
                    account_resp = await client.post(
                        "https://api.dropboxapi.com/2/users/get_current_account",
                        headers={"Authorization": f"Bearer {tokens['access_token']}"},
                    )
                    if account_resp.status_code == 200:
                        email = account_resp.json().get("email", email)
                except Exception:
                    pass

            tokens["email"] = email
            return tokens
