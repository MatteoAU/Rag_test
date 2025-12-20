"""
RAG Model - Qdrant and Ollama Connections
"""
from typing import List, Optional
import httpx
from qdrant_client import QdrantClient
from qdrant_client.http import models
from Utils.Config.config import Config


class OllamaConnection:
    """Gestisce la connessione a Ollama per gli embeddings"""
    
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self._client = httpx.Client(timeout=120.0)
    
    def health_check(self) -> bool:
        """Verifica che Ollama sia raggiungibile"""
        try:
            response = self._client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception:
            return False
    
    def get_embeddings(self, text: str) -> List[float]:
        """Genera embeddings per un singolo testo"""
        response = self._client.post(
            f"{self.base_url}/api/embeddings",
            json={"model": self.model, "prompt": text}
        )
        response.raise_for_status()
        return response.json()["embedding"]
    
    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Genera embeddings per una lista di testi"""
        embeddings = []
        for text in texts:
            embeddings.append(self.get_embeddings(text))
        return embeddings
    
    def get_embedding_dimension(self) -> int:
        """Ottiene la dimensione degli embeddings del modello"""
        # Genera un embedding di test per determinare la dimensione
        test_embedding = self.get_embeddings("test")
        return len(test_embedding)


class QdrantConnection:
    """Gestisce la connessione a Qdrant"""
    
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self._client: Optional[QdrantClient] = None
    
    @property
    def client(self) -> QdrantClient:
        """Lazy initialization del client Qdrant"""
        if self._client is None:
            self._client = QdrantClient(host=self.host, port=self.port)
        return self._client
    
    def health_check(self) -> bool:
        """Verifica che Qdrant sia raggiungibile"""
        try:
            self.client.get_collections()
            return True
        except Exception:
            return False
    
    def collection_exists(self, collection_name: str) -> bool:
        """Verifica se una collection esiste"""
        try:
            collections = self.client.get_collections().collections
            return any(c.name == collection_name for c in collections)
        except Exception:
            return False
    
    def create_collection(self, collection_name: str, vector_size: int) -> bool:
        """Crea una nuova collection"""
        try:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=vector_size,
                    distance=models.Distance.COSINE
                )
            )
            return True
        except Exception:
            return False
    
    def upsert_vectors(
        self, 
        collection_name: str, 
        vectors: List[List[float]], 
        payloads: List[dict],
        ids: Optional[List[int]] = None
    ) -> bool:
        """Inserisce o aggiorna vettori nella collection"""
        try:
            if ids is None:
                ids = list(range(len(vectors)))
            
            points = [
                models.PointStruct(
                    id=idx,
                    vector=vector,
                    payload=payload
                )
                for idx, vector, payload in zip(ids, vectors, payloads)
            ]
            
            self.client.upsert(
                collection_name=collection_name,
                points=points
            )
            return True
        except Exception:
            return False
    
    def list_collections(self) -> List[dict]:
        """
        Restituisce la lista di tutte le collections con informazioni dettagliate.
        
        Returns:
            Lista di dict con name, vectors_count
        """
        try:
            collections_response = self.client.get_collections()
            result = []
            
            for collection in collections_response.collections:
                # Ottieni info dettagliate sulla collection
                try:
                    collection_info = self.client.get_collection(collection.name)
                    result.append({
                        "name": collection.name,
                        "vectors_count": collection_info.points_count
                    })
                except Exception:
                    # Se non riusciamo a ottenere info dettagliate, aggiungiamo solo il nome
                    result.append({
                        "name": collection.name,
                        "vectors_count": 0
                    })
            
            return result
        except Exception:
            return []
    
    def delete_collection(self, collection_name: str) -> bool:
        """
        Elimina una collection.
        
        Args:
            collection_name: Nome della collection da eliminare
        
        Returns:
            True se successo, False altrimenti
        """
        try:
            self.client.delete_collection(collection_name=collection_name)
            return True
        except Exception:
            return False


class RagModel:
    """
    Singleton per gestire le connessioni Qdrant e Ollama.
    Fornisce accesso centralizzato ai servizi di embedding e vector store.
    """
    _instance: Optional['RagModel'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.qdrant = QdrantConnection(
            host=Config.QDRANT_HOST,
            port=Config.QDRANT_PORT
        )
        self.ollama = OllamaConnection(
            base_url=Config.OLLAMA_BASE_URL,
            model=Config.OLLAMA_EMBEDDING_MODEL
        )
        self._initialized = True
    
    def health_check(self) -> dict:
        """Verifica lo stato di tutti i servizi"""
        return {
            "qdrant": self.qdrant.health_check(),
            "ollama": self.ollama.health_check()
        }
