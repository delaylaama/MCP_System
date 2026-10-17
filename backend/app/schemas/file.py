"""Unified File Model schemas."""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime


class FileRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Unique internal or composite file identifier")
    provider: str = Field(..., description="Storage provider: google_drive, onedrive, dropbox, local")
    provider_file_id: str = Field(..., description="Provider-native file identifier")
    name: str = Field(..., description="File name including extension")
    path: Optional[str] = Field(None, description="Logical folder or filesystem path")
    mime_type: Optional[str] = Field(None, description="Standard MIME type")
    extension: Optional[str] = Field(None, description="File extension with leading dot")
    size: int = Field(0, description="Size in bytes")
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    web_url: Optional[str] = Field(None, description="Direct web link to open file in provider viewer")
    downloadable: bool = Field(True, description="Whether the file can be downloaded directly")
    is_folder: bool = Field(False, description="Whether this record represents a directory/folder")
    content_available: bool = Field(False, description="Whether textual content extraction is available")
    content_hash: Optional[str] = Field(None, description="SHA-256 hash of file content")
    score: Optional[float] = Field(None, description="Relevance ranking score (0.0 to 1.0)")
    score_breakdown: Optional[Dict[str, float]] = Field(None, description="Detailed score decomposition")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Provider-specific attributes")


class DuplicateGroup(BaseModel):
    content_hash: str
    size: int
    files: list[FileRecord]
