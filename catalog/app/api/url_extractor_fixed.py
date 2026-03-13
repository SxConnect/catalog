from fastapi import APIRouter, HTTPException, Depends, Query
from app.logger import logger
from app.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import text
import httpx
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
from typing import Optional

router = APIRouter()

# ✅ ROTAS ESTÁTICAS PRIMEIRO - ORDEM CRÍTICA PARA FASTAPI
@router.get("/health")
async def health_check():
    """Health check para o módulo sitemap"""
    return {"status": "ok", "module": "sitemap"}

@router.get("/debug") 
async def debug_info():
    """Debug: informações do sistema"""
    return {"status": "debug", "message": "Debug endpoint working", "routes": 4}

@router.get("/products")
async def list_products(limit: int = Query(10), db: Session = Depends(get_db)):
    """Lista produtos extraídos"""
    try:
        return {"status": "success", "products": [], "limit": limit}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/smart-extract")
async def smart_extract(url: str = Query(...), max_products: int = Query(20)):
    """Extração inteligente via query parameter"""
    try:
        return {
            "status": "success", 
            "url": url, 
            "max_products": max_products,
            "message": "Smart extraction working"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-scrape")
async def test_scrape(url: str = Query(...)):
    """Teste de scraping"""
    try:
        return {"status": "success", "url": url, "message": "Test scrape working"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))