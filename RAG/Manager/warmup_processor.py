"""
RAG Warmup Processor - Logica per pre-caricamento modelli LLM
Gestisce il warmup dei modelli embedding e chat per ridurre la latenza.
"""
from Utils.Config.config import Config


class WarmupProcessor:
    """
    Gestisce il processo di warmup dei modelli LLM:
    1. Verifica disponibilità Ollama
    2. Esegue query di test su modello embedding
    3. Esegue query di test su modello chat
    """
    
    def __init__(self, ollama_client):
        """
        Args:
            ollama_client: Istanza di OllamaConnection
        """
        self.ollama = ollama_client
    
    async def execute_warmup(self) -> dict:
        """
        Esegue warmup completo dei modelli LLM.
        
        Returns:
            dict con stato del warmup per ogni modello
        """
        result = {
            "status": "success",
            "embedding_model": {
                "model": Config.OLLAMA_EMBEDDING_MODEL,
                "status": "error",
                "message": ""
            },
            "chat_model": {
                "model": Config.OLLAMA_CHAT_MODEL,
                "status": "error",
                "message": ""
            }
        }
        
        # Verifica che Ollama sia raggiungibile
        if not self.ollama.health_check():
            result["status"] = "error"
            result["embedding_model"]["message"] = "Ollama non raggiungibile"
            result["chat_model"]["message"] = "Ollama non raggiungibile"
            return result
        
        # Warmup del modello embedding
        result = self._warmup_embedding_model(result)
        
        # Warmup del modello chat
        result = self._warmup_chat_model(result)
        
        return result
    
    def _warmup_embedding_model(self, result: dict) -> dict:
        """
        Esegue warmup del modello embedding.
        
        Args:
            result: Dizionario risultato da aggiornare
            
        Returns:
            Dizionario risultato aggiornato
        """
        try:
            warmup_text = "This is a warmup query to preload the embedding model."
            _ = self.ollama.get_embeddings(warmup_text)
            result["embedding_model"]["status"] = "success"
            result["embedding_model"]["message"] = "Modello embedding caricato con successo"
        except Exception as e:
            result["status"] = "partial"
            result["embedding_model"]["message"] = f"Errore nel warmup embedding: {str(e)}"
        
        return result
    
    def _warmup_chat_model(self, result: dict) -> dict:
        """
        Esegue warmup del modello chat.
        
        Args:
            result: Dizionario risultato da aggiornare
            
        Returns:
            Dizionario risultato aggiornato
        """
        try:
            warmup_messages = [
                {
                    "role": "user",
                    "content": "Hello, this is a warmup message."
                }
            ]
            _ = self.ollama.generate_chat_response(
                messages=warmup_messages,
                model=Config.OLLAMA_CHAT_MODEL
            )
            result["chat_model"]["status"] = "success"
            result["chat_model"]["message"] = "Modello chat caricato con successo"
        except Exception as e:
            if result["embedding_model"]["status"] == "success":
                result["status"] = "partial"
            else:
                result["status"] = "error"
            result["chat_model"]["message"] = f"Errore nel warmup chat: {str(e)}"
        
        return result
