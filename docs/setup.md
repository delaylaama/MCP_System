# Universal AI File Manager: Setup & Installation Guide

This guide walks through configuring and running the complete platform locally and with Docker.

---

## 1. System Requirements

- **Operating System**: Windows 10/11, macOS, or Linux
- **Python**: Version 3.11, 3.12, or 3.13
- **Node.js**: Version 18.x, 20.x, or 22.x (with npm)
- **Database**: PostgreSQL 14+ (or SQLite async for rapid local development)
- **Docker**: Docker Desktop (optional, for containerized deployment)

---

## 2. Environment Configuration

1. Copy the template:
   ```bash
   cp .env.example .env
   ```

2. Review and adjust key configuration settings in `.env`:
   - `ENCRYPTION_KEY`: A Fernet 32-byte URL-safe base64 string.
   - `SECRET_KEY`: A 32+ character random string for signing JWT tokens.
   - `DATABASE_URL`:
     - For PostgreSQL: `postgresql+asyncpg://postgres:postgrespassword@localhost:5432/mcp_file_manager`
     - For SQLite (async): `sqlite+aiosqlite:///./mcp_file_manager.db`
   - `MCP_SERVER_URL`: `http://127.0.0.1:8001/mcp`
   - `LOCAL_STORAGE_ROOT`: Path to local folder containing test documents (default: `./local_storage`)

---

## 3. Local Installation Steps

### Step 3.1: Python Environment & Dependencies
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r backend/requirements.txt
```

### Step 3.2: Database Migrations
```bash
# Apply Alembic database migrations
alembic -c backend/migrations/alembic.ini upgrade head
```

### Step 3.3: Frontend Dependencies
```bash
npm install
```

---

## 4. Running the System Locally

To run the complete system, open three terminal windows (with virtual environment activated):

### Terminal 1: MCP Server
```bash
python -m mcp_server.server
# Runs MCP server on http://127.0.0.1:8001/mcp
```

### Terminal 2: FastAPI Backend
```bash
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
# Runs API server on http://127.0.0.1:8000
# OpenAPI Docs available at: http://127.0.0.1:8000/docs
```

### Terminal 3: React Frontend
```bash
npm run dev
# Starts Vite dev server at http://localhost:5173
```

---

## 5. Docker Deployment

If Docker Desktop is installed:
```bash
# Launch PostgreSQL, MCP Server, Backend, and Frontend
docker-compose up --build
```
