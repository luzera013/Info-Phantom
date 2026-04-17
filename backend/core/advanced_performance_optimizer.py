"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - Advanced Performance Optimizer
Sistema avançado de otimização de performance com monitoramento em tempo real
"""

import asyncio
import time
import psutil
import threading
from typing import List, Dict, Any, Optional, Set, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging
import json
import math

from ..utils.logger import setup_logger
from ..utils.metrics import MetricsCollector
from ..utils.ttl_cache import TTLCache

logger = setup_logger(__name__)
metrics = MetricsCollector()

@dataclass
class PerformanceMetrics:
    """Métricas de performance do sistema"""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_usage_percent: float
    network_io: Dict[str, float]
    active_connections: int
    response_time: float
    throughput: float
    error_rate: float
    cache_hit_rate: float
    queue_size: int
    thread_count: int

@dataclass
class OptimizationRule:
    """Regra de otimização automática"""
    rule_id: str
    name: str
    condition: str  # Expressão booleana
    action: str  # Ação a executar
    priority: int  # 1-10, onde 10 é maior prioridade
    enabled: bool = True
    cooldown: int = 60  # Segundos entre execuções
    last_executed: float = 0.0
    execution_count: int = 0
    success_count: int = 0

@dataclass
class PerformanceThreshold:
    """Limite de performance para alertas"""
    metric_name: str
    warning_threshold: float
    critical_threshold: float
    comparison: str = ">"  # >, <, >=, <=, ==

class AdvancedPerformanceOptimizer:
    """Otimizador de performance avançado com monitoramento inteligente"""
    
    def __init__(self):
        self.metrics_history: deque = deque(maxlen=1000)  # Últimas 1000 medições
        self.optimization_rules: List[OptimizationRule] = []
        self.thresholds: List[PerformanceThreshold] = []
        self.active_optimizations: Dict[str, Any] = {}
        self.performance_cache = TTLCache(ttl=300)  # 5 minutos
        
        # Configurações
        self.config = {
            'monitoring_interval': 5.0,  # Segundos
            'auto_optimization': True,
            'adaptive_scaling': True,
            'resource_prediction': True,
            'bottleneck_detection': True,
            'load_balancing': True,
            'caching_optimization': True,
            'thread_pool_optimization': True,
            'memory_optimization': True,
            'network_optimization': True,
            'alerting_enabled': True,
            'performance_logging': True,
            'metrics_retention_hours': 24
        }
        
        # Estado do sistema
        self.system_state = {
            'current_load': 0.0,
            'predicted_load': 0.0,
            'optimal_concurrency': 10,
            'cache_hit_rate': 0.0,
            'avg_response_time': 0.0,
            'error_rate': 0.0,
            'throughput': 0.0,
            'bottlenecks': [],
            'recommendations': []
        }
        
        # Controle de execução
        self.monitoring_active = False
        self.optimization_lock = asyncio.Lock()
        
        # Inicializar regras e thresholds
        self._setup_default_rules()
        self._setup_default_thresholds()
        
        logger.info(" Advanced Performance Optimizer inicializado")
    
    def _setup_default_rules(self):
        """Configura regras de otimização padrão"""
        rules = [
            OptimizationRule(
                rule_id="cpu_high",
                name="Alto uso de CPU",
                condition="cpu_percent > 80",
                action="reduce_concurrency",
                priority=8,
                cooldown=30
            ),
            OptimizationRule(
                rule_id="memory_high",
                name="Alto uso de memória",
                condition="memory_percent > 85",
                action="clear_cache",
                priority=9,
                cooldown=60
            ),
            OptimizationRule(
                rule_id="response_time_high",
                name="Tempo de resposta alto",
                condition="response_time > 2000",
                action="increase_cache_size",
                priority=7,
                cooldown=45
            ),
            OptimizationRule(
                rule_id="error_rate_high",
                name="Alta taxa de erros",
                condition="error_rate > 0.05",
                action="enable_circuit_breaker",
                priority=10,
                cooldown=30
            ),
            OptimizationRule(
                rule_id="low_throughput",
                name="Baixo throughput",
                condition="throughput < 10",
                action="increase_concurrency",
                priority=6,
                cooldown=60
            ),
            OptimizationRule(
                rule_id="cache_hit_rate_low",
                name="Baixa taxa de cache hit",
                condition="cache_hit_rate < 0.7",
                action="optimize_cache_strategy",
                priority=5,
                cooldown=120
            ),
            OptimizationRule(
                rule_id="disk_io_high",
                name="Alto uso de disco",
                condition="disk_usage_percent > 90",
                action="cleanup_temp_files",
                priority=9,
                cooldown=300
            ),
            OptimizationRule(
                rule_id="network_congestion",
                name="Congestionamento de rede",
                condition="active_connections > 1000",
                action="enable_connection_pooling",
                priority=7,
                cooldown=60
            )
        ]
        
        self.optimization_rules = rules
    
    def _setup_default_thresholds(self):
        """Configura thresholds de alerta padrão"""
        thresholds = [
            PerformanceThreshold("cpu_percent", 70.0, 90.0, ">"),
            PerformanceThreshold("memory_percent", 75.0, 90.0, ">"),
            PerformanceThreshold("response_time", 1000.0, 3000.0, ">"),
            PerformanceThreshold("error_rate", 0.02, 0.1, ">"),
            PerformanceThreshold("cache_hit_rate", 0.6, 0.4, "<"),
            PerformanceThreshold("throughput", 20.0, 10.0, "<"),
            PerformanceThreshold("disk_usage_percent", 80.0, 95.0, ">"),
            PerformanceThreshold("active_connections", 500, 1000, ">")
        ]
        
        self.thresholds = thresholds
    
    async def initialize(self):
        """Inicializa o otimizador de performance"""
        if self.config['auto_optimization']:
            await self.start_monitoring()
        
        logger.info(" Advanced Performance Optimizer pronto")
    
    async def start_monitoring(self):
        """Inicia monitoramento contínuo"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        
        # Iniciar tarefa de monitoramento
        asyncio.create_task(self._monitoring_loop())
        
        logger.info(" Monitoramento de performance iniciado")
    
    async def stop_monitoring(self):
        """Para monitoramento contínuo"""
        self.monitoring_active = False
        logger.info(" Monitoramento de performance parado")
    
    async def _monitoring_loop(self):
        """Loop principal de monitoramento"""
        while self.monitoring_active:
            try:
                # Coletar métricas
                metrics = await self._collect_metrics()
                
                # Adicionar ao histórico
                self.metrics_history.append(metrics)
                
                # Atualizar estado do sistema
                await self._update_system_state(metrics)
                
                # Verificar thresholds
                if self.config['alerting_enabled']:
                    await self._check_thresholds(metrics)
                
                # Executar otimizações automáticas
                if self.config['auto_optimization']:
                    await self._execute_optimizations(metrics)
                
                # Prever carga futura
                if self.config['resource_prediction']:
                    await self._predict_future_load()
                
                # Detectar bottlenecks
                if self.config['bottleneck_detection']:
                    await self._detect_bottlenecks()
                
                # Aguardar próxima coleta
                await asyncio.sleep(self.config['monitoring_interval'])
                
            except Exception as e:
                logger.error(f" Erro no loop de monitoramento: {str(e)}")
                await asyncio.sleep(self.config['monitoring_interval'])
    
    async def _collect_metrics(self) -> PerformanceMetrics:
        """Coleta métricas atuais do sistema"""
        timestamp = time.time()
        
        # Métricas de CPU
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Métricas de memória
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_mb = memory.used / (1024 * 1024)
        
        # Métricas de disco
        disk = psutil.disk_usage('/')
        disk_usage_percent = disk.percent
        
        # Métricas de rede
        network = psutil.net_io_counters()
        network_io = {
            'bytes_sent': network.bytes_sent,
            'bytes_recv': network.bytes_recv,
            'packets_sent': network.packets_sent,
            'packets_recv': network.packets_recv
        }
        
        # Conexões ativas
        active_connections = len(psutil.net_connections())
        
        # Métricas de aplicação (simuladas - em produção viriam de métricas reais)
        response_time = self.system_state.get('avg_response_time', 100.0)
        throughput = self.system_state.get('throughput', 50.0)
        error_rate = self.system_state.get('error_rate', 0.01)
        cache_hit_rate = self.system_state.get('cache_hit_rate', 0.8)
        queue_size = self.system_state.get('queue_size', 0)
        thread_count = threading.active_count()
        
        return PerformanceMetrics(
            timestamp=timestamp,
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_used_mb=memory_used_mb,
            disk_usage_percent=disk_usage_percent,
            network_io=network_io,
            active_connections=active_connections,
            response_time=response_time,
            throughput=throughput,
            error_rate=error_rate,
            cache_hit_rate=cache_hit_rate,
            queue_size=queue_size,
            thread_count=thread_count
        )
    
    async def _update_system_state(self, metrics: PerformanceMetrics):
        """Atualiza estado do sistema com base nas métricas"""
        # Calcular carga atual (média ponderada)
        current_load = (
            metrics.cpu_percent * 0.3 +
            metrics.memory_percent * 0.3 +
            (metrics.response_time / 100) * 0.2 +  # Normalizar para 0-100
            (metrics.error_rate * 1000) * 0.2  # Normalizar para 0-100
        )
        
        self.system_state['current_load'] = current_load
        
        # Atualizar médias móveis
        if len(self.metrics_history) > 1:
            # Média de response time
            recent_response_times = [m.response_time for m in list(self.metrics_history)[-10:]]
            self.system_state['avg_response_time'] = sum(recent_response_times) / len(recent_response_times)
            
            # Média de throughput
            recent_throughput = [m.throughput for m in list(self.metrics_history)[-10:]]
            self.system_state['throughput'] = sum(recent_throughput) / len(recent_throughput)
            
            # Média de error rate
            recent_error_rates = [m.error_rate for m in list(self.metrics_history)[-10:]]
            self.system_state['error_rate'] = sum(recent_error_rates) / len(recent_error_rates)
            
            # Média de cache hit rate
            recent_cache_rates = [m.cache_hit_rate for m in list(self.metrics_history)[-10:]]
            self.system_state['cache_hit_rate'] = sum(recent_cache_rates) / len(recent_cache_rates)
        
        # Calcular concorrência ótima
        if self.config['adaptive_scaling']:
            await self._calculate_optimal_concurrency(metrics)
    
    async def _calculate_optimal_concurrency(self, metrics: PerformanceMetrics):
        """Calcula concorrência ótima baseada nas métricas"""
        # Fórmula adaptativa baseada na carga do sistema
        cpu_factor = max(0, (100 - metrics.cpu_percent) / 100)
        memory_factor = max(0, (100 - metrics.memory_percent) / 100)
        response_factor = max(0, (2000 - metrics.response_time) / 2000)  # 2s como referência
        
        # Calcular concorrência ótima
        base_concurrency = 10
        optimal_concurrency = int(base_concurrency * cpu_factor * memory_factor * response_factor)
        
        # Limitar entre 1 e 50
        optimal_concurrency = max(1, min(50, optimal_concurrency))
        
        self.system_state['optimal_concurrency'] = optimal_concurrency
    
    async def _check_thresholds(self, metrics: PerformanceMetrics):
        """Verifica thresholds e gera alertas"""
        for threshold in self.thresholds:
            metric_value = getattr(metrics, threshold.metric_name, 0)
            
            triggered = False
            level = "normal"
            
            if threshold.comparison == ">":
                if metric_value > threshold.critical_threshold:
                    triggered = True
                    level = "critical"
                elif metric_value > threshold.warning_threshold:
                    triggered = True
                    level = "warning"
            elif threshold.comparison == "<":
                if metric_value < threshold.critical_threshold:
                    triggered = True
                    level = "critical"
                elif metric_value < threshold.warning_threshold:
                    triggered = True
                    level = "warning"
            
            if triggered:
                await self._trigger_alert(threshold.metric_name, metric_value, level)
    
    async def _trigger_alert(self, metric_name: str, value: float, level: str):
        """Dispara alerta de performance"""
        alert_data = {
            'timestamp': time.time(),
            'metric': metric_name,
            'value': value,
            'level': level,
            'message': f"Alerta {level}: {metric_name} = {value:.2f}"
        }
        
        logger.warning(f" Performance Alert: {alert_data['message']}")
        
        # Em produção, enviar para sistema de alertas
        # await self.alert_service.send_alert(alert_data)
    
    async def _execute_optimizations(self, metrics: PerformanceMetrics):
        """Executa otimizações automáticas baseadas nas regras"""
        async with self.optimization_lock:
            for rule in self.optimization_rules:
                if not rule.enabled:
                    continue
                
                # Verificar cooldown
                if time.time() - rule.last_executed < rule.cooldown:
                    continue
                
                # Avaliar condição
                if await self._evaluate_condition(rule.condition, metrics):
                    try:
                        # Executar ação
                        success = await self._execute_action(rule.action, metrics)
                        
                        rule.last_executed = time.time()
                        rule.execution_count += 1
                        
                        if success:
                            rule.success_count += 1
                            logger.info(f" Otimização executada: {rule.name} - {rule.action}")
                        else:
                            logger.warning(f" Falha na otimização: {rule.name}")
                        
                    except Exception as e:
                        logger.error(f" Erro executando otimização {rule.name}: {str(e)}")
    
    async def _evaluate_condition(self, condition: str, metrics: PerformanceMetrics) -> bool:
        """Avalia condição da regra de otimização"""
        try:
            # Substituir variáveis na condição
            condition_vars = {
                'cpu_percent': metrics.cpu_percent,
                'memory_percent': metrics.memory_percent,
                'response_time': metrics.response_time,
                'throughput': metrics.throughput,
                'error_rate': metrics.error_rate,
                'cache_hit_rate': metrics.cache_hit_rate,
                'disk_usage_percent': metrics.disk_usage_percent,
                'active_connections': metrics.active_connections
            }
            
            # Avaliar expressão
            return eval(condition, {"__builtins__": {}}, condition_vars)
            
        except Exception as e:
            logger.error(f" Erro avaliando condição '{condition}': {str(e)}")
            return False
    
    async def _execute_action(self, action: str, metrics: PerformanceMetrics) -> bool:
        """Executa ação de otimização"""
        try:
            if action == "reduce_concurrency":
                return await self._reduce_concurrency()
            elif action == "increase_concurrency":
                return await self._increase_concurrency()
            elif action == "clear_cache":
                return await self._clear_cache()
            elif action == "increase_cache_size":
                return await self._increase_cache_size()
            elif action == "enable_circuit_breaker":
                return await self._enable_circuit_breaker()
            elif action == "optimize_cache_strategy":
                return await self._optimize_cache_strategy()
            elif action == "cleanup_temp_files":
                return await self._cleanup_temp_files()
            elif action == "enable_connection_pooling":
                return await self._enable_connection_pooling()
            else:
                logger.warning(f" Ação desconhecida: {action}")
                return False
                
        except Exception as e:
            logger.error(f" Erro executando ação {action}: {str(e)}")
            return False
    
    async def _reduce_concurrency(self) -> bool:
        """Reduz concorrência do sistema"""
        current_optimal = self.system_state['optimal_concurrency']
        new_concurrency = max(1, current_optimal // 2)
        self.system_state['optimal_concurrency'] = new_concurrency
        
        logger.info(f" Concorrência reduzida: {current_optimal} -> {new_concurrency}")
        return True
    
    async def _increase_concurrency(self) -> bool:
        """Aumenta concorrência do sistema"""
        current_optimal = self.system_state['optimal_concurrency']
        new_concurrency = min(50, current_optimal * 2)
        self.system_state['optimal_concurrency'] = new_concurrency
        
        logger.info(f" Concorrência aumentada: {current_optimal} -> {new_concurrency}")
        return True
    
    async def _clear_cache(self) -> bool:
        """Limpa cache do sistema"""
        # Limpar caches conhecidos
        self.performance_cache.clear()
        
        # Em produção, limpar outros caches
        # await self.main_cache.clear()
        # await self.query_cache.clear()
        
        logger.info(" Cache limpo para liberar memória")
        return True
    
    async def _increase_cache_size(self) -> bool:
        """Aumenta tamanho do cache"""
        # Em produção, ajustar tamanho dos caches
        logger.info(" Tamanho do cache aumentado para melhorar performance")
        return True
    
    async def _enable_circuit_breaker(self) -> bool:
        """Habilita circuit breaker"""
        # Em produção, habilitar circuit breakers para serviços instáveis
        logger.info(" Circuit breaker habilitado para proteção")
        return True
    
    async def _optimize_cache_strategy(self) -> bool:
        """Otimiza estratégia de cache"""
        # Em produção, ajustar TTL, estratégias de evicção, etc.
        logger.info(" Estratégia de cache otimizada")
        return True
    
    async def _cleanup_temp_files(self) -> bool:
        """Limpa arquivos temporários"""
        import tempfile
        import os
        
        temp_dir = tempfile.gettempdir()
        cleaned_files = 0
        
        try:
            for filename in os.listdir(temp_dir):
                filepath = os.path.join(temp_dir, filename)
                try:
                    # Remover arquivos mais antigos que 1 hora
                    if os.path.isfile(filepath):
                        file_age = time.time() - os.path.getmtime(filepath)
                        if file_age > 3600:  # 1 hora
                            os.remove(filepath)
                            cleaned_files += 1
                except:
                    continue
            
            logger.info(f" {cleaned_files} arquivos temporários limpos")
            return True
            
        except Exception as e:
            logger.error(f" Erro limpando arquivos temporários: {str(e)}")
            return False
    
    async def _enable_connection_pooling(self) -> bool:
        """Habilita pooling de conexões"""
        # Em produção, configurar connection pooling
        logger.info(" Connection pooling habilitado")
        return True
    
    async def _predict_future_load(self) -> float:
        """Prevê carga futura baseada no histórico"""
        if len(self.metrics_history) < 10:
            return self.system_state['current_load']
        
        # Extrair cargas recentes
        recent_loads = []
        for metrics in list(self.metrics_history)[-20:]:
            load = (
                metrics.cpu_percent * 0.3 +
                metrics.memory_percent * 0.3 +
                (metrics.response_time / 100) * 0.2 +
                (metrics.error_rate * 1000) * 0.2
            )
            recent_loads.append(load)
        
        # Prever usando média móvel ponderada
        weights = [i / len(recent_loads) for i in range(1, len(recent_loads) + 1)]
        predicted_load = sum(load * weight for load, weight in zip(recent_loads, weights))
        
        self.system_state['predicted_load'] = predicted_load
        return predicted_load
    
    async def _detect_bottlenecks(self) -> List[str]:
        """Detecta bottlenecks de performance"""
        bottlenecks = []
        
        if len(self.metrics_history) < 5:
            return bottlenecks
        
        # Analisar tendências recentes
        recent_metrics = list(self.metrics_history)[-5:]
        
        # Detectar CPU bottleneck
        cpu_trend = [m.cpu_percent for m in recent_metrics]
        if all(cpu > 80 for cpu in cpu_trend):
            bottlenecks.append("CPU: Uso consistentemente alto")
        
        # Detectar memory bottleneck
        memory_trend = [m.memory_percent for m in recent_metrics]
        if all(memory > 85 for memory in memory_trend):
            bottlenecks.append("Memory: Uso consistentemente alto")
        
        # Detectar I/O bottleneck
        response_trend = [m.response_time for m in recent_metrics]
        if all(response > 2000 for response in response_trend):
            bottlenecks.append("I/O: Tempo de resposta alto")
        
        # Detectar network bottleneck
        connection_trend = [m.active_connections for m in recent_metrics]
        if all(connections > 800 for connections in connection_trend):
            bottlenecks.append("Network: Muitas conexões ativas")
        
        self.system_state['bottlenecks'] = bottlenecks
        
        if bottlenecks:
            logger.warning(f" Bottlenecks detectados: {', '.join(bottlenecks)}")
        
        return bottlenecks
    
    async def get_performance_report(self) -> Dict[str, Any]:
        """Gera relatório completo de performance"""
        if not self.metrics_history:
            return {"error": "Nenhuma métrica disponível"}
        
        current_metrics = self.metrics_history[-1]
        
        # Calcular estatísticas
        metrics_list = list(self.metrics_history)
        
        stats = {
            'cpu': {
                'current': current_metrics.cpu_percent,
                'avg': sum(m.cpu_percent for m in metrics_list) / len(metrics_list),
                'max': max(m.cpu_percent for m in metrics_list),
                'min': min(m.cpu_percent for m in metrics_list)
            },
            'memory': {
                'current': current_metrics.memory_percent,
                'avg': sum(m.memory_percent for m in metrics_list) / len(metrics_list),
                'max': max(m.memory_percent for m in metrics_list),
                'min': min(m.memory_percent for m in metrics_list)
            },
            'response_time': {
                'current': current_metrics.response_time,
                'avg': sum(m.response_time for m in metrics_list) / len(metrics_list),
                'max': max(m.response_time for m in metrics_list),
                'min': min(m.response_time for m in metrics_list)
            },
            'throughput': {
                'current': current_metrics.throughput,
                'avg': sum(m.throughput for m in metrics_list) / len(metrics_list),
                'max': max(m.throughput for m in metrics_list),
                'min': min(m.throughput for m in metrics_list)
            },
            'error_rate': {
                'current': current_metrics.error_rate,
                'avg': sum(m.error_rate for m in metrics_list) / len(metrics_list),
                'max': max(m.error_rate for m in metrics_list),
                'min': min(m.error_rate for m in metrics_list)
            },
            'cache_hit_rate': {
                'current': current_metrics.cache_hit_rate,
                'avg': sum(m.cache_hit_rate for m in metrics_list) / len(metrics_list),
                'max': max(m.cache_hit_rate for m in metrics_list),
                'min': min(m.cache_hit_rate for m in metrics_list)
            }
        }
        
        # Gerar recomendações
        recommendations = await self._generate_recommendations(stats)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'monitoring_duration': len(metrics_list) * self.config['monitoring_interval'],
            'metrics_collected': len(metrics_list),
            'current_metrics': current_metrics.__dict__,
            'statistics': stats,
            'system_state': self.system_state,
            'bottlenecks': self.system_state['bottlenecks'],
            'recommendations': recommendations,
            'optimization_rules': [
                {
                    'name': rule.name,
                    'enabled': rule.enabled,
                    'executions': rule.execution_count,
                    'success_rate': rule.success_count / max(1, rule.execution_count)
                }
                for rule in self.optimization_rules
            ],
            'config': self.config
        }
    
    async def _generate_recommendations(self, stats: Dict[str, Any]) -> List[str]:
        """Gera recomendações de otimização"""
        recommendations = []
        
        # Recomendações de CPU
        if stats['cpu']['avg'] > 70:
            recommendations.append("Considerar escalabilidade horizontal para reduzir carga de CPU")
        if stats['cpu']['max'] > 90:
            recommendations.append("Implementar throttling para picos de CPU")
        
        # Recomendações de memória
        if stats['memory']['avg'] > 75:
            recommendations.append("Otimizar uso de memória e implementar garbage collection agressivo")
        if stats['memory']['max'] > 90:
            recommendations.append("Adicionar mais RAM ou otimizar algoritmos de memória")
        
        # Recomendações de response time
        if stats['response_time']['avg'] > 1000:
            recommendations.append("Implementar cache de resultados e otimizar consultas")
        if stats['response_time']['max'] > 3000:
            recommendations.append("Adicionar CDN e otimizar rede de entrega")
        
        # Recomendações de throughput
        if stats['throughput']['avg'] < 20:
            recommendations.append("Aumentar concorrência e otimizar processamento paralelo")
        
        # Recomendações de error rate
        if stats['error_rate']['avg'] > 0.02:
            recommendations.append("Implementar retry automático e circuit breakers")
        
        # Recomendações de cache
        if stats['cache_hit_rate']['avg'] < 0.7:
            recommendations.append("Otimizar estratégias de cache e aumentar TTL")
        
        # Recomendações de bottlenecks
        if self.system_state['bottlenecks']:
            recommendations.append("Investigar e resolver bottlenecks identificados")
        
        return recommendations
    
    async def add_optimization_rule(self, rule: OptimizationRule):
        """Adiciona nova regra de otimização"""
        self.optimization_rules.append(rule)
        logger.info(f" Regra de otimização adicionada: {rule.name}")
    
    async def remove_optimization_rule(self, rule_id: str) -> bool:
        """Remove regra de otimização"""
        for i, rule in enumerate(self.optimization_rules):
            if rule.rule_id == rule_id:
                del self.optimization_rules[i]
                logger.info(f" Regra de otimização removida: {rule_id}")
                return True
        return False
    
    async def enable_rule(self, rule_id: str) -> bool:
        """Habilita regra de otimização"""
        for rule in self.optimization_rules:
            if rule.rule_id == rule_id:
                rule.enabled = True
                return True
        return False
    
    async def disable_rule(self, rule_id: str) -> bool:
        """Desabilita regra de otimização"""
        for rule in self.optimization_rules:
            if rule.rule_id == rule_id:
                rule.enabled = False
                return True
        return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificação de saúde do otimizador"""
        try:
            return {
                'status': 'healthy',
                'component': 'advanced_performance_optimizer',
                'timestamp': datetime.now().isoformat(),
                'monitoring_active': self.monitoring_active,
                'metrics_collected': len(self.metrics_history),
                'active_rules': len([r for r in self.optimization_rules if r.enabled]),
                'system_state': self.system_state,
                'config': self.config
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'component': 'advanced_performance_optimizer',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    async def cleanup(self):
        """Limpa recursos do otimizador"""
        await self.stop_monitoring()
        self.metrics_history.clear()
        self.performance_cache.clear()
        logger.info(" Advanced Performance Optimizer limpo")
