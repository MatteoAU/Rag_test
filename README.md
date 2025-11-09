# 📚 RAG-Ollama-Qdrant API

Un progetto dimostrativo che implementa l'architettura **Retrieval-Augmented Generation (RAG)** utilizzando **FastAPI** come interfaccia API, **Ollama** per i modelli linguistici (LLM) ed *embedding* locali, e **Qdrant** come database vettoriale.

Il sistema è interamente containerizzato per garantire la massima portabilità e facilità d'uso.

## 🏗️ Architettura del Progetto

Il progetto utilizza una struttura a strati **Controller-Manager-Model** all'interno di un'infrastruttura Dockerizzata:

* **Controller (`RAG/RagController.py`):** Gestisce gli endpoint **FastAPI** (`/index` e `/query`).
* **Manager (`RAG/RagManager.py`):** Orchestratore del flusso RAG (suddivisione testo, ricerca del contesto, formattazione del prompt).
* **Model (`RAG/RagModel.py`):** Interfaccia a basso livello per i servizi esterni (**Ollama** e **Qdrant**).

---

## ⚙️ Requisiti

Per avviare questo progetto, è necessario avere installato solo **Docker Desktop** e assicurarsi che sia in esecuzione.

---

## 🚀 Guida all'Avvio del Progetto

Segui questi passaggi per avviare l'intera architettura con un solo comando.

### 1. Clonazione e Setup

    Clona il Repository:
    bash
    git clone [Il tuo URL del repository]
    cd [Nome della cartella del progetto]
    
    Configura il `.env`:**
    Assicurati che il file `.env` sia presente nella directory principale e definisca i modelli che utilizzerai.
    env
    # Esempio:
    OLLAMA_MODEL_NAME="llama3" 
    EMBEDDING_MODEL_NAME="nomic-embed-text" 
    

### 2. Avvio dei Container (Qdrant, Ollama, FastAPI)

Esegui il comando di Docker Compose per costruire e avviare tutti e tre i servizi in background (`-d`).

    bash
    docker compose up --build -d

### 3. Download dei Modelli LLM (Cruciale)
Dopo l'avvio, devi istruire Ollama a scaricare i modelli che l'applicazione utilizzerà, accedendo al container Ollama.

Esegui il download (usa i nomi dei modelli specificati nel tuo .env):

Bash

docker exec -it ollama_server ollama pull llama3
docker exec -it ollama_server ollama pull nomic-embed-text 
Una volta che i download sono completati, il tuo sistema RAG è pronto. L'API è accessibile su http://localhost:8000.

💡 Interazione e Testing (Come Usare il Progetto)
Questa sezione mostra come utilizzare gli endpoint dell'API per caricare un documento e ottenere una risposta basata su di esso.

FASE A: Creazione del Documento di Test
Crea un file chiamato manuale.txt nella directory principale del progetto.

Contenuto di manuale.txt (Esempio): "La funzione primaria del sistema RAG è recuperare informazioni pertinenti da documenti indicizzati. Il sistema è ottimizzato per l'uso su schede grafiche NVIDIA, utilizzando la memoria HBM per le operazioni di vettorizzazione ad alta velocità."

FASE B: 1. Indicizzazione del Documento (POST /api/v1/document/index)
Questo passaggio carica il file, esegue il chunking, l'embedding e salva i vettori in Qdrant.

Esecuzione con cURL:

Bash

curl -X 'POST' \
  'http://localhost:8000/api/v1/document/index' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@manuale.txt;type=text/plain'
Verifica Attesa (JSON):

JSON

{
  "status": "success",
  "message": "File 'manuale.txt' indicizzato con successo in Qdrant."
}
FASE C: 2. Esecuzione della Query RAG (POST /api/v1/rag/query)
Questo passaggio cerca il contesto in Qdrant e lo invia al modello LLM (Ollama) per generare la risposta.

Esecuzione con cURL:

Bash

curl -X 'POST' \
  'http://localhost:8000/api/v1/rag/query' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "query": "Quale tipo di memoria viene usata per la vettorizzazione ad alta velocità?"
}'
Verifica Attesa (JSON):

JSON

{
  "response": "La memoria utilizzata per le operazioni di vettorizzazione ad alta velocità è la memoria HBM, specialmente su schede grafiche NVIDIA."
}
🌐 Altri Metodi di Interazione
L'interfaccia Swagger UI è disponibile all'indirizzo http://localhost:8000/docs per testare gli endpoint direttamente dal browser.

🗑️ Pulizia
Per spegnere e rimuovere tutti i container (lasciando i dati nei volumi per un riavvio rapido):

Bash

docker compose down
Per eliminare anche i volumi di dati persistenti (LLM e Qdrant):

Bash

docker compose down -v

---