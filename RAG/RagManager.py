from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from RAG.RagModel import RAGModel
from RAG.DatabaseRegistry import DatabaseRegistry
from Config.Config import Settings
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
        self.registry = DatabaseRegistry()
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

    def create_database(self, name: str) -> dict:
        """Crea un nuovo database vettoriale.
        
        Args:
            name: Nome del database
            
        Returns:
            Dizionario con le informazioni del database creato
            
        Raises:
            ValueError: Se esiste già un database con lo stesso nome
        """
        logger.info(f"Creazione database: {name}")
        
        # Crea entry nel registry
        db_info = self.registry.create_database(name)
        
        # Inizializza la collection in Qdrant
        self.model.initialize_collection(db_info['collection_name'])
        
        logger.info(f"✓ Database '{name}' creato con hash: {db_info['hash']}")
        return db_info

    def list_databases(self) -> list[dict]:
        """Restituisce la lista di tutti i database registrati."""
        return self.registry.list_databases()

    def delete_database(self, db_hash: str) -> None:
        """Elimina un database.
        
        Args:
            db_hash: Hash del database da eliminare
            
        Raises:
            ValueError: Se il database non esiste
        """
        # Verifica che il database esista
        db_info = self.registry.get_database(db_hash)
        if not db_info:
            raise ValueError(f"Database con hash '{db_hash}' non trovato")
        
        logger.info(f"Eliminazione database: {db_info['name']} (hash: {db_hash})")
        
        # Elimina la collection da Qdrant
        self.model.delete_collection(db_info['collection_name'])
        
        # Rimuovi dal registry
        self.registry.delete_database(db_hash)
        
        logger.info(f"✓ Database '{db_info['name']}' eliminato")

    def index_file(self, file_path: str, db_hash: str) -> int:
        """Carica, splitta e salva un file in un database specifico.
        
        Args:
            file_path: Path del file da indicizzare
            db_hash: Hash del database di destinazione
            
        Returns:
            Numero di chunks creati
            
        Raises:
            ValueError: Se il database non esiste
        """
        # Verifica che il database esista
        collection_name = self.registry.get_collection_name(db_hash)
        if not collection_name:
            raise ValueError(f"Database con hash '{db_hash}' non trovato")
        
        # 1. Caricamento
        raw_documents = self._load_documents(file_path)
        
        # 2. Salvataggio (Chunking + Embedding avviene nel Model)
        chunks_count = self.model.save_documents(raw_documents, collection_name)
        
        # 3. Aggiorna il conteggio documenti nel registry
        db_info = self.registry.get_database(db_hash)
        new_count = db_info.get('document_count', 0) + len(raw_documents)
        self.registry.update_document_count(db_hash, new_count)
        
        logger.info(f"✓ Indicizzazione completata per il file: {file_path}")
        return chunks_count

    def get_rag_response(self, query: str, db_hash: str) -> str:
        """Esegue il flusso completo RAG per una query su un database specifico.
        
        Args:
            query: Query dell'utente
            db_hash: Hash del database da interrogare
            
        Returns:
            Risposta generata dall'LLM
            
        Raises:
            ValueError: Se il database non esiste
        """
        # Verifica che il database esista
        collection_name = self.registry.get_collection_name(db_hash)
        if not collection_name:
            raise ValueError(f"Database con hash '{db_hash}' non trovato")
        
        # 1. Retrieval: Cerca i frammenti più rilevanti
        k = max(3, self.model.embedding_dimension // 100)
        retrieved_docs = self.model.search_documents(query, collection_name, k=k)

        # 2. Formattazione del Contesto
        context_text = "\n---\n".join([doc.page_content for doc in retrieved_docs])
        
        if not context_text:
            return "Non ho trovato alcun contesto rilevante nei documenti."

        # 3. Generazione Aumentata: Crea il prompt finale
        final_prompt = self.prompt_template.format(context=context_text, question=query)
        
        # 4. Invocazione LLM
        response = self.model.generate(final_prompt)
        
        return response