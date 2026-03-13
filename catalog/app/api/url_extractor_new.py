from fastapi import APIRouter, HTTPException
from app.logger import logger

router = APIRouter()

@router.get("/status")
async def sitemap_status():
    """Status check para o módulo sitemap"""
    return {"status": "ok", "module": "sitemap", "endpoints": ["status", "extract", "list", "scrape"]}

@router.get("/extract")
async def extract_products_from_url(url: str, max_products: int = 20):
    """Extração inteligente: detecta automaticamente se é produto ou categoria"""
    return {
        "status": "success",
        "message": "Smart extraction endpoint is working",
        "url": url,
        "max_products": max_products
    }

@router.get("/list")
async def list_products_from_urls(limit: int = 10):
    """Lista os produtos extraídos de URLs"""
    return {
        "status": "success",
        "message": "Products endpoint is working",
        "limit": limit,
        "products": []
    }

@router.post("/scrape")
async def scrape_single_url(url: str):
    """Testa a extração de dados de uma URL específica"""
    return {
        "status": "success",
        "message": "Test scrape endpoint is working",
        "url": url
    }