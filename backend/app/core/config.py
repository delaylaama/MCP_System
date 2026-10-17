"""Application Configuration Settings"""

from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # General Environment
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    APP_NAME: str = "Universal AI File Manager"
    VERSION: str = "1.0.0"

    # Security & JWT
    SECRET_KEY: str = "dev_jwt_secret_universal_ai_file_manager_2026_academic"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # AES-256 Fernet Key for encrypting OAuth tokens
    ENCRYPTION_KEY: str = "AnEW-Wuk_uumgk55BoVlrDT0t5HeX8AciGlNHwgWHpE="

    # Database: Supports PostgreSQL or SQLite async
    DATABASE_URL: str = "sqlite+aiosqlite:///./mcp_file_manager.db"

    # Frontend & CORS
    FRONTEND_URL: str = "http://localhost:5173"
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    # Model Context Protocol (MCP) Server
    MCP_SERVER_HOST: str = "127.0.0.1"
    MCP_SERVER_PORT: int = 8001
    MCP_SERVER_URL: str = "http://127.0.0.1:8001/mcp"

    # Local Filesystem Root
    LOCAL_STORAGE_ROOT: str = "./local_storage"

    # AI & LLM Service
    LLM_PROVIDER: str = "openai"  # "openai", "gemini", "ollama", or "heuristic"
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    GEMINI_API_KEY: Optional[str] = None
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:7b"

    # Vector Database (ChromaDB)
    CHROMA_PERSIST_DIRECTORY: str = "./chroma_db"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # Google Drive OAuth 2.0
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/providers/google_drive/callback"

    # Microsoft Graph / OneDrive OAuth 2.0
    MICROSOFT_CLIENT_ID: Optional[str] = None
    MICROSOFT_CLIENT_SECRET: Optional[str] = None
    MICROSOFT_TENANT_ID: str = "common"
    MICROSOFT_REDIRECT_URI: str = "http://localhost:8000/api/providers/onedrive/callback"

    # Dropbox OAuth 2.0
    DROPBOX_APP_KEY: Optional[str] = None
    DROPBOX_APP_SECRET: Optional[str] = None
    DROPBOX_REDIRECT_URI: str = "http://localhost:8000/api/providers/dropbox/callback"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
