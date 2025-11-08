# main.py

from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from RAG.RagManager import RAGManager
from Config.Config import settings
import os
import shutil

# --- Setup ---
app = FastAPI(title=settings.PROJECT_NAME)
rag_manager = RAGManager()

# --- Modelli Pydantic per l'API ---
class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    response: str
    
class StatusResponse(BaseModel):
    status: str
    message: str

# --- Endpoint dell'API (Controller) ---

@app.get("/status", response_model=StatusResponse, tags=["Utility"])
def get_status():
    """Controlla lo stato del server."""
    return {"status": "ok", "message": f"Server RAG {settings.PROJECT_NAME} in esecuzione."}

@app.post("/api/v1/document/index", response_model=StatusResponse, tags=["Indexing"])
async def index_document(file: UploadFile = File(...)):
    """Carica un documento, lo suddivide, vettorizza e lo salva in Qdrant."""
    
    # Salva il file temporaneamente
    temp_file_path = f"temp_{file.filename}"
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Chiama il Manager per l'indicizzazione
        rag_manager.index_file(temp_file_path)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore durante l'indicizzazione: {e}")
    finally:
        # Pulisci il file temporaneo
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

    return {"status": "success", "message": f"File '{file.filename}' indicizzato con successo in Qdrant."}

@app.post("/api/v1/rag/query", response_model=QueryResponse, tags=["Query"])
def rag_query(request: QueryRequest):
    """Esegue una query RAG e restituisce la risposta dell'LLM."""
    try:
        response = rag_manager.get_rag_response(request.query)
        return {"response": response}
    except Exception as e:
        print(f"Errore RAG: {e}")
        raise HTTPException(status_code=500, detail="Impossibile ottenere la risposta RAG.")

# --- Comando per Eseguire il Server ---
# Esegui con: uvicorn RAG:RagController:app --reload