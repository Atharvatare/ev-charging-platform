@echo off
title GoBharat EV - Full-Stack Web Server
echo --------------------------------------------------
echo BOOTING GOBHARAT EV FULL-STACK ENGINE...
echo --------------------------------------------------

:: Change directory to where the batch script resides
cd /d "%~dp0"

:: Check if virtual environment exists
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment 'venv' not found!
    echo Please ensure the project dependencies are installed.
    pause
    exit /b
)

:: Set python path and configure secure SECRET_KEY
set PYTHONPATH=.
set SECRET_KEY=7d4b4a11f26a11394c8b2d41b8a5d3c8c24f6ae9bcfd9f4e244fe7ad54b51815

echo [OK] Environment configured.
echo [OK] Launching asynchronous FastAPI server...

:: Open the default web browser to the GoBharat EV landing page in 2 seconds
start "" "http://127.0.0.1:8000/"

:: Start Uvicorn web server process
venv\Scripts\python.exe -m uvicorn app.main:app --port 8000 --reload

pause
