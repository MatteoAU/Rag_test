"""
RAG Manager - Business Logic for Vector DB Creation
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import UploadFile
import uuid
import hashlib
from datetime import datetime
from RAG.Model.response_models import CreateVectorDBResponse, UploadFileResponse

def generate_db_hash() -> str:
    """
    Genera un hash unico per il database.
    Combina UUID4 + timestamp per massima unicità.
    Ritorna un hash SHA256 troncato a 16 caratteri.
    """
    unique_string = f"{uuid.uuid4()}-{datetime.utcnow().isoformat()}-{uuid.uuid4()}"
    full_hash = hashlib.sha256(unique_string.encode()).hexdigest()
    return f"db_{full_hash[:16]}"

class RagManager:
    """Manager per la logica di business del RAG"""
    
    def __init__(self):
        # Import qui per evitare circular imports
        from RAG.Model.model import RagModel
        self.model = RagModel()
    
    async def create_vector_db(self) -> CreateVectorDBResponse:
        """
        Crea un database vettoriale vuoto.
        Genera automaticamente un hash unico per il database.
        
        Ritorna il db_hash da usare per caricare documenti successivamente.
        """
        # Genera hash unico per questo database
        db_hash = generate_db_hash()
        
        # Verifica che Qdrant sia raggiungibile
        health = self.model.health_check()
        if not health["qdrant"]:
            return CreateVectorDBResponse(
                db_hash=db_hash,
                status="error",
                message="Qdrant non raggiungibile. Verifica che il container Docker sia attivo."
            )
        
        # Ottieni dimensione embeddings da Ollama (serve per creare la collection)
        if not health["ollama"]:
            return CreateVectorDBResponse(
                db_hash=db_hash,
                status="error",
                message="Ollama non raggiungibile. Verifica che il container Docker sia attivo."
            )
        
        try:
            vector_size = self.model.ollama.get_embedding_dimension()
        except Exception as e:
            return CreateVectorDBResponse(
                db_hash=db_hash,
                status="error",
                message=f"Errore nel determinare la dimensione degli embeddings: {str(e)}"
            )
        
        # Crea collection vuota in Qdrant
        success = self.model.qdrant.create_collection(db_hash, vector_size)
        if not success:
            return CreateVectorDBResponse(
                db_hash=db_hash,
                status="error",
                message="Errore nella creazione della collection Qdrant."
            )
        
        return CreateVectorDBResponse(
            db_hash=db_hash,
            status="success",
            message=f"Vector DB '{db_hash}' creato con successo. Pronto per ricevere documenti."
        )

