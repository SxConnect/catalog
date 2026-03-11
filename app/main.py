from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import catalog, products, admin, search, deduplication, sitemap, status, health
from app.middleware.security import setup_security

app = FastAPI(title="SixPet Catalog Engine", version="1.0.7")

# Configurar segurança (rate limiting, headers, validação)
setup_security(app)

# Aumentar limite de upload para 50MB (conforme especificação de segurança)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://catalog.sxconnect.com.br",
        "https://catalog-api.sxconnect.com.br"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

app.include_router(catalog.router, prefix="/api/catalog", tags=["catalog"])
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(deduplication.router, prefix="/api/deduplication", tags=["deduplication"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(sitemap.router, prefix="/api/sitemap", tags=["sitemap"])
app.include_router(status.router, prefix="/api/status", tags=["status"])
app.include_router(health.router, prefix="/api/health", tags=["health"])

@app.get("/")
def root():
    return {"message": "SixPet Catalog Engine API", "version": "1.0.7"}

@app.get("/health")
def health():
    return {"status": "healthy"}
