"""Microsoft Identity Platform OAuth 2.0 Flow Handler."""

import urllib.parse
import httpx
from typing import Dict, Any
from backend.app.core.config import get_settings
from backend.app.core.logging import logger

settings = get_settings()

MS_AUTH_URL = f"https://login.microsoftonline.com/{settings.MICROSOFT_TENANT_ID}/oauth2/v2.0/authorize"
MS_TOKEN_URL = f"https://login.microsoftonline.com/{settings.MICROSOFT_TENANT_ID}/oauth2/v2.0/token"
MS_SCOPES = [
    "Files.Read.All",
    "User.Read",
    "offline_access",
]


class MicrosoftOAuthHandler:
    @staticmethod
    def _get_tenant(current_settings) -> str:
        # Default to 'common' to support personal Microsoft accounts (@outlook.com, @gmail.com) and org accounts
        tenant = getattr(current_settings, "MICROSOFT_TENANT_ID", None)
        return tenant if tenant else "common"

    @staticmethod
    def get_authorization_url(state: str) -> str:
        current_settings = get_settings()
        tenant = MicrosoftOAuthHandler._get_tenant(current_settings)
        ms_auth_url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize"
        params = {
            "client_id": current_settings.MICROSOFT_CLIENT_ID or "missing_microsoft_client_id",
            "response_type": "code",
            "redirect_uri": current_settings.MICROSOFT_REDIRECT_URI,
            "response_mode": "query",
            "scope": " ".join(MS_SCOPES),
            "state": state,
        }
        return f"{ms_auth_url}?{urllib.parse.urlencode(params)}"

    @staticmethod
    async def exchange_code_for_tokens(code: str) -> Dict[str, Any]:
        current_settings = get_settings()
        tenant = MicrosoftOAuthHandler._get_tenant(current_settings)
        ms_token_url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
        data = {
            "client_id": current_settings.MICROSOFT_CLIENT_ID,
            "client_secret": current_settings.MICROSOFT_CLIENT_SECRET,
            "code": code,
            "redirect_uri": current_settings.MICROSOFT_REDIRECT_URI,
            "grant_type": "authorization_code",
            "scope": " ".join(MS_SCOPES),
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(ms_token_url, data=data)
            if resp.status_code != 200:
                logger.error(f"Microsoft token exchange failed: {resp.text}")
                raise RuntimeError(f"Failed to exchange Microsoft OAuth code: {resp.text}")
            tokens = resp.json()

            # Retrieve account email
            email = "OneDrive Account"
            if tokens.get("access_token"):
                try:
                    user_resp = await client.get(
                        "https://graph.microsoft.com/v1.0/me",
                        headers={"Authorization": f"Bearer {tokens['access_token']}"},
                    )
                    if user_resp.status_code == 200:
                        data = user_resp.json()
                        email = data.get("userPrincipalName") or data.get("mail") or email
                except Exception:
                    pass

            tokens["email"] = email
            return tokens
