"""
Local AI Indexer Module:
- Extracts text from PDF (with OCR fallback), DOCX, TXT, MD, CSV, Code.
- Extracts visual embeddings via CLIP for images (with OCR for embedded text).
- Chunks text to ~300-500 tokens with overlap + filename/path context.
- Downloads cloud files to temporary folder, embeds on-device, and cleans up immediately in try/finally.
- Runs in background with incremental skipping (hash/mtime) and watchdog integration.
- Never logs file contents or user queries.
"""

import os
import io
import time
import hashlib
import asyncio
import threading
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple

from backend.search.config import (
    APP_NAME,
    INDEX_DIR,
    TEMP_DOWNLOAD_DIR,
)
from backend.search.db import db
from backend.search.models import model_manager
from backend.app.schemas.file import FileRecord
from backend.app.core.logging import logger

# File format definitions
DOC_EXTS = {".pdf", ".docx", ".doc", ".txt", ".md", ".markdown", ".json", ".csv", ".py", ".js", ".jsx", ".ts", ".tsx", ".html", ".css", ".rtf"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tiff"}

# Junk folder / file filters
JUNK_FOLDERS = {
    "node_modules", ".git", ".svn", "appdata", "windows", "program files",
    "program files (x86)", "$recycle.bin", "system volume information",
    "__pycache__", ".vscode", ".idea", "temp", "tmp", ".cache"
}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB limit

# OCR engine lazy loader
_ocr_engine = None


def get_ocr_engine():
    global _ocr_engine
    if _ocr_engine is None:
        try:
            from rapidocr_onnxruntime import RapidOCR
            _ocr_engine = RapidOCR()
        except Exception as e:
            logger.warning(f"RapidOCR initialization error (fallback to text-only): {e}")
    return _ocr_engine


def calculate_file_hash(file_path: Path) -> str:
    """Calculates SHA-256 hash of a local file."""
    hasher = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception:
        return ""


def extract_text_from_file(file_path: Path, mime: Optional[str] = None) -> Tuple[str, str]:
    """
    Extracts text from file.
    Returns: (extracted_text, snippet_for_fts)
    """
    ext = file_path.suffix.lower()
    text = ""

    try:
        if ext == ".pdf":
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(file_path)
                pages_text = []
                for page in doc:
                    pages_text.append(page.get_text())
                text = "\n".join(pages_text).strip()

                # If text is very short or empty, attempt OCR fallback on first 5 pages
                if len(text) < 50:
                    ocr = get_ocr_engine()
                    if ocr:
                        ocr_pages = []
                        for i, page in enumerate(doc):
                            if i >= 5:
                                break
                            pix = page.get_pixmap()
                            img_bytes = pix.tobytes("png")
                            ocr_res, _ = ocr(img_bytes)
                            if ocr_res:
                                page_str = " ".join([line[1] for line in ocr_res])
                                ocr_pages.append(page_str)
                        if ocr_pages:
                            text = "\n".join(ocr_pages).strip()
            except Exception as e:
                logger.warning(f"PDF extraction error on {file_path.name}: {e}")

        elif ext == ".docx":
            try:
                import docx
                doc = docx.Document(file_path)
                paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
                for table in doc.tables:
                    for row in table.rows:
                        paragraphs.append(" | ".join([cell.text.strip() for cell in row.cells]))
                text = "\n".join(paragraphs)
            except Exception as e:
                logger.warning(f"DOCX extraction error on {file_path.name}: {e}")

        elif ext in (".txt", ".md", ".markdown", ".csv", ".json", ".py", ".js", ".jsx", ".ts", ".tsx", ".html", ".css", ".rtf"):
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    text = f.read(500000)  # Read up to 500KB
            except Exception as e:
                logger.warning(f"Text file read error on {file_path.name}: {e}")

        elif ext in IMAGE_EXTS:
            # Extract text from image via OCR if available
            ocr = get_ocr_engine()
            if ocr:
                try:
                    ocr_res, _ = ocr(str(file_path))
                    if ocr_res:
                        text = " ".join([line[1] for line in ocr_res])
                except Exception:
                    pass

    except Exception as e:
        logger.warning(f"Unexpected text extraction error on {file_path.name}: {e}")

    snippet = text[:500].strip() if text else file_path.name
    return text, snippet


def chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> List[str]:
    """Chunks text into word/token blocks with overlap."""
    words = text.split()
    if not words:
        return []
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i : i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return chunks


class LocalIndexer:
    def __init__(self):
        self.indexing_status = {
            "status": "idle",
            "current_file": "",
            "total_scanned": 0,
            "indexed_count": 0,
            "error_count": 0,
            "by_source": {"local": 0, "google_drive": 0, "onedrive": 0, "dropbox": 0},
            "last_indexed_at": None,
        }
        self._lock = threading.Lock()
        self._watcher = None

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self.indexing_status)

    def _should_skip_path(self, path: Path) -> bool:
        """Determines if path points to system junk or ignored folders."""
        parts = [p.lower() for p in path.parts]
        for junk in JUNK_FOLDERS:
            if junk in parts:
                return True
        return False

    def index_single_file(
        self,
        file_id: str,
        source: str,
        name: str,
        path: str,
        local_path: Optional[Path] = None,
        file_bytes: Optional[bytes] = None,
        mime: Optional[str] = None,
        modified: Optional[str] = None,
        size: int = 0,
        content_hash: Optional[str] = None,
    ) -> bool:
        """
        Indexes a single file (local or cloud).
        Generates FTS5 entries and LanceDB embeddings (text or image).
        """
        ext = f".{name.split('.')[-1].lower()}" if "." in name else ""
        temp_file_created = False
        target_file_path = local_path

        try:
            # If cloud file and bytes provided, write to temp directory
            if not target_file_path and file_bytes is not None:
                TEMP_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
                safe_name = "".join(c for c in name if c.isalnum() or c in "._- ")
                target_file_path = TEMP_DOWNLOAD_DIR / f"temp_{int(time.time()*1000)}_{safe_name}"
                with open(target_file_path, "wb") as tf:
                    tf.write(file_bytes)
                temp_file_created = True

            if not target_file_path or not target_file_path.exists():
                # Index metadata only
                db.upsert_file_metadata(
                    file_id=file_id,
                    source=source,
                    path=path,
                    name=name,
                    mime=mime,
                    ext=ext,
                    modified=modified,
                    size=size,
                    content_hash=content_hash,
                    content_snippet=name,
                )
                return True

            actual_size = target_file_path.stat().st_size
            if actual_size > MAX_FILE_SIZE:
                return False

            if not content_hash:
                content_hash = calculate_file_hash(target_file_path)

            # Check if unchanged
            existing = db.get_file(file_id)
            if existing and existing.get("hash") == content_hash and content_hash:
                return True  # Already indexed and unchanged

            # 1. Image Indexing (CLIP)
            if ext in IMAGE_EXTS:
                img_vector = model_manager.embed_image(str(target_file_path))
                if img_vector:
                    db.save_image_vector(file_id, img_vector)

                # Extract any text in the image
                _, ocr_snippet = extract_text_from_file(target_file_path, mime)
                db.upsert_file_metadata(
                    file_id=file_id,
                    source=source,
                    path=path,
                    name=name,
                    mime=mime or "image/jpeg",
                    ext=ext,
                    modified=modified,
                    size=actual_size,
                    content_hash=content_hash,
                    content_snippet=ocr_snippet or name,
                )
                return True

            # 2. Document & Text Indexing (MiniLM + FTS5)
            if ext in DOC_EXTS:
                extracted_text, snippet = extract_text_from_file(target_file_path, mime)
                
                # Context prefix with filename and logical path
                header = f"File: {name}\nPath: {path}\n\n"
                full_text = header + extracted_text

                chunks = chunk_text(full_text, chunk_size=400, overlap=50)
                chunks_with_vectors = []
                for idx, chunk in enumerate(chunks[:30]):  # Cap at 30 chunks per doc for efficiency
                    vec = model_manager.embed_text(chunk)
                    if vec:
                        chunks_with_vectors.append({
                            "chunk_idx": idx,
                            "snippet": chunk[:300],
                            "vector": vec,
                        })

                if chunks_with_vectors:
                    db.save_text_vectors(file_id, chunks_with_vectors)

                db.upsert_file_metadata(
                    file_id=file_id,
                    source=source,
                    path=path,
                    name=name,
                    mime=mime or "application/octet-stream",
                    ext=ext,
                    modified=modified,
                    size=actual_size,
                    content_hash=content_hash,
                    content_snippet=snippet,
                )
                return True

            # 3. Generic file fallback (media, video, audio, archives, etc.)
            name_desc = f"File: {name}\nPath: {path}\nExtension: {ext}"
            vec = model_manager.embed_text(name_desc)
            if vec:
                db.save_text_vectors(file_id, [{"chunk_idx": 0, "snippet": name, "vector": vec}])

            db.upsert_file_metadata(
                file_id=file_id,
                source=source,
                path=path,
                name=name,
                mime=mime or "application/octet-stream",
                ext=ext,
                modified=modified,
                size=actual_size,
                content_hash=content_hash,
                content_snippet=name,
            )
            return True

        finally:
            # Enforce deletion of temporary downloaded cloud files
            if temp_file_created and target_file_path and target_file_path.exists():
                try:
                    os.unlink(target_file_path)
                except Exception as e:
                    logger.warning(f"Could not remove temp file {target_file_path}: {e}")

    def crawl_local_sources(self):
        """Crawls user folders and local directories with priority order."""
        user_home = Path.home()
        priority_dirs = [
            Path("./local_storage").resolve(),
            user_home / "Documents",
            user_home / "Desktop",
            user_home / "Downloads",
            user_home / "Pictures",
            user_home / "Videos",
            user_home / "Music",
        ]

        # System/temp extensions to ignore
        skip_exts = {".tmp", ".temp", ".log", ".bak", ".dll", ".sys", ".ini", ".lnk", ".dat", ".cache"}

        scanned = set()
        for root_dir in priority_dirs:
            if not root_dir.exists():
                continue
            for root, dirs, files in os.walk(root_dir):
                # Filter out junk directories in-place
                dirs[:] = [d for d in dirs if not self._should_skip_path(Path(root) / d)]
                
                for f_name in files:
                    file_path = Path(root) / f_name
                    if file_path in scanned or self._should_skip_path(file_path):
                        continue
                    scanned.add(file_path)

                    ext = file_path.suffix.lower()
                    if ext in skip_exts:
                        continue

                    try:
                        stat = file_path.stat()
                        mtime_iso = datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat()
                        file_id = f"local_{hashlib.md5(str(file_path).encode('utf-8')).hexdigest()}"
                        
                        with self._lock:
                            self.indexing_status["current_file"] = f_name
                            self.indexing_status["total_scanned"] += 1

                        ok = self.index_single_file(
                            file_id=file_id,
                            source="local",
                            name=f_name,
                            path=str(file_path),
                            local_path=file_path,
                            modified=mtime_iso,
                            size=stat.st_size,
                        )
                        if ok:
                            with self._lock:
                                self.indexing_status["indexed_count"] += 1
                                self.indexing_status["by_source"]["local"] += 1
                    except Exception as e:
                        with self._lock:
                            self.indexing_status["error_count"] += 1

    async def crawl_cloud_sources(self, credentials_map: Dict[str, Dict[str, Any]]):
        """Crawls connected cloud sources using existing providers."""
        from backend.app.providers.manager import provider_manager

        for provider_name, creds in credentials_map.items():
            if provider_name == "local":
                continue
            try:
                files: List[FileRecord] = await provider_manager.list_files(
                    provider_name=provider_name,
                    limit=100,
                    credentials=creds,
                )
                for f in files:
                    if f.is_folder:
                        continue
                    ext = (f.extension or "").lower()
                    if ext not in DOC_EXTS and ext not in IMAGE_EXTS:
                        continue

                    with self._lock:
                        self.indexing_status["current_file"] = f.name
                        self.indexing_status["total_scanned"] += 1

                    # Download binary content for local embedding, then immediately delete
                    file_bytes = None
                    try:
                        file_bytes, _, _ = await provider_manager.download_file(
                            provider_name=provider_name,
                            file_id=f.provider_file_id,
                            credentials=creds,
                        )
                    except Exception as e:
                        logger.warning(f"Could not download {f.name} from {provider_name}: {e}")

                    mod_str = f.modified_at.isoformat() if f.modified_at else None
                    ok = self.index_single_file(
                        file_id=f.id,
                        source=provider_name,
                        name=f.name,
                        path=f.path or f"/{f.name}",
                        file_bytes=file_bytes,
                        mime=f.mime_type,
                        modified=mod_str,
                        size=f.size,
                        content_hash=f.content_hash,
                    )
                    if ok:
                        with self._lock:
                            self.indexing_status["indexed_count"] += 1
                            self.indexing_status["by_source"][provider_name] = (
                                self.indexing_status["by_source"].get(provider_name, 0) + 1
                            )
            except Exception as e:
                logger.error(f"Error crawling cloud provider {provider_name}: {e}")

    def run_full_index(self, credentials_map: Optional[Dict[str, Dict[str, Any]]] = None):
        """Runs complete indexing pass across local and cloud sources in background."""
        def _task():
            with self._lock:
                self.indexing_status["status"] = "indexing"
            try:
                # 1. Local crawl
                self.crawl_local_sources()
                # 2. Cloud crawl if event loop is available
                if credentials_map:
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(self.crawl_cloud_sources(credentials_map))
                        loop.close()
                    except Exception as e:
                        logger.warning(f"Cloud crawl loop error: {e}")
            finally:
                with self._lock:
                    self.indexing_status["status"] = "idle"
                    self.indexing_status["current_file"] = ""
                    self.indexing_status["last_indexed_at"] = datetime.now(timezone.utc).isoformat()

        thread = threading.Thread(target=_task, daemon=True)
        thread.start()
        return thread

    def start_local_watcher(self):
        """Starts watchdog filesystem watcher for local directories."""
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler

            class ChangeHandler(FileSystemEventHandler):
                def __init__(self, indexer):
                    self.indexer = indexer

                def on_modified(self, event):
                    if not event.is_directory:
                        p = Path(event.src_path)
                        if p.suffix.lower() in DOC_EXTS | IMAGE_EXTS:
                            time.sleep(0.5)  # Let write settle
                            file_id = f"local_{hashlib.md5(str(p).encode('utf-8')).hexdigest()}"
                            try:
                                stat = p.stat()
                                self.indexer.index_single_file(
                                    file_id=file_id,
                                    source="local",
                                    name=p.name,
                                    path=str(p),
                                    local_path=p,
                                    modified=datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                                    size=stat.st_size,
                                )
                            except Exception:
                                pass

                def on_created(self, event):
                    self.on_modified(event)

            self._watcher = Observer()
            watch_path = Path("./local_storage").resolve()
            watch_path.mkdir(parents=True, exist_ok=True)
            self._watcher.schedule(ChangeHandler(self), str(watch_path), recursive=True)
            self._watcher.start()
            logger.info(f"Local filesystem watcher active on {watch_path}")
        except Exception as e:
            logger.warning(f"Could not start filesystem watcher: {e}")


indexer = LocalIndexer()
