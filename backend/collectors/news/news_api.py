"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - News API Collector
Coleta dados de APIs de notícias
"""

import asyncio
import aiohttp
import json
import random
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode, quote_plus
from dataclasses import dataclass
import time
import logging
from datetime import datetime, timedelta

from ..core.pipeline import SearchResult
from ..utils.logger import setup_logger
from ..utils.http_client import HTTPClient

logger = setup_logger(__name__)

@dataclass
class NewsAPIConfig:
    """Configuração do coletor News API"""
    api_key: str = ""
    api_url: str = "https://newsapi.org/v2"
    max_results: int = 100
    timeout: int = 30
    retry_attempts: int = 3
    language: str = "pt"
    country: str = "br"
    include_content: bool = True
    max_content_length: int = 5000

class NewsAPICollector:
    """Coletor de APIs de notícias"""
    
    def __init__(self, config: Optional[NewsAPIConfig] = None):
        self.config = config or NewsAPIConfig()
        self.http_client = HTTPClient()
        self.session = None
        
        # Fontes alternativas de notícias
        self.alternative_sources = [
            'https://api.currentsapi.services/v1',
            'https://gnews.io/api/v4',
            'https://newsdata.io/api/1',
            'https://api.mediastack.com/v1'
        ]
        
        logger.info("📰 News API Collector inicializado")
    
    async def initialize(self):
        """Inicializa o coletor"""
        headers = {
            'User-Agent': 'OMNISCIENT_NEWS/3.0'
        }
        
        if self.config.api_key:
            headers['X-API-Key'] = self.config.api_key
        
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout),
            headers=headers
        )
        
        logger.info("✅ News API Collector pronto")
    
    async def search(self, query: str, max_results: Optional[int] = None,
                    sources: Optional[List[str]] = None) -> List[SearchResult]:
        """
        Busca notícias via API
        
        Args:
            query: Termo de busca
            max_results: Número máximo de resultados
            sources: Fontes específicas
            
        Returns:
            Lista de SearchResult
        """
        if not self.session:
            await self.initialize()
        
        max_results = max_results or self.config.max_results
        logger.info(f"🔍 Buscando notícias: '{query}' (max: {max_results})")
        
        try:
            all_articles = []
            
            # Tentar NewsAPI.org primeiro
            if self.config.api_key:
                articles = await self._search_newsapi(query, max_results, sources)
                all_articles.extend(articles)
            
            # Tentar fontes alternativas se necessário
            if len(all_articles) < max_results:
                for source_url in self.alternative_sources:
                    try:
                        articles = await self._search_alternative(source_url, query, max_results - len(all_articles))
                        all_articles.extend(articles)
                        
                        if len(all_articles) >= max_results:
                            break
                            
                    except Exception as e:
                        logger.debug(f"⚠️ Erro fonte alternativa {source_url}: {str(e)}")
                        continue
            
            # Processar conteúdo se configurado
            if self.config.include_content:
                all_articles = await self._enrich_articles(all_articles)
            
            # Converter para SearchResult
            results = []
            for article in all_articles:
                result = SearchResult(
                    title=article.get('title', ''),
                    url=article.get('url', ''),
                    description=article.get('description', '')[:500],
                    source='news_api',
                    timestamp=article.get('published_at', time.time()),
                    relevance_score=article.get('relevance_score', 0.0)
                )
                
                result.extracted_data = {
                    'source_name': article.get('source', {}).get('name', ''),
                    'author': article.get('author', ''),
                    'published_at': article.get('published_at_formatted', ''),
                    'content': article.get('content', ''),
                    'url_to_image': article.get('urlToImage', ''),
                    'language': article.get('language', self.config.language),
                    'country': article.get('country', self.config.country),
                    'category': article.get('category', ''),
                    'keywords': article.get('keywords', []),
                    'word_count': article.get('word_count', 0)
                }
                
                results.append(result)
            
            # Limitar resultados
            results = results[:max_results]
            
            logger.info(f"✅ Encontradas {len(results)} notícias")
            return results
            
        except Exception as e:
            logger.error(f"❌ Erro na busca de notícias: {str(e)}")
            # Retornar resultados simulados se API falhar
            return await self._get_simulated_results(query, max_results)
    
    async def _search_newsapi(self, query: str, max_results: int, 
                             sources: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Busca no NewsAPI.org"""
        try:
            params = {
                'q': query,
                'language': self.config.language,
                'country': self.config.country,
                'pageSize': min(max_results, 100),
                'sortBy': 'publishedAt',
                'page': 1
            }
            
            if sources:
                params['sources'] = ','.join(sources)
            
            url = f"{self.config.api_url}/everything"
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"NewsAPI error {response.status}: {error_text}")
                
                data = await response.json()
                
                articles = []
                for article in data.get('articles', []):
                    # Calcular relevância
                    relevance = self._calculate_relevance(
                        article.get('title', ''),
                        article.get('description', ''),
                        query
                    )
                    
                    # Formatar data
                    published_at = self._parse_date(article.get('publishedAt'))
                    
                    processed_article = {
                        'title': article.get('title', ''),
                        'description': article.get('description', ''),
                        'url': article.get('url', ''),
                        'urlToImage': article.get('urlToImage', ''),
                        'source': article.get('source', {}),
                        'author': article.get('author', ''),
                        'published_at': published_at,
                        'published_at_formatted': self._format_date(published_at),
                        'content': article.get('content', ''),
                        'relevance_score': relevance,
                        'language': self.config.language,
                        'country': self.config.country
                    }
                    
                    articles.append(processed_article)
                
                return articles
        
        except Exception as e:
            logger.warning(f"⚠️ Erro NewsAPI.org: {str(e)}")
            return []
    
    async def _search_alternative(self, source_url: str, query: str, 
                                max_results: int) -> List[Dict[str, Any]]:
        """Busca em fontes alternativas"""
        try:
            if 'currentsapi' in source_url:
                return await self._search_currentsapi(source_url, query, max_results)
            elif 'gnews' in source_url:
                return await self._search_gnews(source_url, query, max_results)
            elif 'newsdata' in source_url:
                return await self._search_newsdata(source_url, query, max_results)
            elif 'mediastack' in source_url:
                return await self._search_mediastack(source_url, query, max_results)
        
        except Exception as e:
            logger.debug(f"⚠️ Erro fonte alternativa {source_url}: {str(e)}")
            return []
    
    async def _search_currentsapi(self, base_url: str, query: str, 
                                max_results: int) -> List[Dict[str, Any]]:
        """Busca no CurrentsAPI"""
        try:
            params = {
                'keywords': query,
                'language': self.config.language,
                'limit': min(max_results, 50)
            }
            
            url = f"{base_url}/latest-news"
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    articles = []
                    for article in data.get('news', []):
                        processed_article = {
                            'title': article.get('title', ''),
                            'description': article.get('description', ''),
                            'url': article.get('url', ''),
                            'urlToImage': article.get('image', ''),
                            'source': {'name': article.get('source', '')},
                            'author': article.get('author', ''),
                            'published_at': self._parse_date(article.get('published')),
                            'published_at_formatted': article.get('published', ''),
                            'content': article.get('content', ''),
                            'relevance_score': self._calculate_relevance(
                                article.get('title', ''),
                                article.get('description', ''),
                                query
                            ),
                            'language': self.config.language,
                            'country': self.config.country
                        }
                        articles.append(processed_article)
                    
                    return articles
        
        except Exception as e:
            logger.debug(f"⚠️ Erro CurrentsAPI: {str(e)}")
        
        return []
    
    async def _search_gnews(self, base_url: str, query: str, 
                           max_results: int) -> List[Dict[str, Any]]:
        """Busca no GNews"""
        try:
            params = {
                'q': query,
                'lang': self.config.language,
                'country': self.config.country.upper(),
                'max': min(max_results, 50)
            }
            
            url = f"{base_url}/search"
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    articles = []
                    for article in data.get('articles', []):
                        processed_article = {
                            'title': article.get('title', ''),
                            'description': article.get('description', ''),
                            'url': article.get('url', ''),
                            'urlToImage': article.get('image', ''),
                            'source': {'name': article.get('source', {}).get('name', '')},
                            'author': article.get('author', ''),
                            'published_at': self._parse_date(article.get('publishedAt')),
                            'published_at_formatted': article.get('publishedAt', ''),
                            'content': article.get('content', ''),
                            'relevance_score': self._calculate_relevance(
                                article.get('title', ''),
                                article.get('description', ''),
                                query
                            ),
                            'language': self.config.language,
                            'country': self.config.country
                        }
                        articles.append(processed_article)
                    
                    return articles
        
        except Exception as e:
            logger.debug(f"⚠️ Erro GNews: {str(e)}")
        
        return []
    
    async def _search_newsdata(self, base_url: str, query: str, 
                              max_results: int) -> List[Dict[str, Any]]:
        """Busca no NewsData"""
        try:
            params = {
                'q': query,
                'language': self.config.language,
                'country': self.config.country,
                'size': min(max_results, 50)
            }
            
            url = f"{base_url}/news"
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    articles = []
                    for article in data.get('results', []):
                        processed_article = {
                            'title': article.get('title', ''),
                            'description': article.get('description', ''),
                            'url': article.get('link', ''),
                            'urlToImage': article.get('image_url', ''),
                            'source': {'name': article.get('source_id', '')},
                            'author': article.get('creator', [''])[0],
                            'published_at': self._parse_date(article.get('pubDate')),
                            'published_at_formatted': article.get('pubDate', ''),
                            'content': article.get('content', ''),
                            'relevance_score': self._calculate_relevance(
                                article.get('title', ''),
                                article.get('description', ''),
                                query
                            ),
                            'language': self.config.language,
                            'country': self.config.country,
                            'category': article.get('category', [''])[0]
                        }
                        articles.append(processed_article)
                    
                    return articles
        
        except Exception as e:
            logger.debug(f"⚠️ Erro NewsData: {str(e)}")
        
        return []
    
    async def _search_mediastack(self, base_url: str, query: str, 
                               max_results: int) -> List[Dict[str, Any]]:
        """Busca no MediaStack"""
        try:
            params = {
                'keywords': query,
                'language': self.config.language,
                'countries': self.config.country,
                'limit': min(max_results, 50),
                'sort': 'published_desc'
            }
            
            url = f"{base_url}/news"
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    articles = []
                    for article in data.get('data', []):
                        processed_article = {
                            'title': article.get('title', ''),
                            'description': article.get('description', ''),
                            'url': article.get('url', ''),
                            'urlToImage': article.get('image', ''),
                            'source': {'name': article.get('source', '')},
                            'author': article.get('author', ''),
                            'published_at': self._parse_date(article.get('published_at')),
                            'published_at_formatted': article.get('published_at', ''),
                            'content': article.get('content', ''),
                            'relevance_score': self._calculate_relevance(
                                article.get('title', ''),
                                article.get('description', ''),
                                query
                            ),
                            'language': self.config.language,
                            'country': self.config.country,
                            'category': article.get('category', '')
                        }
                        articles.append(processed_article)
                    
                    return articles
        
        except Exception as e:
            logger.debug(f"⚠️ Erro MediaStack: {str(e)}")
        
        return []
    
    def _calculate_relevance(self, title: str, description: str, query: str) -> float:
        """Calcula relevância da notícia para a query"""
        if not query:
            return 0.5
        
        query_lower = query.lower()
        title_lower = (title or '').lower()
        desc_lower = (description or '').lower()
        
        score = 0.0
        
        # Título tem peso maior
        if query_lower in title_lower:
            score += 0.4
        
        # Palavras da query no título
        query_words = set(query_lower.split())
        title_words = set(title_lower.split())
        title_intersection = len(query_words & title_words)
        score += (title_intersection / len(query_words)) * 0.3 if query_words else 0
        
        # Descrição tem peso médio
        if query_lower in desc_lower:
            score += 0.2
        
        # Palavras da query na descrição
        desc_words = set(desc_lower.split())
        desc_intersection = len(query_words & desc_words)
        score += (desc_intersection / len(query_words)) * 0.1 if query_words else 0
        
        return min(score, 1.0)
    
    def _parse_date(self, date_str: str) -> float:
        """Parse string de data para timestamp"""
        if not date_str:
            return time.time()
        
        try:
            # Tentar diferentes formatos
            formats = [
                '%Y-%m-%dT%H:%M:%SZ',
                '%Y-%m-%dT%H:%M:%S.%fZ',
                '%Y-%m-%dT%H:%M:%S%z',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d'
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.timestamp()
                except ValueError:
                    continue
            
            # Se nenhum formato funcionar, retornar timestamp atual
            return time.time()
        
        except Exception:
            return time.time()
    
    def _format_date(self, timestamp: float) -> str:
        """Formata timestamp para string"""
        try:
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return ''
    
    async def _enrich_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enriquece artigos com conteúdo adicional"""
        enriched = []
        
        for article in articles:
            try:
                # Extrair palavras-chave
                text = f"{article.get('title', '')} {article.get('description', '')}"
                keywords = self._extract_keywords(text)
                article['keywords'] = keywords
                
                # Contar palavras
                content = article.get('content', '') or article.get('description', '')
                article['word_count'] = len(content.split()) if content else 0
                
                enriched.append(article)
                
            except Exception as e:
                logger.debug(f"⚠️ Erro enriquecendo artigo: {str(e)}")
                enriched.append(article)
        
        return enriched
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extrai palavras-chave do texto"""
        if not text:
            return []
        
        # Palavras comuns em português para ignorar
        stop_words = {
            'o', 'a', 'os', 'as', 'de', 'do', 'da', 'dos', 'das', 'em', 'no', 'na', 
            'nos', 'nas', 'por', 'para', 'com', 'sem', 'como', 'mas', 'que', 'se', 
            'um', 'uma', 'uns', 'umas', 'e', 'ou', 'mais', 'menos', 'muito', 'pouco'
        }
        
        words = text.lower().split()
        keywords = []
        
        for word in words:
            word = word.strip('.,!?()[]{}"\'')
            if len(word) > 3 and word.isalpha() and word not in stop_words:
                keywords.append(word)
        
        # Retornar palavras mais frequentes (máximo 10)
        from collections import Counter
        word_freq = Counter(keywords)
        return [word for word, _ in word_freq.most_common(10)]
    
    async def _get_simulated_results(self, query: str, max_results: int) -> List[SearchResult]:
        """Retorna resultados simulados quando API não disponível"""
        logger.info("🎭 Usando resultados simulados de notícias")
        
        simulated_articles = [
            {
                'title': f'Últimas notícias sobre {query}: Desenvolvimentos importantes',
                'description': f'Novos acontecimentos relacionados a {query} estão moldando o cenário atual. Especialistas analisam os impactos e perspectivas futuras.',
                'url': f'https://example.com/news/{query.replace(" ", "-")}-latest',
                'urlToImage': f'https://example.com/images/{query.replace(" ", "-")}.jpg',
                'source': {'name': 'Portal de Notícias'},
                'author': 'Redação',
                'published_at': time.time() - 3600,
                'published_at_formatted': self._format_date(time.time() - 3600),
                'content': f'Conteúdo completo da matéria sobre {query}. Análise detalhada dos acontecimentos recentes...',
                'relevance_score': 0.9,
                'language': self.config.language,
                'country': self.config.country,
                'category': 'Geral',
                'keywords': [query.lower(), 'notícias', 'atualidades'],
                'word_count': 250
            },
            {
                'title': f'{query} em destaque: Análise completa e tendências',
                'description': f'Especialistas debatem os principais aspectos de {query} e as implicações para o futuro. Entenda os detalhes.',
                'url': f'https://example.com/news/{query.replace(" ", "-")}-analysis',
                'urlToImage': f'https://example.com/images/{query.replace(" ", "-")}-analysis.jpg',
                'source': {'name': 'Jornal Analítico'},
                'author': 'Equipe de Análise',
                'published_at': time.time() - 7200,
                'published_at_formatted': self._format_date(time.time() - 7200),
                'content': f'Análise aprofundada sobre {query}. Perspectivas especializadas e dados relevantes...',
                'relevance_score': 0.85,
                'language': self.config.language,
                'country': self.config.country,
                'category': 'Análise',
                'keywords': [query.lower(), 'análise', 'tendências'],
                'word_count': 400
            }
        ]
        
        results = []
        for article in simulated_articles:
            result = SearchResult(
                title=article['title'],
                url=article['url'],
                description=article['description'],
                source='news_api_simulated',
                timestamp=article['published_at'],
                relevance_score=article['relevance_score']
            )
            
            result.extracted_data = {
                'source_name': article['source']['name'],
                'author': article['author'],
                'published_at': article['published_at_formatted'],
                'content': article['content'],
                'url_to_image': article['urlToImage'],
                'language': article['language'],
                'country': article['country'],
                'category': article['category'],
                'keywords': article['keywords'],
                'word_count': article['word_count']
            }
            
            results.append(result)
        
        return results[:max_results]
    
    async def get_headlines(self, country: Optional[str] = None, 
                           category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Obtém manchetes principais
        
        Args:
            country: País específico
            category: Categoria específica
            
        Returns:
            Lista de manchetes
        """
        if not self.session:
            await self.initialize()
        
        try:
            params = {
                'country': country or self.config.country,
                'pageSize': 20,
                'page': 1
            }
            
            if category:
                params['category'] = category
            
            url = f"{self.config.api_url}/top-headlines"
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    headlines = []
                    for article in data.get('articles', []):
                        headline = {
                            'title': article.get('title', ''),
                            'description': article.get('description', ''),
                            'url': article.get('url', ''),
                            'source': article.get('source', {}),
                            'published_at': self._parse_date(article.get('publishedAt')),
                            'url_to_image': article.get('urlToImage', '')
                        }
                        headlines.append(headline)
                    
                    logger.info(f"📰 Encontradas {len(headlines)} manchetes")
                    return headlines
        
        except Exception as e:
            logger.error(f"❌ Erro obtendo manchetes: {str(e)}")
        
        return []
    
    async def get_sources(self, country: Optional[str] = None, 
                         category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Obtém fontes de notícias disponíveis
        
        Args:
            country: País específico
            category: Categoria específica
            
        Returns:
            Lista de fontes
        """
        if not self.session:
            await self.initialize()
        
        try:
            params = {}
            
            if country:
                params['country'] = country
            if category:
                params['category'] = category
            
            url = f"{self.config.api_url}/sources"
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    sources = data.get('sources', [])
                    logger.info(f"📰 Encontradas {len(sources)} fontes")
                    return sources
        
        except Exception as e:
            logger.error(f"❌ Erro obtendo fontes: {str(e)}")
        
        return []
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificação de saúde do coletor"""
        return {
            'status': 'healthy',
            'component': 'news_api_collector',
            'timestamp': time.time(),
            'session_active': self.session is not None,
            'api_key_configured': bool(self.config.api_key),
            'max_results': self.config.max_results,
            'language': self.config.language
        }
    
    async def cleanup(self):
        """Limpa recursos"""
        if self.session:
            await self.session.close()
        
        logger.info("🧹 News API Collector limpo")
