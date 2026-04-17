"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - RSS Collector
Coleta dados de feeds RSS
"""

import asyncio
import aiohttp
import feedparser
import random
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass
import time
import logging
from datetime import datetime, timedelta

from ..core.pipeline import SearchResult
from ..utils.logger import setup_logger
from ..utils.http_client import HTTPClient

logger = setup_logger(__name__)

@dataclass
class RSSConfig:
    """Configuração do coletor RSS"""
    max_results: int = 100
    timeout: int = 30
    retry_attempts: int = 3
    max_feed_age_days: int = 7  # Ignorar feeds mais antigos
    include_content: bool = True
    max_content_length: int = 5000

class RSSCollector:
    """Coletor de feeds RSS"""
    
    def __init__(self, config: Optional[RSSConfig] = None):
        self.config = config or RSSConfig()
        self.http_client = HTTPClient()
        self.session = None
        
        # Fontes RSS populares (Brasil e Internacional)
        self.default_feeds = [
            # Brasil
            'https://g1.globo.com/rss/g1/',
            'https://rss.uol.com.br/feed/ultimas.xml',
            'https://www.folha.uol.com.br/rss/rss091.xml',
            'https://www.estadao.com.br/rss/ultimas.xml',
            'https://www.cnnbrasil.com.br/feed/',
            'https://www.bbc.com/portuguese/index.xml',
            'https://www1.folha.uol.com.br/feed/',
            'https://www.gov.br/pt-br/noticias/rss',
            
            # Internacional
            'https://rss.cnn.com/rss/edition.rss',
            'https://feeds.bbci.co.uk/news/rss.xml',
            'https://feeds.reuters.com/reuters/topNews',
            'https://feeds.npr.org/1001/rss.xml',
            'https://feeds.washingtonpost.com/rss/politics',
            'https://feeds.nytimes.com/nyt/rss/HomePage',
            'https://feeds.theguardian.com/theguardian/rss',
            'https://techcrunch.com/feed/',
            'https://feeds.huffpost.com/huffpost/blog',
            'https://www.wired.com/feed/rss'
        ]
        
        logger.info("📰 RSS Collector inicializado")
    
    async def initialize(self):
        """Inicializa o coletor"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        )
        
        logger.info("✅ RSS Collector pronto")
    
    async def search(self, query: str, max_results: Optional[int] = None,
                    feeds: Optional[List[str]] = None) -> List[SearchResult]:
        """
        Busca notícias em feeds RSS
        
        Args:
            query: Termo de busca
            max_results: Número máximo de resultados
            feeds: Lista específica de feeds (None = usar defaults)
            
        Returns:
            Lista de SearchResult
        """
        if not self.session:
            await self.initialize()
        
        max_results = max_results or self.config.max_results
        feeds_to_use = feeds or self.default_feeds
        
        logger.info(f"🔍 Buscando em RSS: '{query}' (max: {max_results}, feeds: {len(feeds_to_use)})")
        
        try:
            all_articles = []
            
            # Processar feeds em paralelo
            tasks = []
            for feed_url in feeds_to_use:
                task = self._process_feed(feed_url, query)
                tasks.append(task)
            
            # Executar com limite de concorrência
            semaphore = asyncio.Semaphore(10)  # Máximo 10 feeds simultâneos
            
            async def process_with_semaphore(feed_url, query):
                async with semaphore:
                    return await self._process_feed(feed_url, query)
            
            tasks = [process_with_semaphore(url, query) for url in feeds_to_use]
            feed_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combinar resultados
            for result in feed_results:
                if isinstance(result, list):
                    all_articles.extend(result)
                elif isinstance(result, Exception):
                    logger.debug(f"⚠️ Erro processando feed: {str(result)}")
            
            # Filtrar por relevância e data
            filtered_articles = await self._filter_articles(all_articles, query)
            
            # Ordenar por data (mais recentes primeiro)
            filtered_articles.sort(key=lambda x: x.get('published', 0), reverse=True)
            
            # Limitar resultados
            final_articles = filtered_articles[:max_results]
            
            # Converter para SearchResult
            results = []
            for article in final_articles:
                result = SearchResult(
                    title=article.get('title', ''),
                    url=article.get('url', ''),
                    description=article.get('summary', '')[:500],
                    source='rss',
                    timestamp=article.get('published', time.time()),
                    relevance_score=article.get('relevance_score', 0.0)
                )
                
                result.extracted_data = {
                    'feed_title': article.get('feed_title', ''),
                    'feed_url': article.get('feed_url', ''),
                    'author': article.get('author', ''),
                    'published': article.get('published_formatted', ''),
                    'tags': article.get('tags', []),
                    'content': article.get('content', ''),
                    'language': article.get('language', ''),
                    'word_count': article.get('word_count', 0)
                }
                
                results.append(result)
            
            logger.info(f"✅ Encontrados {len(results)} artigos no RSS")
            return results
            
        except Exception as e:
            logger.error(f"❌ Erro na busca RSS: {str(e)}")
            return []
    
    async def _process_feed(self, feed_url: str, query: str) -> List[Dict[str, Any]]:
        """Processa um feed RSS específico"""
        try:
            # Fazer download do feed
            async with self.session.get(feed_url) as response:
                if response.status != 200:
                    logger.debug(f"⚠️ Feed {feed_url} retornou {response.status}")
                    return []
                
                feed_content = await response.text()
                
                # Parsear feed
            feed = feedparser.parse(feed_content)
            
            if feed.bozo:
                logger.debug(f"⚠️ Feed malformado: {feed_url} - {feed.bozo_exception}")
            
            articles = []
            feed_title = getattr(feed.feed, 'title', 'Unknown Feed')
            
            for entry in feed.entries:
                try:
                    article = await self._parse_entry(entry, feed_url, feed_title, query)
                    if article:
                        articles.append(article)
                
                except Exception as e:
                    logger.debug(f"⚠️ Erro parseando entry: {str(e)}")
                    continue
            
            logger.debug(f"📊 Feed {feed_url}: {len(articles)} artigos")
            return articles
        
        except Exception as e:
            logger.debug(f"⚠️ Erro processando feed {feed_url}: {str(e)}")
            return []
    
    async def _parse_entry(self, entry, feed_url: str, feed_title: str, 
                          query: str) -> Optional[Dict[str, Any]]:
        """Parse de uma entrada de feed"""
        try:
            # Extrair informações básicas
            title = getattr(entry, 'title', '')
            link = getattr(entry, 'link', '')
            summary = getattr(entry, 'summary', '')
            
            # Extrair conteúdo completo se disponível
            content = ''
            if hasattr(entry, 'content') and entry.content:
                content = entry.content[0].value if entry.content else ''
            elif hasattr(entry, 'description'):
                content = entry.description
            
            # Limitar tamanho do conteúdo
            if content and len(content) > self.config.max_content_length:
                content = content[:self.config.max_content_length] + '...'
            
            # Extrair data de publicação
            published = time.time()
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published = time.mktime(entry.published_parsed)
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                published = time.mktime(entry.updated_parsed)
            
            # Verificar idade do artigo
            article_age_days = (time.time() - published) / (24 * 3600)
            if article_age_days > self.config.max_feed_age_days:
                return None
            
            # Calcular relevância
            relevance_score = self._calculate_relevance(title, summary, content, query)
            
            # Se não for relevante, pular
            if relevance_score <= 0:
                return None
            
            # Extrair metadados
            article = {
                'title': title,
                'url': link,
                'summary': summary,
                'content': content,
                'feed_title': feed_title,
                'feed_url': feed_url,
                'author': getattr(entry, 'author', ''),
                'published': published,
                'published_formatted': self._format_date(published),
                'tags': self._extract_tags(entry),
                'language': getattr(entry, 'language', ''),
                'relevance_score': relevance_score,
                'word_count': len(content.split()) if content else 0
            }
            
            return article
        
        except Exception as e:
            logger.debug(f"⚠️ Erro parseando entry: {str(e)}")
            return None
    
    def _calculate_relevance(self, title: str, summary: str, content: str, query: str) -> float:
        """Calcula relevância do artigo para a query"""
        if not query:
            return 0.5  # Relevância neutra se não há query
        
        query_lower = query.lower()
        title_lower = (title or '').lower()
        summary_lower = (summary or '').lower()
        content_lower = (content or '').lower()
        
        score = 0.0
        
        # Título tem peso maior
        if query_lower in title_lower:
            score += 0.4
        
        # Palavras da query no título
        query_words = set(query_lower.split())
        title_words = set(title_lower.split())
        title_intersection = len(query_words & title_words)
        score += (title_intersection / len(query_words)) * 0.3 if query_words else 0
        
        # Summary tem peso médio
        if query_lower in summary_lower:
            score += 0.2
        
        # Conteúdo tem peso menor
        if query_lower in content_lower:
            score += 0.1
        
        return min(score, 1.0)
    
    def _extract_tags(self, entry) -> List[str]:
        """Extrai tags do entry"""
        tags = []
        
        if hasattr(entry, 'tags') and entry.tags:
            for tag in entry.tags:
                if hasattr(tag, 'term'):
                    tags.append(tag.term)
                elif isinstance(tag, str):
                    tags.append(tag)
        
        return tags
    
    def _format_date(self, timestamp: float) -> str:
        """Formata timestamp para string legível"""
        try:
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return ''
    
    async def _filter_articles(self, articles: List[Dict[str, Any]], 
                             query: str) -> List[Dict[str, Any]]:
        """Filtra artigos por relevância e remove duplicatas"""
        if not query:
            return articles
        
        # Filtrar por relevância mínima
        filtered = [a for a in articles if a.get('relevance_score', 0) > 0.1]
        
        # Remover duplicatas baseado na URL
        seen_urls = set()
        unique_articles = []
        
        for article in filtered:
            url = article.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_articles.append(article)
        
        return unique_articles
    
    async def add_feed(self, feed_url: str) -> bool:
        """
        Adiciona novo feed RSS
        
        Args:
            feed_url: URL do feed
            
        Returns:
            True se adicionado com sucesso
        """
        try:
            # Testar feed
            async with self.session.get(feed_url) as response:
                if response.status == 200:
                    feed_content = await response.text()
                    feed = feedparser.parse(feed_content)
                    
                    if not feed.bozo and len(feed.entries) > 0:
                        if feed_url not in self.default_feeds:
                            self.default_feeds.append(feed_url)
                            logger.info(f"➕ Feed adicionado: {feed_url}")
                            return True
                    else:
                        logger.warning(f"⚠️ Feed inválido: {feed_url}")
                else:
                    logger.warning(f"⚠️ Erro acessando feed {feed_url}: {response.status}")
        
        except Exception as e:
            logger.error(f"❌ Erro adicionando feed {feed_url}: {str(e)}")
        
        return False
    
    async def get_feed_info(self, feed_url: str) -> Dict[str, Any]:
        """
        Obtém informações sobre um feed
        
        Args:
            feed_url: URL do feed
            
        Returns:
            Informações do feed
        """
        try:
            async with self.session.get(feed_url) as response:
                if response.status == 200:
                    feed_content = await response.text()
                    feed = feedparser.parse(feed_content)
                    
                    info = {
                        'url': feed_url,
                        'title': getattr(feed.feed, 'title', 'Unknown'),
                        'description': getattr(feed.feed, 'description', ''),
                        'language': getattr(feed.feed, 'language', ''),
                        'updated': getattr(feed.feed, 'updated', ''),
                        'entries_count': len(feed.entries),
                        'is_valid': not feed.bozo,
                        'last_entry_date': None
                    }
                    
                    # Data da última entrada
                    if feed.entries:
                        last_entry = feed.entries[0]
                        if hasattr(last_entry, 'published_parsed') and last_entry.published_parsed:
                            info['last_entry_date'] = time.mktime(last_entry.published_parsed)
                    
                    return info
        
        except Exception as e:
            logger.error(f"❌ Erro obtendo info feed {feed_url}: {str(e)}")
        
        return {}
    
    async def get_trending_topics(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Identifica tópicos trending dos feeds
        
        Args:
            hours: Período em horas
            
        Returns:
            Lista de tópicos trending
        """
        logger.info(f"🔥 Analisando tópicos trending (últimas {hours}h)")
        
        # Coletar artigos recentes
        cutoff_time = time.time() - (hours * 3600)
        recent_articles = []
        
        for feed_url in self.default_feeds[:20]:  # Limitar a 20 feeds para performance
            try:
                articles = await self._process_feed(feed_url, '')
                for article in articles:
                    if article.get('published', 0) > cutoff_time:
                        recent_articles.append(article)
            except:
                continue
        
        # Extrair palavras-chave e contar frequência
        word_freq = {}
        
        for article in recent_articles:
            text = f"{article.get('title', '')} {article.get('summary', '')}".lower()
            words = text.split()
            
            for word in words:
                if len(word) > 3 and word.isalpha():  # Ignorar palavras curtas e não-alfabéticas
                    word_freq[word] = word_freq.get(word, 0) + 1
        
        # Ordenar por frequência
        trending = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20]
        
        topics = [
            {
                'topic': word,
                'frequency': freq,
                'relevance': freq / len(recent_articles) if recent_articles else 0
            }
            for word, freq in trending
        ]
        
        logger.info(f"🔥 Encontrados {len(topics)} tópicos trending")
        return topics
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificação de saúde do coletor"""
        return {
            'status': 'healthy',
            'component': 'rss_collector',
            'timestamp': time.time(),
            'session_active': self.session is not None,
            'max_results': self.config.max_results,
            'max_feed_age_days': self.config.max_feed_age_days
        }
    
    async def cleanup(self):
        """Limpa recursos"""
        if self.session:
            await self.session.close()
        
        logger.info("🧹 RSS Collector limpo")
