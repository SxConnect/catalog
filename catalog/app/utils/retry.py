"""
Sistema de Retry Automático e Circuit Breaker para o SixPet Catalog Engine.

Este módulo implementa decorators para retry automático com backoff exponencial
e circuit breaker para proteger contra falhas em cascata.
"""

import time
import logging
from typing import Dict, Any, Optional, Callable, Type, Union
from functools import wraps
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from tenacity import (
    retry, 
    stop_after_attempt, 
    wait_exponential, 
    wait_random,
    retry_if_exception_type,
    before_sleep_log,
    after_log
)
from groq import RateLimitError
import httpx
import redis

logger = logging.getLogger(__name__)

# Configuração do Redis para circuit breaker
import os
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
redis_client = redis.from_url(REDIS_URL)


class CircuitBreakerState(Enum):
    """Estados do Circuit Breaker."""
    CLOSED = "closed"      # Funcionando normalmente
    OPEN = "open"          # Falhas detectadas, bloqueando chamadas
    HALF_OPEN = "half_open"  # Testando recuperação


@dataclass
class CircuitBreakerConfig:
    """Configuração do Circuit Breaker."""
    failure_threshold: int = 5          # Falhas consecutivas para abrir
    recovery_timeout: int = 120         # Segundos para tentar half-open
    success_threshold: int = 3          # Sucessos para fechar novamente
    timeout_window: int = 60            # Janela de tempo para contar falhas


@dataclass
class CircuitBreakerStats:
    """Estatísticas do Circuit Breaker."""
    state: CircuitBreakerState = CircuitBreakerState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    total_requests: int = 0
    total_failures: int = 0
    opened_at: Optional[datetime] = None


class CircuitBreakerError(Exception):
    """Exceção lançada quando circuit breaker está aberto."""
    pass


class CircuitBreaker:
    """
    Implementação de Circuit Breaker com estado persistido no Redis.
    
    O Circuit Breaker protege contra falhas em cascata, bloqueando chamadas
    quando um serviço está falhando consistentemente.
    """
    
    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        """
        Inicializa o Circuit Breaker.
        
        Args:
            name: Nome único do circuit breaker
            config: Configuração personalizada
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.redis_key = f"circuit_breaker:{name}"
        
    def _get_stats(self) -> CircuitBreakerStats:
        """Recupera estatísticas do Redis."""
        try:
            data = redis_client.hgetall(self.redis_key)
            if not data:
                return CircuitBreakerStats()
            
            return CircuitBreakerStats(
                state=CircuitBreakerState(data.get('state', 'closed')),
                failure_count=int(data.get('failure_count', 0)),
                success_count=int(data.get('success_count', 0)),
                last_failure_time=datetime.fromisoformat(data['last_failure_time']) if data.get('last_failure_time') else None,
                last_success_time=datetime.fromisoformat(data['last_success_time']) if data.get('last_success_time') else None,
                total_requests=int(data.get('total_requests', 0)),
                total_failures=int(data.get('total_failures', 0)),
                opened_at=datetime.fromisoformat(data['opened_at']) if data.get('opened_at') else None
            )
        except Exception as e:
            logger.error(f"Error getting circuit breaker stats for {self.name}: {e}")
            return CircuitBreakerStats()
    
    def _save_stats(self, stats: CircuitBreakerStats):
        """Salva estatísticas no Redis."""
        try:
            data = {
                'state': stats.state.value,
                'failure_count': stats.failure_count,
                'success_count': stats.success_count,
                'total_requests': stats.total_requests,
                'total_failures': stats.total_failures
            }
            
            if stats.last_failure_time:
                data['last_failure_time'] = stats.last_failure_time.isoformat()
            if stats.last_success_time:
                data['last_success_time'] = stats.last_success_time.isoformat()
            if stats.opened_at:
                data['opened_at'] = stats.opened_at.isoformat()
            
            redis_client.hset(self.redis_key, mapping=data)
            redis_client.expire(self.redis_key, 86400)  # Expira em 24h
            
        except Exception as e:
            logger.error(f"Error saving circuit breaker stats for {self.name}: {e}")
    
    def _should_attempt_reset(self, stats: CircuitBreakerStats) -> bool:
        """Verifica se deve tentar resetar o circuit breaker."""
        if stats.state != CircuitBreakerState.OPEN:
            return False
        
        if not stats.opened_at:
            return True
        
        time_since_opened = datetime.now() - stats.opened_at
        return time_since_opened.total_seconds() >= self.config.recovery_timeout
    
    def _record_success(self):
        """Registra uma chamada bem-sucedida."""
        stats = self._get_stats()
        stats.success_count += 1
        stats.total_requests += 1
        stats.last_success_time = datetime.now()
        
        # Se estava em half-open e atingiu sucessos suficientes, fechar
        if stats.state == CircuitBreakerState.HALF_OPEN:
            if stats.success_count >= self.config.success_threshold:
                stats.state = CircuitBreakerState.CLOSED
                stats.failure_count = 0
                stats.success_count = 0
                stats.opened_at = None
                logger.info(f"Circuit breaker {self.name} closed after successful recovery")
        
        # Se estava fechado, resetar contador de falhas
        elif stats.state == CircuitBreakerState.CLOSED:
            stats.failure_count = 0
        
        self._save_stats(stats)
    
    def _record_failure(self):
        """Registra uma falha."""
        stats = self._get_stats()
        stats.failure_count += 1
        stats.total_requests += 1
        stats.total_failures += 1
        stats.last_failure_time = datetime.now()
        
        # Se estava em half-open, voltar para open
        if stats.state == CircuitBreakerState.HALF_OPEN:
            stats.state = CircuitBreakerState.OPEN
            stats.opened_at = datetime.now()
            stats.success_count = 0
            logger.warning(f"Circuit breaker {self.name} reopened after failure during recovery")
        
        # Se estava fechado e atingiu limite de falhas, abrir
        elif stats.state == CircuitBreakerState.CLOSED:
            if stats.failure_count >= self.config.failure_threshold:
                stats.state = CircuitBreakerState.OPEN
                stats.opened_at = datetime.now()
                logger.error(f"Circuit breaker {self.name} opened after {stats.failure_count} failures")
        
        self._save_stats(stats)
    
    def call(self, func: Callable, *args, **kwargs):
        """
        Executa uma função protegida pelo circuit breaker.
        
        Args:
            func: Função a ser executada
            *args: Argumentos posicionais
            **kwargs: Argumentos nomeados
            
        Returns:
            Resultado da função
            
        Raises:
            CircuitBreakerError: Se circuit breaker estiver aberto
        """
        stats = self._get_stats()
        
        # Se está aberto, verificar se deve tentar recovery
        if stats.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset(stats):
                stats.state = CircuitBreakerState.HALF_OPEN
                stats.success_count = 0
                self._save_stats(stats)
                logger.info(f"Circuit breaker {self.name} entering half-open state")
            else:
                raise CircuitBreakerError(f"Circuit breaker {self.name} is open")
        
        # Executar função
        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure()
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do circuit breaker."""
        stats = self._get_stats()
        return {
            "name": self.name,
            "state": stats.state.value,
            "failure_count": stats.failure_count,
            "success_count": stats.success_count,
            "total_requests": stats.total_requests,
            "total_failures": stats.total_failures,
            "failure_rate": stats.total_failures / max(stats.total_requests, 1),
            "last_failure_time": stats.last_failure_time.isoformat() if stats.last_failure_time else None,
            "last_success_time": stats.last_success_time.isoformat() if stats.last_success_time else None,
            "opened_at": stats.opened_at.isoformat() if stats.opened_at else None,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "recovery_timeout": self.config.recovery_timeout,
                "success_threshold": self.config.success_threshold
            }
        }


# Instâncias globais de circuit breakers
groq_circuit_breaker = CircuitBreaker("groq_api", CircuitBreakerConfig(
    failure_threshold=5,
    recovery_timeout=120,
    success_threshold=3
))

scraping_circuit_breaker = CircuitBreaker("web_scraping", CircuitBreakerConfig(
    failure_threshold=10,
    recovery_timeout=60,
    success_threshold=2
))


def retry_with_backoff(
    max_attempts: int = 3,
    min_wait: int = 1,
    max_wait: int = 30,
    exceptions: tuple = (Exception,)
):
    """
    Decorator para retry com backoff exponencial.
    
    Args:
        max_attempts: Número máximo de tentativas
        min_wait: Tempo mínimo de espera (segundos)
        max_wait: Tempo máximo de espera (segundos)
        exceptions: Tupla de exceções que devem causar retry
    
    Returns:
        Decorator function
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(exceptions),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.INFO)
    )


def retry_on_network_error(
    max_attempts: int = 5,
    min_wait: int = 2,
    max_wait: int = 10
):
    """
    Decorator para retry em erros de rede com wait aleatório.
    
    Args:
        max_attempts: Número máximo de tentativas
        min_wait: Tempo mínimo de espera (segundos)
        max_wait: Tempo máximo de espera (segundos)
    
    Returns:
        Decorator function
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_random(min=min_wait, max=max_wait),
        retry=retry_if_exception_type((
            httpx.ConnectError,
            httpx.TimeoutException,
            httpx.NetworkError,
            ConnectionError,
            TimeoutError
        )),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.INFO)
    )


def with_circuit_breaker(circuit_breaker: CircuitBreaker):
    """
    Decorator para proteger função com circuit breaker.
    
    Args:
        circuit_breaker: Instância do circuit breaker
    
    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return circuit_breaker.call(func, *args, **kwargs)
        return wrapper
    return decorator


# Decorators combinados para casos específicos
def retry_groq_api(max_attempts: int = 3):
    """
    Decorator específico para chamadas à API Groq.
    Combina retry com circuit breaker.
    """
    def decorator(func):
        @retry_with_backoff(
            max_attempts=max_attempts,
            min_wait=1,
            max_wait=30,
            exceptions=(RateLimitError, httpx.HTTPStatusError, httpx.TimeoutException)
        )
        @with_circuit_breaker(groq_circuit_breaker)
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


def retry_web_scraping(max_attempts: int = 5):
    """
    Decorator específico para web scraping.
    Combina retry com circuit breaker.
    """
    def decorator(func):
        @retry_on_network_error(max_attempts=max_attempts)
        @with_circuit_breaker(scraping_circuit_breaker)
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


def get_all_circuit_breaker_stats() -> Dict[str, Any]:
    """
    Retorna estatísticas de todos os circuit breakers.
    
    Returns:
        Dicionário com estatísticas de todos os circuit breakers
    """
    return {
        "groq_api": groq_circuit_breaker.get_stats(),
        "web_scraping": scraping_circuit_breaker.get_stats()
    }


def reset_circuit_breaker(name: str) -> bool:
    """
    Reseta um circuit breaker específico.
    
    Args:
        name: Nome do circuit breaker
        
    Returns:
        True se resetado com sucesso, False caso contrário
    """
    try:
        if name == "groq_api":
            redis_client.delete(groq_circuit_breaker.redis_key)
            logger.info(f"Circuit breaker {name} reset successfully")
            return True
        elif name == "web_scraping":
            redis_client.delete(scraping_circuit_breaker.redis_key)
            logger.info(f"Circuit breaker {name} reset successfully")
            return True
        else:
            logger.error(f"Unknown circuit breaker: {name}")
            return False
    except Exception as e:
        logger.error(f"Error resetting circuit breaker {name}: {e}")
        return False


# Função para validar configuração
def validate_retry_config():
    """Valida configuração do sistema de retry."""
    try:
        # Testar conexão Redis
        redis_client.ping()
        logger.info("Redis connection for circuit breakers: OK")
        
        # Testar circuit breakers
        groq_stats = groq_circuit_breaker.get_stats()
        scraping_stats = scraping_circuit_breaker.get_stats()
        
        logger.info(f"Groq circuit breaker state: {groq_stats['state']}")
        logger.info(f"Scraping circuit breaker state: {scraping_stats['state']}")
        
        return True
        
    except Exception as e:
        logger.error(f"Retry configuration validation failed: {e}")
        return False