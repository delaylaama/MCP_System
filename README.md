# Universal AI File Manager: An MCP-Based Platform for Intelligent Multi-Cloud File Search and Retrieval

A production-grade final-year Computer Science project implementing an intelligent multi-cloud file search and retrieval system using the **Model Context Protocol (MCP)**.

---

## 1. System Overview

Universal AI File Manager connects multiple cloud storage providers (**Google Drive**, **Microsoft OneDrive**, **Dropbox**) and **Local Filesystem** under a unified AI-driven search interface. Rather than coupling search algorithms or LLM logic directly to proprietary provider APIs, the system utilizes the official **Model Context Protocol (MCP)** as a standardized tool execution and communication layer.

```
                     USER
                       │
                       ▼
              ┌───────────────────┐
              │   React Frontend  │
              └─────────┬─────────┘
                        │ REST API / JWT
                        ▼
              ┌───────────────────┐
              │  FastAPI Backend  │
              └─────────┬─────────┘
                        │
          ┌─────────────┴─────────────┐
          ▼                           ▼
    Authentication               AI Service (LLM)
    (JWT / OAuth)                     │
                                      ▼
                                 MCP Client
                                      │ MCP Protocol (HTTP Streamable / SSE)
                                      ▼
                                 MCP Server
                                      │
                 ┌────────────────────┼────────────────────┐
                 ▼                    ▼                    ▼
           Google Drive          OneDrive (Graph)       Dropbox
            (Drive API)             (Graph API)          (API v2)
                 │                    │                    │
                 └────────────────────┼────────────────────┘
                                      ▼
                               Local Filesystem
```

---

## 2. Key Features

- **Standardized MCP Architecture**: MCP Python SDK v2 integration running via Streamable HTTP.
- **Multi-Cloud Integration**: Real OAuth 2.0 flows and API integrations with Google Drive, Microsoft OneDrive (Microsoft Graph), Dropbox, and Local Storage.
- **Unified File Model**: Normalized metadata schema across all providers (ID, name, path, mime type, size, modified date, web URL, download capability).
- **AI-Powered Natural Language Search**: Intent resolution, automated MCP tool selection, structured filter extraction, and contextual response synthesis.
- **Hybrid Retrieval & Configurable Ranking**: Combines keyword matching (BM25/fuzzy), semantic vector similarity (ChromaDB / embeddings), and recency weighting into an auditable scoring engine.
- **Text Extraction & Vector Indexing**: Automatic chunking and indexing for PDF, DOCX, TXT, and Markdown files.
- **Duplicate File Detection**: Multi-provider content hashing (SHA-256) and metadata matching to identify exact duplicates across cloud boundaries.
- **Security & Token Encryption**: Fernet (AES-256) encryption for all OAuth access and refresh tokens stored at rest. JWT authentication with Argon2/bcrypt password hashing.
- **Comprehensive Research Benchmarks**: Comparative evaluation framework between direct traditional APIs vs. MCP integration.

---

## 3. Directory Structure

```
├── backend/
│   ├── app/
│   │   ├── api/             # REST endpoints (auth, search, providers, files, history)
│   │   ├── core/            # Config, database, security, logging
│   │   ├── mcp/             # MCP Client & tool dispatch manager
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── oauth/           # Provider-specific OAuth 2.0 flows
│   │   ├── providers/       # Cloud & Local file provider adapters
│   │   ├── repositories/    # Clean DB query layer
│   │   ├── schemas/         # Pydantic v2 schemas
│   │   ├── services/        # Business logic (AI, Search, Ranking, Indexing)
│   │   ├── utils/           # Encryption, file processing, date helpers
│   │   └── main.py          # FastAPI application entrypoint
│   ├── migrations/          # Alembic migrations
│   ├── tests/               # Pytest automated test suite
│   └── requirements.txt
├── mcp_server/
│   ├── schemas/             # Standardized MCP data models
│   ├── services/            # Provider coordination layer
│   ├── tools/               # MCP tools (search_files, list_files, get_metadata, etc.)
│   └── server.py            # MCP server application (SDK v2)
├── src/                     # React + Vite frontend application
│   ├── components/          # Reusable UI components
│   ├── context/             # App & Authentication state
│   ├── pages/               # React views (Dashboard, Search, Providers, Files)
│   ├── routes/              # Application route definitions
│   └── services/            # API client services (Axios)
├── research/                # Empirical evaluation & benchmarking
├── docs/                    # Architectural specs, API references, OAuth setup
├── docker-compose.yml       # Production/development Docker configuration
└── .env.example             # Environment variable template
```

---

## 4. Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (optional, for PostgreSQL)

### 1. Backend Setup
```bash
# Activate virtual environment
python -m venv venv
.\venv\Scripts\activate   # Windows
source venv/bin/activate  # Linux / macOS

# Install backend dependencies
pip install -r backend/requirements.txt

# Copy environment variables
cp .env.example .env

# Run database migrations
alembic -c backend/migrations/alembic.ini upgrade head

# Start MCP Server
python -m mcp_server.server

# Start FastAPI Backend
uvicorn backend.app.main:app --reload --port 8000
```

### 2. Frontend Setup
```bash
npm install
npm run dev
```

Visit `http://localhost:5173` to access the application.

---

## 5. Documentation Links
- [System Architecture](docs/architecture.md)
- [OAuth 2.0 Setup Guide](docs/oauth.md)
- [REST API Reference](docs/api.md)
- [MCP Specification & Tools](docs/mcp.md)
- [Research & Benchmarking](docs/research.md)
- [Development Setup](docs/setup.md)
