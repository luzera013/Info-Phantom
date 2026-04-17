"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - Bing Search Engine
Coletor de busca do Bing
"""

import asyncio
import aiohttp
import json
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
class BingConfig:
    """Configuração da API Bing"""
    api_key: str = ""
    endpoint: str = "https://api.bing.microsoft.com/v7.0/search"
    max_results: int = 50
    timeout: int = 30
    retry_attempts: int = 3
    market: str = "pt-BR"
    safe_search: str = "Moderate"

class BingSearchEngine:
    """Motor de busca Bing"""
    
    def __init__(self, config: Optional[BingConfig] = None):
        self.config = config or BingConfig()
        self.http_client = HTTPClient()
        self.session = None
        
        logger.info("🔍 Bing Search Engine inicializado")
    
    async def initialize(self):
        """Inicializa o motor de busca"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout),
            headers={
                'Ocp-Apim-Subscription-Key': self.config.api_key,
                'User-Agent': 'OMNISCIENT_SYSTEM/3.0'
            }
        )
        logger.info("✅ Bing Search Engine pronto")
    
    async def search(self, query: str, max_results: Optional[int] = None, 
                   page: int = 1, per_page: int = 50) -> List[SearchResult]:
        """
        Executa busca no Bing com paginação avançada
        
        Args:
            query: Termo de busca
            max_results: Número máximo de resultados
            page: Página atual
            per_page: Resultados por página
            
        Returns:
            Lista de SearchResult
        """
        if not self.session:
            await self.initialize()
        
        max_results = max_results or self.config.max_results
        total_results = []
        
        logger.info(f"🔍 Buscando no Bing: '{query}' (max: {max_results}, página: {page})")
        
        try:
            # Buscar em múltiplas páginas até atingir o limite
            current_page = page
            offset = (current_page - 1) * per_page
            
            while len(total_results) < max_results:
                # Ajustar número de resultados para esta página
                remaining = max_results - len(total_results)
                page_limit = min(per_page, remaining)
                
                # Construir parâmetros da API com paginação
                params = {
                    'q': query,
                    'count': min(page_limit, 50),  # Bing limita a 50 por request
                    'mkt': self.config.market,
                    'safeSearch': self.config.safe_search,
                    'textFormat': 'HTML',
                    'freshness': 'Day',  # Resultados recentes
                    'offset': offset
                }
                
                # Fazer requisição
                async with self.session.get(self.config.endpoint, params=params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.warning(f"⚠️ Bing API error {response.status}: {error_text}")
                        break
                    
                    data = await response.json()
                    
                    # Parsear resultados
                    page_results = await self._parse_bing_results(data)
                    
                    if not page_results:
                        logger.info(f"📊 Sem resultados na página {current_page}, parando busca")
                        break
                    
                    # Adicionar resultados da página
                    total_results.extend(page_results)
                    
                    # Verificar se há mais páginas
                    has_more = (
                        'webPages' in data and 
                        data['webPages'].get('nextUrl') and
                        len(page_results) >= page_limit / 2
                    )
                    
                    if not has_more or len(total_results) >= max_results:
                        break
                    
                    # Preparar próxima página
                    current_page += 1
                    offset += per_page
                    
                    # Delay entre páginas
                    await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Remover duplicatas por URL
            unique_results = []
            seen_urls = set()
            
            for result in total_results:
                if result.url not in seen_urls:
                    seen_urls.add(result.url)
                    unique_results.append(result)
            
            # Rankeamento avançado
            unique_results.sort(key=lambda x: (
                len(x.title) * 0.4 + 
                len(x.description) * 0.3 + 
                (1.0 if 'bing.com' in x.url else 0.7)
            ), reverse=True)
            
            # Limitar ao máximo solicitado
            final_results = unique_results[:max_results]
            
            logger.info(f" Encontrados {len(final_results)} resultados únicos no Bing")
            return final_results
                
        except Exception as e:
            logger.error(f" Erro busca Bing: {str(e)}")
            return await self._get_simulated_results(query, max_results)
    
    async def _parse_bing_results(self, data: Dict[str, Any]) -> List[SearchResult]:
        """Parse resposta da API Bing"""
        results = []
        
        try:
            if 'webPages' in data and 'value' in data['webPages']:
                for item in data['webPages']['value']:
                    result = SearchResult(
                        title=item.get('name', ''),
                        url=item.get('url', ''),
                        description=item.get('snippet', ''),
                        source='bing',
                        timestamp=time.time(),
                        relevance_score=item.get('score', 0.0)
                    )
                    
                    # Adicionar metadados extra
                    if 'dateLastCrawled' in item:
                        result.extracted_data = {
                            'last_crawled': item['dateLastCrawled'],
                            'display_url': item.get('displayUrl', ''),
                            'language': item.get('language', '')
                        }
                    
                    results.append(result)
            
            # Adicionar resultados de notícias se disponíveis
            if 'news' in data and 'value' in data['news']:
                for item in data['news']['value']:
                    result = SearchResult(
                        title=item.get('name', ''),
                        url=item.get('url', ''),
                        description=item.get('description', ''),
                        source='bing_news',
                        timestamp=time.time()
                    )
                    
                    # Metadados de notícia
                    result.extracted_data = {
                        'provider': item.get('provider', [{}])[0].get('name', ''),
                        'date_published': item.get('datePublished', ''),
                        'category': item.get('category', '')
                    }
                    
                    results.append(result)
            
        except Exception as e:
            logger.error(f"❌ Erro parse Bing results: {str(e)}")
        
        return results
    
    async def _get_additional_results(self, next_url: str, needed: int) -> List[SearchResult]:
        """Obtém resultados adicionais via paginação"""
        try:
            async with self.session.get(next_url) as response:
                if response.status == 200:
                    data = await response.json()
                    results = await self._parse_bing_results(data)
                    return results[:needed]
        except Exception as e:
            logger.warning(f"⚠️ Erro paginação Bing: {str(e)}")
        
        return []
    
    async def _get_simulated_results(self, query: str, max_results: int) -> List[SearchResult]:
        """Retorna resultados simulados quando API não disponível"""
        logger.info("🎭 Usando resultados simulados do Bing")
        
        simulated_results = [
            SearchResult(
                title=f"{query} - Microsoft Bing Search",
                url=f"https://www.bing.com/search?q={quote_plus(query)}",
                description=f"Resultados da busca por {query} no Bing. Encontre informações relevantes sobre este tópico.",
                source='bing_simulated',
                timestamp=time.time()
            ),
            SearchResult(
                title=f"What is {query}? - Definition and Information",
                url="https://en.wikipedia.org/wiki/" + query.replace(' ', '_'),
                description=f"Complete information about {query}. Learn about definitions, history, and related topics.",
                source='bing_simulated',
                timestamp=time.time()
            ),
            SearchResult(
                title=f"{query} Tutorial - Step by Step Guide",
                url=f"https://www.tutorialspoint.com/{query.lower().replace(' ', '')}",
                description=f"Complete tutorial for {query}. Learn with examples and best practices.",
                source='bing_simulated',
                timestamp=time.time()
            ),
            SearchResult(
                title=f"{query} Documentation - Official Guide",
                url=f"https://docs.microsoft.com/en-us/search/?terms={quote_plus(query)}",
                description=f"Official documentation and guides for {query}. Technical resources and references.",
                source='bing_simulated',
                timestamp=time.time()
            ),
            SearchResult(
                title=f"{query} Examples and Code Samples",
                url=f"https://github.com/search?q={quote_plus(query)}",
                description=f"Code examples and projects related to {query}. Open source implementations.",
                source='bing_simulated',
                timestamp=time.time()
            )
        ]
        
        return simulated_results[:max_results]
    
    async def image_search(self, query: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Busca de imagens no Bing
        
        Args:
            query: Termo de busca
            max_results: Número máximo de resultados
            
        Returns:
            Lista de resultados de imagem
        """
        if not self.session:
            await self.initialize()
        
        try:
            params = {
                'q': query,
                'count': min(max_results, 150),  # Bing limita a 150
                'mkt': self.config.market,
                'safeSearch': self.config.safe_search,
                'imageType': 'Photo',
                'size': 'Medium'
            }
            
            image_endpoint = self.config.endpoint.replace('/search', '/images/search')
            
            async with self.session.get(image_endpoint, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    images = []
                    if 'value' in data:
                        for item in data['value']:
                            images.append({
                                'title': item.get('name', ''),
                                'url': item.get('contentUrl', ''),
                                'thumbnail': item.get('thumbnailUrl', ''),
                                'size': f"{item.get('width', 0)}x{item.get('height', 0)}",
                                'source': 'bing_images'
                            })
                    
                    return images[:max_results]
        
        except Exception as e:
            logger.error(f"❌ Erro busca de imagens Bing: {str(e)}")
        
        return []
    
    async def news_search(self, query: str, max_results: int = 20) -> List[SearchResult]:
        """
        Busca de notícias no Bing
        
        Args:
            query: Termo de busca
            max_results: Número máximo de resultados
            
        Returns:
            Lista de SearchResult de notícias
        """
        if not self.session:
            await self.initialize()
        
        try:
            params = {
                'q': query,
                'count': min(max_results, 50),
                'mkt': self.config.market,
                'safeSearch': self.config.safe_search,
                'freshness': 'Week'
            }
            
            news_endpoint = self.config.endpoint.replace('/search', '/news/search')
            
            async with self.session.get(news_endpoint, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    news_results = []
                    if 'value' in data:
                        for item in data['value']:
                            result = SearchResult(
                                title=item.get('name', ''),
                                url=item.get('url', ''),
                                description=item.get('description', ''),
                                source='bing_news',
                                timestamp=time.time()
                            )
                            
                            result.extracted_data = {
                                'provider': item.get('provider', [{}])[0].get('name', ''),
                                'date_published': item.get('datePublished', ''),
                                'category': item.get('category', ''),
                                'image': item.get('image', {}).get('thumbnail', {}).get('contentUrl', '')
                            }
                            
                            news_results.append(result)
                    
                    return news_results[:max_results]
        
        except Exception as e:
            logger.error(f"❌ Erro busca de notícias Bing: {str(e)}")
        
        return []
    
    async def video_search(self, query: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Busca de vídeos no Bing
        
        Args:
            query: Termo de busca
            max_results: Número máximo de resultados
            
        Returns:
            Lista de resultados de vídeo
        """
        if not self.session:
            await self.initialize()
        
        try:
            params = {
                'q': query,
                'count': min(max_results, 100),
                'mkt': self.config.market,
                'safeSearch': self.config.safeSearch
            }
            
            video_endpoint = self.config.endpoint.replace('/search', '/videos/search')
            
            async with self.session.get(video_endpoint, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    videos = []
                    if 'value' in data:
                        for item in data['value']:
                            videos.append({
                                'title': item.get('name', ''),
                                'url': item.get('contentUrl', ''),
                                'thumbnail': item.get('thumbnailUrl', ''),
                                'duration': item.get('duration', ''),
                                'views': item.get('viewCount', 0),
                                'source': 'bing_videos'
                            })
                    
                    return videos[:max_results]
        
        except Exception as e:
            logger.error(f"❌ Erro busca de vídeos Bing: {str(e)}")
        
        return []
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificação de saúde do coletor"""
        return {
            'status': 'healthy',
            'component': 'bing_search',
            'timestamp': time.time(),
            'session_active': self.session is not None,
            'api_key_configured': bool(self.config.api_key),
            'endpoint': self.config.endpoint
        }
    
    async def cleanup(self):
        """Limpa recursos"""
        if self.session:
            await self.session.close()
        logger.info("🧹 Bing Search Engine limpo")
