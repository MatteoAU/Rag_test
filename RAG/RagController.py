from fastapi import FastAPI, UploadFile, File, HTTPException, Form
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
    description="Sistema RAG Multi-Database con Ollama, Qdrant e FastAPI",
    version="2.0.0"
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
    db_hash: str = Field(..., min_length=1, description="Hash del database da interrogare")

class QueryResponse(BaseModel):
    response: str = Field(..., description="Risposta generata dal sistema RAG")
    
class StatusResponse(BaseModel):
    status: str = Field(..., description="Stato dell'operazione")
    message: str = Field(..., description="Messaggio descrittivo")

class CreateDatabaseRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="Nome del database")

class CreateDatabaseResponse(BaseModel):
    status: str
    message: str
    db_hash: str
    db_name: str
    collection_name: str

class DatabaseInfo(BaseModel):
    name: str
    hash: str
    collection_name: str
    created_at: str
    document_count: int

class ListDatabasesResponse(BaseModel):
    databases: list[DatabaseInfo]

# --- Endpoint dell'API (Controller) ---

# ======== DATABASE MANAGEMENT ENDPOINTS ========

@app.post("/database/create", response_model=CreateDatabaseResponse, tags=["Database Management"])
async def create_database(request: CreateDatabaseRequest):
    """
    Crea un nuovo database vettoriale e restituisce l'hash univoco per identificarlo.
    """
    if not rag_manager:
        raise HTTPException(status_code=503, detail="RAG Manager non disponibile")
    
    try:
        db_info = rag_manager.create_database(request.name)
        return {
            "status": "success",
            "message": f"Database '{request.name}' creato con successo",
            "db_hash": db_info['hash'],
            "db_name": db_info['name'],
            "collection_name": db_info['collection_name']
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Errore nella creazione del database: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Errore interno: {str(e)}")

@app.get("/database/list", response_model=ListDatabasesResponse, tags=["Database Management"])
async def list_databases():
    """
    Restituisce la lista di tutti i database registrati.
    """
    if not rag_manager:
        raise HTTPException(status_code=503, detail="RAG Manager non disponibile")
    
    try:
        databases = rag_manager.list_databases()
        return {"databases": databases}
    except Exception as e:
        logger.error(f"Errore nel recupero della lista database: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Errore interno: {str(e)}")

@app.delete("/database/{db_hash}", response_model=StatusResponse, tags=["Database Management"])
async def delete_database(db_hash: str):
    """
    Elimina un database specifico utilizzando il suo hash.
    """
    if not rag_manager:
        raise HTTPException(status_code=503, detail="RAG Manager non disponibile")
    
    try:
        rag_manager.delete_database(db_hash)
        return {
            "status": "success",
            "message": f"Database con hash '{db_hash}' eliminato con successo"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Errore nell'eliminazione del database: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Errore interno: {str(e)}")

# ======== DOCUMENT INDEXING ENDPOINT ========

@app.post("/document/upload", response_model=StatusResponse, tags=["Document Indexing"])
async def index_document(
    file: UploadFile = File(...),
    db_hash: str = Form(..., description="Hash del database di destinazione")
):
    """
    Carica un documento in un database specifico.
    Richiede il db_hash del database target.
    """
    if not rag_manager:
        raise HTTPException(
            status_code=503, 
            detail="RAG Manager non disponibile. Verificare i servizi e i log di startup."
        )
    
    # Valida che il database esista
    if not rag_manager.registry.database_exists(db_hash):
        raise HTTPException(
            status_code=404,
            detail=f"Database con hash '{db_hash}' non trovato. Creare prima il database."
        )
    
    # Validazione estensione file
    allowed_extensions = {'.pdf', '.txt', '.md', '.csv'}
    file_extension = Path(file.filename).suffix.lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Formato file non supportato: {file_extension}. "
                   f"Formati accettati: {', '.join(allowed_extensions)}"
        )
    
    MAX_FILE_SIZE = getattr(settings, 'MAX_FILE_SIZE_MB', 50) * 1024 * 1024 
    temp_file_path = TEMP_UPLOAD_DIR / f"temp_{Path(file.filename).name}"
    
    try:
        # Salva il file temporaneamente con verifica dimensione
        file_size = 0
        
        with open(temp_file_path, "wb") as buffer:
            while True:
                chunk = await file.read(8192)
                if not chunk:
                    break
                
                file_size += len(chunk)
                
                if file_size > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail=f"File troppo grande. Dimensione massima: {MAX_FILE_SIZE / 1024 / 1024:.2f} MB"
                    )
                
                buffer.write(chunk)
        
        logger.info(f"File salvato: {file.filename} ({file_size / (1024*1024):.2f} MB). Avvio indicizzazione...")
        
        # Chiama il Manager per l'indicizzazione nel database specifico
        chunks_count = rag_manager.index_file(str(temp_file_path), db_hash)
        
        return {
            "status": "success",
            "message": f"File '{file.filename}' indicizzato con successo ({chunks_count} chunks)."
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Errore durante l'indicizzazione: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Errore durante l'elaborazione del file: {str(e)}"
        )
    finally:
        if temp_file_path.exists():
            try:
                temp_file_path.unlink()
                logger.info(f"File temporaneo eliminato: {temp_file_path}")
            except Exception as e:
                logger.warning(f"Impossibile eliminare il file temporaneo: {e}")

# ======== QUERY ENDPOINT ========

@app.post("/query", response_model=QueryResponse, tags=["Query"])
async def rag_query(request: QueryRequest):
    """
    Esegue una query RAG su un database specifico.
    Richiede il db_hash del database da interrogare.
    """
    if not rag_manager:
        raise HTTPException(
            status_code=503,
            detail="RAG Manager non disponibile. Verificare i servizi."
        )
    
    # Valida che il database esista
    if not rag_manager.registry.database_exists(request.db_hash):
        raise HTTPException(
            status_code=404,
            detail=f"Database con hash '{request.db_hash}' non trovato."
        )
    
    try:
        logger.info(f"Query ricevuta per db {request.db_hash}: {request.query}")
        response = rag_manager.get_rag_response(request.query, request.db_hash)
        return {"response": response}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Errore durante l'elaborazione della query: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Impossibile ottenere la risposta RAG: {str(e)}"
        )

# --- Esecuzione del Server ---
# Esegui con: uvicorn RAG.RagController:app --reload --host 0.0.0.0 --port 8000