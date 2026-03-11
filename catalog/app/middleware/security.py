"""
Middleware de segurança para o SixPet Catalog Engine.

Este módulo implementa rate limiting, validação de entrada, headers de segurança
e outras medidas de proteção para a API.
"""

import re
import redis
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from pydantic import BaseModel, validator, Field
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging
import os

logger = logging.getLogger(__name__)

# Configuração do Redis para rate limiting usando variáveis de ambiente
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
redis_client = redis.from_url(REDIS_URL)

# Inicializar limiter
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=REDIS_URL,
    default_limits=["200 per hour"]
)

class SecurityConfig:
    """Configurações de segurança."""
    
    # Tamanho máximo de arquivo PDF (50MB)
    MAX_PDF_SIZE = 50 * 1024 * 1024
    
    # Extensões de arquivo permitidas
    ALLOWED_EXTENSIONS = ['.pdf']
    
    # Domínios permitidos para sitemap (whitelist configurável)
    ALLOWED_DOMAINS = [
        'bbbpet.com.br',
        'petshop.com.br',
        'mundopet.com.br',
        'petlove.com.br',
        'cobasi.com.br',
        'petz.com.br',
        'americanas.com.br',
        'mercadolivre.com.br',
        'amazon.com.br',
        'magazineluiza.com.br',
        'casasbahia.com.br',
        'extra.com.br',
        'pontofrio.com.br',
        'submarino.com.br',
        'shoptime.com.br',
        'walmart.com.br',
        'carrefour.com.br',
        'localhost',  # Para desenvolvimento
        '127.0.0.1',  # Para desenvolvimento
    ]
    
    # Padrões XSS para sanitização
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'<iframe[^>]*>.*?</iframe>',
        r'<object[^>]*>.*?</object>',
        r'<embed[^>]*>.*?</embed>',
        r'<link[^>]*>',
        r'<meta[^>]*>',
        r'<style[^>]*>.*?</style>',
    ]
    
    # Headers de segurança
    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Content-Security-Policy": (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        ),
    }


class FileValidationError(Exception):
    """Exceção para erros de validação de arquivo."""
    pass


class SecurityValidator:
    """Validador de segurança para entrada de dados."""
    
    @staticmethod
    def sanitize_text(text: str) -> str:
        """
        Sanitiza texto contra XSS e outras injeções.
        
        Args:
            text: Texto a ser sanitizado
            
        Returns:
            Texto sanitizado
        """
        if not text or not isinstance(text, str):
            return ""
        
        # Remove padrões XSS
        sanitized = text
        for pattern in SecurityConfig.XSS_PATTERNS:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove caracteres de controle
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', sanitized)
        
        # Limita tamanho
        return sanitized[:10000]  # Máximo 10k caracteres
    
    @staticmethod
    def validate_pdf_file(filename: str, file_size: int) -> None:
        """
        Valida arquivo PDF.
        
        Args:
            filename: Nome do arquivo
            file_size: Tamanho do arquivo em bytes
            
        Raises:
            FileValidationError: Se arquivo for inválido
        """
        if not filename:
            raise FileValidationError("Filename is required")
        
        # Validar extensão
        file_ext = '.' + filename.split('.')[-1].lower() if '.' in filename else ''
        if file_ext not in SecurityConfig.ALLOWED_EXTENSIONS:
            raise FileValidationError(f"Invalid file extension. Allowed: {SecurityConfig.ALLOWED_EXTENSIONS}")
        
        # Validar tamanho
        if file_size > SecurityConfig.MAX_PDF_SIZE:
            size_mb = file_size / (1024 * 1024)
            max_mb = SecurityConfig.MAX_PDF_SIZE / (1024 * 1024)
            raise FileValidationError(f"File too large: {size_mb:.1f}MB. Maximum allowed: {max_mb}MB")
        
        # Validar nome do arquivo
        if not re.match(r'^[a-zA-Z0-9._\-\s()àáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞß]+$', filename):
            raise FileValidationError("Invalid characters in filename")
    
    @staticmethod
    def validate_sitemap_url(url: str) -> None:
        """
        Valida URL de sitemap contra whitelist de domínios.
        
        Args:
            url: URL do sitemap
            
        Raises:
            HTTPException: Se domínio não for permitido
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove porta se presente
            if ':' in domain:
                domain = domain.split(':')[0]
            
            # Verificar se domínio está na whitelist
            allowed = False
            for allowed_domain in SecurityConfig.ALLOWED_DOMAINS:
                if domain == allowed_domain or domain.endswith('.' + allowed_domain):
                    allowed = True
                    break
            
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Domain '{domain}' is not in the allowed domains list"
                )
                
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid URL format: {str(e)}"
            )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware para adicionar headers de segurança."""
    
    async def dispatch(self, request: Request, call_next):
        """Processa request e adiciona headers de segurança."""
        response = await call_next(request)
        
        # Adicionar headers de segurança
        for header, value in SecurityConfig.SECURITY_HEADERS.items():
            response.headers[header] = value
        
        # Adicionar HSTS se HTTPS
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


# Modelos Pydantic com validação de segurança
class SecureUploadFile(BaseModel):
    """Modelo para validação segura de upload de arquivo."""
    
    filename: str = Field(..., min_length=1, max_length=255)
    content_type: str = Field(..., pattern=r'^application/pdf$')
    size: int = Field(..., gt=0, le=SecurityConfig.MAX_PDF_SIZE)
    
    @validator('filename')
    def validate_filename(cls, v):
        """Valida nome do arquivo."""
        if not v:
            raise ValueError("Filename is required")
        
        # Sanitizar nome do arquivo
        sanitized = SecurityValidator.sanitize_text(v)
        
        # Validar extensão
        if not sanitized.lower().endswith('.pdf'):
            raise ValueError("Only PDF files are allowed")
        
        # Validar caracteres
        if not re.match(r'^[a-zA-Z0-9._\-\s()àáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞß]+$', sanitized):
            raise ValueError("Invalid characters in filename")
        
        return sanitized


class SecureSitemapRequest(BaseModel):
    """Modelo para validação segura de request de sitemap."""
    
    sitemap_url: str = Field(..., min_length=10, max_length=2000)
    catalog_id: int = Field(..., gt=0)
    url_filter: Optional[str] = Field(None, max_length=500)
    max_products: Optional[int] = Field(None, gt=0, le=1000)
    auto_save: bool = True
    
    @validator('sitemap_url')
    def validate_sitemap_url(cls, v):
        """Valida URL do sitemap."""
        # Sanitizar URL
        sanitized = SecurityValidator.sanitize_text(v)
        
        # Validar formato
        if not sanitized.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")
        
        # Validar domínio
        SecurityValidator.validate_sitemap_url(sanitized)
        
        return sanitized
    
    @validator('url_filter')
    def validate_url_filter(cls, v):
        """Valida filtro de URL."""
        if v is None:
            return v
        
        # Sanitizar filtro
        sanitized = SecurityValidator.sanitize_text(v)
        
        # Validar regex (tentar compilar)
        try:
            re.compile(sanitized)
        except re.error:
            raise ValueError("Invalid regex pattern in url_filter")
        
        return sanitized


class SecureTextInput(BaseModel):
    """Modelo para validação segura de entrada de texto."""
    
    text: str = Field(..., min_length=1, max_length=10000)
    
    @validator('text')
    def sanitize_text(cls, v):
        """Sanitiza texto de entrada."""
        return SecurityValidator.sanitize_text(v)


# Rate limiting decorators para endpoints específicos
def rate_limit_upload():
    """Rate limit para upload de catálogos: 10 req/min por IP."""
    return limiter.limit("10/minute")

def rate_limit_products():
    """Rate limit para busca de produtos: 60 req/min por IP."""
    return limiter.limit("60/minute")

def rate_limit_sitemap():
    """Rate limit para import de sitemap: 5 req/min por IP."""
    return limiter.limit("5/minute")

def rate_limit_admin():
    """Rate limit para endpoints admin: 3 req/min por IP."""
    return limiter.limit("3/minute")


# Função para configurar rate limiting na aplicação
def setup_rate_limiting(app):
    """
    Configura rate limiting na aplicação FastAPI.
    
    Args:
        app: Instância da aplicação FastAPI
    """
    # Adicionar middleware do SlowAPI
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
    
    logger.info("Rate limiting configured successfully")


# Função para configurar headers de segurança
def setup_security_headers(app):
    """
    Configura headers de segurança na aplicação FastAPI.
    
    Args:
        app: Instância da aplicação FastAPI
    """
    app.add_middleware(SecurityHeadersMiddleware)
    logger.info("Security headers middleware configured successfully")


# Função para validar configuração de segurança
def validate_security_config():
    """Valida configuração de segurança."""
    try:
        # Testar conexão Redis
        redis_client.ping()
        logger.info("Redis connection for rate limiting: OK")
        
        # Validar configurações
        assert SecurityConfig.MAX_PDF_SIZE > 0, "MAX_PDF_SIZE must be positive"
        assert len(SecurityConfig.ALLOWED_EXTENSIONS) > 0, "ALLOWED_EXTENSIONS cannot be empty"
        assert len(SecurityConfig.ALLOWED_DOMAINS) > 0, "ALLOWED_DOMAINS cannot be empty"
        
        logger.info("Security configuration validation: OK")
        return True
        
    except Exception as e:
        logger.error(f"Security configuration validation failed: {e}")
        return False


# Utilitários para logging de segurança
def log_security_event(event_type: str, details: Dict[str, Any], request: Request = None):
    """
    Registra evento de segurança.
    
    Args:
        event_type: Tipo do evento (rate_limit, file_validation, etc.)
        details: Detalhes do evento
        request: Request HTTP (opcional)
    """
    log_data = {
        "event_type": event_type,
        "timestamp": __import__('datetime').datetime.utcnow().isoformat(),
        **details
    }
    
    if request:
        log_data.update({
            "client_ip": get_remote_address(request),
            "user_agent": request.headers.get("user-agent", ""),
            "endpoint": str(request.url.path),
            "method": request.method
        })
    
    logger.warning(f"SECURITY_EVENT: {log_data}")


# Função principal para configurar toda a segurança
def setup_security(app):
    """
    Configura todos os aspectos de segurança da aplicação.
    
    Args:
        app: Instância da aplicação FastAPI
    """
    # Validar configuração
    if not validate_security_config():
        raise RuntimeError("Security configuration validation failed")
    
    # Configurar rate limiting
    setup_rate_limiting(app)
    
    # Configurar headers de segurança
    setup_security_headers(app)
    
    logger.info("Security setup completed successfully")