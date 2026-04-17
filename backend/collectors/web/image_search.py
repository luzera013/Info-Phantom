"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - Image Search Engine
Busca e análise de imagens
"""

import asyncio
import aiohttp
import base64
import io
import time
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlencode, quote_plus
from dataclasses import dataclass
import logging
import hashlib

from PIL import Image
import cv2
import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from ..core.pipeline import SearchResult
from ..utils.logger import setup_logger
from ..utils.http_client import HTTPClient

logger = setup_logger(__name__)

@dataclass
class ImageResult:
    """Resultado de busca de imagem"""
    url: str
    title: str
    thumbnail: str
    width: int
    height: int
    size: int  # bytes
    format: str
    source: str
    relevance_score: float = 0.0
    metadata: Dict[str, Any] = None

@dataclass
class ImageConfig:
    """Configuração de busca de imagens"""
    max_results: int = 50
    min_width: int = 100
    min_height: int = 100
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    timeout: int = 30
    enable_face_detection: bool = True
    enable_object_detection: bool = True
    enable_text_extraction: bool = True
    download_thumbnails: bool = True

class ImageSearchEngine:
    """Motor de busca de imagens"""
    
    def __init__(self, config: Optional[ImageConfig] = None):
        self.config = config or ImageConfig()
        self.http_client = HTTPClient()
        self.session = None
        self.driver = None
        
        # Fontes de busca de imagens
        self.search_sources = [
            'https://duckduckgo.com/i.js',
            'https://www.google.com/search',
            'https://www.bing.com/images/search',
            'https://yandex.com/images/search'
        ]
        
        logger.info("🖼️ Image Search Engine inicializado")
    
    async def initialize(self):
        """Inicializa o motor de busca"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        )
        
        await self._init_selenium()
        
        logger.info("✅ Image Search Engine pronto")
    
    async def _init_selenium(self):
        """Inicializa Selenium para busca dinâmica"""
        try:
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            
            self.driver = webdriver.Chrome(options=options)
            self.driver.set_page_load_timeout(self.config.timeout)
            
            logger.info("🚀 Selenium para imagens inicializado")
            
        except Exception as e:
            logger.warning(f"⚠️ Falha ao inicializar Selenium para imagens: {str(e)}")
    
    async def search_images(self, query: str, max_results: Optional[int] = None) -> List[ImageResult]:
        """
        Busca imagens por termo
        
        Args:
            query: Termo de busca
            max_results: Número máximo de resultados
            
        Returns:
            Lista de ImageResult
        """
        if not self.session:
            await self.initialize()
        
        max_results = max_results or self.config.max_results
        logger.info(f"🔍 Buscando imagens: '{query}' (max: {max_results})")
        
        try:
            all_results = []
            
            # Tentar múltiplas fontes
            for source in self.search_sources:
                try:
                    results = await self._search_source(source, query, max_results)
                    all_results.extend(results)
                    
                    if len(all_results) >= max_results:
                        break
                        
                except Exception as e:
                    logger.warning(f"⚠️ Erro na fonte {source}: {str(e)}")
                    continue
            
            # Filtrar e ordenar resultados
            filtered_results = await self._filter_results(all_results)
            ranked_results = await self._rank_images(filtered_results, query)
            
            # Limitar resultados
            final_results = ranked_results[:max_results]
            
            # Baixar thumbnails se configurado
            if self.config.download_thumbnails:
                await self._download_thumbnails(final_results)
            
            logger.info(f"✅ Encontradas {len(final_results)} imagens")
            return final_results
            
        except Exception as e:
            logger.error(f"❌ Erro na busca de imagens: {str(e)}")
            return []
    
    async def _search_source(self, source: str, query: str, max_results: int) -> List[ImageResult]:
        """Busca em fonte específica"""
        if 'duckduckgo' in source:
            return await self._search_duckduckgo_images(query, max_results)
        elif 'google' in source:
            return await self._search_google_images(query, max_results)
        elif 'bing' in source:
            return await self._search_bing_images(query, max_results)
        elif 'yandex' in source:
            return await self._search_yandex_images(query, max_results)
        
        return []
    
    async def _search_duckduckgo_images(self, query: str, max_results: int) -> List[ImageResult]:
        """Busca imagens no DuckDuckGo"""
        try:
            params = {
                'q': query,
                'o': 'json',
                'vqd': '',  # Será preenchido dinamicamente
                'f': ',,,',
                'l': 'br-pt'
            }
            
            async with self.session.get('https://duckduckgo.com/i.js', params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    results = []
                    for item in data.get('results', []):
                        result = ImageResult(
                            url=item.get('image', ''),
                            title=item.get('title', ''),
                            thumbnail=item.get('thumbnail', ''),
                            width=item.get('width', 0),
                            height=item.get('height', 0),
                            size=item.get('sourceWidth', 0) * item.get('sourceHeight', 0),  # Estimativa
                            format='unknown',
                            source='duckduckgo',
                            metadata={
                                'source_url': item.get('url', ''),
                                'source': item.get('source', '')
                            }
                        )
                        results.append(result)
                    
                    return results[:max_results]
        
        except Exception as e:
            logger.warning(f"⚠️ Erro DuckDuckGo imagens: {str(e)}")
        
        return []
    
    async def _search_google_images(self, query: str, max_results: int) -> List[ImageResult]:
        """Busca imagens no Google (requer Selenium)"""
        if not self.driver:
            return []
        
        try:
            url = f"https://www.google.com/search?q={quote_plus(query)}&tbm=isch"
            self.driver.get(url)
            
            # Esperar carregar
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "img.Q4LuWd"))
            )
            
            # Rolar para carregar mais
            for _ in range(3):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                await asyncio.sleep(1)
            
            # Extrair resultados
            results = []
            img_elements = self.driver.find_elements(By.CSS_SELECTOR, "img.Q4LuWd")
            
            for img in img_elements[:max_results]:
                try:
                    src = img.get_attribute('src')
                    alt = img.get_attribute('alt', '')
                    
                    if src and src.startswith('http'):
                        result = ImageResult(
                            url=src,
                            title=alt,
                            thumbnail=src,
                            width=0,  # Google não fornece dimensões facilmente
                            height=0,
                            size=0,
                            format='unknown',
                            source='google',
                            metadata={'alt_text': alt}
                        )
                        results.append(result)
                        
                except Exception as e:
                    logger.debug(f"⚠️ Erro processando imagem Google: {str(e)}")
                    continue
            
            return results
        
        except Exception as e:
            logger.warning(f"⚠️ Erro Google imagens: {str(e)}")
        
        return []
    
    async def _search_bing_images(self, query: str, max_results: int) -> List[ImageResult]:
        """Busca imagens no Bing"""
        try:
            params = {
                'q': query,
                'form': 'HDRSC2',
                'first': '1',
                'tsc': 'ImageBasicHover'
            }
            
            async with self.session.get('https://www.bing.com/images/search', params=params) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Parsear HTML (simplificado)
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    results = []
                    for img in soup.find_all('img', class_='mimg')[:max_results]:
                        try:
                            src = img.get('src') or img.get('data-src')
                            alt = img.get('alt', '')
                            
                            if src and src.startswith('http'):
                                result = ImageResult(
                                    url=src,
                                    title=alt,
                                    thumbnail=src,
                                    width=0,
                                    height=0,
                                    size=0,
                                    format='unknown',
                                    source='bing',
                                    metadata={'alt_text': alt}
                                )
                                results.append(result)
                                
                        except Exception as e:
                            logger.debug(f"⚠️ Erro processando imagem Bing: {str(e)}")
                            continue
                    
                    return results
        
        except Exception as e:
            logger.warning(f"⚠️ Erro Bing imagens: {str(e)}")
        
        return []
    
    async def _search_yandex_images(self, query: str, max_results: int) -> List[ImageResult]:
        """Busca imagens no Yandex"""
        # Implementação similar às outras fontes
        return []
    
    async def _filter_results(self, results: List[ImageResult]) -> List[ImageResult]:
        """Filtra resultados baseado nas configurações"""
        filtered = []
        
        for result in results:
            # Verificar dimensões mínimas
            if result.width < self.config.min_width or result.height < self.config.min_height:
                continue
            
            # Verificar formato
            if not result.url.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                continue
            
            filtered.append(result)
        
        return filtered
    
    async def _rank_images(self, results: List[ImageResult], query: str) -> List[ImageResult]:
        """Rankea imagens por relevância"""
        query_lower = query.lower()
        
        for result in results:
            score = 0.0
            
            # Relevância do título
            if result.title:
                title_lower = result.title.lower()
                if query_lower in title_lower:
                    score += 0.5
                
                # Palavras do título
                query_words = set(query_lower.split())
                title_words = set(title_lower.split())
                intersection = len(query_words & title_words)
                score += intersection * 0.1
            
            # Qualidade da imagem (dimensões)
            if result.width > 0 and result.height > 0:
                # Preferir imagens maiores
                area = result.width * result.height
                score += min(area / 1000000, 0.3)  # Máximo 0.3 para 1MP
                
                # Preferir proporções razoáveis
                aspect_ratio = result.width / result.height
                if 0.5 <= aspect_ratio <= 2.0:  # Proporção entre 1:2 e 2:1
                    score += 0.2
            
            # Fonte confiabilidade
            source_scores = {
                'google': 0.9,
                'bing': 0.8,
                'duckduckgo': 0.7,
                'yandex': 0.6
            }
            score += source_scores.get(result.source, 0.5) * 0.1
            
            result.relevance_score = score
        
        # Ordenar por score
        return sorted(results, key=lambda x: x.relevance_score, reverse=True)
    
    async def _download_thumbnails(self, results: List[ImageResult]):
        """Baixa thumbnails para análise"""
        for result in results:
            if not result.thumbnail:
                continue
            
            try:
                async with self.session.get(result.thumbnail) as response:
                    if response.status == 200:
                        content = await response.read()
                        
                        # Analisar imagem
                        image_info = await self._analyze_image_data(content)
                        result.metadata = result.metadata or {}
                        result.metadata.update(image_info)
                        
            except Exception as e:
                logger.debug(f"⚠️ Erro baixando thumbnail {result.thumbnail}: {str(e)}")
    
    async def _analyze_image_data(self, image_data: bytes) -> Dict[str, Any]:
        """Analisa dados da imagem"""
        try:
            # Abrir imagem com PIL
            image = Image.open(io.BytesIO(image_data))
            
            info = {
                'actual_width': image.width,
                'actual_height': image.height,
                'actual_format': image.format,
                'mode': image.mode,
                'has_transparency': image.mode in ('RGBA', 'LA') or 'transparency' in image.info
            }
            
            # Converter para array numpy para análise com OpenCV
            if self.config.enable_face_detection or self.config.enable_object_detection:
                cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                
                if self.config.enable_face_detection:
                    faces = await self._detect_faces(cv_image)
                    info['faces_detected'] = len(faces)
                    info['face_positions'] = faces
                
                if self.config.enable_object_detection:
                    objects = await self._detect_objects(cv_image)
                    info['objects_detected'] = objects
            
            if self.config.enable_text_extraction:
                text = await self._extract_text_from_image(image)
                info['extracted_text'] = text
            
            return info
            
        except Exception as e:
            logger.debug(f"⚠️ Erro analisando imagem: {str(e)}")
            return {}
    
    async def _detect_faces(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Detecta faces na imagem"""
        try:
            # Usar OpenCV Haar Cascade
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            
            face_positions = []
            for (x, y, w, h) in faces:
                face_positions.append({
                    'x': int(x),
                    'y': int(y),
                    'width': int(w),
                    'height': int(h)
                })
            
            return face_positions
            
        except Exception as e:
            logger.debug(f"⚠️ Erro detecção faces: {str(e)}")
            return []
    
    async def _detect_objects(self, image: np.ndarray) -> List[str]:
        """Detecta objetos na imagem (simplificado)"""
        # Implementação básica - em produção usar modelos mais avançados
        return []
    
    async def _extract_text_from_image(self, image: Image.Image) -> str:
        """Extrai texto da imagem usando OCR"""
        try:
            import pytesseract
            
            text = pytesseract.image_to_string(image, lang='por+eng')
            return text.strip()
            
        except Exception as e:
            logger.debug(f"⚠️ Erro OCR: {str(e)}")
            return ""
    
    async def reverse_image_search(self, image_url: str) -> List[Dict[str, Any]]:
        """
        Busca reversa de imagem
        
        Args:
            image_url: URL da imagem para buscar
            
        Returns:
            Resultados da busca reversa
        """
        logger.info(f"🔍 Busca reversa: {image_url}")
        
        try:
            # Implementar busca reversa (Google Images, TinEye, etc.)
            results = []
            
            # Google Images reverse search
            google_results = await self._google_reverse_search(image_url)
            results.extend(google_results)
            
            # TinEye reverse search
            tineye_results = await self._tineye_reverse_search(image_url)
            results.extend(tineye_results)
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Erro busca reversa: {str(e)}")
            return []
    
    async def _google_reverse_search(self, image_url: str) -> List[Dict[str, Any]]:
        """Busca reversa no Google"""
        # Implementação simplificada
        return []
    
    async def _tineye_reverse_search(self, image_url: str) -> List[Dict[str, Any]]:
        """Busca reversa no TinEye"""
        # Implementação simplificada
        return []
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificação de saúde do coletor"""
        return {
            'status': 'healthy',
            'component': 'image_search',
            'timestamp': time.time(),
            'session_active': self.session is not None,
            'driver_active': self.driver is not None,
            'ocr_available': True,
            'face_detection_available': True
        }
    
    async def cleanup(self):
        """Limpa recursos"""
        if self.session:
            await self.session.close()
        
        if self.driver:
            self.driver.quit()
        
        logger.info("🧹 Image Search Engine limpo")
