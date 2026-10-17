@echo off
title MCP Server (Port 8001)
cd /d "%~dp0"
echo ===================================================
echo Starting MCP Server on http://127.0.0.1:8001/mcp...
echo ===================================================
call .\venv\Scripts\activate.bat
python -m mcp_server.server
pause
