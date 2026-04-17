"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - Worker Utilities
Utilitários para processamento assíncrono e workers
"""

import asyncio
import time
import logging
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from enum import Enum
import queue
import threading
from datetime import datetime
import psutil
import gc

from .logger import setup_logger

logger = setup_logger(__name__)

class TaskStatus(Enum):
    """Status das tarefas"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class Task:
    """Tarefa para processamento"""
    id: str
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    priority: int = 0
    timeout: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[Exception] = None
    worker_id: Optional[str] = None

@dataclass
class WorkerStats:
    """Estatísticas do worker"""
    worker_id: str
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_execution_time: float = 0.0
    average_execution_time: float = 0.0
    current_task: Optional[str] = None
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    last_activity: float = field(default_factory=time.time)

class BaseWorker:
    """Worker base para processamento de tarefas"""
    
    def __init__(self, worker_id: str, max_concurrent_tasks: int = 1):
        self.worker_id = worker_id
        self.max_concurrent_tasks = max_concurrent_tasks
        self.is_running = False
        self.current_tasks: Dict[str, Task] = {}
        self.task_queue = asyncio.PriorityQueue()
        self.stats = WorkerStats(worker_id=worker_id)
        self.process = psutil.Process()
        
        logger.info(f"🔧 Worker {worker_id} inicializado (max_tasks: {max_concurrent_tasks})")
    
    async def start(self):
        """Inicia o worker"""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info(f"🚀 Worker {self.worker_id} iniciado")
        
        # Criar tasks para processamento concorrente
        tasks = [
            asyncio.create_task(self._process_tasks())
            for _ in range(self.max_concurrent_tasks)
        ]
        
        # Task para atualizar estatísticas
        stats_task = asyncio.create_task(self._update_stats())
        
        try:
            await asyncio.gather(*tasks, stats_task)
        except asyncio.CancelledError:
            logger.info(f"🛑 Worker {self.worker_id} parado")
        finally:
            self.is_running = False
    
    async def stop(self):
        """Para o worker"""
        self.is_running = False
        
        # Cancelar tarefas em execução
        for task in self.current_tasks.values():
            task.status = TaskStatus.CANCELLED
        
        logger.info(f"🛑 Worker {self.worker_id} parado")
    
    async def submit_task(self, task: Task) -> bool:
        """
        Submete tarefa para processamento
        
        Args:
            task: Tarefa para processar
            
        Returns:
            True se submetida com sucesso
        """
        if not self.is_running:
            return False
        
        # Usar prioridade negativa para que maior prioridade venha primeiro
        await self.task_queue.put((-task.priority, task))
        
        logger.debug(f"📤 Tarefa {task.id} submetida para worker {self.worker_id}")
        return True
    
    async def get_task_status(self, task_id: str) -> Optional[Task]:
        """
        Obtém status de tarefa
        
        Args:
            task_id: ID da tarefa
            
        Returns:
            Tarefa ou None
        """
        # Verificar tarefas em execução
        if task_id in self.current_tasks:
            return self.current_tasks[task_id]
        
        return None
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancela tarefa
        
        Args:
            task_id: ID da tarefa
            
        Returns:
            True se cancelada com sucesso
        """
        if task_id in self.current_tasks:
            task = self.current_tasks[task_id]
            task.status = TaskStatus.CANCELLED
            logger.info(f"🚫 Tarefa {task_id} cancelada")
            return True
        
        return False
    
    async def _process_tasks(self):
        """Processa tarefas da fila"""
        while self.is_running:
            try:
                # Obter próxima tarefa
                _, task = await asyncio.wait_for(
                    self.task_queue.get(),
                    timeout=1.0
                )
                
                # Verificar se worker ainda está rodando
                if not self.is_running:
                    self.task_queue.put((task.priority, task))
                    break
                
                # Adicionar às tarefas em execução
                self.current_tasks[task.id] = task
                task.status = TaskStatus.RUNNING
                task.started_at = time.time()
                task.worker_id = self.worker_id
                self.stats.current_task = task.id
                
                logger.debug(f"🔄 Processando tarefa {task.id} no worker {self.worker_id}")
                
                # Executar tarefa
                try:
                    if task.timeout:
                        result = await asyncio.wait_for(
                            self._execute_task(task),
                            timeout=task.timeout
                        )
                    else:
                        result = await self._execute_task(task)
                    
                    task.result = result
                    task.status = TaskStatus.COMPLETED
                    self.stats.tasks_completed += 1
                    
                    logger.debug(f"✅ Tarefa {task.id} concluída")
                    
                except asyncio.TimeoutError:
                    task.error = Exception(f"Timeout após {task.timeout}s")
                    task.status = TaskStatus.FAILED
                    self.stats.tasks_failed += 1
                    logger.warning(f"⏰ Tarefa {task.id} falhou por timeout")
                    
                except Exception as e:
                    task.error = e
                    task.status = TaskStatus.FAILED
                    self.stats.tasks_failed += 1
                    logger.error(f"❌ Tarefa {task.id} falhou: {str(e)}")
                    
                    # Tentar retry se configurado
                    if task.retry_count < task.max_retries:
                        task.retry_count += 1
                        task.status = TaskStatus.PENDING
                        task.error = None
                        
                        # Adicionar de volta à fila com menor prioridade
                        await self.task_queue.put((-task.priority + 1, task))
                        logger.info(f"🔄 Tarefa {task.id} agendada para retry ({task.retry_count}/{task.max_retries})")
                
                finally:
                    task.completed_at = time.time()
                    execution_time = task.completed_at - task.started_at
                    
                    # Atualizar estatísticas
                    self.stats.total_execution_time += execution_time
                    self.stats.average_execution_time = (
                        self.stats.total_execution_time / 
                        (self.stats.tasks_completed + self.stats.tasks_failed)
                    )
                    
                    # Remover das tarefas em execução
                    del self.current_tasks[task.id]
                    self.stats.current_task = None
                    self.stats.last_activity = time.time()
                    
            except asyncio.TimeoutError:
                # Timeout normal para verificar se worker ainda deve rodar
                continue
            except Exception as e:
                logger.error(f"❌ Erro processando tarefa: {str(e)}")
                continue
    
    async def _execute_task(self, task: Task) -> Any:
        """
        Executa tarefa específica
        
        Args:
            task: Tarefa para executar
            
        Returns:
            Resultado da tarefa
        """
        # Verificar se é função assíncrona
        if asyncio.iscoroutinefunction(task.func):
            return await task.func(*task.args, **task.kwargs)
        else:
            # Executar em thread pool para não bloquear
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, task.func, *task.args, **task.kwargs
            )
    
    async def _update_stats(self):
        """Atualiza estatísticas do worker"""
        while self.is_running:
            try:
                # Obter uso de CPU e memória
                self.stats.cpu_usage = self.process.cpu_percent()
                self.stats.memory_usage = self.process.memory_info().rss / 1024 / 1024  # MB
                
                # Limpar garbage collector
                if len(self.current_tasks) == 0:
                    gc.collect()
                
                await asyncio.sleep(5)  # Atualizar a cada 5 segundos
                
            except Exception as e:
                logger.error(f"❌ Erro atualizando estatísticas: {str(e)}")
                await asyncio.sleep(5)
    
    def get_stats(self) -> WorkerStats:
        """Obtém estatísticas do worker"""
        return self.stats

class ThreadPoolWorker(BaseWorker):
    """Worker usando ThreadPoolExecutor"""
    
    def __init__(self, worker_id: str, max_workers: int = 4):
        super().__init__(worker_id, max_workers)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        logger.info(f"🧵 ThreadPoolWorker {worker_id} criado (workers: {max_workers})")
    
    async def _execute_task(self, task: Task) -> Any:
        """Executa tarefa em thread pool"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, task.func, *task.args, **task.kwargs
        )
    
    async def stop(self):
        """Para o worker e executor"""
        await super().stop()
        self.executor.shutdown(wait=True)
        logger.info(f"🧵 ThreadPoolWorker {self.worker_id} parado")

class ProcessPoolWorker(BaseWorker):
    """Worker usando ProcessPoolExecutor"""
    
    def __init__(self, worker_id: str, max_processes: int = 2):
        super().__init__(worker_id, max_processes)
        self.executor = ProcessPoolExecutor(max_processes=max_processes)
        
        logger.info(f"⚙️ ProcessPoolWorker {worker_id} criado (processes: {max_processes})")
    
    async def _execute_task(self, task: Task) -> Any:
        """Executa tarefa em process pool"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, task.func, *task.args, **task.kwargs
        )
    
    async def stop(self):
        """Para o worker e executor"""
        await super().stop()
        self.executor.shutdown(wait=True)
        logger.info(f"⚙️ ProcessPoolWorker {self.worker_id} parado")

class WorkerManager:
    """Gerenciador de múltiplos workers"""
    
    def __init__(self):
        self.workers: Dict[str, BaseWorker] = {}
        self.task_registry: Dict[str, Task] = {}
        self.is_running = False
        
        logger.info("👷 Worker Manager inicializado")
    
    async def start(self):
        """Inicia todos os workers"""
        if self.is_running:
            return
        
        self.is_running = True
        
        # Iniciar workers
        for worker in self.workers.values():
            asyncio.create_task(worker.start())
        
        logger.info("🚀 Worker Manager iniciado")
    
    async def stop(self):
        """Para todos os workers"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Parar workers
        stop_tasks = [worker.stop() for worker in self.workers.values()]
        await asyncio.gather(*stop_tasks)
        
        logger.info("🛑 Worker Manager parado")
    
    def add_worker(self, worker: BaseWorker):
        """
        Adiciona worker ao gerenciador
        
        Args:
            worker: Worker para adicionar
        """
        self.workers[worker.worker_id] = worker
        logger.info(f"➕ Worker {worker.worker_id} adicionado")
    
    def remove_worker(self, worker_id: str):
        """
        Remove worker do gerenciador
        
        Args:
            worker_id: ID do worker
        """
        if worker_id in self.workers:
            worker = self.workers[worker_id]
            asyncio.create_task(worker.stop())
            del self.workers[worker_id]
            logger.info(f"➖ Worker {worker_id} removido")
    
    async def submit_task(self, task: Task, worker_id: Optional[str] = None) -> bool:
        """
        Submete tarefa para processamento
        
        Args:
            task: Tarefa para processar
            worker_id: Worker específico (opcional)
            
        Returns:
            True se submetida com sucesso
        """
        # Registrar tarefa
        self.task_registry[task.id] = task
        
        # Escolher worker
        if worker_id and worker_id in self.workers:
            return await self.workers[worker_id].submit_task(task)
        
        # Escolher worker com menos tarefas
        best_worker = self._get_best_worker()
        
        if best_worker:
            return await best_worker.submit_task(task)
        
        return False
    
    async def get_task_status(self, task_id: str) -> Optional[Task]:
        """
        Obtém status de tarefa
        
        Args:
            task_id: ID da tarefa
            
        Returns:
            Tarefa ou None
        """
        # Verificar no registro
        if task_id in self.task_registry:
            return self.task_registry[task_id]
        
        # Verificar nos workers
        for worker in self.workers.values():
            task = await worker.get_task_status(task_id)
            if task:
                return task
        
        return None
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancela tarefa
        
        Args:
            task_id: ID da tarefa
            
        Returns:
            True se cancelada com sucesso
        """
        # Tentar cancelar em todos os workers
        for worker in self.workers.values():
            if await worker.cancel_task(task_id):
                return True
        
        return False
    
    def _get_best_worker(self) -> Optional[BaseWorker]:
        """
        Escolhe melhor worker disponível
        
        Returns:
            Worker com menos carga
        """
        if not self.workers:
            return None
        
        best_worker = None
        min_tasks = float('inf')
        
        for worker in self.workers.values():
            if not worker.is_running:
                continue
            
            current_tasks = len(worker.current_tasks)
            if current_tasks < min_tasks:
                min_tasks = current_tasks
                best_worker = worker
        
        return best_worker
    
    def get_all_stats(self) -> Dict[str, WorkerStats]:
        """
        Obtém estatísticas de todos os workers
        
        Returns:
            Dicionário com estatísticas
        """
        stats = {}
        
        for worker_id, worker in self.workers.items():
            stats[worker_id] = worker.get_stats()
        
        return stats
    
    def get_system_stats(self) -> Dict[str, Any]:
        """
        Obtém estatísticas do sistema
        
        Returns:
            Estatísticas do sistema
        """
        total_tasks = len(self.task_registry)
        completed_tasks = sum(
            1 for task in self.task_registry.values()
            if task.status == TaskStatus.COMPLETED
        )
        failed_tasks = sum(
            1 for task in self.task_registry.values()
            if task.status == TaskStatus.FAILED
        )
        running_tasks = sum(
            1 for task in self.task_registry.values()
            if task.status == TaskStatus.RUNNING
        )
        
        return {
            'total_workers': len(self.workers),
            'active_workers': sum(
                1 for w in self.workers.values() if w.is_running
            ),
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'failed_tasks': failed_tasks,
            'running_tasks': running_tasks,
            'success_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            'system_cpu': psutil.cpu_percent(),
            'system_memory': psutil.virtual_memory().percent
        }

# Funções utilitárias
async def create_task(func: Callable, *args, **kwargs) -> Task:
    """
    Cria nova tarefa
    
    Args:
        func: Função para executar
        *args: Argumentos posicionais
        **kwargs: Argumentos nomeados
        
    Returns:
        Tarefa criada
    """
    task_id = f"task_{int(time.time() * 1000)}_{hash(func.__name__) % 10000}"
    
    return Task(
        id=task_id,
        func=func,
        args=args,
        kwargs=kwargs
    )

async def run_with_timeout(func: Callable, timeout: float, *args, **kwargs) -> Any:
    """
    Executa função com timeout
    
    Args:
        func: Função para executar
        timeout: Timeout em segundos
        *args: Argumentos posicionais
        **kwargs: Argumentos nomeados
        
    Returns:
        Resultado da função
        
    Raises:
        asyncio.TimeoutError: Se timeout
    """
    try:
        if asyncio.iscoroutinefunction(func):
            return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
        else:
            loop = asyncio.get_event_loop()
            return await asyncio.wait_for(
                loop.run_in_executor(None, func, *args, **kwargs),
                timeout=timeout
            )
    except asyncio.TimeoutError:
        logger.error(f"⏰ Função {func.__name__} falhou por timeout ({timeout}s)")
        raise

async def batch_process(items: List[Any], func: Callable, 
                       batch_size: int = 10, max_workers: int = 4) -> List[Any]:
    """
    Processa itens em lote usando workers
    
    Args:
        items: Itens para processar
        func: Função de processamento
        batch_size: Tamanho do lote
        max_workers: Máximo de workers
        
    Returns:
        Resultados do processamento
    """
    logger.info(f"🔄 Processando {len(items)} itens em lotes de {batch_size}")
    
    # Criar worker manager
    manager = WorkerManager()
    
    # Adicionar worker
    worker = ThreadPoolWorker("batch_worker", max_workers)
    manager.add_worker(worker)
    
    # Iniciar workers
    await manager.start()
    
    try:
        # Criar tarefas
        tasks = []
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            
            async def process_batch(batch_items):
                return [func(item) for item in batch_items]
            
            task = await create_task(process_batch, batch)
            tasks.append(task)
        
        # Submeter tarefas
        submitted_tasks = []
        for task in tasks:
            await manager.submit_task(task)
            submitted_tasks.append(task)
        
        # Aguardar conclusão
        results = []
        for task in submitted_tasks:
            while task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
                await asyncio.sleep(0.1)
            
            if task.status == TaskStatus.COMPLETED:
                results.extend(task.result)
            else:
                logger.error(f"❌ Tarefa {task.id} falhou: {task.error}")
        
        await manager.stop()
        logger.info(f"✅ Processamento concluído: {len(results)} resultados")
        return results
        
    except Exception as e:
        await manager.stop()
        logger.error(f"❌ Erro no processamento em lote: {str(e)}")
        raise

# Instância global do manager (em produção, seria injetada)
worker_manager = WorkerManager()

async def get_worker_manager() -> WorkerManager:
    """Obtém instância do worker manager"""
    return worker_manager

async def initialize_workers():
    """Inicializa workers padrão"""
    # Adicionar workers padrão
    cpu_worker = ThreadPoolWorker("cpu_worker", max_workers=4)
    io_worker = ThreadPoolWorker("io_worker", max_workers=8)
    
    worker_manager.add_worker(cpu_worker)
    worker_manager.add_worker(io_worker)
    
    await worker_manager.start()
    logger.info("🚀 Workers padrão inicializados")
