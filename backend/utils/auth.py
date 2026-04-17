"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - Authentication Utilities
Utilitários para autenticação e autorização
"""

import hashlib
import secrets
import time
import jwt
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

from .logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class AuthConfig:
    """Configuração de autenticação"""
    secret_key: str = None
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    password_min_length: int = 6
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    session_timeout_minutes: int = 60

class JWTHandler:
    """Handler para tokens JWT"""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        
        if not secret_key:
            self.secret_key = secrets.token_urlsafe(32)
            logger.warning("🔐 Usando secret key gerada automaticamente")
    
    def create_access_token(self, data: Dict[str, Any], 
                          expires_delta: Optional[timedelta] = None) -> str:
        """
        Cria token de acesso
        
        Args:
            data: Dados para incluir no token
            expires_delta: Tempo de expiração
            
        Returns:
            Token JWT
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=30)
        
        to_encode.update({"exp": expire})
        to_encode.update({"type": "access"})
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        
        logger.debug(f"🔐 Access token criado para: {data.get('sub', 'unknown')}")
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any], 
                           expires_delta: Optional[timedelta] = None) -> str:
        """
        Cria token de refresh
        
        Args:
            data: Dados para incluir no token
            expires_delta: Tempo de expiração
            
        Returns:
            Token JWT
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=7)
        
        to_encode.update({"exp": expire})
        to_encode.update({"type": "refresh"})
        to_encode.update({"jti": secrets.token_urlsafe(16)})  # Unique ID
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        
        logger.debug(f"🔄 Refresh token criado para: {data.get('sub', 'unknown')}")
        return encoded_jwt
    
    def decode_token(self, token: str) -> Dict[str, Any]:
        """
        Decodifica token JWT
        
        Args:
            token: Token JWT
            
        Returns:
            Payload do token
            
        Raises:
            jwt.PyJWTError: Se token inválido
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("🔐 Token expirado")
            raise
        except jwt.InvalidTokenError as e:
            logger.warning(f"🔐 Token inválido: {str(e)}")
            raise
    
    def decode_access_token(self, token: str) -> Dict[str, Any]:
        """
        Decodifica token de acesso
        
        Args:
            token: Token JWT
            
        Returns:
            Payload do token
        """
        payload = self.decode_token(token)
        
        if payload.get("type") != "access":
            raise jwt.InvalidTokenError("Token não é de acesso")
        
        return payload
    
    def decode_refresh_token(self, token: str) -> Dict[str, Any]:
        """
        Decodifica token de refresh
        
        Args:
            token: Token JWT
            
        Returns:
            Payload do token
        """
        payload = self.decode_token(token)
        
        if payload.get("type") != "refresh":
            raise jwt.InvalidTokenError("Token não é de refresh")
        
        return payload
    
    def verify_token(self, token: str) -> bool:
        """
        Verifica se token é válido
        
        Args:
            token: Token JWT
            
        Returns:
            True se válido
        """
        try:
            self.decode_token(token)
            return True
        except jwt.PyJWTError:
            return False

class PasswordUtils:
    """Utilitários para senhas"""
    
    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
        """
        Gera hash da senha
        
        Args:
            password: Senha em texto claro
            salt: Salt opcional
            
        Returns:
            Tuple (hash, salt)
        """
        if salt is None:
            salt = secrets.token_hex(16)
        
        # Usar PBKDF2 com SHA-256
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # Iterações
        )
        
        return password_hash.hex(), salt
    
    @staticmethod
    def verify_password(password: str, password_hash: str, salt: str) -> bool:
        """
        Verifica senha
        
        Args:
            password: Senha em texto claro
            password_hash: Hash armazenado
            salt: Salt usado
            
        Returns:
            True se senha correta
        """
        calculated_hash, _ = PasswordUtils.hash_password(password, salt)
        return calculated_hash == password_hash
    
    @staticmethod
    def generate_password(length: int = 12) -> str:
        """
        Gera senha aleatória
        
        Args:
            length: Comprimento da senha
            
        Returns:
            Senha gerada
        """
        alphabet = (
            "abcdefghijklmnopqrstuvwxyz"
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "0123456789"
            "!@#$%^&*()_+-=[]{}|;:,.<>?"
        )
        
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        
        logger.debug(f"🔐 Senha gerada ({length} caracteres)")
        return password
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """
        Valida força da senha
        
        Args:
            password: Senha para validar
            
        Returns:
            Informações sobre a força da senha
        """
        score = 0
        feedback = []
        
        # Comprimento
        if len(password) >= 8:
            score += 1
        else:
            feedback.append("Senha deve ter pelo menos 8 caracteres")
        
        if len(password) >= 12:
            score += 1
        else:
            feedback.append("Senha ideal tem 12+ caracteres")
        
        # Letras minúsculas
        if any(c.islower() for c in password):
            score += 1
        else:
            feedback.append("Inclua letras minúsculas")
        
        # Letras maiúsculas
        if any(c.isupper() for c in password):
            score += 1
        else:
            feedback.append("Inclua letras maiúsculas")
        
        # Números
        if any(c.isdigit() for c in password):
            score += 1
        else:
            feedback.append("Inclua números")
        
        # Caracteres especiais
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if any(c in special_chars for c in password):
            score += 1
        else:
            feedback.append("Inclua caracteres especiais")
        
        # Classificar força
        if score >= 5:
            strength = "Muito Forte"
        elif score >= 4:
            strength = "Forte"
        elif score >= 3:
            strength = "Média"
        elif score >= 2:
            strength = "Fraca"
        else:
            strength = "Muito Fraca"
        
        return {
            'score': score,
            'max_score': 6,
            'strength': strength,
            'feedback': feedback,
            'valid': score >= 3
        }

class SessionManager:
    """Gerenciador de sessões"""
    
    def __init__(self, config: Optional[AuthConfig] = None):
        self.config = config or AuthConfig()
        self.sessions: Dict[str, Dict[str, Any]] = {}
        
        logger.info("🔐 Session Manager inicializado")
    
    def create_session(self, user_id: str, user_data: Dict[str, Any]) -> str:
        """
        Cria nova sessão
        
        Args:
            user_id: ID do usuário
            user_data: Dados do usuário
            
        Returns:
            ID da sessão
        """
        session_id = secrets.token_urlsafe(32)
        
        session_data = {
            'session_id': session_id,
            'user_id': user_id,
            'user_data': user_data,
            'created_at': time.time(),
            'last_access': time.time(),
            'expires_at': time.time() + (self.config.session_timeout_minutes * 60),
            'ip_address': None,
            'user_agent': None
        }
        
        self.sessions[session_id] = session_data
        
        logger.info(f"🔐 Sessão criada: {session_id[:8]}... (user: {user_id})")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém sessão
        
        Args:
            session_id: ID da sessão
            
        Returns:
            Dados da sessão ou None
        """
        session = self.sessions.get(session_id)
        
        if not session:
            return None
        
        # Verificar expiração
        if time.time() > session['expires_at']:
            self.delete_session(session_id)
            return None
        
        # Atualizar último acesso
        session['last_access'] = time.time()
        
        return session
    
    def update_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """
        Atualiza dados da sessão
        
        Args:
            session_id: ID da sessão
            data: Dados para atualizar
            
        Returns:
            True se atualizado com sucesso
        """
        session = self.get_session(session_id)
        
        if not session:
            return False
        
        session['user_data'].update(data)
        session['last_access'] = time.time()
        
        return True
    
    def delete_session(self, session_id: str) -> bool:
        """
        Remove sessão
        
        Args:
            session_id: ID da sessão
            
        Returns:
            True se removida com sucesso
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"🗑️ Sessão removida: {session_id[:8]}...")
            return True
        
        return False
    
    def cleanup_expired_sessions(self) -> int:
        """
        Remove sessões expiradas
        
        Returns:
            Número de sessões removidas
        """
        current_time = time.time()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if current_time > session['expires_at']:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
        
        if expired_sessions:
            logger.info(f"🧹 {len(expired_sessions)} sessões expiradas removidas")
        
        return len(expired_sessions)
    
    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Obtém todas as sessões de um usuário
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Lista de sessões
        """
        user_sessions = []
        current_time = time.time()
        
        for session_id, session in self.sessions.items():
            if (session['user_id'] == user_id and 
                current_time <= session['expires_at']):
                user_sessions.append(session.copy())
        
        return user_sessions
    
    def revoke_user_sessions(self, user_id: str, except_session: Optional[str] = None) -> int:
        """
        Revoga todas as sessões de um usuário
        
        Args:
            user_id: ID do usuário
            except_session: Sessão para manter
            
        Returns:
            Número de sessões revogadas
        """
        revoked_count = 0
        sessions_to_revoke = []
        
        for session_id, session in self.sessions.items():
            if (session['user_id'] == user_id and 
                session_id != except_session):
                sessions_to_revoke.append(session_id)
        
        for session_id in sessions_to_revoke:
            del self.sessions[session_id]
            revoked_count += 1
        
        if revoked_count > 0:
            logger.info(f"🚫 {revoked_count} sessões revogadas (user: {user_id})")
        
        return revoked_count

class RateLimiter:
    """Limitador de taxa de requisições"""
    
    def __init__(self):
        self.requests: Dict[str, List[float]] = {}
        self.limits = {
            'login': {'requests': 5, 'window': 300},      # 5 tentativas em 5 minutos
            'register': {'requests': 3, 'window': 300},   # 3 tentativas em 5 minutos
            'api': {'requests': 100, 'window': 60},       # 100 requisições por minuto
            'search': {'requests': 10, 'window': 60}       # 10 buscas por minuto
        }
        
        logger.info("🚦 Rate Limiter inicializado")
    
    def is_allowed(self, key: str, action: str) -> bool:
        """
        Verifica se requisição é permitida
        
        Args:
            key: Chave única (IP, user_id, etc)
            action: Tipo de ação
            
        Returns:
            True se permitido
        """
        if action not in self.limits:
            return True
        
        current_time = time.time()
        limit_config = self.limits[action]
        
        # Inicializar lista de requisições
        if key not in self.requests:
            self.requests[key] = {}
        
        if action not in self.requests[key]:
            self.requests[key][action] = []
        
        # Remover requisições antigas
        window_start = current_time - limit_config['window']
        self.requests[key][action] = [
            req_time for req_time in self.requests[key][action]
            if req_time > window_start
        ]
        
        # Verificar limite
        if len(self.requests[key][action]) >= limit_config['requests']:
            logger.warning(f"🚫 Rate limit excedido: {key} - {action}")
            return False
        
        # Adicionar requisição atual
        self.requests[key][action].append(current_time)
        
        return True
    
    def get_remaining_requests(self, key: str, action: str) -> int:
        """
        Obtém número de requisições restantes
        
        Args:
            key: Chave única
            action: Tipo de ação
            
        Returns:
            Número de requisições restantes
        """
        if action not in self.limits:
            return float('inf')
        
        current_time = time.time()
        limit_config = self.limits[action]
        
        if key not in self.requests or action not in self.requests[key]:
            return limit_config['requests']
        
        # Contar requisições na janela
        window_start = current_time - limit_config['window']
        recent_requests = [
            req_time for req_time in self.requests[key][action]
            if req_time > window_start
        ]
        
        remaining = limit_config['requests'] - len(recent_requests)
        return max(0, remaining)
    
    def cleanup(self):
        """Limpa dados antigos"""
        current_time = time.time()
        max_window = max(config['window'] for config in self.limits.values())
        cutoff_time = current_time - max_window
        
        cleaned_keys = []
        
        for key, actions in self.requests.items():
            for action, requests in actions.items():
                # Manter apenas requisições recentes
                self.requests[key][action] = [
                    req_time for req_time in requests
                    if req_time > cutoff_time
                ]
            
            # Remover chaves vazias
            if all(not reqs for reqs in self.requests[key].values()):
                cleaned_keys.append(key)
        
        for key in cleaned_keys:
            del self.requests[key]
        
        if cleaned_keys:
            logger.debug(f"🧹 {len(cleaned_keys)} chaves limpas do rate limiter")

class PermissionManager:
    """Gerenciador de permissões"""
    
    def __init__(self):
        self.roles = {
            'admin': [
                'user.create', 'user.read', 'user.update', 'user.delete',
                'search.execute', 'search.read', 'search.delete',
                'system.read', 'system.update',
                'config.read', 'config.update'
            ],
            'user': [
                'search.execute', 'search.read',
                'user.read', 'user.update'
            ],
            'guest': [
                'search.execute', 'search.read'
            ]
        }
        
        logger.info("🔑 Permission Manager inicializado")
    
    def has_permission(self, user_role: str, permission: str) -> bool:
        """
        Verifica se usuário tem permissão
        
        Args:
            user_role: Role do usuário
            permission: Permissão para verificar
            
        Returns:
            True se tem permissão
        """
        role_permissions = self.roles.get(user_role, [])
        return permission in role_permissions
    
    def get_user_permissions(self, user_role: str) -> List[str]:
        """
        Obtém todas as permissões de um role
        
        Args:
            user_role: Role do usuário
            
        Returns:
            Lista de permissões
        """
        return self.roles.get(user_role, []).copy()
    
    def add_role(self, role_name: str, permissions: List[str]):
        """
        Adiciona novo role
        
        Args:
            role_name: Nome do role
            permissions: Lista de permissões
        """
        self.roles[role_name] = permissions.copy()
        logger.info(f"🔑 Role adicionado: {role_name}")
    
    def update_role_permissions(self, role_name: str, permissions: List[str]):
        """
        Atualiza permissões de um role
        
        Args:
            role_name: Nome do role
            permissions: Nova lista de permissões
        """
        if role_name in self.roles:
            self.roles[role_name] = permissions.copy()
            logger.info(f"🔑 Permissões atualizadas: {role_name}")
        else:
            logger.warning(f"⚠️ Role não encontrado: {role_name}")

# Instâncias globais (em produção, seriam injetadas)
jwt_handler = None
session_manager = SessionManager()
rate_limiter = RateLimiter()
permission_manager = PermissionManager()

def initialize_auth(secret_key: Optional[str] = None):
    """Inicializa sistema de autenticação"""
    global jwt_handler
    
    jwt_handler = JWTHandler(secret_key or secrets.token_urlsafe(32))
    
    logger.info("🔐 Sistema de autenticação inicializado")

def get_jwt_handler() -> JWTHandler:
    """Obtém handler JWT"""
    global jwt_handler
    
    if not jwt_handler:
        initialize_auth()
    
    return jwt_handler
