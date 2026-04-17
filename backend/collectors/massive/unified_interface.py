"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - Unified Interface
Interface unificada para todos os 100 coletores de dados da internet
"""

import asyncio
import json
import time
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid

from .massive_collector_factory import MassiveCollectorFactory, MassiveSearchRequest, MassiveSearchResult
from .distributed_orchestrator import DistributedOrchestrator, OrchestrationMode
from .collector_registry import CollectorCategory
from .base_collector import CollectorRequest, CollectorResult
from ..utils.logger import setup_logger
from ..utils.metrics import MetricsCollector

logger = setup_logger(__name__)
metrics = MetricsCollector()

class SearchType(Enum):
    """Tipos de busca suportados"""
    UNIFIED = "unified"
    CATEGORY_SPECIFIC = "category_specific"
    COLLECTOR_SPECIFIC = "collector_specific"
    INTELLIGENT = "intelligent"
    COMPREHENSIVE = "comprehensive"

class ResultFormat(Enum):
    """Formatos de resultado"""
    JSON = "json"
    CSV = "csv"
    XML = "xml"
    EXCEL = "excel"
    PARQUET = "parquet"

@dataclass
class UnifiedSearchRequest:
    """Requisição de busca unificada"""
    query: str
    search_type: SearchType = SearchType.UNIFIED
    categories: List[CollectorCategory] = field(default_factory=list)
    specific_collectors: List[str] = field(default_factory=list)
    max_collectors: int = 20
    max_results_per_collector: int = 50
    max_total_results: int = 1000
    timeout: int = 60
    priority: int = 1
    filters: Dict[str, Any] = field(default_factory=dict)
    result_format: ResultFormat = ResultFormat.JSON
    include_metadata: bool = True
    include_raw_data: bool = False
    enable_caching: bool = True
    enable_ranking: bool = True
    merge_strategy: str = "unified"
    orchestration_mode: OrchestrationMode = OrchestrationMode.ADAPTIVE

@dataclass
class UnifiedSearchResult:
    """Resultado de busca unificado"""
    request_id: str
    query: str
    search_type: str
    total_collectors_used: int
    successful_collectors: int
    failed_collectors: int
    total_results: int
    processing_time: float
    results: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    errors: List[str]
    statistics: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

class UnifiedInterface:
    """Interface unificada para 100 coletores de dados"""
    
    def __init__(self):
        self.factory = MassiveCollectorFactory()
        self.orchestrator = None
        self.is_initialized = False
        
        # Cache para resultados
        self.request_cache = {}
        self.cache_ttl = 3600  # 1 hora
        
        # Estatísticas da interface
        self.interface_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_response_time': 0.0,
            'cache_hit_rate': 0.0,
            'popular_queries': {},
            'category_usage': {},
            'collector_usage': {}
        }
        
        logger.info(" Unified Interface inicializada")
    
    async def initialize(self):
        """Inicializa a interface unificada"""
        if self.is_initialized:
            return
        
        logger.info(" Inicializando Unified Interface...")
        start_time = time.time()
        
        try:
            # Inicializar factory
            await self.factory.initialize()
            
            # Inicializar orquestrador
            self.orchestrator = DistributedOrchestrator(self.factory)
            await self.orchestrator.initialize()
            
            self.is_initialized = True
            initialization_time = time.time() - start_time
            
            logger.info(f" Unified Interface inicializada em {initialization_time:.2f}s")
            
        except Exception as e:
            logger.error(f" Falha na inicialização da interface: {str(e)}")
            raise
    
    async def search(self, request: UnifiedSearchRequest) -> UnifiedSearchResult:
        """
        Executa busca unificada usando todos os coletores disponíveis
        
        Args:
            request: Requisição de busca unificada
            
        Returns:
            Resultado unificado da busca
        """
        if not self.is_initialized:
            raise RuntimeError("Interface não inicializada")
        
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        logger.info(f" Iniciando busca unificada: {request_id} - '{request.query}'")
        
        try:
            # Atualizar estatísticas
            self.interface_stats['total_requests'] += 1
            
            # Verificar cache
            if request.enable_caching:
                cache_key = self._generate_cache_key(request)
                cached_result = self._get_from_cache(cache_key)
                if cached_result:
                    logger.debug(f" Cache hit para busca {request_id}")
                    self.interface_stats['cache_hit_rate'] = self._update_cache_hit_rate(True)
                    return cached_result
                else:
                    self.interface_stats['cache_hit_rate'] = self._update_cache_hit_rate(False)
            
            # Executar busca baseada no tipo
            if request.search_type == SearchType.UNIFIED:
                result = await self._execute_unified_search(request, request_id)
            elif request.search_type == SearchType.CATEGORY_SPECIFIC:
                result = await self._execute_category_search(request, request_id)
            elif request.search_type == SearchType.COLLECTOR_SPECIFIC:
                result = await self._execute_collector_search(request, request_id)
            elif request.search_type == SearchType.INTELLIGENT:
                result = await self._execute_intelligent_search(request, request_id)
            elif request.search_type == SearchType.COMPREHENSIVE:
                result = await self._execute_comprehensive_search(request, request_id)
            else:
                raise ValueError(f"Tipo de busca não suportado: {request.search_type}")
            
            # Formatar resultados
            formatted_result = await self._format_results(result, request)
            
            # Adicionar metadados
            formatted_result.metadata = await self._generate_metadata(result, request)
            
            # Adicionar estatísticas
            formatted_result.statistics = await self._generate_statistics(result, request)
            
            # Salvar em cache
            if request.enable_caching:
                cache_key = self._generate_cache_key(request)
                self._save_to_cache(cache_key, formatted_result)
            
            # Atualizar estatísticas da interface
            processing_time = time.time() - start_time
            self.interface_stats['successful_requests'] += 1
            self._update_average_response_time(processing_time)
            self._update_usage_stats(request)
            
            logger.info(f" Busca unificada {request_id} concluída em {processing_time:.2f}s")
            return formatted_result
            
        except Exception as e:
            self.interface_stats['failed_requests'] += 1
            logger.error(f" Erro na busca unificada {request_id}: {str(e)}")
            
            # Retornar resultado de erro
            return UnifiedSearchResult(
                request_id=request_id,
                query=request.query,
                search_type=request.search_type.value,
                total_collectors_used=0,
                successful_collectors=0,
                failed_collectors=0,
                total_results=0,
                processing_time=time.time() - start_time,
                results=[],
                metadata={},
                errors=[str(e)],
                statistics={}
            )
    
    async def _execute_unified_search(self, request: UnifiedSearchRequest, request_id: str) -> MassiveSearchResult:
        """Executa busca unificada padrão"""
        # Criar requisição massiva
        massive_request = MassiveSearchRequest(
            request_id=request_id,
            query=request.query,
            categories=request.categories,
            specific_collectors=request.specific_collectors,
            max_collectors=request.max_collectors,
            max_results_per_collector=request.max_results_per_collector,
            timeout=request.timeout,
            priority=request.priority,
            filters=request.filters,
            merge_strategy=request.merge_strategy
        )
        
        # Submeter ao orquestrador
        task_id = await self.orchestrator.submit_task(massive_request)
        
        # Aguardar conclusão
        while True:
            task_status = await self.orchestrator.get_task_status(task_id)
            if task_status and task_status['status'] in ['completed', 'failed']:
                break
            await asyncio.sleep(0.5)
        
        # Obter resultado
        result = await self.orchestrator.get_task_result(task_id)
        return result
    
    async def _execute_category_search(self, request: UnifiedSearchRequest, request_id: str) -> MassiveSearchResult:
        """Executa busca específica por categoria"""
        # Se não especificou categorias, usar todas
        if not request.categories:
            request.categories = list(CollectorCategory)
        
        return await self._execute_unified_search(request, request_id)
    
    async def _execute_collector_search(self, request: UnifiedSearchRequest, request_id: str) -> MassiveSearchResult:
        """Executa busca específica por coletores"""
        # Se não especificou coletores, selecionar os melhores
        if not request.specific_collectors:
            request.specific_collectors = await self._get_best_collectors(request.query, 10)
        
        return await self._execute_unified_search(request, request_id)
    
    async def _execute_intelligent_search(self, request: UnifiedSearchRequest, request_id: str) -> MassiveSearchResult:
        """Executa busca inteligente com seleção adaptativa"""
        # Análise da query para determinar melhores coletores
        query_analysis = await self._analyze_query(request.query)
        
        # Selecionar coletores baseado na análise
        selected_collectors = await self._select_collectors_intelligently(query_analysis)
        
        # Ajustar requisição
        request.specific_collectors = selected_collectors
        request.max_collectors = len(selected_collectors)
        
        return await self._execute_unified_search(request, request_id)
    
    async def _execute_comprehensive_search(self, request: UnifiedSearchRequest, request_id: str) -> MassiveSearchResult:
        """Executa busca compreensiva usando todos os coletores disponíveis"""
        # Usar todos os coletores saudáveis
        request.max_collectors = 100
        request.categories = list(CollectorCategory)
        
        return await self._execute_unified_search(request, request_id)
    
    async def _analyze_query(self, query: str) -> Dict[str, Any]:
        """Analisa a query para determinar estratégia ótima"""
        analysis = {
            'query_type': 'general',
            'entities': [],
            'intent': 'search',
            'categories': [],
            'keywords': query.lower().split(),
            'language': 'pt',  # Detecção simplificada
            'complexity': 'medium'
        }
        
        # Detectar tipo de query
        if any(word in query.lower() for word in ['comprar', 'preço', 'promoção']):
            analysis['query_type'] = 'ecommerce'
            analysis['categories'].append(CollectorCategory.MASSIVE_PLATFORMS)
        elif any(word in query.lower() for word in ['notícia', 'jornal', 'notícias']):
            analysis['query_type'] = 'news'
            analysis['categories'].append(CollectorCategory.API_PLATFORMS)
        elif any(word in query.lower() for word in ['pesquisar', 'buscar', 'encontrar']):
            analysis['query_type'] = 'search'
            analysis['categories'].append(CollectorCategory.WEB_SCRAPING)
        elif any(word in query.lower() for word in ['dados', 'dataset', 'análise']):
            analysis['query_type'] = 'data'
            analysis['categories'].append(CollectorCategory.CRAWLERS_BOTS)
        
        # Detectar entidades (simplificado)
        import re
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', query)
        urls = re.findall(r'https?://[^\s]+', query)
        
        if emails:
            analysis['entities'].extend([('email', email) for email in emails])
        if urls:
            analysis['entities'].extend([('url', url) for url in urls])
        
        return analysis
    
    async def _select_collectors_intelligently(self, analysis: Dict[str, Any]) -> List[str]:
        """Seleciona coletores de forma inteligente baseada na análise"""
        selected_collectors = []
        
        # Baseado nas categorias detectadas
        for category in analysis.get('categories', []):
            category_collectors = [
                cid for cid, instance in self.factory.collectors.items()
                if (instance.instance and 
                    instance.instance.metadata.category == category and
                    instance.status.value == "ready" and
                    instance.health_score > 0.7)
            ]
            selected_collectors.extend(category_collectors[:5])  # Top 5 por categoria
        
        # Se não detectou categorias específicas, usar os melhores coletores gerais
        if not selected_collectors:
            best_collectors = [
                cid for cid, instance in self.factory.collectors.items()
                if (instance.instance and
                    instance.status.value == "ready" and
                    instance.health_score > 0.8)
            ]
            selected_collectors = best_collectors[:20]
        
        return selected_collectors[:request.max_collectors] if hasattr(request, 'max_collectors') else selected_collectors[:20]
    
    async def _get_best_collectors(self, query: str, limit: int) -> List[str]:
        """Obtém os melhores coletores para uma query"""
        # Análise simples da query
        query_lower = query.lower()
        
        # Coletores por prioridade baseada na query
        priority_collectors = []
        
        # Se parece com busca web
        if any(word in query_lower for word in ['buscar', 'pesquisar', 'encontrar']):
            priority_collectors.extend([
                'web_scraping_01_scrapycollector',
                'web_scraping_02_beautysoupcollector',
                'web_scraping_03_seleniumcollector',
                'massive_platforms_01_googlesearchcollector'
            ])
        
        # Se parece com busca de dados
        if any(word in query_lower for word in ['dados', 'data', 'informação']):
            priority_collectors.extend([
                'massive_platforms_02_wikipediacollector',
                'massive_platforms_03_commoncrawlcollector',
                'massive_platforms_04_kagglecollector',
                'crawlers_bots_03_dataminingcollector'
            ])
        
        # Se parece com busca de notícias
        if any(word in query_lower for word in ['notícia', 'jornal', 'notícias']):
            priority_collectors.extend([
                'api_platforms_11_newsapicollector',
                'massive_platforms_01_googlesearchcollector'
            ])
        
        # Se não detectou padrão, usar coletores gerais
        if not priority_collectors:
            priority_collectors = [
                'web_scraping_01_scrapycollector',
                'api_platforms_09_githubapicollector',
                'massive_platforms_02_wikipediacollector',
                'massive_platforms_01_googlesearchcollector',
                'api_platforms_08_openweatherapicollector'
            ]
        
        # Obter coletores disponíveis e saudáveis
        available_collectors = [
            cid for cid in priority_collectors
            if cid in self.factory.collectors and
               self.factory.collectors[cid].status.value == "ready" and
               self.factory.collectors[cid].health_score > 0.5
        ]
        
        return available_collectors[:limit]
    
    async def _format_results(self, result: MassiveSearchResult, request: UnifiedSearchRequest) -> UnifiedSearchResult:
        """Formata resultados baseado no formato solicitado"""
        unified_result = UnifiedSearchResult(
            request_id=result.request_id,
            query=request.query,
            search_type=request.search_type.value,
            total_collectors_used=result.total_collectors_used,
            successful_collectors=result.successful_collectors,
            failed_collectors=result.failed_collectors,
            total_results=result.total_results,
            processing_time=result.processing_time,
            results=[],
            metadata={},
            errors=result.errors,
            statistics={}
        )
        
        # Formatar baseado no tipo de resultado
        if request.merge_strategy == "unified" and hasattr(result, 'unified_results'):
            unified_result.results = result.unified_results
        elif hasattr(result, 'ranked_results') and result.ranked_results:
            unified_result.results = result.ranked_results
        else:
            # Formatar resultados brutos
            for collector_id, collector_result in result.results.items():
                if hasattr(collector_result, 'success') and collector_result.success:
                    if isinstance(collector_result.data, list):
                        for item in collector_result.data:
                            formatted_item = {
                                'data': item,
                                'source_collector': collector_id,
                                'collector_name': self.factory.collectors[collector_id].instance.metadata.name if collector_id in self.factory.collectors else 'Unknown',
                                'category': self.factory.collectors[collector_id].instance.metadata.category.value if collector_id in self.factory.collectors else 'Unknown'
                            }
                            unified_result.results.append(formatted_item)
                    else:
                        formatted_item = {
                            'data': collector_result.data,
                            'source_collector': collector_id,
                            'collector_name': self.factory.collectors[collector_id].instance.metadata.name if collector_id in self.factory.collectors else 'Unknown',
                            'category': self.factory.collectors[collector_id].instance.metadata.category.value if collector_id in self.factory.collectors else 'Unknown'
                        }
                        unified_result.results.append(formatted_item)
        
        # Limitar número de resultados
        if request.max_total_results and len(unified_result.results) > request.max_total_results:
            unified_result.results = unified_result.results[:request.max_total_results]
            unified_result.total_results = request.max_total_results
        
        return unified_result
    
    async def _generate_metadata(self, result: MassiveSearchResult, request: UnifiedSearchRequest) -> Dict[str, Any]:
        """Gera metadados do resultado"""
        metadata = {
            'request_id': result.request_id,
            'search_type': request.search_type.value,
            'merge_strategy': request.merge_strategy,
            'orchestration_mode': request.orchestration_mode.value,
            'categories_used': [],
            'collectors_used': [],
            'processing_details': {
                'total_collectors_available': len(self.factory.collectors),
                'collectors_considered': len(result.results),
                'cache_enabled': request.enable_caching,
                'ranking_enabled': request.enable_ranking
            },
            'quality_metrics': {
                'success_rate': result.successful_collectors / max(1, result.total_collectors_used),
                'error_rate': result.failed_collectors / max(1, result.total_collectors_used),
                'data_completeness': result.total_results / max(1, request.max_total_results)
            }
        }
        
        # Adicionar informações dos coletores usados
        for collector_id in result.results.keys():
            if collector_id in self.factory.collectors:
                instance = self.factory.collectors[collector_id]
                if instance.instance:
                    metadata['collectors_used'].append({
                        'id': collector_id,
                        'name': instance.instance.metadata.name,
                        'category': instance.instance.metadata.category.value,
                        'health_score': instance.health_score
                    })
                    
                    category = instance.instance.metadata.category.value
                    if category not in metadata['categories_used']:
                        metadata['categories_used'].append(category)
        
        return metadata
    
    async def _generate_statistics(self, result: MassiveSearchResult, request: UnifiedSearchRequest) -> Dict[str, Any]:
        """Gera estatísticas detalhadas"""
        statistics = {
            'performance': {
                'processing_time': result.processing_time,
                'collectors_per_second': result.total_collectors_used / max(0.001, result.processing_time),
                'results_per_second': result.total_results / max(0.001, result.processing_time),
                'average_collector_time': result.processing_time / max(1, result.total_collectors_used)
            },
            'data_volume': {
                'total_results': result.total_results,
                'successful_collectors': result.successful_collectors,
                'failed_collectors': result.failed_collectors,
                'average_results_per_collector': result.total_results / max(1, result.successful_collectors)
            },
            'distribution': {
                'by_category': {},
                'by_collector': {}
            },
            'quality': {
                'overall_success_rate': result.successful_collectors / max(1, result.total_collectors_used),
                'data_quality_score': min(1.0, result.total_results / max(1, request.max_total_results)),
                'error_rate': result.failed_collectors / max(1, result.total_collectors_used)
            }
        }
        
        # Distribuição por categoria
        category_counts = {}
        for collector_id in result.results.keys():
            if collector_id in self.factory.collectors:
                instance = self.factory.collectors[collector_id]
                if instance.instance:
                    category = instance.instance.metadata.category.value
                    category_counts[category] = category_counts.get(category, 0) + 1
        
        statistics['distribution']['by_category'] = category_counts
        
        return statistics
    
    def _generate_cache_key(self, request: UnifiedSearchRequest) -> str:
        """Gera chave de cache para a requisição"""
        cache_data = {
            'query': request.query,
            'search_type': request.search_type.value,
            'categories': [c.value for c in request.categories],
            'collectors': request.specific_collectors,
            'max_collectors': request.max_collectors,
            'filters': request.filters
        }
        return hashlib.md5(json.dumps(cache_data, sort_keys=True).encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[UnifiedSearchResult]:
        """Obtém resultado do cache"""
        if cache_key in self.request_cache:
            cached_data, timestamp = self.request_cache[cache_key]
            
            # Verificar se ainda é válido
            if time.time() - timestamp < self.cache_ttl:
                return cached_data
            else:
                del self.request_cache[cache_key]
        
        return None
    
    def _save_to_cache(self, cache_key: str, result: UnifiedSearchResult):
        """Salva resultado no cache"""
        self.request_cache[cache_key] = (result, time.time())
        
        # Limpar cache antigo se necessário
        if len(self.request_cache) > 1000:  # Limite de 1000 itens
            oldest_key = min(self.request_cache.keys(), 
                           key=lambda k: self.request_cache[k][1])
            del self.request_cache[oldest_key]
    
    def _update_cache_hit_rate(self, hit: bool) -> float:
        """Atualiza taxa de cache hit"""
        total_requests = self.interface_stats['total_requests']
        if total_requests <= 1:
            return 1.0 if hit else 0.0
        
        current_rate = self.interface_stats.get('cache_hit_rate', 0.0)
        
        if hit:
            new_rate = (current_rate * (total_requests - 1) + 1.0) / total_requests
        else:
            new_rate = (current_rate * (total_requests - 1)) / total_requests
        
        return new_rate
    
    def _update_average_response_time(self, response_time: float):
        """Atualiza tempo médio de resposta"""
        total_requests = self.interface_stats['total_requests']
        current_avg = self.interface_stats['average_response_time']
        new_avg = (current_avg * (total_requests - 1) + response_time) / total_requests
        self.interface_stats['average_response_time'] = new_avg
    
    def _update_usage_stats(self, request: UnifiedSearchRequest):
        """Atualiza estatísticas de uso"""
        # Query popularity
        query = request.query.lower()
        self.interface_stats['popular_queries'][query] = \
            self.interface_stats['popular_queries'].get(query, 0) + 1
        
        # Category usage
        for category in request.categories:
            cat_name = category.value
            self.interface_stats['category_usage'][cat_name] = \
                self.interface_stats['category_usage'].get(cat_name, 0) + 1
        
        # Collector usage
        for collector in request.specific_collectors:
            self.interface_stats['collector_usage'][collector] = \
                self.interface_stats['collector_usage'].get(collector, 0) + 1
    
    async def get_available_collectors(self) -> Dict[str, Any]:
        """Obtém coletores disponíveis"""
        return await self.factory.get_factory_status()
    
    async def get_collector_details(self, collector_id: str) -> Optional[Dict[str, Any]]:
        """Obtém detalhes de um coletor específico"""
        return await self.factory.get_collector_details(collector_id)
    
    async def get_interface_status(self) -> Dict[str, Any]:
        """Obtém status da interface unificada"""
        return {
            'initialized': self.is_initialized,
            'statistics': self.interface_stats,
            'factory_status': await self.factory.get_factory_status(),
            'orchestrator_status': await self.orchestrator.get_orchestrator_status() if self.orchestrator else None,
            'cache_size': len(self.request_cache),
            'cache_ttl': self.cache_ttl
        }
    
    async def export_results(self, request_id: str, format: ResultFormat = ResultFormat.JSON) -> Union[str, bytes]:
        """Exporta resultados em diferentes formatos"""
        # Implementação básica - em produção teria exportação real para CSV, Excel, etc.
        return f"Resultados para {request_id} em formato {format.value}"
    
    async def batch_search(self, requests: List[UnifiedSearchRequest]) -> List[UnifiedSearchResult]:
        """Executa múltiplas buscas em lote"""
        logger.info(f" Executando batch search: {len(requests)} requisições")
        
        # Executar em paralelo com limite de concorrência
        semaphore = asyncio.Semaphore(10)  # Limite de 10 requisições simultâneas
        
        async def execute_with_semaphore(req):
            async with semaphore:
                return await self.search(req)
        
        tasks = [execute_with_semaphore(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Processar exceções
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f" Erro na requisição {i}: {str(result)}")
                error_result = UnifiedSearchResult(
                    request_id=f"error_{i}",
                    query=requests[i].query,
                    search_type=requests[i].search_type.value,
                    total_collectors_used=0,
                    successful_collectors=0,
                    failed_collectors=0,
                    total_results=0,
                    processing_time=0.0,
                    results=[],
                    metadata={},
                    errors=[str(result)],
                    statistics={}
                )
                processed_results.append(error_result)
            else:
                processed_results.append(result)
        
        logger.info(f" Batch search concluído: {len(processed_results)} resultados")
        return processed_results
    
    async def cleanup(self):
        """Limpa recursos da interface"""
        logger.info(" Limpando Unified Interface...")
        
        if self.orchestrator:
            await self.orchestrator.cleanup()
        
        await self.factory.cleanup()
        
        self.request_cache.clear()
        self.interface_stats.clear()
        
        logger.info(" Unified Interface limpa")

# Instância global da interface unificada
unified_interface = UnifiedInterface()
