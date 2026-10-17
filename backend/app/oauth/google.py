"""Google OAuth 2.0 Flow Handler."""

import urllib.parse
import httpx
from typing import Dict, Any, Tuple
from backend.app.core.config import get_settings
from backend.app.core.logging import logger

settings = get_settings()

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]


class GoogleOAuthHandler:
    @staticmethod
    def get_authorization_url(state: str) -> str:
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID or "missing_google_client_id",
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": " ".join(GOOGLE_SCOPES),
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
        return f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"

    @staticmethod
    async def exchange_code_for_tokens(code: str) -> Dict[str, Any]:
        data = {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(GOOGLE_TOKEN_URL, data=data)
            if resp.status_code != 200:
                logger.error(f"Google token exchange failed: {resp.text}")
                raise RuntimeError(f"Failed to exchange Google OAuth code: {resp.text}")
            tokens = resp.json()

            # Retrieve user email for identifier
            email = "Google Drive Account"
            if tokens.get("access_token"):
                try:
                    user_info_resp = await client.get(
                        "https://www.googleapis.com/oauth2/v2/userinfo",
                        headers={"Authorization": f"Bearer {tokens['access_token']}"},
                    )
                    if user_info_resp.status_code == 200:
                        email = user_info_resp.json().get("email", email)
                except Exception:
                    pass

            tokens["email"] = email
            return tokens
