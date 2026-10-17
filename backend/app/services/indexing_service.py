"""
Document Text Extraction, Chunking, and Vector Indexing with ChromaDB.
Provides Semantic Search across multi-cloud documents.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from backend.app.core.config import get_settings
from backend.app.core.logging import logger
from backend.app.schemas.file import FileRecord

settings = get_settings()


class DocumentExtractor:
    """Extracts plain text from various document formats."""

    @staticmethod
    def extract_text(file_path: Path, max_chars: int = 200000) -> str:
        if not file_path.exists():
            return ""

        ext = file_path.suffix.lower()
        try:
            if ext in [".txt", ".md", ".json", ".csv", ".py", ".html"]:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    return f.read(max_chars)
            elif ext == ".pdf":
                import pypdf
                reader = pypdf.PdfReader(file_path)
                return "\n".join(page.extract_text() or "" for page in reader.pages)[:max_chars]
            elif ext == ".docx":
                import docx
                doc = docx.Document(file_path)
                return "\n".join(p.text for p in doc.paragraphs)[:max_chars]
        except Exception as e:
            logger.error(f"Text extraction failed on {file_path}: {e}")
        return ""


class TextChunker:
    """Splits large texts into overlapping chunks for embedding generation."""

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 100) -> List[str]:
        if not text or not text.strip():
            return []

        words = text.split()
        chunks = []
        start = 0
        while start < len(words):
            end = start + chunk_size
            chunk = " ".join(words[start:end])
            chunks.append(chunk)
            if end >= len(words):
                break
            start += (chunk_size - chunk_overlap)
        return chunks


class SemanticSearchService:
    """Manages persistent ChromaDB vector store and semantic similarity queries."""

    def __init__(self, persist_dir: Optional[str] = None):
        self.persist_dir = persist_dir or settings.CHROMA_PERSIST_DIRECTORY
        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)
        try:
            self.client = chromadb.PersistentClient(path=self.persist_dir)
            self.collection = self.client.get_or_create_collection(
                name="file_documents",
                metadata={"hnsw:space": "cosine"},
            )
            logger.info("ChromaDB vector store initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB persistent client: {e}")
            self.client = None
            self.collection = None

    def index_document(self, file_record: FileRecord, content: str):
        """Indexes document chunks into ChromaDB."""
        if not self.collection or not content or not content.strip():
            return

        chunks = TextChunker.chunk_text(content)
        if not chunks:
            return

        documents = []
        ids = []
        metadatas = []

        for idx, chunk in enumerate(chunks):
            chunk_id = f"{file_record.id}_chunk_{idx}"
            ids.append(chunk_id)
            documents.append(chunk)
            metadatas.append({
                "file_id": file_record.id,
                "provider": file_record.provider,
                "name": file_record.name,
                "chunk_index": idx,
            })

        try:
            self.collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
            )
            logger.info(f"Indexed {len(chunks)} chunks for document {file_record.name}")
        except Exception as e:
            logger.error(f"Failed to index document {file_record.id}: {e}")

    def semantic_query(self, query: str, top_k: int = 20) -> Dict[str, float]:
        """
        Executes dense vector similarity search for query.
        Returns mapping from file_id to highest semantic similarity score (0.0 to 1.0).
        """
        if not self.collection:
            return {}

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
            )

            file_scores: Dict[str, float] = {}
            if results and "metadatas" in results and results["metadatas"]:
                metas = results["metadatas"][0]
                distances = results["distances"][0] if "distances" in results and results["distances"] else []

                for meta, dist in zip(metas, distances):
                    f_id = meta.get("file_id")
                    if not f_id:
                        continue
                    # Cosine distance to similarity (0 <= dist <= 2; dist=0 => score=1.0)
                    similarity = max(0.0, 1.0 - (dist / 2.0))
                    if f_id not in file_scores or similarity > file_scores[f_id]:
                        file_scores[f_id] = round(similarity, 3)

            return file_scores
        except Exception as e:
            logger.error(f"Semantic search query error: {e}")
            return {}


semantic_search_service = SemanticSearchService()
