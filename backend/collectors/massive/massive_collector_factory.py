"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - Massive Collector Factory
Factory massivo para gerenciar 100 coletores de dados da internet
"""

import asyncio
import json
import time
import hashlib
from typing import List, Dict, Any, Optional, Type, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging
from enum import Enum

from .collector_registry import CollectorRegistry, CollectorCategory, CollectorStatus
from .base_collector import BaseCollector, CollectorRequest, CollectorResult, CollectorConfig
from .web_scraping.web_scraping_collectors import get_web_scraping_collectors
from .api_platforms.api_platforms_collectors import get_api_platforms_collectors
from .crawlers_bots.crawlers_bots_collectors import get_crawlers_bots_collectors
from .massive_platforms.massive_platforms_collectors import get_massive_platforms_collectors
from .advanced_tools.advanced_tools_collectors import get_advanced_tools_collectors
from .specialized_apis.specialized_apis_collectors import get_specialized_apis_collectors
from .collection_techniques.collection_techniques_collectors import get_collection_techniques_collectors
from .massive_databases.massive_databases_collectors import get_massive_databases_collectors
from .ai_platforms.ai_platforms_collectors import get_ai_platforms_collectors
from ..utils.logger import setup_logger
from ..utils.metrics import MetricsCollector
from ..utils.ttl_cache import TTLCache

logger = setup_logger(__name__)
metrics = MetricsCollector()

class CollectorStatus(Enum):
    """Status do coletor no factory"""
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    DISABLED = "disabled"

@dataclass
class CollectorInstance:
    """Instância de coletor no factory"""
    collector_id: str
    collector_class: Type[BaseCollector]
    instance: Optional[BaseCollector] = None
    status: CollectorStatus = CollectorStatus.INITIALIZING
    last_used: float = 0.0
    usage_count: int = 0
    error_count: int = 0
    total_requests: int = 0
    successful_requests: int = 0
    average_response_time: float = 0.0
    last_error: Optional[str] = None
    health_score: float = 1.0
    config: Optional[CollectorConfig] = None

@dataclass
class MassiveSearchRequest:
    """Requisição de busca massiva"""
    request_id: str
    query: str
    categories: List[CollectorCategory] = field(default_factory=list)
    specific_collectors: List[str] = field(default_factory=list)
    max_collectors: int = 10
    max_results_per_collector: int = 50
    timeout: int = 60
    priority: int = 1
    filters: Dict[str, Any] = field(default_factory=dict)
    merge_strategy: str = "unified"  # unified, separated, ranked

@dataclass
class MassiveSearchResult:
    """Resultado de busca massiva"""
    request_id: str
    total_collectors_used: int
    successful_collectors: int
    failed_collectors: int
    total_results: int
    processing_time: float
    results: Dict[str, Any]  # Por coletor
    unified_results: List[Dict[str, Any]] = field(default_factory=list)
    ranked_results: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class MassiveCollectorFactory:
    """Factory massivo para gerenciar 100 coletores"""
    
    def __init__(self):
        self.registry = CollectorRegistry()
        self.collectors: Dict[str, CollectorInstance] = {}
        self.active_requests: Dict[str, MassiveSearchRequest] = {}
        self.request_queue: deque = deque()
        self.cache = TTLCache(ttl=3600)  # 1 hora
        
        # Configurações
        self.config = {
            'max_concurrent_requests': 100,
            'collector_timeout': 30,
            'auto_health_check': True,
            'health_check_interval': 300,  # 5 minutos
            'auto_recovery': True,
            'load_balancing': True,
            'caching_enabled': True,
            'metrics_enabled': True,
            'max_collectors_per_request': 50,
            'default_timeout': 60
        }
        
        # Estatísticas
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_collectors_used': 0,
            'average_response_time': 0.0,
            'cache_hit_rate': 0.0,
            'active_collectors': 0,
            'healthy_collectors': 0,
            'category_usage': defaultdict(int)
        }
        
        # Controle
        self.is_initialized = False
        self.health_check_task = None
        self.request_processor_task = None
        
        logger.info(" Massive Collector Factory inicializado")
    
    async def initialize(self):
        """Inicializa o factory e todos os coletores"""
        if self.is_initialized:
            return
        
        logger.info(" Inicializando Massive Collector Factory...")
        start_time = time.time()
        
        try:
            # Registrar todos os coletores
            await self._register_all_collectors()
            
            # Inicializar coletores
            await self._initialize_collectors()
            
            # Iniciar health checks
            if self.config['auto_health_check']:
                await self._start_health_checks()
            
            # Iniciar processador de requisições
            await self._start_request_processor()
            
            self.is_initialized = True
            initialization_time = time.time() - start_time
            
            logger.info(f" Massive Collector Factory inicializado em {initialization_time:.2f}s")
            logger.info(f" {len(self.collectors)} coletores registrados")
            
            # Registrar métricas
            metrics.record_event('factory_initialization', initialization_time)
            
        except Exception as e:
            logger.error(f" Falha na inicialização do factory: {str(e)}")
            raise
    
    async def _register_all_collectors(self):
        """Registra todos os 240 coletores"""
        logger.info(" Registrando coletores...")
        
        # Web Scraping (1-30)
        web_scraping_collectors = get_web_scraping_collectors()
        for i, collector_class in enumerate(web_scraping_collectors, 1):
            collector_id = f"web_scraping_{i:02d}_{collector_class.__name__.lower()}"
            instance = CollectorInstance(
                collector_id=collector_id,
                collector_class=collector_class,
                status=CollectorStatus.INITIALIZING
            )
            self.collectors[collector_id] = instance
        
        # APIs e Plataformas (31-60)
        api_collectors = get_api_platforms_collectors()
        for i, collector_class in enumerate(api_collectors, 31):
            collector_id = f"api_platforms_{i:02d}_{collector_class.__name__.lower()}"
            instance = CollectorInstance(
                collector_id=collector_id,
                collector_class=collector_class,
                status=CollectorStatus.INITIALIZING
            )
            self.collectors[collector_id] = instance
        
        # Crawlers e Bots (61-80)
        crawler_collectors = get_crawlers_bots_collectors()
        for i, collector_class in enumerate(crawler_collectors, 61):
            collector_id = f"crawlers_bots_{i:02d}_{collector_class.__name__.lower()}"
            instance = CollectorInstance(
                collector_id=collector_id,
                collector_class=collector_class,
                status=CollectorStatus.INITIALIZING
            )
            self.collectors[collector_id] = instance
        
        # Plataformas Massivas (81-100)
        massive_collectors = get_massive_platforms_collectors()
        for i, collector_class in enumerate(massive_collectors, 81):
            collector_id = f"massive_platforms_{i:02d}_{collector_class.__name__.lower()}"
            instance = CollectorInstance(
                collector_id=collector_id,
                collector_class=collector_class,
                status=CollectorStatus.INITIALIZING
            )
            self.collectors[collector_id] = instance
        
        # Ferramentas Avançadas/Scraping Pesado (101-130)
        advanced_tools_collectors = get_advanced_tools_collectors()
        for i, collector_class in enumerate(advanced_tools_collectors, 101):
            collector_id = f"advanced_tools_{i:02d}_{collector_class.__name__.lower()}"
            instance = CollectorInstance(
                collector_id=collector_id,
                collector_class=collector_class,
                status=CollectorStatus.INITIALIZING
            )
            self.collectors[collector_id] = instance
        
        # APIs e Dados Especializados (131-160)
        specialized_apis_collectors = get_specialized_apis_collectors()
        for i, collector_class in enumerate(specialized_apis_collectors, 131):
            collector_id = f"specialized_apis_{i:02d}_{collector_class.__name__.lower()}"
            instance = CollectorInstance(
                collector_id=collector_id,
                collector_class=collector_class,
                status=CollectorStatus.INITIALIZING
            )
            self.collectors[collector_id] = instance
        
        # Técnicas e Métodos de Coleta (161-190)
        collection_techniques_collectors = get_collection_techniques_collectors()
        for i, collector_class in enumerate(collection_techniques_collectors, 161):
            collector_id = f"collection_techniques_{i:02d}_{collector_class.__name__.lower()}"
            instance = CollectorInstance(
                collector_id=collector_id,
                collector_class=collector_class,
                status=CollectorStatus.INITIALIZING
            )
            self.collectors[collector_id] = instance
        
        # Bancos de Dados e Fontes Massivas (191-220)
        massive_databases_collectors = get_massive_databases_collectors()
        for i, collector_class in enumerate(massive_databases_collectors, 191):
            collector_id = f"massive_databases_{i:02d}_{collector_class.__name__.lower()}"
            instance = CollectorInstance(
                collector_id=collector_id,
                collector_class=collector_class,
                status=CollectorStatus.INITIALIZING
            )
            self.collectors[collector_id] = instance
        
        # IA e Data Platforms (221-240)
        ai_platforms_collectors = get_ai_platforms_collectors()
        for i, collector_class in enumerate(ai_platforms_collectors, 221):
            collector_id = f"ai_platforms_{i:02d}_{collector_class.__name__.lower()}"
            instance = CollectorInstance(
                collector_id=collector_id,
                collector_class=collector_class,
                status=CollectorStatus.INITIALIZING
            )
            self.collectors[collector_id] = instance
        
        logger.info(f" Registrados {len(self.collectors)} coletores")
    
    async def _initialize_collectors(self):
        """Inicializa todos os coletores registrados"""
        logger.info(" Inicializando coletores...")
        
        initialization_tasks = []
        
        for collector_id, instance in self.collectors.items():
            task = asyncio.create_task(self._initialize_collector(instance))
            initialization_tasks.append(task)
        
        # Executar inicializações em paralelo com limite de concorrência
        semaphore = asyncio.Semaphore(10)  # Limite de 10 inicializações simultâneas
        
        async def initialize_with_semaphore(task):
            async with semaphore:
                try:
                    await task
                except Exception as e:
                    logger.error(f" Erro na inicialização: {str(e)}")
        
        await asyncio.gather(*[initialize_with_semaphore(task) for task in initialization_tasks], return_exceptions=True)
        
        # Contabilizar estatísticas
        ready_count = len([c for c in self.collectors.values() if c.status == CollectorStatus.READY])
        error_count = len([c for c in self.collectors.values() if c.status == CollectorStatus.ERROR])
        
        logger.info(f" Coletores inicializados: {ready_count} prontos, {error_count} com erro")
        self.stats['active_collectors'] = ready_count
        self.stats['healthy_collectors'] = ready_count
    
    async def _initialize_collector(self, instance: CollectorInstance):
        """Inicializa um coletor individual"""
        try:
            # Criar instância do coletor
            instance.instance = instance.collector_class(instance.config)
            
            # Inicializar coletor
            await instance.instance.initialize()
            
            # Atualizar status
            instance.status = CollectorStatus.READY
            instance.health_score = 1.0
            
            logger.debug(f" Coletor {instance.collector_id} inicializado com sucesso")
            
        except Exception as e:
            instance.status = CollectorStatus.ERROR
            instance.last_error = str(e)
            instance.health_score = 0.0
            logger.error(f" Erro inicializando coletor {instance.collector_id}: {str(e)}")
    
    async def _start_health_checks(self):
        """Inicia health checks automáticos"""
        self.health_check_task = asyncio.create_task(self._health_check_loop())
        logger.info(" Health checks automáticos iniciados")
    
    async def _health_check_loop(self):
        """Loop de health checks"""
        while True:
            try:
                await asyncio.sleep(self.config['health_check_interval'])
                await self._perform_health_checks()
            except Exception as e:
                logger.error(f" Erro no health check: {str(e)}")
    
    async def _perform_health_checks(self):
        """Executa health checks em todos os coletores"""
        healthy_count = 0
        total_checked = 0
        
        for collector_id, instance in self.collectors.items():
            if instance.status in [CollectorStatus.READY, CollectorStatus.BUSY]:
                try:
                    health_result = await instance.instance.health_check()
                    
                    if health_result.get('status') == 'healthy':
                        instance.health_score = min(1.0, instance.health_score + 0.1)
                        if instance.status == CollectorStatus.ERROR:
                            instance.status = CollectorStatus.READY
                        healthy_count += 1
                    else:
                        instance.health_score = max(0.0, instance.health_score - 0.2)
                        if instance.health_score < 0.3:
                            instance.status = CollectorStatus.ERROR
                    
                    total_checked += 1
                    
                except Exception as e:
                    instance.health_score = max(0.0, instance.health_score - 0.3)
                    instance.last_error = str(e)
                    if instance.health_score < 0.3:
                        instance.status = CollectorStatus.ERROR
                    total_checked += 1
        
        self.stats['healthy_collectors'] = healthy_count
        logger.debug(f" Health check: {healthy_count}/{total_checked} coletores saudáveis")
    
    async def _start_request_processor(self):
        """Inicia processador de requisições"""
        self.request_processor_task = asyncio.create_task(self._request_processor_loop())
        logger.info(" Processador de requisições iniciado")
    
    async def _request_processor_loop(self):
        """Loop do processador de requisições"""
        while True:
            try:
                if self.request_queue:
                    request = self.request_queue.popleft()
                    await self._process_massive_request(request)
                else:
                    await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f" Erro processando requisição: {str(e)}")
    
    async def massive_search(self, request: MassiveSearchRequest) -> MassiveSearchResult:
        """Executa busca massiva em múltiplos coletores"""
        if not self.is_initialized:
            raise RuntimeError("Factory não inicializado")
        
        start_time = time.time()
        logger.info(f" Iniciando busca massiva: {request.request_id}")
        
        # Verificar cache
        if self.config['caching_enabled']:
            cache_key = f"massive_search:{hashlib.md5(str(request).encode()).hexdigest()}"
            cached_result = await self.cache.get(cache_key)
            if cached_result:
                logger.debug(f" Cache hit para busca massiva {request.request_id}")
                return cached_result
        
        # Adicionar à fila
        self.request_queue.append(request)
        self.active_requests[request.request_id] = request
        
        # Aguardar processamento
        while request.request_id in self.active_requests:
            await asyncio.sleep(0.1)
        
        # Obter resultado (será armazenado em cache)
        cache_key = f"massive_search:{hashlib.md5(str(request).encode()).hexdigest()}"
        result = await self.cache.get(cache_key)
        
        if result:
            # Atualizar estatísticas
            processing_time = time.time() - start_time
            self.stats['total_requests'] += 1
            self.stats['successful_requests'] += 1
            self.stats['total_collectors_used'] += result.total_collectors_used
            
            # Atualizar tempo médio
            self._update_average_response_time(processing_time)
            
            logger.info(f" Busca massiva {request.request_id} concluída em {processing_time:.2f}s")
            return result
        else:
            raise RuntimeError(f"Resultado não encontrado para requisição {request.request_id}")
    
    async def _process_massive_request(self, request: MassiveSearchRequest):
        """Processa requisição massiva"""
        try:
            # Selecionar coletores
            selected_collectors = await self._select_collectors(request)
            
            # Executar buscas em paralelo
            results = await self._execute_parallel_searches(request, selected_collectors)
            
            # Processar resultados
            processed_result = await self._process_search_results(request, results)
            
            # Salvar em cache
            if self.config['caching_enabled']:
                cache_key = f"massive_search:{hashlib.md5(str(request).encode()).hexdigest()}"
                await self.cache.set(cache_key, processed_result)
            
            # Remover requisição ativa
            self.active_requests.pop(request.request_id, None)
            
        except Exception as e:
            logger.error(f" Erro processando requisição {request.request_id}: {str(e)}")
            
            # Criar resultado de erro
            error_result = MassiveSearchResult(
                request_id=request.request_id,
                total_collectors_used=0,
                successful_collectors=0,
                failed_collectors=0,
                total_results=0,
                processing_time=0.0,
                results={},
                errors=[str(e)]
            )
            
            # Salvar em cache
            if self.config['caching_enabled']:
                cache_key = f"massive_search:{hashlib.md5(str(request).encode()).hexdigest()}"
                await self.cache.set(cache_key, error_result)
            
            # Remover requisição ativa
            self.active_requests.pop(request.request_id, None)
    
    async def _select_collectors(self, request: MassiveSearchRequest) -> List[CollectorInstance]:
        """Seleciona coletores para a requisição"""
        selected = []
        
        # Se coletores específicos foram solicitados
        if request.specific_collectors:
            for collector_id in request.specific_collectors:
                if collector_id in self.collectors:
                    instance = self.collectors[collector_id]
                    if instance.status == CollectorStatus.READY and instance.health_score > 0.5:
                        selected.append(instance)
        
        # Se categorias foram especificadas
        elif request.categories:
            for category in request.categories:
                category_collectors = [
                    instance for instance in self.collectors.values()
                    if (instance.instance and 
                        instance.instance.metadata.category == category and
                        instance.status == CollectorStatus.READY and
                        instance.health_score > 0.5)
                ]
                selected.extend(category_collectors)
        
        # Seleção automática baseada em saúde e disponibilidade
        else:
            ready_collectors = [
                instance for instance in self.collectors.values()
                if (instance.status == CollectorStatus.READY and 
                    instance.health_score > 0.5)
            ]
            
            # Ordenar por saúde e uso recente
            ready_collectors.sort(key=lambda x: (x.health_score, -x.last_used))
            
            selected = ready_collectors[:request.max_collectors]
        
        # Limitar número de coletores
        if len(selected) > request.max_collectors:
            selected = selected[:request.max_collectors]
        
        # Atualizar estatísticas de uso por categoria
        for instance in selected:
            if instance.instance:
                category = instance.instance.metadata.category
                self.stats['category_usage'][category.value] += 1
        
        logger.info(f" Selecionados {len(selected)} coletores para requisição {request.request_id}")
        return selected
    
    async def _execute_parallel_searches(self, request: MassiveSearchRequest, selected_collectors: List[CollectorInstance]) -> Dict[str, Any]:
        """Executa buscas em paralelo"""
        results = {}
        semaphore = asyncio.Semaphore(self.config['max_concurrent_requests'])
        
        async def execute_search(instance: CollectorInstance):
            async with semaphore:
                try:
                    # Marcar como ocupado
                    instance.status = CollectorStatus.BUSY
                    instance.usage_count += 1
                    instance.last_used = time.time()
                    
                    # Criar requisição do coletor
                    collector_request = CollectorRequest(
                        request_id=f"{request.request_id}_{instance.collector_id}",
                        query=request.query,
                        limit=request.max_results_per_collector,
                        filters=request.filters,
                        priority=request.priority
                    )
                    
                    # Executar busca
                    start_time = time.time()
                    result = await instance.instance.execute_request(collector_request)
                    processing_time = time.time() - start_time
                    
                    # Atualizar estatísticas do coletor
                    instance.total_requests += 1
                    if result.success:
                        instance.successful_requests += 1
                        
                        # Atualizar tempo médio
                        if instance.successful_requests > 0:
                            instance.average_response_time = (
                                (instance.average_response_time * (instance.successful_requests - 1) + processing_time) /
                                instance.successful_requests
                            )
                    else:
                        instance.error_count += 1
                    
                    # Retornar ao status ready
                    instance.status = CollectorStatus.READY
                    
                    return instance.collector_id, result
                    
                except Exception as e:
                    instance.status = CollectorStatus.ERROR
                    instance.last_error = str(e)
                    instance.error_count += 1
                    
                    return instance.collector_id, CollectorResult(
                        request_id=collector_request.request_id,
                        collector_id=instance.collector_id,
                        success=False,
                        data=None,
                        error=str(e)
                    )
        
        # Executar buscas em paralelo
        tasks = [execute_search(instance) for instance in selected_collectors]
        task_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Processar resultados
        for task_result in task_results:
            if isinstance(task_result, Exception):
                logger.error(f" Erro na busca paralela: {str(task_result)}")
            else:
                collector_id, result = task_result
                results[collector_id] = result
        
        return results
    
    async def _process_search_results(self, request: MassiveSearchRequest, results: Dict[str, Any]) -> MassiveSearchResult:
        """Processa e formata resultados da busca"""
        start_time = time.time()
        
        successful_collectors = 0
        failed_collectors = 0
        total_results = 0
        errors = []
        
        # Contabilizar resultados
        for collector_id, result in results.items():
            if result.success:
                successful_collectors += 1
                if hasattr(result, 'items_count'):
                    total_results += result.items_count
                elif isinstance(result.data, list):
                    total_results += len(result.data)
                elif result.data:
                    total_results += 1
            else:
                failed_collectors += 1
                errors.append(f"{collector_id}: {result.error}")
        
        # Criar resultado base
        massive_result = MassiveSearchResult(
            request_id=request.request_id,
            total_collectors_used=len(results),
            successful_collectors=successful_collectors,
            failed_collectors=failed_collectors,
            total_results=total_results,
            processing_time=time.time() - start_time,
            results=results,
            errors=errors
        )
        
        # Processar baseado na estratégia
        if request.merge_strategy == "unified":
            massive_result.unified_results = await self._create_unified_results(results)
        elif request.merge_strategy == "ranked":
            massive_result.ranked_results = await self._create_ranked_results(results)
        
        # Adicionar metadados
        massive_result.metadata = {
            'merge_strategy': request.merge_strategy,
            'categories_used': list(set([
                self.collectors[cid].instance.metadata.category.value 
                for cid in results.keys() 
                if cid in self.collectors and self.collectors[cid].instance
            ])),
            'average_collector_health': sum(
                self.collectors[cid].health_score 
                for cid in results.keys() 
                if cid in self.collectors
            ) / max(1, len(results)),
            'timestamp': datetime.now().isoformat()
        }
        
        return massive_result
    
    async def _create_unified_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Cria resultados unificados"""
        unified = []
        
        for collector_id, result in results.items():
            if result.success and result.data:
                if isinstance(result.data, list):
                    for item in result.data:
                        unified_item = {
                            'data': item,
                            'source_collector': collector_id,
                            'collector_name': self.collectors[collector_id].instance.metadata.name,
                            'category': self.collectors[collector_id].instance.metadata.category.value,
                            'timestamp': time.time()
                        }
                        unified.append(unified_item)
                else:
                    unified_item = {
                        'data': result.data,
                        'source_collector': collector_id,
                        'collector_name': self.collectors[collector_id].instance.metadata.name,
                        'category': self.collectors[collector_id].instance.metadata.category.value,
                        'timestamp': time.time()
                    }
                    unified.append(unified_item)
        
        return unified
    
    async def _create_ranked_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Cria resultados ranqueados"""
        # Implementação básica de ranking baseado na saúde do coletor
        ranked = []
        
        for collector_id, result in results.items():
            if result.success and result.data:
                health_score = self.collectors[collector_id].health_score
                
                if isinstance(result.data, list):
                    for item in result.data:
                        ranked_item = {
                            'data': item,
                            'source_collector': collector_id,
                            'collector_name': self.collectors[collector_id].instance.metadata.name,
                            'category': self.collectors[collector_id].instance.metadata.category.value,
                            'health_score': health_score,
                            'rank_score': health_score * 100,  # Base score
                            'timestamp': time.time()
                        }
                        ranked.append(ranked_item)
                else:
                    ranked_item = {
                        'data': result.data,
                        'source_collector': collector_id,
                        'collector_name': self.collectors[collector_id].instance.metadata.name,
                        'category': self.collectors[collector_id].instance.metadata.category.value,
                        'health_score': health_score,
                        'rank_score': health_score * 100,
                        'timestamp': time.time()
                    }
                    ranked.append(ranked_item)
        
        # Ordenar por rank_score
        ranked.sort(key=lambda x: x['rank_score'], reverse=True)
        
        return ranked
    
    def _update_average_response_time(self, response_time: float):
        """Atualiza tempo médio de resposta"""
        total = self.stats['total_requests']
        current_avg = self.stats['average_response_time']
        new_avg = (current_avg * (total - 1) + response_time) / total
        self.stats['average_response_time'] = new_avg
    
    async def get_factory_status(self) -> Dict[str, Any]:
        """Obtém status completo do factory"""
        status = {
            'initialized': self.is_initialized,
            'total_collectors': len(self.collectors),
            'active_collectors': len([c for c in self.collectors.values() if c.status == CollectorStatus.READY]),
            'healthy_collectors': len([c for c in self.collectors.values() if c.health_score > 0.7]),
            'busy_collectors': len([c for c in self.collectors.values() if c.status == CollectorStatus.BUSY]),
            'error_collectors': len([c for c in self.collectors.values() if c.status == CollectorStatus.ERROR]),
            'active_requests': len(self.active_requests),
            'queued_requests': len(self.request_queue),
            'statistics': self.stats,
            'config': self.config,
            'category_distribution': defaultdict(int),
            'health_distribution': defaultdict(int)
        }
        
        # Distribuição por categoria
        for instance in self.collectors.values():
            if instance.instance:
                category = instance.instance.metadata.category.value
                status['category_distribution'][category] += 1
                
                health_range = "healthy" if instance.health_score > 0.7 else "degraded" if instance.health_score > 0.3 else "unhealthy"
                status['health_distribution'][health_range] += 1
        
        return dict(status)
    
    async def get_collector_details(self, collector_id: str) -> Optional[Dict[str, Any]]:
        """Obtém detalhes de um coletor específico"""
        if collector_id not in self.collectors:
            return None
        
        instance = self.collectors[collector_id]
        
        details = {
            'collector_id': collector_id,
            'status': instance.status.value,
            'health_score': instance.health_score,
            'usage_count': instance.usage_count,
            'error_count': instance.error_count,
            'total_requests': instance.total_requests,
            'successful_requests': instance.successful_requests,
            'average_response_time': instance.average_response_time,
            'last_used': instance.last_used,
            'last_error': instance.last_error
        }
        
        if instance.instance:
            metadata = instance.instance.get_metadata()
            details['metadata'] = {
                'name': metadata.name,
                'category': metadata.category.value,
                'description': metadata.description,
                'version': metadata.version,
                'author': metadata.author,
                'capabilities': metadata.capabilities,
                'limitations': metadata.limitations,
                'requirements': metadata.requirements,
                'api_key_required': metadata.api_key_required,
                'real_time': metadata.real_time,
                'bulk_support': metadata.bulk_support
            }
            
            # Health check do coletor
            try:
                health = await instance.instance.health_check()
                details['health_check'] = health
            except Exception as e:
                details['health_check'] = {'status': 'error', 'error': str(e)}
        
        return details
    
    async def enable_collector(self, collector_id: str) -> bool:
        """Habilita um coletor"""
        if collector_id not in self.collectors:
            return False
        
        instance = self.collectors[collector_id]
        
        if instance.status == CollectorStatus.DISABLED:
            try:
                # Tentar reinicializar
                await self._initialize_collector(instance)
                return True
            except Exception as e:
                logger.error(f" Erro habilitando coletor {collector_id}: {str(e)}")
                return False
        
        return True
    
    async def disable_collector(self, collector_id: str) -> bool:
        """Desabilita um coletor"""
        if collector_id not in self.collectors:
            return False
        
        instance = self.collectors[collector_id]
        instance.status = CollectorStatus.DISABLED
        
        # Limpar instância se existir
        if instance.instance:
            try:
                await instance.instance.cleanup()
            except:
                pass
            instance.instance = None
        
        return True
    
    async def cleanup(self):
        """Limpa recursos do factory"""
        logger.info(" Limpando Massive Collector Factory...")
        
        # Parar tarefas
        if self.health_check_task:
            self.health_check_task.cancel()
        
        if self.request_processor_task:
            self.request_processor_task.cancel()
        
        # Limpar coletores
        for instance in self.collectors.values():
            if instance.instance:
                try:
                    await instance.instance.cleanup()
                except:
                    pass
        
        # Limpar cache
        self.cache.clear()
        
        # Limpar filas
        self.request_queue.clear()
        self.active_requests.clear()
        
        logger.info(" Massive Collector Factory limpo")

# Instância global do factory
massive_factory = MassiveCollectorFactory()
