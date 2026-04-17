"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - Network Utilities
Utilitários para operações de rede
"""

import asyncio
import aiohttp
import socket
import ssl
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse
import ipaddress
from dataclasses import dataclass

from .logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class NetworkConfig:
    """Configuração de rede"""
    timeout: int = 30
    max_connections: int = 100
    user_agent: str = "OMNISCIENT/3.0"
    verify_ssl: bool = True
    max_redirects: int = 5
    retry_attempts: int = 3
    retry_delay: float = 1.0

class NetworkUtils:
    """Utilitários de rede"""
    
    def __init__(self, config: Optional[NetworkConfig] = None):
        self.config = config or NetworkConfig()
        self.session = None
        
        logger.info(f"🌐 Network Utils inicializado (timeout: {self.config.timeout}s)")
    
    async def initialize(self):
        """Inicializa o cliente HTTP"""
        # Configurar SSL context
        ssl_context = ssl.create_default_context()
        if not self.config.verify_ssl:
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
        
        # Configurar connector
        connector = aiohttp.TCPConnector(
            ssl=ssl_context,
            limit=self.config.max_connections,
            limit_per_host=20,
            ttl_dns_cache=300,
            use_dns_cache=True,
            family=socket.AF_UNSPEC,
            enable_cleanup_closed=True
        )
        
        # Configurar headers padrão
        headers = {
            'User-Agent': self.config.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'DNT': '1',
            'Cache-Control': 'max-age=0'
        }
        
        # Criar sessão
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=self.config.timeout),
            headers=headers,
            max_redirects=self.config.max_redirects
        )
        
        logger.info("✅ Network Utils pronto")
    
    async def get(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """
        Faz requisição GET com retry
        
        Args:
            url: URL para acessar
            **kwargs: Argumentos adicionais
            
        Returns:
            Response da requisição
        """
        if not self.session:
            await self.initialize()
        
        last_error = None
        
        for attempt in range(self.config.retry_attempts):
            try:
                logger.debug(f"🌐 GET {url} (tentativa {attempt + 1})")
                
                async with self.session.get(url, **kwargs) as response:
                    logger.debug(f"✅ Response: {response.status} - {url}")
                    return response
                    
            except Exception as e:
                last_error = e
                logger.warning(f"⚠️ GET {url} falhou (tentativa {attempt + 1}): {str(e)}")
                
                if attempt < self.config.retry_attempts - 1:
                    await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
        
        raise last_error
    
    async def post(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """
        Faz requisição POST com retry
        
        Args:
            url: URL para acessar
            **kwargs: Argumentos adicionais
            
        Returns:
            Response da requisição
        """
        if not self.session:
            await self.initialize()
        
        last_error = None
        
        for attempt in range(self.config.retry_attempts):
            try:
                logger.debug(f"📤 POST {url} (tentativa {attempt + 1})")
                
                async with self.session.post(url, **kwargs) as response:
                    logger.debug(f"✅ Response: {response.status} - {url}")
                    return response
                    
            except Exception as e:
                last_error = e
                logger.warning(f"⚠️ POST {url} falhou (tentativa {attempt + 1}): {str(e)}")
                
                if attempt < self.config.retry_attempts - 1:
                    await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
        
        raise last_error
    
    async def head(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """
        Faz requisição HEAD com retry
        
        Args:
            url: URL para acessar
            **kwargs: Argumentos adicionais
            
        Returns:
            Response da requisição
        """
        if not self.session:
            await self.initialize()
        
        last_error = None
        
        for attempt in range(self.config.retry_attempts):
            try:
                logger.debug(f"🔍 HEAD {url} (tentativa {attempt + 1})")
                
                async with self.session.head(url, **kwargs) as response:
                    logger.debug(f"✅ Response: {response.status} - {url}")
                    return response
                    
            except Exception as e:
                last_error = e
                logger.warning(f"⚠️ HEAD {url} falhou (tentativa {attempt + 1}): {str(e)}")
                
                if attempt < self.config.retry_attempts - 1:
                    await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
        
        raise last_error
    
    async def check_url(self, url: str) -> Dict[str, Any]:
        """
        Verifica se URL está acessível
        
        Args:
            url: URL para verificar
            
        Returns:
            Informações sobre a URL
        """
        try:
            start_time = time.time()
            
            async with self.head(url) as response:
                load_time = time.time() - start_time
                
                return {
                    'url': url,
                    'accessible': True,
                    'status_code': response.status,
                    'content_type': response.headers.get('content-type', ''),
                    'content_length': response.headers.get('content-length', ''),
                    'load_time': load_time,
                    'headers': dict(response.headers),
                    'redirects': len(response.history),
                    'final_url': str(response.url)
                }
                
        except Exception as e:
            return {
                'url': url,
                'accessible': False,
                'error': str(e),
                'load_time': time.time() - start_time
            }
    
    async def check_urls_batch(self, urls: List[str], 
                              max_concurrent: int = 10) -> List[Dict[str, Any]]:
        """
        Verifica múltiplas URLs em paralelo
        
        Args:
            urls: Lista de URLs para verificar
            max_concurrent: Máximo de verificações simultâneas
            
        Returns:
            Lista de resultados
        """
        logger.info(f"🔍 Verificando {len(urls)} URLs (max: {max_concurrent})")
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def check_single(url):
            async with semaphore:
                return await self.check_url(url)
        
        tasks = [check_single(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Processar exceções
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'url': urls[i],
                    'accessible': False,
                    'error': str(result)
                })
            else:
                processed_results.append(result)
        
        accessible = sum(1 for r in processed_results if r.get('accessible', False))
        logger.info(f"✅ Verificação concluída: {accessible}/{len(urls)} acessíveis")
        
        return processed_results
    
    async def get_ip_info(self, url_or_ip: str) -> Dict[str, Any]:
        """
        Obtém informações de IP/domínio
        
        Args:
            url_or_ip: URL ou endereço IP
            
        Returns:
            Informações do IP/domínio
        """
        try:
            # Extrair hostname da URL
            parsed = urlparse(url_or_ip)
            hostname = parsed.hostname or url_or_ip
            
            # Obter endereço IP
            ip_info = socket.getaddrinfo(hostname, None)
            ips = [info[4][0] for info in ip_info]
            
            if not ips:
                return {'error': 'Não foi possível resolver hostname'}
            
            primary_ip = ips[0]
            
            # Obter informações geográficas (simulado)
            geo_info = await self._get_geo_info(primary_ip)
            
            return {
                'hostname': hostname,
                'ips': ips,
                'primary_ip': primary_ip,
                'geo_info': geo_info,
                'reverse_dns': await self._get_reverse_dns(primary_ip)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    async def _get_geo_info(self, ip: str) -> Dict[str, Any]:
        """
        Obtém informações geográficas do IP (simulado)
        
        Args:
            ip: Endereço IP
            
        Returns:
            Informações geográficas
        """
        try:
            # Em produção, usaria API de geolocalização
            # Por ora, retorna dados simulados
            
            ip_obj = ipaddress.ip_address(ip)
            
            if ip_obj.is_private:
                return {
                    'type': 'private',
                    'range': 'RFC1918',
                    'description': 'Endereço IP privado'
                }
            
            # Simular dados públicos
            return {
                'type': 'public',
                'country': 'BR',
                'region': 'São Paulo',
                'city': 'São Paulo',
                'isp': 'Internet Provider',
                'organization': 'Tech Company',
                'latitude': -23.5505,
                'longitude': -46.6333,
                'timezone': 'America/Sao_Paulo'
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    async def _get_reverse_dns(self, ip: str) -> Optional[str]:
        """
        Obtém DNS reverso do IP
        
        Args:
            ip: Endereço IP
            
        Returns:
            Nome do host ou None
        """
        try:
            hostname, _, _ = socket.gethostbyaddr(ip)
            return hostname
        except:
            return None
    
    async def test_connectivity(self, hosts: List[str], 
                              ports: List[int]) -> Dict[str, Any]:
        """
        Testa conectividade com hosts e portas
        
        Args:
            hosts: Lista de hosts
            ports: Lista de portas
            
        Returns:
            Resultados dos testes
        """
        logger.info(f"🔌 Testando conectividade: {len(hosts)} hosts, {len(ports)} portas")
        
        results = {}
        
        for host in hosts:
            results[host] = {}
            
            for port in ports:
                try:
                    start_time = time.time()
                    
                    # Criar socket e testar conexão
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(5)
                    
                    result = sock.connect_ex((host, port))
                    connect_time = time.time() - start_time
                    
                    sock.close()
                    
                    results[host][port] = {
                        'connected': result == 0,
                        'connect_time': connect_time,
                        'error': None if result == 0 else f'Connection failed (code: {result})'
                    }
                    
                except Exception as e:
                    results[host][port] = {
                        'connected': False,
                        'connect_time': 0,
                        'error': str(e)
                    }
        
        return results
    
    async def scan_ports(self, host: str, ports: List[int],
                        timeout: float = 3.0) -> Dict[int, Dict[str, Any]]:
        """
        Escaneia portas de um host
        
        Args:
            host: Host para escanear
            ports: Lista de portas
            timeout: Timeout por porta
            
        Returns:
            Resultados do scan
        """
        logger.info(f"🔍 Escaneando portas de {host}: {len(ports)} portas")
        
        results = {}
        semaphore = asyncio.Semaphore(50)  # Limite de conexões simultâneas
        
        async def scan_port(port):
            async with semaphore:
                try:
                    start_time = time.time()
                    
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(timeout)
                    
                    result = sock.connect_ex((host, port))
                    scan_time = time.time() - start_time
                    
                    sock.close()
                    
                    return {
                        'port': port,
                        'open': result == 0,
                        'scan_time': scan_time,
                        'service': await self._guess_service(port)
                    }
                    
                except Exception as e:
                    return {
                        'port': port,
                        'open': False,
                        'scan_time': timeout,
                        'error': str(e)
                    }
        
        tasks = [scan_port(port) for port in ports]
        scan_results = await asyncio.gather(*tasks)
        
        for result in scan_results:
            port = result['port']
            results[port] = result
        
        open_ports = sum(1 for r in results.values() if r.get('open', False))
        logger.info(f"✅ Scan concluído: {open_ports}/{len(ports)} portas abertas")
        
        return results
    
    async def _guess_service(self, port: int) -> str:
        """
        Adivinha o serviço baseado na porta
        
        Args:
            port: Número da porta
            
        Returns:
            Nome do serviço
        """
        common_ports = {
            20: 'FTP Data',
            21: 'FTP Control',
            22: 'SSH',
            23: 'Telnet',
            25: 'SMTP',
            53: 'DNS',
            80: 'HTTP',
            110: 'POP3',
            143: 'IMAP',
            443: 'HTTPS',
            993: 'IMAPS',
            995: 'POP3S',
            3306: 'MySQL',
            5432: 'PostgreSQL',
            6379: 'Redis',
            8080: 'HTTP Alt',
            8443: 'HTTPS Alt',
            9050: 'Tor SOCKS',
            9051: 'Tor Control'
        }
        
        return common_ports.get(port, 'Unknown')
    
    async def get_network_stats(self) -> Dict[str, Any]:
        """
        Obtém estatísticas de rede
        
        Returns:
            Estatísticas da rede
        """
        try:
            import psutil
            
            # Obter interfaces de rede
            interfaces = psutil.net_if_addrs()
            stats = psutil.net_if_stats()
            io_counters = psutil.net_io_counters(pernic=True)
            
            network_info = {}
            
            for interface_name, addresses in interfaces.items():
                interface_info = {
                    'addresses': [],
                    'is_up': False,
                    'speed': 0,
                    'mtu': 0,
                    'bytes_sent': 0,
                    'bytes_recv': 0
                }
                
                # Endereços
                for addr in addresses:
                    interface_info['addresses'].append({
                        'family': addr.family.name,
                        'address': addr.address,
                        'netmask': addr.netmask,
                        'broadcast': addr.broadcast
                    })
                
                # Estatísticas
                if interface_name in stats:
                    if_stats = stats[interface_name]
                    interface_info['is_up'] = if_stats.isup
                    interface_info['speed'] = if_stats.speed
                    interface_info['mtu'] = if_stats.mtu
                
                # Contadores I/O
                if interface_name in io_counters:
                    io_stats = io_counters[interface_name]
                    interface_info['bytes_sent'] = io_stats.bytes_sent
                    interface_info['bytes_recv'] = io_stats.bytes_recv
                    interface_info['packets_sent'] = io_stats.packets_sent
                    interface_info['packets_recv'] = io_stats.packets_recv
                
                network_info[interface_name] = interface_info
            
            # Estatísticas gerais
            total_io = psutil.net_io_counters()
            
            return {
                'interfaces': network_info,
                'total': {
                    'bytes_sent': total_io.bytes_sent,
                    'bytes_recv': total_io.bytes_recv,
                    'packets_sent': total_io.packets_sent,
                    'packets_recv': total_io.packets_recv,
                    'errin': total_io.errin,
                    'errout': total_io.errout,
                    'dropin': total_io.dropin,
                    'dropout': total_io.dropout
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Erro obtendo estatísticas de rede: {str(e)}")
            return {'error': str(e)}
    
    async def resolve_domains(self, domains: List[str]) -> Dict[str, List[str]]:
        """
        Resolve múltiplos domínios
        
        Args:
            domains: Lista de domínios
            
        Returns:
            Mapeamento de domínio -> IPs
        """
        logger.info(f"🔍 Resolvendo {len(domains)} domínios")
        
        results = {}
        
        for domain in domains:
            try:
                ips = socket.gethostbyname_ex(domain)[2]
                results[domain] = ips
                logger.debug(f"✅ {domain} -> {ips}")
            except Exception as e:
                results[domain] = []
                logger.warning(f"⚠️ Erro resolvendo {domain}: {str(e)}")
        
        return results
    
    async def check_ssl_cert(self, hostname: str, port: int = 443) -> Dict[str, Any]:
        """
        Verifica certificado SSL
        
        Args:
            hostname: Hostname para verificar
            port: Porta SSL
            
        Returns:
            Informações do certificado
        """
        try:
            context = ssl.create_default_context()
            
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    
                    return {
                        'valid': True,
                        'subject': dict(x[0] for x in cert['subject']),
                        'issuer': dict(x[0] for x in cert['issuer']),
                        'version': cert['version'],
                        'serial_number': cert['serialNumber'],
                        'not_before': cert['notBefore'],
                        'not_after': cert['notAfter'],
                        'subject_alt_name': cert.get('subjectAltName', []),
                        'days_until_expiry': self._calculate_ssl_expiry(cert['notAfter'])
                    }
                    
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }
    
    def _calculate_ssl_expiry(self, not_after: str) -> int:
        """
        Calcula dias até expiração do certificado SSL
        
        Args:
            not_after: Data de expiração
            
        Returns:
            Dias até expiração
        """
        try:
            from datetime import datetime
            
            # Parse da data do certificado
            expiry_date = datetime.strptime(not_after, '%b %d %H:%M:%S %Y %Z')
            
            # Calcular diferença
            now = datetime.now()
            delta = expiry_date - now
            
            return delta.days
            
        except:
            return -1
    
    async def cleanup(self):
        """Limpa recursos"""
        if self.session:
            await self.session.close()
            self.session = None
        
        logger.info("🧹 Network Utils limpo")
