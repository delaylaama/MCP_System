@echo off
title Launch Universal AI File Manager
cd /d "%~dp0"
echo ===================================================
echo Starting Universal AI File Manager System...
echo ===================================================

echo [1/3] Launching MCP Server (Port 8001)...
start "MCP Server (Port 8001)" cmd /k "call .\venv\Scripts\activate.bat && python -m mcp_server.server"

ping 127.0.0.1 -n 3 >nul

echo [2/3] Launching FastAPI Backend (Port 8000)...
start "FastAPI Backend (Port 8000)" cmd /k "call .\venv\Scripts\activate.bat && uvicorn backend.app.main:app --reload --port 8000"

ping 127.0.0.1 -n 3 >nul

echo [3/3] Launching Vite Frontend (Port 5173)...
start "Vite Frontend (Port 5173)" cmd /k "npm run dev"

echo.
echo ===================================================
echo All services launched in separate windows!
echo - Frontend:   http://localhost:5173
echo - Backend:    http://localhost:8000
echo - API Docs:   http://localhost:8000/docs
echo - MCP Server: http://127.0.0.1:8001/mcp
echo.
echo To stop all services, run stop_all.bat
echo ===================================================
ping 127.0.0.1 -n 5 >nul
