# 📚 RAG Multi-Database System

Sistema **Retrieval-Augmented Generation (RAG)** avanzato con supporto per **database vettoriali multipli**, costruito con **FastAPI**, **Ollama** (LLM locale), e **Qdrant** (vector database).

Gestisci più collezioni di documenti isolate, ognuna identificata da un hash univoco per massima flessibilità e organizzazione.

---

## 🌟 Caratteristiche Principali

- ✅ **Multi-Database**: Crea e gestisci database vettoriali separati per diversi domini
- ✅ **Hash-Based Identification**: Ogni database ha un hash univoco SHA-256
- ✅ **REST API Completa**: Endpoints per CRUD database, upload documenti, query RAG
- ✅ **Auto-Embedding Detection**: Dimensione embeddings rilevata automaticamente dal modello
- ✅ **Persistenza**: Registry JSON per mantenere mappature database
- ✅ **Dockerized**: Setup completo con un singolo comando
- ✅ **Swagger UI**: Interfaccia interattiva per testare le API

---

## 🏗️ Architettura

```
┌─────────────────┐
│   FastAPI App   │  ← Controller (RagController.py)
└────────┬────────┘
         │
    ┌────▼─────────────────┐
    │   RAG Manager        │  ← Orchestrazione (RagManager.py)
    │  + DatabaseRegistry  │
    └────┬─────────────────┘
         │
    ┌────▼────────┐
    │  RAG Model  │  ← Interfaccia Ollama/Qdrant (RagModel.py)
    └─────────────┘
         │
    ┌────▼────────────────────────┐
    │  Ollama (LLM + Embeddings) │
    │  Qdrant (Vector DB)         │
    └─────────────────────────────┘
```

**Pattern**: Controller → Manager → Model

---

## ⚙️ Requisiti

- **Docker Desktop** (in esecuzione)
- Un file `.env` configurato (vedi sotto)

---

## 🚀 Guida Rapida

### 1. Clone e Setup

```bash
git clone <repository-url>
cd Rag_test
```

### 2. Configura Variabili d'Ambiente

Copia il template e modifica secondo le tue esigenze:

```bash
cp .env_layout.md .env
```

**File `.env` esempio**:
```env
PROJECT_NAME="RAG Multi-Database System"
ENVIRONMENT="development"
DEBUG=True

# Ollama Configuration
OLLAMA_BASE_URL="http://ollama:11434"
OLLAMA_MODEL_NAME="llama3"

# Qdrant Configuration
QDRANT_HOST="qdrant"
QDRANT_PORT="6333"

# Embedding Configuration
EMBEDDING_MODEL_NAME="nomic-embed-text"
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

### 3. Avvia i Container

```bash
docker-compose up --build -d
```

Questo avvierà:
- **Qdrant** (port 6333 - API, 6334 - UI)
- **Ollama** (port 11434)
- **FastAPI** (port 8000)

### 4. Download Modelli Ollama

**IMPORTANTE**: Scarica i modelli LLM ed embedding:

```bash
# Modello LLM
docker exec -it ollama_server ollama pull llama3

# Modello Embedding
docker exec -it ollama_server ollama pull nomic-embed-text
```

> 💡 **Tip**: Puoi usare altri modelli cambiando i nomi nel `.env`

### 5. Verifica Installazione

Apri nel browser:
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **Qdrant UI**: http://localhost:6334

---

## 📖 Utilizzo del Sistema

### Workflow Tipo

#### 1️⃣ Crea un Database

**Endpoint**: `POST /database/create`

```bash
curl -X POST "http://localhost:8000/database/create" \
  -H "Content-Type: application/json" \
  -d '{"name": "documenti_medici"}'
```

**Risposta**:
```json
{
  "status": "success",
  "message": "Database 'documenti_medici' creato con successo",
  "db_hash": "a1b2c3d4e5f6g7h8",
  "db_name": "documenti_medici",
  "collection_name": "qdrant_collection_a1b2c3d4e5f6g7h8"
}
```

> 🔑 **Salva il `db_hash`** - lo userai per tutte le operazioni successive!

---

#### 2️⃣ Carica Documenti

**Endpoint**: `POST /document/upload`

```bash
curl -X POST "http://localhost:8000/document/upload" \
  -F "file=@/path/to/documento.pdf" \
  -F "db_hash=a1b2c3d4e5f6g7h8"
```

**Formati supportati**: `.pdf`, `.txt`, `.md`, `.csv`

**Risposta**:
```json
{
  "status": "success",
  "message": "File 'documento.pdf' indicizzato con successo (15 chunks)."
}
```

---

#### 3️⃣ Esegui Query RAG

**Endpoint**: `POST /query`

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Quali sono i sintomi principali?",
    "db_hash": "a1b2c3d4e5f6g7h8"
  }'
```

**Risposta**:
```json
{
  "response": "Secondo i documenti, i sintomi principali sono..."
}
```

---

#### 4️⃣ Lista Database

**Endpoint**: `GET /database/list`

```bash
curl "http://localhost:8000/database/list"
```

**Risposta**:
```json
{
  "databases": [
    {
      "name": "documenti_medici",
      "hash": "a1b2c3d4e5f6g7h8",
      "collection_name": "qdrant_collection_a1b2c3d4e5f6g7h8",
      "created_at": "2025-11-24T20:00:00",
      "document_count": 3
    }
  ]
}
```

---

#### 5️⃣ Elimina Database

**Endpoint**: `DELETE /database/{db_hash}`

```bash
curl -X DELETE "http://localhost:8000/database/a1b2c3d4e5f6g7h8"
```

**Risposta**:
```json
{
  "status": "success",
  "message": "Database con hash 'a1b2c3d4e5f6g7h8' eliminato con successo"
}
```

---

## 🔌 API Reference

### Database Management

| Endpoint | Method | Descrizione |
|----------|--------|-------------|
| `/database/create` | POST | Crea nuovo database vettoriale |
| `/database/list` | GET | Lista tutti i database |
| `/database/{db_hash}` | DELETE | Elimina database specifico |

### Document Operations

| Endpoint | Method | Descrizione |
|----------|--------|-------------|
| `/document/upload` | POST | Carica documento in database (richiede `db_hash`) |

### Query Operations

| Endpoint | Method | Descrizione |
|----------|--------|-------------|
| `/query` | POST | Esegue query RAG su database specifico |

---

## 📁 Struttura Progetto

```
Rag_test/
├── RAG/
│   ├── RagController.py      # FastAPI endpoints
│   ├── RagManager.py          # Orchestrazione RAG
│   ├── RagModel.py            # Interfaccia Ollama/Qdrant
│   └── DatabaseRegistry.py    # Gestione multi-database
├── Config/
│   └── Config.py              # Configurazione settings
├── docker-compose.yml         # Orchestrazione container
├── Dockerfile                 # Immagine app FastAPI
├── requirements.txt           # Dipendenze Python
├── .env                       # Variabili d'ambiente (non committato)
├── db_registry.json           # Registry database (non committato)
└── README.md                  # Questa guida
```

---

## 🎯 Casi d'Uso

### Multi-Tenancy SaaS
```python
# Cliente A
create_database("cliente_a_docs") → hash_a
upload_documents(files, hash_a)
query("domanda", hash_a)  # Vede solo i suoi dati

# Cliente B
create_database("cliente_b_docs") → hash_b
upload_documents(files, hash_b)
query("domanda", hash_b)  # Vede solo i suoi dati
```

### Domini Separati
```python
# Database separati per dominio
medical_db = create_database("medical_knowledge")
legal_db = create_database("legal_contracts")
technical_db = create_database("technical_manuals")

# Query mirate per dominio
query("sintomi influenza", medical_db)
query("clausola rescissione", legal_db)
query("installazione prodotto", technical_db)
```

---

## 🛠️ Comandi Utili

### Gestione Container

```bash
# Avvia servizi
docker-compose up -d

# Ferma servizi
docker-compose down

# Ricostruisci dopo modifiche al codice
docker-compose up --build -d

# Visualizza log
docker-compose logs -f rag_api
docker-compose logs -f ollama
docker-compose logs -f qdrant

# Accedi al container
docker exec -it rag_api_server bash
```

### Pulizia Completa

```bash
# Ferma e rimuovi tutto (inclusi volumi)
docker-compose down -v

# Rimuovi anche db_registry.json
rm db_registry.json
```

---

## ⚠️ Note Importanti

### File `db_registry.json`
- **NON eliminare manualmente** - contiene le mappature database → collection
- È automaticamente creato all'avvio
- È ignorato da Git (vedi `.gitignore`)
- Se perso, perdi i riferimenti ai database Qdrant

### Cambio Modello Embedding
Se cambi `EMBEDDING_MODEL_NAME` nel `.env`:
1. Riavvia i container: `docker-compose restart`
2. I **nuovi database** useranno la nuova dimensione
3. I **database esistenti** continueranno con la dimensione originale

### Dimensione Massima File
Default: **50 MB** per file (configurabile in `RagController.py`)

---

## 🐛 Troubleshooting

### App non si avvia
```bash
# Verifica che Docker sia in esecuzione
docker ps

# Controlla i log
docker-compose logs rag_api
```

### Errore "OutputTooSmall" in Qdrant
- **Causa**: Mismatch dimensioni embedding
- **Soluzione**: Elimina collection vecchie e ricrea database

```bash
docker-compose down -v
rm -rf qdrant_data/*
docker-compose up -d
```

### Modelli Ollama non trovati
```bash
# Verifica modelli installati
docker exec -it ollama_server ollama list

# Scarica modelli mancanti
docker exec -it ollama_server ollama pull <model-name>
```

---

## 🚀 Roadmap Futuri Miglioramenti

- [ ] Reranking dei risultati per maggiore accuratezza
- [ ] Hybrid search (semantic + keyword)
- [ ] Metadata filtering sui documenti
- [ ] Query globale su tutti i database
- [ ] Auto-routing intelligente database
- [ ] Response streaming
- [ ] Batch upload documenti
- [ ] Metrics e monitoring

---
