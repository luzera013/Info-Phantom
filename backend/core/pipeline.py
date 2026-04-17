"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - Pipeline Principal
Orquestra buscas, scraping, extração e IA
"""

import asyncio
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

from collectors.web.search_engine import WebSearchEngine
from collectors.web.bing import BingSearchEngine
from collectors.web.crawler import WebCrawler
from collectors.web.parser import DataParser
from collectors.social.reddit import RedditCollector
from collectors.social.github import GitHubCollector
from collectors.knowledge.wikipedia import WikipediaCollector
from collectors.knowledge.wikidata import WikidataCollector
from collectors.news.rss import RSSCollector
from collectors.news.news_api import NewsAPICollector
from collectors.tor.tor_client import TorClient
from collectors.tor.onion_scraper import OnionScraper
from services.ai.llm import LLMService
from services.ai.summarizer import SummarizerService
from services.ai.fallback import FallbackAIService
from utils.memory_cache import MemoryCache
from utils.ttl_cache import TTLCache
from utils.logger import setup_logger
from utils.metrics import MetricsCollector
from .data_aggregator import DataAggregator
from ..utils.performance_optimizer import PerformanceOptimizer

logger = setup_logger(__name__)
metrics = MetricsCollector()

@dataclass
class SearchResult:
    """Estrutura de resultado de busca"""
    title: str
    url: str
    description: str
    source: str
    timestamp: float
    relevance_score: float = 0.0
    extracted_data: Dict[str, Any] = None

@dataclass
class PipelineResult:
    """Resultado completo do pipeline"""
    query: str
    results: List[SearchResult]
    summary: str
    total_results: int
    processing_time: float
    sources_used: List[str]
    extracted_data: Dict[str, Any]

class SearchPipeline:
    """Pipeline principal de busca e análise"""
    
    def __init__(self):
        self.cache = TTLCache(ttl=3600)  # 1 hora
        self.memory_cache = MemoryCache()
        self.llm_service = LLMService()
        self.summarizer = SummarizerService()
        self.fallback_ai = FallbackAIService()
        
        # Inicializar otimizador de performance
        self.perf_optimizer = PerformanceOptimizer()
        
        # Inicializar coletores
        self.web_search = WebSearchEngine()
        self.bing_search = BingSearchEngine()
        self.crawler = WebCrawler()
        self.parser = DataParser()
        self.reddit_collector = RedditCollector()
        self.github_collector = GitHubCollector()
        self.wikipedia_collector = WikipediaCollector()
        self.wikidata_collector = WikidataCollector()
        self.rss_collector = RSSCollector()
        self.news_collector = NewsAPICollector()
        self.tor_client = TorClient()
        self.onion_scraper = OnionScraper()
        
        logger.info("🔧 Pipeline inicializado com todos os coletores e otimizador")
    
    async def execute_search(self, query: str, max_results: int = 500, 
                           sources: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Executa pipeline completo de busca com agregação unificada
        
        Args:
            query: Termo de busca
            max_results: Número máximo de resultados
            sources: Fontes específicas para usar
        
        Returns:
            Resposta unificada completa com TODAS as fontes agregadas
        """
        start_time = time.time()
        logger.info(f"🔍 Iniciando busca unificada por: '{query}'")
        
        # Verificar cache unificado
        cache_key = f"unified_search:{query}:{max_results}:{sources}"
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            logger.info("📦 Resultado unificado encontrado em cache")
            metrics.increment_cache_hit()
            return cached_result
        
        try:
            # Inicializar agregador com otimização
            aggregator = DataAggregator()
            
            # Fase 1: Busca em TODAS as fontes com otimização extrema
            search_tasks = []
            
            # Buscas web otimizadas
            if not sources or 'web' in sources:
                search_tasks.append(
                    self.perf_optimizer.execute_with_optimization(
                        self.web_search.search, query, max_results//4
                    )
                )
                search_tasks.append(
                    self.perf_optimizer.execute_with_optimization(
                        self.bing_search.search, query, max_results//4
                    )
                )
            
            # Busca social otimizada
            if not sources or 'social' in sources:
                search_tasks.append(
                    self.perf_optimizer.execute_with_optimization(
                        self.reddit_collector.search, query, max_results//6
                    )
                )
                search_tasks.append(
                    self.perf_optimizer.execute_with_optimization(
                        self.github_collector.search, query, max_results//6
                    )
                )
            
            # Busca conhecimento otimizada
            if not sources or 'knowledge' in sources:
                search_tasks.append(
                    self.perf_optimizer.execute_with_optimization(
                        self.wikipedia_collector.search, query, max_results//6
                    )
                )
                search_tasks.append(
                    self.perf_optimizer.execute_with_optimization(
                        self.wikidata_collector.search, query, max_results//6
                    )
                )
            
            # Busca notícias otimizada
            if not sources or 'news' in sources:
                search_tasks.append(
                    self.perf_optimizer.execute_with_optimization(
                        self.rss_collector.search, query, max_results//6
                    )
                )
                search_tasks.append(
                    self.perf_optimizer.execute_with_optimization(
                        self.news_collector.search, query, max_results//6
                    )
                )
            
            # Busca Tor otimizada
            if not sources or 'tor' in sources:
                search_tasks.append(
                    self.perf_optimizer.execute_with_optimization(
                        self.onion_scraper.search, query, max_results//8
                    )
                )
            
            # Executar todas as buscas com otimização extrema
            logger.info(f"� Executando {len(search_tasks)} buscas otimizadas em paralelo...")
            search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # Separar resultados por fonte
            web_results = []
            news_results = []
            wikipedia_results = []
            github_results = []
            reddit_results = []
            tor_results = []
            
            for i, result in enumerate(search_results):
                if isinstance(result, Exception):
                    logger.warning(f"⚠️ Erro na busca {i}: {str(result)}")
                    continue
                
                # Classificar resultados por fonte baseado na ordem das tarefas
                task_index = i % len(search_tasks)
                if task_index < 2:  # Web searches
                    web_results.extend(result)
                elif task_index < 4:  # Social
                    if task_index == 2:
                        reddit_results.extend(result)
                    else:
                        github_results.extend(result)
                elif task_index < 6:  # Knowledge
                    if task_index == 4:
                        wikipedia_results.extend(result)
                    else:
                        wikidata_results = result  # Não usado diretamente
                elif task_index < 8:  # News
                    if task_index == 6:
                        rss_results = result  # RSS não usado diretamente
                    else:
                        news_results.extend(result)
                else:  # Tor
                    tor_results.extend(result)
            
            logger.info(f"📊 Resultados por fonte: Web={len(web_results)}, Reddit={len(reddit_results)}, GitHub={len(github_results)}, Wikipedia={len(wikipedia_results)}, News={len(news_results)}, Tor={len(tor_results)}")
            
            # Fase 2: AGREGAÇÃO UNIFICADA de TODAS as fontes
            unified_response = await aggregator.aggregate_all_sources(
                query=query,
                web_results=web_results,
                news_results=news_results,
                wikipedia_results=wikipedia_results,
                github_results=github_results,
                reddit_results=reddit_results,
                tor_results=tor_results
            )
            
            # Adicionar estatísticas de processamento
            processing_time = time.time() - start_time
            unified_response["processing_stats"] = {
                "total_search_time": processing_time,
                "parallel_searches": len(search_tasks),
                "sources_success": len([r for r in search_results if not isinstance(r, Exception)]),
                "sources_failed": len([r for r in search_results if isinstance(r, Exception)])
            }
            
            # Salvar resposta unificada em cache
            await self.cache.set(cache_key, unified_response)
            
            # Métricas
            metrics.increment_search_count()
            metrics.record_processing_time(processing_time)
            
            logger.info(f"✅ Busca unificada concluída em {processing_time:.2f}s - {unified_response['total']} resultados únicos")
            return unified_response
            
        except Exception as e:
            logger.error(f"❌ Erro na busca unificada: {str(e)}")
            metrics.increment_error_count()
            
            # Retornar resposta de erro estruturada
            return {
                "query": query,
                "total": 0,
                "data": [],
                "summary": f"Erro durante a busca: {str(e)}",
                "error": str(e),
                "generated_at": time.time()
            }
    
    async def _multi_source_search(self, query: str, sources: Optional[List[str]]) -> List[SearchResult]:
        """Busca em múltiplas fontes em paralelo"""
        tasks = []
        
        # Buscas web
        if not sources or 'web' in sources:
            tasks.append(self.web_search.search(query))
            tasks.append(self.bing_search.search(query))
        
        # Redes sociais
        if not sources or 'social' in sources:
            tasks.append(self.reddit_collector.search(query))
            tasks.append(self.github_collector.search(query))
        
        # Bases de conhecimento
        if not sources or 'knowledge' in sources:
            tasks.append(self.wikipedia_collector.search(query))
            tasks.append(self.wikidata_collector.search(query))
        
        # Notícias
        if not sources or 'news' in sources:
            tasks.append(self.rss_collector.search(query))
            tasks.append(self.news_collector.search(query))
        
        # Tor/Deep Web
        if not sources or 'tor' in sources:
            tasks.append(self.onion_scraper.search(query))
        
        # Executar em paralelo
        results_lists = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combinar resultados
        combined = []
        for i, results in enumerate(results_lists):
            if isinstance(results, Exception):
                logger.warning(f"⚠️ Erro na fonte {i}: {str(results)}")
                continue
            if results:
                combined.extend(results)
        
        return combined
    
    async def _deep_scrape_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Scraping profundo dos resultados"""
        enriched = []
        
        for result in results:
            try:
                # Fazer scraping do conteúdo
                content = await self.crawler.scrape_url(result.url)
                
                # Adicionar conteúdo extraído
                if content:
                    result.extracted_data = result.extracted_data or {}
                    result.extracted_data['scraped_content'] = content[:10000]  # Limitar tamanho
                
                enriched.append(result)
                
            except Exception as e:
                logger.warning(f"⚠️ Erro scraping {result.url}: {str(e)}")
                enriched.append(result)
        
        return enriched
    
    async def _extract_all_data(self, results: List[SearchResult]) -> Dict[str, Any]:
        """Extração de dados estruturados"""
        extracted = {
            'emails': set(),
            'phones': set(),
            'names': set(),
            'links': set(),
            'keywords': set(),
            'entities': set()
        }
        
        for result in results:
            if result.extracted_data and 'scraped_content' in result.extracted_data:
                content = result.extracted_data['scraped_content']
                
                # Usar parser para extrair dados
                parsed = await self.parser.parse_content(content)
                
                # Adicionar aos conjuntos
                for key in extracted:
                    if key in parsed:
                        extracted[key].update(parsed[key])
        
        # Converter sets para lists
        return {k: list(v) for k, v in extracted.items()}
    
    async def _generate_ai_summary(self, query: str, results: List[SearchResult], 
                                  extracted_data: Dict[str, Any]) -> str:
        """Gera resumo com IA"""
        try:
            # Tentar usar LLM principal
            summary = await self.llm_service.generate_summary(query, results, extracted_data)
            if summary:
                return summary
        except Exception as e:
            logger.warning(f"⚠️ Erro LLM principal: {str(e)}")
        
        try:
            # Tentar summarizer
            summary = await self.summarizer.summarize_results(query, results)
            if summary:
                return summary
        except Exception as e:
            logger.warning(f"⚠️ Erro summarizer: {str(e)}")
        
        try:
            # Usar fallback
            return await self.fallback_ai.generate_summary(query, results)
        except Exception as e:
            logger.error(f"❌ Erro fallback IA: {str(e)}")
            return f"Análise de {len(results)} resultados para '{query}'. Dados extraídos: {extracted_data}"
    
    async def _rank_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Rankea resultados por relevância"""
        # Implementar algoritmo de ranking
        for result in results:
            # Calcular score baseado em múltiplos fatores
            score = 0.0
            
            # Relevância do título
            if result.title:
                score += len(result.title.split()) * 0.1
            
            # Dados extraídos
            if result.extracted_data:
                score += len(str(result.extracted_data)) * 0.001
            
            # Fonte confiabilidade
            source_scores = {
                'wikipedia': 0.9,
                'github': 0.8,
                'reddit': 0.6,
                'news': 0.7,
                'web': 0.5,
                'tor': 0.3
            }
            score += source_scores.get(result.source.lower(), 0.5)
            
            result.relevance_score = score
        
        # Ordenar por score
        return sorted(results, key=lambda x: x.relevance_score, reverse=True)
    
    def _get_sources_used(self, sources: Optional[List[str]]) -> List[str]:
        """Retorna lista de fontes utilizadas"""
        if sources:
            return sources
        return ['web', 'bing', 'reddit', 'github', 'wikipedia', 'wikidata', 'rss', 'news', 'tor']
