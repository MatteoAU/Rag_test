# Dockerfile

# Usa un'immagine base Python
FROM python:3.11-slim

# Imposta la directory di lavoro all'interno del container
WORKDIR /app

# Copia il file requirements.txt e installa le dipendenze
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia il resto del codice sorgente nel container
COPY . .

# Comando di default per avviare l'applicazione (sarà sovrascritto da docker-compose)
CMD ["uvicorn", "RAG.RagController:app", "--host", "0.0.0.0", "--port", "8000"]