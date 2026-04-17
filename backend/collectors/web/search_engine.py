"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - Web Search Engine
Coletor de busca web genérico (Google-like)
"""

import asyncio
import aiohttp
import random
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode, quote_plus
from dataclasses import dataclass
import time
import logging

from ..core.pipeline import SearchResult
from ..utils.logger import setup_logger
from ..utils.http_client import HTTPClient

logger = setup_logger(__name__)

@dataclass
class SearchConfig:
    """Configuração de busca web"""
    max_results: int = 50
    timeout: int = 30
    retry_attempts: int = 3
    delay_range: tuple = (1, 3)  # Delay entre requisições
    user_agents: List[str] = None
    
    def __post_init__(self):
        if self.user_agents is None:
            self.user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            ]

class WebSearchEngine:
    """Motor de busca web genérico"""
    
    def __init__(self, config: Optional[SearchConfig] = None):
        self.config = config or SearchConfig()
        self.http_client = HTTPClient()
        self.session = None
        
        # URLs de busca (simuladas - em produção usar APIs reais)
        self.search_endpoints = [
            'https://duckduckgo.com/html/',
            'https://html.duckduckgo.com/html/',
            'https://startpage.com/do/search',
            'https://search.brave.com/search'
        ]
        
        logger.info("🔍 Web Search Engine inicializado")
    
    async def initialize(self):
        """Inicializa o motor de busca"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout),
            headers={'User-Agent': random.choice(self.config.user_agents)}
        )
        logger.info("✅ Web Search Engine pronto")
    
    async def search(self, query: str, max_results: Optional[int] = None, 
                   page: int = 1, per_page: int = 50) -> List[SearchResult]:
        """
        Executa busca web com paginação
        
        Args:
            query: Termo de busca
            max_results: Número máximo de resultados
            page: Página atual (para paginação)
            per_page: Resultados por página
            
        Returns:
            Lista de SearchResult
        """
        if not self.session:
            await self.initialize()
        
        max_results = max_results or self.config.max_results
        total_results = []
        
        logger.info(f"🔍 Buscando na web: '{query}' (max: {max_results}, página: {page})")
        
        try:
            # Buscar em múltiplas páginas até atingir o limite
            current_page = page
            while len(total_results) < max_results:
                # Ajustar número de resultados para esta página
                remaining = max_results - len(total_results)
                page_limit = min(per_page, remaining)
                
                # Buscar em múltiplos endpoints em paralelo
                page_tasks = []
                for endpoint in self.search_endpoints:
                    task = self._search_endpoint_paged(
                        endpoint, query, page_limit, current_page
                    )
                    page_tasks.append(task)
                
                # Executar buscas da página atual em paralelo
                page_results = await asyncio.gather(*page_tasks, return_exceptions=True)
                
                # Combinar resultados da página
                page_combined = []
                for result in page_results:
                    if isinstance(result, Exception):
                        logger.warning(f"⚠️ Erro no endpoint: {str(result)}")
                        continue
                    if result:
                        page_combined.extend(result)
                
                # Adicionar resultados totais
                total_results.extend(page_combined[:page_limit])
                
                # Verificar se encontrou resultados suficientes
                if len(page_combined) < page_limit / 2:
                    logger.info(f"📊 Poucos resultados na página {current_page}, parando busca")
                    break
                
                current_page += 1
                
                # Delay entre páginas
                await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Remover duplicatas e ordenar por relevância
            unique_results = []
            seen_urls = set()
            
            for result in total_results:
                if result.url not in seen_urls:
                    seen_urls.add(result.url)
                    unique_results.append(result)
            
            # Rankeamento básico por URL e título
            unique_results.sort(key=lambda x: (
                len(x.title) * 0.3 + 
                len(x.description) * 0.2 + 
                (1.0 if 'http' in x.url else 0.5)
            ), reverse=True)
            
            # Limitar ao máximo solicitado
            final_results = unique_results[:max_results]
            
            logger.info(f"✅ Encontrados {len(final_results)} resultados únicos na web")
            return final_results
            
        except Exception as e:
            logger.error(f"❌ Erro na busca web: {str(e)}")
            return []
    
    async def _search_endpoint_paged(self, endpoint: str, query: str, 
                                  max_results: int, page: int) -> List[SearchResult]:
        """
        Busca em endpoint específico com suporte a paginação
        """
        params = self._build_search_params_paged(query, max_results, page)
        
        for attempt in range(self.config.retry_attempts):
            try:
                async with self.session.get(endpoint, params=params) as response:
                    if response.status != 200:
                        raise Exception(f"HTTP {response.status}")
                    
                    html_content = await response.text()
                    
                    # Parsear resultados
                    results = await self._parse_search_results(html_content, endpoint)
                    
                    if results:
                        logger.debug(f"📊 Página {page}: {len(results)} resultados de {endpoint}")
                        return results
                    
            except Exception as e:
                logger.warning(f"⚠️ Tentativa {attempt + 1} falhou: {str(e)}")
                if attempt < self.config.retry_attempts - 1:
                    await asyncio.sleep(random.uniform(2, 5))
        
        return []
    
    def _build_search_params_paged(self, query: str, max_results: int, page: int) -> Dict[str, str]:
        """
        Constrói parâmetros de busca com paginação
        """
        params = {
            'q': query,
            'kl': 'br-pt'
        }
        
        # Adicionar parâmetros de paginação
        if 'duckduckgo' in self.search_endpoints[0]:
            params.update({
                'kl': 'br-pt',
                'num': str(max_results),
                's': str((page - 1) * max_results + 1)  # Start result
            })
        elif 'startpage' in self.search_endpoints[0]:
            params.update({
                'query': query,
                'cat': 'web',
                'pl': 'ext-ff',
                'extVersion': '1.3.0',
                'page': str(page),
                'count': str(max_results)
            })
        elif 'brave' in self.search_endpoints[0]:
            params.update({
                'source': 'web',
                'count': str(max_results),
                'offset': str((page - 1) * max_results)
            })
        
        return params
    
    async def _search_endpoint(self, endpoint: str, query: str, max_results: int) -> List[SearchResult]:
        """Busca em endpoint específico"""
        params = self._build_search_params(query, max_results)
        
        for attempt in range(self.config.retry_attempts):
            try:
                # Fazer requisição
                async with self.session.get(endpoint, params=params) as response:
                    if response.status != 200:
                        raise Exception(f"HTTP {response.status}")
                    
                    html_content = await response.text()
                    
                    # Parsear resultados
                    results = await self._parse_search_results(html_content, endpoint)
                    
                    if results:
                        logger.debug(f"📊 {len(results)} resultados de {endpoint}")
                        return results
                    
            except Exception as e:
                logger.warning(f"⚠️ Tentativa {attempt + 1} falhou: {str(e)}")
                if attempt < self.config.retry_attempts - 1:
                    await asyncio.sleep(random.uniform(2, 5))
        
        return []
    
    def _build_search_params(self, query: str, max_results: int) -> Dict[str, str]:
        """Constrói parâmetros de busca"""
        params = {
            'q': query,
            'kl': 'br-pt',  # Português Brasil
        }
        
        # Parâmetros específicos por endpoint
        if 'duckduckgo' in self.search_endpoints[0]:
            params.update({
                'kl': 'br-pt',
                'num': str(max_results)
            })
        elif 'startpage' in self.search_endpoints[0]:
            params.update({
                'query': query,
                'cat': 'web',
                'pl': 'ext-ff',
                'extVersion': '1.3.0'
            })
        elif 'brave' in self.search_endpoints[0]:
            params.update({
                'source': 'web',
                'count': str(max_results)
            })
        
        return params
    
    async def _parse_search_results(self, html_content: str, source: str) -> List[SearchResult]:
        """Parse HTML para extrair resultados"""
        from bs4 import BeautifulSoup
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            results = []
            
            # Seletores diferentes para cada motor
            if 'duckduckgo' in source:
                results.extend(self._parse_duckduckgo(soup))
            elif 'startpage' in source:
                results.extend(self._parse_startpage(soup))
            elif 'brave' in source:
                results.extend(self._parse_brave(soup))
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Erro no parse HTML: {str(e)}")
            return []
    
    def _parse_duckduckgo(self, soup) -> List[SearchResult]:
        """Parse resultados DuckDuckGo"""
        results = []
        
        # DuckDuckGo usa classe .result
        for result in soup.find_all('div', class_='result'):
            try:
                title_elem = result.find('a', class_='result__a')
                snippet_elem = result.find('a', class_='result__snippet')
                
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    url = title_elem.get('href', '')
                    description = snippet_elem.get_text(strip=True) if snippet_elem else ''
                    
                    results.append(SearchResult(
                        title=title,
                        url=url,
                        description=description,
                        source='duckduckgo',
                        timestamp=time.time()
                    ))
                    
            except Exception as e:
                logger.debug(f"⚠️ Erro parse resultado DDG: {str(e)}")
                continue
        
        return results
    
    def _parse_startpage(self, soup) -> List[SearchResult]:
        """Parse resultados StartPage"""
        results = []
        
        # StartPage usa w-gl__result
        for result in soup.find_all('div', class_='w-gl__result'):
            try:
                title_elem = result.find('h3')
                link_elem = result.find('a', class_='w-gl__result-title')
                desc_elem = result.find('p', class_='w-gl__description')
                
                if title_elem and link_elem:
                    title = title_elem.get_text(strip=True)
                    url = link_elem.get('href', '')
                    description = desc_elem.get_text(strip=True) if desc_elem else ''
                    
                    results.append(SearchResult(
                        title=title,
                        url=url,
                        description=description,
                        source='startpage',
                        timestamp=time.time()
                    ))
                    
            except Exception as e:
                logger.debug(f"⚠️ Erro parse resultado StartPage: {str(e)}")
                continue
        
        return results
    
    def _parse_brave(self, soup) -> List[SearchResult]:
        """Parse resultados Brave Search"""
        results = []
        
        # Brave usa .web-result
        for result in soup.find_all('div', class_='web-result'):
            try:
                title_elem = result.find('h3')
                link_elem = result.find('a')
                desc_elem = result.find('div', class_='snippet')
                
                if title_elem and link_elem:
                    title = title_elem.get_text(strip=True)
                    url = link_elem.get('href', '')
                    description = desc_elem.get_text(strip=True) if desc_elem else ''
                    
                    results.append(SearchResult(
                        title=title,
                        url=url,
                        description=description,
                        source='brave',
                        timestamp=time.time()
                    ))
                    
            except Exception as e:
                logger.debug(f"⚠️ Erro parse resultado Brave: {str(e)}")
                continue
        
        return results
    
    async def advanced_search(self, query: str, filters: Dict[str, Any] = None) -> List[SearchResult]:
        """
        Busca avançada com filtros
        
        Args:
            query: Termo de busca
            filters: Filtros (site, filetype, date_range, etc.)
            
        Returns:
            Lista de SearchResult
        """
        if not filters:
            return await self.search(query)
        
        # Construir query com filtros
        advanced_query = query
        
        if filters.get('site'):
            advanced_query += f" site:{filters['site']}"
        
        if filters.get('filetype'):
            advanced_query += f" filetype:{filters['filetype']}"
        
        if filters.get('intitle'):
            advanced_query += f" intitle:{filters['intitle']}"
        
        if filters.get('inurl'):
            advanced_query += f" inurl:{filters['inurl']}"
        
        logger.info(f"🔍 Busca avançada: '{advanced_query}'")
        return await self.search(advanced_query)
    
    async def get_suggestions(self, partial_query: str) -> List[str]:
        """
        Obtém sugestões de autocomplete
        
        Args:
            partial_query: Query parcial
            
        Returns:
            Lista de sugestões
        """
        # Simular sugestões (em produção usar API real)
        suggestions = [
            f"{partial_query} tutorial",
            f"{partial_query} guide",
            f"{partial_query} examples",
            f"{partial_query} documentation",
            f"{partial_query} best practices"
        ]
        
        return random.sample(suggestions, min(3, len(suggestions)))
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificação de saúde do coletor"""
        return {
            'status': 'healthy',
            'component': 'web_search',
            'timestamp': time.time(),
            'session_active': self.session is not None,
            'endpoints_count': len(self.search_endpoints),
            'max_results': self.config.max_results
        }
    
    async def cleanup(self):
        """Limpa recursos"""
        if self.session:
            await self.session.close()
        logger.info("🧹 Web Search Engine limpo")
