from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Classe che carica e valida tutte le variabili d'ambiente 
    definite nel file .env
    """

    PROJECT_NAME: str = "Default RAG Project"
    ENVIRONMENT: str = "local"
    DEBUG: bool = True
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL_NAME: str = "llama3"
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: str = "6333"
    QDRANT_COLLECTION_NAME: str = "rag_ollama_collection"
    EMBEDDING_MODEL_NAME: str = "nomic-embed-text"
    EMBEDDING_DIMENSION: int = 768
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    # Classe interna che specifica da dove caricare le impostazioni
    class Config:
        env_file = ".env"
        case_sensitive = True

# Creazione di un'istanza globale delle impostazioni
settings = Settings()