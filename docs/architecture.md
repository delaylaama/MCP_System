# System Architecture & Development Plan
## Universal AI File Manager: An MCP-Based Platform for Intelligent Multi-Cloud File Search and Retrieval

---

## 1. Architectural Philosophy

The core architectural tenet of this platform is: **MCP Does Not Replace Provider APIs; MCP Standardizes the Tool Layer for AI Agents**.

```
+-------------------------------------------------------------------+
|                        PRESENTATION TIER                         |
| React 19 + Vite + React Router + Axios (Responsive UI / SPA)      |
+---------------------------------+---------------------------------+
                                  | REST / JSON / Bearer JWT
+---------------------------------v---------------------------------+
|                         APPLICATION TIER                          |
|                       FastAPI 0.115+ (Async)                      |
|                                                                   |
| +---------------------+   +-----------------+   +---------------+ |
| | Auth / User Service |   | Provider Mgmt   |   | Hybrid Search | |
| +---------------------+   +-----------------+   +---------------+ |
|            |                                            |         |
| +----------v----------+                   +-------------v-------+ |
| | PostgreSQL / SQLite |                   | Ranking Engine      | |
| +---------------------+                   +-------------+-------+ |
|                                                         |         |
|                          +------------------------------+         |
|                          | AI Service (Intent & LLM)              |
|                          +--------------+-------------------------+ |
|                                         |                         |
|                          +--------------v-------------------------+ |
|                          | MCP Client (Official SDK v2)           |
|                          +--------------+-------------------------+ |
+-----------------------------------------|-------------------------+
                                          | MCP Protocol (Streamable HTTP)
+-----------------------------------------v-------------------------+
|                         MCP SERVER TIER                           |
| MCP Server (FastMCP / Official Python MCP SDK v2)                 |
| - search_files                                                    |
| - list_files                                                      |
| - get_file_metadata                                               |
| - download_file                                                   |
| - get_file_content                                                |
| - find_duplicates                                                 |
|                                 |                                 |
|                     +-----------v------------+                    |
|                     | ProviderManager Service|                    |
|                     +-----------+------------+                    |
+---------------------------------|---------------------------------+
                                  | Provider Protocol
+---------------------------------v---------------------------------+
|                     PROVIDER ADAPTERS TIER                        |
|                                                                   |
| +-------------------+ +-------------------+ +-------------------+ |
| | GoogleDriveAdapter| | OneDriveAdapter   | | DropboxAdapter    | |
| | (Google Drive v3) | | (Microsoft Graph) | | (Dropbox API v2)  | |
| +---------+---------+ +---------+---------+ +---------+---------+ |
|           |                     |                     |           |
|           |           +---------v---------+           |           |
|           |           | LocalFileAdapter  |           |           |
|           |           | (OS sandboxed)    |           |           |
|           |           +---------+---------+           |           |
+-----------|---------------------|---------------------|-----------+
            |                     |                     |
            v                     v                     v
     Google Drive API       MS Graph API           Dropbox API
```

---

## 2. Component Specifications

### 2.1 FastAPI Backend
- **Framework**: FastAPI with asynchronous route handlers and dependency injection.
- **ORM**: SQLAlchemy 2.0 with asynchronous engine (`AsyncSession`), mapped declarative models, and Alembic database migrations.
- **Security**: Argon2 password hashing for credentials, JWT tokens (HS256) for session management, and Fernet (AES-256-CBC with HMAC) encryption for all OAuth access tokens and refresh tokens stored in the database.
- **AI Service**: LLM integration abstraction (`LLMService`) supporting dynamic tool selection, parameter generation, and natural-language synthesis.
- **Search & Ranking Service**: Multi-stage retrieval combining keyword matching, vector similarity (ChromaDB), recency scoring, and exact filename relevance.

### 2.2 Model Context Protocol (MCP) Server & Client
- **Protocol**: Official Python MCP SDK v2.
- **Transport**: Streamable HTTP / Server-Sent Events (SSE) over HTTP (`http://localhost:8001/mcp`).
- **Tools Exposed**:
  1. `search_files(query, provider=None, file_type=None, modified_after=None, modified_before=None, user_id=None)`
  2. `list_files(provider=None, folder_id=None, limit=50, user_id=None)`
  3. `get_file_metadata(file_id, provider, user_id=None)`
  4. `get_file_content(file_id, provider, user_id=None, max_bytes=1048576)`
  5. `download_file(file_id, provider, user_id=None)`
  6. `find_duplicates(provider=None, user_id=None)`
- **Independence**: The MCP server interfaces solely through `ProviderManager` and standardized `FileRecord` schemas, completely isolated from frontend details and proprietary LLM abstractions.

### 2.3 Provider Abstraction (`BaseProvider`)
All providers adhere to an asynchronous abstract base class:
```python
class BaseProvider(ABC):
    @abstractmethod
    async def search_files(self, query: str, filters: dict, credentials: dict) -> list[FileRecord]: ...
    @abstractmethod
    async def list_files(self, folder_id: str | None, limit: int, credentials: dict) -> list[FileRecord]: ...
    @abstractmethod
    async def get_file_metadata(self, file_id: str, credentials: dict) -> FileRecord: ...
    @abstractmethod
    async def download_file(self, file_id: str, credentials: dict) -> tuple[bytes, str, str]: ...
    @abstractmethod
    async def get_file_content(self, file_id: str, credentials: dict, max_bytes: int) -> str: ...
```

---

## 3. Step-by-Step Implementation Roadmap

| Step | Phase | Key Deliverables | Status |
|:---:|:---|:---|:---:|
| **1** | Repository Inspection | Analyze existing code, directory mapping, verify environment | COMPLETED |
| **2** | Project Scaffolding | Requirements, .env, docker-compose, directory tree, documentation | IN PROGRESS |
| **3** | Database & Models | SQLAlchemy async models (User, ProviderConnection, FileMetadata, SearchHistory), Alembic | PENDING |
| **4** | Authentication | JWT authentication, Argon2 hashing, register, login, me, protected routes | PENDING |
| **5** | Local Provider | Sandboxed `LocalFileProvider` with path-traversal protection and hash calculation | PENDING |
| **6** | MCP Server | Official SDK v2 FastMCP/Server with Streamable HTTP transport and tools | PENDING |
| **7** | MCP Client | Async MCP Client with tool discovery, connection health checks, invocation | PENDING |
| **8** | Backend ↔ MCP Integration | FastAPI router triggering MCP tools via MCP client | PENDING |
| **9** | AI & LLM Service | Pluggable LLMService (OpenAI, Gemini, fallback heuristic agent) | PENDING |
| **10**| AI Search Flow | Full pipeline: natural language query -> LLM tool selection -> MCP -> Provider -> Results | PENDING |
| **11**| Google Drive Integration | Real Google OAuth 2.0 flow + Google Drive API v3 adapter | PENDING |
| **12**| OneDrive Integration | Real Microsoft identity OAuth 2.0 + Microsoft Graph DriveItem adapter | PENDING |
| **13**| Dropbox Integration | Real Dropbox OAuth 2.0 + Dropbox API v2 adapter | PENDING |
| **14**| Unified Cross-Provider Search | Normalized multi-provider concurrent search orchestration | PENDING |
| **15**| File Metadata & Storage | Database-backed file metadata caching and sync | PENDING |
| **16**| File Content & Download | Streaming download proxy and preview endpoint | PENDING |
| **17**| Document Extraction | PyPDF, python-docx, markdown, plain text parser pipeline | PENDING |
| **18**| Vector Indexing | ChromaDB vector indexing and chunking engine | PENDING |
| **19**| Semantic Search | Cosine similarity vector search on document contents | PENDING |
| **20**| Hybrid Search & Ranking | Configurable weighted ranking (keyword + semantic + recency + exact match) | PENDING |
| **21**| Duplicate Detection | Multi-cloud SHA-256 hash matching and grouping | PENDING |
| **22**| Frontend Refinement | Connect React UI to real backend endpoints via Axios and state management | PENDING |
| **23**| Search History | Persistent search history with result count and deletion | PENDING |
| **24**| Automated Testing | Pytest suite covering Auth, Providers, MCP, and Search | PENDING |
| **25**| Research & Benchmarks | Experimental harness comparing Direct API vs. MCP overhead | PENDING |
