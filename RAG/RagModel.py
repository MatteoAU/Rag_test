from qdrant_client import QdrantClient
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.llms import Ollama
from langchain_community.vectorstores import Qdrant
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from Config.Config import settings

class RAGModel:
    """Gestisce le connessioni a Qdrant e Ollama."""

    def __init__(self):
        # ... (Componenti Embedding, LLM e Text Splitter Omissi per brevità) ...
        self.embeddings = OllamaEmbeddings(
            model=settings.EMBEDDING_MODEL_NAME,
            base_url=settings.OLLAMA_BASE_URL
        )

        self.llm = Ollama(
            model=settings.OLLAMA_MODEL_NAME,
            base_url=settings.OLLAMA_BASE_URL
        )

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            length_function=len,
            is_separator_regex=False,
        )
        
        # PASSO 1: Crea l'oggetto QdrantClient usando l'URL completo
        qdrant_url = f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}"
        client = QdrantClient(url=qdrant_url)
        
        # PASSO 2: Passa l'oggetto client al VectorStore di LangChain
        self.qdrant = Qdrant(
            client=client, 
            collection_name=settings.QDRANT_COLLECTION_NAME,
            embeddings=self.embeddings,
        )

    # ... (Metodi save_documents, search_documents, generate Omissi per brevità) ...
    # def save_documents(self, raw_documents: list[Document]):
    #     # ...
    #     pass
        
    # def search_documents(self, query: str, k: int = 4) -> list[Document]:
    #     # ...
    #     pass

    # def generate(self, prompt: str) -> str:
    #     # ...
    #     pass