"""
Security Logger
"""
from fastapi import Request
from pathlib import Path
from datetime import datetime
import logging
import os
import ipaddress
import unicodedata

# Configurazione directory log

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
os.makedirs(LOG_DIR, exist_ok=True)
def sanitize_log_string(text: str) -> str:
    """Rimuove caratteri Unicode invisibili"""
    if not text:
        return text
    
    cleaned = ''.join(
        char for char in text
        if unicodedata.category(char) not in ('Cc', 'Cf', 'Cs', 'Co', 'Cn')
        or char in ('\n', '\r', '\t')
    )
    
    zero_width_chars = ['\u200b', '\u200c', '\u200d', '\ufeff', '\u2060']
    for char in zero_width_chars:
        cleaned = cleaned.replace(char, '')
    
    return cleaned

# Configurazione logging
security_logger = logging.getLogger("security")
security_logger.setLevel(logging.INFO)

# Rimuovi handler esistenti per evitare duplicati
for handler in security_logger.handlers[:]:
    security_logger.removeHandler(handler)

# Crea formattatore
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# FileHandler
file_handler = logging.FileHandler(LOG_DIR / "api_security.log", encoding='utf-8', errors='replace')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)
security_logger.addHandler(file_handler)

# StreamHandler (console)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(formatter)
security_logger.addHandler(stream_handler)

# Impedisci propagazione al logger root
security_logger.propagate = False
class SecurityEventType:
    """Tipi di eventi di sicurezza"""
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILURE = "LOGIN_FAILURE"
    TOKEN_CREATION = "TOKEN_CREATION"
    FILE_UPLOAD = "FILE_UPLOAD"
    DOCUMENT_DELETE = "DOCUMENT_DELETE"
    QUERY_EXECUTION = "QUERY_EXECUTION"
    UNAUTHORIZED_ACCESS = "UNAUTHORIZED_ACCESS"
    INVALID_INPUT = "INVALID_INPUT"
    DATABASE_OPERATION = "DATABASE_OPERATION"
    API_REQUEST = "API_REQUEST"
def get_client_ip(request: Request) -> str:
    """Estrae IP del client"""
    if not request:
        return "no-request"
    
    try:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        elif request.client:
            ip = request.client.host
        else:
            return "no-client-info"
        
        ipaddress.ip_address(ip)
        return ip
    except (ValueError, AttributeError, TypeError):
        return "invalid-ip"
def log_security_event(
    request: Request,
    event_type: str,
    user: str = "anonymous",
    status: str = "info",
    details: str = None
):
    """Registra evento di sicurezza"""
    try:
        client_ip = get_client_ip(request) if request else "no-request"
        user_agent = request.headers.get("User-Agent", "unknown") if request and hasattr(request, 'headers') else "unknown"
        method = request.method if request and hasattr(request, 'method') else "unknown"
        url = str(request.url) if request and hasattr(request, 'url') else "no-url"
    except (AttributeError, TypeError):
        client_ip = "error-extracting-ip"
        user_agent = "error-extracting-ua"
        method = "unknown"
        url = "error-extracting-url"
    
    sanitized_details = sanitize_log_string(details) if details else ""
    
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "user": user,
        "client_ip": client_ip,
        "user_agent": user_agent,
        "method": method,
        "url": url,
        "details": sanitized_details
    }
    
    log_message = f"SECURITY: {event_type} - User: {user} - IP: {client_ip} - {sanitized_details or 'no details'}"
    
    if status == "warning":
        security_logger.warning(log_message)
    elif status == "error":
        security_logger.error(log_message)
    elif status == "critical":
        security_logger.critical(log_message)
    else:
        security_logger.info(log_message)
    
    return log_data