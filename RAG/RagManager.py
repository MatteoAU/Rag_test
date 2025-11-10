from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.documents import Document  # ✅ Import CORRETTO
from langchain_core.prompts import PromptTemplate
from RAG.RagModel import RAGModel
from Config.Config import settings
import logging

logger = logging.getLogger(__name__)

# Prompt per istruire l'LLM a usare il contesto fornito
RAG_PROMPT = """Sei un assistente RAG utile. Rispondi alla domanda
solo ed esclusivamente in base al contesto seguente.
Se non trovi la risposta nel contesto, dì onestamente che non hai informazioni sufficienti.

Contesto: {context}

Domanda: {question}

Risposta:
"""

class RAGManager:
    """Orchestra il flusso RAG: Caricamento, Ricerca e Generazione."""

    def __init__(self):
        logger.info("Inizializzazione RAGManager...")
        self.model = RAGModel()
        self.prompt_template = PromptTemplate.from_template(RAG_PROMPT)
        logger.info("✓ RAGManager pronto")

    def _load_documents(self, file_path: str) -> list[Document]:
        """Carica documenti in base all'estensione del file."""
        logger.info(f"Caricamento documento: {file_path}")
        
        if file_path.lower().endswith(".pdf"):
            loader = PyPDFLoader(file_path)
        elif file_path.lower().endswith((".txt", ".md")):
            loader = TextLoader(file_path, encoding='utf-8')
        else:
            raise ValueError("Tipo di file non supportato. Usare .pdf, .txt, o .md.")
        
        docs = loader.load()
        logger.info(f"✓ Caricati {len(docs)} documenti")
        return docs

    def index_file(self, file_path: str):
        """Carica, splitta e salva un file in Qdrant."""
        
        # 1. Caricamento
        raw_documents = self._load_documents(file_path)
        
        # 2. Salvataggio (Chunking + Embedding avviene nel Model)
        self.model.save_documents(raw_documents)
        
        logger.info(f"✓ Indicizzazione completata per il file: {file_path}")

    def get_rag_response(self, query: str) -> str:
        """Esegue il flusso completo RAG per una query."""
        
        # 1. Retrieval: Cerca i frammenti più rilevanti
        # Calcolo più robusto per k
        k = max(3, settings.EMBEDDING_DIMENSION // 100)
        retrieved_docs = self.model.search_documents(query, k=k)

        # 2. Formattazione del Contesto
        context_text = "\n---\n".join([doc.page_content for doc in retrieved_docs])
        
        if not context_text:
            return "Non ho trovato alcun contesto rilevante nei documenti."

        # 3. Generazione Aumentata: Crea il prompt finale
        final_prompt = self.prompt_template.format(context=context_text, question=query)
        
        # 4. Invocazione LLM
        response = self.model.generate(final_prompt)
        
        return response