"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - Web Crawler
Faz scraping profundo de páginas web
"""

import asyncio
import aiohttp
import random
from typing import Dict, Any, Optional, List
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass
import time
import logging
import hashlib
import re

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from ..utils.logger import setup_logger
from ..utils.http_client import HTTPClient

logger = setup_logger(__name__)

@dataclass
class CrawlerConfig:
    """Configuração do crawler"""
    timeout: int = 30
    max_content_length: int = 1000000  # 1MB
    use_selenium: bool = False
    headless: bool = True
    wait_time: int = 10
    retry_attempts: int = 3
    delay_range: tuple = (1, 3)
    respect_robots: bool = True
    user_agent: str = "OMNISCIENT_CRAWLER/3.0"

class WebCrawler:
    """Crawler web avançado"""
    
    def __init__(self, config: Optional[CrawlerConfig] = None):
        self.config = config or CrawlerConfig()
        self.http_client = HTTPClient()
        self.session = None
        self.driver = None
        self.cache = {}
        
        logger.info("🕷️ Web Crawler inicializado")
    
    async def initialize(self):
        """Inicializa o crawler"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout),
            headers={'User-Agent': self.config.user_agent}
        )
        
        if self.config.use_selenium:
            await self._init_selenium()
        
        logger.info("✅ Web Crawler pronto")
    
    async def _init_selenium(self):
        """Inicializa Selenium para JavaScript-heavy sites"""
        try:
            options = Options()
            if self.config.headless:
                options.add_argument('--headless')
            
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument(f'--user-agent={self.config.user_agent}')
            
            self.driver = webdriver.Chrome(options=options)
            self.driver.set_page_load_timeout(self.config.timeout)
            
            logger.info("🚀 Selenium inicializado")
            
        except Exception as e:
            logger.warning(f"⚠️ Falha ao inicializar Selenium: {str(e)}")
            self.config.use_selenium = False
    
    async def scrape_url(self, url: str, use_selenium: Optional[bool] = None) -> Dict[str, Any]:
        """
        Faz scraping completo de uma URL
        
        Args:
            url: URL para fazer scraping
            use_selenium: Forçar uso do Selenium
            
        Returns:
            Dicionário com conteúdo extraído
        """
        if not self.session:
            await self.initialize()
        
        # Verificar cache
        cache_key = hashlib.md5(url.encode()).hexdigest()
        if cache_key in self.cache:
            logger.debug(f"📦 Cache hit para {url}")
            return self.cache[cache_key]
        
        logger.info(f"🕷️ Scraping: {url}")
        
        try:
            # Decidir método
            should_use_selenium = use_selenium if use_selenium is not None else self.config.use_selenium
            
            if should_use_selenium and self.driver:
                content = await self._scrape_with_selenium(url)
            else:
                content = await self._scrape_with_aiohttp(url)
            
            # Parsear conteúdo
            parsed_content = await self._parse_content(content, url)
            
            # Salvar em cache
            self.cache[cache_key] = parsed_content
            
            logger.info(f"✅ Scraping concluído: {len(parsed_content.get('text', ''))} chars")
            return parsed_content
            
        except Exception as e:
            logger.error(f"❌ Erro scraping {url}: {str(e)}")
            return {
                'url': url,
                'error': str(e),
                'text': '',
                'html': '',
                'metadata': {}
            }
    
    async def _scrape_with_aiohttp(self, url: str) -> str:
        """Scraping usando aiohttp"""
        for attempt in range(self.config.retry_attempts):
            try:
                async with self.session.get(url) as response:
                    if response.status != 200:
                        raise Exception(f"HTTP {response.status}")
                    
                    content_type = response.headers.get('content-type', '').lower()
                    
                    if 'text/html' not in content_type:
                        raise Exception(f"Content-type não HTML: {content_type}")
                    
                    content = await response.text()
                    
                    # Limitar tamanho
                    if len(content) > self.config.max_content_length:
                        content = content[:self.config.max_content_length]
                        logger.warning(f"⚠️ Conteúdo truncado para {self.config.max_content_length} chars")
                    
                    return content
                    
            except Exception as e:
                logger.warning(f"⚠️ Tentativa {attempt + 1} falhou: {str(e)}")
                if attempt < self.config.retry_attempts - 1:
                    await asyncio.sleep(random.uniform(*self.config.delay_range))
                else:
                    raise
    
    async def _scrape_with_selenium(self, url: str) -> str:
        """Scraping usando Selenium para sites com JavaScript"""
        if not self.driver:
            raise Exception("Selenium não inicializado")
        
        try:
            self.driver.get(url)
            
            # Esperar página carregar
            WebDriverWait(self.driver, self.config.wait_time).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Esperar um pouco mais para JavaScript
            await asyncio.sleep(2)
            
            # Tentar rolar a página para carregar conteúdo dinâmico
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            await asyncio.sleep(1)
            
            content = self.driver.page_source
            
            # Limitar tamanho
            if len(content) > self.config.max_content_length:
                content = content[:self.config.max_content_length]
            
            return content
            
        except TimeoutException:
            logger.warning(f"⚠️ Timeout Selenium para {url}")
            # Tentar pegar o que já carregou
            return self.driver.page_source[:self.config.max_content_length]
        
        except Exception as e:
            logger.error(f"❌ Erro Selenium: {str(e)}")
            raise
    
    async def _parse_content(self, html_content: str, url: str) -> Dict[str, Any]:
        """Parse HTML para extrair conteúdo estruturado"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remover scripts e styles
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Extrair informações básicas
            title = self._extract_title(soup)
            description = self._extract_description(soup)
            text_content = self._extract_text(soup)
            links = self._extract_links(soup, url)
            images = self._extract_images(soup, url)
            metadata = self._extract_metadata(soup)
            
            # Extrair dados estruturados
            structured_data = self._extract_structured_data(soup)
            
            # Detectar linguagem
            language = self._detect_language(soup, text_content)
            
            return {
                'url': url,
                'title': title,
                'description': description,
                'text': text_content,
                'html': html_content,
                'links': links,
                'images': images,
                'metadata': metadata,
                'structured_data': structured_data,
                'language': language,
                'word_count': len(text_content.split()),
                'scraped_at': time.time()
            }
            
        except Exception as e:
            logger.error(f"❌ Erro parse HTML: {str(e)}")
            return {
                'url': url,
                'title': '',
                'description': '',
                'text': '',
                'html': html_content,
                'links': [],
                'images': [],
                'metadata': {},
                'structured_data': {},
                'language': 'unknown',
                'word_count': 0,
                'scraped_at': time.time()
            }
    
    def _extract_title(self, soup) -> str:
        """Extrai título da página"""
        # Tentar title tag
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text(strip=True)
            if title:
                return title
        
        # Tentar h1
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text(strip=True)
        
        # Tentar meta property og:title
        og_title = soup.find('meta', property='og:title')
        if og_title:
            return og_title.get('content', '')
        
        return ''
    
    def _extract_description(self, soup) -> str:
        """Extrai descrição da página"""
        # Tentar meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            return meta_desc.get('content', '')
        
        # Tentar meta property og:description
        og_desc = soup.find('meta', property='og:description')
        if og_desc:
            return og_desc.get('content', '')
        
        # Tentar primeiro parágrafo
        first_p = soup.find('p')
        if first_p:
            text = first_p.get_text(strip=True)
            return text[:200] + '...' if len(text) > 200 else text
        
        return ''
    
    def _extract_text(self, soup) -> str:
        """Extrai texto principal"""
        # Tentar encontrar conteúdo principal
        main_content = None
        
        # Procurar por tags semânticas
        for tag in ['main', 'article', '[role="main"]']:
            main_content = soup.select_one(tag)
            if main_content:
                break
        
        # Se não encontrar, usar body
        if not main_content:
            main_content = soup.find('body')
        
        if main_content:
            text = main_content.get_text(separator=' ', strip=True)
            # Limpar espaços extras
            text = re.sub(r'\s+', ' ', text)
            return text
        
        return ''
    
    def _extract_links(self, soup, base_url: str) -> List[Dict[str, str]]:
        """Extrai links da página"""
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text(strip=True)
            
            # Converter URL relativa para absoluta
            absolute_url = urljoin(base_url, href)
            
            # Validar URL
            parsed = urlparse(absolute_url)
            if parsed.scheme in ['http', 'https']:
                links.append({
                    'url': absolute_url,
                    'text': text,
                    'title': link.get('title', '')
                })
        
        return links[:100]  # Limitar a 100 links
    
    def _extract_images(self, soup, base_url: str) -> List[Dict[str, str]]:
        """Extrai imagens da página"""
        images = []
        
        for img in soup.find_all('img'):
            src = img.get('src', '')
            alt = img.get('alt', '')
            title = img.get('title', '')
            
            if src:
                absolute_url = urljoin(base_url, src)
                
                images.append({
                    'url': absolute_url,
                    'alt': alt,
                    'title': title,
                    'width': img.get('width', ''),
                    'height': img.get('height', '')
                })
        
        return images[:50]  # Limitar a 50 imagens
    
    def _extract_metadata(self, soup) -> Dict[str, Any]:
        """Extrai metadados da página"""
        metadata = {}
        
        # Meta tags
        for meta in soup.find_all('meta'):
            name = meta.get('name') or meta.get('property')
            content = meta.get('content')
            
            if name and content:
                metadata[name] = content
        
        # Canonical URL
        canonical = soup.find('link', rel='canonical')
        if canonical:
            metadata['canonical_url'] = canonical.get('href', '')
        
        # Language
        html_tag = soup.find('html')
        if html_tag:
            metadata['html_lang'] = html_tag.get('lang', '')
        
        return metadata
    
    def _extract_structured_data(self, soup) -> Dict[str, Any]:
        """Extrai dados estruturados (JSON-LD, microdata)"""
        structured_data = {}
        
        # JSON-LD
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            try:
                import json
                data = json.loads(script.string)
                structured_data['json_ld'] = data
                break  # Pegar apenas o primeiro
            except:
                continue
        
        # Microdata (simplificado)
        items = soup.find_all(attrs={'itemscope': True})
        if items:
            structured_data['microdata_count'] = len(items)
        
        return structured_data
    
    def _extract_social_links(self, soup) -> List[Dict[str, str]]:
        """Extrai links de redes sociais"""
        social_links = []
        
        # Padrões de redes sociais
        social_patterns = {
            'facebook': r'facebook\.com|fb\.com',
            'twitter': r'twitter\.com|x\.com',
            'instagram': r'instagram\.com',
            'linkedin': r'linkedin\.com',
            'youtube': r'youtube\.com|youtu\.be',
            'whatsapp': r'wa\.me|whatsapp\.com',
            'telegram': r't\.me|telegram\.org'
        }
        
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            for platform, pattern in social_patterns.items():
                if re.search(pattern, href, re.IGNORECASE):
                    social_links.append({
                        'platform': platform,
                        'url': href,
                        'text': text
                    })
        
        return list({(item['url']): item for item in social_links})  # Remover duplicatas
    
    def _extract_forms(self, soup) -> List[Dict[str, Any]]:
        """Extrai formulários da página"""
        forms = []
        
        for form in soup.find_all('form'):
            form_data = {
                'action': form.get('action', ''),
                'method': form.get('method', 'GET'),
                'fields': []
            }
            
            for field in form.find_all(['input', 'select', 'textarea']):
                field_data = {
                    'name': field.get('name', ''),
                    'type': field.get('type', ''),
                    'id': field.get('id', ''),
                    'required': field.get('required') is not None,
                    'placeholder': field.get('placeholder', '')
                }
                form_data['fields'].append(field_data)
            
            forms.append(form_data)
        
        return forms
    
    def _extract_tables(self, soup) -> List[Dict[str, Any]]:
        """Extrai tabelas da página"""
        tables = []
        
        for table in soup.find_all('table'):
            table_data = {
                'headers': [],
                'rows': [],
                'row_count': 0
            }
            
            # Extrair headers
            header_row = table.find('tr')
            if header_row:
                for th in header_row.find_all('th'):
                    table_data['headers'].append(th.get_text(strip=True))
            
            # Extrair linhas de dados
            for tr in table.find_all('tr')[1:]:  # Pular header se existir
                row = []
                for td in tr.find_all('td'):
                    row.append(td.get_text(strip=True))
                
                if row:
                    table_data['rows'].append(row)
                    table_data['row_count'] += 1
            
            tables.append(table_data)
        
        return tables
    
    def _detect_language(self, soup, text: str) -> str:
        """Detecta idioma do conteúdo"""
        # Tentar meta tag
        html_tag = soup.find('html')
        if html_tag:
            lang = html_tag.get('lang', '')
            if lang:
                return lang.split('-')[0]  # Pegar apenas código principal
        
        # Tentar detectar pelo texto (simplificado)
        if text:
            # Verificar palavras comuns em português
            pt_words = ['que', 'de', 'a', 'o', 'em', 'para', 'com', 'uma', 'os', 'no', 'se', 'na', 'por', 'mais', 'as', 'dos', 'como', 'mas', 'foi', 'ao', 'ele']
            text_words = text.lower().split()[:100]  # Primeiras 100 palavras
            
            pt_matches = sum(1 for word in text_words if word in pt_words)
            
            if pt_matches > 10:
                return 'pt'
            elif pt_matches > 5:
                return 'es'  # Espanhol tem palavras similares
        
        return 'unknown'
    
    async def scrape_multiple(self, urls: List[str], max_concurrent: int = 5) -> List[Dict[str, Any]]:
        """
        Faz scraping de múltiplas URLs em paralelo
        
        Args:
            urls: Lista de URLs
            max_concurrent: Máximo de requisições simultâneas
            
        Returns:
            Lista de conteúdos extraídos
        """
        logger.info(f"🕷️ Scraping múltiplas URLs: {len(urls)}")
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def scrape_with_semaphore(url):
            async with semaphore:
                return await self.scrape_url(url)
        
        tasks = [scrape_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Converter exceções para resultados de erro
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'url': urls[i],
                    'error': str(result),
                    'text': '',
                    'html': '',
                    'metadata': {}
                })
            else:
                processed_results.append(result)
        
        logger.info(f"✅ Scraping múltiplas concluído: {len(processed_results)} URLs")
        return processed_results
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificação de saúde do coletor"""
        return {
            'status': 'healthy',
            'component': 'web_crawler',
            'timestamp': time.time(),
            'session_active': self.session is not None,
            'driver_active': self.driver is not None,
            'cache_size': len(self.cache),
            'use_selenium': self.config.use_selenium
        }
    
    async def cleanup(self):
        """Limpa recursos"""
        if self.session:
            await self.session.close()
        
        if self.driver:
            self.driver.quit()
        
        logger.info("🧹 Web Crawler limpo")
