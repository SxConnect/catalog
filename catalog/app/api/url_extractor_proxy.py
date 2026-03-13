"""
Proxy endpoints para o microserviço URL Extractor
Encaminha requisições para o serviço independente na porta 8001
"""
from fastapi import APIRouter, HTTPException, Query
import httpx
import os
from app.logger import logger
from typing import Optional

router = APIRouter()

# URL do microserviço
URL_EXTRACTOR_SERVICE = os.getenv("URL_EXTRACTOR_SERVICE", "http://url-extractor:8001")

@router.get("/health")
async def health_check():
    """Health check - proxy para o microserviço"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{URL_EXTRACTOR_SERVICE}/health")
            return response.json()
    except Exception as e:
        logger.error(f"Error connecting to URL extractor service: {e}")
        raise HTTPException(status_code=503, detail="URL extractor service unavailable")

@router.get("/debug")
async def debug_info():
    """Debug info - proxy para o microserviço"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{URL_EXTRACTOR_SERVICE}/debug")
            return response.json()
    except Exception as e:
        logger.error(f"Error connecting to URL extractor service: {e}")
        raise HTTPException(status_code=503, detail="URL extractor service unavailable")

@router.get("/products")
async def list_products(limit: int = Query(10, description="Maximum number of products")):
    """List products - proxy para o microserviço"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{URL_EXTRACTOR_SERVICE}/products",
                params={"limit": limit}
            )
            return response.json()
    except Exception as e:
        logger.error(f"Error connecting to URL extractor service: {e}")
        raise HTTPException(status_code=503, detail="URL extractor service unavailable")

@router.get("/smart-extract")
async def smart_extract(
    url: str = Query(..., description="URL to extract products from"),
    max_products: int = Query(20, description="Maximum products to extract")
):
    """Smart extraction - proxy para o microserviço"""
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:  # Timeout maior para extração
            response = await client.get(
                f"{URL_EXTRACTOR_SERVICE}/smart-extract",
                params={"url": url, "max_products": max_products}
            )
            return response.json()
    except Exception as e:
        logger.error(f"Error connecting to URL extractor service: {e}")
        raise HTTPException(status_code=503, detail="URL extractor service unavailable")

@router.post("/test-scrape")
async def test_scrape(url: str = Query(..., description="URL to test scraping")):
    """Test scraping - proxy para o microserviço"""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{URL_EXTRACTOR_SERVICE}/test-scrape",
                params={"url": url}
            )
            return response.json()
    except Exception as e:
        logger.error(f"Error connecting to URL extractor service: {e}")
        raise HTTPException(status_code=503, detail="URL extractor service unavailable")