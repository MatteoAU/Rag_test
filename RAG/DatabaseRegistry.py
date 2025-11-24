import json
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class DatabaseRegistry:
    """Gestisce la registrazione e persistenza dei database vettoriali."""
    
    def __init__(self, registry_file: str = "db_registry.json"):
        """
        Inizializza il registry dei database.
        
        Args:
            registry_file: Path del file JSON per persistenza
        """
        self.registry_file = Path(registry_file)
        self.databases = self._load_registry()
        logger.info(f"DatabaseRegistry inizializzato con {len(self.databases)} database")
    
    def _load_registry(self) -> dict:
        """Carica il registry dal file JSON."""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"✓ Registry caricato da {self.registry_file}")
                    return data.get('databases', {})
            except Exception as e:
                logger.error(f"Errore nel caricamento del registry: {e}")
                return {}
        else:
            logger.info("Registry non trovato, creazione nuovo registry")
            return {}
    
    def _save_registry(self) -> None:
        """Salva il registry nel file JSON."""
        try:
            data = {'databases': self.databases}
            with open(self.registry_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"✓ Registry salvato in {self.registry_file}")
        except Exception as e:
            logger.error(f"Errore nel salvataggio del registry: {e}")
            raise
    
    def _generate_hash(self, name: str) -> str:
        """
        Genera un hash univoco per il database.
        
        Args:
            name: Nome del database
            
        Returns:
            Hash SHA-256 (primi 16 caratteri)
        """
        timestamp = datetime.now().isoformat()
        unique_string = f"{name}_{timestamp}"
        hash_full = hashlib.sha256(unique_string.encode()).hexdigest()
        return hash_full[:16]
    
    def create_database(self, name: str) -> dict:
        """
        Crea una nuova entry nel registry.
        
        Args:
            name: Nome del database
            
        Returns:
            Dizionario con le informazioni del database creato
            
        Raises:
            ValueError: Se esiste già un database con lo stesso nome
        """
        # Verifica se esiste già un database con questo nome
        for db_hash, db_info in self.databases.items():
            if db_info['name'] == name:
                raise ValueError(f"Esiste già un database con nome '{name}'")
        
        # Genera hash univoco
        db_hash = self._generate_hash(name)
        collection_name = f"qdrant_collection_{db_hash}"
        
        # Crea entry
        db_info = {
            'name': name,
            'hash': db_hash,
            'collection_name': collection_name,
            'created_at': datetime.now().isoformat(),
            'document_count': 0
        }
        
        self.databases[db_hash] = db_info
        self._save_registry()
        
        logger.info(f"✓ Database creato: {name} (hash: {db_hash})")
        return db_info
    
    def get_database(self, db_hash: str) -> Optional[dict]:
        """
        Recupera le informazioni di un database dal suo hash.
        
        Args:
            db_hash: Hash del database
            
        Returns:
            Dizionario con le informazioni del database o None se non trovato
        """
        return self.databases.get(db_hash)
    
    def get_collection_name(self, db_hash: str) -> Optional[str]:
        """
        Recupera il nome della collection Qdrant per un database.
        
        Args:
            db_hash: Hash del database
            
        Returns:
            Nome della collection o None se non trovato
        """
        db_info = self.get_database(db_hash)
        return db_info['collection_name'] if db_info else None
    
    def list_databases(self) -> list[dict]:
        """
        Restituisce la lista di tutti i database registrati.
        
        Returns:
            Lista di dizionari con le informazioni dei database
        """
        return list(self.databases.values())
    
    def delete_database(self, db_hash: str) -> bool:
        """
        Elimina un database dal registry.
        
        Args:
            db_hash: Hash del database da eliminare
            
        Returns:
            True se eliminato, False se non trovato
        """
        if db_hash in self.databases:
            db_name = self.databases[db_hash]['name']
            del self.databases[db_hash]
            self._save_registry()
            logger.info(f"✓ Database eliminato dal registry: {db_name} (hash: {db_hash})")
            return True
        else:
            logger.warning(f"Database con hash {db_hash} non trovato nel registry")
            return False
    
    def update_document_count(self, db_hash: str, count: int) -> None:
        """
        Aggiorna il conteggio dei documenti per un database.
        
        Args:
            db_hash: Hash del database
            count: Nuovo conteggio documenti
        """
        if db_hash in self.databases:
            self.databases[db_hash]['document_count'] = count
            self._save_registry()
    
    def database_exists(self, db_hash: str) -> bool:
        """
        Verifica se un database esiste nel registry.
        
        Args:
            db_hash: Hash del database
            
        Returns:
            True se esiste, False altrimenti
        """
        return db_hash in self.databases
