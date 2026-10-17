"""FileMetadata database model."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, BigInteger, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class FileMetadata(Base):
    __tablename__ = "file_metadata"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String(50), nullable=False, index=True)
    provider_file_id = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    path = Column(Text, nullable=True)
    mime_type = Column(String(100), nullable=True)
    extension = Column(String(20), nullable=True)
    size = Column(BigInteger, default=0, nullable=False)
    modified_at = Column(DateTime(timezone=True), nullable=True)
    web_url = Column(Text, nullable=True)
    downloadable = Column(Boolean, default=True, nullable=False)
    is_folder = Column(Boolean, default=False, nullable=False)
    content_hash = Column(String(64), nullable=True, index=True)  # SHA-256 for duplicate detection
    metadata_json = Column(Text, nullable=True)  # Provider-specific raw metadata serialized
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("User", back_populates="cached_files")
