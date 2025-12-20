"""
RAG Response Models - Pydantic Models for API Responses
Modelli Pydantic per le response degli endpoint RAG.
"""
from pydantic import BaseModel
from typing import List, Optional


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


class VectorDBInfo(BaseModel):
    """Informazioni su un singolo Vector DB"""
    db_hash: str
    vectors_count: int


class ListVectorDBResponse(BaseModel):
    """Response model per la lista di Vector DB"""
    status: str
    databases: List[VectorDBInfo]
    total_count: int


class DeleteVectorDBResponse(BaseModel):
    """Response model per l'eliminazione di un Vector DB"""
    db_hash: str
    status: str
    message: str

