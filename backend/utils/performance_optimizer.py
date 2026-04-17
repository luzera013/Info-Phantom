"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - Performance Optimizer
Otimização extrema de performance com cache, concorrência e recursos
"""

import asyncio
import time
import psutil
import gc
import threading
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import functools
import logging
from collections import defaultdict, deque
import weakref

from .logger import setup_logger
from .metrics import MetricsCollector

logger = setup_logger(__name__)

@dataclass
class PerformanceConfig:
    """Configuração de otimização de performance"""
    max_concurrent_requests: int = 100
    max_concurrent_scraping: int = 50
    cache_size_mb: int = 512
    enable_memory_optimization: bool = True
    enable_connection_pooling: bool = True
    enable_batch_processing: bool = True
    gc_threshold: float = 0.8  # Usar GC quando 80% da memória estiver em uso
    connection_timeout: float = 30.0
    max_retries: int = 3
    backoff_factor: float = 2.0

class PerformanceOptimizer:
    """Otimizador avançado de performance"""
    
    def __init__(self, config: Optional[PerformanceConfig] = None):
        self.config = config or PerformanceConfig()
        self.metrics = MetricsCollector()
        
        # Pools de concorrência
        self.executor_pool = ThreadPoolExecutor(
            max_workers=self.config.max_concurrent_requests,
            thread_name_prefix="perf_opt"
        )
        
        self.process_pool = ProcessPoolExecutor(
            max_workers=min(8, psutil.cpu_count()),
            mp_context=None  # Usar contexto padrão
        )
        
        # Cache de performance
        self.performance_cache = {}
        self.cache_access_times = defaultdict(list)
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Monitoramento de recursos
        self.resource_monitor = ResourceMonitor()
        self.memory_monitor = MemoryMonitor(self.config.gc_threshold)
        
        # Connection pooling
        self.connection_pools = {}
        self.session_pools = {}
        
        # Fila de tarefas otimizada
        self.task_queue = asyncio.PriorityQueue(maxsize=1000)
        self.batch_processor = BatchProcessor(self.config)
        
        # Locks granulares
        self.locks = {
            'cache': asyncio.RWLock(),
            'connections': asyncio.RWLock(),
            'metrics': asyncio.Lock(),
            'resources': asyncio.Lock()
        }
        
        logger.info("🚀 Performance Optimizer inicializado")
    
    async def initialize(self):
        """Inicializa otimizações de performance"""
        logger.info("🔧 Inicializando otimizações de performance...")
        
        # Iniciar monitoramento de recursos
        await self.resource_monitor.start()
        await self.memory_monitor.start()
        
        # Configurar garbage collection otimizado
        gc.set_threshold(700, 10, 10)
        gc.set_debug(gc.DEBUG_STATS)
        
        # Pré-aquecer pools
        await self._warm_up_pools()
        
        logger.info("✅ Otimizações de performance inicializadas")
    
    async def _warm_up_pools(self):
        """Pré-aquece pools de conexões"""
        logger.info("🔥 Pré-aquecendo pools de conexões...")
        
        # Criar conexões iniciais para evitar cold starts
        warmup_tasks = []
        
        # Pool HTTP
        for i in range(5):
            task = self._create_warmup_connection(f"warmup_http_{i}")
            warmup_tasks.append(task)
        
        # Pool de scraping
        for i in range(3):
            task = self._create_warmup_connection(f"warmup_scrape_{i}")
            warmup_tasks.append(task)
        
        await asyncio.gather(*warmup_tasks, return_exceptions=True)
        logger.info("🌡️ Pools pré-aquecidos")
    
    async def _create_warmup_connection(self, name: str):
        """Cria conexão de warmup"""
        try:
            # Simular criação de sessão/conexão
            await asyncio.sleep(0.1)
            logger.debug(f"Conexão {name} criada")
        except Exception as e:
            logger.debug(f"Erro warmup {name}: {str(e)}")
    
    def optimize_function(self, func: Callable) -> Callable:
        """Otimizador automático de funções"""
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                # Verificar se deve usar pool de processos
                if self._should_use_process_pool(func):
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        self.process_pool, 
                        functools.partial(func, *args, **kwargs)
                    )
                else:
                    result = await func(*args, **kwargs)
                
                # Métricas de performance
                execution_time = time.time() - start_time
                self.metrics.record_function_performance(func.__name__, execution_time)
                
                return result
                
            except Exception as e:
                self.metrics.increment_function_error(func.__name__)
                raise
        
        return wrapper
    
    def _should_use_process_pool(self, func: Callable) -> bool:
        """Decide se deve usar pool de processos"""
        # Funções CPU-intensive devem usar process pool
        cpu_intensive_patterns = [
            'parse', 'extract', 'analyze', 'process', 'compute',
            'calculate', 'transform', 'encode', 'decode'
        ]
        
        func_name = func.__name__.lower()
        return any(pattern in func_name for pattern in cpu_intensive_patterns)
    
    async def execute_with_optimization(self, func: Callable, *args, **kwargs):
        """Executa função com otimizações automáticas"""
        # Verificar cache de performance
        cache_key = self._generate_cache_key(func, args, kwargs)
        
        async with self.locks['cache']:
            if cache_key in self.performance_cache:
                self.cache_hits += 1
                return self.performance_cache[cache_key]['result']
        
        self.cache_misses += 1
        
        # Executar com monitoramento
        start_time = time.time()
        start_memory = self.memory_monitor.get_current_usage()
        
        try:
            # Escolher método de execução otimizado
            if self._should_use_process_pool(func):
                result = await self._execute_in_process_pool(func, *args, **kwargs)
            else:
                result = await self._execute_in_thread_pool(func, *args, **kwargs)
            
            # Métricas detalhadas
            execution_time = time.time() - start_time
            memory_delta = self.memory_monitor.get_current_usage() - start_memory
            
            self.metrics.record_execution_details(
                func.__name__, execution_time, memory_delta
            )
            
            # Cachear resultado se for pequeno
            if self._should_cache_result(result, execution_time):
                async with self.locks['cache']:
                    self.performance_cache[cache_key] = {
                        'result': result,
                        'timestamp': time.time(),
                        'execution_time': execution_time
                    }
            
            return result
            
        except Exception as e:
            self.metrics.increment_function_error(func.__name__)
            raise
    
    async def _execute_in_process_pool(self, func: Callable, *args, **kwargs):
        """Executa função no pool de processos"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.process_pool,
            functools.partial(func, *args, **kwargs)
        )
    
    async def _execute_in_thread_pool(self, func: Callable, *args, **kwargs):
        """Executa função no pool de threads"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor_pool,
            functools.partial(func, *args, **kwargs)
        )
    
    def _generate_cache_key(self, func: Callable, args: tuple, kwargs: dict) -> str:
        """Gera chave de cache otimizada"""
        import hashlib
        
        # Criar hash dos argumentos
        args_str = str(args) + str(sorted(kwargs.items()))
        func_name = func.__name__
        
        return hashlib.md5(f"{func_name}:{args_str}".encode()).hexdigest()
    
    def _should_cache_result(self, result: Any, execution_time: float) -> bool:
        """Decide se deve cachear resultado"""
        # Não cachear resultados muito grandes ou muito rápidos
        result_size = len(str(result)) if result else 0
        
        return (
            result_size < 10000 and  # Máximo 10KB
            execution_time > 0.1 and  # Mínimo 100ms
            len(self.performance_cache) < 1000  # Máximo 1000 itens
        )
    
    async def batch_process(self, items: List[Any], 
                        processor: Callable, 
                        batch_size: int = None) -> List[Any]:
        """Processa itens em lotes para performance otimizada"""
        batch_size = batch_size or self.config.max_concurrent_requests
        results = []
        
        # Dividir em lotes
        batches = [
            items[i:i + batch_size] 
            for i in range(0, len(items), batch_size)
        ]
        
        logger.info(f"📦 Processando {len(items)} itens em {len(batches)} lotes de {batch_size}")
        
        # Processar lotes em paralelo
        tasks = []
        for batch in batches:
            task = self.batch_processor.process_batch(batch, processor)
            tasks.append(task)
        
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combinar resultados
        for result in batch_results:
            if isinstance(result, Exception):
                logger.error(f"❌ Erro no lote: {str(result)}")
                continue
            
            if isinstance(result, list):
                results.extend(result)
            else:
                results.append(result)
        
        logger.info(f"✅ Processamento em lote concluído: {len(results)} resultados")
        return results
    
    async def get_connection_pool(self, pool_name: str, 
                                factory: Callable) -> 'ConnectionPool':
        """Obtém ou cria pool de conexões otimizado"""
        async with self.locks['connections']:
            if pool_name not in self.connection_pools:
                self.connection_pools[pool_name] = ConnectionPool(
                    factory, 
                    self.config.max_concurrent_requests,
                    self.config.connection_timeout
                )
                logger.info(f"🌐 Pool de conexões criado: {pool_name}")
        
        return self.connection_pools[pool_name]
    
    async def get_cached_session(self, session_type: str = 'default'):
        """Obtém sessão HTTP cachada e otimizada"""
        async with self.locks['cache']:
            if session_type not in self.session_pools:
                # Criar pool de sessões otimizadas
                self.session_pools[session_type] = OptimizedSessionPool(
                    session_type,
                    self.config
                )
                logger.info(f"🌐 Pool de sessões criado: {session_type}")
        
        return await self.session_pools[session_type].get_session()
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas detalhadas de performance"""
        cache_hit_rate = (
            self.cache_hits / (self.cache_hits + self.cache_misses) * 100
            if (self.cache_hits + self.cache_misses) > 0 else 0
        )
        
        return {
            'cache_performance': {
                'hit_rate': cache_hit_rate,
                'hits': self.cache_hits,
                'misses': self.cache_misses,
                'size': len(self.performance_cache)
            },
            'resource_usage': self.resource_monitor.get_stats(),
            'memory_usage': self.memory_monitor.get_stats(),
            'pool_stats': {
                'thread_pool_size': self.executor_pool._max_workers,
                'process_pool_size': self.process_pool._max_workers,
                'active_connections': sum(
                    len(pool.connections) for pool in self.connection_pools.values()
                )
            },
            'optimization_stats': self.metrics.get_optimization_stats()
        }
    
    async def cleanup(self):
        """Limpa recursos de otimização"""
        logger.info("🧹 Limpando recursos de otimização...")
        
        # Parar monitoramento
        await self.resource_monitor.stop()
        await self.memory_monitor.stop()
        
        # Limpar pools
        self.executor_pool.shutdown(wait=True)
        self.process_pool.shutdown(wait=True)
        
        # Limpar caches
        self.performance_cache.clear()
        self.connection_pools.clear()
        self.session_pools.clear()
        
        # Forçar garbage collection
        gc.collect()
        
        logger.info("✅ Recursos de otimização limpos")

class ConnectionPool:
    """Pool de conexões otimizado"""
    
    def __init__(self, factory: Callable, max_size: int, timeout: float):
        self.factory = factory
        self.max_size = max_size
        self.timeout = timeout
        self.connections = deque(maxlen=max_size)
        self.active_connections = 0
        self.lock = asyncio.Lock()
    
    async def get_connection(self):
        """Obtém conexão do pool"""
        async with self.lock:
            if self.connections:
                connection = self.connections.popleft()
                self.active_connections += 1
                return connection
            
            # Criar nova conexão se não houver disponível
            if self.active_connections < self.max_size:
                connection = await self.factory()
                self.active_connections += 1
                return connection
            
            raise Exception("Pool de conexões esgotado")
    
    async def return_connection(self, connection):
        """Retorna conexão ao pool"""
        async with self.lock:
            self.active_connections -= 1
            self.connections.append(connection)

class OptimizedSessionPool:
    """Pool de sessões HTTP otimizado"""
    
    def __init__(self, session_type: str, config: PerformanceConfig):
        self.session_type = session_type
        self.config = config
        self.sessions = asyncio.Queue(maxsize=config.max_concurrent_requests)
        self.created_sessions = 0
        self.lock = asyncio.Lock()
    
    async def get_session(self):
        """Obtém sessão otimizada"""
        async with self.lock:
            if not self.sessions.empty():
                return await self.sessions.get()
            
            if self.created_sessions < self.config.max_concurrent_requests:
                # Criar nova sessão otimizada
                import aiohttp
                
                session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=self.config.connection_timeout),
                    connector=aiohttp.TCPConnector(
                        limit=self.config.max_concurrent_requests,
                        limit_per_host=20,
                        ttl_dns_cache=300,
                        use_dns_cache=True,
                        family=0,  # AF_UNSPEC
                    ),
                    headers={
                        'User-Agent': 'OMNISCIENT_PERF_OPT/3.0',
                        'Connection': 'keep-alive',
                        'Keep-Alive': 'timeout=30, max=100'
                    }
                )
                
                self.created_sessions += 1
                return session
            
            raise Exception("Pool de sessões esgotado")

class BatchProcessor:
    """Processador de lotes otimizado"""
    
    def __init__(self, config: PerformanceConfig):
        self.config = config
    
    async def process_batch(self, batch: List[Any], processor: Callable) -> List[Any]:
        """Processa lote com otimizações"""
        if not batch:
            return []
        
        # Usar processamento paralelo dentro do lote
        if len(batch) > 10:
            # Dividir lote grande em sub-lotes
            sub_batch_size = max(5, len(batch) // 4)
            sub_batches = [
                batch[i:i + sub_batch_size] 
                for i in range(0, len(batch), sub_batch_size)
            ]
            
            tasks = [
                self._process_sub_batch(sub_batch, processor) 
                for sub_batch in sub_batches
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combinar resultados
            final_results = []
            for result in results:
                if isinstance(result, Exception):
                    continue
                if isinstance(result, list):
                    final_results.extend(result)
                else:
                    final_results.append(result)
            
            return final_results
        else:
            # Processar lote pequeno diretamente
            return await processor(batch)
    
    async def _process_sub_batch(self, sub_batch: List[Any], processor: Callable) -> List[Any]:
        """Processa sub-lote"""
        try:
            return await processor(sub_batch)
        except Exception as e:
            logger.error(f"❌ Erro processando sub-lote: {str(e)}")
            return []

class ResourceMonitor:
    """Monitor de recursos do sistema"""
    
    def __init__(self):
        self.monitoring = False
        self.stats = {
            'cpu_usage': [],
            'memory_usage': [],
            'disk_usage': [],
            'network_io': []
        }
        self.start_time = None
    
    async def start(self):
        """Inicia monitoramento"""
        self.monitoring = True
        self.start_time = time.time()
        
        # Iniciar monitoramento em background
        asyncio.create_task(self._monitor_loop())
        logger.info("📊 Monitoramento de recursos iniciado")
    
    async def stop(self):
        """Para monitoramento"""
        self.monitoring = False
        logger.info("📊 Monitoramento de recursos parado")
    
    async def _monitor_loop(self):
        """Loop de monitoramento"""
        while self.monitoring:
            try:
                # CPU
                cpu_percent = psutil.cpu_percent(interval=1)
                self.stats['cpu_usage'].append(cpu_percent)
                
                # Memória
                memory = psutil.virtual_memory()
                self.stats['memory_usage'].append(memory.percent)
                
                # Disco
                disk = psutil.disk_usage('/')
                self.stats['disk_usage'].append(disk.percent)
                
                # Manter apenas últimas 100 medições
                for key in self.stats:
                    if len(self.stats[key]) > 100:
                        self.stats[key] = self.stats[key][-100:]
                
                await asyncio.sleep(5)  # Monitorar a cada 5 segundos
                
            except Exception as e:
                logger.error(f"❌ Erro monitoramento: {str(e)}")
                await asyncio.sleep(10)
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de recursos"""
        if not self.stats['cpu_usage']:
            return {}
        
        return {
            'cpu': {
                'current': self.stats['cpu_usage'][-1] if self.stats['cpu_usage'] else 0,
                'average': sum(self.stats['cpu_usage']) / len(self.stats['cpu_usage']),
                'max': max(self.stats['cpu_usage'])
            },
            'memory': {
                'current': self.stats['memory_usage'][-1] if self.stats['memory_usage'] else 0,
                'average': sum(self.stats['memory_usage']) / len(self.stats['memory_usage']),
                'max': max(self.stats['memory_usage'])
            },
            'disk': {
                'current': self.stats['disk_usage'][-1] if self.stats['disk_usage'] else 0,
                'average': sum(self.stats['disk_usage']) / len(self.stats['disk_usage']),
                'max': max(self.stats['disk_usage'])
            },
            'uptime': time.time() - self.start_time if self.start_time else 0
        }

class MemoryMonitor:
    """Monitor avançado de memória com GC otimizado"""
    
    def __init__(self, gc_threshold: float = 0.8):
        self.gc_threshold = gc_threshold
        self.monitoring = False
        self.memory_history = deque(maxlen=100)
        self.gc_stats = {
            'collections': 0,
            'collected_objects': 0,
            'uncollectable_objects': 0
        }
    
    async def start(self):
        """Inicia monitoramento de memória"""
        self.monitoring = True
        asyncio.create_task(self._memory_monitor_loop())
        logger.info("🧠 Monitoramento de memória iniciado")
    
    async def stop(self):
        """Para monitoramento de memória"""
        self.monitoring = False
        logger.info("🧠 Monitoramento de memória parado")
    
    def get_current_usage(self) -> float:
        """Retorna uso atual de memória"""
        memory = psutil.virtual_memory()
        self.memory_history.append(memory.percent)
        return memory.percent
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de memória"""
        if not self.memory_history:
            return {}
        
        return {
            'current': self.memory_history[-1] if self.memory_history else 0,
            'average': sum(self.memory_history) / len(self.memory_history),
            'max': max(self.memory_history),
            'min': min(self.memory_history),
            'gc_stats': self.gc_stats,
            'history_size': len(self.memory_history)
        }
    
    async def _memory_monitor_loop(self):
        """Loop de monitoramento de memória com GC otimizado"""
        while self.monitoring:
            try:
                memory = psutil.virtual_memory()
                self.memory_history.append(memory.percent)
                
                # Trigger GC otimizado se necessário
                if memory.percent / 100 > self.gc_threshold:
                    await self._optimized_gc()
                
                await asyncio.sleep(2)  # Monitorar a cada 2 segundos
                
            except Exception as e:
                logger.error(f"❌ Erro monitoramento memória: {str(e)}")
                await asyncio.sleep(5)
    
    async def _optimized_gc(self):
        """Executa garbage collection otimizado"""
        start_time = time.time()
        
        # Coletar estatísticas antes
        gc.collect()
        
        # Calcular objetos coletados
        stats = gc.get_stats()
        self.gc_stats['collections'] += 1
        self.gc_stats['collected_objects'] += stats.get('collected', 0)
        self.gc_stats['uncollectable_objects'] += stats.get('uncollectable', 0)
        
        gc_time = time.time() - start_time
        logger.info(f"🗑️ GC otimizado executado em {gc_time:.3f}s")
