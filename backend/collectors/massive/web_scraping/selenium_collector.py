"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - Selenium Collector
Coletor baseado no Selenium para automação de navegadores web
"""

import asyncio
import json
import time
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
import logging
from urllib.parse import urljoin, urlparse

from ..base_collector import AsynchronousCollector, CollectorRequest, CollectorResult
from ..collector_registry import CollectorMetadata, CollectorCategory
from ...utils.logger import setup_logger

logger = setup_logger(__name__)

class SeleniumCollector(AsynchronousCollector):
    """Coletor usando Selenium para automação de navegadores"""
    
    def __init__(self, config=None):
        metadata = CollectorMetadata(
            name="Selenium",
            category=CollectorCategory.WEB_SCRAPING,
            description="Automação de navegadores web para scraping dinâmico",
            version="4.15",
            author="Selenium Team",
            documentation_url="https://selenium-python.readthedocs.io",
            repository_url="https://github.com/SeleniumHQ/selenium",
            tags=["automation", "browser", "javascript", "dynamic"],
            capabilities=["browser_automation", "javascript_execution", "screenshot", "dynamic_scraping"],
            limitations=["requer browser instalado", "consome muitos recursos"],
            requirements=["selenium", "webdriver-manager"],
            javascript_support=True,
            proxy_support=True,
            real_time=True,
            bulk_support=False
        )
        
        super().__init__("selenium", metadata, config)
        self.driver = None
        self.driver_options = None
        self.browser_type = "chrome"  # Padrão
    
    async def _setup_collector(self):
        """Setup do coletor Selenium"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options as ChromeOptions
            from selenium.webdriver.firefox.options import Options as FirefoxOptions
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.chrome.service import Service as ChromeService
            from selenium.webdriver.firefox.service import Service as FirefoxService
            from webdriver_manager.chrome import ChromeDriverManager
            from webdriver_manager.firefox import GeckoDriverManager
            
            # Configurar opções do browser
            self.driver_options = self._setup_browser_options()
            
            # Inicializar driver
            if self.browser_type == "chrome":
                service = ChromeService(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=self.driver_options)
            elif self.browser_type == "firefox":
                service = FirefoxService(GeckoDriverManager().install())
                self.driver = webdriver.Firefox(service=service, options=self.driver_options)
            else:
                raise ValueError(f"Browser não suportado: {self.browser_type}")
            
            # Configurar timeouts
            self.driver.set_page_load_timeout(self.config.timeout)
            self.driver.implicitly_wait(10)
            
            logger.info(f" Selenium collector configurado com browser: {self.browser_type}")
            
        except ImportError:
            logger.error(" Selenium não está instalado")
            raise
        except Exception as e:
            logger.error(f" Erro configurando Selenium: {str(e)}")
            raise
    
    def _setup_browser_options(self):
        """Configura opções do browser"""
        if self.browser_type == "chrome":
            from selenium.webdriver.chrome.options import Options
            options = Options()
            
            # Opções de performance
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-plugins')
            options.add_argument('--disable-images')  # Para performance
            options.add_argument('--disable-javascript') if not self.config.custom_params.get('javascript_enabled', True) else None
            
            # Headless mode
            if self.config.custom_params.get('headless', True):
                options.add_argument('--headless')
                options.add_argument('--window-size=1920,1080')
            
            # User agent
            if self.config.user_agent:
                options.add_argument(f'--user-agent={self.config.user_agent}')
            
            # Proxy
            if self.config.proxy_enabled and self.config.proxy_list:
                proxy = self.config.proxy_list[0]
                options.add_argument(f'--proxy-server={proxy}')
            
            return options
            
        elif self.browser_type == "firefox":
            from selenium.webdriver.firefox.options import Options
            options = Options()
            
            # Headless mode
            if self.config.custom_params.get('headless', True):
                options.add_argument('--headless')
            
            # User agent
            if self.config.user_agent:
                options.set_preference("general.useragent.override", self.config.user_agent)
            
            # Proxy
            if self.config.proxy_enabled and self.config.proxy_list:
                proxy = self.config.proxy_list[0]
                options.set_preference("network.proxy.type", 1)
                options.set_preference("network.proxy.http", proxy.split(':')[0])
                options.set_preference("network.proxy.http_port", int(proxy.split(':')[1]))
            
            return options
    
    async def _async_collect(self, request: CollectorRequest) -> Dict[str, Any]:
        """Coleta assíncrona com Selenium"""
        if not self.driver:
            raise Exception("Driver não inicializado")
        
        try:
            # Determinar URLs para processar
            urls = self._extract_urls(request)
            results = []
            
            for url in urls:
                try:
                    # Navegar para URL
                    await self._navigate_to_url(url)
                    
                    # Esperar carregamento
                    await self._wait_for_page_load()
                    
                    # Executar JavaScript se necessário
                    if request.parameters.get('execute_js', False):
                        await self._execute_javascript(request.parameters.get('js_code', ''))
                    
                    # Tirar screenshot se solicitado
                    screenshot = None
                    if request.parameters.get('screenshot', False):
                        screenshot = await self._take_screenshot()
                    
                    # Extrair dados
                    selenium_data = await self._extract_selenium_data(url, request)
                    
                    if screenshot:
                        selenium_data['screenshot'] = screenshot
                    
                    results.append(selenium_data)
                    
                except Exception as e:
                    logger.error(f" Erro processando {url}: {str(e)}")
                    results.append({
                        'url': url,
                        'error': str(e),
                        'success': False
                    })
            
            return {
                'results': results,
                'total_urls': len(urls),
                'successful': len([r for r in results if r.get('success', True)]),
                'browser_type': self.browser_type,
                'collection_time': time.time()
            }
            
        except Exception as e:
            logger.error(f" Erro na coleta Selenium: {str(e)}")
            raise
    
    def _extract_urls(self, request: CollectorRequest) -> List[str]:
        """Extrai URLs da requisição"""
        if isinstance(request.query, str):
            return [request.query]
        elif isinstance(request.query, list):
            return request.query
        elif isinstance(request.query, dict):
            return request.query.get('urls', [])
        else:
            return []
    
    async def _navigate_to_url(self, url: str):
        """Navega para URL com tratamento de erros"""
        try:
            self.driver.get(url)
        except Exception as e:
            logger.error(f" Erro navegando para {url}: {str(e)}")
            raise
    
    async def _wait_for_page_load(self):
        """Espera carregamento completo da página"""
        try:
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            # Esperar pelo menos o body estar presente
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Esperar adicional para JavaScript
            await asyncio.sleep(2)
            
        except Exception as e:
            logger.warning(f" Timeout esperando carregamento: {str(e)}")
    
    async def _execute_javascript(self, js_code: str):
        """Executa código JavaScript na página"""
        try:
            result = self.driver.execute_script(js_code)
            logger.debug(f" JavaScript executado: {result}")
            return result
        except Exception as e:
            logger.error(f" Erro executando JavaScript: {str(e)}")
            return None
    
    async def _take_screenshot(self) -> str:
        """Tira screenshot da página"""
        try:
            screenshot_data = self.driver.get_screenshot_as_png()
            import base64
            return base64.b64encode(screenshot_data).decode()
        except Exception as e:
            logger.error(f" Erro tirando screenshot: {str(e)}")
            return ""
    
    async def _extract_selenium_data(self, url: str, request: CollectorRequest) -> Dict[str, Any]:
        """Extrai dados usando Selenium"""
        try:
            from selenium.webdriver.common.by import By
            from bs4 import BeautifulSoup
            
            # Obter HTML após renderização
            html_content = self.driver.page_source
            
            # Parse com Beautiful Soup para extração
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extração básica
            basic_data = {
                'url': url,
                'title': self.driver.title,
                'current_url': self.driver.current_url,
                'window_handles': len(self.driver.window_handles),
                'cookies': len(self.driver.get_cookies()),
                'local_storage': await self._get_local_storage(),
                'session_storage': await self._get_session_storage(),
                'console_logs': await self._get_console_logs(),
                'network_logs': await self._get_network_logs(),
                'page_metrics': await self._get_page_metrics(),
                'dynamic_content': await self._extract_dynamic_content(request),
                'timestamp': time.time()
            }
            
            # Extração de elementos
            elements_data = {
                'headings': self._extract_headings_selenium(),
                'paragraphs': self._extract_paragraphs_selenium(),
                'links': self._extract_links_selenium(url),
                'images': self._extract_images_selenium(url),
                'forms': self._extract_forms_selenium(),
                'tables': self._extract_tables_selenium(),
                'buttons': self._extract_buttons_selenium(),
                'inputs': self._extract_inputs_selenium(),
                'scripts': self._extract_scripts_selenium()
            }
            
            basic_data.update(elements_data)
            basic_data['success'] = True
            
            return basic_data
            
        except Exception as e:
            logger.error(f" Erro extração Selenium: {str(e)}")
            return {
                'url': url,
                'error': str(e),
                'success': False
            }
    
    async def _get_local_storage(self) -> Dict[str, Any]:
        """Obtém dados do localStorage"""
        try:
            local_storage = self.driver.execute_script(
                "return Object.keys(localStorage).reduce((obj, key) => { obj[key] = localStorage[key]; return obj; }, {});"
            )
            return local_storage
        except:
            return {}
    
    async def _get_session_storage(self) -> Dict[str, Any]:
        """Obtém dados do sessionStorage"""
        try:
            session_storage = self.driver.execute_script(
                "return Object.keys(sessionStorage).reduce((obj, key) => { obj[key] = sessionStorage[key]; return obj; }, {});"
            )
            return session_storage
        except:
            return {}
    
    async def _get_console_logs(self) -> List[Dict[str, Any]]:
        """Obtém logs do console"""
        try:
            from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
            
            # Habilitar logging
            desired = DesiredCapabilities.CHROME
            desired['loggingPrefs'] = {'browser': 'ALL'}
            
            logs = self.driver.get_log('browser')
            return [{'level': log['level'], 'message': log['message'], 'timestamp': log['timestamp']} for log in logs]
        except:
            return []
    
    async def _get_network_logs(self) -> List[Dict[str, Any]]:
        """Obtém logs de rede (simplificado)"""
        try:
            # Usar Performance API para obter logs de rede
            network_logs = self.driver.execute_script("""
                return performance.getEntriesByType('resource').map(entry => ({
                    name: entry.name,
                    type: entry.initiatorType,
                    duration: entry.duration,
                    size: entry.transferSize
                }));
            """)
            return network_logs
        except:
            return []
    
    async def _get_page_metrics(self) -> Dict[str, Any]:
        """Obtém métricas da página"""
        try:
            metrics = self.driver.execute_script("""
                return {
                    load_time: performance.timing.loadEventEnd - performance.timing.navigationStart,
                    dom_content_loaded: performance.timing.domContentLoadedEventEnd - performance.timing.navigationStart,
                    first_paint: performance.getEntriesByType('paint')[0]?.startTime || 0,
                    first_contentful_paint: performance.getEntriesByType('paint')[1]?.startTime || 0
                };
            """)
            return metrics
        except:
            return {}
    
    async def _extract_dynamic_content(self, request: CollectorRequest) -> Dict[str, Any]:
        """Extrai conteúdo dinâmico"""
        dynamic_data = {}
        
        try:
            # Esperar por conteúdo dinâmico
            wait_selectors = request.parameters.get('wait_selectors', [])
            for selector in wait_selectors:
                try:
                    from selenium.webdriver.support.ui import WebDriverWait
                    from selenium.webdriver.support import expected_conditions as EC
                    
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    dynamic_data[f'waited_for_{selector}'] = True
                except:
                    dynamic_data[f'waited_for_{selector}'] = False
            
            # Extrair conteúdo após interações
            interactions = request.parameters.get('interactions', [])
            for interaction in interactions:
                result = await self._perform_interaction(interaction)
                dynamic_data[f'interaction_{interaction["type"]}'] = result
            
            # Scroll infinito
            if request.parameters.get('infinite_scroll', False):
                scroll_data = await self._handle_infinite_scroll()
                dynamic_data['infinite_scroll'] = scroll_data
            
        except Exception as e:
            logger.warning(f" Erro extração dinâmica: {str(e)}")
        
        return dynamic_data
    
    async def _perform_interaction(self, interaction: Dict[str, Any]) -> Dict[str, Any]:
        """Realiza interação na página"""
        try:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.common.action_chains import ActionChains
            
            interaction_type = interaction.get('type')
            selector = interaction.get('selector')
            
            if interaction_type == 'click':
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                element.click()
                return {'action': 'clicked', 'element': selector}
            
            elif interaction_type == 'scroll':
                scroll_to = interaction.get('scroll_to', 'bottom')
                if scroll_to == 'bottom':
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                elif scroll_to == 'top':
                    self.driver.execute_script("window.scrollTo(0, 0);")
                return {'action': 'scrolled', 'to': scroll_to}
            
            elif interaction_type == 'type':
                text = interaction.get('text', '')
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                element.clear()
                element.send_keys(text)
                return {'action': 'typed', 'text': text, 'element': selector}
            
            elif interaction_type == 'hover':
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                ActionChains(self.driver).move_to_element(element).perform()
                return {'action': 'hovered', 'element': selector}
            
            else:
                return {'action': 'unknown', 'type': interaction_type}
                
        except Exception as e:
            return {'action': 'error', 'error': str(e)}
    
    async def _handle_infinite_scroll(self) -> Dict[str, Any]:
        """Lida com scroll infinito"""
        scroll_data = {
            'scrolls_performed': 0,
            'new_items_found': 0,
            'final_height': 0
        }
        
        try:
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            for i in range(10):  # Máximo 10 scrolls
                # Scroll para o final
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                # Esperar carregar
                await asyncio.sleep(2)
                
                # Calcular nova altura
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                
                if new_height == last_height:
                    break
                
                last_height = new_height
                scroll_data['scrolls_performed'] += 1
                scroll_data['new_items_found'] = new_height - scroll_data.get('final_height', 0)
                scroll_data['final_height'] = new_height
            
        except Exception as e:
            logger.warning(f" Erro no scroll infinito: {str(e)}")
        
        return scroll_data
    
    def _extract_headings_selenium(self) -> Dict[str, List[str]]:
        """Extrai cabeçalhos com Selenium"""
        from selenium.webdriver.common.by import By
        
        headings = {}
        for i in range(1, 7):
            elements = self.driver.find_elements(By.TAG_NAME, f'h{i}')
            headings[f'h{i}'] = [elem.text for elem in elements if elem.text.strip()]
        
        return headings
    
    def _extract_paragraphs_selenium(self) -> List[str]:
        """Extrai parágrafos com Selenium"""
        from selenium.webdriver.common.by import By
        
        paragraphs = self.driver.find_elements(By.TAG_NAME, 'p')
        return [p.text for p in paragraphs if p.text.strip()]
    
    def _extract_links_selenium(self, base_url: str) -> List[Dict[str, str]]:
        """Extrai links com Selenium"""
        from selenium.webdriver.common.by import By
        
        links = []
        elements = self.driver.find_elements(By.TAG_NAME, 'a')
        
        for elem in elements:
            href = elem.get_attribute('href')
            text = elem.text.strip()
            title = elem.get_attribute('title') or ''
            
            if href:
                links.append({
                    'url': href,
                    'text': text,
                    'title': title
                })
        
        return links
    
    def _extract_images_selenium(self, base_url: str) -> List[Dict[str, str]]:
        """Extrai imagens com Selenium"""
        from selenium.webdriver.common.by import By
        
        images = []
        elements = self.driver.find_elements(By.TAG_NAME, 'img')
        
        for elem in elements:
            src = elem.get_attribute('src')
            alt = elem.get_attribute('alt') or ''
            title = elem.get_attribute('title') or ''
            
            if src:
                images.append({
                    'src': src,
                    'alt': alt,
                    'title': title
                })
        
        return images
    
    def _extract_forms_selenium(self) -> List[Dict[str, Any]]:
        """Extrai formulários com Selenium"""
        from selenium.webdriver.common.by import By
        
        forms = []
        elements = self.driver.find_elements(By.TAG_NAME, 'form')
        
        for elem in elements:
            form_data = {
                'action': elem.get_attribute('action') or '',
                'method': elem.get_attribute('method') or 'GET',
                'fields': []
            }
            
            # Extrair campos do formulário
            fields = elem.find_elements(By.TAG_NAME, 'input')
            for field in fields:
                field_data = {
                    'name': field.get_attribute('name') or '',
                    'type': field.get_attribute('type') or 'text',
                    'value': field.get_attribute('value') or '',
                    'placeholder': field.get_attribute('placeholder') or '',
                    'required': field.get_attribute('required') is not None
                }
                form_data['fields'].append(field_data)
            
            forms.append(form_data)
        
        return forms
    
    def _extract_tables_selenium(self) -> List[Dict[str, Any]]:
        """Extrai tabelas com Selenium"""
        from selenium.webdriver.common.by import By
        
        tables = []
        elements = self.driver.find_elements(By.TAG_NAME, 'table')
        
        for elem in elements:
            table_data = {
                'headers': [],
                'rows': []
            }
            
            # Headers
            header_cells = elem.find_elements(By.TAG_NAME, 'th')
            table_data['headers'] = [cell.text for cell in header_cells]
            
            # Linhas
            rows = elem.find_elements(By.TAG_NAME, 'tr')
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, 'td')
                row_data = [cell.text for cell in cells]
                if row_data:
                    table_data['rows'].append(row_data)
            
            tables.append(table_data)
        
        return tables
    
    def _extract_buttons_selenium(self) -> List[Dict[str, str]]:
        """Extrai botões com Selenium"""
        from selenium.webdriver.common.by import By
        
        buttons = []
        elements = self.driver.find_elements(By.TAG_NAME, 'button')
        
        for elem in elements:
            button_data = {
                'text': elem.text.strip(),
                'type': elem.get_attribute('type') or '',
                'class': elem.get_attribute('class') or '',
                'id': elem.get_attribute('id') or ''
            }
            buttons.append(button_data)
        
        return buttons
    
    def _extract_inputs_selenium(self) -> List[Dict[str, str]]:
        """Extrai inputs com Selenium"""
        from selenium.webdriver.common.by import By
        
        inputs = []
        elements = self.driver.find_elements(By.TAG_NAME, 'input')
        
        for elem in elements:
            input_data = {
                'name': elem.get_attribute('name') or '',
                'type': elem.get_attribute('type') or 'text',
                'value': elem.get_attribute('value') or '',
                'placeholder': elem.get_attribute('placeholder') or '',
                'id': elem.get_attribute('id') or '',
                'class': elem.get_attribute('class') or ''
            }
            inputs.append(input_data)
        
        return inputs
    
    def _extract_scripts_selenium(self) -> List[Dict[str, str]]:
        """Extrai scripts com Selenium"""
        from selenium.webdriver.common.by import By
        
        scripts = []
        elements = self.driver.find_elements(By.TAG_NAME, 'script')
        
        for elem in elements:
            script_data = {
                'src': elem.get_attribute('src') or '',
                'type': elem.get_attribute('type') or '',
                'has_content': bool(elem.get_attribute('innerHTML'))
            }
            scripts.append(script_data)
        
        return scripts
    
    async def switch_browser(self, browser_type: str):
        """Muda tipo de browser"""
        if self.browser_type == browser_type:
            return
        
        # Fechar driver atual
        if self.driver:
            self.driver.quit()
        
        # Mudar tipo e reinicializar
        self.browser_type = browser_type
        await self._setup_collector()
    
    async def cleanup(self):
        """Limpa recursos do coletor"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
        
        await super().cleanup()
