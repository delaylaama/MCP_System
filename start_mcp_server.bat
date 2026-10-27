@echo off
title FastMCP Protocol Server (Port 8001)
color 0A
cd /d "%~dp0"
echo ===================================================
echo Starting FastMCP Protocol Server...
echo Endpoint: http://127.0.0.1:8001/mcp
echo ===================================================
set "PYTHONPATH=%~dp0"
"%~dp0venv\Scripts\python.exe" -m mcp_server.server
pause
