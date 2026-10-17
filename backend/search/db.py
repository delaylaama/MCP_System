"""
Database management for Local AI Search:
1. SQLite: Metadata table `files` + Full-Text Search table `files_fts` (FTS5).
2. LanceDB: Vector tables `text_vectors` (384-dim MiniLM) & `image_vectors` (512-dim CLIP).
All data stored in %APPDATA%/MCP Drivers/index/.
"""

import sqlite3
import datetime
from typing import Optional, List, Dict, Any
from backend.search.config import INDEX_DIR
from backend.app.core.logging import logger

try:
    import lancedb
    import pyarrow as pa
except ImportError:
    lancedb = None
    pa = None

SQLITE_PATH = INDEX_DIR / "metadata.db"
LANCEDB_PATH = INDEX_DIR / "lancedb"


class SearchDatabase:
    def __init__(self, db_path=SQLITE_PATH, lancedb_path=LANCEDB_PATH):
        self.db_path = db_path
        self.lancedb_path = lancedb_path
        self._init_sqlite()
        self._lance_db = None
        self._text_table = None
        self._image_table = None
        self._init_lancedb()

    def get_sqlite_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA busy_timeout=30000")
        return conn

    def _init_sqlite(self):
        with self.get_sqlite_conn() as conn:
            # Metadata table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    id TEXT PRIMARY KEY,
                    source TEXT NOT NULL,
                    path TEXT NOT NULL,
                    name TEXT NOT NULL,
                    mime TEXT,
                    ext TEXT,
                    modified TEXT,
                    size INTEGER DEFAULT 0,
                    hash TEXT,
                    indexed_at TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_files_source ON files(source)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_files_ext ON files(ext)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_files_modified ON files(modified)")

            # FTS5 Full-Text Search table
            try:
                conn.execute("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS files_fts USING fts5(
                        id UNINDEXED,
                        name,
                        path,
                        content_snippet,
                        tokenize = 'porter unicode61'
                    )
                """)
            except Exception as e:
                logger.warning(f"FTS5 virtual table initialization notice: {e}")

    def _init_lancedb(self):
        if not lancedb or not pa:
            return
        try:
            self._lance_db = lancedb.connect(str(self.lancedb_path))
            table_names = self._lance_db.table_names()

            # Text Vectors Schema (MiniLM 384-dim)
            if "text_vectors" not in table_names:
                text_schema = pa.schema([
                    pa.field("file_id", pa.string()),
                    pa.field("chunk_idx", pa.int32()),
                    pa.field("snippet", pa.string()),
                    pa.field("vector", pa.list_(pa.float32(), 384)),
                ])
                self._text_table = self._lance_db.create_table("text_vectors", schema=text_schema)
            else:
                self._text_table = self._lance_db.open_table("text_vectors")

            # Image Vectors Schema (CLIP 512-dim)
            if "image_vectors" not in table_names:
                image_schema = pa.schema([
                    pa.field("file_id", pa.string()),
                    pa.field("vector", pa.list_(pa.float32(), 512)),
                ])
                self._image_table = self._lance_db.create_table("image_vectors", schema=image_schema)
            else:
                self._image_table = self._lance_db.open_table("image_vectors")
        except Exception as e:
            logger.warning(f"LanceDB init error: {e}")

    # ==================== Unified SQLite Access ====================

    def upsert_file_metadata(
        self,
        file_id: str,
        source: str,
        path: str,
        name: str,
        mime: Optional[str] = None,
        ext: Optional[str] = None,
        modified: Optional[str] = None,
        size: int = 0,
        content_hash: Optional[str] = None,
        content_snippet: Optional[str] = None,
    ):
        """Unified function for all connectors to record file metadata and FTS snippet."""
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with self.get_sqlite_conn() as conn:
            conn.execute("""
                INSERT INTO files (id, source, path, name, mime, ext, modified, size, hash, indexed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    source=excluded.source,
                    path=excluded.path,
                    name=excluded.name,
                    mime=excluded.mime,
                    ext=excluded.ext,
                    modified=excluded.modified,
                    size=excluded.size,
                    hash=excluded.hash,
                    indexed_at=excluded.indexed_at
            """, (file_id, source, path, name, mime, ext, modified, size, content_hash, now))

            # Update FTS5 index
            try:
                conn.execute("DELETE FROM files_fts WHERE id = ?", (file_id,))
                conn.execute("""
                    INSERT INTO files_fts (id, name, path, content_snippet)
                    VALUES (?, ?, ?, ?)
                """, (file_id, name, path, content_snippet or ""))
            except Exception as e:
                logger.warning(f"FTS5 insert failed for {file_id}: {e}")

    def get_file(self, file_id: str) -> Optional[Dict[str, Any]]:
        with self.get_sqlite_conn() as conn:
            row = conn.execute("SELECT * FROM files WHERE id = ?", (file_id,)).fetchone()
            return dict(row) if row else None

    def search_fts(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Executes FTS5 keyword search and returns ranked matches."""
        from backend.app.utils.query_parser import extract_terms, clean_query_text

        clean_terms = extract_terms(query, keep_recency=True)
        if not clean_terms:
            # Fallback to alphanumeric tokens if all words were filtered
            clean_terms = [t for t in query.replace("'", " ").replace('"', ' ').split() if len(t) > 1]
        if not clean_terms:
            return []

        # Construct prioritized FTS5 query:
        # If multiple terms: exact phrase or AND query takes precedence over loose OR
        if len(clean_terms) >= 2:
            phrase = " ".join(clean_terms)
            and_query = " AND ".join([f'"{t}"*' for t in clean_terms])
            or_query = " OR ".join([f'"{t}"*' for t in clean_terms])
            # In FTS5, we can query both with rank ordering
            match_query = f'"{phrase}" OR ({and_query})'
        else:
            match_query = f'"{clean_terms[0]}"*'

        with self.get_sqlite_conn() as conn:
            try:
                rows = conn.execute("""
                    SELECT f.*, fts.rank, fts.content_snippet
                    FROM files_fts fts
                    JOIN files f ON f.id = fts.id
                    WHERE files_fts MATCH ?
                    ORDER BY fts.rank
                    LIMIT ?
                """, (match_query, limit)).fetchall()
                if not rows and len(clean_terms) >= 2:
                    # Fallback to loose OR if strict AND found zero records
                    rows = conn.execute("""
                        SELECT f.*, fts.rank, fts.content_snippet
                        FROM files_fts fts
                        JOIN files f ON f.id = fts.id
                        WHERE files_fts MATCH ?
                        ORDER BY fts.rank
                        LIMIT ?
                    """, (or_query, limit)).fetchall()
                return [dict(r) for r in rows]
            except Exception as e:
                logger.warning(f"FTS search error on '{query}': {e}")
                return []

    # ==================== LanceDB Vector Operations ====================

    def save_text_vectors(self, file_id: str, chunks_with_vectors: List[Dict[str, Any]]):
        """Saves text embedding vectors for chunks into LanceDB."""
        if not self._text_table:
            self._init_lancedb()
        if not self._text_table:
            return
        try:
            # Delete any existing entries for this file_id
            self._text_table.delete(f'file_id = "{file_id}"')
            if chunks_with_vectors:
                records = [
                    {
                        "file_id": file_id,
                        "chunk_idx": c["chunk_idx"],
                        "snippet": c["snippet"],
                        "vector": c["vector"],
                    }
                    for c in chunks_with_vectors
                ]
                self._text_table.add(records)
        except Exception as e:
            logger.warning(f"Error saving text vectors for {file_id}: {e}")

    def save_image_vector(self, file_id: str, vector: List[float]):
        """Saves image embedding vector into LanceDB."""
        if not self._image_table:
            self._init_lancedb()
        if not self._image_table:
            return
        try:
            self._image_table.delete(f'file_id = "{file_id}"')
            self._image_table.add([{"file_id": file_id, "vector": vector}])
        except Exception as e:
            logger.warning(f"Error saving image vector for {file_id}: {e}")

    def search_text_vectors(self, query_vector: List[float], limit: int = 50) -> List[Dict[str, Any]]:
        """Queries LanceDB text_vectors using cosine/L2 distance."""
        if not self._text_table:
            return []
        try:
            results = self._text_table.search(query_vector).limit(limit).to_list()
            return results
        except Exception as e:
            logger.warning(f"Text vector search error: {e}")
            return []

    def search_image_vectors(self, query_vector: List[float], limit: int = 50) -> List[Dict[str, Any]]:
        """Queries LanceDB image_vectors with text or image vector."""
        if not self._image_table:
            return []
        try:
            results = self._image_table.search(query_vector).limit(limit).to_list()
            return results
        except Exception as e:
            logger.warning(f"Image vector search error: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """Returns counts of indexed files, breakdown by source, and vector counts."""
        with self.get_sqlite_conn() as conn:
            total_files = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
            sources = conn.execute("SELECT source, COUNT(*) as cnt FROM files GROUP BY source").fetchall()
            by_source = {row["source"]: row["cnt"] for row in sources}

            text_vecs = 0
            image_vecs = 0
            if self._text_table:
                try:
                    text_vecs = len(self._text_table)
                except Exception:
                    pass
            if self._image_table:
                try:
                    image_vecs = len(self._image_table)
                except Exception:
                    pass

            return {
                "total_files": total_files,
                "by_source": by_source,
                "text_vectors": text_vecs,
                "image_vectors": image_vecs,
            }


db = SearchDatabase()
