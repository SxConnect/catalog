"""
Sistema de Monitoramento com Prometheus para o SixPet Catalog Engine.

Este módulo implementa instrumentação completa com métricas de negócio,
performance e saúde do sistema para monitoramento via Prometheus + Grafana.
"""

import time
import logging
from typing import Dict, Any, Optional, List
from functools import wraps
from datetime import datetime, timedelta
from prometheus_client import (
    Counter, 
    Histogram, 
    Gauge, 
    Info,
    generate_latest,
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    REGISTRY
)
from fastapi import Request, Response
from fastapi.responses import PlainTextResponse
import psutil
import redis

logger = logging.getLogger(__name__)

# Registry personalizado para métricas do SixPet
sixpet_registry = CollectorRegistry()

# ============================================================================
# CONTADORES - Eventos que só aumentam
# ============================================================================

# Processamento de produtos
produtos_processados_total = Counter(
    'sixpet_produtos_processados_total',
    'Total de produtos processados com sucesso',
    ['catalog_id', 'source'],
    registry=sixpet_registry
)

produtos_duplicados_total = Counter(
    'sixpet_produtos_duplicados_total', 
    'Total de produtos identificados como duplicados',
    ['method'],  # ean, similarity, manual
    registry=sixpet_registry
)

# Erros por serviço
erros_groq_total = Counter(
    'sixpet_erros_groq_total',
    'Total de erros na API Groq',
    ['error_type'],  # rate_limit, timeout, api_error
    registry=sixpet_registry
)

erros_scraping_total = Counter(
    'sixpet_erros_scraping_total',
    'Total de erros em web scraping',
    ['error_type', 'domain'],
    registry=sixpet_registry
)

# Uploads e processamento
catalogs_uploaded_total = Counter(
    'sixpet_catalogs_uploaded_total',
    'Total de catálogos enviados',
    ['status'],  # success, failed, processing
    registry=sixpet_registry
)

# Cache
cache_operations_total = Counter(
    'sixpet_cache_operations_total',
    'Total de operações de cache',
    ['operation', 'result'],  # get/set, hit/miss/error
    registry=sixpet_registry
)

# API Requests
api_requests_total = Counter(
    'sixpet_api_requests_total',
    'Total de requests da API',
    ['method', 'endpoint', 'status_code'],
    registry=sixpet_registry
)

# ============================================================================
# HISTOGRAMAS - Distribuição de tempos/tamanhos
# ============================================================================

# Tempos de processamento
tempo_extracao_pdf_seconds = Histogram(
    'sixpet_tempo_extracao_pdf_seconds',
    'Tempo para extrair dados de PDF',
    ['catalog_id'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0],
    registry=sixpet_registry
)

tempo_enrichment_seconds = Histogram(
    'sixpet_tempo_enrichment_seconds',
    'Tempo para enriquecer produto via web scraping',
    ['source'],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 60.0],
    registry=sixpet_registry
)

tempo_scraping_seconds = Histogram(
    'sixpet_tempo_scraping_seconds',
    'Tempo para fazer scraping de uma página',
    ['domain'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0],
    registry=sixpet_registry
)

# Tempos de resposta da API
api_request_duration_seconds = Histogram(
    'sixpet_api_request_duration_seconds',
    'Duração de requests da API',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    registry=sixpet_registry
)

# Tamanhos de arquivo
pdf_file_size_bytes = Histogram(
    'sixpet_pdf_file_size_bytes',
    'Tamanho dos arquivos PDF processados',
    buckets=[1024, 10240, 102400, 1048576, 10485760, 52428800],  # 1KB to 50MB
    registry=sixpet_registry
)

# ============================================================================
# GAUGES - Valores que podem subir e descer
# ============================================================================

# Filas e workers
produtos_na_fila = Gauge(
    'sixpet_produtos_na_fila',
    'Número de produtos aguardando processamento',
    registry=sixpet_registry
)

workers_ativos = Gauge(
    'sixpet_workers_ativos',
    'Número de workers Celery ativos',
    registry=sixpet_registry
)

# Cache
cache_hit_rate = Gauge(
    'sixpet_cache_hit_rate',
    'Taxa de acerto do cache (0-1)',
    ['cache_type'],
    registry=sixpet_registry
)

cache_keys_total = Gauge(
    'sixpet_cache_keys_total',
    'Número total de chaves no cache',
    ['prefix'],
    registry=sixpet_registry
)

# Circuit Breakers
circuit_breaker_state = Gauge(
    'sixpet_circuit_breaker_state',
    'Estado do circuit breaker (0=closed, 1=open, 2=half_open)',
    ['service'],
    registry=sixpet_registry
)

circuit_breaker_failure_rate = Gauge(
    'sixpet_circuit_breaker_failure_rate',
    'Taxa de falhas do circuit breaker (0-1)',
    ['service'],
    registry=sixpet_registry
)

# Sistema
system_memory_usage_bytes = Gauge(
    'sixpet_system_memory_usage_bytes',
    'Uso de memória do sistema',
    registry=sixpet_registry
)

system_cpu_usage_percent = Gauge(
    'sixpet_system_cpu_usage_percent',
    'Uso de CPU do sistema',
    registry=sixpet_registry
)

# Database
database_connections_active = Gauge(
    'sixpet_database_connections_active',
    'Conexões ativas com o banco de dados',
    registry=sixpet_registry
)

database_query_duration_seconds = Histogram(
    'sixpet_database_query_duration_seconds',
    'Duração de queries no banco',
    ['operation'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
    registry=sixpet_registry
)

# ============================================================================
# INFO - Metadados do sistema
# ============================================================================

system_info = Info(
    'sixpet_system_info',
    'Informações do sistema SixPet',
    registry=sixpet_registry
)

# Definir informações do sistema
system_info.info({
    'version': '1.0.7',
    'python_version': __import__('sys').version.split()[0],
    'environment': 'development',  # TODO: pegar de variável de ambiente
    'build_date': datetime.now().isoformat()
})

# ============================================================================
# DECORATORS PARA INSTRUMENTAÇÃO AUTOMÁTICA
# ============================================================================

def monitor_pdf_extraction(func):
    """
    Decorator para monitorar extração de PDF.
    
    Args:
        func: Função de extração de PDF
        
    Returns:
        Função decorada com monitoramento
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        catalog_id = str(kwargs.get('catalog_id', args[0] if args else 'unknown'))
        
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            
            # Registrar sucesso
            produtos_processados_total.labels(
                catalog_id=catalog_id,
                source='pdf'
            ).inc()
            
            return result
            
        except Exception as e:
            logger.error(f"PDF extraction error for catalog {catalog_id}: {e}")
            raise
            
        finally:
            # Registrar tempo de processamento
            duration = time.time() - start_time
            tempo_extracao_pdf_seconds.labels(catalog_id=catalog_id).observe(duration)
    
    return wrapper


def monitor_enrichment(func):
    """
    Decorator para monitorar enriquecimento de produtos.
    
    Args:
        func: Função de enriquecimento
        
    Returns:
        Função decorada com monitoramento
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        source = kwargs.get('source', 'web')
        
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            return result
            
        except Exception as e:
            logger.error(f"Enrichment error from {source}: {e}")
            raise
            
        finally:
            duration = time.time() - start_time
            tempo_enrichment_seconds.labels(source=source).observe(duration)
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        source = kwargs.get('source', 'web')
        
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
            
        except Exception as e:
            logger.error(f"Enrichment error from {source}: {e}")
            raise
            
        finally:
            duration = time.time() - start_time
            tempo_enrichment_seconds.labels(source=source).observe(duration)
    
    # Retornar wrapper apropriado baseado na função
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def monitor_scraping(func):
    """
    Decorator para monitorar web scraping.
    
    Args:
        func: Função de scraping
        
    Returns:
        Função decorada com monitoramento
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        url = args[0] if args else kwargs.get('url', 'unknown')
        domain = __import__('urllib.parse').urlparse(url).netloc
        
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            return result
            
        except Exception as e:
            # Registrar erro de scraping
            error_type = type(e).__name__
            erros_scraping_total.labels(
                error_type=error_type,
                domain=domain
            ).inc()
            raise
            
        finally:
            duration = time.time() - start_time
            tempo_scraping_seconds.labels(domain=domain).observe(duration)
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        url = args[0] if args else kwargs.get('url', 'unknown')
        domain = __import__('urllib.parse').urlparse(url).netloc
        
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
            
        except Exception as e:
            error_type = type(e).__name__
            erros_scraping_total.labels(
                error_type=error_type,
                domain=domain
            ).inc()
            raise
            
        finally:
            duration = time.time() - start_time
            tempo_scraping_seconds.labels(domain=domain).observe(duration)
    
    # Retornar wrapper apropriado
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def monitor_api_request(func):
    """
    Decorator para monitorar requests da API.
    
    Args:
        func: Função do endpoint da API
        
    Returns:
        Função decorada com monitoramento
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        # Extrair informações do request
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break
        
        method = request.method if request else 'UNKNOWN'
        endpoint = request.url.path if request else 'unknown'
        
        start_time = time.time()
        status_code = 200
        
        try:
            result = await func(*args, **kwargs)
            return result
            
        except Exception as e:
            status_code = getattr(e, 'status_code', 500)
            raise
            
        finally:
            # Registrar métricas
            duration = time.time() - start_time
            
            api_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=str(status_code)
            ).inc()
            
            api_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        # Extrair informações do request
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break
        
        method = request.method if request else 'UNKNOWN'
        endpoint = request.url.path if request else 'unknown'
        
        start_time = time.time()
        status_code = 200
        
        try:
            result = func(*args, **kwargs)
            return result
            
        except Exception as e:
            status_code = getattr(e, 'status_code', 500)
            raise
            
        finally:
            duration = time.time() - start_time
            
            api_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=str(status_code)
            ).inc()
            
            api_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
    
    # Retornar wrapper apropriado
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


# ============================================================================
# COLETORES DE MÉTRICAS DO SISTEMA
# ============================================================================

class MetricsCollector:
    """Coletor de métricas do sistema."""
    
    def __init__(self):
        self.redis_client = None
        try:
            import os
            REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            self.redis_client = redis.from_url(REDIS_URL)
        except Exception as e:
            logger.warning(f"Could not connect to Redis for metrics: {e}")
    
    def collect_system_metrics(self):
        """Coleta métricas do sistema operacional."""
        try:
            # Memória
            memory = psutil.virtual_memory()
            system_memory_usage_bytes.set(memory.used)
            
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            system_cpu_usage_percent.set(cpu_percent)
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    def collect_cache_metrics(self):
        """Coleta métricas do cache Redis."""
        if not self.redis_client:
            return
        
        try:
            from app.utils.cache import CacheStats
            stats = CacheStats.get_stats()
            
            # Total de chaves
            cache_keys_total.labels(prefix='total').set(stats.get('total_keys', 0))
            
            # Chaves por prefixo
            for prefix, count in stats.get('keys_by_prefix', {}).items():
                cache_keys_total.labels(prefix=prefix).set(count)
            
        except Exception as e:
            logger.error(f"Error collecting cache metrics: {e}")
    
    def collect_circuit_breaker_metrics(self):
        """Coleta métricas dos circuit breakers."""
        try:
            from app.utils.retry import get_all_circuit_breaker_stats
            cb_stats = get_all_circuit_breaker_stats()
            
            for service, stats in cb_stats.items():
                # Estado (0=closed, 1=open, 2=half_open)
                state_map = {'closed': 0, 'open': 1, 'half_open': 2}
                state_value = state_map.get(stats['state'], 0)
                circuit_breaker_state.labels(service=service).set(state_value)
                
                # Taxa de falhas
                failure_rate = stats.get('failure_rate', 0)
                circuit_breaker_failure_rate.labels(service=service).set(failure_rate)
                
        except Exception as e:
            logger.error(f"Error collecting circuit breaker metrics: {e}")
    
    def collect_database_metrics(self):
        """Coleta métricas do banco de dados."""
        try:
            # TODO: Implementar coleta de métricas do PostgreSQL
            # Por enquanto, definir valor padrão
            database_connections_active.set(1)
            
        except Exception as e:
            logger.error(f"Error collecting database metrics: {e}")
    
    def collect_all_metrics(self):
        """Coleta todas as métricas do sistema."""
        logger.debug("Collecting system metrics...")
        
        self.collect_system_metrics()
        self.collect_cache_metrics()
        self.collect_circuit_breaker_metrics()
        self.collect_database_metrics()
        
        logger.debug("System metrics collection completed")


# Instância global do coletor
metrics_collector = MetricsCollector()


# ============================================================================
# FUNÇÕES UTILITÁRIAS PARA INSTRUMENTAÇÃO MANUAL
# ============================================================================

def record_product_processed(catalog_id: str, source: str = 'pdf'):
    """Registra produto processado."""
    produtos_processados_total.labels(
        catalog_id=catalog_id,
        source=source
    ).inc()


def record_product_duplicate(method: str = 'ean'):
    """Registra produto duplicado."""
    produtos_duplicados_total.labels(method=method).inc()


def record_groq_error(error_type: str):
    """Registra erro da API Groq."""
    erros_groq_total.labels(error_type=error_type).inc()


def record_catalog_upload(status: str = 'success'):
    """Registra upload de catálogo."""
    catalogs_uploaded_total.labels(status=status).inc()


def record_cache_operation(operation: str, result: str):
    """Registra operação de cache."""
    cache_operations_total.labels(
        operation=operation,
        result=result
    ).inc()


def record_pdf_size(size_bytes: int):
    """Registra tamanho de arquivo PDF."""
    pdf_file_size_bytes.observe(size_bytes)


def update_queue_size(size: int):
    """Atualiza tamanho da fila de processamento."""
    produtos_na_fila.set(size)


def update_active_workers(count: int):
    """Atualiza número de workers ativos."""
    workers_ativos.set(count)


def update_cache_hit_rate(cache_type: str, rate: float):
    """Atualiza taxa de acerto do cache."""
    cache_hit_rate.labels(cache_type=cache_type).set(rate)


# ============================================================================
# ENDPOINT PARA MÉTRICAS PROMETHEUS
# ============================================================================

def get_prometheus_metrics() -> str:
    """
    Retorna métricas no formato Prometheus.
    
    Returns:
        String com métricas formatadas para Prometheus
    """
    # Coletar métricas atuais do sistema
    metrics_collector.collect_all_metrics()
    
    # Gerar métricas no formato Prometheus
    return generate_latest(sixpet_registry).decode('utf-8')


def get_metrics_content_type() -> str:
    """Retorna content-type para métricas Prometheus."""
    return CONTENT_TYPE_LATEST


# ============================================================================
# HEALTH CHECK AVANÇADO
# ============================================================================

def get_comprehensive_health_status() -> Dict[str, Any]:
    """
    Retorna status de saúde abrangente do sistema.
    
    Returns:
        Dicionário com status detalhado de todos os componentes
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.7",
        "uptime_seconds": 0,  # TODO: calcular uptime real
        "services": {},
        "metrics_summary": {},
        "alerts": []
    }
    
    overall_healthy = True
    
    # Verificar serviços básicos
    try:
        from app.api.health import get_services_status
        from app.database import get_db
        
        # Simular sessão de DB para health check
        db_session = next(get_db())
        services = get_services_status(db_session)
        health_status["services"] = services["services"]
        
        if services["overall_status"] != "healthy":
            overall_healthy = False
            
    except Exception as e:
        logger.error(f"Error checking services health: {e}")
        overall_healthy = False
        health_status["services"]["error"] = str(e)
    
    # Coletar resumo de métricas
    try:
        # Métricas de circuit breakers
        from app.utils.retry import get_all_circuit_breaker_stats
        cb_stats = get_all_circuit_breaker_stats()
        
        open_breakers = [name for name, stats in cb_stats.items() if stats["state"] == "open"]
        if open_breakers:
            health_status["alerts"].append({
                "level": "warning",
                "message": f"Circuit breakers open: {', '.join(open_breakers)}"
            })
        
        health_status["metrics_summary"]["circuit_breakers"] = {
            "total": len(cb_stats),
            "open": len(open_breakers),
            "closed": len([name for name, stats in cb_stats.items() if stats["state"] == "closed"])
        }
        
    except Exception as e:
        logger.error(f"Error collecting metrics summary: {e}")
    
    # Verificar uso de recursos
    try:
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent()
        
        health_status["metrics_summary"]["system"] = {
            "memory_usage_percent": memory.percent,
            "cpu_usage_percent": cpu_percent,
            "available_memory_gb": round(memory.available / (1024**3), 2)
        }
        
        # Alertas de recursos
        if memory.percent > 90:
            health_status["alerts"].append({
                "level": "critical",
                "message": f"High memory usage: {memory.percent}%"
            })
            overall_healthy = False
        elif memory.percent > 80:
            health_status["alerts"].append({
                "level": "warning", 
                "message": f"Elevated memory usage: {memory.percent}%"
            })
        
        if cpu_percent > 90:
            health_status["alerts"].append({
                "level": "critical",
                "message": f"High CPU usage: {cpu_percent}%"
            })
            overall_healthy = False
            
    except Exception as e:
        logger.error(f"Error checking system resources: {e}")
    
    # Status final
    health_status["status"] = "healthy" if overall_healthy else "unhealthy"
    
    return health_status