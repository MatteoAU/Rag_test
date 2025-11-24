from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.llms import Ollama
from langchain_community.vectorstores import Qdrant
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from Config.Config import settings
import logging

logger = logging.getLogger(__name__)

class RAGModel:
    """Gestisce le connessioni a Qdrant e Ollama."""

    def __init__(self):
        logger.info("Inizializzazione RAGModel...")
        
        # Componente Embedding
        self.embeddings = OllamaEmbeddings(
            model=settings.EMBEDDING_MODEL_NAME,
            base_url=settings.OLLAMA_BASE_URL
        )
        logger.info(f"Embeddings configurati: {settings.EMBEDDING_MODEL_NAME}")

        # Rileva automaticamente la dimensione degli embeddings
        self.embedding_dimension = self._get_embedding_dimension()
        logger.info(f"Dimensione embeddings rilevata automaticamente: {self.embedding_dimension}")

        # Componente LLM
        self.llm = Ollama(
            model=settings.OLLAMA_MODEL_NAME,
            base_url=settings.OLLAMA_BASE_URL
        )
        logger.info(f"LLM configurato: {settings.OLLAMA_MODEL_NAME}")

        # Text Splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            length_function=len,
            is_separator_regex=False,
        )
        logger.info(f"Text Splitter configurato: chunk_size={settings.CHUNK_SIZE}, overlap={settings.CHUNK_OVERLAP}")
        
        # Crea l'oggetto QdrantClient usando l'URL completo
        qdrant_url = f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}"
        logger.info(f"Connessione a Qdrant: {qdrant_url}")
        self.client = QdrantClient(url=qdrant_url)
        logger.info(f"✓ Client Qdrant connesso")

    def _get_embedding_dimension(self) -> int:
        """Rileva automaticamente la dimensione degli embeddings del modello."""
        logger.info("Rilevamento dimensione embeddings...")
        # Crea un embedding di prova con un testo semplice
        test_embedding = self.embeddings.embed_query("test")
        dimension = len(test_embedding)
        logger.info(f"✓ Dimensione embeddings rilevata: {dimension}")
        return dimension

    def initialize_collection(self, collection_name: str) -> None:
        """Crea una nuova collection in Qdrant.
        
        Args:
            collection_name: Nome della collection da creare
            
        Raises:
            ValueError: Se la collection esiste già
        """
        try:
            # Verifica se la collection esiste
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]
            
            if collection_name in collection_names:
                raise ValueError(f"Collection '{collection_name}' esiste già")
            
            # Crea la collection con i parametri corretti
            logger.info(f"Creazione collection '{collection_name}'...")
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dimension,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"✓ Collection '{collection_name}' creata con successo")
                
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Errore durante la creazione della collection: {e}")
            raise

    def save_documents(self, raw_documents: list[Document], collection_name: str) -> int:
        """Splitta e salva i documenti in una collection specifica.
        
        Args:
            raw_documents: Lista di documenti da salvare
            collection_name: Nome della collection Qdrant
            
        Returns:
            Numero di chunks salvati
        """
        try:
            logger.info(f"Splitting {len(raw_documents)} documenti...")
            chunks = self.text_splitter.split_documents(raw_documents)
            logger.info(f"Generati {len(chunks)} chunks")
            
            if not chunks:
                logger.warning("Nessun chunk generato dai documenti")
                return 0
            
            # Crea un VectorStore per questa collection specifica
            qdrant = Qdrant(
                client=self.client,
                collection_name=collection_name,
                embeddings=self.embeddings,
            )
            
            logger.info(f"Salvataggio {len(chunks)} chunks in collection '{collection_name}'...")
            qdrant.add_documents(chunks)
            logger.info(f"✓ {len(chunks)} chunks salvati con successo")
            
            return len(chunks)
            
        except Exception as e:
            logger.error(f"Errore durante il salvataggio dei documenti: {e}")
            raise
        
    def search_documents(self, query: str, collection_name: str, k: int = 4) -> list[Document]:
        """Cerca documenti simili alla query in una collection specifica.
        
        Args:
            query: Query di ricerca
            collection_name: Nome della collection Qdrant
            k: Numero di documenti da recuperare
            
        Returns:
            Lista di documenti rilevanti
        """
        try:
            # Crea un VectorStore per questa collection specifica
            qdrant = Qdrant(
                client=self.client,
                collection_name=collection_name,
                embeddings=self.embeddings,
            )
            
            logger.info(f"Ricerca in '{collection_name}' per query: '{query}' (k={k})")
            results = qdrant.similarity_search(query, k=k)
            logger.info(f"✓ Trovati {len(results)} documenti rilevanti")
            return results
        except Exception as e:
            logger.error(f"Errore durante la ricerca: {e}")
            raise

    def delete_collection(self, collection_name: str) -> None:
        """Elimina una collection da Qdrant.
        
        Args:
            collection_name: Nome della collection da eliminare
        """
        try:
            logger.info(f"Eliminazione collection '{collection_name}'...")
            self.client.delete_collection(collection_name=collection_name)
            logger.info(f"✓ Collection '{collection_name}' eliminata")
        except Exception as e:
            logger.error(f"Errore durante l'eliminazione della collection: {e}")
            raise
    
    def get_collection_info(self, collection_name: str) -> dict:
        """Recupera informazioni su una collection.
        
        Args:
            collection_name: Nome della collection
            
        Returns:
            Dizionario con informazioni sulla collection
        """
        try:
            info = self.client.get_collection(collection_name=collection_name)
            return {
                'name': collection_name,
                'vectors_count': info.vectors_count,
                'points_count': info.points_count,
            }
        except Exception as e:
            logger.error(f"Errore nel recupero info collection: {e}")
            raise
    
    def generate(self, prompt: str) -> str:
        """Genera risposta dall'LLM."""
        try:
            logger.info("Generazione risposta LLM...")
            response = self.llm.invoke(prompt)
            logger.info(f"✓ Risposta generata (lunghezza: {len(response)} caratteri)")
            return response
        except Exception as e:
            logger.error(f"Errore durante la generazione: {e}")
            raise