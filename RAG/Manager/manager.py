"""
RAG Manager - Business Logic for Vector DB Creation
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import UploadFile
import io
import re
import uuid
import hashlib
from datetime import datetime


def generate_db_hash() -> str:
    """
    Genera un hash unico per il database.
    Combina UUID4 + timestamp per massima unicità.
    Ritorna un hash SHA256 troncato a 16 caratteri.
    """
    unique_string = f"{uuid.uuid4()}-{datetime.utcnow().isoformat()}-{uuid.uuid4()}"
    full_hash = hashlib.sha256(unique_string.encode()).hexdigest()
    return f"db_{full_hash[:16]}"


class CreateVectorDBResponse(BaseModel):
    """Response model per la creazione di un Vector DB"""
    db_hash: str
    status: str
    message: str


class DocumentParser:
    """Parser per diversi formati di documenti"""
    
    SUPPORTED_EXTENSIONS = {'.txt', '.pdf', '.md', '.docx', '.doc', '.csv', '.json', '.html', '.xml'}
    
    @staticmethod
    def get_extension(filename: str) -> str:
        """Estrae l'estensione dal nome file"""
        if '.' in filename:
            return '.' + filename.rsplit('.', 1)[1].lower()
        return ''
    
    @staticmethod
    def is_supported(filename: str) -> bool:
        """Verifica se il formato è supportato"""
        ext = DocumentParser.get_extension(filename)
        return ext in DocumentParser.SUPPORTED_EXTENSIONS
    
    @staticmethod
    async def parse_file(file: UploadFile) -> str:
        """
        Estrae il testo da un file.
        Supporta: TXT, PDF, MD, DOCX, CSV, JSON, HTML, XML
        """
        content = await file.read()
        ext = DocumentParser.get_extension(file.filename or '')
        
        try:
            if ext == '.pdf':
                return DocumentParser._parse_pdf(content)
            elif ext == '.docx':
                return DocumentParser._parse_docx(content)
            elif ext == '.doc':
                return DocumentParser._parse_doc(content)
            elif ext in {'.txt', '.md', '.csv', '.json', '.html', '.xml'}:
                return content.decode('utf-8', errors='ignore')
            else:
                # Prova a decodificare come testo
                return content.decode('utf-8', errors='ignore')
        except Exception as e:
            raise ValueError(f"Errore nel parsing del file {file.filename}: {str(e)}")
    
    @staticmethod
    def _parse_pdf(content: bytes) -> str:
        """Estrae testo da PDF usando pypdf"""
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(content))
            text_parts = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            return '\n\n'.join(text_parts)
        except ImportError:
            raise ValueError("pypdf non installato. Installa con: pip install pypdf")
    
    @staticmethod
    def _parse_docx(content: bytes) -> str:
        """Estrae testo da DOCX usando python-docx"""
        try:
            from docx import Document
            doc = Document(io.BytesIO(content))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return '\n\n'.join(paragraphs)
        except ImportError:
            raise ValueError("python-docx non installato. Installa con: pip install python-docx")
    
    @staticmethod
    def _parse_doc(content: bytes) -> str:
        """Prova a estrarre testo da DOC (formato legacy)"""
        # Per i file .doc legacy, proviamo a estrarre il testo grezzo
        # Questo è un fallback limitato, consigliamo di convertire in DOCX
        try:
            # Cerca pattern di testo nel file binario
            text = content.decode('utf-8', errors='ignore')
            # Rimuovi caratteri di controllo
            text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', ' ', text)
            return text
        except Exception:
            raise ValueError("Impossibile parsare file .doc. Converti in .docx per risultati migliori.")


class TextChunker:
    """Divide il testo in chunks per l'embedding"""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Divide il testo in chunks con overlap.
        Cerca di dividere su punti naturali (fine frase, paragrafo).
        """
        if not text or not text.strip():
            return []
        
        # Pulisci il testo
        text = text.strip()
        text = re.sub(r'\n{3,}', '\n\n', text)  # Max 2 newline consecutive
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            if end >= len(text):
                # Ultimo chunk
                chunk = text[start:].strip()
                if chunk:
                    chunks.append(chunk)
                break
            
            # Cerca un punto di divisione naturale
            chunk = text[start:end]
            
            # Prova a dividere su fine paragrafo
            last_para = chunk.rfind('\n\n')
            if last_para > self.chunk_size // 2:
                end = start + last_para + 2
            else:
                # Prova a dividere su fine frase
                last_sentence = max(
                    chunk.rfind('. '),
                    chunk.rfind('? '),
                    chunk.rfind('! '),
                    chunk.rfind('.\n'),
                    chunk.rfind('?\n'),
                    chunk.rfind('!\n')
                )
                if last_sentence > self.chunk_size // 2:
                    end = start + last_sentence + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Avanza con overlap
            start = end - self.chunk_overlap
            if start < 0:
                start = end
        
        return chunks


class RagManager:
    """Manager per la logica di business del RAG"""
    
    def __init__(self):
        # Import qui per evitare circular imports
        from RAG.Model.model import RagModel
        self.model = RagModel()
        self.parser = DocumentParser()
        self.chunker = TextChunker(chunk_size=500, chunk_overlap=50)
    
    async def create_vector_db(self) -> CreateVectorDBResponse:
        """
        Crea un database vettoriale vuoto.
        Genera automaticamente un hash unico per il database.
        
        Ritorna il db_hash da usare per caricare documenti successivamente.
        """
        # Genera hash unico per questo database
        db_hash = generate_db_hash()
        
        # Verifica che Qdrant sia raggiungibile
        health = self.model.health_check()
        if not health["qdrant"]:
            return CreateVectorDBResponse(
                db_hash=db_hash,
                status="error",
                message="Qdrant non raggiungibile. Verifica che il container Docker sia attivo."
            )
        
        # Ottieni dimensione embeddings da Ollama (serve per creare la collection)
        if not health["ollama"]:
            return CreateVectorDBResponse(
                db_hash=db_hash,
                status="error",
                message="Ollama non raggiungibile. Verifica che il container Docker sia attivo."
            )
        
        try:
            vector_size = self.model.ollama.get_embedding_dimension()
        except Exception as e:
            return CreateVectorDBResponse(
                db_hash=db_hash,
                status="error",
                message=f"Errore nel determinare la dimensione degli embeddings: {str(e)}"
            )
        
        # Crea collection vuota in Qdrant
        success = self.model.qdrant.create_collection(db_hash, vector_size)
        if not success:
            return CreateVectorDBResponse(
                db_hash=db_hash,
                status="error",
                message="Errore nella creazione della collection Qdrant."
            )
        
        return CreateVectorDBResponse(
            db_hash=db_hash,
            status="success",
            message=f"Vector DB '{db_hash}' creato con successo. Pronto per ricevere documenti."
        )
