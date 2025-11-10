from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from RAG.RagManager import RAGManager
from Config.Config import settings
import os
import shutil
import logging
from pathlib import Path

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Setup ---
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Sistema RAG con Ollama, Qdrant e FastAPI",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory per upload temporanei
TEMP_UPLOAD_DIR = Path("temp_uploads")
TEMP_UPLOAD_DIR.mkdir(exist_ok=True)

# Inizializzazione RAG Manager
try:
    rag_manager = RAGManager()
    logger.info("✓ RAG Manager inizializzato con successo")
except Exception as e:
    logger.error(f"❌ Errore nell'inizializzazione del RAG Manager: {e}")
    rag_manager = None

# --- Modelli Pydantic per l'API ---
class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Query da inviare al sistema RAG")

class QueryResponse(BaseModel):
    response: str = Field(..., description="Risposta generata dal sistema RAG")
    
class StatusResponse(BaseModel):
    status: str = Field(..., description="Stato dell'operazione")
    message: str = Field(..., description="Messaggio descrittivo")

class HealthResponse(BaseModel):
    status: str
    services: dict

# --- Endpoint dell'API (Controller) ---

@app.post("/api/document/index", response_model=StatusResponse, tags=["Indexing"])
async def index_document(file: UploadFile = File(...)):
    """
    Carica un documento, lo suddivide in chunks, vettorizza e lo salva in Qdrant.
    """
    
    if not rag_manager:
        raise HTTPException(
            status_code=503, 
            detail="RAG Manager non disponibile. Verificare i servizi e i log di startup."
        )
    
    # Validazione estensione file
    allowed_extensions = {'.pdf', '.txt', '.md', '.csv'} # Aggiungi estensioni se supportate dal Manager
    file_extension = Path(file.filename).suffix.lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Formato file non supportato: {file_extension}. "
                   f"Formati accettati: {', '.join(allowed_extensions)}"
        )
    
    # Usa le settings per la dimensione massima se le hai definite nel file .env
    # Altrimenti, usa un default.
    MAX_FILE_SIZE = getattr(settings, 'MAX_FILE_SIZE_MB', 50) * 1024 * 1024 
    
    temp_file_path = TEMP_UPLOAD_DIR / f"temp_{Path(file.filename).name}"
    
    try:
        # Salva il file temporaneamente con verifica dimensione
        file_size = 0
        
        with open(temp_file_path, "wb") as buffer:
            while True:
                chunk = await file.read(8192) # Leggi in chunk asincroni
                if not chunk:
                    break  # Fine del file
                
                file_size += len(chunk)
                
                if file_size > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail=f"File troppo grande. Dimensione massima: {MAX_FILE_SIZE / 1024 / 1024:.2f} MB"
                    )
                
                buffer.write(chunk)
        
        logger.info(f"File salvato: {file.filename} ({file_size / (1024*1024):.2f} MB). Avvio indicizzazione...")
        
        # Chiama il Manager per l'indicizzazione
        # Il manager userà il percorso del file temporaneo
        rag_manager.index_file(str(temp_file_path))
        
        return {
            "status": "success",
            "message": f"File '{file.filename}' indicizzato con successo in Qdrant."
        }
        
    except HTTPException:
        # Rilancia le eccezioni HTTP che hai sollevato (es. 400, 413)
        raise
    except Exception as e:
        logger.error(f"Errore durante l'indicizzazione: {e}", exc_info=True)
        # Se l'errore è dovuto a un problema interno (es. LLM, Qdrant), lancia 500
        raise HTTPException(
            status_code=500,
            detail=f"Errore durante l'elaborazione del file: {str(e)}"
        )
    finally:
        # Pulisci il file temporaneo ASSOLUTAMENTE SEMPRE
        if temp_file_path.exists():
            try:
                temp_file_path.unlink()
                logger.info(f"File temporaneo eliminato: {temp_file_path}")
            except Exception as e:
                logger.warning(f"Impossibile eliminare il file temporaneo: {e}")

@app.post("/api/query", response_model=QueryResponse, tags=["Query"])
async def rag_query(request: QueryRequest):
    """
    Esegue una query RAG e restituisce la risposta dell'LLM.
    
    Il sistema cerca i documenti più rilevanti nel database vettoriale
    e genera una risposta basata sul contesto trovato.
    """
    
    if not rag_manager:
        raise HTTPException(
            status_code=503,
            detail="RAG Manager non disponibile. Verificare i servizi."
        )
    
    try:
        logger.info(f"Query ricevuta: {request.query}")
        response = rag_manager.get_rag_response(request.query)
        return {"response": response}
    except Exception as e:
        logger.error(f"Errore durante l'elaborazione della query: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Impossibile ottenere la risposta RAG: {str(e)}"
        )

# --- Esecuzione del Server ---
# Esegui con: uvicorn RAG.RagController:app --reload --host 0.0.0.0 --port 8000