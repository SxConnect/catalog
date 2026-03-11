"""
Endpoints de health check e monitoramento do sistema.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.utils.retry import get_all_circuit_breaker_stats, reset_circuit_breaker, validate_retry_config
from app.middleware.security import rate_limit_admin
from typing import Dict, Any
import redis
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/")
def health_check():
    """
    Health check básico do sistema.
    
    Returns:
        Status geral do sistema
    """
    return {
        "status": "healthy",
        "service": "SixPet Catalog Engine",
        "version": "1.0.7"
    }

@router.get("/circuit-breakers")
@rate_limit_admin()
def get_circuit_breaker_status():
    """
    Retorna status de todos os circuit breakers.
    
    Returns:
        Estatísticas detalhadas dos circuit breakers
    """
    try:
        stats = get_all_circuit_breaker_stats()
        return {
            "status": "success",
            "circuit_breakers": stats,
            "summary": {
                "total_breakers": len(stats),
                "open_breakers": sum(1 for cb in stats.values() if cb["state"] == "open"),
                "half_open_breakers": sum(1 for cb in stats.values() if cb["state"] == "half_open"),
                "closed_breakers": sum(1 for cb in stats.values() if cb["state"] == "closed")
            }
        }
    except Exception as e:
        logger.error(f"Error getting circuit breaker status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/circuit-breakers/{name}/reset")
@rate_limit_admin()
def reset_circuit_breaker_endpoint(name: str):
    """
    Reseta um circuit breaker específico.
    
    Args:
        name: Nome do circuit breaker (groq_api, web_scraping)
        
    Returns:
        Status da operação
    """
    if name not in ["groq_api", "web_scraping"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid circuit breaker name. Valid options: groq_api, web_scraping"
        )
    
    success = reset_circuit_breaker(name)
    if success:
        return {
            "status": "success",
            "message": f"Circuit breaker '{name}' reset successfully"
        }
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset circuit breaker '{name}'"
        )

@router.get("/services")
@rate_limit_admin()
def get_services_status(db: Session = Depends(get_db)):
    """
    Verifica status de todos os serviços dependentes.
    
    Returns:
        Status de cada serviço (database, redis, etc.)
    """
    services_status = {}
    overall_healthy = True
    
    # Verificar Database
    try:
        db.execute("SELECT 1")
        services_status["database"] = {
            "status": "healthy",
            "message": "PostgreSQL connection OK"
        }
    except Exception as e:
        services_status["database"] = {
            "status": "unhealthy",
            "message": f"Database error: {str(e)}"
        }
        overall_healthy = False
    
    # Verificar Redis
    try:
        redis_client = redis.Redis(host='localhost', port=6381, db=0, decode_responses=True)
        redis_client.ping()
        services_status["redis"] = {
            "status": "healthy",
            "message": "Redis connection OK"
        }
    except Exception as e:
        services_status["redis"] = {
            "status": "unhealthy",
            "message": f"Redis error: {str(e)}"
        }
        overall_healthy = False
    
    # Verificar sistema de retry
    try:
        retry_ok = validate_retry_config()
        services_status["retry_system"] = {
            "status": "healthy" if retry_ok else "unhealthy",
            "message": "Retry system OK" if retry_ok else "Retry system configuration error"
        }
        if not retry_ok:
            overall_healthy = False
    except Exception as e:
        services_status["retry_system"] = {
            "status": "unhealthy",
            "message": f"Retry system error: {str(e)}"
        }
        overall_healthy = False
    
    return {
        "overall_status": "healthy" if overall_healthy else "unhealthy",
        "services": services_status,
        "timestamp": __import__('datetime').datetime.utcnow().isoformat()
    }

@router.get("/metrics")
def get_basic_metrics(db: Session = Depends(get_db)):
    """
    Métricas básicas do sistema (sem autenticação para monitoramento).
    
    Returns:
        Métricas básicas em formato JSON
    """
    try:
        # Contar registros principais
        from app.models import Catalog, Product
        
        total_catalogs = db.query(Catalog).count()
        total_products = db.query(Product).count()
        processing_catalogs = db.query(Catalog).filter(
            Catalog.status == "processing"
        ).count()
        
        # Estatísticas dos circuit breakers
        cb_stats = get_all_circuit_breaker_stats()
        
        return {
            "catalog_metrics": {
                "total_catalogs": total_catalogs,
                "total_products": total_products,
                "processing_catalogs": processing_catalogs
            },
            "circuit_breaker_metrics": {
                name: {
                    "state": stats["state"],
                    "failure_rate": stats["failure_rate"],
                    "total_requests": stats["total_requests"],
                    "total_failures": stats["total_failures"]
                }
                for name, stats in cb_stats.items()
            },
            "timestamp": __import__('datetime').datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return {
            "error": "Failed to get metrics",
            "timestamp": __import__('datetime').datetime.utcnow().isoformat()
        }