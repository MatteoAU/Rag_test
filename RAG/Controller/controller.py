from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt
from fastapi import Depends, HTTPException, Request, FastAPI
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from Utils.Config.config import Config
from Utils.Logger.security_logger import log_security_event, SecurityEventType
from fastapi.middleware.cors import CORSMiddleware
from RAG.Manager.manager import RagManager, CreateVectorDBResponse

app = FastAPI()

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Consente richieste da qualsiasi dominio (anche esterno), QUANDO PUB CHECK 
    allow_credentials=True, # Abilita l'invio di cookie/header di autenticazione
    allow_methods=["*"], # Permette tutti i metodi HTTP (GET, POST, DELETE, ecc.)
    allow_headers=["*"], # Autorizza tutti gli header nelle richieste (inclusi custom)
)

security = HTTPBearer()

class TokenRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

@app.post("/token/", response_model=TokenResponse)
async def generate_token(request: Request, token_request: TokenRequest):
    if token_request.username == Config.USER and token_request.password == Config.PASS:
        expiration = datetime.utcnow() + timedelta(hours=Config.JWT_EXPIRATION)
        
        payload = {
            "sub": token_request.username,
            "exp": expiration
        }
        
        token = jwt.encode(payload, Config.JWT_SECRET, algorithm=Config.JWT_ALGORITHM)
        
        # Log di login riuscito
        log_security_event(
            request=request,
            event_type=SecurityEventType.LOGIN_SUCCESS,
            user=token_request.username,
            status="info",
            details=f"Login riuscito per l'utente {token_request.username}"
        )
        
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=Config.JWT_EXPIRATION * 3600
        )
    else:
        log_security_event(
            request=request,
            event_type=SecurityEventType.LOGIN_FAILURE,
            user=token_request.username,
            status="warning",
            details=f"Tentativo di login fallito per l'utente {token_request.username}"
        )
        raise HTTPException(status_code=401, detail="Credenziali non valide")
    
# Funzione per verificare il token JWT
def verify_token(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, Config.JWT_SECRET, algorithms=[Config.JWT_ALGORITHM])
        # Log del token valido
        log_security_event(
            request=request,
            event_type=SecurityEventType.TOKEN_CREATION,
            user=payload.get("sub", "unknown"),
            details="Token JWT valido"
        )
        return payload
    except jwt.ExpiredSignatureError:
        log_security_event(
            request=request,
            event_type=SecurityEventType.UNAUTHORIZED_ACCESS,
            status="warning",
            details="Tentativo di accesso con token scaduto"
        )
        raise HTTPException(status_code=401, detail="Token scaduto")
    except jwt.InvalidTokenError:
        log_security_event(
            request=request,
            event_type=SecurityEventType.UNAUTHORIZED_ACCESS,
            status="warning",
            details="Tentativo di accesso con token non valido"
        )
        raise HTTPException(status_code=401, detail="Token non valido")
    
@app.get("/test")
def test(request: Request, creds = Depends(security)):  # ← Aggiungi Request
    log_security_event(
        request=request,
        event_type=SecurityEventType.API_REQUEST,
        user=request.headers.get("Authorization", "unknown"),
        status="info",
        details="Accesso all'endpoint /test"
    )
    return {"token": creds.credentials}


# ============= RAG Endpoints =============

# Manager singleton
_rag_manager = None

def get_rag_manager() -> RagManager:
    """Lazy initialization del RagManager"""
    global _rag_manager
    if _rag_manager is None:
        _rag_manager = RagManager()
    return _rag_manager


@app.post("/create_vectorDB/", response_model=CreateVectorDBResponse)
async def create_vector_db(
    request: Request,
    token: dict = Depends(verify_token)
):
    """
    Crea un database vettoriale vuoto.
    Genera automaticamente un hash unico per identificare il database.
    
    Richiede autenticazione JWT.
    Ritorna il db_hash univoco da usare per caricare documenti successivamente.
    """
    # Log dell'operazione
    log_security_event(
        request=request,
        event_type=SecurityEventType.DATABASE_OPERATION,
        user=token.get("sub", "unknown"),
        status="info",
        details="Creazione nuovo vector DB"
    )
    
    manager = get_rag_manager()
    result = await manager.create_vector_db()
    
    # Log del risultato
    log_security_event(
        request=request,
        event_type=SecurityEventType.DATABASE_OPERATION,
        user=token.get("sub", "unknown"),
        status="info" if result.status == "success" else "warning",
        details=f"Vector DB creation result: {result.status} - {result.message}"
    )
    
    if result.status == "error":
        raise HTTPException(status_code=400, detail=result.message)
    
    return result


@app.get("/health/")
async def health_check(request: Request):
    """
    Verifica lo stato dei servizi (Qdrant, Ollama).
    Endpoint pubblico per monitoring.
    """
    manager = get_rag_manager()
    health = manager.model.health_check()
    
    all_healthy = all(health.values())
    
    # Log dell'health check
    log_security_event(
        request=request,
        event_type=SecurityEventType.API_REQUEST,
        user="system",
        status="info" if all_healthy else "warning",
        details=f"Health check - Qdrant: {health['qdrant']}, Ollama: {health['ollama']}"
    )
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "services": health
    }