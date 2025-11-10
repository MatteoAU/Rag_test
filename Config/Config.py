from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Schema di configurazione che elenca SOLO i nomi e i tipi delle variabili
    che DEVONO essere caricate dal file .env.
    """

    PROJECT_NAME: str
    ENVIRONMENT: str
    DEBUG: bool
    OLLAMA_BASE_URL: str
    OLLAMA_MODEL_NAME: str
    QDRANT_HOST: str
    QDRANT_PORT: str
    QDRANT_COLLECTION_NAME: str
    EMBEDDING_MODEL_NAME: str
    EMBEDDING_DIMENSION: int
    CHUNK_SIZE: int
    CHUNK_OVERLAP: int

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()