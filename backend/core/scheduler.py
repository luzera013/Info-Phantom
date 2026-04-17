"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - Task Scheduler
Agenda e executa tarefas automáticas
"""

import asyncio
from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging

from utils.logger import setup_logger
from utils.metrics import MetricsCollector

logger = setup_logger(__name__)
metrics = MetricsCollector()

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskType(Enum):
    SEARCH = "search"
    SCRAPE = "scrape"
    ANALYZE = "analyze"
    CLEANUP = "cleanup"
    HEALTH_CHECK = "health_check"

@dataclass
class ScheduledTask:
    """Tarefa agendada"""
    id: str
    task_type: TaskType
    execute_at: datetime
    params: Dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            'id': self.id,
            'task_type': self.task_type.value,
            'execute_at': self.execute_at.isoformat(),
            'params': self.params,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'result': self.result,
            'error': self.error,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries
        }

class TaskScheduler:
    """Agendador de tarefas"""
    
    def __init__(self):
        self.tasks: Dict[str, ScheduledTask] = {}
        self.task_handlers: Dict[TaskType, Callable] = {}
        self.is_running = False
        self.scheduler_task = None
        self.cleanup_interval = 3600  # 1 hora
        
        logger.info("⏰ Task Scheduler inicializado")
    
    async def initialize(self):
        """Inicializa o scheduler"""
        logger.info("🔧 Inicializando Task Scheduler...")
        
        # Registrar handlers padrão
        await self._register_default_handlers()
        
        logger.info("✅ Task Scheduler pronto")
    
    async def _register_default_handlers(self):
        """Regera handlers para tarefas padrão"""
        # Aqui registraremos os handlers quando implementarmos
        # Por enquanto, usamos handlers genéricos
        self.task_handlers[TaskType.HEALTH_CHECK] = self._handle_health_check
        self.task_handlers[TaskType.CLEANUP] = self._handle_cleanup
        self.task_handlers[TaskType.SEARCH] = self._handle_search
        self.task_handlers[TaskType.SCRAPE] = self._handle_scrape
        self.task_handlers[TaskType.ANALYZE] = self._handle_analyze
    
    async def start_scheduled_tasks(self):
        """Inicia o loop de execução de tarefas agendadas"""
        if self.is_running:
            logger.warning("⚠️ Scheduler já está rodando")
            return
        
        self.is_running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        
        logger.info("🚀 Scheduler iniciado")
    
    async def stop(self):
        """Para o scheduler"""
        self.is_running = False
        
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        
        logger.info("🛑 Scheduler parado")
    
    async def schedule_task(self, task_type: TaskType, execute_at: datetime, 
                          params: Dict[str, Any], max_retries: int = 3) -> str:
        """
        Agenda uma nova tarefa
        
        Args:
            task_type: Tipo da tarefa
            execute_at: Quando executar
            params: Parâmetros da tarefa
            max_retries: Máximo de tentativas
            
        Returns:
            ID da tarefa criada
        """
        task_id = f"{task_type.value}_{datetime.now().timestamp()}"
        
        task = ScheduledTask(
            id=task_id,
            task_type=task_type,
            execute_at=execute_at,
            params=params,
            max_retries=max_retries
        )
        
        self.tasks[task_id] = task
        
        logger.info(f"📅 Tarefa agendada: {task_id} para {execute_at}")
        metrics.increment_scheduled_tasks()
        
        return task_id
    
    async def schedule_immediate(self, task_type: TaskType, params: Dict[str, Any], 
                               max_retries: int = 3) -> str:
        """Agenda tarefa para execução imediata"""
        return await self.schedule_task(
            task_type=task_type,
            execute_at=datetime.now(),
            params=params,
            max_retries=max_retries
        )
    
    async def schedule_recurring(self, task_type: TaskType, interval: timedelta,
                               params: Dict[str, Any], max_executions: int = None):
        """
        Agenda tarefa recorrente
        
        Args:
            task_type: Tipo da tarefa
            interval: Intervalo entre execuções
            params: Parâmetros da tarefa
            max_executions: Máximo de execuções (None = infinito)
        """
        execution_count = 0
        next_execution = datetime.now()
        
        while self.is_running and (max_executions is None or execution_count < max_executions):
            await self.schedule_task(task_type, next_execution, params.copy())
            
            next_execution = datetime.now() + interval
            execution_count += 1
            
            # Esperar até próxima execução
            await asyncio.sleep(interval.total_seconds())
    
    async def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """Retorna tarefa por ID"""
        return self.tasks.get(task_id)
    
    async def get_tasks(self, status: Optional[TaskStatus] = None, 
                       task_type: Optional[TaskType] = None) -> List[ScheduledTask]:
        """Retorna lista de tarefas filtradas"""
        tasks = list(self.tasks.values())
        
        if status:
            tasks = [t for t in tasks if t.status == status]
        
        if task_type:
            tasks = [t for t in tasks if t.task_type == task_type]
        
        return sorted(tasks, key=lambda x: x.created_at, reverse=True)
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancela uma tarefa"""
        task = self.tasks.get(task_id)
        if task and task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
            task.status = TaskStatus.CANCELLED
            logger.info(f"❌ Tarefa cancelada: {task_id}")
            return True
        return False
    
    async def retry_task(self, task_id: str) -> bool:
        """Retenta executar uma tarefa falha"""
        task = self.tasks.get(task_id)
        if task and task.status == TaskStatus.FAILED and task.retry_count < task.max_retries:
            task.status = TaskStatus.PENDING
            task.retry_count += 1
            task.error = None
            task.execute_at = datetime.now() + timedelta(seconds=60)  # 1 minuto depois
            
            logger.info(f"🔄 Retentando tarefa: {task_id} (tentativa {task.retry_count})")
            return True
        return False
    
    async def _scheduler_loop(self):
        """Loop principal do scheduler"""
        logger.info("🔄 Iniciando loop do scheduler")
        
        while self.is_running:
            try:
                await self._process_pending_tasks()
                await self._cleanup_completed_tasks()
                
                # Esperar um pouco antes da próxima verificação
                await asyncio.sleep(10)  # Verificar a cada 10 segundos
                
            except asyncio.CancelledError:
                logger.info("🛑 Loop do scheduler cancelado")
                break
            except Exception as e:
                logger.error(f"❌ Erro no loop do scheduler: {str(e)}")
                await asyncio.sleep(30)  # Esperar mais tempo em caso de erro
    
    async def _process_pending_tasks(self):
        """Processa tarefas pendentes"""
        now = datetime.now()
        
        for task in self.tasks.values():
            if (task.status == TaskStatus.PENDING and 
                task.execute_at <= now):
                
                await self._execute_task(task)
    
    async def _execute_task(self, task: ScheduledTask):
        """Executa uma tarefa"""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        
        logger.info(f"⚡ Executando tarefa: {task.id}")
        
        try:
            handler = self.task_handlers.get(task.task_type)
            if not handler:
                raise ValueError(f"Handler não encontrado para {task.task_type}")
            
            # Executar handler
            result = await handler(task.params)
            
            task.result = result
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            
            logger.info(f"✅ Tarefa concluída: {task.id}")
            metrics.increment_completed_tasks()
            
        except Exception as e:
            task.error = str(e)
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            
            logger.error(f"❌ Falha na tarefa {task.id}: {str(e)}")
            metrics.increment_failed_tasks()
            
            # Tentar novamente se possível
            if task.retry_count < task.max_retries:
                await self.retry_task(task.id)
    
    async def _cleanup_completed_tasks(self):
        """Limpa tarefas antigas"""
        cutoff_time = datetime.now() - timedelta(seconds=self.cleanup_interval)
        
        tasks_to_remove = []
        for task_id, task in self.tasks.items():
            if (task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED] and
                task.completed_at and task.completed_at < cutoff_time):
                tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            del self.tasks[task_id]
        
        if tasks_to_remove:
            logger.info(f"🧹 Limpadas {len(tasks_to_remove)} tarefas antigas")
    
    # Handlers padrão
    async def _handle_health_check(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler para health check"""
        return {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'params': params
        }
    
    async def _handle_cleanup(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler para cleanup"""
        # Implementar lógica de cleanup
        return {
            'status': 'completed',
            'timestamp': datetime.now().isoformat(),
            'cleaned_items': 0
        }
    
    async def _handle_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler para busca"""
        # Implementar lógica de busca
        return {
            'status': 'completed',
            'timestamp': datetime.now().isoformat(),
            'query': params.get('query', ''),
            'results': []
        }
    
    async def _handle_scrape(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler para scraping"""
        # Implementar lógica de scraping
        return {
            'status': 'completed',
            'timestamp': datetime.now().isoformat(),
            'url': params.get('url', ''),
            'extracted': {}
        }
    
    async def _handle_analyze(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler para análise"""
        # Implementar lógica de análise
        return {
            'status': 'completed',
            'timestamp': datetime.now().isoformat(),
            'analysis': {}
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificação de saúde do scheduler"""
        return {
            'status': 'healthy' if self.is_running else 'stopped',
            'timestamp': datetime.now().isoformat(),
            'total_tasks': len(self.tasks),
            'pending_tasks': len([t for t in self.tasks.values() if t.status == TaskStatus.PENDING]),
            'running_tasks': len([t for t in self.tasks.values() if t.status == TaskStatus.RUNNING]),
            'completed_tasks': len([t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED]),
            'failed_tasks': len([t for t in self.tasks.values() if t.status == TaskStatus.FAILED])
        }
