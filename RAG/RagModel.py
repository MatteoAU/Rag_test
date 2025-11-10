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
        
        # PASSO 1: Crea l'oggetto QdrantClient usando l'URL completo
        qdrant_url = f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}"
        logger.info(f"Connessione a Qdrant: {qdrant_url}")
        self.client = QdrantClient(url=qdrant_url)
        
        # PASSO 2: Verifica e crea la collection se non esiste
        self._ensure_collection_exists()
        
        # PASSO 3: Passa l'oggetto client al VectorStore di LangChain
        self.qdrant = Qdrant(
            client=self.client, 
            collection_name=settings.QDRANT_COLLECTION_NAME,
            embeddings=self.embeddings,
        )
        logger.info(f"VectorStore Qdrant inizializzato: collection={settings.QDRANT_COLLECTION_NAME}")

    def _get_embedding_dimension(self) -> int:
        """Rileva automaticamente la dimensione degli embeddings del modello."""
        logger.info("Rilevamento dimensione embeddings...")
        # Crea un embedding di prova con un testo semplice
        test_embedding = self.embeddings.embed_query("test")
        dimension = len(test_embedding)
        logger.info(f"✓ Dimensione embeddings rilevata: {dimension}")
        return dimension

    def _ensure_collection_exists(self):
        """Crea la collection in Qdrant se non esiste già."""
        try:
            # Verifica se la collection esiste
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]
            
            if settings.QDRANT_COLLECTION_NAME in collection_names:
                logger.info(f"✓ Collection '{settings.QDRANT_COLLECTION_NAME}' già esistente")
            else:
                # Crea la collection con i parametri corretti
                logger.info(f"Creazione collection '{settings.QDRANT_COLLECTION_NAME}'...")
                self.client.create_collection(
                    collection_name=settings.QDRANT_COLLECTION_NAME,
                    vectors_config=VectorParams(
                        size=self.embedding_dimension,  # Usa la dimensione rilevata automaticamente
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"✓ Collection '{settings.QDRANT_COLLECTION_NAME}' creata con successo")
                
        except Exception as e:
            logger.error(f"Errore durante la verifica/creazione della collection: {e}")
            raise

    def save_documents(self, raw_documents: list[Document]):
        """Splitta e salva i documenti in Qdrant."""
        try:
            logger.info(f"Splitting {len(raw_documents)} documenti...")
            chunks = self.text_splitter.split_documents(raw_documents)
            logger.info(f"Generati {len(chunks)} chunks")
            
            if not chunks:
                logger.warning("Nessun chunk generato dai documenti")
                return
            
            logger.info("Salvataggio chunks in Qdrant...")
            self.qdrant.add_documents(chunks)
            logger.info(f"✓ {len(chunks)} chunks salvati con successo in Qdrant")
            
        except Exception as e:
            logger.error(f"Errore durante il salvataggio dei documenti: {e}")
            raise
        
    def search_documents(self, query: str, k: int = 4) -> list[Document]:
        """Cerca documenti simili alla query."""
        try:
            logger.info(f"Ricerca documenti per query: '{query}' (k={k})")
            results = self.qdrant.similarity_search(query, k=k)
            logger.info(f"✓ Trovati {len(results)} documenti rilevanti")
            return results
        except Exception as e:
            logger.error(f"Errore durante la ricerca: {e}")
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