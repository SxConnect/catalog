"""
Sistema de Cache Redis para o SixPet Catalog Engine.

Este módulo implementa decorators para cache de queries frequentes
com TTL configurável e invalidação automática.
"""

import json
import hashlib
import logging
from typing import Any, Optional, Callable, Dict, Union
from functools import wraps
import redis
from datetime import datetime, timedelta
import pickle

logger = logging.getLogger(__name__)

# Configuração do Redis para cache
cache_redis = redis.Redis(host='localhost', port=6381, db=3, decode_responses=False)

class CacheConfig:
    """Configurações de cache."""
    
    # TTLs padrão (em segundos)
    DEFAULT_TTL = 300  # 5 minutos
    PRODUCTS_LIST_TTL = 300  # 5 minutos
    DASHBOARD_STATS_TTL = 60  # 1 minuto
    DEDUPLICATION_TTL = 86400  # 24 horas
    SEARCH_RESULTS_TTL = 180  # 3 minutos
    
    # Prefixos de chave
    KEY_PREFIX = "sixpet"
    PRODUCTS_PREFIX = f"{KEY_PREFIX}:products"
    STATS_PREFIX = f"{KEY_PREFIX}:stats"
    DEDUP_PREFIX = f"{KEY_PREFIX}:dedup"
    SEARCH_PREFIX = f"{KEY_PREFIX}:search"
    
    # Configurações de serialização
    USE_COMPRESSION = True
    MAX_KEY_LENGTH = 250


class CacheStats:
    """Estatísticas do cache."""
    
    @staticmethod
    def get_stats() -> Dict[str, Any]:
        """
        Retorna estatísticas do cache Redis.
        
        Returns:
            Dicionário com estatísticas do cache
        """
        try:
            info = cache_redis.info()
            
            # Contar chaves por prefixo
            all_keys = cache_redis.keys(f"{CacheConfig.KEY_PREFIX}:*")
            
            prefixes = {
                "products": 0,
                "stats": 0,
                "dedup": 0,
                "search": 0,
                "other": 0
            }
            
            for key in all_keys:
                key_str = key.decode('utf-8') if isinstance(key, bytes) else key
                if ":products:" in key_str:
                    prefixes["products"] += 1
                elif ":stats:" in key_str:
                    prefixes["stats"] += 1
                elif ":dedup:" in key_str:
                    prefixes["dedup"] += 1
                elif ":search:" in key_str:
                    prefixes["search"] += 1
                else:
                    prefixes["other"] += 1
            
            return {
                "total_keys": len(all_keys),
                "keys_by_prefix": prefixes,
                "memory_usage": info.get("used_memory_human", "N/A"),
                "hit_rate": "N/A",  # Redis não fornece hit rate nativo
                "connected_clients": info.get("connected_clients", 0),
                "uptime_seconds": info.get("uptime_in_seconds", 0),
                "redis_version": info.get("redis_version", "unknown")
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {
                "error": str(e),
                "total_keys": 0,
                "keys_by_prefix": {},
                "memory_usage": "N/A"
            }


def _generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Gera chave de cache baseada nos argumentos.
    
    Args:
        prefix: Prefixo da chave
        *args: Argumentos posicionais
        **kwargs: Argumentos nomeados
        
    Returns:
        Chave de cache única
    """
    # Criar string única baseada nos argumentos
    key_data = {
        "args": args,
        "kwargs": sorted(kwargs.items())  # Ordenar para consistência
    }
    
    # Gerar hash dos argumentos
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    key_hash = hashlib.md5(key_str.encode()).hexdigest()
    
    # Construir chave final
    cache_key = f"{prefix}:{key_hash}"
    
    # Truncar se muito longa
    if len(cache_key) > CacheConfig.MAX_KEY_LENGTH:
        cache_key = cache_key[:CacheConfig.MAX_KEY_LENGTH]
    
    return cache_key


def _serialize_value(value: Any) -> bytes:
    """
    Serializa valor para armazenamento no Redis.
    
    Args:
        value: Valor a ser serializado
        
    Returns:
        Valor serializado em bytes
    """
    try:
        # Usar pickle para serialização completa
        serialized = pickle.dumps(value)
        
        # Comprimir se configurado
        if CacheConfig.USE_COMPRESSION:
            import gzip
            serialized = gzip.compress(serialized)
        
        return serialized
        
    except Exception as e:
        logger.error(f"Error serializing cache value: {e}")
        raise


def _deserialize_value(data: bytes) -> Any:
    """
    Deserializa valor do Redis.
    
    Args:
        data: Dados serializados
        
    Returns:
        Valor deserializado
    """
    try:
        # Descomprimir se necessário
        if CacheConfig.USE_COMPRESSION:
            import gzip
            data = gzip.decompress(data)
        
        # Deserializar com pickle
        return pickle.loads(data)
        
    except Exception as e:
        logger.error(f"Error deserializing cache value: {e}")
        raise


def cached(
    ttl: int = CacheConfig.DEFAULT_TTL,
    prefix: str = CacheConfig.KEY_PREFIX,
    key_func: Optional[Callable] = None
):
    """
    Decorator para cache de funções com TTL configurável.
    
    Args:
        ttl: Time to live em segundos
        prefix: Prefixo da chave de cache
        key_func: Função personalizada para gerar chave (opcional)
    
    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Gerar chave de cache
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = _generate_cache_key(prefix, func.__name__, *args, **kwargs)
            
            try:
                # Tentar buscar do cache
                cached_data = cache_redis.get(cache_key)
                if cached_data is not None:
                    logger.debug(f"Cache HIT for key: {cache_key}")
                    return _deserialize_value(cached_data)
                
                # Cache miss - executar função
                logger.debug(f"Cache MISS for key: {cache_key}")
                result = func(*args, **kwargs)
                
                # Armazenar no cache
                if result is not None:  # Não cachear None
                    serialized = _serialize_value(result)
                    cache_redis.setex(cache_key, ttl, serialized)
                    logger.debug(f"Cached result for key: {cache_key} (TTL: {ttl}s)")
                
                return result
                
            except Exception as e:
                logger.error(f"Cache error for key {cache_key}: {e}")
                # Em caso de erro no cache, executar função normalmente
                return func(*args, **kwargs)
        
        # Adicionar método para invalidar cache
        def invalidate_cache(*args, **kwargs):
            """Invalida cache para os argumentos específicos."""
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = _generate_cache_key(prefix, func.__name__, *args, **kwargs)
            
            try:
                cache_redis.delete(cache_key)
                logger.info(f"Cache invalidated for key: {cache_key}")
                return True
            except Exception as e:
                logger.error(f"Error invalidating cache for key {cache_key}: {e}")
                return False
        
        wrapper.invalidate_cache = invalidate_cache
        return wrapper
    
    return decorator


def cached_async(
    ttl: int = CacheConfig.DEFAULT_TTL,
    prefix: str = CacheConfig.KEY_PREFIX,
    key_func: Optional[Callable] = None
):
    """
    Decorator para cache de funções assíncronas.
    
    Args:
        ttl: Time to live em segundos
        prefix: Prefixo da chave de cache
        key_func: Função personalizada para gerar chave (opcional)
    
    Returns:
        Decorator function para funções async
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Gerar chave de cache
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = _generate_cache_key(prefix, func.__name__, *args, **kwargs)
            
            try:
                # Tentar buscar do cache
                cached_data = cache_redis.get(cache_key)
                if cached_data is not None:
                    logger.debug(f"Cache HIT for key: {cache_key}")
                    return _deserialize_value(cached_data)
                
                # Cache miss - executar função
                logger.debug(f"Cache MISS for key: {cache_key}")
                result = await func(*args, **kwargs)
                
                # Armazenar no cache
                if result is not None:  # Não cachear None
                    serialized = _serialize_value(result)
                    cache_redis.setex(cache_key, ttl, serialized)
                    logger.debug(f"Cached result for key: {cache_key} (TTL: {ttl}s)")
                
                return result
                
            except Exception as e:
                logger.error(f"Cache error for key {cache_key}: {e}")
                # Em caso de erro no cache, executar função normalmente
                return await func(*args, **kwargs)
        
        # Adicionar método para invalidar cache
        async def invalidate_cache(*args, **kwargs):
            """Invalida cache para os argumentos específicos."""
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = _generate_cache_key(prefix, func.__name__, *args, **kwargs)
            
            try:
                cache_redis.delete(cache_key)
                logger.info(f"Cache invalidated for key: {cache_key}")
                return True
            except Exception as e:
                logger.error(f"Error invalidating cache for key {cache_key}: {e}")
                return False
        
        wrapper.invalidate_cache = invalidate_cache
        return wrapper
    
    return decorator


# Decorators específicos para casos de uso comuns
def cache_products_list(ttl: int = CacheConfig.PRODUCTS_LIST_TTL):
    """Cache para listagem de produtos."""
    return cached(
        ttl=ttl,
        prefix=CacheConfig.PRODUCTS_PREFIX,
        key_func=lambda *args, **kwargs: f"{CacheConfig.PRODUCTS_PREFIX}:list:{_generate_cache_key('', *args, **kwargs)}"
    )


def cache_dashboard_stats(ttl: int = CacheConfig.DASHBOARD_STATS_TTL):
    """Cache para estatísticas do dashboard."""
    return cached(
        ttl=ttl,
        prefix=CacheConfig.STATS_PREFIX,
        key_func=lambda *args, **kwargs: f"{CacheConfig.STATS_PREFIX}:dashboard"
    )


def cache_deduplication_by_ean(ttl: int = CacheConfig.DEDUPLICATION_TTL):
    """Cache para resultados de deduplicação por EAN."""
    def key_func(*args, **kwargs):
        # Assumir que o primeiro argumento é o EAN
        ean = args[0] if args else kwargs.get('ean', 'unknown')
        return f"{CacheConfig.DEDUP_PREFIX}:ean:{ean}"
    
    return cached(
        ttl=ttl,
        prefix=CacheConfig.DEDUP_PREFIX,
        key_func=key_func
    )


def cache_search_results(ttl: int = CacheConfig.SEARCH_RESULTS_TTL):
    """Cache para resultados de busca."""
    return cached(
        ttl=ttl,
        prefix=CacheConfig.SEARCH_PREFIX,
        key_func=lambda *args, **kwargs: f"{CacheConfig.SEARCH_PREFIX}:query:{_generate_cache_key('', *args, **kwargs)}"
    )


# Funções utilitárias para gerenciamento de cache
def invalidate_products_cache():
    """
    Invalida todo o cache de produtos.
    Usar quando produtos são adicionados/atualizados.
    """
    try:
        pattern = f"{CacheConfig.PRODUCTS_PREFIX}:*"
        keys = cache_redis.keys(pattern)
        if keys:
            cache_redis.delete(*keys)
            logger.info(f"Invalidated {len(keys)} product cache keys")
            return len(keys)
        return 0
    except Exception as e:
        logger.error(f"Error invalidating products cache: {e}")
        return 0


def invalidate_stats_cache():
    """
    Invalida todo o cache de estatísticas.
    Usar quando dados que afetam stats são alterados.
    """
    try:
        pattern = f"{CacheConfig.STATS_PREFIX}:*"
        keys = cache_redis.keys(pattern)
        if keys:
            cache_redis.delete(*keys)
            logger.info(f"Invalidated {len(keys)} stats cache keys")
            return len(keys)
        return 0
    except Exception as e:
        logger.error(f"Error invalidating stats cache: {e}")
        return 0


def invalidate_all_cache():
    """
    Invalida todo o cache do sistema.
    Usar com cuidado - apenas em casos extremos.
    """
    try:
        pattern = f"{CacheConfig.KEY_PREFIX}:*"
        keys = cache_redis.keys(pattern)
        if keys:
            cache_redis.delete(*keys)
            logger.warning(f"Invalidated ALL cache - {len(keys)} keys deleted")
            return len(keys)
        return 0
    except Exception as e:
        logger.error(f"Error invalidating all cache: {e}")
        return 0


def warm_cache():
    """
    Aquece o cache com dados frequentemente acessados.
    Executar após deploy ou limpeza de cache.
    """
    logger.info("Starting cache warm-up...")
    
    try:
        # Aqui você pode adicionar chamadas para endpoints frequentes
        # Por exemplo, buscar estatísticas do dashboard
        from app.api.admin import get_stats
        from app.database import get_db
        
        # Simular aquecimento (em produção, fazer chamadas reais)
        logger.info("Cache warm-up completed")
        return True
        
    except Exception as e:
        logger.error(f"Error during cache warm-up: {e}")
        return False


def validate_cache_config():
    """Valida configuração do cache."""
    try:
        # Testar conexão Redis
        cache_redis.ping()
        logger.info("Cache Redis connection: OK")
        
        # Testar operações básicas
        test_key = f"{CacheConfig.KEY_PREFIX}:test"
        cache_redis.setex(test_key, 10, "test_value")
        value = cache_redis.get(test_key)
        cache_redis.delete(test_key)
        
        if value == b"test_value":
            logger.info("Cache operations test: OK")
            return True
        else:
            logger.error("Cache operations test: FAILED")
            return False
            
    except Exception as e:
        logger.error(f"Cache configuration validation failed: {e}")
        return False