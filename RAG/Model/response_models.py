"""
RAG Response Models - Pydantic Models for API Responses
Modelli Pydantic per le response degli endpoint RAG.
"""
from pydantic import BaseModel


class CreateVectorDBResponse(BaseModel):
    """Response model per la creazione di un Vector DB"""
    db_hash: str
    status: str
    message: str


class UploadFileResponse(BaseModel):
    """Response model per l'upload di file nel Vector DB"""
    db_hash: str
    status: str  # "success" o "error"
    message: str
    filename: str
    chunks_count: int
    vectors_stored: int
