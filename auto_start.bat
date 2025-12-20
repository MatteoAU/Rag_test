@echo off
title RAG System Launcher
setlocal

echo ==========================================
echo         STARTING RAG SYSTEM
echo ==========================================
echo.

:: 1. Start Docker Containers
echo [1/4] Starting Database Services (Qdrant ^& Ollama)...
docker-compose up -d
IF %ERRORLEVEL% NEQ 0 (
    echo Error starting Docker containers. Make sure Docker Desktop is running.
    pause
    exit /b
)
echo Services started.

echo [1.5/4] Ensuring AI Models are ready (this might take a while on first run)...
echo Pulling embedding model (nomic-embed-text)...
docker exec rag_ollama ollama pull nomic-embed-text
echo Pulling chat model (llama3.2)...
docker exec rag_ollama ollama pull llama3.2
echo Models ready.
echo.

:: 2. Start Backend
echo [2/4] Starting Backend (FastAPI)...
start "RAG Backend" cmd /k "call .venv\Scripts\activate && uvicorn RAG.Controller.controller:app --reload"
echo Backend launched in new window.
echo.

:: 3. Start Frontend
echo [3/4] Starting Frontend (Vite)...
cd Front-end
start "RAG Frontend" cmd /k "npm run dev"
cd ..
echo Frontend launched in new window.
echo.

:: 4. Launch Browser
echo [4/4] Opening Application...
echo Waiting 5 seconds for services to initialize...
timeout /t 5 >nul
start http://localhost:5173

echo.
echo System is running!
echo Backend: http://127.0.0.1:8000/docs
echo Frontend: http://localhost:5173
echo.
echo Press any key to close this launcher (Environment will keep running)...
pause >nul
