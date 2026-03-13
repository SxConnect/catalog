from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi import Depends, HTTPException
from app.api import catalog, products, admin, search, deduplication, status, health
from app.api import url_extractor_fixed as sitemap
from app.monitoring.metrics import get_prometheus_metrics, get_metrics_content_type
import secrets
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SixPet Catalog Engine", version="1.0.8")

# Configurar CORS com máxima permissividade para resolver problemas de conectividade
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todas as origens temporariamente
    allow_credentials=False,  # Desabilitar credentials quando allow_origins=["*"]
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Configurar segurança (rate limiting, headers, validação) - APÓS CORS
try:
    from app.middleware.security import setup_security
    setup_security(app)
    logger.info("Security middleware configured successfully")
except Exception as e:
    logger.error(f"Failed to configure security middleware: {e}")
    logger.warning("Continuing without security middleware")

app.include_router(catalog.router, prefix="/api/catalog", tags=["catalog"])
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(deduplication.router, prefix="/api/deduplication", tags=["deduplication"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(sitemap.router, prefix="/api/sitemap", tags=["sitemap"])
app.include_router(status.router, prefix="/api/status", tags=["status"])
app.include_router(health.router, prefix="/api/health", tags=["health"])

# Autenticação para métricas Prometheus
security = HTTPBasic()

def verify_metrics_auth(credentials: HTTPBasicCredentials = Depends(security)):
    """Verifica autenticação para endpoint de métricas."""
    correct_username = "admin"
    correct_password = "metrics123"
    
    is_correct_username = secrets.compare_digest(credentials.username, correct_username)
    is_correct_password = secrets.compare_digest(credentials.password, correct_password)
    
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return True

@app.get("/metrics", response_class=PlainTextResponse)
def prometheus_metrics(authenticated: bool = Depends(verify_metrics_auth)):
    """
    Endpoint de métricas Prometheus (protegido por autenticação básica).
    
    Credenciais: admin / metrics123
    """
    metrics_data = get_prometheus_metrics()
    return PlainTextResponse(
        content=metrics_data,
        media_type=get_metrics_content_type()
    )

@app.get("/")
def root():
    return {"message": "SixPet Catalog Engine API", "version": "1.0.8", "status": "running"}

@app.get("/health")
def health():
    return {"status": "healthy", "version": "1.0.8"}
