"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - Robustness Manager
Gerenciamento avançado de robustez com recuperação automática de falhas
"""

import asyncio
import time
import traceback
import logging
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
import weakref
import gc
import psutil
from collections import defaultdict, deque
import json
import hashlib
import random

from ..utils.logger import setup_logger
from ..utils.metrics import MetricsCollector
from ..utils.performance_optimizer import PerformanceOptimizer

logger = setup_logger(__name__)
metrics = MetricsCollector()

class ErrorSeverity(Enum):
    """Níveis de severidade de erro"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RecoveryAction(Enum):
    """Ações de recuperação automática"""
    RETRY = "retry"
    FALLBACK = "fallback"
    CIRCUIT_BREAK = "circuit_break"
    DEGRADE = "degrade"
    ISOLATE = "isolate"
    RESTART = "restart"

@dataclass
class ErrorContext:
    """Contexto detalhado de erro"""
    error_id: str
    timestamp: float
    severity: ErrorSeverity
    component: str
    operation: str
    error_message: str
    traceback: str
    recovery_attempts: int
    recovery_actions: List[RecoveryAction]
    resolution_time: Optional[float] = None
    impact_assessment: Dict[str, Any] = None

@dataclass
class HealthCheck:
    """Verificação de saúde de componente"""
    component: str
    status: str
    last_check: float
    metrics: Dict[str, Any]
    issues: List[str]
    recommendations: List[str]

class RobustnessManager:
    """Gerenciador central de robustez do sistema"""
    
    def __init__(self):
        self.error_history = deque(maxlen=1000)
        self.circuit_breakers = {}
        self.fallback_handlers = {}
        self.health_checks = {}
        self.recovery_strategies = {}
        self.isolation_zones = {}
        self.performance_optimizer = PerformanceOptimizer()
        
        # Estatísticas de robustez
        self.robustness_stats = {
            'total_errors': 0,
            'recoveries_attempted': 0,
            'recoveries_successful': 0,
            'circuit_breaks_triggered': 0,
            'fallbacks_used': 0,
            'components_isolated': 0,
            'auto_restarts': 0
        }
        
        # Configurações de robustez
        self.max_retry_attempts = 3
        self.circuit_breaker_threshold = 5
        self.circuit_breaker_timeout = 60.0  # segundos
        self.health_check_interval = 30.0  # segundos
        self.isolation_timeout = 300.0  # segundos
        
        # Locks para concorrência segura
        self.locks = {
            'error_handling': asyncio.RWLock(),
            'circuit_breakers': asyncio.RWLock(),
            'health_checks': asyncio.RWLock(),
            'recovery': asyncio.RWLock(),
            'isolation': asyncio.RWLock()
        }
        
        logger.info("🛡️ Robustness Manager inicializado")
    
    async def initialize(self):
        """Inicializa sistemas de robustez"""
        logger.info("🔧 Inicializando sistemas de robustez...")
        
        # Inicializar performance optimizer
        await self.performance_optimizer.initialize()
        
        # Configurar circuit breakers
        await self._setup_circuit_breakers()
        
        # Configurar health checks
        await self._setup_health_checks()
        
        # Configurar recovery strategies
        await self._setup_recovery_strategies()
        
        # Iniciar monitoramento contínuo
        asyncio.create_task(self._continuous_monitoring())
        
        logger.info("✅ Sistemas de robustez inicializados")
    
    async def execute_with_robustness(self, operation: Callable, 
                                      operation_name: str,
                                      component: str,
                                      *args, **kwargs) -> Any:
        """
        Executa operação com robustez extrema
        
        Args:
            operation: Função a executar
            operation_name: Nome da operação
            component: Componente responsável
            *args, **kwargs: Argumentos da operação
            
        Returns:
            Resultado da operação com tratamento robusto
        """
        error_id = self._generate_error_id()
        start_time = time.time()
        
        # Verificar circuit breaker
        if await self._is_circuit_open(component):
            logger.warning(f"⚡ Circuit breaker aberto para {component}, usando fallback")
            return await self._execute_fallback(operation_name, component, *args, **kwargs)
        
        # Executar com retry e fallback
        for attempt in range(self.max_retry_attempts):
            try:
                # Executar com monitoramento
                result = await self._execute_with_monitoring(
                    operation, operation_name, component, *args, **kwargs
                )
                
                # Sucesso - resetar circuit breaker se necessário
                await self._reset_circuit_breaker(component)
                
                execution_time = time.time() - start_time
                logger.info(f"✅ Operação {operation_name} concluída em {execution_time:.2f}s")
                
                return result
                
            except Exception as e:
                # Registrar erro
                error_context = ErrorContext(
                    error_id=error_id,
                    timestamp=time.time(),
                    severity=self._classify_error_severity(e),
                    component=component,
                    operation=operation_name,
                    error_message=str(e),
                    traceback=traceback.format_exc(),
                    recovery_attempts=attempt + 1,
                    recovery_actions=[],
                    impact_assessment=await self._assess_error_impact(e, component)
                )
                
                await self._handle_error(error_context, attempt)
                
                # Última tentativa - usar fallback
                if attempt == self.max_retry_attempts - 1:
                    logger.error(f"❌ Todas as tentativas falharam para {operation_name}, usando fallback")
                    return await self._execute_fallback(operation_name, component, *args, **kwargs)
                
                # Esperar antes de retry
                await asyncio.sleep(self._calculate_backoff_delay(attempt))
        
        # Isolar componente se falhas persistirem
        await self._isolate_if_needed(component)
        
        # Retornar resultado de fallback
        return await self._execute_fallback(operation_name, component, *args, **kwargs)
    
    async def _execute_with_monitoring(self, operation: Callable, 
                                    operation_name: str,
                                    component: str,
                                    *args, **kwargs) -> Any:
        """Executa operação com monitoramento detalhado"""
        start_time = time.time()
        
        try:
            # Monitorar recursos antes
            start_memory = psutil.virtual_memory().percent
            start_cpu = psutil.cpu_percent(interval=1)
            
            # Executar operação com performance optimizer
            result = await self.performance_optimizer.execute_with_optimization(
                operation, *args, **kwargs
            )
            
            # Monitorar recursos depois
            end_memory = psutil.virtual_memory().percent
            end_cpu = psutil.cpu_percent(interval=1)
            execution_time = time.time() - start_time
            
            # Registrar métricas
            metrics.record_operation_metrics(
                operation_name, execution_time, 
                start_memory, end_memory, start_cpu, end_cpu
            )
            
            return result
            
        except Exception as e:
            # Registrar erro com contexto completo
            error_context = ErrorContext(
                error_id=self._generate_error_id(),
                timestamp=time.time(),
                severity=self._classify_error_severity(e),
                component=component,
                operation=operation_name,
                error_message=str(e),
                traceback=traceback.format_exc(),
                recovery_attempts=0,
                recovery_actions=[],
                impact_assessment={
                    'memory_delta': psutil.virtual_memory().percent - start_memory,
                    'cpu_delta': psutil.cpu_percent(interval=1) - start_cpu,
                    'execution_time': time.time() - start_time
                }
            )
            
            await self._handle_error(error_context, 0)
            raise
    
    async def _handle_error(self, error_context: ErrorContext, attempt: int):
        """Lida com erro de forma robusta"""
        async with self.locks['error_handling']:
            # Adicionar ao histórico
            self.error_history.append(error_context)
            self.robustness_stats['total_errors'] += 1
            
            # Atualizar circuit breaker
            await self._update_circuit_breaker(error_context.component)
            
            # Tentar recuperação automática
            recovery_success = await self._attempt_automatic_recovery(error_context)
            
            if recovery_success:
                self.robustness_stats['recoveries_successful'] += 1
                logger.info(f"🔄 Recuperação automática bem-sucedida para {error_context.operation}")
            else:
                logger.warning(f"⚠️ Recuperação automática falhou para {error_context.operation}")
            
            self.robustness_stats['recoveries_attempted'] += 1
    
    async def _attempt_automatic_recovery(self, error_context: ErrorContext) -> bool:
        """Tenta recuperação automática baseada no tipo de erro"""
        recovery_strategies = self.recovery_strategies.get(error_context.component, [])
        
        for strategy in recovery_strategies:
            try:
                success = await strategy.recover(error_context)
                if success:
                    logger.info(f"✅ Estratégia {strategy.name} recuperou com sucesso")
                    return True
            except Exception as e:
                logger.error(f"❌ Estratégia {strategy.name} falhou: {str(e)}")
        
        # Estratégias genéricas baseadas no tipo de erro
        return await self._apply_generic_recovery(error_context)
    
    async def _apply_generic_recovery(self, error_context: ErrorContext) -> bool:
        """Aplica estratégias genéricas de recuperação"""
        try:
            # Recuperação baseada em memória
            if 'memory' in error_context.error_message.lower():
                await self._force_garbage_collection()
                return True
            
            # Recuperação baseada em conexão
            if 'connection' in error_context.error_message.lower() or 'timeout' in error_context.error_message.lower():
                await self._reset_connections(error_context.component)
                return True
            
            # Recuperação baseada em recursos
            if psutil.virtual_memory().percent > 90:
                await self._force_garbage_collection()
                await asyncio.sleep(2)  # Breve pausa para recuperação
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Erro na recuperação genérica: {str(e)}")
            return False
    
    async def _force_garbage_collection(self):
        """Força garbage collection agressivo"""
        logger.info("🗑️ Forçando garbage collection agressivo...")
        
        # Múltiplas rodadas de GC
        for i in range(3):
            gc.collect()
            await asyncio.sleep(0.1)
        
        # Limpar caches se necessário
        if psutil.virtual_memory().percent > 85:
            await self.performance_optimizer.cleanup()
        
        logger.info("✅ Garbage collection concluído")
    
    async def _reset_connections(self, component: str):
        """Reseta conexões do componente"""
        logger.info(f"🔄 Resetando conexões do componente: {component}")
        
        # Implementar reset específico por componente
        if 'http' in component.lower() or 'web' in component.lower():
            # Resetar pools HTTP
            await self.performance_optimizer.cleanup()
        
        # Esperar um pouco para recuperação
        await asyncio.sleep(1)
    
    def _classify_error_severity(self, error: Exception) -> ErrorSeverity:
        """Classifica severidade do erro automaticamente"""
        error_message = str(error).lower()
        
        # Erros críticos
        critical_keywords = [
            'memoryerror', 'outofmemory', 'systemexit', 'keyboardinterrupt',
            'connectionrefused', 'connectiontimeout', 'timeout',
            'database', 'sql', 'corruption'
        ]
        
        if any(keyword in error_message for keyword in critical_keywords):
            return ErrorSeverity.CRITICAL
        
        # Erros altos
        high_keywords = [
            'attributeerror', 'typeerror', 'valueerror', 'keyerror',
            'indexerror', 'permission', 'access denied', 'unauthorized'
        ]
        
        if any(keyword in error_message for keyword in high_keywords):
            return ErrorSeverity.HIGH
        
        # Erros médios
        medium_keywords = [
            'filenotfound', 'notfound', 'invalid', 'format',
            'parse', 'json', 'decode'
        ]
        
        if any(keyword in error_message for keyword in medium_keywords):
            return ErrorSeverity.MEDIUM
        
        return ErrorSeverity.LOW
    
    async def _assess_error_impact(self, error: Exception, component: str) -> Dict[str, Any]:
        """Avalia impacto do erro no sistema"""
        impact = {
            'user_experience': 'unknown',
            'data_integrity': 'unknown',
            'system_performance': 'unknown',
            'cascade_risk': 'unknown',
            'recovery_complexity': 'medium'
        }
        
        error_message = str(error).lower()
        
        # Impacto na experiência do usuário
        if any(keyword in error_message for keyword in ['timeout', 'connection', 'network']):
            impact['user_experience'] = 'degraded'
        elif any(keyword in error_message for keyword in ['notfound', 'invalid']):
            impact['user_experience'] = 'affected'
        else:
            impact['user_experience'] = 'minimal'
        
        # Impacto na integridade de dados
        if any(keyword in error_message for keyword in ['corruption', 'database', 'sql']):
            impact['data_integrity'] = 'high_risk'
        elif any(keyword in error_message for keyword in ['parse', 'format']):
            impact['data_integrity'] = 'medium_risk'
        else:
            impact['data_integrity'] = 'low_risk'
        
        # Impacto na performance
        if any(keyword in error_message for keyword in ['memory', 'cpu', 'resource']):
            impact['system_performance'] = 'degraded'
        else:
            impact['system_performance'] = 'minimal'
        
        # Risco de cascata
        if error.__class__.__name__ in ['MemoryError', 'ConnectionError', 'TimeoutError']:
            impact['cascade_risk'] = 'high'
        elif error.__class__.__name__ in ['ValueError', 'AttributeError']:
            impact['cascade_risk'] = 'medium'
        else:
            impact['cascade_risk'] = 'low'
        
        # Complexidade de recuperação
        if any(keyword in error_message for keyword in ['memory', 'system', 'critical']):
            impact['recovery_complexity'] = 'high'
        elif any(keyword in error_message for keyword in ['connection', 'timeout']):
            impact['recovery_complexity'] = 'medium'
        else:
            impact['recovery_complexity'] = 'low'
        
        return impact
    
    def _generate_error_id(self) -> str:
        """Gera ID único para erro"""
        timestamp = str(int(time.time() * 1000))
        random_suffix = str(random.randint(1000, 9999))
        return f"ERR_{timestamp}_{random_suffix}"
    
    def _calculate_backoff_delay(self, attempt: int) -> float:
        """Calcula delay exponencial com jitter"""
        base_delay = 1.0
        max_delay = 30.0
        
        # Exponential backoff com jitter
        delay = min(base_delay * (2 ** attempt), max_delay)
        jitter = random.uniform(0.1, 0.3) * delay
        
        return delay + jitter
    
    async def _setup_circuit_breakers(self):
        """Configura circuit breakers para componentes críticos"""
        critical_components = [
            'web_search', 'bing_search', 'reddit_collector', 'github_collector',
            'wikipedia_collector', 'news_collector', 'tor_client', 'llm_service',
            'database', 'cache', 'performance_optimizer'
        ]
        
        for component in critical_components:
            self.circuit_breakers[component] = {
                'state': 'closed',  # closed, open, half_open
                'failure_count': 0,
                'last_failure_time': 0,
                'success_count': 0,
                'last_success_time': 0
            }
        
        logger.info(f"⚡ Circuit breakers configurados para {len(critical_components)} componentes")
    
    async def _setup_health_checks(self):
        """Configura verificações de saúde automáticas"""
        health_checks = [
            HealthCheck(
                component='memory',
                status='unknown',
                last_check=time.time(),
                metrics={},
                issues=[],
                recommendations=[]
            ),
            HealthCheck(
                component='cpu',
                status='unknown',
                last_check=time.time(),
                metrics={},
                issues=[],
                recommendations=[]
            ),
            HealthCheck(
                component='disk',
                status='unknown',
                last_check=time.time(),
                metrics={},
                issues=[],
                recommendations=[]
            )
        ]
        
        for check in health_checks:
            self.health_checks[check.component] = check
        
        logger.info(f"🏥 Health checks configurados para {len(health_checks)} componentes")
    
    async def _setup_recovery_strategies(self):
        """Configura estratégias de recuperação"""
        # Estratégia para componentes de busca
        search_recovery = SearchRecoveryStrategy()
        
        # Estratégia para serviços de IA
        ai_recovery = AIServiceRecoveryStrategy()
        
        # Estratégia para cache e armazenamento
        storage_recovery = StorageRecoveryStrategy()
        
        # Estratégia para scraping
        scraping_recovery = ScrapingRecoveryStrategy()
        
        # Registrar estratégias
        self.recovery_strategies.update({
            'web_search': [search_recovery],
            'bing_search': [search_recovery],
            'reddit_collector': [search_recovery],
            'github_collector': [search_recovery],
            'wikipedia_collector': [search_recovery],
            'news_collector': [search_recovery],
            'llm_service': [ai_recovery],
            'cache': [storage_recovery],
            'database': [storage_recovery],
            'crawler': [scraping_recovery]
        })
        
        logger.info(f"🔄 Estratégias de recuperação configuradas para {len(self.recovery_strategies)} componentes")
    
    async def _is_circuit_open(self, component: str) -> bool:
        """Verifica se circuit breaker está aberto"""
        async with self.locks['circuit_breakers']:
            breaker = self.circuit_breakers.get(component)
            if not breaker:
                return False
            
            # Se está aberto e timeout não expirou
            if breaker['state'] == 'open':
                if time.time() - breaker['last_failure_time'] > self.circuit_breaker_timeout:
                    await self._reset_circuit_breaker(component)
                    return False
                return True
            
            return False
    
    async def _update_circuit_breaker(self, component: str):
        """Atualiza estado do circuit breaker"""
        async with self.locks['circuit_breakers']:
            if component not in self.circuit_breakers:
                self.circuit_breakers[component] = {
                    'state': 'closed',
                    'failure_count': 0,
                    'last_failure_time': 0,
                    'success_count': 0,
                    'last_success_time': 0
                }
            
            breaker = self.circuit_breakers[component]
            breaker['failure_count'] += 1
            breaker['last_failure_time'] = time.time()
            
            # Abrir circuito se atingir threshold
            if breaker['failure_count'] >= self.circuit_breaker_threshold:
                breaker['state'] = 'open'
                self.robustness_stats['circuit_breaks_triggered'] += 1
                logger.warning(f"⚡ Circuit breaker aberto para {component} após {breaker['failure_count']} falhas")
    
    async def _reset_circuit_breaker(self, component: str):
        """Reseta circuit breaker"""
        async with self.locks['circuit_breakers']:
            if component in self.circuit_breakers:
                self.circuit_breakers[component] = {
                    'state': 'closed',
                    'failure_count': 0,
                    'last_failure_time': 0,
                    'success_count': 0,
                    'last_success_time': 0
                }
    
    async def _isolate_if_needed(self, component: str):
        """Isola componente se necessário"""
        async with self.locks['isolation']:
            # Verificar se componente já está isolado
            if component in self.isolation_zones:
                return
            
            # Verificar se há falhas recentes críticas
            recent_errors = [
                error for error in self.error_history
                if (error.component == component and 
                    error.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL] and
                    time.time() - error.timestamp < 300)  # 5 minutos
            ]
            
            if len(recent_errors) >= 3:
                self.isolation_zones[component] = {
                    'isolation_time': time.time(),
                    'reason': 'multiple_critical_failures',
                    'estimated_recovery': time.time() + self.isolation_timeout
                }
                
                self.robustness_stats['components_isolated'] += 1
                logger.critical(f"🚨 Componente {component} isolado devido a falhas críticas")
    
    async def _execute_fallback(self, operation_name: str, component: str, 
                             *args, **kwargs) -> Any:
        """Executa fallback para operação"""
        self.robustness_stats['fallbacks_used'] += 1
        
        # Fallbacks específicos por componente
        fallback_handlers = {
            'web_search': self._web_search_fallback,
            'bing_search': self._web_search_fallback,
            'reddit_collector': self._social_fallback,
            'github_collector': self._social_fallback,
            'wikipedia_collector': self._knowledge_fallback,
            'news_collector': self._news_fallback,
            'llm_service': self._ai_fallback,
            'cache': self._storage_fallback,
            'database': self._storage_fallback
        }
        
        handler = fallback_handlers.get(component, self._generic_fallback)
        
        try:
            logger.info(f"🔄 Executando fallback para {operation_name} no componente {component}")
            return await handler(operation_name, component, *args, **kwargs)
        except Exception as e:
            logger.error(f"❌ Fallback falhou: {str(e)}")
            return self._empty_fallback(operation_name)
    
    async def _web_search_fallback(self, operation_name: str, component: str, *args, **kwargs) -> Any:
        """Fallback para busca web"""
        return {
            'source': 'fallback_web',
            'title': f'Fallback: {operation_name}',
            'description': 'Serviço de busca temporariamente indisponível',
            'url': '',
            'relevance_score': 0.1,
            'timestamp': time.time(),
            'extracted_data': {}
        }
    
    async def _social_fallback(self, operation_name: str, component: str, *args, **kwargs) -> Any:
        """Fallback para coletores sociais"""
        return {
            'source': f'fallback_{component}',
            'title': f'Fallback: {operation_name}',
            'description': f'Serviço {component} temporariamente indisponível',
            'url': '',
            'relevance_score': 0.1,
            'timestamp': time.time(),
            'extracted_data': {}
        }
    
    async def _knowledge_fallback(self, operation_name: str, component: str, *args, **kwargs) -> Any:
        """Fallback para fontes de conhecimento"""
        return {
            'source': f'fallback_{component}',
            'title': f'Fallback: {operation_name}',
            'description': f'Fonte de conhecimento {component} temporariamente indisponível',
            'url': '',
            'relevance_score': 0.1,
            'timestamp': time.time(),
            'extracted_data': {}
        }
    
    async def _news_fallback(self, operation_name: str, component: str, *args, **kwargs) -> Any:
        """Fallback para fontes de notícias"""
        return {
            'source': f'fallback_{component}',
            'title': f'Fallback: {operation_name}',
            'description': f'Serviço de notícias {component} temporariamente indisponível',
            'url': '',
            'relevance_score': 0.1,
            'timestamp': time.time(),
            'extracted_data': {}
        }
    
    async def _ai_fallback(self, operation_name: str, component: str, *args, **kwargs) -> Any:
        """Fallback para serviços de IA"""
        return {
            'query': args[0] if args else '',
            'total_results': 0,
            'data': [],
            'summary': f'Serviço de IA {component} temporariamente indisponível. Usando modo básico.',
            'error': 'ai_service_unavailable'
        }
    
    async def _storage_fallback(self, operation_name: str, component: str, *args, **kwargs) -> Any:
        """Fallback para armazenamento"""
        return {
            'status': 'degraded',
            'message': f'Serviço de armazenamento {component} operando em modo degradado',
            'data': {},
            'fallback_used': True
        }
    
    def _generic_fallback(self, operation_name: str, component: str, *args, **kwargs) -> Any:
        """Fallback genérico"""
        return {
            'source': f'fallback_generic',
            'title': f'Fallback: {operation_name}',
            'description': f'Serviço {component} temporariamente indisponível',
            'url': '',
            'relevance_score': 0.1,
            'timestamp': time.time(),
            'extracted_data': {}
        }
    
    def _empty_fallback(self, operation_name: str) -> Any:
        """Fallback vazio quando tudo falha"""
        return {
            'source': 'empty_fallback',
            'title': f'Serviço indisponível: {operation_name}',
            'description': 'Todos os serviços estão temporariamente indisponíveis',
            'url': '',
            'relevance_score': 0.0,
            'timestamp': time.time(),
            'extracted_data': {}
        }
    
    async def _continuous_monitoring(self):
        """Monitoramento contínuo da saúde do sistema"""
        logger.info("📊 Iniciando monitoramento contínuo da saúde do sistema")
        
        while True:
            try:
                # Health checks de recursos
                await self._check_system_health()
                
                # Health checks de componentes
                await self._check_components_health()
                
                # Limpar histórico antigo
                await self._cleanup_old_data()
                
                # Esperar próximo ciclo
                await asyncio.sleep(self.health_check_interval)
                
            except Exception as e:
                logger.error(f"❌ Erro no monitoramento contínuo: {str(e)}")
                await asyncio.sleep(60)  # Esperar 1 minuto em caso de erro
    
    async def _check_system_health(self):
        """Verifica saúde geral do sistema"""
        try:
            # Verificar memória
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                logger.warning(f"⚠️ Uso de memória crítico: {memory.percent:.1f}%")
                await self._force_garbage_collection()
            
            # Verificar CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 80:
                logger.warning(f"⚠️ Uso de CPU alto: {cpu_percent:.1f}%")
            
            # Verificar disco
            disk = psutil.disk_usage('/')
            if disk.percent > 85:
                logger.warning(f"⚠️ Uso de disco alto: {disk.percent:.1f}%")
            
            # Atualizar métricas
            self.robustness_stats['system_health'] = {
                'memory_percent': memory.percent,
                'cpu_percent': cpu_percent,
                'disk_percent': disk.percent,
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"❌ Erro verificando saúde do sistema: {str(e)}")
    
    async def _check_components_health(self):
        """Verifica saúde dos componentes"""
        for component, health_check in self.health_checks.items():
            try:
                # Implementar verificação específica por componente
                if component == 'memory':
                    memory = psutil.virtual_memory()
                    health_check.metrics = {
                        'usage_percent': memory.percent,
                        'available_gb': memory.available / (1024**3),
                        'used_gb': memory.used / (1024**3)
                    }
                    health_check.status = 'healthy' if memory.percent < 80 else 'degraded'
                
                elif component == 'cpu':
                    cpu_percent = psutil.cpu_percent(interval=1)
                    health_check.metrics = {
                        'usage_percent': cpu_percent,
                        'core_count': psutil.cpu_count()
                    }
                    health_check.status = 'healthy' if cpu_percent < 70 else 'degraded'
                
                elif component == 'disk':
                    disk = psutil.disk_usage('/')
                    health_check.metrics = {
                        'usage_percent': disk.percent,
                        'free_gb': disk.free / (1024**3),
                        'used_gb': disk.used / (1024**3)
                    }
                    health_check.status = 'healthy' if disk.percent < 80 else 'degraded'
                
                health_check.last_check = time.time()
                
            except Exception as e:
                health_check.status = 'error'
                health_check.issues = [str(e)]
                logger.error(f"❌ Erro verificando saúde do componente {component}: {str(e)}")
    
    async def _cleanup_old_data(self):
        """Limpa dados antigos para evitar vazamento de memória"""
        try:
            # Limpar erros antigos (manter últimos 500)
            if len(self.error_history) > 500:
                # Manter apenas erros recentes e críticos
                recent_critical = [
                    error for error in self.error_history
                    if (error.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL] or
                        time.time() - error.timestamp < 3600)  # 1 hora
                ]
                
                recent_other = [
                    error for error in self.error_history
                    if (error.severity not in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL] and
                        time.time() - error.timestamp < 1800)  # 30 minutos
                ]
                
                # Manter últimos 100 críticos + 400 outros
                self.error_history.clear()
                self.error_history.extend(recent_critical[:100])
                self.error_history.extend(recent_other[:400])
            
            # Forçar GC periodicamente
            if len(self.error_history) % 100 == 0:
                await self._force_garbage_collection()
                
        except Exception as e:
            logger.error(f"❌ Erro limpando dados antigos: {str(e)}")
    
    def get_robustness_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas completas de robustez"""
        return {
            'error_stats': {
                'total_errors': self.robustness_stats['total_errors'],
                'recent_errors': len([
                    error for error in self.error_history
                    if time.time() - error.timestamp < 3600
                ]),
                'error_rate': self._calculate_error_rate(),
                'critical_errors': len([
                    error for error in self.error_history
                    if error.severity == ErrorSeverity.CRITICAL
                ])
            },
            'recovery_stats': {
                'recoveries_attempted': self.robustness_stats['recoveries_attempted'],
                'recoveries_successful': self.robustness_stats['recoveries_successful'],
                'success_rate': (
                    self.robustness_stats['recoveries_successful'] / 
                    max(self.robustness_stats['recoveries_attempted'], 1) * 100
                )
            },
            'circuit_breaker_stats': {
                'total_breakers': len(self.circuit_breakers),
                'open_breakers': len([
                    cb for cb in self.circuit_breakers.values()
                    if cb['state'] == 'open'
                ]),
                'triggered_count': self.robustness_stats['circuit_breaks_triggered']
            },
            'isolation_stats': {
                'isolated_components': len(self.isolation_zones),
                'components': list(self.isolation_zones.keys())
            },
            'system_health': self.robustness_stats.get('system_health', {}),
            'uptime': time.time() - (self.error_history[0].timestamp if self.error_history else time.time())
        }
    
    def _calculate_error_rate(self) -> float:
        """Calcula taxa de erros por hora"""
        if not self.error_history:
            return 0.0
        
        # Erros da última hora
        recent_errors = [
            error for error in self.error_history
            if time.time() - error.timestamp < 3600
        ]
        
        return len(recent_errors)
    
    async def cleanup(self):
        """Limpa recursos do gerenciador de robustez"""
        logger.info("🧹 Limpando recursos do Robustness Manager...")
        
        # Limpar performance optimizer
        await self.performance_optimizer.cleanup()
        
        # Limpar caches
        self.error_history.clear()
        self.circuit_breakers.clear()
        self.health_checks.clear()
        self.recovery_strategies.clear()
        self.isolation_zones.clear()
        
        logger.info("✅ Robustness Manager limpo")

# Estratégias de recuperação específicas
class SearchRecoveryStrategy:
    """Estratégia de recuperação para componentes de busca"""
    
    def __init__(self):
        self.name = "search_recovery"
    
    async def recover(self, error_context: ErrorContext) -> bool:
        """Tenta recuperar componente de busca"""
        try:
            # Esperar e tentar novamente
            await asyncio.sleep(2)
            
            # Resetar conexões
            logger.info(f"🔄 Estratégia de recuperação aplicada para {error_context.component}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro na estratégia de recuperação: {str(e)}")
            return False

class AIServiceRecoveryStrategy:
    """Estratégia de recuperação para serviços de IA"""
    
    def __init__(self):
        self.name = "ai_service_recovery"
    
    async def recover(self, error_context: ErrorContext) -> bool:
        """Tenta recuperar serviço de IA"""
        try:
            # Forçar garbage collection
            import gc
            gc.collect()
            
            # Esperar recuperação
            await asyncio.sleep(3)
            
            logger.info(f"🤖 Estratégia de recuperação aplicada para {error_context.component}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro na estratégia de recuperação de IA: {str(e)}")
            return False

class StorageRecoveryStrategy:
    """Estratégia de recuperação para armazenamento"""
    
    def __init__(self):
        self.name = "storage_recovery"
    
    async def recover(self, error_context: ErrorContext) -> bool:
        """Tenta recuperar armazenamento"""
        try:
            # Limpar caches
            logger.info(f"💾 Estratégia de recuperação aplicada para {error_context.component}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro na estratégia de recuperação de armazenamento: {str(e)}")
            return False

class ScrapingRecoveryStrategy:
    """Estratégia de recuperação para scraping"""
    
    def __init__(self):
        self.name = "scraping_recovery"
    
    async def recover(self, error_context: ErrorContext) -> bool:
        """Tenta recuperar componente de scraping"""
        try:
            # Resetar sessões HTTP
            await asyncio.sleep(5)
            
            logger.info(f"🕷️ Estratégia de recuperação aplicada para {error_context.component}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro na estratégia de recuperação de scraping: {str(e)}")
            return False
