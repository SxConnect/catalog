import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """Formatter que gera logs em JSON"""
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Adicionar campos extras
        if hasattr(record, "catalog_id"):
            log_data["catalog_id"] = record.catalog_id
        if hasattr(record, "product_id"):
            log_data["product_id"] = record.product_id
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        
        return json.dumps(log_data)

def setup_logger(name: str = "sixpet_catalog") -> logging.Logger:
    """Configura logger com handlers para console e arquivo"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Evitar duplicação de handlers
    if logger.handlers:
        return logger
    
    # Handler para console (formato legível)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    
    # Handler para arquivo (formato JSON)
    log_dir = Path("/app/logs")
    log_dir.mkdir(exist_ok=True)
    
    file_handler = RotatingFileHandler(
        log_dir / "app.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(JSONFormatter())
    
    # Handler para erros (arquivo separado)
    error_handler = RotatingFileHandler(
        log_dir / "errors.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter())
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    
    return logger

# Logger global
logger = setup_logger()

# Funções auxiliares para logging contextual
def log_catalog_event(catalog_id: int, message: str, level: str = "info"):
    """Log de eventos relacionados a catálogos"""
    extra = {"catalog_id": catalog_id}
    getattr(logger, level)(message, extra=extra)

def log_product_event(product_id: int, message: str, level: str = "info"):
    """Log de eventos relacionados a produtos"""
    extra = {"product_id": product_id}
    getattr(logger, level)(message, extra=extra)

def log_api_request(endpoint: str, method: str, status_code: int, duration_ms: float):
    """Log de requisições API"""
    logger.info(
        f"API {method} {endpoint} - {status_code} - {duration_ms:.2f}ms"
    )

def log_error(error: Exception, context: dict = None):
    """Log de erros com contexto"""
    logger.error(
        f"Error: {str(error)}",
        exc_info=True,
        extra=context or {}
    )
