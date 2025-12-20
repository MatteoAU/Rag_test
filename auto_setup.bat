@echo off
setlocal
title RAG Project Setup

echo ==========================================
echo       RAG SYSTEM SETUP AUTOMATION
echo ==========================================
echo.

:: 1. Check/Install Python Dependencies
echo [1/4] Checking Python environment...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH.
    pause
    exit /b 1
)

if not exist "RAG\.venv" (
    echo    - Creating virtual environment in RAG directory...
    python -m venv RAG\.venv
) else (
    echo    - Virtual environment found in RAG directory.
)

echo    - Installing requirements...
:: Activate venv and install
call RAG\.venv\Scripts\activate
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error: Failed to install Python requirements.
    pause
    exit /b 1
)
echo    - Python setup complete.
echo.

:: 2. Setup Environment Variables
echo [2/4] Setting up Environment Variables...
if not exist ".env" (
    echo    - Creating .env from .env.example...
    copy .env.example .env >nul
    echo    PLEASE UPDATE .env WITH YOUR CONFIGURATION!
) else (
    echo    - .env file already exists.
)
echo.

:: 3. Setup Frontend
echo [3/4] Setting up Frontend...
cd Front-end
if not exist "node_modules" (
    echo    - Installing npm dependencies...
    call npm install
) else (
    echo    - Node modules found, skipping install.
)
cd ..
echo    - Frontend setup complete.
echo.

:: 4. Setup Docker
echo [4/4] Setting up Docker Containers...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Warning: Docker is not running or not installed. Skipping container pull.
) else (
    echo    - Pulling latest images...
    docker-compose pull
)

echo.
echo ==========================================
echo           SETUP COMPLETED!
echo ==========================================
echo You can now run 'auto_start.bat' to launch the system.
echo.
pause
