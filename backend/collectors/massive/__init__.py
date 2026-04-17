"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - Massive Collectors Package
Pacote principal dos 100 coletores de dados da internet
"""

from .collector_registry import CollectorRegistry, CollectorMetadata, CollectorCategory, CollectorStatus
from .base_collector import BaseCollector, CollectorRequest, CollectorResult, CollectorConfig
from .massive_collector_factory import MassiveCollectorFactory, MassiveSearchRequest, MassiveSearchResult
from .distributed_orchestrator import DistributedOrchestrator, OrchestrationMode, OrchestrationTask
from .unified_interface import UnifiedInterface, UnifiedSearchRequest, UnifiedSearchResult, SearchType, ResultFormat
from .massive_cache_system import MassiveCacheSystem, CacheLevel, CachePolicy, CompressionType

# Importar coletores específicos
from .web_scraping.web_scraping_collectors import get_web_scraping_collectors
from .api_platforms.api_platforms_collectors import get_api_platforms_collectors
from .crawlers_bots.crawlers_bots_collectors import get_crawlers_bots_collectors
from .massive_platforms.massive_platforms_collectors import get_massive_platforms_collectors
from .advanced_tools.advanced_tools_collectors import get_advanced_tools_collectors
from .specialized_apis.specialized_apis_collectors import get_specialized_apis_collectors
from .collection_techniques.collection_techniques_collectors import get_collection_techniques_collectors
from .massive_databases.massive_databases_collectors import get_massive_databases_collectors
from .ai_platforms.ai_platforms_collectors import get_ai_platforms_collectors

# Instâncias globais
massive_collector_factory = MassiveCollectorFactory()
unified_interface = UnifiedInterface()
massive_cache_system = MassiveCacheSystem()

# Funções de conveniência
async def initialize_massive_collectors():
    """Inicializa todos os 100 coletores"""
    await massive_collector_factory.initialize()
    await unified_interface.initialize()
    await massive_cache_system.initialize()

async def search_all_sources(query: str, **kwargs):
    """Busca em todas as fontes disponíveis"""
    request = UnifiedSearchRequest(
        query=query,
        search_type=SearchType.COMPREHENSIVE,
        max_collectors=100,
        max_results_per_collector=50,
        **kwargs
    )
    return await unified_interface.search(request)

async def search_by_category(query: str, category: CollectorCategory, **kwargs):
    """Busca por categoria específica"""
    request = UnifiedSearchRequest(
        query=query,
        search_type=SearchType.CATEGORY_SPECIFIC,
        categories=[category],
        **kwargs
    )
    return await unified_interface.search(request)

async def search_intelligent(query: str, **kwargs):
    """Busca inteligente com seleção automática"""
    request = UnifiedSearchRequest(
        query=query,
        search_type=SearchType.INTELLIGENT,
        **kwargs
    )
    return await unified_interface.search(request)

def get_all_collectors():
    """Retorna todos os 240 coletores disponíveis"""
    return {
        'web_scraping': get_web_scraping_collectors(),
        'api_platforms': get_api_platforms_collectors(),
        'crawlers_bots': get_crawlers_bots_collectors(),
        'massive_platforms': get_massive_platforms_collectors(),
        'advanced_tools': get_advanced_tools_collectors(),
        'specialized_apis': get_specialized_apis_collectors(),
        'collection_techniques': get_collection_techniques_collectors(),
        'massive_databases': get_massive_databases_collectors(),
        'ai_platforms': get_ai_platforms_collectors()
    }

def get_collector_count():
    """Retorna o número total de coletores"""
    collectors = get_all_collectors()
    return sum(len(collectors) for collectors in collectors.values())

# Exportar classes e funções principais
__all__ = [
    # Classes principais
    'CollectorRegistry',
    'CollectorMetadata', 
    'CollectorCategory',
    'CollectorStatus',
    'BaseCollector',
    'CollectorRequest',
    'CollectorResult',
    'CollectorConfig',
    'MassiveCollectorFactory',
    'MassiveSearchRequest',
    'MassiveSearchResult',
    'DistributedOrchestrator',
    'OrchestrationMode',
    'OrchestrationTask',
    'UnifiedInterface',
    'UnifiedSearchRequest',
    'UnifiedSearchResult',
    'SearchType',
    'ResultFormat',
    'MassiveCacheSystem',
    'CacheLevel',
    'CachePolicy',
    'CompressionType',
    
    # Instâncias globais
    'massive_collector_factory',
    'unified_interface',
    'massive_cache_system',
    
    # Funções de conveniência
    'initialize_massive_collectors',
    'search_all_sources',
    'search_by_category',
    'search_intelligent',
    'get_all_collectors',
    'get_collector_count',
    
    # Funções para obter coletores
    'get_web_scraping_collectors',
    'get_api_platforms_collectors',
    'get_crawlers_bots_collectors',
    'get_massive_platforms_collectors',
    'get_advanced_tools_collectors',
    'get_specialized_apis_collectors',
    'get_collection_techniques_collectors',
    'get_massive_databases_collectors',
    'get_ai_platforms_collectors'
]

# Informações do pacote
__version__ = "2.0.0"
__author__ = "Info-Phantom Team"
__description__ = "Sistema massivo com 240 coletores de dados da internet"
__total_collectors__ = 240

# Logging de inicialização
import logging
logger = logging.getLogger(__name__)
logger.info(f" Massive Collectors Package v{__version__} carregado")
logger.info(f" Total de coletores: {__total_collectors__}")
logger.info(f" Estrutura: 30 Web Scraping + 30 APIs + 20 Crawlers + 20 Plataformas + 30 Advanced Tools + 30 Specialized APIs + 30 Collection Techniques + 30 Massive Databases + 20 AI Platforms")
