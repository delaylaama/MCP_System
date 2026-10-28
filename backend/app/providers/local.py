"""Local Filesystem Provider Adapter with system drives support and sandboxed access."""

import os
import asyncio
import string
import shutil
import ctypes
import hashlib
import mimetypes
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
from backend.app.providers.base import BaseProvider
from backend.app.schemas.file import FileRecord
from backend.app.core.config import get_settings
from backend.app.core.logging import logger

settings = get_settings()


class LocalFileProvider(BaseProvider):
    provider_name = "local"

    def __init__(self, root_path: Optional[str] = None):
        base_dir = root_path or settings.LOCAL_STORAGE_ROOT
        self.root_path = Path(base_dir).resolve()
        self.root_path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def get_system_drives() -> List[Dict[str, Any]]:
        """Returns all system drives (C:, D:, etc.) with volume label, usage, and format."""
        drives = []
        if os.name == "nt":
            kernel32 = ctypes.windll.kernel32
            for letter in string.ascii_uppercase:
                drive_root = f"{letter}:\\"
                if os.path.exists(drive_root):
                    try:
                        vol_name = ctypes.create_unicode_buffer(1024)
                        fs_name = ctypes.create_unicode_buffer(1024)
                        kernel32.GetVolumeInformationW(
                            ctypes.c_wchar_p(drive_root),
                            vol_name,
                            ctypes.sizeof(vol_name),
                            None, None, None,
                            fs_name,
                            ctypes.sizeof(fs_name),
                        )
                        label = vol_name.value or f"Local Disk ({letter}:)"
                        fs = fs_name.value or "NTFS"
                        total, used, free = shutil.disk_usage(drive_root)
                        percent = round((used / total) * 100, 1) if total > 0 else 0.0
                        drives.append({
                            "drive": f"{letter}:",
                            "root": drive_root,
                            "label": label,
                            "display_name": f"{label} ({letter}:)",
                            "file_system": fs,
                            "total_bytes": total,
                            "used_bytes": used,
                            "free_bytes": free,
                            "used_percent": percent,
                            "is_system": letter.upper() == "C",
                        })
                    except Exception as e:
                        logger.warning(f"Error querying drive {drive_root}: {e}")
        else:
            try:
                total, used, free = shutil.disk_usage("/")
                percent = round((used / total) * 100, 1) if total > 0 else 0.0
                drives.append({
                    "drive": "/",
                    "root": "/",
                    "label": "Root",
                    "display_name": "Root (/)",
                    "file_system": "ext4",
                    "total_bytes": total,
                    "used_bytes": used,
                    "free_bytes": free,
                    "used_percent": percent,
                    "is_system": True,
                })
            except Exception:
                pass
        return drives

    def _resolve_safe_path(self, relative_or_absolute: str) -> Path:
        """
        Resolves path. If path specifies a drive or absolute path, validates that it points to a real drive path.
        Otherwise resolves within self.root_path.
        """
        raw = relative_or_absolute.replace("\\", "/")
        # Decode drive prefixes e.g. "D__" or "D_/" -> "D:/"
        if len(raw) >= 3 and raw[0].isalpha() and raw[1:3] in ["__", "_/"]:
            raw = f"{raw[0]}:/{raw[3:]}"
        elif len(raw) >= 2 and raw[0].isalpha() and raw[1] == ':':
            pass
        elif raw.startswith("/"):
            parts = raw.strip("/").split("/")
            if parts and len(parts[0]) == 2 and parts[0][1] == ':':
                raw = "/".join(parts)
            elif parts and len(parts[0]) == 1 and len(parts) > 1 and parts[0].isalpha():
                raw = f"{parts[0]}:/{'/'.join(parts[1:])}"

        p = Path(raw)
        if p.is_absolute() and p.exists():
            return p.resolve()

        clean_input = raw.lstrip("/")
        candidate = (self.root_path / clean_input).resolve()
        return candidate

    def _compute_hash(self, file_path: Path) -> str:
        """Computes SHA-256 hash for file content."""
        hasher = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception:
            return ""

    def _to_file_record(self, file_path: Path, compute_hash: bool = False) -> FileRecord:
        try:
            rel_path = file_path.relative_to(self.root_path).as_posix()
            file_id_key = rel_path
        except ValueError:
            posix_path = file_path.as_posix()
            file_id_key = posix_path.replace(":", "_")
            rel_path = posix_path

        is_dir = file_path.is_dir()
        try:
            stat = file_path.stat()
            size = 0 if is_dir else stat.st_size
            mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
            ctime = datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc)
        except Exception:
            size = 0
            mtime = datetime.now(timezone.utc)
            ctime = mtime

        mime_type, _ = mimetypes.guess_type(file_path.name)
        if is_dir:
            mime_type = "inode/directory"
        elif not mime_type:
            mime_type = "application/octet-stream"

        ext = file_path.suffix.lower() if not is_dir else ""
        content_hash = self._compute_hash(file_path) if compute_hash and not is_dir and size < 10_000_000 else None

        return FileRecord(
            id=f"local_{file_id_key}",
            provider="local",
            provider_file_id=file_id_key,
            name=file_path.name,
            path=rel_path if rel_path.startswith("/") else f"/{rel_path}",
            mime_type=mime_type,
            extension=ext,
            size=size,
            created_at=ctime,
            modified_at=mtime,
            web_url=f"/api/files/local_{file_id_key}/download",
            downloadable=not is_dir,
            is_folder=is_dir,
            content_available=ext in [".txt", ".md", ".json", ".csv", ".py", ".pdf", ".docx"],
            content_hash=content_hash,
            metadata={"absolute_path": str(file_path)},
        )

    def browse_path(self, target_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Browses local filesystem.
        If target_path is None or empty or 'root': returns all system drives and project storage folder.
        If target_path is a directory: returns child folders and files.
        """
        if not target_path or target_path.strip().lower() in ["root", "", "/"]:
            drives = self.get_system_drives()
            drive_items = []
            for d in drives:
                drive_items.append({
                    "id": f"local_{d['drive'][0]}__",
                    "name": d["display_name"],
                    "path": d["root"].replace("\\", "/"),
                    "is_folder": True,
                    "is_drive": True,
                    "drive_letter": d["drive"],
                    "file_system": d["file_system"],
                    "size": d["used_bytes"],
                    "total_size": d["total_bytes"],
                    "free_size": d["free_bytes"],
                    "used_percent": d["used_percent"],
                    "extension": "",
                    "mime_type": "inode/drive",
                    "modified_at": datetime.now(timezone.utc).isoformat(),
                })

            try:
                local_files = [f for f in self.root_path.rglob("*") if f.is_file()]
                local_size = sum(f.stat().st_size for f in local_files)
            except Exception:
                local_files = []
                local_size = 0

            drive_items.append({
                "id": "local_project_storage",
                "name": "Project Storage (./local_storage)",
                "path": self.root_path.as_posix(),
                "is_folder": True,
                "is_drive": False,
                "size": local_size,
                "file_count": len(local_files),
                "extension": "",
                "mime_type": "inode/directory",
                "modified_at": datetime.now(timezone.utc).isoformat(),
            })

            return {
                "current_path": "root",
                "parent_path": None,
                "is_root": True,
                "items": drive_items,
            }

        resolved = self._resolve_safe_path(target_path)
        if not resolved.exists() or not resolved.is_dir():
            raise FileNotFoundError(f"Directory not found: {target_path}")

        parent_path = None
        try:
            p_parent = resolved.parent
            if p_parent != resolved:
                parent_path = p_parent.as_posix()
            else:
                parent_path = "root"
        except Exception:
            parent_path = "root"

        folders = []
        files = []

        try:
            with os.scandir(resolved) as scanner:
                for entry in scanner:
                    if entry.name.startswith("$") or entry.name in ["System Volume Information", "pagefile.sys", "hiberfil.sys", "swapfile.sys"]:
                        continue
                    try:
                        is_dir = entry.is_dir(follow_symlinks=False)
                        st = entry.stat(follow_symlinks=False)
                        mtime = datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat()
                        ext = Path(entry.name).suffix.lower() if not is_dir else ""
                        mime, _ = mimetypes.guess_type(entry.name)
                        clean_key = Path(entry.path).as_posix().replace(":", "_")

                        item = {
                            "id": f"local_{clean_key}",
                            "name": entry.name,
                            "path": Path(entry.path).as_posix(),
                            "is_folder": is_dir,
                            "size": 0 if is_dir else st.st_size,
                            "extension": ext,
                            "mime_type": "inode/directory" if is_dir else (mime or "application/octet-stream"),
                            "modified_at": mtime,
                        }
                        if is_dir:
                            folders.append(item)
                        else:
                            files.append(item)
                    except (PermissionError, FileNotFoundError, OSError):
                        continue
        except PermissionError:
            raise PermissionError(f"Access denied to folder {resolved}")

        folders.sort(key=lambda x: x["name"].lower())
        files.sort(key=lambda x: x["name"].lower())

        return {
            "current_path": resolved.as_posix(),
            "parent_path": parent_path,
            "is_root": False,
            "items": folders + files,
        }

    async def list_files(
        self,
        folder_id: Optional[str] = None,
        limit: int = 100,
        credentials: Optional[Dict[str, Any]] = None,
    ) -> List[FileRecord]:
        target_dir = self._resolve_safe_path(folder_id) if folder_id else self.root_path
        if not target_dir.is_dir():
            return []

        records = []
        for entry in target_dir.iterdir():
            if entry.name.startswith("$") or entry.name in ["System Volume Information"]:
                continue
            try:
                records.append(self._to_file_record(entry))
                if len(records) >= limit:
                    break
            except Exception as e:
                logger.error(f"Error reading file entry {entry}: {e}")
        return records

    async def search_files(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        credentials: Optional[Dict[str, Any]] = None,
    ) -> List[FileRecord]:
        return await asyncio.to_thread(self._sync_search_files, query, filters)

    def _sync_search_files(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[FileRecord]:
        import re
        from backend.app.utils.query_parser import extract_terms, compute_term_match, clean_query_text

        query_lower = query.lower().strip()
        query_terms = extract_terms(query, keep_recency=True)
        query_clean = clean_query_text(query)
        file_type_filter = filters.get("file_type") if filters else None
        modified_after = filters.get("modified_after") if filters else None
        modified_before = filters.get("modified_before") if filters else None

        is_wildcard = (
            not query_lower
            or query_lower in ["*", "all", "all files", "local", "local storage", "local_storage", "local files"]
        )

        # Determine local directory roots to search across C: and D: drives
        search_dirs = []
        home = Path.home()
        folder_target = (filters.get("folder") or "").lower().strip() if filters else ""

        # 1. Targeted folder/drive if explicitly specified in query
        if folder_target:
            if "download" in folder_target:
                p = home / "Downloads"
                if p.exists():
                    search_dirs.append((p, 4))
            elif "document" in folder_target:
                p = home / "Documents"
                if p.exists():
                    search_dirs.append((p, 4))
            elif "desktop" in folder_target:
                p = home / "Desktop"
                if p.exists():
                    search_dirs.append((p, 4))
            elif "d:" in folder_target or "d drive" in folder_target or folder_target == "d":
                p = Path("D:/")
                if p.exists():
                    search_dirs.append((p, 3))
            elif "c:" in folder_target or "c drive" in folder_target or folder_target == "c":
                for f_name in ["Downloads", "Documents", "Desktop"]:
                    p = home / f_name
                    if p.exists():
                        search_dirs.append((p, 4))

        # 2. General search: traverse standard user directories on C: drive, project storage, and D: drive
        if not search_dirs:
            # User profile primary folders on C: drive
            for f_name in ["Downloads", "Documents", "Desktop"]:
                f_path = home / f_name
                if f_path.exists() and f_path.is_dir():
                    search_dirs.append((f_path, 3))

            # Project storage root
            if self.root_path.exists():
                search_dirs.append((self.root_path, 99))

            # System drives (e.g. D:, E:)
            for letter in ["D", "E"]:
                d_path = Path(f"{letter}:/")
                if d_path.exists():
                    search_dirs.append((d_path, 2))

        results = []
        seen_paths = set()

        for base_dir, max_depth in search_dirs:
            if len(results) >= 50:
                break
            for root, dirs, files in os.walk(base_dir):
                if len(results) >= 50:
                    break
                # Prune non-user/hidden folders
                dirs[:] = [
                    d for d in dirs
                    if not d.startswith((".", "$")) and d not in ["System Volume Information", "node_modules", "venv", "env", "AppData", "__pycache__"]
                ]
                try:
                    rel_parts = Path(root).relative_to(base_dir).parts
                    if len(rel_parts) >= max_depth:
                        dirs.clear()
                except ValueError:
                    pass

                for file_name in files:
                    if len(results) >= 50:
                        break
                    if file_name.startswith((".", "$")):
                        continue
                    file_path = Path(root) / file_name
                    str_path = str(file_path.resolve())
                    if str_path in seen_paths:
                        continue
                    seen_paths.add(str_path)

                    if file_type_filter:
                        clean_ext = file_type_filter.lower().lstrip(".")
                        image_exts = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg", ".tiff"}
                        doc_exts = {".pdf", ".docx", ".doc", ".txt", ".rtf", ".odt", ".md"}
                        sheet_exts = {".xlsx", ".xls", ".csv"}
                        fn_ext = Path(file_name).suffix.lower()
                        if clean_ext in ["image", "images", "photo", "photos", "picture", "pictures"]:
                            if fn_ext not in image_exts:
                                continue
                        elif clean_ext in ["document", "documents", "doc", "docs"]:
                            if fn_ext not in doc_exts:
                                continue
                        elif clean_ext in ["sheet", "sheets", "spreadsheet", "spreadsheets"]:
                            if fn_ext not in sheet_exts:
                                continue
                        elif not file_name.lower().endswith(f".{clean_ext}"):
                            continue

                    q_compact = re.sub(r"[^a-z0-9]", "", query_lower)
                    f_compact = re.sub(r"[^a-z0-9]", "", file_name.lower())
                    file_clean = re.sub(r"[_\-\s]+", " ", file_name.lower())

                    name_match = False
                    if is_wildcard:
                        name_match = True
                    elif (q_compact and q_compact in f_compact) or (query_clean and (query_clean in file_clean or query_clean in file_name.lower())):
                        name_match = True
                    else:
                        is_hit, coverage = compute_term_match(query_terms, file_clean)
                        if is_hit:
                            name_match = True

                    content_match = False
                    if not name_match and not is_wildcard and file_path.suffix.lower() in [".txt", ".md", ".json", ".csv", ".py"]:
                        try:
                            if file_path.stat().st_size < 100_000:
                                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                                    c = f.read(50000).lower()
                                    if query_clean and query_clean in c:
                                        content_match = True
                                    else:
                                        is_hit, _ = compute_term_match(query_terms, c)
                                        if is_hit:
                                            content_match = True
                        except Exception:
                            pass

                    if name_match or content_match:
                        try:
                            record = self._to_file_record(file_path, compute_hash=False)
                            if modified_after and record.modified_at and record.modified_at < modified_after:
                                continue
                            if modified_before and record.modified_at and record.modified_at > modified_before:
                                continue
                            results.append(record)
                        except Exception:
                            pass
        return results

    async def get_file_metadata(
        self,
        file_id: str,
        credentials: Optional[Dict[str, Any]] = None,
    ) -> FileRecord:
        clean_id = file_id.removeprefix("local_")
        target_path = self._resolve_safe_path(clean_id)
        if not target_path.exists():
            raise FileNotFoundError(f"File not found: {clean_id}")
        return self._to_file_record(target_path)

    async def get_file_content(
        self,
        file_id: str,
        credentials: Optional[Dict[str, Any]] = None,
        max_bytes: int = 1048576,
    ) -> str:
        clean_id = file_id.removeprefix("local_")
        target_path = self._resolve_safe_path(clean_id)
        if not target_path.is_file():
            raise FileNotFoundError(f"File not found: {clean_id}")

        ext = target_path.suffix.lower()
        if ext in [".txt", ".md", ".json", ".csv", ".py", ".html", ".css", ".js", ".env", ".bat", ".sh", ".yaml", ".yml"]:
            with open(target_path, "r", encoding="utf-8", errors="replace") as f:
                return f.read(max_bytes)
        elif ext == ".pdf":
            try:
                import pypdf
                reader = pypdf.PdfReader(target_path)
                text = "\n".join(page.extract_text() or "" for page in reader.pages)
                return text[:max_bytes]
            except Exception as e:
                logger.error(f"PDF extraction error on {target_path}: {e}")
                return ""
        elif ext == ".docx":
            try:
                import docx
                doc = docx.Document(target_path)
                text = "\n".join(p.text for p in doc.paragraphs)
                return text[:max_bytes]
            except Exception as e:
                logger.error(f"DOCX extraction error on {target_path}: {e}")
                return ""
        return ""

    async def download_file(
        self,
        file_id: str,
        credentials: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bytes, str, str]:
        clean_id = file_id.removeprefix("local_")
        target_path = self._resolve_safe_path(clean_id)
        if not target_path.is_file():
            raise FileNotFoundError(f"File not found: {clean_id}")

        with open(target_path, "rb") as f:
            data = f.read()

        mime_type, _ = mimetypes.guess_type(target_path.name)
        return data, target_path.name, mime_type or "application/octet-stream"
