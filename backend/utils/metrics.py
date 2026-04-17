"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - Metrics Collector
Coleta e gerencia métricas do sistema
"""

import time
import threading
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging

from .logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class MetricPoint:
    """Ponto de métrica"""
    timestamp: float
    value: float
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class MetricSummary:
    """Resumo de métrica"""
    count: int = 0
    sum: float = 0.0
    min: float = float('inf')
    max: float = float('-inf')
    avg: float = 0.0
    last_updated: float = field(default_factory=time.time)

class MetricsCollector:
    """Coletor de métricas do sistema"""
    
    def __init__(self, max_history: int = 10000):
        self.max_history = max_history
        self.lock = threading.RLock()
        
        # Contadores
        self.counters = defaultdict(int)
        
        # Métricas de tempo
        self.timers = defaultdict(list)
        self.timer_summaries = defaultdict(MetricSummary)
        
        # Gauges (valores atuais)
        self.gauges = defaultdict(float)
        
        # Histórico
        self.history = defaultdict(lambda: deque(maxlen=max_history))
        
        # Estatísticas do sistema
        self.system_stats = {
            'start_time': time.time(),
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'active_connections': 0,
            'total_processing_time': 0.0,
            'average_processing_time': 0.0
        }
        
        logger.info("📊 Metrics Collector inicializado")
    
    def increment_counter(self, name: str, value: int = 1, tags: Dict[str, str] = None):
        """
        Incrementa contador
        
        Args:
            name: Nome do contador
            value: Valor para incrementar
            tags: Tags adicionais
        """
        with self.lock:
            key = self._make_key(name, tags)
            self.counters[key] += value
            
            # Adicionar ao histórico
            self.history[key].append(MetricPoint(
                timestamp=time.time(),
                value=self.counters[key],
                tags=tags or {}
            ))
            
            # Atualizar estatísticas do sistema
            if name == 'search_count':
                self.system_stats['total_requests'] += value
            elif name == 'successful_searches':
                self.system_stats['successful_requests'] += value
            elif name == 'failed_searches':
                self.system_stats['failed_requests'] += value
            elif name == 'cache_hits':
                self.system_stats['cache_hits'] += value
            elif name == 'cache_misses':
                self.system_stats['cache_misses'] += value
    
    def set_gauge(self, name: str, value: float, tags: Dict[str, str] = None):
        """
        Define valor de gauge
        
        Args:
            name: Nome do gauge
            value: Valor
            tags: Tags adicionais
        """
        with self.lock:
            key = self._make_key(name, tags)
            self.gauges[key] = value
            
            # Adicionar ao histórico
            self.history[key].append(MetricPoint(
                timestamp=time.time(),
                value=value,
                tags=tags or {}
            ))
            
            # Atualizar estatísticas do sistema
            if name == 'active_connections':
                self.system_stats['active_connections'] = int(value)
    
    def record_timer(self, name: str, value: float, tags: Dict[str, str] = None):
        """
        Registra tempo de execução
        
        Args:
            name: Nome do timer
            value: Tempo em segundos
            tags: Tags adicionais
        """
        with self.lock:
            key = self._make_key(name, tags)
            self.timers[key].append(value)
            
            # Manter apenas últimos valores
            if len(self.timers[key]) > self.max_history:
                self.timers[key] = self.timers[key][-self.max_history:]
            
            # Atualizar resumo
            self._update_timer_summary(key, value)
            
            # Adicionar ao histórico
            self.history[key].append(MetricPoint(
                timestamp=time.time(),
                value=value,
                tags=tags or {}
            ))
            
            # Atualizar estatísticas do sistema
            if name == 'processing_time':
                self.system_stats['total_processing_time'] += value
                total_requests = max(1, self.system_stats['total_requests'])
                self.system_stats['average_processing_time'] = (
                    self.system_stats['total_processing_time'] / total_requests
                )
    
    def increment_search_count(self):
        """Incrementa contador de buscas"""
        self.increment_counter('search_count')
    
    def increment_successful_searches(self):
        """Incrementa contador de buscas bem-sucedidas"""
        self.increment_counter('successful_searches')
    
    def increment_failed_searches(self):
        """Incrementa contador de buscas falhas"""
        self.increment_counter('failed_searches')
    
    def increment_cache_hit(self):
        """Incrementa contador de cache hits"""
        self.increment_counter('cache_hits')
    
    def increment_cache_miss(self):
        """Incrementa contador de cache misses"""
        self.increment_counter('cache_misses')
    
    def increment_error_count(self):
        """Incrementa contador de erros"""
        self.increment_counter('error_count')
    
    def increment_scheduled_tasks(self):
        """Incrementa contador de tarefas agendadas"""
        self.increment_counter('scheduled_tasks')
    
    def increment_completed_tasks(self):
        """Incrementa contador de tarefas completadas"""
        self.increment_counter('completed_tasks')
    
    def increment_failed_tasks(self):
        """Incrementa contador de tarefas falhas"""
        self.increment_counter('failed_tasks')
    
    def get_counter(self, name: str, tags: Dict[str, str] = None) -> int:
        """
        Obtém valor do contador
        
        Args:
            name: Nome do contador
            tags: Tags adicionais
            
        Returns:
            Valor do contador
        """
        with self.lock:
            key = self._make_key(name, tags)
            return self.counters.get(key, 0)
    
    def get_gauge(self, name: str, tags: Dict[str, str] = None) -> float:
        """
        Obtém valor do gauge
        
        Args:
            name: Nome do gauge
            tags: Tags adicionais
            
        Returns:
            Valor do gauge
        """
        with self.lock:
            key = self._make_key(name, tags)
            return self.gauges.get(key, 0.0)
    
    def get_timer_stats(self, name: str, tags: Dict[str, str] = None) -> MetricSummary:
        """
        Obtém estatísticas do timer
        
        Args:
            name: Nome do timer
            tags: Tags adicionais
            
        Returns:
            Estatísticas do timer
        """
        with self.lock:
            key = self._make_key(name, tags)
            return self.timer_summaries.get(key, MetricSummary())
    
    def get_history(self, name: str, tags: Dict[str, str] = None, 
                   since: Optional[float] = None) -> list:
        """
        Obtém histórico da métrica
        
        Args:
            name: Nome da métrica
            tags: Tags adicionais
            since: Timestamp inicial (opcional)
            
        Returns:
            Lista de pontos históricos
        """
        with self.lock:
            key = self._make_key(name, tags)
            history = list(self.history[key])
            
            if since:
                history = [p for p in history if p.timestamp >= since]
            
            return history
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """
        Obtém todas as métricas
        
        Returns:
            Dicionário com todas as métricas
        """
        with self.lock:
            return {
                'counters': dict(self.counters),
                'gauges': dict(self.gauges),
                'timer_summaries': {
                    k: {
                        'count': v.count,
                        'sum': v.sum,
                        'min': v.min,
                        'max': v.max,
                        'avg': v.avg,
                        'last_updated': v.last_updated
                    }
                    for k, v in self.timer_summaries.items()
                },
                'system_stats': self.get_system_stats()
            }
    
    def get_system_stats(self) -> Dict[str, Any]:
        """
        Obtém estatísticas do sistema
        
        Returns:
            Estatísticas do sistema
        """
        uptime = time.time() - self.system_stats['start_time']
        
        return {
            **self.system_stats,
            'uptime_seconds': uptime,
            'uptime_formatted': str(timedelta(seconds=int(uptime))),
            'requests_per_second': (
                self.system_stats['total_requests'] / max(1, uptime)
            ),
            'success_rate': (
                (self.system_stats['successful_requests'] / 
                 max(1, self.system_stats['total_requests'])) * 100
            ),
            'cache_hit_rate': (
                (self.system_stats['cache_hits'] / 
                 max(1, self.system_stats['cache_hits'] + self.system_stats['cache_misses'])) * 100
            )
        }
    
    def reset_metrics(self):
        """Reseta todas as métricas"""
        with self.lock:
            self.counters.clear()
            self.timers.clear()
            self.timer_summaries.clear()
            self.gauges.clear()
            self.history.clear()
            
            # Resetar estatísticas do sistema (mantendo start_time)
            start_time = self.system_stats['start_time']
            self.system_stats = {
                'start_time': start_time,
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'cache_hits': 0,
                'cache_misses': 0,
                'active_connections': 0,
                'total_processing_time': 0.0,
                'average_processing_time': 0.0
            }
        
        logger.info("🧹 Métricas resetadas")
    
    def cleanup_old_metrics(self, max_age_seconds: int = 3600):
        """
        Limpa métricas antigas
        
        Args:
            max_age_seconds: Idade máxima das métricas
        """
        with self.lock:
            cutoff_time = time.time() - max_age_seconds
            cleaned_count = 0
            
            for key, history in self.history.items():
                original_len = len(history)
                
                # Remover pontos antigos
                while history and history[0].timestamp < cutoff_time:
                    history.popleft()
                
                cleaned_count += original_len - len(history)
            
            if cleaned_count > 0:
                logger.info(f"🧹 Limpas {cleaned_count} métricas antigas")
    
    def _make_key(self, name: str, tags: Dict[str, str] = None) -> str:
        """
        Cria chave composta para métrica
        
        Args:
            name: Nome da métrica
            tags: Tags adicionais
            
        Returns:
            Chave composta
        """
        if not tags:
            return name
        
        tag_str = ','.join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name},{tag_str}"
    
    def _update_timer_summary(self, key: str, value: float):
        """
        Atualiza resumo de timer
        
        Args:
            key: Chave do timer
            value: Valor a adicionar
        """
        if key not in self.timer_summaries:
            self.timer_summaries[key] = MetricSummary()
        
        summary = self.timer_summaries[key]
        summary.count += 1
        summary.sum += value
        summary.min = min(summary.min, value)
        summary.max = max(summary.max, value)
        summary.avg = summary.sum / summary.count
        summary.last_updated = time.time()
    
    def export_metrics(self, format: str = 'json') -> str:
        """
        Exporta métricas em formato específico
        
        Args:
            format: Formato de exportação ('json', 'prometheus')
            
        Returns:
            Métricas exportadas
        """
        metrics = self.get_all_metrics()
        
        if format == 'json':
            import json
            return json.dumps(metrics, indent=2, default=str)
        
        elif format == 'prometheus':
            lines = []
            
            # Exportar contadores
            for name, value in metrics['counters'].items():
                lines.append(f"omniscient_counter_{name} {value}")
            
            # Exportar gauges
            for name, value in metrics['gauges'].items():
                lines.append(f"omniscient_gauge_{name} {value}")
            
            # Exportar timers
            for name, summary in metrics['timer_summaries'].items():
                lines.extend([
                    f"omniscient_timer_{name}_count {summary['count']}",
                    f"omniscient_timer_{name}_sum {summary['sum']}",
                    f"omniscient_timer_{name}_avg {summary['avg']}",
                    f"omniscient_timer_{name}_min {summary['min']}",
                    f"omniscient_timer_{name}_max {summary['max']}"
                ])
            
            return '\n'.join(lines)
        
        else:
            raise ValueError(f"Formato não suportado: {format}")

# Instância global
metrics = MetricsCollector()

def get_metrics() -> MetricsCollector:
    """Obtém instância do coletor de métricas"""
    return metrics
