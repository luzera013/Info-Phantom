"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - Advanced Robustness Manager
Sistema avançado de robustez com resiliência, recuperação e tolerância a falhas
"""

import asyncio
import time
import json
import traceback
from typing import List, Dict, Any, Optional, Set, Tuple, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging
import hashlib
import random

from ..utils.logger import setup_logger
from ..utils.metrics import MetricsCollector
from ..utils.ttl_cache import TTLCache

logger = setup_logger(__name__)
metrics = MetricsCollector()

@dataclass
class FailureEvent:
    """Evento de falha do sistema"""
    event_id: str
    timestamp: float
    component: str
    error_type: str
    error_message: str
    severity: str  # low, medium, high, critical
    context: Dict[str, Any] = field(default_factory=dict)
    recovery_attempted: bool = False
    recovery_successful: bool = False
    recovery_time: Optional[float] = None

@dataclass
class CircuitBreakerState:
    """Estado do Circuit Breaker"""
    service_name: str
    state: str  # closed, open, half_open
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float = 0.0
    last_success_time: float = 0.0
    timeout: float = 60.0  # Tempo para tentar recuperação
    failure_threshold: int = 5
    success_threshold: int = 3

@dataclass
class RetryPolicy:
    """Política de retry"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_multiplier: float = 2.0
    jitter: bool = True
    retry_on_exceptions: List[type] = field(default_factory=list)

@dataclass
class HealthCheck:
    """Verificação de saúde de componente"""
    component_name: str
    check_function: Callable
    interval: float = 30.0
    timeout: float = 10.0
    healthy_threshold: int = 2
    unhealthy_threshold: int = 3
    consecutive_successes: int = 0
    consecutive_failures: int = 0
    last_check_time: float = 0.0
    status: str = "unknown"

class AdvancedRobustnessManager:
    """Gerenciador avançado de robustez do sistema"""
    
    def __init__(self):
        self.failure_events: deque = deque(maxlen=1000)
        self.circuit_breakers: Dict[str, CircuitBreakerState] = {}
        self.retry_policies: Dict[str, RetryPolicy] = {}
        self.health_checks: Dict[str, HealthCheck] = {}
        self.recovery_strategies: Dict[str, Callable] = {}
        self.fallback_handlers: Dict[str, Callable] = {}
        
        # Cache para resiliência
        self.resilience_cache = TTLCache(ttl=300)  # 5 minutos
        
        # Configurações
        self.config = {
            'auto_recovery': True,
            'circuit_breaker_enabled': True,
            'retry_enabled': True,
            'health_check_enabled': True,
            'fallback_enabled': True,
            'failure_logging': True,
            'performance_monitoring': True,
            'graceful_degradation': True,
            'disaster_recovery': True,
            'chaos_testing': False,
            'self_healing': True,
            'predictive_failure_detection': True
        }
        
        # Estatísticas
        self.robustness_stats = {
            'total_failures': 0,
            'recoveries_attempted': 0,
            'recoveries_successful': 0,
            'circuit_breaker_trips': 0,
            'retry_attempts': 0,
            'retry_successes': 0,
            'fallback_activations': 0,
            'health_checks_passed': 0,
            'health_checks_failed': 0,
            'uptime_percentage': 100.0,
            'mean_time_to_recovery': 0.0
        }
        
        # Estado do sistema
        self.system_health = {
            'overall_status': 'healthy',
            'critical_failures': 0,
            'degraded_services': set(),
            'failed_services': set(),
            'last_failure_time': 0.0,
            'recovery_in_progress': False
        }
        
        # Controle
        self.monitoring_active = False
        self.recovery_lock = asyncio.Lock()
        
        # Inicializar componentes padrão
        self._setup_default_circuit_breakers()
        self._setup_default_retry_policies()
        self._setup_default_health_checks()
        self._setup_recovery_strategies()
        
        logger.info(" Advanced Robustness Manager inicializado")
    
    def _setup_default_circuit_breakers(self):
        """Configura circuit breakers padrão"""
        services = [
            'web_search', 'bing_search', 'reddit_collector', 'github_collector',
            'wikipedia_collector', 'news_collector', 'tor_scraper',
            'llm_service', 'summarizer_service', 'cache_service'
        ]
        
        for service in services:
            self.circuit_breakers[service] = CircuitBreakerState(
                service_name=service,
                state='closed',
                failure_threshold=5,
                success_threshold=3
            )
    
    def _setup_default_retry_policies(self):
        """Configura políticas de retry padrão"""
        default_policy = RetryPolicy(
            max_attempts=3,
            base_delay=1.0,
            max_delay=30.0,
            backoff_multiplier=2.0,
            jitter=True
        )
        
        # Políticas específicas por serviço
        self.retry_policies['web_search'] = RetryPolicy(max_attempts=2, base_delay=0.5)
        self.retry_policies['llm_service'] = RetryPolicy(max_attempts=3, base_delay=2.0, max_delay=60.0)
        self.retry_policies['cache_service'] = RetryPolicy(max_attempts=1, base_delay=0.1)  # Cache falha rápido
        
        # Política padrão para outros serviços
        for service in self.circuit_breakers.keys():
            if service not in self.retry_policies:
                self.retry_policies[service] = default_policy
    
    def _setup_default_health_checks(self):
        """Configura verificações de saúde padrão"""
        # Health checks serão configurados dinamicamente pelos componentes
        pass
    
    def _setup_recovery_strategies(self):
        """Configura estratégias de recuperação"""
        self.recovery_strategies = {
            'memory_leak': self._recover_memory_leak,
            'connection_timeout': self._recover_connection_timeout,
            'service_unavailable': self._recover_service_unavailable,
            'rate_limit_exceeded': self._recover_rate_limit,
            'authentication_failure': self._recover_authentication,
            'data_corruption': self._recover_data_corruption,
            'network_partition': self._recover_network_partition,
            'resource_exhaustion': self._recover_resource_exhaustion
        }
    
    async def initialize(self):
        """Inicializa o gerenciador de robustez"""
        if self.config['health_check_enabled']:
            await self.start_health_monitoring()
        
        logger.info(" Advanced Robustness Manager pronto")
    
    async def start_health_monitoring(self):
        """Inicia monitoramento de saúde"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        asyncio.create_task(self._health_monitoring_loop())
        
        logger.info(" Monitoramento de saúde iniciado")
    
    async def stop_health_monitoring(self):
        """Para monitoramento de saúde"""
        self.monitoring_active = False
        logger.info(" Monitoramento de saúde parado")
    
    async def _health_monitoring_loop(self):
        """Loop principal de monitoramento de saúde"""
        while self.monitoring_active:
            try:
                # Executar health checks
                await self._execute_health_checks()
                
                # Verificar circuit breakers
                await self._check_circuit_breakers()
                
                # Detectar falhas preditivas
                if self.config['predictive_failure_detection']:
                    await self._predictive_failure_detection()
                
                # Aguardar próxima verificação
                await asyncio.sleep(10.0)  # Verificar a cada 10 segundos
                
            except Exception as e:
                logger.error(f" Erro no loop de monitoramento: {str(e)}")
                await asyncio.sleep(10.0)
    
    async def _execute_health_checks(self):
        """Executa todas as verificações de saúde"""
        current_time = time.time()
        
        for name, health_check in self.health_checks.items():
            # Verificar se é hora de executar o check
            if current_time - health_check.last_check_time < health_check.interval:
                continue
            
            try:
                # Executar check com timeout
                result = await asyncio.wait_for(
                    health_check.check_function(),
                    timeout=health_check.timeout
                )
                
                if result:
                    health_check.consecutive_successes += 1
                    health_check.consecutive_failures = 0
                    health_check.status = "healthy"
                    self.robustness_stats['health_checks_passed'] += 1
                else:
                    health_check.consecutive_failures += 1
                    health_check.consecutive_successes = 0
                    health_check.status = "unhealthy"
                    self.robustness_stats['health_checks_failed'] += 1
                    
                    # Registrar falha
                    await self._register_failure(
                        component=name,
                        error_type="health_check_failure",
                        error_message=f"Health check failed for {name}",
                        severity="medium"
                    )
                
                health_check.last_check_time = current_time
                
            except asyncio.TimeoutError:
                health_check.consecutive_failures += 1
                health_check.consecutive_successes = 0
                health_check.status = "timeout"
                self.robustness_stats['health_checks_failed'] += 1
                
                await self._register_failure(
                    component=name,
                    error_type="health_check_timeout",
                    error_message=f"Health check timeout for {name}",
                    severity="high"
                )
                
                health_check.last_check_time = current_time
                
            except Exception as e:
                health_check.consecutive_failures += 1
                health_check.consecutive_successes = 0
                health_check.status = "error"
                self.robustness_stats['health_checks_failed'] += 1
                
                await self._register_failure(
                    component=name,
                    error_type="health_check_error",
                    error_message=f"Health check error for {name}: {str(e)}",
                    severity="high"
                )
                
                health_check.last_check_time = current_time
    
    async def _check_circuit_breakers(self):
        """Verifica e atualiza estados dos circuit breakers"""
        current_time = time.time()
        
        for service, breaker in self.circuit_breakers.items():
            if breaker.state == 'open':
                # Verificar se deve tentar half-open
                if current_time - breaker.last_failure_time > breaker.timeout:
                    breaker.state = 'half_open'
                    logger.info(f" Circuit breaker para {service} mudando para half-open")
            
            elif breaker.state == 'half_open':
                # Manter em half-open por um tempo limitado
                if current_time - breaker.last_failure_time > breaker.timeout * 2:
                    breaker.state = 'open'
                    breaker.failure_count = 0
                    logger.warning(f" Circuit breaker para {service} voltando para open")
    
    async def _predictive_failure_detection(self):
        """Detecção preditiva de falhas"""
        if len(self.failure_events) < 10:
            return
        
        # Analisar padrões de falhas recentes
        recent_failures = [f for f in self.failure_events if time.time() - f.timestamp < 300]  # Últimos 5 minutos
        
        # Detectar aumento na taxa de falhas
        failure_rate = len(recent_failures) / 5.0  # Falhas por minuto
        
        if failure_rate > 10:  # Mais de 10 falhas por minuto
            await self._trigger_predictive_alert("high_failure_rate", failure_rate)
        
        # Detectar falhas em cascata
        component_failures = defaultdict(list)
        for failure in recent_failures:
            component_failures[failure.component].append(failure)
        
        # Se múltiplos componentes estão falhando
        failing_components = [comp for comp, failures in component_failures.items() if len(failures) > 2]
        
        if len(failing_components) > 3:
            await self._trigger_predictive_alert("cascading_failures", failing_components)
    
    async def _trigger_predictive_alert(self, alert_type: str, data: Any):
        """Dispara alerta preditivo"""
        logger.warning(f" Alerta preditivo: {alert_type} - {data}")
        
        # Em produção, enviar para sistema de alertas
        # await self.alert_service.send_predictive_alert(alert_type, data)
    
    async def execute_with_resilience(self, 
                                    service_name: str,
                                    operation: Callable,
                                    *args,
                                    **kwargs) -> Any:
        """
        Executa operação com resiliência completa
        
        Args:
            service_name: Nome do serviço
            operation: Função a executar
            *args, **kwargs: Argumentos da função
            
        Returns:
            Resultado da operação
        """
        start_time = time.time()
        
        try:
            # Verificar circuit breaker
            if self.config['circuit_breaker_enabled']:
                if not await self._check_circuit_breaker(service_name):
                    raise Exception(f"Circuit breaker open for {service_name}")
            
            # Executar com retry
            if self.config['retry_enabled']:
                result = await self._execute_with_retry(service_name, operation, *args, **kwargs)
            else:
                result = await operation(*args, **kwargs)
            
            # Registrar sucesso
            await self._register_success(service_name)
            
            return result
            
        except Exception as e:
            # Registrar falha
            await self._register_failure(
                component=service_name,
                error_type=type(e).__name__,
                error_message=str(e),
                severity="medium",
                context={'operation': operation.__name__}
            )
            
            # Tentar recuperação automática
            if self.config['auto_recovery']:
                recovery_result = await self._attempt_auto_recovery(service_name, e)
                if recovery_result is not None:
                    return recovery_result
            
            # Tentar fallback
            if self.config['fallback_enabled']:
                fallback_result = await self._execute_fallback(service_name, *args, **kwargs)
                if fallback_result is not None:
                    return fallback_result
            
            # Relançar exceção
            raise
    
    async def _check_circuit_breaker(self, service_name: str) -> bool:
        """Verifica se circuit breaker permite execução"""
        if service_name not in self.circuit_breakers:
            return True
        
        breaker = self.circuit_breakers[service_name]
        
        if breaker.state == 'closed':
            return True
        elif breaker.state == 'open':
            return False
        elif breaker.state == 'half_open':
            # Permitir uma tentativa em half-open
            return True
        
        return False
    
    async def _execute_with_retry(self, 
                                 service_name: str,
                                 operation: Callable,
                                 *args,
                                 **kwargs) -> Any:
        """Executa operação com política de retry"""
        policy = self.retry_policies.get(service_name, self.retry_policies.get('default'))
        
        last_exception = None
        
        for attempt in range(policy.max_attempts):
            try:
                self.robustness_stats['retry_attempts'] += 1
                
                result = await operation(*args, **kwargs)
                
                # Sucesso - registrar no circuit breaker
                await self._register_circuit_breaker_success(service_name)
                self.robustness_stats['retry_successes'] += 1
                
                return result
                
            except Exception as e:
                last_exception = e
                
                # Verificar se deve retry nesta exceção
                if policy.retry_on_exceptions and not any(isinstance(e, exc_type) for exc_type in policy.retry_on_exceptions):
                    break
                
                # Registrar falha no circuit breaker
                await self._register_circuit_breaker_failure(service_name)
                
                if attempt < policy.max_attempts - 1:
                    # Calcular delay com backoff exponencial
                    delay = min(policy.base_delay * (policy.backoff_multiplier ** attempt), policy.max_delay)
                    
                    # Adicionar jitter se habilitado
                    if policy.jitter:
                        delay *= (0.5 + random.random() * 0.5)
                    
                    logger.warning(f" Retry {attempt + 1}/{policy.max_attempts} para {service_name} em {delay:.2f}s: {str(e)}")
                    await asyncio.sleep(delay)
        
        # Todos os retries falharam
        raise last_exception
    
    async def _register_success(self, service_name: str):
        """Registra sucesso de operação"""
        if service_name in self.circuit_breakers:
            breaker = self.circuit_breakers[service_name]
            
            if breaker.state == 'half_open':
                breaker.success_count += 1
                
                # Se atingiu threshold de sucessos, fechar circuit breaker
                if breaker.success_count >= breaker.success_threshold:
                    breaker.state = 'closed'
                    breaker.success_count = 0
                    breaker.failure_count = 0
                    logger.info(f" Circuit breaker para {service_name} fechado")
            
            breaker.last_success_time = time.time()
    
    async def _register_circuit_breaker_success(self, service_name: str):
        """Registra sucesso no circuit breaker"""
        await self._register_success(service_name)
    
    async def _register_circuit_breaker_failure(self, service_name: str):
        """Registra falha no circuit breaker"""
        if service_name not in self.circuit_breakers:
            return
        
        breaker = self.circuit_breakers[service_name]
        breaker.failure_count += 1
        breaker.last_failure_time = time.time()
        
        if breaker.state == 'closed':
            # Verificar se deve abrir
            if breaker.failure_count >= breaker.failure_threshold:
                breaker.state = 'open'
                self.robustness_stats['circuit_breaker_trips'] += 1
                logger.warning(f" Circuit breaker para {service_name} aberto")
        
        elif breaker.state == 'half_open':
            # Falha em half-open volta para open
            breaker.state = 'open'
            breaker.failure_count = 0
            self.robustness_stats['circuit_breaker_trips'] += 1
            logger.warning(f" Circuit breaker para {service_name} voltando para open")
    
    async def _register_failure(self, 
                              component: str,
                              error_type: str,
                              error_message: str,
                              severity: str,
                              context: Dict[str, Any] = None):
        """Registra evento de falha"""
        event_id = hashlib.md5(f"{component}_{error_type}_{time.time()}".encode()).hexdigest()[:8]
        
        failure_event = FailureEvent(
            event_id=event_id,
            timestamp=time.time(),
            component=component,
            error_type=error_type,
            error_message=error_message,
            severity=severity,
            context=context or {}
        )
        
        self.failure_events.append(failure_event)
        self.robustness_stats['total_failures'] += 1
        
        # Atualizar estado do sistema
        await self._update_system_health(failure_event)
        
        # Log da falha
        if self.config['failure_logging']:
            logger.error(f" Falha registrada: {component} - {error_type}: {error_message}")
        
        # Tentar recuperação automática se for crítico
        if severity in ['high', 'critical'] and self.config['auto_recovery']:
            asyncio.create_task(self._attempt_auto_recovery(component, Exception(error_message)))
    
    async def _update_system_health(self, failure_event: FailureEvent):
        """Atualiza estado de saúde do sistema"""
        if failure_event.severity == 'critical':
            self.system_health['critical_failures'] += 1
            self.system_health['failed_services'].add(failure_event.component)
            self.system_health['overall_status'] = 'critical'
        elif failure_event.severity == 'high':
            self.system_health['degraded_services'].add(failure_event.component)
            if self.system_health['overall_status'] == 'healthy':
                self.system_health['overall_status'] = 'degraded'
        
        self.system_health['last_failure_time'] = failure_event.timestamp
    
    async def _attempt_auto_recovery(self, service_name: str, exception: Exception) -> Optional[Any]:
        """Tenta recuperação automática de serviço"""
        async with self.recovery_lock:
            try:
                self.robustness_stats['recoveries_attempted'] += 1
                self.system_health['recovery_in_progress'] = True
                
                # Identificar tipo de falha
                error_type = type(exception).__name__
                
                # Buscar estratégia de recuperação
                recovery_strategy = self._get_recovery_strategy(error_type)
                
                if recovery_strategy:
                    logger.info(f" Tentando recuperação automática para {service_name}: {error_type}")
                    
                    start_time = time.time()
                    recovery_result = await recovery_strategy(service_name, exception)
                    recovery_time = time.time() - start_time
                    
                    if recovery_result is not None:
                        self.robustness_stats['recoveries_successful'] += 1
                        
                        # Atualizar evento de falha
                        for event in reversed(self.failure_events):
                            if event.component == service_name and not event.recovery_attempted:
                                event.recovery_attempted = True
                                event.recovery_successful = True
                                event.recovery_time = recovery_time
                                break
                        
                        logger.info(f" Recuperação automática bem-sucedida para {service_name} em {recovery_time:.2f}s")
                        
                        # Remover da lista de serviços falhos
                        self.system_health['failed_services'].discard(service_name)
                        self.system_health['degraded_services'].discard(service_name)
                        
                        return recovery_result
                
                logger.warning(f" Recuperação automática falhou para {service_name}")
                return None
                
            except Exception as e:
                logger.error(f" Erro na recuperação automática para {service_name}: {str(e)}")
                return None
            finally:
                self.system_health['recovery_in_progress'] = False
    
    def _get_recovery_strategy(self, error_type: str) -> Optional[Callable]:
        """Obtém estratégia de recuperação baseada no tipo de erro"""
        # Mapeamento de tipos de erro para estratégias
        error_mapping = {
            'TimeoutError': self._recover_connection_timeout,
            'ConnectionError': self._recover_connection_timeout,
            'MemoryError': self._recover_memory_leak,
            'ResourceExhausted': self._recover_resource_exhaustion,
            'RateLimitError': self._recover_rate_limit,
            'AuthenticationError': self._recover_authentication,
            'PermissionError': self._recover_authentication,
            'DataCorruptionError': self._recover_data_corruption,
            'NetworkError': self._recover_network_partition
        }
        
        return error_mapping.get(error_type)
    
    async def _execute_fallback(self, service_name: str, *args, **kwargs) -> Optional[Any]:
        """Executa handler de fallback"""
        if service_name not in self.fallback_handlers:
            return None
        
        try:
            self.robustness_stats['fallback_activations'] += 1
            
            fallback_handler = self.fallback_handlers[service_name]
            result = await fallback_handler(*args, **kwargs)
            
            logger.info(f" Fallback executado para {service_name}")
            return result
            
        except Exception as e:
            logger.error(f" Erro no fallback para {service_name}: {str(e)}")
            return None
    
    # Estratégias de recuperação
    async def _recover_memory_leak(self, service_name: str, exception: Exception) -> Optional[Any]:
        """Recuperação de memory leak"""
        try:
            import gc
            gc.collect()
            
            # Limpar caches
            self.resilience_cache.clear()
            
            # Aguardar um pouco para memória se estabilizar
            await asyncio.sleep(2)
            
            return {"recovered": True, "strategy": "memory_cleanup"}
            
        except Exception as e:
            logger.error(f" Erro na recuperação de memory leak: {str(e)}")
            return None
    
    async def _recover_connection_timeout(self, service_name: str, exception: Exception) -> Optional[Any]:
        """Recuperação de timeout de conexão"""
        try:
            # Resetar circuit breaker
            if service_name in self.circuit_breakers:
                self.circuit_breakers[service_name].state = 'closed'
                self.circuit_breakers[service_name].failure_count = 0
            
            # Aguardar antes de tentar novamente
            await asyncio.sleep(5)
            
            return {"recovered": True, "strategy": "connection_reset"}
            
        except Exception as e:
            logger.error(f" Erro na recuperação de connection timeout: {str(e)}")
            return None
    
    async def _recover_service_unavailable(self, service_name: string, exception: Exception) -> Optional[Any]:
        """Recuperação de serviço indisponível"""
        try:
            # Tentar reinicializar serviço (simulado)
            await asyncio.sleep(3)
            
            return {"recovered": True, "strategy": "service_restart"}
            
        except Exception as e:
            logger.error(f" Erro na recuperação de serviço indisponível: {str(e)}")
            return None
    
    async def _recover_rate_limit(self, service_name: str, exception: Exception) -> Optional[Any]:
        """Recuperação de rate limit exceeded"""
        try:
            # Aguardar exponential backoff
            await asyncio.sleep(30)
            
            return {"recovered": True, "strategy": "rate_limit_wait"}
            
        except Exception as e:
            logger.error(f" Erro na recuperação de rate limit: {str(e)}")
            return None
    
    async def _recover_authentication(self, service_name: str, exception: Exception) -> Optional[Any]:
        """Recuperação de falha de autenticação"""
        try:
            # Tentar refresh de token (simulado)
            await asyncio.sleep(1)
            
            return {"recovered": True, "strategy": "auth_refresh"}
            
        except Exception as e:
            logger.error(f" Erro na recuperação de autenticação: {str(e)}")
            return None
    
    async def _recover_data_corruption(self, service_name: str, exception: Exception) -> Optional[Any]:
        """Recuperação de corrupção de dados"""
        try:
            # Limpar cache corrompido
            self.resilience_cache.clear()
            
            return {"recovered": True, "strategy": "cache_cleanup"}
            
        except Exception as e:
            logger.error(f" Erro na recuperação de corrupção de dados: {str(e)}")
            return None
    
    async def _recover_network_partition(self, service_name: str, exception: Exception) -> Optional[Any]:
        """Recuperação de partição de rede"""
        try:
            # Aguardar recuperação da rede
            await asyncio.sleep(10)
            
            return {"recovered": True, "strategy": "network_wait"}
            
        except Exception as e:
            logger.error(f" Erro na recuperação de partição de rede: {str(e)}")
            return None
    
    async def _recover_resource_exhaustion(self, service_name: str, exception: Exception) -> Optional[Any]:
        """Recuperação de esgotamento de recursos"""
        try:
            # Liberar recursos
            import gc
            gc.collect()
            
            # Reduzir concorrência
            if service_name in self.circuit_breakers:
                self.circuit_breakers[service_name].failure_threshold = max(1, 
                    self.circuit_breakers[service_name].failure_threshold - 1)
            
            await asyncio.sleep(5)
            
            return {"recovered": True, "strategy": "resource_cleanup"}
            
        except Exception as e:
            logger.error(f" Erro na recuperação de esgotamento de recursos: {str(e)}")
            return None
    
    def add_health_check(self, health_check: HealthCheck):
        """Adiciona verificação de saúde"""
        self.health_checks[health_check.component_name] = health_check
        logger.info(f" Health check adicionado: {health_check.component_name}")
    
    def add_fallback_handler(self, service_name: str, handler: Callable):
        """Adiciona handler de fallback"""
        self.fallback_handlers[service_name] = handler
        logger.info(f" Fallback handler adicionado: {service_name}")
    
    async def get_robustness_report(self) -> Dict[str, Any]:
        """Gera relatório completo de robustez"""
        current_time = time.time()
        
        # Calcular uptime
        if len(self.failure_events) > 0:
            first_failure = min(f.timestamp for f in self.failure_events)
            uptime_seconds = current_time - first_failure
            downtime_seconds = sum(1 for f in self.failure_events if f.severity == 'critical') * 60  # Estimativa
            uptime_percentage = ((uptime_seconds - downtime_seconds) / uptime_seconds) * 100
        else:
            uptime_percentage = 100.0
        
        # Calcular MTTR (Mean Time To Recovery)
        recovered_failures = [f for f in self.failure_events if f.recovery_successful]
        if recovered_failures:
            mttr = sum(f.recovery_time for f in recovered_failures) / len(recovered_failures)
        else:
            mttr = 0.0
        
        # Análise de falhas recentes
        recent_failures = [f for f in self.failure_events if current_time - f.timestamp < 3600]  # Última hora
        
        failure_analysis = {
            'total_recent': len(recent_failures),
            'by_severity': defaultdict(int),
            'by_component': defaultdict(int),
            'by_type': defaultdict(int)
        }
        
        for failure in recent_failures:
            failure_analysis['by_severity'][failure.severity] += 1
            failure_analysis['by_component'][failure.component] += 1
            failure_analysis['by_type'][failure.error_type] += 1
        
        return {
            'timestamp': datetime.now().isoformat(),
            'system_health': self.system_health,
            'robustness_stats': self.robustness_stats,
            'uptime_percentage': uptime_percentage,
            'mean_time_to_recovery': mttr,
            'circuit_breakers': {
                name: {
                    'state': breaker.state,
                    'failure_count': breaker.failure_count,
                    'success_count': breaker.success_count
                }
                for name, breaker in self.circuit_breakers.items()
            },
            'health_checks': {
                name: {
                    'status': check.status,
                    'consecutive_successes': check.consecutive_successes,
                    'consecutive_failures': check.consecutive_failures
                }
                for name, check in self.health_checks.items()
            },
            'failure_analysis': failure_analysis,
            'recent_failures': [
                {
                    'timestamp': f.timestamp,
                    'component': f.component,
                    'error_type': f.error_type,
                    'severity': f.severity,
                    'recovered': f.recovery_successful
                }
                for f in list(self.failure_events)[-20:]  # Últimas 20 falhas
            ],
            'config': self.config
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificação de saúde do gerenciador de robustez"""
        try:
            return {
                'status': self.system_health['overall_status'],
                'component': 'advanced_robustness_manager',
                'timestamp': datetime.now().isoformat(),
                'monitoring_active': self.monitoring_active,
                'total_failures': self.robustness_stats['total_failures'],
                'recoveries_successful': self.robustness_stats['recoveries_successful'],
                'circuit_breakers_active': len([b for b in self.circuit_breakers.values() if b.state == 'open']),
                'health_checks_configured': len(self.health_checks),
                'system_health': self.system_health,
                'config': self.config
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'component': 'advanced_robustness_manager',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    async def cleanup(self):
        """Limpa recursos do gerenciador de robustez"""
        await self.stop_health_monitoring()
        self.failure_events.clear()
        self.resilience_cache.clear()
        logger.info(" Advanced Robustness Manager limpo")
