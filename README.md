# 📚 RAG-Ollama-Qdrant API

Un progetto dimostrativo che implementa l'architettura **Retrieval-Augmented Generation (RAG)** utilizzando **FastAPI** come interfaccia API, **Ollama** per i modelli linguistici (LLM) ed *embedding* locali, e **Qdrant** come database vettoriale.

Il sistema è interamente containerizzato per garantire la massima portabilità e facilità d'uso.

## 🏗️ Architettura del Progetto

Il progetto utilizza una struttura a strati **Controller-Manager-Model** all'interno di un'infrastruttura Dockerizzata:

* **Controller (`RAG/RagController.py`):** Gestisce gli endpoint **FastAPI**.
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