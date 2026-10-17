"""
Configuration for Local Search, Storage Paths, Keyring, and Model Management.
All paths and service names are derived dynamically from APP_NAME.
"""

import os
from pathlib import Path

# The single master constant for application branding
APP_NAME = "MCP Drivers"

# Base AppData Directory
_appdata = os.environ.get("APPDATA")
if _appdata:
    BASE_APPDATA_DIR = Path(_appdata) / APP_NAME
else:
    BASE_APPDATA_DIR = Path.home() / f".{APP_NAME.lower().replace(' ', '_')}"

INDEX_DIR = BASE_APPDATA_DIR / "index"
MODELS_DIR = BASE_APPDATA_DIR / "models"
LOGS_DIR = BASE_APPDATA_DIR / "logs"
TEMP_DOWNLOAD_DIR = BASE_APPDATA_DIR / "temp"

# Keyring service name derived from APP_NAME
KEYRING_SERVICE_NAME = APP_NAME.lower().replace(" ", "-")

# Model configuration
TEXT_MODEL_NAME = "all-MiniLM-L6-v2"
CLIP_MODEL_NAME = "ViT-B-32"
CLIP_PRETRAINED = "openai"

# Create directories if they do not exist
for _directory in (BASE_APPDATA_DIR, INDEX_DIR, MODELS_DIR, LOGS_DIR, TEMP_DOWNLOAD_DIR):
    _directory.mkdir(parents=True, exist_ok=True)
