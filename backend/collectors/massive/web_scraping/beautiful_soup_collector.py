"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - Beautiful Soup Collector
Coletor baseado na biblioteca Beautiful Soup para parsing HTML/XML
"""

import asyncio
import aiohttp
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

class Beautiful SoupCollector(AsynchronousCollector):
    """Coletor usando Beautiful Soup para parsing HTML/XML"""
    
    def __init__(self, config=None):
        metadata = CollectorMetadata(
            name="Beautiful Soup",
            category=CollectorCategory.WEB_SCRAPING,
            description="Biblioteca Python para parsing HTML/XML simplificado",
            version="4.12",
            author="Leonard Richardson",
            documentation_url="https://www.crummy.com/software/BeautifulSoup/bs4/doc/",
            repository_url="https://github.com/waylan/beautifulsoup",
            tags=["parsing", "html", "xml", "extraction"],
            capabilities=["parsing", "data_extraction", "html_processing", "xml_processing"],
            limitations=["não executa JavaScript", "requer HTML pré-carregado"],
            requirements=["beautifulsoup4", "requests", "lxml"],
            javascript_support=False,
            proxy_support=True,
            real_time=False,
            bulk_support=True
        )
        
        super().__init__("beautiful_soup", metadata, config)
        self.session = None
        self.parser = "html.parser"  # Padrão
    
    async def _setup_collector(self):
        """Setup do coletor Beautiful Soup"""
        try:
            import bs4
            from bs4 import BeautifulSoup
            
            # Testar parsers disponíveis
            available_parsers = ['html.parser', 'lxml', 'html5lib', 'xml']
            self.parser = 'html.parser'  # Padrão sempre disponível
            
            for parser in ['lxml', 'html5lib']:
                try:
                    BeautifulSoup("<test>", parser)
                    self.parser = parser
                    break
                except:
                    continue
            
            # Configurar sessão HTTP
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            headers = {
                'User-Agent': self.config.user_agent or 'BeautifulSoup-Collector/1.0'
            }
            headers.update(self.config.headers)
            
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers=headers
            )
            
            logger.info(f" Beautiful Soup collector configurado com parser: {self.parser}")
            
        except ImportError:
            logger.error(" Beautiful Soup não está instalado")
            raise
        except Exception as e:
            logger.error(f" Erro configurando Beautiful Soup: {str(e)}")
            raise
    
    async def _async_collect(self, request: CollectorRequest) -> Dict[str, Any]:
        """Coleta assíncrona com Beautiful Soup"""
        if not self.session:
            raise Exception("Sessão não inicializada")
        
        try:
            # Determinar URLs para processar
            urls = self._extract_urls(request)
            results = []
            
            for url in urls:
                try:
                    # Fazer requisição HTTP
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            content = await response.text()
                            
                            # Parse com Beautiful Soup
                            soup_data = await self._parse_with_beautiful_soup(
                                content, url, request
                            )
                            
                            results.append(soup_data)
                        else:
                            logger.warning(f" HTTP {response.status} para {url}")
                            
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
                'parser_used': self.parser,
                'extraction_time': time.time()
            }
            
        except Exception as e:
            logger.error(f" Erro na coleta Beautiful Soup: {str(e)}")
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
    
    async def _parse_with_beautiful_soup(self, html_content: str, url: str, request: CollectorRequest) -> Dict[str, Any]:
        """Faz parsing do HTML com Beautiful Soup"""
        try:
            from bs4 import BeautifulSoup
            
            # Criar objeto BeautifulSoup
            soup = BeautifulSoup(html_content, self.parser)
            
            # Extração básica
            basic_data = {
                'url': url,
                'title': self._extract_title(soup),
                'meta_description': self._extract_meta_description(soup),
                'meta_keywords': self._extract_meta_keywords(soup),
                'headings': self._extract_headings(soup),
                'paragraphs': self._extract_paragraphs(soup),
                'links': self._extract_links(soup, url),
                'images': self._extract_images(soup, url),
                'tables': self._extract_tables(soup),
                'forms': self._extract_forms(soup),
                'lists': self._extract_lists(soup),
                'text_content': soup.get_text(strip=True),
                'html_structure': self._analyze_html_structure(soup),
                'timestamp': time.time()
            }
            
            # Extração customizada baseada nos parâmetros
            custom_extractors = request.parameters.get('extractors', {})
            if custom_extractors:
                custom_data = await self._custom_extraction(soup, custom_extractors)
                basic_data.update(custom_data)
            
            # Aplicar filtros
            if request.filters:
                basic_data = self._apply_filters(basic_data, request.filters)
            
            basic_data['success'] = True
            return basic_data
            
        except Exception as e:
            logger.error(f" Erro no parsing Beautiful Soup: {str(e)}")
            return {
                'url': url,
                'error': str(e),
                'success': False
            }
    
    def _extract_title(self, soup) -> str:
        """Extrai título da página"""
        title_tag = soup.find('title')
        return title_tag.get_text(strip=True) if title_tag else ""
    
    def _extract_meta_description(self, soup) -> str:
        """Extrai meta description"""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            return meta_desc.get('content', '')
        
        meta_desc = soup.find('meta', attrs={'property': 'og:description'})
        if meta_desc:
            return meta_desc.get('content', '')
        
        return ""
    
    def _extract_meta_keywords(self, soup) -> str:
        """Extrai meta keywords"""
        meta_keys = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keys:
            return meta_keys.get('content', '')
        
        return ""
    
    def _extract_headings(self, soup) -> Dict[str, List[str]]:
        """Extrai cabeçalhos (h1-h6)"""
        headings = {}
        
        for i in range(1, 7):
            heading_tags = soup.find_all(f'h{i}')
            headings[f'h{i}'] = [tag.get_text(strip=True) for tag in heading_tags]
        
        return headings
    
    def _extract_paragraphs(self, soup) -> List[str]:
        """Extrai parágrafos"""
        paragraphs = soup.find_all('p')
        return [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]
    
    def _extract_links(self, soup, base_url: str) -> List[Dict[str, str]]:
        """Extrai links"""
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            text = link.get_text(strip=True)
            title = link.get('title', '')
            
            # Converter URL relativa para absoluta
            if href and not href.startswith(('http://', 'https://', 'mailto:', 'tel:')):
                href = urljoin(base_url, href)
            
            links.append({
                'url': href,
                'text': text,
                'title': title
            })
        
        return links
    
    def _extract_images(self, soup, base_url: str) -> List[Dict[str, str]]:
        """Extrai imagens"""
        images = []
        
        for img in soup.find_all('img'):
            src = img.get('src')
            alt = img.get('alt', '')
            title = img.get('title', '')
            
            # Converter URL relativa para absoluta
            if src and not src.startswith(('http://', 'https://')):
                src = urljoin(base_url, src)
            
            images.append({
                'src': src,
                'alt': alt,
                'title': title
            })
        
        return images
    
    def _extract_tables(self, soup) -> List[Dict[str, Any]]:
        """Extrai tabelas"""
        tables = []
        
        for table in soup.find_all('table'):
            table_data = {
                'headers': [],
                'rows': []
            }
            
            # Extrair headers
            header_row = table.find('tr')
            if header_row:
                headers = header_row.find_all(['th', 'td'])
                table_data['headers'] = [h.get_text(strip=True) for h in headers]
            
            # Extrair linhas de dados
            for row in table.find_all('tr')[1:]:  # Pular header se existir
                cells = row.find_all(['td', 'th'])
                row_data = [cell.get_text(strip=True) for cell in cells]
                table_data['rows'].append(row_data)
            
            tables.append(table_data)
        
        return tables
    
    def _extract_forms(self, soup) -> List[Dict[str, Any]]:
        """Extrai formulários"""
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
                    'type': field.get('type', field.name),
                    'value': field.get('value', ''),
                    'placeholder': field.get('placeholder', ''),
                    'required': field.has_attr('required')
                }
                form_data['fields'].append(field_data)
            
            forms.append(form_data)
        
        return forms
    
    def _extract_lists(self, soup) -> Dict[str, List[str]]:
        """Extrai listas (ul, ol, dl)"""
        lists = {
            'unordered': [],
            'ordered': [],
            'definition': []
        }
        
        # Listas não ordenadas (ul)
        for ul in soup.find_all('ul'):
            items = [li.get_text(strip=True) for li in ul.find_all('li')]
            lists['unordered'].append(items)
        
        # Listas ordenadas (ol)
        for ol in soup.find_all('ol'):
            items = [li.get_text(strip=True) for li in ol.find_all('li')]
            lists['ordered'].append(items)
        
        # Listas de definição (dl)
        for dl in soup.find_all('dl'):
            dt_items = [dt.get_text(strip=True) for dt in dl.find_all('dt')]
            dd_items = [dd.get_text(strip=True) for dd in dl.find_all('dd')]
            lists['definition'].append({'terms': dt_items, 'definitions': dd_items})
        
        return lists
    
    def _analyze_html_structure(self, soup) -> Dict[str, Any]:
        """Analisa estrutura do HTML"""
        structure = {
            'total_elements': len(soup.find_all()),
            'element_counts': {},
            'depth': self._calculate_html_depth(soup),
            'has_doctype': bool(soup.find(lambda tag: tag.name == '!DOCTYPE')),
            'encoding': self._detect_encoding(soup)
        }
        
        # Contar elementos por tipo
        for tag in soup.find_all():
            tag_name = tag.name
            structure['element_counts'][tag_name] = structure['element_counts'].get(tag_name, 0) + 1
        
        return structure
    
    def _calculate_html_depth(self, soup) -> int:
        """Calcula profundidade máxima do HTML"""
        def max_depth(element, current_depth=0):
            if not hasattr(element, 'contents'):
                return current_depth
            
            max_child_depth = current_depth
            for child in element.contents:
                if hasattr(child, 'name') and child.name:
                    child_depth = max_depth(child, current_depth + 1)
                    max_child_depth = max(max_child_depth, child_depth)
            
            return max_child_depth
        
        return max_depth(soup)
    
    def _detect_encoding(self, soup) -> str:
        """Detecta encoding do HTML"""
        # Procurar charset meta tag
        charset_meta = soup.find('meta', attrs={'charset': True})
        if charset_meta:
            return charset_meta.get('charset', '')
        
        # Procurar charset em content
        content_meta = soup.find('meta', attrs={'content': True})
        if content_meta:
            content = content_meta.get('content', '')
            if 'charset=' in content:
                return content.split('charset=')[1].split(';')[0].strip()
        
        return 'utf-8'  # Padrão
    
    async def _custom_extraction(self, soup, extractors: Dict[str, Any]) -> Dict[str, Any]:
        """Executa extração customizada"""
        custom_data = {}
        
        for extractor_name, extractor_config in extractors.items():
            try:
                if extractor_name == 'css_selectors':
                    custom_data['css_extraction'] = self._extract_by_css_selectors(soup, extractor_config)
                elif extractor_name == 'xpath':
                    custom_data['xpath_extraction'] = self._extract_by_xpath(soup, extractor_config)
                elif extractor_name == 'regex':
                    custom_data['regex_extraction'] = self._extract_by_regex(soup, extractor_config)
                elif extractor_name == 'attributes':
                    custom_data['attributes_extraction'] = self._extract_attributes(soup, extractor_config)
            except Exception as e:
                logger.warning(f" Erro no extrator customizado {extractor_name}: {str(e)}")
        
        return custom_data
    
    def _extract_by_css_selectors(self, soup, selectors: Dict[str, str]) -> Dict[str, List[str]]:
        """Extrai dados usando seletores CSS"""
        results = {}
        
        for name, selector in selectors.items():
            elements = soup.select(selector)
            results[name] = [elem.get_text(strip=True) for elem in elements]
        
        return results
    
    def _extract_by_xpath(self, soup, xpath_queries: Dict[str, str]) -> Dict[str, List[str]]:
        """Extrai dados usando XPath (requer lxml)"""
        results = {}
        
        try:
            from lxml import etree
            
            # Converter BeautifulSoup para lxml
            dom = etree.HTML(str(soup))
            
            for name, xpath in xpath_queries.items():
                elements = dom.xpath(xpath)
                results[name] = [str(elem) for elem in elements]
                
        except ImportError:
            logger.warning(" lxml não disponível para XPath")
        
        return results
    
    def _extract_by_regex(self, soup, patterns: Dict[str, str]) -> Dict[str, List[str]]:
        """Extrai dados usando expressões regulares"""
        import re
        
        results = {}
        text_content = soup.get_text()
        
        for name, pattern in patterns.items():
            matches = re.findall(pattern, text_content, re.IGNORECASE | re.MULTILINE)
            results[name] = matches
        
        return results
    
    def _extract_attributes(self, soup, attributes_config: Dict[str, Any]) -> Dict[str, List[str]]:
        """Extrai atributos específicos"""
        results = {}
        
        for attr_name, config in attributes_config.items():
            tag_name = config.get('tag', '*')
            elements = soup.find_all(tag_name)
            
            attr_values = []
            for elem in elements:
                if elem.has_attr(attr_name):
                    attr_values.append(elem.get(attr_name))
            
            results[attr_name] = attr_values
        
        return results
    
    def _apply_filters(self, data: Dict[str, Any], filters: Dict[str, Any]) -> Dict[str, Any]:
        """Aplica filtros aos dados extraídos"""
        filtered_data = data.copy()
        
        # Filtrar por tamanho mínimo
        if 'min_text_length' in filters:
            min_length = filters['min_text_length']
            if 'text_content' in filtered_data:
                if len(filtered_data['text_content']) < min_length:
                    filtered_data['filtered'] = 'text_too_short'
        
        # Filtrar por palavras-chave
        if 'required_keywords' in filters:
            keywords = filters['required_keywords']
            text = filtered_data.get('text_content', '').lower()
            
            if not any(keyword.lower() in text for keyword in keywords):
                filtered_data['filtered'] = 'keywords_not_found'
        
        # Filtrar elementos vazios
        if 'remove_empty' in filters and filters['remove_empty']:
            for key, value in filtered_data.items():
                if isinstance(value, list):
                    filtered_data[key] = [v for v in value if v and str(v).strip()]
        
        return filtered_data
    
    async def validate_html(self, html_content: str) -> Dict[str, Any]:
        """Valida estrutura HTML"""
        try:
            from bs4 import BeautifulSoup
            
            soup = BeautifulSoup(html_content, self.parser)
            
            validation = {
                'is_valid': True,
                'errors': [],
                'warnings': [],
                'structure': self._analyze_html_structure(soup)
            }
            
            # Verificar elementos básicos
            if not soup.find('title'):
                validation['warnings'].append('Sem título')
            
            if not soup.find('body'):
                validation['warnings'].append('Sem body')
            
            # Verificar tags não fechadas (simplificado)
            unclosed_tags = []
            for tag in soup.find_all():
                if tag.name in ['img', 'br', 'hr', 'input', 'meta', 'link']:
                    continue  # Self-closing tags
                
                # Verificar se tag tem fechamento correspondente
                if not tag.find_next_sibling() and not tag.contents:
                    unclosed_tags.append(tag.name)
            
            if unclosed_tags:
                validation['warnings'].append(f'Tags possivelmente não fechadas: {set(unclosed_tags)}')
            
            return validation
            
        except Exception as e:
            return {
                'is_valid': False,
                'errors': [str(e)],
                'warnings': []
            }
    
    async def cleanup(self):
        """Limpa recursos do coletor"""
        if self.session:
            await self.session.close()
        
        await super().cleanup()
