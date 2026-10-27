@echo off
title FastAPI Backend (Port 8000)
color 09
cd /d "%~dp0"
echo ===================================================
echo Starting FastAPI Backend on http://127.0.0.1:8000...
echo Swagger Docs: http://127.0.0.1:8000/docs
echo ===================================================
set "PYTHONPATH=%~dp0"
"%~dp0venv\Scripts\python.exe" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
pause
