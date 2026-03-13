from fastapi import APIRouter, HTTPException
from app.logger import logger

router = APIRouter()

@router.get("/health")
async def sitemap_health():
    """Health check para o módulo sitemap"""
    return {"status": "ok", "module": "sitemap"}

@router.get("/debug")
async def debug_routes():
    """Debug: endpoint de teste"""
    return {"status": "debug", "message": "Debug endpoint is working"}

@router.get("/smart-extract")
async def smart_extract_products(url: str, max_products: int = 20):
    """Extração inteligente: detecta automaticamente se é produto ou categoria"""
    return {
        "status": "success",
        "message": "Smart extraction endpoint is working",
        "url": url,
        "max_products": max_products
    }

@router.get("/products")
async def list_extracted_products(limit: int = 10):
    """Lista os produtos extraídos de URLs"""
    return {
        "status": "success",
        "message": "Products endpoint is working",
        "limit": limit,
        "products": []
    }

@router.post("/test-scrape")
async def test_scrape_url(url: str):
    """Testa a extração de dados de uma URL específica"""
    return {
        "status": "success",
        "message": "Test scrape endpoint is working",
        "url": url
    }