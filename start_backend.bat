@echo off
title FastAPI Backend (Port 8000)
cd /d "%~dp0"
echo ===================================================
echo Starting FastAPI Backend on http://localhost:8000...
echo ===================================================
call .\venv\Scripts\activate.bat
uvicorn backend.app.main:app --reload --port 8000
pause
