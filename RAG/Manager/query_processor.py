"""
RAG Query Processor - Logica completa per query RAG
Gestisce ricerca semantica e generazione risposte con LLM.
"""
from typing import List
from RAG.Model.response_models import QueryResponse, DocumentMatch
from Utils.Config.config import Config


class QueryProcessor:
    """
    Gestisce il processo completo di query RAG:
    1. Genera embedding della query
    2. Ricerca documenti simili
    3. Costruisce prompt con contesto
    4. Genera risposta con LLM
    """
    
    def __init__(self, qdrant_client, ollama_client):
        """
        Args:
            qdrant_client: Istanza di QdrantConnection
            ollama_client: Istanza di OllamaConnection
        """
        self.qdrant = qdrant_client
        self.ollama = ollama_client
    
    async def execute_query(
        self, 
        db_hash: str, 
        query: str, 
        top_k: int = 5
    ) -> QueryResponse:
        """
        Esegue query RAG completa sul database vettoriale.
        
        Args:
            db_hash: Hash del database vettoriale
            query: Query testuale dell'utente
            top_k: Numero di documenti da recuperare
        
        Returns:
            QueryResponse con risposta e fonti
        """
        # Verifica che la collection esista
        if not self.qdrant.collection_exists(db_hash):
            return QueryResponse(
                db_hash=db_hash,
                query=query,
                answer="",
                sources=[],
                status="error",
                message=f"Database '{db_hash}' non trovato."
            )
        
        try:
            # 1. Genera embedding della query
            query_embedding = self.ollama.get_embeddings(query)
            
            # 2. Ricerca documenti simili
            search_results = self.qdrant.search(
                collection_name=db_hash,
                query_vector=query_embedding,
                limit=top_k
            )
            
            # 3. Prepara sources per la response e contesto
            sources = []
            context_parts = []
            
            if search_results:
                for idx, result in enumerate(search_results):
                    payload = result["payload"]
                    sources.append(DocumentMatch(
                        text=payload.get("text", ""),
                        score=round(result["score"], 4),
                        filename=payload.get("filename", "unknown"),
                        chunk_index=payload.get("chunk_index", 0)
                    ))
                    
                    # Costruisci contesto per il prompt
                    context_parts.append(
                        f"[Documento {idx+1} - {payload.get('filename', 'unknown')}]\n"
                        f"{payload.get('text', '')}"
                    )
            
            # 4. Costruisci prompt con contesto (anche se vuoto)
            context = "\n\n".join(context_parts) if context_parts else "Nessun documento disponibile nel database."
            prompt = self._build_prompt(query, context)
            
            # 5. Genera risposta con LLM
            messages = [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            answer = self.ollama.generate_chat_response(
                messages=messages,
                model=Config.OLLAMA_CHAT_MODEL
            )
            
            return QueryResponse(
                db_hash=db_hash,
                query=query,
                answer=answer,
                sources=sources,
                status="success"
            )
            
        except Exception as e:
            return QueryResponse(
                db_hash=db_hash,
                query=query,
                answer="",
                sources=[],
                status="error",
                message=f"Errore durante la query: {str(e)}"
            )
    
    def _build_prompt(self, query: str, context: str) -> str:
        """
        Costruisce il prompt per il LLM.
        
        Args:
            query: Domanda dell'utente
            context: Documenti recuperati come contesto
        
        Returns:
            Prompt formattato
        """
        return f"""Sei un assistente esperto. Rispondi alla domanda dell'utente basandoti SOLO sulle informazioni fornite nel contesto.

Contesto:
{context}

Domanda: {query}

Istruzioni:
- Rispondi in modo chiaro e conciso
- Usa SOLO le informazioni presenti nel contesto
- Se il contesto non contiene informazioni rilevanti, dillo chiaramente
- Cita i documenti quando possibile (es: "Secondo il Documento 1...")

Risposta:"""
