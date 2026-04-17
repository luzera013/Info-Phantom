"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - Base Collector
Classe base para todos os 100 coletores de dados
"""

import asyncio
import time
import json
import hashlib
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime
import logging
from enum import Enum

from .collector_registry import CollectorMetadata, CollectorCategory, CollectorStatus
from ..utils.logger import setup_logger
from ..utils.metrics import MetricsCollector
from ..utils.ttl_cache import TTLCache

logger = setup_logger(__name__)
metrics = MetricsCollector()

class CollectorType(Enum):
    """Tipos de coletores"""
    SYNCHRONOUS = "synchronous"
    ASYNCHRONOUS = "asynchronous"
    BATCH = "batch"
    STREAMING = "streaming"

class DataType(Enum):
    """Tipos de dados suportados"""
    TEXT = "text"
    JSON = "json"
    HTML = "html"
    XML = "xml"
    CSV = "csv"
    BINARY = "binary"
    STRUCTURED = "structured"
    UNSTRUCTURED = "unstructured"

@dataclass
class CollectorConfig:
    """Configuração base para coletores"""
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    rate_limit: Optional[int] = None
    cache_enabled: bool = True
    cache_ttl: int = 3600
    proxy_enabled: bool = False
    proxy_list: List[str] = field(default_factory=list)
    user_agent: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    authentication: Dict[str, Any] = field(default_factory=dict)
    custom_params: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CollectorRequest:
    """Requisição para coletor"""
    request_id: str
    query: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    filters: Dict[str, Any] = field(default_factory=dict)
    limit: Optional[int] = None
    offset: int = 0
    data_types: List[DataType] = field(default_factory=list)
    priority: int = 1
    callback: Optional[Callable] = None

@dataclass
class CollectorResult:
    """Resultado do coletor"""
    request_id: str
    collector_id: str
    success: bool
    data: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    processing_time: float = 0.0
    items_count: int = 0
    data_size: int = 0
    timestamp: float = field(default_factory=time.time)
    cache_hit: bool = False

@dataclass
class CollectorStats:
    """Estatísticas do coletor"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    total_processing_time: float = 0.0
    average_processing_time: float = 0.0
    total_data_size: int = 0
    last_request_time: float = 0.0
    error_rate: float = 0.0
    uptime_percentage: float = 100.0

class BaseCollector(ABC):
    """Classe base abstrata para todos os coletores"""
    
    def __init__(self, collector_id: str, metadata: CollectorMetadata, config: Optional[CollectorConfig] = None):
        self.collector_id = collector_id
        self.metadata = metadata
        self.config = config or CollectorConfig()
        self.stats = CollectorStats()
        self.cache = TTLCache(ttl=self.config.cache_ttl) if self.config.cache_enabled else None
        self.is_initialized = False
        self.is_healthy = True
        
        # Rate limiting
        self._rate_limiter = None
        if self.config.rate_limit:
            self._rate_limiter = asyncio.Semaphore(self.config.rate_limit)
        
        logger.info(f" Coletor base inicializado: {collector_id}")
    
    async def initialize(self):
        """Inicializa o coletor"""
        if self.is_initialized:
            return
        
        try:
            await self._setup_collector()
            self.is_initialized = True
            logger.info(f" Coletor {self.collector_id} inicializado com sucesso")
        except Exception as e:
            logger.error(f" Falha ao inicializar coletor {self.collector_id}: {str(e)}")
            self.is_healthy = False
            raise
    
    @abstractmethod
    async def _setup_collector(self):
        """Setup específico do coletor (deve ser implementado)"""
        pass
    
    @abstractmethod
    async def collect_data(self, request: CollectorRequest) -> CollectorResult:
        """Coleta dados (deve ser implementado)"""
        pass
    
    async def execute_request(self, request: CollectorRequest) -> CollectorResult:
        """Executa requisição com tratamento robusto"""
        start_time = time.time()
        self.stats.total_requests += 1
        self.stats.last_request_time = start_time
        
        try:
            # Verificar se coletor está saudável
            if not self.is_healthy:
                raise Exception(f"Coletor {self.collector_id} não está saudável")
            
            # Verificar cache
            cache_key = None
            if self.cache:
                cache_key = self._generate_cache_key(request)
                cached_result = await self.cache.get(cache_key)
                if cached_result:
                    cached_result.cache_hit = True
                    self.stats.cache_hits += 1
                    logger.debug(f" Cache hit para {self.collector_id}")
                    return cached_result
                self.stats.cache_misses += 1
            
            # Rate limiting
            if self._rate_limiter:
                await self._rate_limiter.acquire()
            
            # Executar coleta
            result = await self.collect_data(request)
            
            # Salvar em cache
            if self.cache and result.success and cache_key:
                await self.cache.set(cache_key, result)
            
            # Atualizar estatísticas
            processing_time = time.time() - start_time
            self._update_stats(result, processing_time)
            
            logger.debug(f" Requisição {request.request_id} concluída em {processing_time:.2f}s")
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.stats.failed_requests += 1
            self.stats.error_rate = self.stats.failed_requests / max(1, self.stats.total_requests)
            
            error_result = CollectorResult(
                request_id=request.request_id,
                collector_id=self.collector_id,
                success=False,
                data=None,
                error=str(e),
                processing_time=processing_time
            )
            
            logger.error(f" Erro na requisição {request.request_id}: {str(e)}")
            return error_result
    
    def _generate_cache_key(self, request: CollectorRequest) -> str:
        """Gera chave de cache para requisição"""
        key_data = {
            'collector_id': self.collector_id,
            'query': request.query,
            'parameters': request.parameters,
            'filters': request.filters,
            'limit': request.limit,
            'offset': request.offset
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _update_stats(self, result: CollectorResult, processing_time: float):
        """Atualiza estatísticas do coletor"""
        if result.success:
            self.stats.successful_requests += 1
            self.stats.total_processing_time += processing_time
            self.stats.total_data_size += result.data_size
            
            # Calcular média de tempo de processamento
            if self.stats.successful_requests > 0:
                self.stats.average_processing_time = (
                    self.stats.total_processing_time / self.stats.successful_requests
                )
            
            # Calcular taxa de erro
            self.stats.error_rate = self.stats.failed_requests / max(1, self.stats.total_requests)
            
            # Calcular uptime
            total_time = time.time() - (self.stats.last_request_time - processing_time)
            error_time = self.stats.failed_requests * 10  # Estimativa de 10s por erro
            self.stats.uptime_percentage = max(0, (total_time - error_time) / total_time * 100)
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificação de saúde do coletor"""
        try:
            health_status = {
                'status': 'healthy' if self.is_healthy else 'unhealthy',
                'collector_id': self.collector_id,
                'initialized': self.is_initialized,
                'timestamp': datetime.now().isoformat(),
                'stats': {
                    'total_requests': self.stats.total_requests,
                    'success_rate': (
                        (self.stats.successful_requests / max(1, self.stats.total_requests)) * 100
                    ),
                    'error_rate': self.stats.error_rate,
                    'cache_hit_rate': (
                        (self.stats.cache_hits / max(1, self.stats.cache_hits + self.stats.cache_misses)) * 100
                    ),
                    'average_processing_time': self.stats.average_processing_time,
                    'uptime_percentage': self.stats.uptime_percentage
                },
                'config': {
                    'timeout': self.config.timeout,
                    'max_retries': self.config.max_retries,
                    'rate_limit': self.config.rate_limit,
                    'cache_enabled': self.config.cache_enabled
                }
            }
            
            # Teste básico de funcionalidade
            test_request = CollectorRequest(
                request_id=f"health_check_{int(time.time())}",
                query="health_check_test",
                limit=1
            )
            
            try:
                test_result = await self.collect_data(test_request)
                health_status['functional_test'] = 'passed'
            except Exception as e:
                health_status['functional_test'] = 'failed'
                health_status['functional_error'] = str(e)
            
            return health_status
            
        except Exception as e:
            return {
                'status': 'error',
                'collector_id': self.collector_id,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def batch_collect(self, requests: List[CollectorRequest]) -> List[CollectorResult]:
        """Coleta em lote"""
        logger.info(f" Executando batch collect: {len(requests)} requisições")
        
        # Ordenar por prioridade
        sorted_requests = sorted(requests, key=lambda r: r.priority, reverse=True)
        
        # Executar em paralelo com limite de concorrência
        semaphore = asyncio.Semaphore(10)  # Limite de 10 requisições simultâneas
        
        async def execute_with_semaphore(request):
            async with semaphore:
                return await self.execute_request(request)
        
        tasks = [execute_with_semaphore(req) for req in sorted_requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Processar exceções
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_result = CollectorResult(
                    request_id=sorted_requests[i].request_id,
                    collector_id=self.collector_id,
                    success=False,
                    data=None,
                    error=str(result)
                )
                processed_results.append(error_result)
            else:
                processed_results.append(result)
        
        logger.info(f" Batch collect concluído: {len(processed_results)} resultados")
        return processed_results
    
    async def stream_collect(self, request: CollectorRequest) -> Any:
        """Coleta streaming (deve ser implementado por subclasses)"""
        raise NotImplementedError("Streaming não implementado neste coletor")
    
    def get_metadata(self) -> CollectorMetadata:
        """Obtém metadados do coletor"""
        return self.metadata
    
    def get_stats(self) -> CollectorStats:
        """Obtém estatísticas do coletor"""
        return self.stats
    
    def update_config(self, config: CollectorConfig):
        """Atualiza configuração do coletor"""
        self.config = config
        
        # Recriar cache se necessário
        if config.cache_enabled and not self.cache:
            self.cache = TTLCache(ttl=config.cache_ttl)
        elif not config.cache_enabled and self.cache:
            self.cache.clear()
            self.cache = None
        
        # Recriar rate limiter se necessário
        if config.rate_limit and config.rate_limit != self.config.rate_limit:
            self._rate_limiter = asyncio.Semaphore(config.rate_limit)
        
        logger.info(f" Configuração atualizada para {self.collector_id}")
    
    async def cleanup(self):
        """Limpa recursos do coletor"""
        if self.cache:
            self.cache.clear()
        
        logger.info(f" Coletor {self.collector_id} limpo")
    
    def __str__(self) -> str:
        return f"{self.metadata.name} ({self.collector_id})"
    
    def __repr__(self) -> str:
        return f"<BaseCollector: {self.collector_id} - {self.metadata.name}>"

class SynchronousCollector(BaseCollector):
    """Coletor síncrono base"""
    
    def __init__(self, collector_id: str, metadata: CollectorMetadata, config: Optional[CollectorConfig] = None):
        super().__init__(collector_id, metadata, config)
        self.collector_type = CollectorType.SYNCHRONOUS
    
    async def collect_data(self, request: CollectorRequest) -> CollectorResult:
        """Implementação padrão para coletores síncronos"""
        start_time = time.time()
        
        try:
            # Implementação síncrona em thread separada
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, self._sync_collect, request)
            
            processing_time = time.time() - start_time
            
            return CollectorResult(
                request_id=request.request_id,
                collector_id=self.collector_id,
                success=True,
                data=data,
                processing_time=processing_time,
                items_count=self._count_items(data),
                data_size=self._calculate_data_size(data)
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            return CollectorResult(
                request_id=request.request_id,
                collector_id=self.collector_id,
                success=False,
                data=None,
                error=str(e),
                processing_time=processing_time
            )
    
    @abstractmethod
    def _sync_collect(self, request: CollectorRequest) -> Any:
        """Coleta síncrona (deve ser implementado)"""
        pass
    
    def _count_items(self, data: Any) -> int:
        """Conta itens nos dados"""
        if isinstance(data, list):
            return len(data)
        elif isinstance(data, dict):
            return 1
        else:
            return 1
    
    def _calculate_data_size(self, data: Any) -> int:
        """Calcula tamanho dos dados"""
        try:
            return len(json.dumps(data).encode())
        except:
            return len(str(data).encode())

class AsynchronousCollector(BaseCollector):
    """Coletor assíncrono base"""
    
    def __init__(self, collector_id: str, metadata: CollectorMetadata, config: Optional[CollectorConfig] = None):
        super().__init__(collector_id, metadata, config)
        self.collector_type = CollectorType.ASYNCHRONOUS
    
    @abstractmethod
    async def _async_collect(self, request: CollectorRequest) -> Any:
        """Coleta assíncrona (deve ser implementado)"""
        pass
    
    async def collect_data(self, request: CollectorRequest) -> CollectorResult:
        """Implementação padrão para coletores assíncronos"""
        start_time = time.time()
        
        try:
            data = await self._async_collect(request)
            processing_time = time.time() - start_time
            
            return CollectorResult(
                request_id=request.request_id,
                collector_id=self.collector_id,
                success=True,
                data=data,
                processing_time=processing_time,
                items_count=self._count_items(data),
                data_size=self._calculate_data_size(data)
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            return CollectorResult(
                request_id=request.request_id,
                collector_id=self.collector_id,
                success=False,
                data=None,
                error=str(e),
                processing_time=processing_time
            )
    
    def _count_items(self, data: Any) -> int:
        """Conta itens nos dados"""
        if isinstance(data, list):
            return len(data)
        elif isinstance(data, dict):
            return 1
        else:
            return 1
    
    def _calculate_data_size(self, data: Any) -> int:
        """Calcula tamanho dos dados"""
        try:
            return len(json.dumps(data).encode())
        except:
            return len(str(data).encode())

class BatchCollector(BaseCollector):
    """Coletor em lote base"""
    
    def __init__(self, collector_id: str, metadata: CollectorMetadata, config: Optional[CollectorConfig] = None):
        super().__init__(collector_id, metadata, config)
        self.collector_type = CollectorType.BATCH
    
    @abstractmethod
    async def _batch_collect(self, requests: List[CollectorRequest]) -> List[CollectorResult]:
        """Coleta em lote (deve ser implementado)"""
        pass
    
    async def collect_data(self, request: CollectorRequest) -> CollectorResult:
        """Implementação padrão para coletores em lote"""
        # Para coletores em lote, delegar para _batch_collect
        results = await self._batch_collect([request])
        return results[0] if results else CollectorResult(
            request_id=request.request_id,
            collector_id=self.collector_id,
            success=False,
            data=None,
            error="No results returned"
        )

class StreamingCollector(BaseCollector):
    """Coletor streaming base"""
    
    def __init__(self, collector_id: str, metadata: CollectorMetadata, config: Optional[CollectorConfig] = None):
        super().__init__(collector_id, metadata, config)
        self.collector_type = CollectorType.STREAMING
    
    @abstractmethod
    async def _stream_collect(self, request: CollectorRequest) -> Any:
        """Coleta streaming (deve ser implementado)"""
        pass
    
    async def collect_data(self, request: CollectorRequest) -> CollectorResult:
        """Implementação padrão para coletores streaming"""
        start_time = time.time()
        
        try:
            # Para streaming, coletar uma amostra
            data = await self._stream_collect(request)
            processing_time = time.time() - start_time
            
            return CollectorResult(
                request_id=request.request_id,
                collector_id=self.collector_id,
                success=True,
                data=data,
                processing_time=processing_time,
                items_count=self._count_items(data),
                data_size=self._calculate_data_size(data)
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            return CollectorResult(
                request_id=request.request_id,
                collector_id=self.collector_id,
                success=False,
                data=None,
                error=str(e),
                processing_time=processing_time
            )
    
    async def stream_collect(self, request: CollectorRequest) -> Any:
        """Interface pública de streaming"""
        return await self._stream_collect(request)
    
    def _count_items(self, data: Any) -> int:
        """Conta itens nos dados"""
        if isinstance(data, list):
            return len(data)
        elif isinstance(data, dict):
            return 1
        else:
            return 1
    
    def _calculate_data_size(self, data: Any) -> int:
        """Calcula tamanho dos dados"""
        try:
            return len(json.dumps(data).encode())
        except:
            return len(str(data).encode())
