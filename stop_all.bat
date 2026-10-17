@echo off
title Stop All Universal AI File Manager Services
echo ===================================================
echo Stopping Universal AI File Manager Services...
echo ===================================================

echo Checking port 8001 (MCP Server)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8001" ^| findstr "LISTENING"') do (
    echo Stopping process PID %%a...
    taskkill /F /PID %%a >nul 2>&1
)

echo Checking port 8000 (FastAPI Backend)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" ^| findstr "LISTENING"') do (
    echo Stopping process PID %%a...
    taskkill /F /PID %%a >nul 2>&1
)

echo Checking port 5173 (Vite Frontend)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5173" ^| findstr "LISTENING"') do (
    echo Stopping process PID %%a...
    taskkill /F /PID %%a >nul 2>&1
)

echo.
echo ===================================================
echo All services have been stopped.
echo ===================================================
pause
