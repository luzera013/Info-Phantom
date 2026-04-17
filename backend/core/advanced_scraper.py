"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - Advanced Scraper
Sistema avançado de scraping com IA e processamento inteligente
"""

import asyncio
import aiohttp
import time
import hashlib
import re
from typing import List, Dict, Any, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import logging
import json
from urllib.parse import urljoin, urlparse, parse_qs
from pathlib import Path

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from ..collectors.web.crawler import WebCrawler
from ..collectors.web.parser import DataParser
from ..utils.logger import setup_logger
from ..utils.metrics import MetricsCollector
from ..utils.ttl_cache import TTLCache

logger = setup_logger(__name__)
metrics = MetricsCollector()

@dataclass
class ScrapingTask:
    """Tarefa de scraping com configurações avançadas"""
    url: str
    task_id: str
    priority: int = 1  # 1-5, onde 5 é maior prioridade
    depth: int = 1
    follow_links: bool = False
    max_links: int = 10
    content_types: List[str] = field(default_factory=lambda: ['text/html'])
    extract_patterns: Dict[str, str] = field(default_factory=dict)
    javascript_required: bool = False
    headless: bool = True
    timeout: int = 30
    retry_attempts: int = 3
    user_agent: Optional[str] = None
    custom_headers: Dict[str, str] = field(default_factory=dict)
    proxy: Optional[str] = None

@dataclass
class ScrapedContent:
    """Conteúdo extraído com metadados avançados"""
    url: str
    task_id: str
    title: str
    content: str
    html_content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    extracted_data: Dict[str, Any] = field(default_factory=dict)
    links: List[Dict[str, str]] = field(default_factory=list)
    images: List[Dict[str, str]] = field(default_factory=list)
    forms: List[Dict[str, Any]] = field(default_factory=list)
    tables: List[Dict[str, Any]] = field(default_factory=list)
    structured_data: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    quality_score: float = 0.0
    timestamp: float = field(default_factory=time.time)

@dataclass
class ScrapingSession:
    """Sessão de scraping com estado persistente"""
    session_id: str
    tasks: List[ScrapingTask] = field(default_factory=list)
    completed_tasks: List[str] = field(default_factory=list)
    failed_tasks: List[str] = field(default_factory=list)
    results: List[ScrapedContent] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    total_urls_processed: int = 0
    total_content_extracted: int = 0
    errors: List[str] = field(default_factory=list)

class AdvancedScraper:
    """Scraper avançado com IA e processamento inteligente"""
    
    def __init__(self):
        self.crawler = WebCrawler()
        self.parser = DataParser()
        self.cache = TTLCache(ttl=7200)  # 2 horas
        self.active_sessions: Dict[str, ScrapingSession] = {}
        self.driver_pool: List[webdriver.Chrome] = []
        self.session_semaphore = asyncio.Semaphore(10)  # Limite de sessões concorrentes
        
        # Configurações avançadas
        self.config = {
            'max_concurrent_tasks': 20,
            'max_depth': 3,
            'respect_robots_txt': True,
            'user_agent_rotation': True,
            'proxy_rotation': True,
            'javascript_rendering': True,
            'content_validation': True,
            'link_discovery': True,
            'image_extraction': True,
            'form_detection': True,
            'table_extraction': True,
            'structured_data_extraction': True,
            'performance_monitoring': True,
            'error_recovery': True,
            'rate_limiting': True,
            'cache_enabled': True
        }
        
        # User agents para rotação
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0'
        ]
        
        # Proxies para rotação (simulado)
        self.proxies = [
            None,  # Sem proxy
            'http://proxy1.example.com:8080',
            'http://proxy2.example.com:8080'
        ]
        
        logger.info(" Advanced Scraper inicializado")
    
    async def initialize(self):
        """Inicializa o scraper avançado"""
        await self.crawler.initialize()
        
        # Inicializar pool de drivers Selenium
        if self.config['javascript_rendering']:
            await self._initialize_driver_pool()
        
        logger.info(" Advanced Scraper pronto")
    
    async def _initialize_driver_pool(self):
        """Inicializa pool de drivers Selenium"""
        try:
            for i in range(3):  # 3 drivers no pool
                options = Options()
                options.add_argument('--headless')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-gpu')
                options.add_argument('--window-size=1920,1080')
                options.add_argument('--disable-extensions')
                options.add_argument('--disable-plugins')
                options.add_argument('--disable-images')  # Para performance
                
                driver = webdriver.Chrome(options=options)
                driver.set_page_load_timeout(30)
                self.driver_pool.append(driver)
            
            logger.info(f" Pool de {len(self.driver_pool)} drivers Selenium inicializado")
            
        except Exception as e:
            logger.warning(f" Falha ao inicializar pool Selenium: {str(e)}")
            self.config['javascript_rendering'] = False
    
    async def create_scraping_session(self, 
                                    tasks: List[ScrapingTask], 
                                    session_id: Optional[str] = None) -> str:
        """
        Cria uma nova sessão de scraping
        
        Args:
            tasks: Lista de tarefas de scraping
            session_id: ID opcional da sessão
            
        Returns:
            ID da sessão criada
        """
        if not session_id:
            session_id = hashlib.md5(f"session_{time.time()}".encode()).hexdigest()[:8]
        
        session = ScrapingSession(
            session_id=session_id,
            tasks=tasks
        )
        
        self.active_sessions[session_id] = session
        
        logger.info(f" Sessão de scraping criada: {session_id} ({len(tasks)} tarefas)")
        return session_id
    
    async def execute_session(self, session_id: str) -> ScrapingSession:
        """
        Executa uma sessão de scraping completa
        
        Args:
            session_id: ID da sessão
            
        Returns:
            Sessão completada com resultados
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Sessão {session_id} não encontrada")
        
        session = self.active_sessions[session_id]
        
        async with self.session_semaphore:
            try:
                logger.info(f" Iniciando execução da sessão {session_id}")
                
                # Ordenar tarefas por prioridade
                sorted_tasks = sorted(session.tasks, key=lambda t: t.priority, reverse=True)
                
                # Executar tarefas em lotes concorrentes
                batch_size = self.config['max_concurrent_tasks']
                
                for i in range(0, len(sorted_tasks), batch_size):
                    batch = sorted_tasks[i:i + batch_size]
                    
                    # Executar lote concorrentemente
                    batch_results = await self._execute_task_batch(batch, session)
                    
                    # Processar resultados do lote
                    for task, result in zip(batch, batch_results):
                        if isinstance(result, ScrapedContent):
                            session.results.append(result)
                            session.completed_tasks.append(task.task_id)
                            session.total_content_extracted += len(result.content)
                        else:
                            session.failed_tasks.append(task.task_id)
                            session.errors.append(str(result))
                    
                    # Delay entre lotes para rate limiting
                    if self.config['rate_limiting']:
                        await asyncio.sleep(0.5)
                
                session.end_time = time.time()
                session.total_urls_processed = len(session.completed_tasks) + len(session.failed_tasks)
                
                logger.info(f" Sessão {session_id} concluída: {len(session.results)} sucesso, {len(session.failed_tasks)} falhas")
                return session
                
            except Exception as e:
                logger.error(f" Erro na sessão {session_id}: {str(e)}")
                session.errors.append(str(e))
                session.end_time = time.time()
                return session
    
    async def _execute_task_batch(self, tasks: List[ScrapingTask], session: ScrapingSession) -> List[Union[ScrapedContent, Exception]]:
        """Executa um lote de tarefas concorrentemente"""
        async def execute_single_task(task: ScrapingTask) -> Union[ScrapedContent, Exception]:
            try:
                return await self._execute_single_task(task)
            except Exception as e:
                logger.warning(f" Erro na tarefa {task.task_id}: {str(e)}")
                return e
        
        # Executar todas as tarefas do lote em paralelo
        tasks_coroutines = [execute_single_task(task) for task in tasks]
        results = await asyncio.gather(*tasks_coroutines, return_exceptions=True)
        
        return results
    
    async def _execute_single_task(self, task: ScrapingTask) -> ScrapedContent:
        """Executa uma única tarefa de scraping"""
        start_time = time.time()
        
        # Verificar cache
        if self.config['cache_enabled']:
            cache_key = f"scrape:{task.url}:{hash(str(task))}"
            cached_result = await self.cache.get(cache_key)
            if cached_result:
                logger.debug(f" Cache hit para {task.url}")
                return cached_result
        
        # Escolher método de scraping
        if task.javascript_required and self.config['javascript_rendering']:
            content = await self._scrape_with_selenium(task)
        else:
            content = await self._scrape_with_aiohttp(task)
        
        # Processar conteúdo extraído
        processed_content = await self._process_scraped_content(content, task)
        
        # Calcular métricas de performance
        processing_time = time.time() - start_time
        processed_content.performance_metrics = {
            'scraping_time': processing_time,
            'content_size': len(processed_content.content),
            'html_size': len(processed_content.html_content),
            'links_found': len(processed_content.links),
            'images_found': len(processed_content.images),
            'forms_found': len(processed_content.forms),
            'tables_found': len(processed_content.tables)
        }
        
        # Calcular score de qualidade
        processed_content.quality_score = self._calculate_content_quality(processed_content)
        
        # Salvar em cache
        if self.config['cache_enabled']:
            await self.cache.set(cache_key, processed_content)
        
        return processed_content
    
    async def _scrape_with_selenium(self, task: ScrapingTask) -> ScrapedContent:
        """Scraping usando Selenium para sites com JavaScript"""
        driver = None
        
        try:
            # Obter driver do pool
            driver = await self._get_driver_from_pool()
            
            # Configurar headers e proxy se necessário
            if task.custom_headers or task.user_agent:
                # Selenium não suporta headers customizados facilmente
                # Usar User-Agent via options na inicialização
                pass
            
            # Fazer scraping
            driver.get(task.url)
            
            # Esperar carregamento
            WebDriverWait(driver, task.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Esperar JavaScript executar
            await asyncio.sleep(2)
            
            # Extrair conteúdo
            title = driver.title
            html_content = driver.page_source
            
            # Extrair texto limpo
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remover scripts e styles
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            content = soup.get_text(separator=' ', strip=True)
            
            return ScrapedContent(
                url=task.url,
                task_id=task.task_id,
                title=title,
                content=content,
                html_content=html_content
            )
            
        except TimeoutException:
            raise Exception(f"Timeout ao carregar {task.url}")
        except WebDriverException as e:
            raise Exception(f"Erro WebDriver: {str(e)}")
        finally:
            if driver:
                await self._return_driver_to_pool(driver)
    
    async def _scrape_with_aiohttp(self, task: ScrapingTask) -> ScrapedContent:
        """Scraping usando aiohttp para sites estáticos"""
        headers = {}
        
        # Configurar User-Agent
        if task.user_agent:
            headers['User-Agent'] = task.user_agent
        elif self.config['user_agent_rotation']:
            headers['User-Agent'] = self._get_rotated_user_agent()
        
        # Adicionar headers customizados
        headers.update(task.custom_headers)
        
        # Configurar proxy
        proxy = None
        if task.proxy:
            proxy = task.proxy
        elif self.config['proxy_rotation']:
            proxy = self._get_rotated_proxy()
        
        # Fazer requisição
        session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=task.timeout),
            headers=headers
        )
        
        try:
            async with session.get(task.url, proxy=proxy) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}: {response.reason}")
                
                # Verificar content-type
                content_type = response.headers.get('content-type', '').lower()
                if not any(ct in content_type for ct in task.content_types):
                    raise Exception(f"Content-type não suportado: {content_type}")
                
                html_content = await response.text()
                
                # Parsear HTML
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Extrair título
                title = soup.find('title')
                title_text = title.get_text(strip=True) if title else ''
                
                # Extrair conteúdo limpo
                for script in soup(["script", "style", "nav", "footer", "header"]):
                    script.decompose()
                
                content = soup.get_text(separator=' ', strip=True)
                
                return ScrapedContent(
                    url=task.url,
                    task_id=task.task_id,
                    title=title_text,
                    content=content,
                    html_content=html_content
                )
                
        finally:
            await session.close()
    
    async def _process_scraped_content(self, content: ScrapedContent, task: ScrapingTask) -> ScrapedContent:
        """Processa e enriquece o conteúdo extraído"""
        soup = BeautifulSoup(content.html_content, 'html.parser')
        
        # Extrair links
        if self.config['link_discovery']:
            content.links = self._extract_links(soup, content.url)
        
        # Extrair imagens
        if self.config['image_extraction']:
            content.images = self._extract_images(soup, content.url)
        
        # Extrair formulários
        if self.config['form_detection']:
            content.forms = self._extract_forms(soup)
        
        # Extrair tabelas
        if self.config['table_extraction']:
            content.tables = self._extract_tables(soup)
        
        # Extrair dados estruturados
        if self.config['structured_data_extraction']:
            content.structured_data = self._extract_structured_data(soup)
        
        # Extrair dados usando o parser avançado
        parsed_data = await self.parser.parse_content(content.content)
        content.extracted_data = parsed_data
        
        # Aplicar padrões de extração customizados
        if task.extract_patterns:
            custom_data = self._apply_custom_patterns(content.content, task.extract_patterns)
            content.extracted_data.update(custom_data)
        
        # Adicionar metadados
        content.metadata.update({
            'content_length': len(content.content),
            'html_length': len(content.html_content),
            'word_count': len(content.content.split()),
            'language': self._detect_language(content.content),
            'encoding': self._detect_encoding(content.html_content),
            'last_modified': self._extract_last_modified(soup),
            'author': self._extract_author(soup),
            'description': self._extract_description(soup),
            'keywords': self._extract_keywords_meta(soup)
        })
        
        return content
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extrai links da página"""
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            text = link.get_text(strip=True)
            title = link.get('title', '')
            
            if not href or not text:
                continue
            
            # Converter URL relativa para absoluta
            absolute_url = urljoin(base_url, href)
            
            # Validar URL
            try:
                parsed = urlparse(absolute_url)
                if parsed.scheme in ['http', 'https'] and parsed.netloc:
                    links.append({
                        'url': absolute_url,
                        'text': text,
                        'title': title,
                        'domain': parsed.netloc
                    })
            except:
                continue
        
        return links[:100]  # Limitar a 100 links
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extrai imagens da página"""
        images = []
        
        for img in soup.find_all('img'):
            src = img.get('src')
            alt = img.get('alt', '')
            title = img.get('title', '')
            
            if not src:
                continue
            
            # Converter URL relativa para absoluta
            absolute_url = urljoin(base_url, src)
            
            images.append({
                'url': absolute_url,
                'alt': alt,
                'title': title,
                'width': img.get('width', ''),
                'height': img.get('height', '')
            })
        
        return images[:50]  # Limitar a 50 imagens
    
    def _extract_forms(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
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
                    'required': field.has_attr('required'),
                    'placeholder': field.get('placeholder', '')
                }
                form_data['fields'].append(field_data)
            
            forms.append(form_data)
        
        return forms
    
    def _extract_tables(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
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
    
    def _extract_structured_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extrai dados estruturados (JSON-LD, microdata)"""
        structured_data = {}
        
        # JSON-LD
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                structured_data['json_ld'] = data
                break  # Pegar apenas o primeiro
            except:
                continue
        
        # Microdata (simplificado)
        items = soup.find_all(attrs={'itemscope': True})
        if items:
            structured_data['microdata_count'] = len(items)
        
        # Open Graph
        og_data = {}
        for meta in soup.find_all('meta', property=True):
            if meta['property'].startswith('og:'):
                og_data[meta['property']] = meta.get('content', '')
        
        if og_data:
            structured_data['open_graph'] = og_data
        
        return structured_data
    
    def _apply_custom_patterns(self, content: str, patterns: Dict[str, str]) -> Dict[str, List[str]]:
        """Aplica padrões de extração customizados"""
        extracted = {}
        
        for name, pattern in patterns.items():
            try:
                matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
                if matches:
                    extracted[name] = matches[:10]  # Limitar a 10 matches
            except Exception as e:
                logger.warning(f" Erro no padrão {name}: {str(e)}")
        
        return extracted
    
    def _detect_language(self, content: str) -> str:
        """Detecta idioma do conteúdo"""
        # Implementação simplificada
        pt_indicators = ['que', 'de', 'a', 'o', 'em', 'para', 'com', 'um', 'uma', 'os', 'as']
        en_indicators = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with']
        
        content_lower = content.lower()
        pt_count = sum(1 for word in pt_indicators if word in content_lower)
        en_count = sum(1 for word in en_indicators if word in content_lower)
        
        if pt_count > en_count:
            return 'pt'
        elif en_count > pt_count:
            return 'en'
        
        return 'unknown'
    
    def _detect_encoding(self, html_content: str) -> str:
        """Detecta encoding do HTML"""
        charset_match = re.search(r'charset=["\']?([^"\'>\s]+)', html_content, re.IGNORECASE)
        if charset_match:
            return charset_match.group(1)
        return 'utf-8'
    
    def _extract_last_modified(self, soup: BeautifulSoup) -> Optional[str]:
        """Extrai data de última modificação"""
        # Provar vários metadados
        for meta_name in ['last-modified', 'date', 'publication-date', 'article:published_time']:
            meta = soup.find('meta', attrs={'name': meta_name}) or soup.find('meta', attrs={'property': meta_name})
            if meta and meta.get('content'):
                return meta['content']
        
        return None
    
    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extrai autor da página"""
        for meta_name in ['author', 'article:author']:
            meta = soup.find('meta', attrs={'name': meta_name}) or soup.find('meta', attrs={'property': meta_name})
            if meta and meta.get('content'):
                return meta['content']
        
        return None
    
    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extrai descrição da página"""
        meta = soup.find('meta', attrs={'name': 'description'})
        if meta and meta.get('content'):
            return meta['content']
        
        meta = soup.find('meta', attrs={'property': 'og:description'})
        if meta and meta.get('content'):
            return meta['content']
        
        return None
    
    def _extract_keywords_meta(self, soup: BeautifulSoup) -> List[str]:
        """Extrai keywords do meta"""
        meta = soup.find('meta', attrs={'name': 'keywords'})
        if meta and meta.get('content'):
            keywords = [k.strip() for k in meta['content'].split(',')]
            return keywords[:10]  # Limitar a 10 keywords
        
        return []
    
    def _calculate_content_quality(self, content: ScrapedContent) -> float:
        """Calcula score de qualidade do conteúdo"""
        score = 0.0
        
        # Título relevante
        if content.title and len(content.title) > 10:
            score += 0.1
        
        # Conteúdo substancial
        if len(content.content) > 500:
            score += 0.2
        elif len(content.content) > 100:
            score += 0.1
        
        # Estrutura rica
        if content.links:
            score += min(len(content.links) / 50, 0.1)
        
        if content.images:
            score += min(len(content.images) / 20, 0.1)
        
        if content.forms:
            score += min(len(content.forms) / 5, 0.1)
        
        if content.tables:
            score += min(len(content.tables) / 3, 0.1)
        
        # Dados estruturados
        if content.structured_data:
            score += 0.1
        
        # Metadados completos
        metadata_score = 0
        if content.metadata.get('author'):
            metadata_score += 0.05
        if content.metadata.get('description'):
            metadata_score += 0.05
        if content.metadata.get('keywords'):
            metadata_score += 0.05
        
        score += metadata_score
        
        # Dados extraídos
        if content.extracted_data:
            total_extracted = sum(len(v) if isinstance(v, list) else 1 for v in content.extracted_data.values())
            score += min(total_extracted / 50, 0.1)
        
        return min(score, 1.0)
    
    async def _get_driver_from_pool(self) -> webdriver.Chrome:
        """Obtém driver do pool"""
        while not self.driver_pool:
            await asyncio.sleep(0.1)
        
        return self.driver_pool.pop()
    
    async def _return_driver_to_pool(self, driver: webdriver.Chrome):
        """Retorna driver ao pool"""
        if len(self.driver_pool) < 3:  # Máximo 3 drivers no pool
            self.driver_pool.append(driver)
        else:
            driver.quit()
    
    def _get_rotated_user_agent(self) -> str:
        """Obtém User-Agent rotacionado"""
        import random
        return random.choice(self.user_agents)
    
    def _get_rotated_proxy(self) -> Optional[str]:
        """Obtém proxy rotacionado"""
        import random
        return random.choice(self.proxies)
    
    async def get_session_results(self, session_id: str) -> Optional[ScrapingSession]:
        """Obtém resultados de uma sessão"""
        return self.active_sessions.get(session_id)
    
    async def get_all_sessions(self) -> Dict[str, ScrapingSession]:
        """Obtém todas as sessões ativas"""
        return self.active_sessions.copy()
    
    async def cleanup_session(self, session_id: str):
        """Limpa uma sessão"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            logger.info(f" Sessão {session_id} removida")
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificação de saúde do scraper"""
        try:
            return {
                'status': 'healthy',
                'component': 'advanced_scraper',
                'timestamp': datetime.now().isoformat(),
                'active_sessions': len(self.active_sessions),
                'driver_pool_size': len(self.driver_pool),
                'cache_size': len(self.cache.cache),
                'config': self.config,
                'crawler_health': await self.crawler.health_check()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'component': 'advanced_scraper',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    async def cleanup(self):
        """Limpa recursos do scraper"""
        # Fechar todos os drivers
        for driver in self.driver_pool:
            try:
                driver.quit()
            except:
                pass
        
        self.driver_pool.clear()
        
        # Limpar cache
        self.cache.clear()
        
        # Limpar sessões
        self.active_sessions.clear()
        
        # Limpar crawler
        await self.crawler.cleanup()
        
        logger.info(" Advanced Scraper limpo")
