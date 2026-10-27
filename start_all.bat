@echo off
title Universal AI File Manager - Launcher
color 0B
cd /d "%~dp0"

echo =======================================================================
echo          UNIVERSAL AI FILE MANAGER - ALL-IN-ONE LAUNCHER
echo =======================================================================
echo.

REM 1. Verify Virtual Environment
if not exist "%~dp0venv\Scripts\python.exe" (
    color 0C
    echo [ERROR] Python virtual environment not found at: %~dp0venv
    echo Please create the virtual environment first using:
    echo   python -m venv venv
    echo   .\venv\Scripts\pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

REM 2. Verify Node Dependencies
if not exist "%~dp0node_modules" (
    echo [WARNING] node_modules not found. Running npm install...
    call npm install
)

set "PYTHONPATH=%~dp0"

echo [1/3] Starting FastMCP Protocol Server on http://127.0.0.1:8001/mcp ...
start "FastMCP Protocol Server (Port 8001)" /d "%~dp0" cmd /k "title FastMCP Protocol Server (Port 8001) && color 0A && echo =================================================== && echo   FASTMCP PROTOCOL SERVER (Port 8001) && echo   Endpoint: http://127.0.0.1:8001/mcp && echo =================================================== && echo. && "%~dp0venv\Scripts\python.exe" -m mcp_server.server"

REM Wait 3 seconds for MCP server to bind port
ping 127.0.0.1 -n 4 >nul

echo [2/3] Starting FastAPI Backend API on http://127.0.0.1:8000 ...
start "FastAPI Backend API (Port 8000)" /d "%~dp0" cmd /k "title FastAPI Backend API (Port 8000) && color 09 && echo =================================================== && echo   FASTAPI BACKEND API (Port 8000) && echo   Swagger Docs: http://127.0.0.1:8000/docs && echo =================================================== && echo. && "%~dp0venv\Scripts\python.exe" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000"

REM Wait 4 seconds for FastAPI & vector database startup
ping 127.0.0.1 -n 5 >nul

echo [3/3] Starting Vite React Frontend on http://127.0.0.1:5173 ...
start "Vite React Frontend (Port 5173)" /d "%~dp0" cmd /k "title Vite React Frontend (Port 5173) && color 0D && echo =================================================== && echo   VITE REACT FRONTEND (Port 5173) && echo   App URL: http://127.0.0.1:5173 && echo =================================================== && echo. && npm run dev -- --host 127.0.0.1 --port 5173"

REM Wait 3 seconds before opening browser
ping 127.0.0.1 -n 4 >nul

echo.
echo =======================================================================
echo          ALL SERVICES HAVE BEEN SUCCESSFULLY LAUNCHED!
echo =======================================================================
echo   - Web App UI:      http://127.0.0.1:5173
echo   - AI Search:       http://127.0.0.1:5173/ai-search
echo   - 5-Model Lab:     http://127.0.0.1:5173/models
echo   - Backend API:     http://127.0.0.1:8000
echo   - Swagger Docs:    http://127.0.0.1:8000/docs
echo   - FastMCP Server:  http://127.0.0.1:8001/mcp
echo =======================================================================
echo.
echo [INFO] Opening default browser at http://localhost:5173 ...
start http://localhost:5173/

echo.
echo To gracefully stop all 3 services at any time, run:
echo   stop_all.bat
echo =======================================================================
echo You can keep this window open or close it (services run in their windows).
pause
