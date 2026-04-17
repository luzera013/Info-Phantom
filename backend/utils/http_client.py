"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - HTTP Client Utility
Cliente HTTP avançado com retry, cache e rate limiting
"""

import asyncio
import aiohttp
import time
import hashlib
import json
from typing import Dict, List, Any, Optional, Union, Callable
from urllib.parse import urlparse, urljoin
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import defaultdict
import weakref

from .logger import setup_logger
from .memory_cache import MemoryCache

logger = setup_logger(__name__)

class HTTPMethod(Enum):
    """Métodos HTTP"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"
    PATCH = "PATCH"

@dataclass
class HTTPConfig:
    """Configuração do cliente HTTP"""
    timeout: int = 30
    max_connections: int = 100
    max_connections_per_host: int = 20
    enable_cache: bool = True
    cache_ttl: int = 300  # 5 minutos
    enable_compression: bool = True
    user_agent: str = "OMNISCIENT_HTTP/3.0"
    retry_attempts: int = 3
    retry_delay: float = 1.0
    max_redirects: int = 5
    verify_ssl: bool = True
    enable_rate_limiting: bool = True
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # segundos
    default_headers: Dict[str, str] = field(default_factory=dict)

@dataclass
class HTTPRequest:
    """Requisição HTTP"""
    method: HTTPMethod
    url: str
    headers: Optional[Dict[str, str]] = None
    params: Optional[Dict[str, Any]] = None
    data: Optional[Union[str, bytes, Dict[str, Any]]] = None
    json_data: Optional[Dict[str, Any]] = None
    timeout: Optional[int] = None
    allow_redirects: bool = True
    verify_ssl: Optional[bool] = None
    cache_key: Optional[str] = None
    cache_ttl: Optional[int] = None
    no_cache: bool = False

@dataclass
class HTTPResponse:
    """Resposta HTTP"""
    status_code: int
    headers: Dict[str, str]
    content: bytes
    text: str
    json_data: Optional[Dict[str, Any]]
    url: str
    request: HTTPRequest
    response_time: float
    from_cache: bool = False
    cached_at: Optional[float] = None

class RateLimiter:
    """Limitador de taxa de requisições"""
    
    def __init__(self, max_requests: int, window: int):
        self.max_requests = max_requests
        self.window = window
        self.requests = defaultdict(list)
    
    async def acquire(self, key: str = "default"):
        """Adquire permissão para fazer requisição"""
        current_time = time.time()
        
        # Remover requisições antigas
        cutoff_time = current_time - self.window
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if req_time > cutoff_time
        ]
        
        # Verificar se pode fazer requisição
        if len(self.requests[key]) >= self.max_requests:
            # Calcular tempo de espera
            oldest_request = min(self.requests[key])
            wait_time = self.window - (current_time - oldest_request)
            
            if wait_time > 0:
                logger.debug(f"🚦 Rate limiting: esperando {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
        
        # Registrar requisição
        self.requests[key].append(current_time)

class HTTPClient:
    """Cliente HTTP avançado"""
    
    def __init__(self, config: Optional[HTTPConfig] = None):
        self.config = config or HTTPConfig()
        self.session = None
        self.cache = MemoryCache() if self.config.enable_cache else None
        self.rate_limiters = {}
        
        # Estatísticas
        self.stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'total_response_time': 0.0,
            'errors': 0,
            'retries': 0
        }
        
        logger.info(f"🌐 HTTP Client inicializado (cache: {self.config.enable_cache})")
    
    async def initialize(self):
        """Inicializa o cliente HTTP"""
        # Configurar headers padrão
        default_headers = {
            'User-Agent': self.config.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'DNT': '1',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Adicionar headers customizados
        default_headers.update(self.config.default_headers)
        
        # Configurar connector
        connector = aiohttp.TCPConnector(
            limit=self.config.max_connections,
            limit_per_host=self.config.max_connections_per_host,
            ttl_dns_cache=300,
            use_dns_cache=True,
            enable_cleanup_closed=True,
            family=0,  # AF_UNSPEC
            ssl=self.config.verify_ssl
        )
        
        # Configurar timeout
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        
        # Criar sessão
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=default_headers,
            auto_decompress=self.config.enable_compression,
            max_redirects=self.config.max_redirects
        )
        
        # Inicializar cache
        if self.cache:
            await self.cache.initialize()
        
        # Configurar rate limiting
        if self.config.enable_rate_limiting:
            self.rate_limiters['default'] = RateLimiter(
                self.config.rate_limit_requests,
                self.config.rate_limit_window
            )
        
        logger.info("✅ HTTP Client pronto")
    
    async def request(self, request: HTTPRequest) -> HTTPResponse:
        """
        Executa requisição HTTP
        
        Args:
            request: Requisição HTTP
            
        Returns:
            Resposta HTTP
        """
        if not self.session:
            await self.initialize()
        
        start_time = time.time()
        self.stats['total_requests'] += 1
        
        try:
            # Verificar cache
            if not request.no_cache and self.cache and request.method == HTTPMethod.GET:
                cached_response = await self._get_from_cache(request)
                if cached_response:
                    self.stats['cache_hits'] += 1
                    logger.debug(f"📦 Cache hit: {request.url}")
                    return cached_response
            
            self.stats['cache_misses'] += 1
            
            # Rate limiting
            if self.config.enable_rate_limiting:
                domain = urlparse(request.url).netloc
                rate_limiter = self.rate_limiters.get(domain, self.rate_limiters['default'])
                await rate_limiter.acquire(domain)
            
            # Executar requisição com retry
            response = await self._execute_with_retry(request)
            
            # Salvar no cache
            if (self.cache and request.method == HTTPMethod.GET and 
                response.status_code == 200):
                await self._save_to_cache(request, response)
            
            # Atualizar estatísticas
            response_time = time.time() - start_time
            self.stats['total_response_time'] += response_time
            
            logger.debug(f"🌐 {request.method.value} {request.url} - {response.status_code} ({response_time:.3f}s)")
            
            return response
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"❌ Erro na requisição {request.method.value} {request.url}: {str(e)}")
            raise
    
    async def _execute_with_retry(self, request: HTTPRequest) -> HTTPResponse:
        """Executa requisição com retry"""
        last_error = None
        
        for attempt in range(self.config.retry_attempts):
            try:
                return await self._execute_single(request)
                
            except Exception as e:
                last_error = e
                self.stats['retries'] += 1
                
                if attempt < self.config.retry_attempts - 1:
                    wait_time = self.config.retry_delay * (2 ** attempt)
                    logger.warning(f"⚠️ Tentativa {attempt + 1} falhou, retry em {wait_time}s: {str(e)}")
                    await asyncio.sleep(wait_time)
        
        raise last_error
    
    async def _execute_single(self, request: HTTPRequest) -> HTTPResponse:
        """Executa requisição única"""
        # Preparar parâmetros
        kwargs = {
            'allow_redirects': request.allow_redirects,
            'timeout': aiohttp.ClientTimeout(total=request.timeout or self.config.timeout)
        }
        
        # Configurar SSL
        if request.verify_ssl is not None:
            kwargs['ssl'] = request.verify_ssl
        elif not self.config.verify_ssl:
            kwargs['ssl'] = False
        
        # Preparar headers
        headers = request.headers.copy() if request.headers else {}
        
        # Preparar dados
        data = None
        if request.json_data:
            headers['Content-Type'] = 'application/json'
            data = json.dumps(request.json_data)
        elif request.data:
            if isinstance(request.data, dict):
                data = aiohttp.FormData(request.data)
            else:
                data = request.data
        
        # Executar requisição baseada no método
        start_time = time.time()
        
        async with self.session.request(
            method=request.method.value,
            url=request.url,
            headers=headers,
            params=request.params,
            data=data,
            **kwargs
        ) as response:
            response_time = time.time() - start_time
            
            # Ler conteúdo
            content = await response.read()
            text = await response.text(errors='replace')
            
            # Tentar parsear JSON
            json_data = None
            try:
                if response.content_type and 'json' in response.content_type:
                    json_data = await response.json()
            except:
                pass
            
            return HTTPResponse(
                status_code=response.status,
                headers=dict(response.headers),
                content=content,
                text=text,
                json_data=json_data,
                url=str(response.url),
                request=request,
                response_time=response_time
            )
    
    async def _get_from_cache(self, request: HTTPRequest) -> Optional[HTTPResponse]:
        """Obtém resposta do cache"""
        if not self.cache:
            return None
        
        cache_key = request.cache_key or self._generate_cache_key(request)
        
        try:
            cached_data = await self.cache.get(cache_key)
            
            if cached_data:
                return HTTPResponse(
                    status_code=cached_data['status_code'],
                    headers=cached_data['headers'],
                    content=cached_data['content'],
                    text=cached_data['text'],
                    json_data=cached_data.get('json_data'),
                    url=cached_data['url'],
                    request=request,
                    response_time=0.0,
                    from_cache=True,
                    cached_at=cached_data['cached_at']
                )
        except Exception as e:
            logger.warning(f"⚠️ Erro obtendo do cache: {str(e)}")
        
        return None
    
    async def _save_to_cache(self, request: HTTPRequest, response: HTTPResponse):
        """Salva resposta no cache"""
        if not self.cache:
            return
        
        cache_key = request.cache_key or self._generate_cache_key(request)
        cache_ttl = request.cache_ttl or self.config.cache_ttl
        
        try:
            cached_data = {
                'status_code': response.status_code,
                'headers': response.headers,
                'content': response.content,
                'text': response.text,
                'json_data': response.json_data,
                'url': response.url,
                'cached_at': time.time()
            }
            
            await self.cache.set(cache_key, cached_data, cache_ttl)
            logger.debug(f"💾 Salvo no cache: {cache_key}")
            
        except Exception as e:
            logger.warning(f"⚠️ Erro salvando no cache: {str(e)}")
    
    def _generate_cache_key(self, request: HTTPRequest) -> str:
        """Gera chave de cache para requisição"""
        # Combinar URL, método e parâmetros
        key_data = {
            'url': request.url,
            'method': request.method.value,
            'params': request.params or {},
            'headers': {k: v for k, v in (request.headers or {}).items() 
                       if k.lower() not in ['authorization', 'cookie']}
        }
        
        # Gerar hash
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    # Métodos de conveniência
    async def get(self, url: str, **kwargs) -> HTTPResponse:
        """Executa requisição GET"""
        request = HTTPRequest(
            method=HTTPMethod.GET,
            url=url,
            **kwargs
        )
        return await self.request(request)
    
    async def post(self, url: str, data=None, json_data=None, **kwargs) -> HTTPResponse:
        """Executa requisição POST"""
        request = HTTPRequest(
            method=HTTPMethod.POST,
            url=url,
            data=data,
            json_data=json_data,
            **kwargs
        )
        return await self.request(request)
    
    async def put(self, url: str, data=None, json_data=None, **kwargs) -> HTTPResponse:
        """Executa requisição PUT"""
        request = HTTPRequest(
            method=HTTPMethod.PUT,
            url=url,
            data=data,
            json_data=json_data,
            **kwargs
        )
        return await self.request(request)
    
    async def delete(self, url: str, **kwargs) -> HTTPResponse:
        """Executa requisição DELETE"""
        request = HTTPRequest(
            method=HTTPMethod.DELETE,
            url=url,
            **kwargs
        )
        return await self.request(request)
    
    async def head(self, url: str, **kwargs) -> HTTPResponse:
        """Executa requisição HEAD"""
        request = HTTPRequest(
            method=HTTPMethod.HEAD,
            url=url,
            **kwargs
        )
        return await self.request(request)
    
    async def batch_requests(self, requests: List[HTTPRequest], 
                           max_concurrent: int = 10) -> List[HTTPResponse]:
        """
        Executa múltiplas requisições em lote
        
        Args:
            requests: Lista de requisições
            max_concurrent: Máximo de requisições simultâneas
            
        Returns:
            Lista de respostas
        """
        logger.info(f"📦 Executando {len(requests)} requisições em lote (max: {max_concurrent})")
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def execute_single(req):
            async with semaphore:
                try:
                    return await self.request(req)
                except Exception as e:
                    logger.error(f"❌ Erro na requisição {req.url}: {str(e)}")
                    return None
        
        tasks = [execute_single(req) for req in requests]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filtrar exceções
        valid_responses = []
        for response in responses:
            if isinstance(response, HTTPResponse):
                valid_responses.append(response)
            elif isinstance(response, Exception):
                logger.error(f"❌ Exceção no lote: {str(response)}")
        
        logger.info(f"✅ Lote concluído: {len(valid_responses)}/{len(requests)} respostas")
        return valid_responses
    
    async def download_file(self, url: str, file_path: str, 
                           chunk_size: int = 8192) -> bool:
        """
        Baixa arquivo
        
        Args:
            url: URL do arquivo
            file_path: Caminho para salvar
            chunk_size: Tamanho do chunk
            
        Returns:
            True se baixado com sucesso
        """
        try:
            request = HTTPRequest(
                method=HTTPMethod.GET,
                url=url,
                no_cache=True  # Não usar cache para downloads
            )
            
            response = await self.request(request)
            
            if response.status_code == 200:
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"💾 Arquivo baixado: {file_path} ({len(response.content)} bytes)")
                return True
            else:
                logger.error(f"❌ Erro baixando arquivo: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro baixando arquivo {url}: {str(e)}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas do cliente"""
        stats = self.stats.copy()
        
        if stats['total_requests'] > 0:
            stats['average_response_time'] = stats['total_response_time'] / stats['total_requests']
            stats['cache_hit_rate'] = (stats['cache_hits'] / stats['total_requests']) * 100
            stats['error_rate'] = (stats['errors'] / stats['total_requests']) * 100
        else:
            stats['average_response_time'] = 0.0
            stats['cache_hit_rate'] = 0.0
            stats['error_rate'] = 0.0
        
        return stats
    
    async def clear_cache(self):
        """Limpa cache"""
        if self.cache:
            await self.cache.clear()
            logger.info("🧹 Cache HTTP limpo")
    
    async def cleanup(self):
        """Limpa recursos"""
        if self.session:
            await self.session.close()
            self.session = None
        
        if self.cache:
            await self.cache.cleanup()
        
        logger.info("🧹 HTTP Client limpo")

# Factory para criar cliente com configurações específicas
def create_http_client(**kwargs) -> HTTPClient:
    """
    Cria cliente HTTP com configurações customizadas
    
    Args:
        **kwargs: Parâmetros de configuração
        
    Returns:
        Cliente HTTP configurado
    """
    config = HTTPConfig(**kwargs)
    return HTTPClient(config)

# Cliente global padrão
default_client = None

async def get_default_client() -> HTTPClient:
    """Obtém cliente HTTP padrão"""
    global default_client
    
    if default_client is None:
        default_client = HTTPClient()
        await default_client.initialize()
    
    return default_client

# Context manager para cliente HTTP
class HTTPClientContext:
    """Context manager para cliente HTTP"""
    
    def __init__(self, config: Optional[HTTPConfig] = None):
        self.client = HTTPClient(config)
    
    async def __aenter__(self) -> HTTPClient:
        await self.client.initialize()
        return self.client
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.cleanup()

# Funções de conveniência
async def get(url: str, **kwargs) -> HTTPResponse:
    """Função de conveniência para GET"""
    client = await get_default_client()
    return await client.get(url, **kwargs)

async def post(url: str, data=None, json_data=None, **kwargs) -> HTTPResponse:
    """Função de conveniência para POST"""
    client = await get_default_client()
    return await client.post(url, data=data, json_data=json_data, **kwargs)

async def put(url: str, data=None, json_data=None, **kwargs) -> HTTPResponse:
    """Função de conveniência para PUT"""
    client = await get_default_client()
    return await client.put(url, data=data, json_data=json_data, **kwargs)

async def delete(url: str, **kwargs) -> HTTPResponse:
    """Função de conveniência para DELETE"""
    client = await get_default_client()
    return await client.delete(url, **kwargs)

async def head(url: str, **kwargs) -> HTTPResponse:
    """Função de conveniência para HEAD"""
    client = await get_default_client()
    return await client.head(url, **kwargs)
