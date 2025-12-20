# RAG System

A customized RAG (Retrieval-Augmented Generation) system featuring a FastAPI backend, a modern React (Glassmorphism) frontend, and local LLM integration via Ollama and Qdrant.

## 📋 Prerequisites
Before running the project, ensure you have the following installed:

1.  **Docker Desktop** (Windows/Mac/Linux)
    > ⚠️ **IMPORTANT**: Docker Desktop MUST be **open and running** in the background for the application to work. The database and AI models run inside containers.
2.  **Python 3.9+**
3.  **Node.js & npm** (for the Frontend)

## 🚀 Quick Start (Windows)
We provide automation scripts to get you up and running instantly.

### 1. First Setup
Double-click **`auto_setup.bat`**.
This will:
- Create a Python virtual environment (`.venv`).
- Install backend dependencies (`requirements.txt`).
- Install frontend dependencies (`npm install`).
- Pull the required Docker images (Qdrant, Ollama).

### 2. Launch Application
Double-click **`auto_start.bat`**.
This will:
- Start the Docker containers.
- Launch the FastAPI Backend.
- Launch the React Frontend.
- Automatically open your browser at `http://localhost:5173`.

## 🛠 Manual Startup
If you prefer to run commands manually:

1.  **Start Services**: `docker-compose up -d`
2.  **Backend**: `uvicorn RAG.Controller.controller:app --reload`
3.  **Frontend**: `cd Front-end && npm run dev`

## 🔑 Default Credentials
Check your `.env` file for the configured credentials.
- **Username**: `admin` (default)
- **Password**: *Defined in your .env file*