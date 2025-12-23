# RAG Project (Retrieval-Augmented Generation)

Questo progetto è un sistema completo di **Retrieval-Augmented Generation (RAG)** che permette di caricare documenti, creare database vettoriali e interrogare i contenuti utilizzando l'intelligenza artificiale locale. Il sistema è progettato per essere modulare, sicuro e facile da avviare.

---

## 🏗️ Architettura del Sistema

Il progetto segue un'architettura **Client-Server** moderna, containerizzata per garantire la portabilità e la facilità di gestione.

### 1. **Frontend (Client)**
- **Tecnologia**: React (Vite)
- **Posizione**: Cartella `Front-end/`
- **Funzione**: Interfaccia utente moderna e reattiva. Permette agli utenti di:
  - Effettuare il login (Autenticazione JWT).
  - Caricare documenti (PDF, TXT, DOCX, ecc.).
  - Gestire database vettoriali multipli.
  - Chattare con i propri documenti.
- **Dettagli**: Utilizza `react-markdown` per renderizzare le risposte dell'AI e componenti personalizzati per una UX fluida.

### 2. **Backend (Server)**
- **Tecnologia**: Python (FastAPI)
- **Posizione**: Cartella `RAG/`
- **Struttura**:
  - **Controller** (`RAG/Controller`): Espone le API REST. Gestisce le rotte HTTP, l'autenticazione JWT (`/token/`), e smista le richieste (es. `/query/`, `/upload_file/`).
  - **Manager** (`RAG/Manager`): Contiene la logica di business.
    - `RagManager`: Facade principale che coordina le operazioni.
    - `DocumentProcessor`: Gestisce il parsing dei file e lo splitting in chunk.
    - `QueryProcessor`: Esegue la ricerca semantica e genera le risposte.
  - **Model** (`RAG/Model`): Gestisce le connessioni ai servizi di dati e AI.
- **Funzione**: Cuore logico del sistema. Orchesta il flusso di dati tra il database vettoriale e il modello linguistico.

### 3. **Servizi Dati & AI (Docker)**
Il sistema si appoggia a due servizi principali eseguiti tramite **Docker**:

- **🔍 Qdrant (Vector Database)**
  - **Porte**: `6333` (API), `6334` (GRPC)
  - **Funzione**: Memorizza gli "embeddings" (rappresentazioni matematiche) dei documenti caricati. Permette la ricerca semantica ultra-veloce per trovare i pezzi di testo rilevanti per una domanda.

- **🧠 Ollama (LLM Engine)**
  - **Porta**: `11434`
  - **Modelli**:
    - `nomic-embed-text`: Modello per creare gli embeddings (trasformare testo in vettori).
    - `llama3.2` (o configurabile): Modello di chat che genera la risposta finale in linguaggio naturale.
  - **Funzione**: Motore di intelligenza artificiale locale. Garantisce privacy totale dei dati (nessun dato viene inviato a cloud esterni).

---

## 🚀 Come Avviare il Progetto

Il progetto include script di automazione per Windows (`.bat`) che semplificano notevolmente l'setup e l'avvio.

### Prerequisiti
Assicurati di avere installato sul tuo computer:
1.  **Docker Desktop** (e che sia in esecuzione).
2.  **Python 3.8+**.
3.  **Node.js** (per il frontend).

### 🛠️ Prima Installazione (Setup)

Esegui lo script `auto_setup.bat`. Questo script farà tutto per te:
1.  Verifica la presenza di Python.
2.  Crea un environment virtuale (`.venv`) nella cartella `RAG`.
3.  Installa le dipendenze Python (`requirements.txt`).
4.  Crea il file `.env` (copiandolo da `.env.example`).
5.  Installa le dipendenze del Frontend (`npm install`).
6.  Scarica le immagini Docker necessarie.

**Comando:**
```cmd
auto_setup.bat
```

> **Nota:** Dopo il setup, apri il file `.env` generato e configura `USER` e `PASS` se vuoi cambiare le credenziali di default.

### ▶️ Avvio Giornaliero

Una volta installato, per avviare il sistema usa semplicemente `auto_start.bat`.

**Comando:**
```cmd
auto_start.bat
```

Questo script eseguirà in sequenza:
1.  Avvia i container Docker (Qdrant e Ollama).
2.  Scarica/Verifica i modelli AI in Ollama (potrebbe richiedere tempo al primo avvio).
3.  Avvia il **Backend** in una nuova finestra.
4.  Avvia il **Frontend** in una nuova finestra.
5.  Apre automaticamente il browser all'indirizzo `http://localhost:5173`.

### 🛑 Arresto
Per fermare il sistema, puoi chiudere le finestre del terminale aperte. I container Docker rimarranno attivi in background (per un riavvio rapido). Per spegnerli completamente:
```cmd
docker-compose down
```

---

## 📂 Struttura Cartelle

```
/
├── RAG/                    # Backend (Python)
│   ├── Controller/         # API Endpoint
│   ├── Manager/            # Logica (Parsing, RAG pipeline)
│   └── Model/              # Interfacce Qdrant/Ollama
├── Front-end/              # Frontend (React/Vite)
├── Utils/                  # Utility scripts
├── auto_setup.bat          # Script di installazione
├── auto_start.bat          # Script di avvio
├── docker-compose.yml      # Configurazione servizi Docker
└── requirements.txt        # Dipendenze Python
```