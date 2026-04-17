"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - Tor Client
Cliente para conexão com rede Tor
"""

import asyncio
import aiohttp
import socket
import socks
import stem.process
import stem.connection
from typing import Dict, Any, Optional
from dataclasses import dataclass
import time
import logging
from pathlib import Path

from ..utils.logger import setup_logger
from ..utils.http_client import HTTPClient

logger = setup_logger(__name__)

@dataclass
class TorConfig:
    """Configuração do cliente Tor"""
    control_port: int = 9051
    socks_port: int = 9050
    data_directory: str = "./tor_data"
    timeout: int = 60
    max_retries: int = 3
    circuit_build_timeout: int = 60
    exclude_exit_nodes: Optional[str] = None
    enable_geolocation: bool = True

class TorClient:
    """Cliente Tor para acesso anônimo"""
    
    def __init__(self, config: Optional[TorConfig] = None):
        self.config = config or TorConfig()
        self.tor_process = None
        self.controller = None
        self.session = None
        self.is_connected = False
        
        logger.info("🕶️ Tor Client inicializado")
    
    async def initialize(self):
        """Inicializa o cliente Tor"""
        try:
            logger.info("🚀 Inicializando Tor...")
            
            # Criar diretório de dados se não existir
            data_dir = Path(self.config.data_directory)
            data_dir.mkdir(exist_ok=True)
            
            # Iniciar processo Tor
            await self._start_tor_process()
            
            # Conectar ao control port
            await self._connect_controller()
            
            # Configurar socks proxy
            await self._setup_socks_proxy()
            
            # Criar sessão HTTP com proxy
            await self._create_session()
            
            self.is_connected = True
            logger.info("✅ Tor inicializado com sucesso")
            
        except Exception as e:
            logger.error(f"❌ Erro inicializando Tor: {str(e)}")
            raise
    
    async def _start_tor_process(self):
        """Inicia processo Tor"""
        try:
            # Configurações do Tor
            tor_config = {
                'SocksPort': str(self.config.socks_port),
                'ControlPort': str(self.config.control_port),
                'DataDirectory': self.config.data_directory,
                'CircuitBuildTimeout': str(self.config.circuit_build_timeout),
                'ExitNodes': 'us,de,fr,gb,ca,au'  # Nós de saída confiáveis
            }
            
            if self.config.exclude_exit_nodes:
                tor_config['ExcludeExitNodes'] = self.config.exclude_exit_nodes
            
            # Iniciar Tor
            self.tor_process = stem.process.launch_tor_with_config(
                config=tor_config,
                timeout=self.config.timeout
            )
            
            logger.info("🔄 Processo Tor iniciado")
            
        except Exception as e:
            logger.error(f"❌ Erro iniciando processo Tor: {str(e)}")
            raise
    
    async def _connect_controller(self):
        """Conecta ao control port do Tor"""
        try:
            from stem.control import Controller
            
            self.controller = Controller.from_port(
                port=self.config.control_port
            )
            
            self.controller.authenticate()
            
            logger.info("🔌 Conectado ao control port do Tor")
            
        except Exception as e:
            logger.error(f"❌ Erro conectando ao control port: {str(e)}")
            raise
    
    async def _setup_socks_proxy(self):
        """Configura proxy SOCKS"""
        try:
            # Configurar proxy global
            socks.set_default_proxy(
                socks.SOCKS5,
                "127.0.0.1",
                self.config.socks_port
            )
            
            # Patch socket para usar proxy
            socket.socket = socks.socksocket
            
            logger.info("🌐 Proxy SOCKS configurado")
            
        except Exception as e:
            logger.error(f"❌ Erro configurando proxy: {str(e)}")
            raise
    
    async def _create_session(self):
        """Cria sessão HTTP com proxy Tor"""
        try:
            connector = aiohttp.TCPConnector()
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout),
                headers={
                    'User-Agent': 'OMNISCIENT_TOR/3.0',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }
            )
            
            logger.info("🌐 Sessão HTTP com Tor criada")
            
        except Exception as e:
            logger.error(f"❌ Erro criando sessão: {str(e)}")
            raise
    
    async def get(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """
        Faz requisição GET através do Tor
        
        Args:
            url: URL para acessar
            **kwargs: Argumentos adicionais
            
        Returns:
            Response da requisição
        """
        if not self.is_connected:
            await self.initialize()
        
        for attempt in range(self.config.max_retries):
            try:
                logger.debug(f"🔍 GET via Tor: {url} (tentativa {attempt + 1})")
                
                async with self.session.get(url, **kwargs) as response:
                    logger.debug(f"✅ Resposta: {response.status}")
                    return response
                    
            except Exception as e:
                logger.warning(f"⚠️ Erro tentativa {attempt + 1}: {str(e)}")
                
                if attempt < self.config.max_retries - 1:
                    # Trocar circuito Tor
                    await self._new_circuit()
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise
    
    async def post(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """
        Faz requisição POST através do Tor
        
        Args:
            url: URL para acessar
            **kwargs: Argumentos adicionais
            
        Returns:
            Response da requisição
        """
        if not self.is_connected:
            await self.initialize()
        
        for attempt in range(self.config.max_retries):
            try:
                logger.debug(f"📤 POST via Tor: {url} (tentativa {attempt + 1})")
                
                async with self.session.post(url, **kwargs) as response:
                    logger.debug(f"✅ Resposta: {response.status}")
                    return response
                    
            except Exception as e:
                logger.warning(f"⚠️ Erro tentativa {attempt + 1}: {str(e)}")
                
                if attempt < self.config.max_retries - 1:
                    await self._new_circuit()
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise
    
    async def _new_circuit(self):
        """Cria novo circuito Tor"""
        try:
            if self.controller:
                # Solicitar novo circuito
                self.controller.signal(stem.Signal.NEWNYM)
                
                # Esperar novo circuito ser estabelecido
                await asyncio.sleep(5)
                
                logger.debug("🔄 Novo circuito Tor criado")
                
        except Exception as e:
            logger.warning(f"⚠️ Erro criando novo circuito: {str(e)}")
    
    async def get_ip_info(self) -> Dict[str, Any]:
        """
        Obtém informações sobre o IP atual através do Tor
        
        Returns:
            Informações do IP e localização
        """
        try:
            # Usar serviços de verificação de IP
            ip_services = [
                'https://check.torproject.org/api/ip',
                'https://api.ipify.org?format=json',
                'https://ipinfo.io/json',
                'https://httpbin.org/ip'
            ]
            
            ip_info = {}
            
            for service in ip_services:
                try:
                    async with self.get(service) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            if 'ip' in data:
                                ip_info['ip'] = data['ip']
                            
                            if 'country' in data:
                                ip_info['country'] = data['country']
                            
                            if 'city' in data:
                                ip_info['city'] = data['city']
                            
                            if 'org' in data:
                                ip_info['organization'] = data['org']
                            
                            break  # Usar primeiro serviço que responder
                            
                except Exception as e:
                    logger.debug(f"⚠️ Erro serviço {service}: {str(e)}")
                    continue
            
            # Verificar se está usando Tor
            tor_check = await self._check_tor_status()
            ip_info['is_tor'] = tor_check
            
            logger.info(f"🌍 IP via Tor: {ip_info.get('ip', 'unknown')}")
            return ip_info
            
        except Exception as e:
            logger.error(f"❌ Erro obtendo IP info: {str(e)}")
            return {}
    
    async def _check_tor_status(self) -> bool:
        """Verifica se está conectado via Tor"""
        try:
            # Usar serviço do Tor Project
            async with self.get('https://check.torproject.org/api/ip') as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('IsTor', False)
                    
        except Exception as e:
            logger.debug(f"⚠️ Erro verificando status Tor: {str(e)}")
        
        return False
    
    async def get_circuit_info(self) -> Dict[str, Any]:
        """
        Obtém informações sobre o circuito Tor atual
        
        Returns:
            Informações do circuito
        """
        try:
            if not self.controller:
                return {}
            
            # Obter circuitos ativos
            circuits = list(self.controller.get_circuits())
            
            if not circuits:
                return {}
            
            # Usar circuito mais recente
            latest_circuit = max(circuits, key=lambda c: c.created)
            
            circuit_info = {
                'id': latest_circuit.id,
                'status': latest_circuit.status,
                'purpose': latest_circuit.purpose,
                'created': latest_circuit.created.isoformat() if latest_circuit.created else None,
                'path': []
            }
            
            # Informações dos nós do circuito
            for i, fingerprint in enumerate(latest_circuit.path):
                try:
                    relay = self.controller.get_network_status(fingerprint)
                    if relay:
                        node_info = {
                            'fingerprint': fingerprint,
                            'nickname': relay.nickname,
                            'country': relay.country,
                            'ip_address': relay.address,
                            'port': relay.or_port,
                            'flags': list(relay.flags)
                        }
                        circuit_info['path'].append(node_info)
                        
                except Exception as e:
                    logger.debug(f"⚠️ Erro informações nó {fingerprint}: {str(e)}")
                    continue
            
            logger.debug(f"🔗 Circuito Tor: {len(circuit_info['path'])} nós")
            return circuit_info
            
        except Exception as e:
            logger.error(f"❌ Erro obtendo circuito info: {str(e)}")
            return {}
    
    async def change_identity(self):
        """Muda identidade (novo circuito e IP)"""
        try:
            logger.info("🔄 Mudando identidade Tor...")
            
            # Criar novo circuito
            await self._new_circuit()
            
            # Verificar novo IP
            ip_info = await self.get_ip_info()
            
            logger.info(f"✅ Nova identidade: {ip_info.get('ip', 'unknown')}")
            return ip_info
            
        except Exception as e:
            logger.error(f"❌ Erro mudando identidade: {str(e)}")
            return {}
    
    async def test_connection(self) -> bool:
        """
        Testa conexão com Tor
        
        Returns:
            True se conectado com sucesso
        """
        try:
            # Testar conexão básica
            async with self.get('https://check.torproject.org/') as response:
                if response.status == 200:
                    content = await response.text()
                    return 'Congratulations' in content or 'Tor' in content
                    
        except Exception as e:
            logger.error(f"❌ Erro teste conexão: {str(e)}")
        
        return False
    
    async def cleanup(self):
        """Limpa recursos"""
        try:
            # Fechar sessão HTTP
            if self.session:
                await self.session.close()
            
            # Desconectar controlador
            if self.controller:
                self.controller.close()
            
            # Parar processo Tor
            if self.tor_process:
                self.tor_process.terminate()
                try:
                    self.tor_process.wait(timeout=10)
                except:
                    self.tor_process.kill()
            
            self.is_connected = False
            logger.info("🧹 Tor Client limpo")
            
        except Exception as e:
            logger.error(f"❌ Erro cleanup Tor: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificação de saúde do cliente Tor"""
        return {
            'status': 'healthy',
            'component': 'tor_client',
            'timestamp': time.time(),
            'control_port': self.config.control_port,
            'socks_port': self.config.socks_port,
            'process_running': hasattr(self, 'tor_process') and self.tor_process and self.tor_process.poll() is None
        }
    
    def __del__(self):
        """Destrutor"""
        if hasattr(self, 'tor_process') and self.tor_process:
            try:
                self.tor_process.terminate()
            except:
                pass
