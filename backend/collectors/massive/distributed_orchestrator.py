"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - Distributed Orchestrator
Sistema de orquestração distribuída para 100 coletores de dados
"""

import asyncio
import json
import time
import hashlib
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging
from enum import Enum
import uuid

from .massive_collector_factory import MassiveCollectorFactory, MassiveSearchRequest, MassiveSearchResult
from .collector_registry import CollectorCategory
from .base_collector import CollectorRequest, CollectorResult
from ..utils.logger import setup_logger
from ..utils.metrics import MetricsCollector
from ..utils.ttl_cache import TTLCache

logger = setup_logger(__name__)
metrics = MetricsCollector()

class OrchestrationMode(Enum):
    """Modos de orquestração"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    ADAPTIVE = "adaptive"
    PRIORITY_BASED = "priority_based"
    LOAD_BALANCED = "load_balanced"

class TaskStatus(Enum):
    """Status das tarefas"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class OrchestrationTask:
    """Tarefa de orquestração"""
    task_id: str
    request: MassiveSearchRequest
    status: TaskStatus = TaskStatus.PENDING
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    assigned_collectors: List[str] = field(default_factory=list)
    results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    priority: int = 1
    retry_count: int = 0
    max_retries: int = 3
    timeout: int = 60

@dataclass
class WorkerNode:
    """Nó de trabalho distribuído"""
    node_id: str
    host: str
    port: int
    status: str = "active"
    current_load: int = 0
    max_capacity: int = 10
    supported_categories: Set[CollectorCategory] = field(default_factory=set)
    last_heartbeat: float = field(default_factory=time.time)
    total_tasks_processed: int = 0
    average_processing_time: float = 0.0
    error_rate: float = 0.0

class DistributedOrchestrator:
    """Orquestrador distribuído para 100 coletores"""
    
    def __init__(self, factory: MassiveCollectorFactory):
        self.factory = factory
        self.mode = OrchestrationMode.ADAPTIVE
        self.tasks: Dict[str, OrchestrationTask] = {}
        self.task_queue: deque = deque()
        self.worker_nodes: Dict[str, WorkerNode] = {}
        self.active_tasks: Dict[str, OrchestrationTask] = {}
        self.completed_tasks: Dict[str, OrchestrationTask] = {}
        self.failed_tasks: Dict[str, OrchestrationTask] = {}
        
        # Cache para resultados
        self.result_cache = TTLCache(ttl=7200)  # 2 horas
        
        # Configurações
        self.config = {
            'max_concurrent_tasks': 50,
            'task_timeout': 300,  # 5 minutos
            'heartbeat_interval': 30,  # 30 segundos
            'load_balancing_enabled': True,
            'auto_scaling_enabled': True,
            'retry_enabled': True,
            'caching_enabled': True,
            'metrics_enabled': True,
            'health_check_interval': 60,  # 1 minuto
            'dead_task_cleanup_interval': 300,  # 5 minutos
            'max_queue_size': 1000
        }
        
        # Estatísticas
        self.stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'active_tasks': 0,
            'queued_tasks': 0,
            'average_task_duration': 0.0,
            'total_processing_time': 0.0,
            'cache_hit_rate': 0.0,
            'worker_utilization': 0.0,
            'category_performance': defaultdict(dict),
            'node_performance': defaultdict(dict)
        }
        
        # Controle
        self.is_running = False
        self.orchestration_loop_task = None
        self.health_check_task = None
        self.cleanup_task = None
        
        logger.info(" Distributed Orchestrator inicializado")
    
    async def initialize(self):
        """Inicializa o orquestrador distribuído"""
        if self.is_running:
            return
        
        logger.info(" Inicializando Distributed Orchestrator...")
        
        try:
            # Iniciar loop de orquestração
            await self._start_orchestration_loop()
            
            # Iniciar health checks
            await self._start_health_checks()
            
            # Iniciar cleanup
            await self._start_cleanup_task()
            
            self.is_running = True
            logger.info(" Distributed Orchestrator inicializado com sucesso")
            
        except Exception as e:
            logger.error(f" Falha na inicialização do orquestrador: {str(e)}")
            raise
    
    async def _start_orchestration_loop(self):
        """Inicia o loop principal de orquestração"""
        self.orchestration_loop_task = asyncio.create_task(self._orchestration_loop())
        logger.info(" Loop de orquestração iniciado")
    
    async def _orchestration_loop(self):
        """Loop principal de orquestração"""
        while self.is_running:
            try:
                # Processar fila de tarefas
                await self._process_task_queue()
                
                # Monitorar tarefas ativas
                await self._monitor_active_tasks()
                
                # Balancear carga se habilitado
                if self.config['load_balancing_enabled']:
                    await self._balance_load()
                
                # Auto-scaling se habilitado
                if self.config['auto_scaling_enabled']:
                    await self._auto_scale()
                
                # Aguardar próximo ciclo
                await asyncio.sleep(1.0)
                
            except Exception as e:
                logger.error(f" Erro no loop de orquestração: {str(e)}")
                await asyncio.sleep(5.0)
    
    async def _process_task_queue(self):
        """Processa a fila de tarefas"""
        while (self.task_queue and 
               len(self.active_tasks) < self.config['max_concurrent_tasks']):
            
            task = self.task_queue.popleft()
            
            # Verificar se a tarefa ainda é válida
            if task.status == TaskStatus.PENDING:
                await self._execute_task(task)
    
    async def _execute_task(self, task: OrchestrationTask):
        """Executa uma tarefa"""
        try:
            # Marcar como em execução
            task.status = TaskStatus.RUNNING
            task.started_at = time.time()
            self.active_tasks[task.task_id] = task
            
            logger.info(f" Executando tarefa {task.task_id}")
            
            # Selecionar coletores baseado no modo
            if self.mode == OrchestrationMode.SEQUENTIAL:
                await self._execute_sequential(task)
            elif self.mode == OrchestrationMode.PARALLEL:
                await self._execute_parallel(task)
            elif self.mode == OrchestrationMode.ADAPTIVE:
                await self._execute_adaptive(task)
            elif self.mode == OrchestrationMode.PRIORITY_BASED:
                await self._execute_priority_based(task)
            elif self.mode == OrchestrationMode.LOAD_BALANCED:
                await self._execute_load_balanced(task)
            
            # Marcar como concluída
            task.status = TaskStatus.COMPLETED
            task.completed_at = time.time()
            
            # Mover para completed
            self.completed_tasks[task.task_id] = task
            self.active_tasks.pop(task.task_id, None)
            
            # Atualizar estatísticas
            self._update_task_stats(task)
            
            logger.info(f" Tarefa {task.task_id} concluída em {task.completed_at - task.started_at:.2f}s")
            
        except Exception as e:
            # Marcar como falha
            task.status = TaskStatus.FAILED
            task.errors.append(str(e))
            task.completed_at = time.time()
            
            # Tentar retry se habilitado
            if self.config['retry_enabled'] and task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.PENDING
                self.task_queue.append(task)
                logger.warning(f" Tarefa {task.task_id} falhou, tentando retry {task.retry_count}/{task.max_retries}")
            else:
                # Mover para failed
                self.failed_tasks[task.task_id] = task
                self.active_tasks.pop(task.task_id, None)
                logger.error(f" Tarefa {task.task_id} falhou permanentemente: {str(e)}")
    
    async def _execute_sequential(self, task: OrchestrationTask):
        """Executa tarefa sequencialmente"""
        # Obter coletores sequencialmente
        collectors = await self._get_collectors_for_task(task)
        
        for collector_id in collectors:
            try:
                result = await self._execute_collector_task(collector_id, task.request)
                task.results[collector_id] = result
                task.assigned_collectors.append(collector_id)
                
            except Exception as e:
                task.errors.append(f"{collector_id}: {str(e)}")
                logger.warning(f" Erro no coletor {collector_id}: {str(e)}")
    
    async def _execute_parallel(self, task: OrchestrationTask):
        """Executa tarefa em paralelo"""
        collectors = await self._get_collectors_for_task(task)
        
        # Criar tarefas paralelas
        parallel_tasks = []
        for collector_id in collectors:
            parallel_task = asyncio.create_task(
                self._execute_collector_task_safe(collector_id, task)
            )
            parallel_tasks.append(parallel_task)
        
        # Aguardar conclusão
        results = await asyncio.gather(*parallel_tasks, return_exceptions=True)
        
        # Processar resultados
        for i, result in enumerate(results):
            collector_id = collectors[i]
            if isinstance(result, Exception):
                task.errors.append(f"{collector_id}: {str(result)}")
            else:
                task.results[collector_id] = result
                task.assigned_collectors.append(collector_id)
    
    async def _execute_adaptive(self, task: OrchestrationTask):
        """Executa tarefa de forma adaptativa"""
        # Análise adaptativa baseada na carga e performance
        collectors = await self._get_collectors_for_task(task)
        
        # Ordenar coletores por performance
        sorted_collectors = await self._sort_collectors_by_performance(collectors)
        
        # Executar em lotes adaptativos
        batch_size = min(len(sorted_collectors), 10)  # Lote inicial
        executed_count = 0
        
        while executed_count < len(sorted_collectors):
            # Selecionar lote
            batch = sorted_collectors[executed_count:executed_count + batch_size]
            
            # Executar lote em paralelo
            batch_tasks = []
            for collector_id in batch:
                batch_task = asyncio.create_task(
                    self._execute_collector_task_safe(collector_id, task)
                )
                batch_tasks.append(batch_task)
            
            # Aguardar lote
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Processar resultados do lote
            batch_success = 0
            for i, result in enumerate(batch_results):
                collector_id = batch[i]
                if isinstance(result, Exception):
                    task.errors.append(f"{collector_id}: {str(result)}")
                else:
                    task.results[collector_id] = result
                    task.assigned_collectors.append(collector_id)
                    batch_success += 1
            
            # Ajustar tamanho do próximo lote baseado no sucesso
            if batch_success / len(batch) > 0.8:
                batch_size = min(batch_size + 2, 20)  # Aumentar lote
            elif batch_success / len(batch) < 0.5:
                batch_size = max(batch_size - 1, 5)  # Reduzir lote
            
            executed_count += len(batch)
    
    async def _execute_priority_based(self, task: OrchestrationTask):
        """Executa tarefa baseada em prioridade"""
        collectors = await self._get_collectors_for_task(task)
        
        # Ordenar por prioridade do coletor
        priority_collectors = await self._sort_collectors_by_priority(collectors)
        
        # Executar em paralelo com limites por prioridade
        high_priority = [c for c in priority_collectors if self._get_collector_priority(c) >= 8]
        medium_priority = [c for c in priority_collectors if 5 <= self._get_collector_priority(c) < 8]
        low_priority = [c for c in priority_collectors if self._get_collector_priority(c) < 5]
        
        # Executar alta prioridade primeiro
        if high_priority:
            await self._execute_collector_batch(high_priority, task)
        
        # Depois média prioridade
        if medium_priority:
            await self._execute_collector_batch(medium_priority, task)
        
        # Por fim baixa prioridade
        if low_priority:
            await self._execute_collector_batch(low_priority, task)
    
    async def _execute_load_balanced(self, task: OrchestrationTask):
        """Executa tarefa com balanceamento de carga"""
        collectors = await self._get_collectors_for_task(task)
        
        # Distribuir coletores entre nós disponíveis
        if self.worker_nodes:
            node_assignments = await self._distribute_collectors_to_nodes(collectors)
            
            # Executar em cada nó
            for node_id, node_collectors in node_assignments.items():
                await self._execute_on_node(node_id, node_collectors, task)
        else:
            # Se não há nós distribuídos, executar localmente
            await self._execute_parallel(task)
    
    async def _execute_collector_task_safe(self, collector_id: str, request: MassiveSearchRequest):
        """Executa tarefa de coletor com tratamento seguro"""
        try:
            return await self._execute_collector_task(collector_id, request)
        except Exception as e:
            logger.error(f" Erro executando coletor {collector_id}: {str(e)}")
            raise
    
    async def _execute_collector_task(self, collector_id: str, request: MassiveSearchRequest) -> Any:
        """Executa tarefa específica de coletor"""
        # Verificar cache
        if self.config['caching_enabled']:
            cache_key = f"{collector_id}:{hashlib.md5(str(request).encode()).hexdigest()}"
            cached_result = await self.result_cache.get(cache_key)
            if cached_result:
                return cached_result
        
        # Executar coletor
        result = await self.factory.collectors[collector_id].instance.execute_request(
            CollectorRequest(
                request_id=f"{request.request_id}_{collector_id}",
                query=request.query,
                limit=request.max_results_per_collector,
                filters=request.filters,
                priority=request.priority
            )
        )
        
        # Salvar em cache
        if self.config['caching_enabled'] and result.success:
            cache_key = f"{collector_id}:{hashlib.md5(str(request).encode()).hexdigest()}"
            await self.result_cache.set(cache_key, result)
        
        return result
    
    async def _execute_collector_batch(self, collectors: List[str], task: OrchestrationTask):
        """Executa lote de coletores"""
        batch_tasks = []
        for collector_id in collectors:
            batch_task = asyncio.create_task(
                self._execute_collector_task_safe(collector_id, task.request)
            )
            batch_tasks.append(batch_task)
        
        results = await asyncio.gather(*batch_tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            collector_id = collectors[i]
            if isinstance(result, Exception):
                task.errors.append(f"{collector_id}: {str(result)}")
            else:
                task.results[collector_id] = result
                task.assigned_collectors.append(collector_id)
    
    async def _get_collectors_for_task(self, task: OrchestrationTask) -> List[str]:
        """Obtém coletores para a tarefa"""
        selected_collectors = []
        
        # Se coletores específicos foram solicitados
        if task.request.specific_collectors:
            for collector_id in task.request.specific_collectors:
                if collector_id in self.factory.collectors:
                    instance = self.factory.collectors[collector_id]
                    if instance.status.value == "ready" and instance.health_score > 0.5:
                        selected_collectors.append(collector_id)
        
        # Se categorias foram especificadas
        elif task.request.categories:
            for category in task.request.categories:
                category_collectors = [
                    cid for cid, instance in self.factory.collectors.items()
                    if (instance.instance and 
                        instance.instance.metadata.category == category and
                        instance.status.value == "ready" and
                        instance.health_score > 0.5)
                ]
                selected_collectors.extend(category_collectors)
        
        # Seleção automática
        else:
            ready_collectors = [
                cid for cid, instance in self.factory.collectors.items()
                if (instance.status.value == "ready" and 
                    instance.health_score > 0.5)
            ]
            
            # Ordenar por saúde
            ready_collectors.sort(
                key=lambda cid: self.factory.collectors[cid].health_score,
                reverse=True
            )
            
            selected_collectors = ready_collectors[:task.request.max_collectors]
        
        return selected_collectors
    
    async def _sort_collectors_by_performance(self, collectors: List[str]) -> List[str]:
        """Ordena coletores por performance"""
        def get_performance_score(collector_id):
            instance = self.factory.collectors[collector_id]
            return (
                instance.health_score * 0.4 +
                (1.0 - min(instance.error_count / max(1, instance.total_requests), 1.0)) * 0.3 +
                (1.0 - min(instance.average_response_time / 10.0, 1.0)) * 0.3
            )
        
        return sorted(collectors, key=get_performance_score, reverse=True)
    
    async def _sort_collectors_by_priority(self, collectors: List[str]) -> List[str]:
        """Ordena coletores por prioridade"""
        return sorted(collectors, key=self._get_collector_priority, reverse=True)
    
    def _get_collector_priority(self, collector_id: str) -> int:
        """Obtém prioridade do coletor"""
        instance = self.factory.collectors[collector_id]
        if instance.instance:
            return instance.instance.metadata.priority
        return 1
    
    async def _distribute_collectors_to_nodes(self, collectors: List[str]) -> Dict[str, List[str]]:
        """Distribui coletores entre nós"""
        node_assignments = defaultdict(list)
        
        # Ordenar nós por carga
        sorted_nodes = sorted(
            self.worker_nodes.values(),
            key=lambda node: node.current_load / node.max_capacity
        )
        
        # Distribuir coletores
        for i, collector_id in enumerate(collectors):
            node = sorted_nodes[i % len(sorted_nodes)]
            node_assignments[node.node_id].append(collector_id)
        
        return dict(node_assignments)
    
    async def _execute_on_node(self, node_id: str, collectors: List[str], task: OrchestrationTask):
        """Executa coletores em um nó específico"""
        # Simulação de execução distribuída
        # Em produção, aqui seria feita a comunicação real com o nó
        
        for collector_id in collectors:
            try:
                result = await self._execute_collector_task(collector_id, task.request)
                task.results[collector_id] = result
                task.assigned_collectors.append(collector_id)
                
                # Atualizar estatísticas do nó
                if node_id in self.worker_nodes:
                    node = self.worker_nodes[node_id]
                    node.total_tasks_processed += 1
                    
            except Exception as e:
                task.errors.append(f"{collector_id} (node {node_id}): {str(e)}")
    
    async def _monitor_active_tasks(self):
        """Monitora tarefas ativas"""
        current_time = time.time()
        timeout = self.config['task_timeout']
        
        for task_id, task in list(self.active_tasks.items()):
            # Verificar timeout
            if task.started_at and (current_time - task.started_at) > timeout:
                logger.warning(f" Tarefa {task_id} excedeu timeout")
                task.status = TaskStatus.FAILED
                task.errors.append("Task timeout")
                task.completed_at = current_time
                
                # Mover para failed
                self.failed_tasks[task_id] = task
                self.active_tasks.pop(task_id, None)
    
    async def _balance_load(self):
        """Balanceia carga entre coletores"""
        # Implementação básica de balanceamento
        overloaded_collectors = []
        underloaded_collectors = []
        
        for collector_id, instance in self.factory.collectors.items():
            if instance.status.value == "ready":
                load_factor = instance.usage_count / max(1, instance.total_requests)
                if load_factor > 0.8:
                    overloaded_collectors.append(collector_id)
                elif load_factor < 0.3:
                    underloaded_collectors.append(collector_id)
        
        # Ajustar prioridades baseado na carga
        if overloaded_collectors and underloaded_collectors:
            logger.info(f" Balanceando carga: {len(overloaded_collectors)} sobrecarregados, {len(underloaded_collectores)} subutilizados")
    
    async def _auto_scale(self):
        """Auto-scaling baseado na demanda"""
        queue_size = len(self.task_queue)
        active_size = len(self.active_tasks)
        
        # Se fila muito grande, aumentar limite
        if queue_size > 50 and active_size < self.config['max_concurrent_tasks']:
            self.config['max_concurrent_tasks'] = min(
                self.config['max_concurrent_tasks'] + 5,
                100
            )
            logger.info(f" Auto-scaling: aumentado max_concurrent_tasks para {self.config['max_concurrent_tasks']}")
        
        # Se fila vazia, reduzir limite
        elif queue_size == 0 and active_size < 10:
            self.config['max_concurrent_tasks'] = max(
                self.config['max_concurrent_tasks'] - 2,
                10
            )
            logger.info(f" Auto-scaling: reduzido max_concurrent_tasks para {self.config['max_concurrent_tasks']}")
    
    def _update_task_stats(self, task: OrchestrationTask):
        """Atualiza estatísticas de tarefas"""
        self.stats['total_tasks'] += 1
        
        if task.status == TaskStatus.COMPLETED:
            self.stats['completed_tasks'] += 1
        elif task.status == TaskStatus.FAILED:
            self.stats['failed_tasks'] += 1
        
        # Atualizar tempo médio
        if task.started_at and task.completed_at:
            duration = task.completed_at - task.started_at
            total_time = self.stats['total_processing_time']
            completed_count = self.stats['completed_tasks']
            
            self.stats['total_processing_time'] += duration
            self.stats['average_task_duration'] = total_time / max(1, completed_count)
        
        # Atualizar contadores atuais
        self.stats['active_tasks'] = len(self.active_tasks)
        self.stats['queued_tasks'] = len(self.task_queue)
    
    async def _start_health_checks(self):
        """Inicia health checks"""
        self.health_check_task = asyncio.create_task(self._health_check_loop())
        logger.info(" Health checks iniciados")
    
    async def _health_check_loop(self):
        """Loop de health checks"""
        while self.is_running:
            try:
                await asyncio.sleep(self.config['health_check_interval'])
                await self._perform_health_checks()
            except Exception as e:
                logger.error(f" Erro no health check: {str(e)}")
    
    async def _perform_health_checks(self):
        """Executa health checks"""
        # Verificar nós workers
        current_time = time.time()
        dead_nodes = []
        
        for node_id, node in self.worker_nodes.items():
            if current_time - node.last_heartbeat > self.config['heartbeat_interval'] * 3:
                dead_nodes.append(node_id)
        
        # Remover nós mortos
        for node_id in dead_nodes:
            logger.warning(f" Nó {node_id} considerado morto")
            del self.worker_nodes[node_id]
    
    async def _start_cleanup_task(self):
        """Inicia tarefa de cleanup"""
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info(" Cleanup task iniciado")
    
    async def _cleanup_loop(self):
        """Loop de cleanup"""
        while self.is_running:
            try:
                await asyncio.sleep(self.config['dead_task_cleanup_interval'])
                await self._cleanup_dead_tasks()
            except Exception as e:
                logger.error(f" Erro no cleanup: {str(e)}")
    
    async def _cleanup_dead_tasks(self):
        """Limpa tarefas mortas"""
        current_time = time.time()
        cleanup_threshold = 3600  # 1 hora
        
        # Limpar completed tasks antigos
        old_completed = [
            task_id for task_id, task in self.completed_tasks.items()
            if task.completed_at and (current_time - task.completed_at) > cleanup_threshold
        ]
        
        for task_id in old_completed:
            del self.completed_tasks[task_id]
        
        # Limpar failed tasks antigos
        old_failed = [
            task_id for task_id, task in self.failed_tasks.items()
            if task.completed_at and (current_time - task.completed_at) > cleanup_threshold
        ]
        
        for task_id in old_failed:
            del self.failed_tasks[task_id]
        
        if old_completed or old_failed:
            logger.info(f" Cleanup: removidas {len(old_completed)} completed e {len(old_failed)} failed tasks")
    
    async def submit_task(self, request: MassiveSearchRequest) -> str:
        """Submete tarefa para orquestração"""
        task_id = str(uuid.uuid4())
        
        task = OrchestrationTask(
            task_id=task_id,
            request=request,
            priority=request.priority,
            timeout=request.timeout
        )
        
        # Adicionar à fila
        self.task_queue.append(task)
        self.tasks[task_id] = task
        
        logger.info(f" Tarefa {task_id} submetida para orquestração")
        return task_id
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Obtém status de tarefa"""
        if task_id not in self.tasks:
            return None
        
        task = self.tasks[task_id]
        
        return {
            'task_id': task.task_id,
            'status': task.status.value,
            'created_at': task.created_at,
            'started_at': task.started_at,
            'completed_at': task.completed_at,
            'assigned_collectors': task.assigned_collectors,
            'results_count': len(task.results),
            'errors_count': len(task.errors),
            'priority': task.priority,
            'retry_count': task.retry_count,
            'max_retries': task.max_retries
        }
    
    async def get_task_result(self, task_id: str) -> Optional[MassiveSearchResult]:
        """Obtém resultado de tarefa"""
        if task_id not in self.completed_tasks:
            return None
        
        task = self.completed_tasks[task_id]
        
        # Criar resultado massivo
        massive_result = MassiveSearchResult(
            request_id=task.task_id,
            total_collectors_used=len(task.assigned_collectors),
            successful_collectors=len([r for r in task.results.values() if hasattr(r, 'success') and r.success]),
            failed_collectors=len(task.errors),
            total_results=sum(
                len(r.data) if isinstance(r.data, list) else 1
                for r in task.results.values()
                if hasattr(r, 'success') and r.success
            ),
            processing_time=task.completed_at - task.started_at if task.started_at and task.completed_at else 0,
            results=task.results,
            errors=task.errors
        )
        
        return massive_result
    
    async def get_orchestrator_status(self) -> Dict[str, Any]:
        """Obtém status do orquestrador"""
        return {
            'is_running': self.is_running,
            'mode': self.mode.value,
            'total_tasks': self.stats['total_tasks'],
            'completed_tasks': self.stats['completed_tasks'],
            'failed_tasks': self.stats['failed_tasks'],
            'active_tasks': self.stats['active_tasks'],
            'queued_tasks': self.stats['queued_tasks'],
            'average_task_duration': self.stats['average_task_duration'],
            'worker_nodes': len(self.worker_nodes),
            'config': self.config,
            'factory_status': await self.factory.get_factory_status()
        }
    
    async def register_worker_node(self, node: WorkerNode):
        """Registra nó worker"""
        self.worker_nodes[node.node_id] = node
        logger.info(f" Nó worker {node.node_id} registrado")
    
    async def unregister_worker_node(self, node_id: str):
        """Remove nó worker"""
        if node_id in self.worker_nodes:
            del self.worker_nodes[node_id]
            logger.info(f" Nó worker {node_id} removido")
    
    async def set_mode(self, mode: OrchestrationMode):
        """Define modo de orquestração"""
        self.mode = mode
        logger.info(f" Modo de orquestração alterado para {mode.value}")
    
    async def cleanup(self):
        """Limpa recursos do orquestrador"""
        logger.info(" Limpando Distributed Orchestrator...")
        
        self.is_running = False
        
        # Cancelar tarefas
        if self.orchestration_loop_task:
            self.orchestration_loop_task.cancel()
        
        if self.health_check_task:
            self.health_check_task.cancel()
        
        if self.cleanup_task:
            self.cleanup_task.cancel()
        
        # Limpar caches
        self.result_cache.clear()
        
        # Limpar estruturas
        self.tasks.clear()
        self.task_queue.clear()
        self.active_tasks.clear()
        self.completed_tasks.clear()
        self.failed_tasks.clear()
        self.worker_nodes.clear()
        
        logger.info(" Distributed Orchestrator limpo")
