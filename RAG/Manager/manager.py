"""
RAG Manager - Business Logic for Vector DB Creation
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import UploadFile
import uuid
import hashlib
from datetime import datetime
from RAG.Model.response_models import (
    CreateVectorDBResponse, 
    UploadFileResponse, 
    ListVectorDBResponse, 
    DeleteVectorDBResponse,
    VectorDBInfo,
    QueryResponse,
    DocumentMatch
)

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
    
    def list_vector_dbs(self) -> ListVectorDBResponse:
        """
        Lista tutti i database vettoriali.
        
        Returns:
            ListVectorDBResponse con lista dei database e conteggio
        """
        # Ottieni lista collections da Qdrant
        collections = self.model.qdrant.list_collections()
        
        # Converti in VectorDBInfo
        databases = [
            VectorDBInfo(
                db_hash=col["name"],
                vectors_count=col["vectors_count"]
            )
            for col in collections
        ]
        
        return ListVectorDBResponse(
            status="success",
            databases=databases,
            total_count=len(databases)
        )
    
    def delete_vector_db(self, db_hash: str) -> DeleteVectorDBResponse:
        """
        Elimina un database vettoriale.
        
        Args:
            db_hash: Hash del database da eliminare
        
        Returns:
            DeleteVectorDBResponse con stato dell'operazione
        """
        # Verifica che la collection esista
        if not self.model.qdrant.collection_exists(db_hash):
            return DeleteVectorDBResponse(
                db_hash=db_hash,
                status="error",
                message=f"Vector DB '{db_hash}' non trovato."
            )
        
        # Elimina la collection
        success = self.model.qdrant.delete_collection(db_hash)
        
        if not success:
            return DeleteVectorDBResponse(
                db_hash=db_hash,
                status="error",
                message=f"Errore nell'eliminazione del Vector DB '{db_hash}'."
            )
        
        return DeleteVectorDBResponse(
            db_hash=db_hash,
            status="success",
            message=f"Vector DB '{db_hash}' eliminato con successo."
        )
    
    async def query_vector_db(self, db_hash: str, query: str, top_k: int = 5) -> QueryResponse:
        """
        Esegue query RAG sul database vettoriale.
        Delega la logica completa a QueryProcessor.
        
        Args:
            db_hash: Hash del database vettoriale
            query: Query testuale dell'utente
            top_k: Numero di documenti da recuperare
        
        Returns:
            QueryResponse con risposta e fonti
        """
        from RAG.Manager.query_processor import QueryProcessor
        
        processor = QueryProcessor(
            qdrant_client=self.model.qdrant,
            ollama_client=self.model.ollama
        )
        
        return await processor.execute_query(db_hash, query, top_k)



