@echo off
title Vite Frontend (Port 5173)
color 0D
cd /d "%~dp0"
echo ===================================================
echo Starting React Vite Frontend on http://127.0.0.1:5173...
echo ===================================================
npm run dev -- --host 127.0.0.1 --port 5173
pause
