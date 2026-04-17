"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - Onion Scraper
Coleta de dados de sites .onion (Tor)
"""

import asyncio
import aiohttp
import random
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass
import time
import logging
import re
from bs4 import BeautifulSoup

from ..core.pipeline import SearchResult
from ..utils.logger import setup_logger
from ..utils.http_client import HTTPClient
from .tor_client import TorClient

logger = setup_logger(__name__)

@dataclass
class OnionScraperConfig:
    """Configuração do scraper .onion"""
    max_results: int = 100
    timeout: int = 60
    retry_attempts: int = 3
    max_depth: int = 2
    respect_robots: bool = True
    max_page_size: int = 5 * 1024 * 1024  # 5MB
    allowed_domains: List[str] = None
    blocked_domains: List[str] = None
    
    def __post_init__(self):
        if self.allowed_domains is None:
            self.allowed_domains = []
        if self.blocked_domains is None:
            self.blocked_domains = []

class OnionScraper:
    """Scraper para sites .onion"""
    
    def __init__(self, config: Optional[OnionScraperConfig] = None):
        self.config = config or OnionScraperConfig()
        self.tor_client = TorClient()
        self.session = None
        
        # Diretórios e sites .onion conhecidos
        self.known_onions = [
            # Diretórios
            'http://tor66sewebgixwhcqfnp5inzp5x5uohhdy3kvtnyfxc2e5mxi5iuoad.onion',
            'http://3g2upl4pq6kufc4m.onion',
            'http://xmh57jrzrnw6insl.onion',
            'http://juhanurmihxlp77nkq76byaxc4y5hj7lvsxfy2o7d6k7wne5qb6r5qd.onion',
            
            # Sites de notícias
            'http://expyuzz4wqqyqhjn.onion',  # The New York Times
            'http://bbcnewsv2vjtpsuy.onion',  # BBC
            'http://propublicp2u7.onion',     # ProPublica
            'http://www.bbcnewsd73hkzno2ini43t4gblxvycyac5aw4gnv7t2rccijh7745uqd.onion',  # BBC
            
            # Sites de conteúdo variado
            'http://librarysgyay6sbrj4.onion',  # Library Genesis
            'http://zlibrary2bto3sydud.onion',  # Z-Library
            'http://bookszlibb74ugqojh3g6ybb6d3qzsj7ovwz6fp3dpt56kyywfz6hqd.onion',  # Z-Library alt
            
            # Fóruns e comunidades
            'http://dreadreddie9onion.onion',  # Dread (Reddit-like)
            'http://8chan2bzyh3j6y5d3.onion',  # 8chan
            'http://hanbx4yfa7ynbak5.onion',   # Hanabira
        ]
        
        # Padrões para encontrar links .onion
        self.onion_pattern = re.compile(r'https?://([a-z0-9]{16,56})\.onion', re.IGNORECASE)
        
        logger.info("🧅 Onion Scraper inicializado")
    
    async def initialize(self):
        """Inicializa o scraper"""
        await self.tor_client.initialize()
        
        # Criar sessão HTTP usando Tor
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
        )
        
        logger.info("✅ Onion Scraper pronto")
    
    async def search(self, query: str, max_results: Optional[int] = None,
                    domains: Optional[List[str]] = None) -> List[SearchResult]:
        """
        Busca em sites .onion
        
        Args:
            query: Termo de busca
            max_results: Número máximo de resultados
            domains: Domínios específicos para buscar
            
        Returns:
            Lista de SearchResult
        """
        if not self.session:
            await self.initialize()
        
        max_results = max_results or self.config.max_results
        domains_to_search = domains or self.known_onions
        
        logger.info(f"🧅 Buscando em sites .onion: '{query}' (max: {max_results})")
        
        try:
            all_results = []
            
            # Buscar em múltiplos sites em paralelo
            semaphore = asyncio.Semaphore(5)  # Limitar concorrência
            
            async def search_domain(domain):
                async with semaphore:
                    return await self._search_single_domain(domain, query)
            
            tasks = [search_domain(domain) for domain in domains_to_search[:10]]
            domain_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combinar resultados
            for result in domain_results:
                if isinstance(result, list):
                    all_results.extend(result)
                elif isinstance(result, Exception):
                    logger.debug(f"⚠️ Erro domínio: {str(result)}")
            
            # Rankear resultados
            ranked_results = await self._rank_results(all_results, query)
            
            # Limitar resultados
            final_results = ranked_results[:max_results]
            
            logger.info(f"✅ Encontrados {len(final_results)} resultados .onion")
            return final_results
            
        except Exception as e:
            logger.error(f"❌ Erro na busca .onion: {str(e)}")
            return []
    
    async def _search_single_domain(self, domain: str, query: str) -> List[SearchResult]:
        """Busca em um único domínio .onion"""
        try:
            results = []
            
            # Fazer scraping do domínio principal
            main_content = await self._scrape_onion_page(domain)
            if main_content:
                page_results = await self._extract_search_results(main_content, domain, query)
                results.extend(page_results)
                
                # Encontrar links .onion adicionais
                onion_links = self._find_onion_links(main_content)
                
                # Fazer scraping de links encontrados (limitado)
                for link in onion_links[:3]:  # Limitar para não sobrecarregar
                    try:
                        link_content = await self._scrape_onion_page(link)
                        if link_content:
                            link_results = await self._extract_search_results(link_content, link, query)
                            results.extend(link_results)
                            
                            await asyncio.sleep(1)  # Delay entre requisições
                            
                    except Exception as e:
                        logger.debug(f"⚠️ Erro scraping link {link}: {str(e)}")
                        continue
            
            return results
            
        except Exception as e:
            logger.debug(f"⚠️ Erro domínio {domain}: {str(e)}")
            return []
    
    async def _scrape_onion_page(self, url: str) -> Optional[str]:
        """Faz scraping de página .onion"""
        try:
            for attempt in range(self.config.retry_attempts):
                try:
                    async with self.tor_client.get(url) as response:
                        if response.status == 200:
                            content_type = response.headers.get('content-type', '').lower()
                            
                            if 'text/html' in content_type:
                                content = await response.text()
                                
                                # Limitar tamanho
                                if len(content) > self.config.max_page_size:
                                    content = content[:self.config.max_page_size]
                                
                                logger.debug(f"📄 Page scraped: {url} ({len(content)} chars)")
                                return content
                            else:
                                logger.debug(f"⚠️ Content-type não HTML: {content_type}")
                                return None
                        else:
                            logger.debug(f"⚠️ HTTP {response.status} para {url}")
                            return None
                
                except Exception as e:
                    logger.debug(f"⚠️ Tentativa {attempt + 1} falhou: {str(e)}")
                    
                    if attempt < self.config.retry_attempts - 1:
                        # Mudar identidade Tor
                        await self.tor_client.change_identity()
                        await asyncio.sleep(2 ** attempt)
                    else:
                        raise
        
        except Exception as e:
            logger.debug(f"⚠️ Erro scraping {url}: {str(e)}")
        
        return None
    
    async def _extract_search_results(self, content: str, source_url: str, 
                                    query: str) -> List[SearchResult]:
        """Extrai resultados de busca do conteúdo"""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            results = []
            
            # Extrair links e textos relevantes
            links = soup.find_all('a', href=True)
            
            for link in links:
                try:
                    href = link.get('href')
                    text = link.get_text(strip=True)
                    
                    if not href or not text:
                        continue
                    
                    # Converter URL relativa para absoluta
                    if href.startswith('/'):
                        href = urljoin(source_url, href)
                    elif not href.startswith(('http://', 'https://')):
                        continue
                    
                    # Verificar relevância
                    relevance = self._calculate_relevance(text, href, query)
                    if relevance <= 0:
                        continue
                    
                    # Extrair descrição do contexto
                    description = self._extract_context_description(link)
                    
                    result = SearchResult(
                        title=text,
                        url=href,
                        description=description,
                        source='onion',
                        timestamp=time.time(),
                        relevance_score=relevance
                    )
                    
                    result.extracted_data = {
                        'source_domain': urlparse(source_url).netloc,
                        'source_url': source_url,
                        'is_onion': href.endswith('.onion'),
                        'link_type': self._classify_link(href),
                        'context': description
                    }
                    
                    results.append(result)
                    
                except Exception as e:
                    logger.debug(f"⚠️ Erro processando link: {str(e)}")
                    continue
            
            # Extrair textos da página que correspondem à query
            page_results = await self._extract_text_matches(soup, source_url, query)
            results.extend(page_results)
            
            return results
            
        except Exception as e:
            logger.debug(f"⚠️ Erro extraindo resultados: {str(e)}")
            return []
    
    def _find_onion_links(self, content: str) -> List[str]:
        """Encontra links .onion no conteúdo"""
        onion_links = set()
        
        # Usar regex para encontrar .onion URLs
        matches = self.onion_pattern.findall(content)
        
        for match in matches:
            if len(match) >= 16:  # Tamanho mínimo de hash .onion
                onion_url = f"http://{match}.onion"
                onion_links.add(onion_url)
        
        return list(onion_links)
    
    def _calculate_relevance(self, title: str, url: str, query: str) -> float:
        """Calcula relevância para a query"""
        if not query:
            return 0.5
        
        query_lower = query.lower()
        title_lower = title.lower()
        url_lower = url.lower()
        
        score = 0.0
        
        # Título tem peso maior
        if query_lower in title_lower:
            score += 0.4
        
        # Palavras da query no título
        query_words = set(query_lower.split())
        title_words = set(title_lower.split())
        title_intersection = len(query_words & title_words)
        score += (title_intersection / len(query_words)) * 0.3 if query_words else 0
        
        # URL tem peso médio
        if query_lower in url_lower:
            score += 0.2
        
        # Bônus para links .onion
        if url.endswith('.onion'):
            score += 0.1
        
        return min(score, 1.0)
    
    def _extract_context_description(self, link_element) -> str:
        """Extrai descrição do contexto do link"""
        try:
            # Tentar pegar texto próximo ao link
            parent = link_element.parent
            if parent:
                parent_text = parent.get_text(strip=True)
                if len(parent_text) > len(link_element.get_text(strip=True)):
                    return parent_text[:200] + '...' if len(parent_text) > 200 else parent_text
            
            # Tentar pegar atributos title ou alt
            title = link_element.get('title') or link_element.get('alt', '')
            if title:
                return title[:200] + '...' if len(title) > 200 else title
            
            return ''
            
        except Exception:
            return ''
    
    def _classify_link(self, url: str) -> str:
        """Classifica tipo de link"""
        url_lower = url.lower()
        
        if any(ext in url_lower for ext in ['.jpg', '.png', '.gif', '.pdf', '.zip', '.tar']):
            return 'file'
        elif any(keyword in url_lower for keyword in ['forum', 'board', 'thread', 'post']):
            return 'forum'
        elif any(keyword in url_lower for keyword in ['wiki', 'doc', 'help', 'guide']):
            return 'documentation'
        elif any(keyword in url_lower for keyword in ['blog', 'news', 'article']):
            return 'content'
        else:
            return 'general'
    
    async def _extract_text_matches(self, soup, source_url: str, query: str) -> List[SearchResult]:
        """Extrai textos da página que correspondem à query"""
        try:
            query_lower = query.lower()
            matches = []
            
            # Procurar em elementos de texto principais
            for element in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div']):
                text = element.get_text(strip=True)
                
                if not text or len(text) < 20:
                    continue
                
                # Verificar se contém a query
                if query_lower in text.lower():
                    # Criar resultado baseado no texto
                    result = SearchResult(
                        title=self._extract_title_from_text(text),
                        url=source_url,
                        description=text[:500] + '...' if len(text) > 500 else text,
                        source='onion_text',
                        timestamp=time.time(),
                        relevance_score=0.6
                    )
                    
                    result.extracted_data = {
                        'source_domain': urlparse(source_url).netloc,
                        'source_url': source_url,
                        'text_match': True,
                        'element_tag': element.name
                    }
                    
                    matches.append(result)
            
            return matches[:5]  # Limitar matches por página
            
        except Exception as e:
            logger.debug(f"⚠️ Erro extraindo text matches: {str(e)}")
            return []
    
    def _extract_title_from_text(self, text: str) -> str:
        """Extrai título de um texto"""
        # Pegar primeira frase ou primeira linha
        sentences = text.split('.')
        if sentences:
            first_sentence = sentences[0].strip()
            if len(first_sentence) > 10:
                return first_sentence
        
        # Pegar primeiras palavras
        words = text.split()
        if len(words) >= 5:
            return ' '.join(words[:5]) + '...'
        
        return text[:50] + '...' if len(text) > 50 else text
    
    async def _rank_results(self, results: List[SearchResult], query: str) -> List[SearchResult]:
        """Rankea resultados por relevância"""
        # Calcular score adicional baseado em múltiplos fatores
        for result in results:
            additional_score = 0.0
            
            # Bônus para sites .onion
            if result.extracted_data.get('is_onion'):
                additional_score += 0.2
            
            # Bônus para tipos específicos de conteúdo
            link_type = result.extracted_data.get('link_type', '')
            if link_type == 'documentation':
                additional_score += 0.1
            elif link_type == 'forum':
                additional_score += 0.05
            
            # Bônus para domínios conhecidos
            source_domain = result.extracted_data.get('source_domain', '')
            if any(known in source_domain for known in ['dread', 'library', 'bbc', 'propublica']):
                additional_score += 0.15
            
            result.relevance_score = min(result.relevance_score + additional_score, 1.0)
        
        # Ordenar por score
        return sorted(results, key=lambda x: x.relevance_score, reverse=True)
    
    async def discover_onion_sites(self, seed_urls: Optional[List[str]] = None,
                                 max_discoveries: int = 100) -> List[str]:
        """
        Descobre novos sites .onion
        
        Args:
            seed_urls: URLs iniciais para descoberta
            max_discoveries: Número máximo de descobertas
            
        Returns:
            Lista de sites .onion descobertos
        """
        logger.info("🔍 Descobrindo sites .onion...")
        
        seed_urls = seed_urls or self.known_onions[:5]
        discovered = set()
        to_visit = set(seed_urls)
        visited = set()
        
        while to_visit and len(discovered) < max_discoveries:
            current_url = to_visit.pop()
            
            if current_url in visited:
                continue
            
            visited.add(current_url)
            
            try:
                # Fazer scraping da página
                content = await self._scrape_onion_page(current_url)
                if content:
                    # Encontrar links .onion
                    onion_links = self._find_onion_links(content)
                    
                    for link in onion_links:
                        if link not in visited and link not in discovered:
                            discovered.add(link)
                            to_visit.add(link)
                            
                            logger.debug(f"🧅 Site descoberto: {link}")
                    
                    await asyncio.sleep(1)  # Delay entre requisições
                    
            except Exception as e:
                logger.debug(f"⚠️ Erro descobrindo sites {current_url}: {str(e)}")
                continue
        
        logger.info(f"✅ Descobertos {len(discovered)} sites .onion")
        return list(discovered)
    
    async def get_tor_status(self) -> Dict[str, Any]:
        """
        Obtém status da conexão Tor
        
        Returns:
            Status do Tor e informações do circuito
        """
        try:
            # Status básico
            ip_info = await self.tor_client.get_ip_info()
            circuit_info = await self.tor_client.get_circuit_info()
            
            status = {
                'connected': self.tor_client.is_connected,
                'ip_info': ip_info,
                'circuit_info': circuit_info,
                'timestamp': time.time()
            }
            
            return status
            
        except Exception as e:
            logger.error(f"❌ Erro obtendo status Tor: {str(e)}")
            return {
                'connected': False,
                'error': str(e),
                'timestamp': time.time()
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificação de saúde do scraper"""
        return {
            'status': 'healthy',
            'component': 'onion_scraper',
            'timestamp': time.time(),
            'session_active': self.session is not None,
            'tor_client_connected': self.tor_client is not None,
            'known_onions_count': len(self.known_onions),
            'max_results': self.config.max_results
        }
    
    async def cleanup(self):
        """Limpa recursos"""
        if self.session:
            await self.session.close()
        
        if self.tor_client:
            await self.tor_client.cleanup()
        
        logger.info("🧹 Onion Scraper limpo")
