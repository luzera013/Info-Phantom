"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - Realtime Utilities
Utilitários para comunicação em tempo real
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Any, Optional, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
import uuid
from datetime import datetime
import weakref
from collections import defaultdict

from .logger import setup_logger

logger = setup_logger(__name__)

class MessageType(Enum):
    """Tipos de mensagens"""
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    BROADCAST = "broadcast"
    DIRECT = "direct"
    SYSTEM = "system"
    ERROR = "error"

@dataclass
class WebSocketMessage:
    """Mensagem WebSocket"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType = MessageType.BROADCAST
    channel: str = "default"
    data: Any = None
    sender: Optional[str] = None
    recipient: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    ttl: Optional[float] = None

@dataclass
class ClientInfo:
    """Informações do cliente WebSocket"""
    id: str
    websocket: Any  # WebSocket object
    user_id: Optional[str] = None
    channels: Set[str] = field(default_factory=set)
    connected_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class RealtimeManager:
    """Gerenciador de comunicação em tempo real"""
    
    def __init__(self):
        self.clients: Dict[str, ClientInfo] = {}
        self.channels: Dict[str, Set[str]] = defaultdict(set)  # channel -> client_ids
        self.message_handlers: Dict[str, List[Callable]] = defaultdict(list)
        self.message_history: Dict[str, List[WebSocketMessage]] = defaultdict(list)
        self.max_history_size = 1000
        self.is_running = False
        
        logger.info("📡 Realtime Manager inicializado")
    
    async def start(self):
        """Inicia o gerenciador"""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info("🚀 Realtime Manager iniciado")
        
        # Iniciar cleanup task
        asyncio.create_task(self._cleanup_task())
    
    async def stop(self):
        """Para o gerenciador"""
        self.is_running = False
        
        # Desconectar todos os clientes
        for client_id in list(self.clients.keys()):
            await self.disconnect_client(client_id, "Server shutdown")
        
        logger.info("🛑 Realtime Manager parado")
    
    async def connect_client(self, websocket, user_id: Optional[str] = None,
                           ip_address: Optional[str] = None,
                           user_agent: Optional[str] = None) -> str:
        """
        Conecta novo cliente
        
        Args:
            websocket: Conexão WebSocket
            user_id: ID do usuário
            ip_address: Endereço IP
            user_agent: User Agent
            
        Returns:
            ID do cliente
        """
        client_id = str(uuid.uuid4())
        
        client_info = ClientInfo(
            id=client_id,
            websocket=websocket,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.clients[client_id] = client_info
        
        # Enviar mensagem de boas-vindas
        welcome_msg = WebSocketMessage(
            type=MessageType.SYSTEM,
            data={"message": "Conectado com sucesso", "client_id": client_id},
            sender="server"
        )
        
        await self._send_to_client(client_id, welcome_msg)
        
        # Notificar outros clientes
        notification = WebSocketMessage(
            type=MessageType.SYSTEM,
            data={"message": f"Cliente {client_id[:8]} conectou"},
            sender="server"
        )
        
        await self.broadcast(notification, exclude_client=client_id)
        
        logger.info(f"🔌 Cliente conectado: {client_id[:8]}... (user: {user_id})")
        return client_id
    
    async def disconnect_client(self, client_id: str, reason: str = "Disconnected"):
        """
        Desconecta cliente
        
        Args:
            client_id: ID do cliente
            reason: Motivo da desconexão
        """
        if client_id not in self.clients:
            return
        
        client = self.clients[client_id]
        
        # Remover de todos os canais
        for channel in client.channels.copy():
            await self.unsubscribe_channel(client_id, channel)
        
        # Remover cliente
        del self.clients[client_id]
        
        # Notificar outros clientes
        notification = WebSocketMessage(
            type=MessageType.SYSTEM,
            data={"message": f"Cliente {client_id[:8]} desconectou: {reason}"},
            sender="server"
        )
        
        await self.broadcast(notification)
        
        logger.info(f"🔌 Cliente desconectado: {client_id[:8]}... ({reason})")
    
    async def subscribe_channel(self, client_id: str, channel: str) -> bool:
        """
        Inscreve cliente em canal
        
        Args:
            client_id: ID do cliente
            channel: Nome do canal
            
        Returns:
            True se inscrito com sucesso
        """
        if client_id not in self.clients:
            return False
        
        client = self.clients[client_id]
        client.channels.add(channel)
        self.channels[channel].add(client_id)
        
        # Enviar confirmação
        confirmation = WebSocketMessage(
            type=MessageType.SYSTEM,
            data={"message": f"Inscrito no canal '{channel}'"},
            sender="server"
        )
        
        await self._send_to_client(client_id, confirmation)
        
        logger.debug(f"📢 Cliente {client_id[:8]} inscrito no canal '{channel}'")
        return True
    
    async def unsubscribe_channel(self, client_id: str, channel: str) -> bool:
        """
        Remove inscrição do cliente do canal
        
        Args:
            client_id: ID do cliente
            channel: Nome do canal
            
        Returns:
            True se removido com sucesso
        """
        if client_id not in self.clients:
            return False
        
        client = self.clients[client_id]
        client.channels.discard(channel)
        self.channels[channel].discard(client_id)
        
        # Limpar canal vazio
        if not self.channels[channel]:
            del self.channels[channel]
        
        # Enviar confirmação
        confirmation = WebSocketMessage(
            type=MessageType.SYSTEM,
            data={"message": f"Removido do canal '{channel}'"},
            sender="server"
        )
        
        await self._send_to_client(client_id, confirmation)
        
        logger.debug(f"📢 Cliente {client_id[:8]} removido do canal '{channel}'")
        return True
    
    async def send_message(self, message: WebSocketMessage) -> bool:
        """
        Envia mensagem
        
        Args:
            message: Mensagem para enviar
            
        Returns:
            True se enviada com sucesso
        """
        try:
            if message.type == MessageType.DIRECT:
                return await self._send_to_client(message.recipient, message)
            elif message.type == MessageType.BROADCAST:
                return await self.broadcast(message)
            else:
                # Mensagem específica para canal
                return await self._send_to_channel(message.channel, message)
        except Exception as e:
            logger.error(f"❌ Erro enviando mensagem: {str(e)}")
            return False
    
    async def broadcast(self, message: WebSocketMessage, 
                       exclude_client: Optional[str] = None) -> int:
        """
        Envia mensagem para todos os clientes
        
        Args:
            message: Mensagem para enviar
            exclude_client: Cliente para excluir
            
        Returns:
            Número de clientes que receberam a mensagem
        """
        sent_count = 0
        
        for client_id, client in self.clients.items():
            if client_id == exclude_client:
                continue
            
            if await self._send_to_client(client_id, message):
                sent_count += 1
        
        # Adicionar ao histórico
        self._add_to_history(message)
        
        logger.debug(f"📡 Broadcast enviado para {sent_count} clientes")
        return sent_count
    
    async def _send_to_channel(self, channel: str, 
                              message: WebSocketMessage) -> int:
        """
        Envia mensagem para clientes de um canal
        
        Args:
            channel: Nome do canal
            message: Mensagem para enviar
            
        Returns:
            Número de clientes que receberam a mensagem
        """
        if channel not in self.channels:
            return 0
        
        sent_count = 0
        failed_clients = set()
        
        for client_id in self.channels[channel].copy():
            if await self._send_to_client(client_id, message):
                sent_count += 1
            else:
                failed_clients.add(client_id)
        
        # Remover clientes que falharam
        for client_id in failed_clients:
            await self.disconnect_client(client_id, "Connection lost")
        
        # Adicionar ao histórico
        self._add_to_history(message)
        
        logger.debug(f"📡 Mensagem enviada para canal '{channel}': {sent_count} clientes")
        return sent_count
    
    async def _send_to_client(self, client_id: str, 
                              message: WebSocketMessage) -> bool:
        """
        Envia mensagem para cliente específico
        
        Args:
            client_id: ID do cliente
            message: Mensagem para enviar
            
        Returns:
            True se enviada com sucesso
        """
        if client_id not in self.clients:
            return False
        
        client = self.clients[client_id]
        
        try:
            # Preparar mensagem JSON
            message_data = {
                "id": message.id,
                "type": message.type.value,
                "channel": message.channel,
                "data": message.data,
                "sender": message.sender,
                "timestamp": message.timestamp
            }
            
            # Enviar via WebSocket
            await client.websocket.send_text(json.dumps(message_data))
            
            # Atualizar atividade
            client.last_activity = time.time()
            
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Erro enviando mensagem para {client_id[:8]}: {str(e)}")
            return False
    
    def add_message_handler(self, message_type: str, handler: Callable):
        """
        Adiciona handler para tipo de mensagem
        
        Args:
            message_type: Tipo de mensagem
            handler: Função handler
        """
        self.message_handlers[message_type].append(handler)
        logger.debug(f"📝 Handler adicionado para tipo '{message_type}'")
    
    async def handle_message(self, client_id: str, raw_message: str):
        """
        Processa mensagem recebida do cliente
        
        Args:
            client_id: ID do cliente
            raw_message: Mensagem em formato JSON
        """
        try:
            # Parsear mensagem
            message_data = json.loads(raw_message)
            
            # Criar objeto de mensagem
            message = WebSocketMessage(
                type=MessageType(message_data.get("type", "broadcast")),
                channel=message_data.get("channel", "default"),
                data=message_data.get("data"),
                sender=client_id,
                recipient=message_data.get("recipient")
            )
            
            # Atualizar atividade
            if client_id in self.clients:
                self.clients[client_id].last_activity = time.time()
            
            # Processar mensagem
            if message.type == MessageType.SUBSCRIBE:
                await self.subscribe_channel(client_id, message.data.get("channel", "default"))
            elif message.type == MessageType.UNSUBSCRIBE:
                await self.unsubscribe_channel(client_id, message.data.get("channel", "default"))
            else:
                # Enviar mensagem
                await self.send_message(message)
            
            # Chamar handlers
            for handler in self.message_handlers.get(message.type.value, []):
                try:
                    await handler(client_id, message)
                except Exception as e:
                    logger.error(f"❌ Erro no handler de mensagem: {str(e)}")
            
        except Exception as e:
            logger.error(f"❌ Erro processando mensagem de {client_id[:8]}: {str(e)}")
            
            # Enviar erro
            error_msg = WebSocketMessage(
                type=MessageType.ERROR,
                data={"error": "Mensagem inválida", "details": str(e)},
                sender="server"
            )
            await self._send_to_client(client_id, error_msg)
    
    def get_channel_history(self, channel: str, limit: int = 100) -> List[WebSocketMessage]:
        """
        Obtém histórico de mensagens do canal
        
        Args:
            channel: Nome do canal
            limit: Limite de mensagens
            
        Returns:
            Lista de mensagens
        """
        history = self.message_history.get(channel, [])
        return history[-limit:] if len(history) > limit else history
    
    def get_client_info(self, client_id: str) -> Optional[ClientInfo]:
        """
        Obtém informações do cliente
        
        Args:
            client_id: ID do cliente
            
        Returns:
            Informações do cliente ou None
        """
        return self.clients.get(client_id)
    
    def get_channel_info(self, channel: str) -> Dict[str, Any]:
        """
        Obtém informações do canal
        
        Args:
            channel: Nome do canal
            
        Returns:
            Informações do canal
        """
        client_count = len(self.channels.get(channel, set()))
        
        return {
            "channel": channel,
            "client_count": client_count,
            "message_count": len(self.message_history.get(channel, [])),
            "clients": list(self.channels.get(channel, []))
        }
    
    def get_system_stats(self) -> Dict[str, Any]:
        """
        Obtém estatísticas do sistema
        
        Returns:
            Estatísticas do sistema
        """
        total_messages = sum(len(history) for history in self.message_history.values())
        
        return {
            "total_clients": len(self.clients),
            "total_channels": len(self.channels),
            "total_messages": total_messages,
            "channels": {
                name: len(clients) 
                for name, clients in self.channels.items()
            },
            "uptime": time.time() - (self.start_time if hasattr(self, 'start_time') else time.time())
        }
    
    def _add_to_history(self, message: WebSocketMessage):
        """
        Adiciona mensagem ao histórico
        
        Args:
            message: Mensagem para adicionar
        """
        channel = message.channel
        
        # Adicionar ao histórico do canal
        self.message_history[channel].append(message)
        
        # Limitar tamanho do histórico
        if len(self.message_history[channel]) > self.max_history_size:
            self.message_history[channel] = self.message_history[channel][-self.max_history_size:]
    
    async def _cleanup_task(self):
        """Task de limpeza periódica"""
        while self.is_running:
            try:
                current_time = time.time()
                timeout = 300  # 5 minutos
                
                # Remover clientes inativos
                inactive_clients = []
                
                for client_id, client in self.clients.items():
                    if current_time - client.last_activity > timeout:
                        inactive_clients.append(client_id)
                
                for client_id in inactive_clients:
                    await self.disconnect_client(client_id, "Inactivity timeout")
                
                # Limpar canais vazios
                empty_channels = [
                    channel for channel, clients in self.channels.items()
                    if not clients
                ]
                
                for channel in empty_channels:
                    del self.channels[channel]
                
                if inactive_clients or empty_channels:
                    logger.info(f"🧹 Cleanup: {len(inactive_clients)} clientes, {len(empty_channels)} canais")
                
                await asyncio.sleep(60)  # Executar a cada minuto
                
            except Exception as e:
                logger.error(f"❌ Erro no cleanup: {str(e)}")
                await asyncio.sleep(60)

class NotificationManager:
    """Gerenciador de notificações"""
    
    def __init__(self, realtime_manager: RealtimeManager):
        self.realtime_manager = realtime_manager
        self.notification_handlers: Dict[str, List[Callable]] = defaultdict(list)
        
        logger.info("🔔 Notification Manager inicializado")
    
    async def send_notification(self, user_id: str, notification: Dict[str, Any]) -> bool:
        """
        Envia notificação para usuário específico
        
        Args:
            user_id: ID do usuário
            notification: Dados da notificação
            
        Returns:
            True se enviada com sucesso
        """
        message = WebSocketMessage(
            type=MessageType.DIRECT,
            channel="notifications",
            data=notification,
            sender="system",
            recipient=user_id
        )
        
        return await self.realtime_manager.send_message(message)
    
    async def broadcast_notification(self, notification: Dict[str, Any], 
                                   role: Optional[str] = None) -> int:
        """
        Envia notificação para múltiplos usuários
        
        Args:
            notification: Dados da notificação
            role: Role específico (opcional)
            
        Returns:
            Número de usuários que receberam
        """
        message = WebSocketMessage(
            type=MessageType.BROADCAST,
            channel="notifications",
            data={**notification, "role": role},
            sender="system"
        )
        
        return await self.realtime_manager.broadcast(message)
    
    def add_notification_handler(self, notification_type: str, 
                                handler: Callable):
        """
        Adiciona handler para tipo de notificação
        
        Args:
            notification_type: Tipo de notificação
            handler: Função handler
        """
        self.notification_handlers[notification_type].append(handler)
        logger.debug(f"🔔 Handler de notificação adicionado: {notification_type}")

# Instância global (em produção, seria injetada)
realtime_manager = RealtimeManager()
notification_manager = None

async def get_realtime_manager() -> RealtimeManager:
    """Obtém instância do realtime manager"""
    return realtime_manager

async def get_notification_manager() -> NotificationManager:
    """Obtém instância do notification manager"""
    global notification_manager
    
    if not notification_manager:
        notification_manager = NotificationManager(realtime_manager)
    
    return notification_manager

async def initialize_realtime():
    """Inicializa sistema de realtime"""
    await realtime_manager.start()
    logger.info("🚀 Sistema de realtime inicializado")

# Handlers padrão
async def default_connect_handler(client_id: str, message: WebSocketMessage):
    """Handler padrão para conexão"""
    logger.info(f"🔌 Conexão recebida: {client_id}")

async def default_disconnect_handler(client_id: str, message: WebSocketMessage):
    """Handler padrão para desconexão"""
    logger.info(f"🔌 Desconexão recebida: {client_id}")

async def default_message_handler(client_id: str, message: WebSocketMessage):
    """Handler padrão para mensagens"""
    logger.debug(f"📨 Mensagem de {client_id[:8]}: {message.type.value}")

# Registrar handlers padrão
def register_default_handlers():
    """Registra handlers padrão"""
    realtime_manager.add_message_handler("connect", default_connect_handler)
    realtime_manager.add_message_handler("disconnect", default_disconnect_handler)
    realtime_manager.add_message_handler("broadcast", default_message_handler)
    realtime_manager.add_message_handler("direct", default_message_handler)
