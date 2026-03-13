from fastapi import APIRouter, HTTPException
from app.logger import logger

router = APIRouter()

@router.get("/health")
async def sitemap_health():
    """Health check para o módulo sitemap"""
    return {"status": "ok", "module": "sitemap"}

@router.get("/test")
async def test_endpoint():
    """Endpoint de teste simples"""
    return {"status": "success", "message": "Sitemap router is working"}