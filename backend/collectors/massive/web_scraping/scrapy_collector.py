"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - Scrapy Collector
Coletor baseado no framework Scrapy para web scraping
"""

import asyncio
import json
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging
from pathlib import Path

from ..base_collector import AsynchronousCollector, CollectorRequest, CollectorResult
from ..collector_registry import CollectorMetadata, CollectorCategory
from ...utils.logger import setup_logger

logger = setup_logger(__name__)

class ScrapyCollector(AsynchronousCollector):
    """Coletor usando framework Scrapy"""
    
    def __init__(self, config=None):
        metadata = CollectorMetadata(
            name="Scrapy",
            category=CollectorCategory.WEB_SCRAPING,
            description="Framework Python para web scraping industrial",
            version="2.11",
            author="Zyte",
            documentation_url="https://docs.scrapy.org",
            repository_url="https://github.com/scrapy/scrapy",
            tags=["scraping", "framework", "python", "crawling"],
            capabilities=["scraping", "crawling", "data_extraction", "pipeline"],
            limitations=["requer setup complexo", "necessita conhecimento Python"],
            requirements=["scrapy", "twisted", "lxml"],
            javascript_support=False,
            proxy_support=True,
            real_time=True,
            bulk_support=True
        )
        
        super().__init__("scrapy", metadata, config)
        self.spider_modules = []
        self.pipelines = []
    
    async def _setup_collector(self):
        """Setup do coletor Scrapy"""
        try:
            import scrapy
            from scrapy.crawler import CrawlerProcess
            from scrapy.utils.project import get_project_settings
            
            # Configurar processo Scrapy
            self.scrapy_process = CrawlerProcess(get_project_settings())
            
            # Adicionar pipelines padrão
            self._setup_default_pipelines()
            
            logger.info(" Scrapy collector configurado com sucesso")
            
        except ImportError:
            logger.warning(" Scrapy não instalado, usando implementação simulada")
            self.scrapy_process = None
    
    def _setup_default_pipelines(self):
        """Configura pipelines padrão do Scrapy"""
        default_pipelines = [
            'scrapy.pipelines.files.FilesPipeline',
            'scrapy.pipelines.images.ImagesPipeline',
            'scrapy.pipelines.media.MediaPipeline'
        ]
        
        for pipeline in default_pipelines:
            try:
                self.scrapy_process.settings.set('ITEM_PIPELINES', {pipeline: 300})
            except:
                continue
    
    async def _async_collect(self, request: CollectorRequest) -> Dict[str, Any]:
        """Coleta assíncrona com Scrapy"""
        if not self.scrapy_process:
            return await self._simulate_scrapy_collection(request)
        
        try:
            # Criar spider dinâmico
            spider_name = f"dynamic_spider_{request.request_id}"
            spider_class = self._create_dynamic_spider(request)
            
            # Executar spider
            items = []
            
            def item_collected(item):
                items.append(item)
            
            # Adicionar callback para coletar itens
            self.scrapy_process.signals.connect(item_collected, signal=scrapy.signals.item_scraped)
            
            # Executar crawling
            deferred = self.scrapy_process.crawl(spider_class, start_urls=[request.query])
            
            # Aguardar conclusão
            await asyncio.get_event_loop().run_in_executor(None, self.scrapy_process.start)
            
            return {
                'items': items,
                'spider_name': spider_name,
                'items_count': len(items),
                'scrapy_stats': self.scrapy_process.stats.get_stats()
            }
            
        except Exception as e:
            logger.error(f" Erro na coleta Scrapy: {str(e)}")
            return await self._simulate_scrapy_collection(request)
    
    def _create_dynamic_spider(self, request: CollectorRequest):
        """Cria spider Scrapy dinâmico"""
        import scrapy
        
        class DynamicSpider(scrapy.Spider):
            name = f"dynamic_spider_{request.request_id}"
            start_urls = [request.query] if isinstance(request.query, str) else request.query.get('urls', [])
            
            def parse(self, response):
                # Parsing básico
                yield {
                    'url': response.url,
                    'title': response.css('title::text').get(),
                    'content': response.css('body::text').getall(),
                    'links': response.css('a::attr(href)').getall(),
                    'images': response.css('img::attr(src)').getall(),
                    'timestamp': time.time()
                }
                
                # Seguir links se configurado
                if request.parameters.get('follow_links', False):
                    for link in response.css('a::attr(href)').getall():
                        if link.startswith('http'):
                            yield response.follow(link, self.parse)
        
        return DynamicSpider
    
    async def _simulate_scrapy_collection(self, request: CollectorRequest) -> Dict[str, Any]:
        """Simulação de coleta Scrapy quando não disponível"""
        try:
            import aiohttp
            from bs4 import BeautifulSoup
            
            async with aiohttp.ClientSession() as session:
                async with session.get(request.query) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        items = [{
                            'url': request.query,
                            'title': soup.title.string if soup.title else '',
                            'content': soup.get_text()[:1000],
                            'links': [a.get('href') for a in soup.find_all('a', href=True)],
                            'images': [img.get('src') for img in soup.find_all('img', src=True)],
                            'timestamp': time.time()
                        }]
                        
                        return {
                            'items': items,
                            'spider_name': 'simulated_spider',
                            'items_count': len(items),
                            'scrapy_stats': {'simulated': True}
                        }
                    else:
                        raise Exception(f"HTTP {response.status}")
                        
        except Exception as e:
            logger.error(f" Erro na simulação Scrapy: {str(e)}")
            return {
                'items': [],
                'spider_name': 'error_spider',
                'items_count': 0,
                'error': str(e)
            }
    
    async def create_spider_from_template(self, template: str, **kwargs) -> str:
        """Cria spider a partir de template"""
        spider_templates = {
            'basic': '''
import scrapy
import time

class {spider_name}(scrapy.Spider):
    name = "{spider_name}"
    start_urls = {start_urls}
    
    def parse(self, response):
        yield {{
            'url': response.url,
            'title': response.css('title::text').get(),
            'content': response.css('body::text').getall(),
            'timestamp': time.time()
        }}
        ''',
            
            'advanced': '''
import scrapy
import time

class {spider_name}(scrapy.Spider):
    name = "{spider_name}"
    start_urls = {start_urls}
    
    custom_settings = {{
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS': 16,
        'AUTOTHROTTLE_ENABLED': True
    }}
    
    def parse(self, response):
        # Extração avançada
        items = []
        
        # Extrair título
        title = response.css('h1::text, title::text').get()
        
        # Extrair conteúdo principal
        content_selectors = {content_selectors}
        for selector in content_selectors:
            elements = response.css(selector)
            for element in elements:
                items.append({{
                    'type': selector,
                    'content': element.get().strip(),
                    'url': response.url,
                    'timestamp': time.time()
                }})
        
        # Seguir links
        for link in response.css('a::attr(href)').getall():
            if link.startswith('http'):
                yield response.follow(link, self.parse)
        
        yield from items
        '''
        }
        
        template_code = spider_templates.get(template, spider_templates['basic'])
        
        # Substituir variáveis
        spider_code = template_code.format(
            spider_name=kwargs.get('spider_name', 'DynamicSpider'),
            start_urls=kwargs.get('start_urls', []),
            content_selectors=kwargs.get('content_selectors', ['p::text', 'div::text'])
        )
        
        return spider_code
    
    async def run_spider_code(self, spider_code: str) -> Dict[str, Any]:
        """Executa código de spider dinamicamente"""
        try:
            # Salvar código temporariamente
            temp_file = Path(f"/tmp/spider_{int(time.time())}.py")
            temp_file.write_text(spider_code)
            
            # Executar spider (implementação simulada)
            result = {
                'spider_file': str(temp_file),
                'execution_status': 'simulated',
                'items': [],
                'message': 'Spider code created successfully'
            }
            
            return result
            
        except Exception as e:
            logger.error(f" Erro executando spider code: {str(e)}")
            return {
                'error': str(e),
                'execution_status': 'failed'
            }
    
    async def get_scrapy_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas do Scrapy"""
        if not self.scrapy_process:
            return {'status': 'scrapy_not_available'}
        
        try:
            stats = self.scrapy_process.stats.get_stats()
            return {
                'status': 'available',
                'stats': stats,
                'active_spiders': len(stats.get('spider_count', {})),
                'items_scraped': stats.get('item_scraped_count', 0),
                'responses_received': stats.get('response_count', 0)
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
