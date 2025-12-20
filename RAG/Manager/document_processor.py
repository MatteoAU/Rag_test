"""
RAG Document Processor - Parsing and Chunking Logic
Contiene tutta la logica per elaborare documenti: parsing e chunking.
"""
from typing import List
from fastapi import UploadFile
import io
import re


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


class DocumentUploader:
    """
    Gestisce l'upload completo di documenti nel database vettoriale.
    Include parsing, chunking, embedding e storage.
    """
    
    def __init__(self, qdrant_client, ollama_client):
        """
        Args:
            qdrant_client: Istanza di QdrantConnection
            ollama_client: Istanza di OllamaConnection
        """
        self.qdrant = qdrant_client
        self.ollama = ollama_client
        self.parser = DocumentParser()
        self.chunker = TextChunker(chunk_size=500, chunk_overlap=50)
    
    async def upload_file(self, file: UploadFile, db_hash: str, response_model):
        """
        Carica un file nel database vettoriale specificato.
        
        Args:
            file: File da caricare
            db_hash: Hash del database vettoriale di destinazione
            response_model: Classe del modello di response (UploadFileResponse)
        
        Returns:
            Istanza del response_model con statistiche e stato dell'operazione
        """
        from datetime import datetime
        
        filename = file.filename or "unknown_file"
        
        # Verifica che la collection esista
        if not self.qdrant.collection_exists(db_hash):
            return response_model(
                db_hash=db_hash,
                status="error",
                message=f"Database '{db_hash}' non trovato. Crea prima il database con /create_vectorDB/",
                filename=filename,
                chunks_count=0,
                vectors_stored=0
            )
        
        # Verifica formato supportato
        if not DocumentParser.is_supported(filename):
            return response_model(
                db_hash=db_hash,
                status="error",
                message=f"Formato file non supportato. Formati supportati: {', '.join(DocumentParser.SUPPORTED_EXTENSIONS)}",
                filename=filename,
                chunks_count=0,
                vectors_stored=0
            )
        
        try:
            # 1. Parsa il file
            text = await self.parser.parse_file(file)
            
            if not text or not text.strip():
                return response_model(
                    db_hash=db_hash,
                    status="error",
                    message="Il file non contiene testo estraibile",
                    filename=filename,
                    chunks_count=0,
                    vectors_stored=0
                )
            
            # 2. Crea chunks
            chunks = self.chunker.chunk_text(text)
            
            if not chunks:
                return response_model(
                    db_hash=db_hash,
                    status="error",
                    message="Impossibile creare chunks dal testo",
                    filename=filename,
                    chunks_count=0,
                    vectors_stored=0
                )
            
            # 3. Genera embeddings
            embeddings = self.ollama.get_embeddings_batch(chunks)
            
            # 4. Prepara metadata e IDs univoci
            # Conta i vettori già presenti per generare ID univoci
            try:
                collection_info = self.qdrant.client.get_collection(db_hash)
                next_id = collection_info.points_count
            except Exception:
                next_id = 0
            
            upload_timestamp = datetime.utcnow().isoformat()
            
            payloads = [
                {
                    "filename": filename,
                    "chunk_index": idx,
                    "text": chunk,
                    "upload_timestamp": upload_timestamp
                }
                for idx, chunk in enumerate(chunks)
            ]
            
            ids = list(range(next_id, next_id + len(chunks)))
            
            # 5. Salva in Qdrant
            success = self.qdrant.upsert_vectors(
                collection_name=db_hash,
                vectors=embeddings,
                payloads=payloads,
                ids=ids
            )
            
            if not success:
                return response_model(
                    db_hash=db_hash,
                    status="error",
                    message="Errore nel salvare i vettori in Qdrant",
                    filename=filename,
                    chunks_count=len(chunks),
                    vectors_stored=0
                )
            
            return response_model(
                db_hash=db_hash,
                status="success",
                message=f"File '{filename}' caricato con successo",
                filename=filename,
                chunks_count=len(chunks),
                vectors_stored=len(chunks)
            )
            
        except ValueError as e:
            # Errori di parsing
            return response_model(
                db_hash=db_hash,
                status="error",
                message=str(e),
                filename=filename,
                chunks_count=0,
                vectors_stored=0
            )
        except Exception as e:
            # Errori generici
            return response_model(
                db_hash=db_hash,
                status="error",
                message=f"Errore durante l'upload: {str(e)}",
                filename=filename,
                chunks_count=0,
                vectors_stored=0
            )

