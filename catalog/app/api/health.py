"""
Endpoints de health check e monitoramento do sistema.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import PlainTextResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.utils.retry import get_all_circuit_breaker_stats, reset_circuit_breaker, validate_retry_config
from app.utils.cache import CacheStats, invalidate_all_cache, invalidate_products_cache, invalidate_stats_cache, validate_cache_config
from app.monitoring.metrics import get_prometheus_metrics, get_metrics_content_type, get_comprehensive_health_status
from app.middleware.security import rate_limit_admin
from typing import Dict, Any
import redis
import logging
import secrets

logger = logging.getLogger(__name__)
router = APIRouter()

# Autenticação básica para endpoint de métricas
security = HTTPBasic()

def verify_metrics_auth(credentials: HTTPBasicCredentials = Depends(security)):
    """
    Verifica autenticação básica para endpoint de métricas.
    
    Args:
        credentials: Credenciais HTTP Basic
        
    Returns:
        True se autenticado
        
    Raises:
        HTTPException: Se credenciais inválidas
    """
    # TODO: Mover para variáveis de ambiente em produção
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
def get_circuit_breaker_status(request: Request):
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
def reset_circuit_breaker_endpoint(request: Request, name: str):
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
def get_services_status(request: Request, db: Session = Depends(get_db)):
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
    
    # Verificar sistema de cache
    try:
        cache_ok = validate_cache_config()
        services_status["cache_system"] = {
            "status": "healthy" if cache_ok else "unhealthy",
            "message": "Cache system OK" if cache_ok else "Cache system configuration error"
        }
        if not cache_ok:
            overall_healthy = False
    except Exception as e:
        services_status["cache_system"] = {
            "status": "unhealthy",
            "message": f"Cache system error: {str(e)}"
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

@router.get("/cache")
@rate_limit_admin()
def get_cache_status(request: Request):
    """
    Retorna status e estatísticas do cache Redis.
    
    Returns:
        Estatísticas detalhadas do cache
    """
    try:
        stats = CacheStats.get_stats()
        return {
            "status": "success",
            "cache_stats": stats,
            "cache_config": {
                "default_ttl": 300,
                "products_ttl": 300,
                "stats_ttl": 60,
                "dedup_ttl": 86400,
                "search_ttl": 180
            }
        }
    except Exception as e:
        logger.error(f"Error getting cache status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cache/invalidate")
@rate_limit_admin()
def invalidate_cache(
    request: Request,
    cache_type: str = Query(..., pattern="^(all|products|stats)$")
):
    """
    Invalida cache específico ou todo o cache.
    
    Args:
        cache_type: Tipo de cache a invalidar (all, products, stats)
        
    Returns:
        Número de chaves invalidadas
    """
    try:
        if cache_type == "all":
            keys_deleted = invalidate_all_cache()
            message = f"All cache invalidated - {keys_deleted} keys deleted"
        elif cache_type == "products":
            keys_deleted = invalidate_products_cache()
            message = f"Products cache invalidated - {keys_deleted} keys deleted"
        elif cache_type == "stats":
            keys_deleted = invalidate_stats_cache()
            message = f"Stats cache invalidated - {keys_deleted} keys deleted"
        else:
            raise HTTPException(status_code=400, detail="Invalid cache type")
        
        logger.info(f"Cache invalidation requested: {message}")
        
        return {
            "status": "success",
            "message": message,
            "keys_deleted": keys_deleted,
            "cache_type": cache_type
        }
        
    except Exception as e:
        logger.error(f"Error invalidating cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cache/metrics")
def get_cache_metrics():
    """
    Métricas de cache para monitoramento (sem autenticação).
    
    Returns:
        Métricas básicas do cache em formato JSON
    """
    try:
        stats = CacheStats.get_stats()
        
        return {
            "cache_metrics": {
                "total_keys": stats.get("total_keys", 0),
                "memory_usage": stats.get("memory_usage", "N/A"),
                "keys_by_prefix": stats.get("keys_by_prefix", {}),
                "connected_clients": stats.get("connected_clients", 0),
                "uptime_seconds": stats.get("uptime_seconds", 0)
            },
            "timestamp": __import__('datetime').datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting cache metrics: {e}")
        return {
            "error": "Failed to get cache metrics",
            "timestamp": __import__('datetime').datetime.utcnow().isoformat()
        }

@router.get("/comprehensive")
@rate_limit_admin()
def get_comprehensive_health(request: Request):
    """
    Health check abrangente com todas as informações do sistema.
    
    Returns:
        Status detalhado de todos os componentes, métricas e alertas
    """
    try:
        health_status = get_comprehensive_health_status()
        return health_status
    except Exception as e:
        logger.error(f"Error getting comprehensive health status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/monitoring")
@rate_limit_admin()
def get_monitoring_status(request: Request):
    """
    Status específico do sistema de monitoramento.
    
    Returns:
        Informações sobre coleta de métricas e instrumentação
    """
    try:
        from app.monitoring.metrics import metrics_collector
        
        # Coletar métricas atuais
        metrics_collector.collect_all_metrics()
        
        return {
            "status": "active",
            "metrics_collected": True,
            "prometheus_endpoint": "/metrics",
            "authentication": "basic_auth_required",
            "collectors": {
                "system_metrics": True,
                "cache_metrics": True,
                "circuit_breaker_metrics": True,
                "database_metrics": True
            },
            "instrumentation": {
                "api_requests": True,
                "pdf_extraction": True,
                "web_scraping": True,
                "enrichment": True
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting monitoring status: {e}")
        raise HTTPException(status_code=500, detail=str(e))