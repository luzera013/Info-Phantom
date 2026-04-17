"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - Auth Route
Rota de autenticação e autorização
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, Any
import time
import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
import logging

from ...utils.jwt_handler import JWTHandler
from ...utils.sqlite import SQLiteStorage
from ...utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()
security = HTTPBearer()

# Configurações JWT
SECRET_KEY = secrets.token_urlsafe(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Modelos de dados
class UserLogin(BaseModel):
    """Modelo para login"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)

class UserRegister(BaseModel):
    """Modelo para registro"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    full_name: Optional[str] = Field(None, max_length=100)

class Token(BaseModel):
    """Modelo para token"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenRefresh(BaseModel):
    """Modelo para refresh token"""
    refresh_token: str

class UserResponse(BaseModel):
    """Modelo para resposta de usuário"""
    id: int
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]

class PasswordChange(BaseModel):
    """Modelo para mudança de senha"""
    current_password: str
    new_password: str = Field(..., min_length=6, max_length=100)

# Handlers globais (em produção viria do container DI)
jwt_handler = JWTHandler(SECRET_KEY, ALGORITHM)
storage = None

async def get_storage() -> SQLiteStorage:
    """Dependency injection para storage"""
    global storage
    if storage is None:
        storage = SQLiteStorage()
        await storage.initialize()
    return storage

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: SQLiteStorage = Depends(get_storage)
) -> Dict[str, Any]:
    """
    Obtém usuário atual a partir do token JWT
    
    Args:
        credentials: Credenciais HTTP Bearer
        db: Storage do banco
        
    Returns:
        Dados do usuário
        
    Raises:
        HTTPException: Se token inválido
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt_handler.decode_token(credentials.credentials)
        username: str = payload.get("sub")
        
        if username is None:
            raise credentials_exception
        
    except jwt.PyJWTError:
        raise credentials_exception
    
    # Buscar usuário no banco
    user = await get_user_by_username(username, db)
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Verifica se usuário está ativo
    
    Args:
        current_user: Usuário atual
        
    Returns:
        Dados do usuário ativo
        
    Raises:
        HTTPException: Se usuário inativo
    """
    if not current_user.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário inativo"
        )
    return current_user

def hash_password(password: str) -> str:
    """Hash de senha"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica senha"""
    return hash_password(plain_password) == hashed_password

async def get_user_by_username(username: str, db: SQLiteStorage) -> Optional[Dict[str, Any]]:
    """Busca usuário por username"""
    try:
        # Em produção, buscaria da tabela users
        # Por ora, retorna usuário mock para testes
        if username == "admin":
            return {
                "id": 1,
                "username": "admin",
                "email": "admin@omniscient.com",
                "full_name": "Administrador",
                "password_hash": hash_password("admin123"),
                "is_active": True,
                "created_at": datetime.now(),
                "last_login": None
            }
        elif username == "user":
            return {
                "id": 2,
                "username": "user",
                "email": "user@omniscient.com",
                "full_name": "Usuário Teste",
                "password_hash": hash_password("user123"),
                "is_active": True,
                "created_at": datetime.now(),
                "last_login": None
            }
        
        return None
        
    except Exception as e:
        logger.error(f"❌ Erro buscando usuário {username}: {str(e)}")
        return None

async def create_user_in_db(user_data: Dict[str, Any], db: SQLiteStorage) -> Optional[int]:
    """Cria usuário no banco"""
    try:
        # Em produção, inseriria na tabela users
        # Por ora, simula criação
        logger.info(f"👤 Usuário criado: {user_data['username']}")
        return int(time.time())  # ID simulado
        
    except Exception as e:
        logger.error(f"❌ Erro criando usuário: {str(e)}")
        return None

async def update_user_last_login(user_id: int, db: SQLiteStorage):
    """Atualiza último login do usuário"""
    try:
        # Em produção, atualizaria no banco
        logger.info(f"👤 Último login atualizado: user_id={user_id}")
        
    except Exception as e:
        logger.error(f"❌ Erro atualizando último login: {str(e)}")

@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserRegister,
    db: SQLiteStorage = Depends(get_storage)
):
    """
    Registra novo usuário
    
    Args:
        user_data: Dados do usuário
        db: Storage do banco
        
    Returns:
        Dados do usuário criado
        
    Raises:
        HTTPException: Se erro no registro
    """
    try:
        # Verificar se usuário já existe
        existing_user = await get_user_by_username(user_data.username, db)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username já existe"
            )
        
        # Hash da senha
        password_hash = hash_password(user_data.password)
        
        # Criar usuário no banco
        user_record = {
            "username": user_data.username,
            "email": user_data.email,
            "full_name": user_data.full_name,
            "password_hash": password_hash,
            "is_active": True,
            "created_at": datetime.now()
        }
        
        user_id = await create_user_in_db(user_record, db)
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao criar usuário"
            )
        
        # Retornar dados do usuário (sem senha)
        user_response = UserResponse(
            id=user_id,
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            is_active=True,
            created_at=user_record["created_at"],
            last_login=None
        )
        
        logger.info(f"👤 Usuário registrado: {user_data.username}")
        return user_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro no registro: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno no registro"
        )

@router.post("/login", response_model=Token)
async def login(
    user_credentials: UserLogin,
    db: SQLiteStorage = Depends(get_storage)
):
    """
    Autentica usuário
    
    Args:
        user_credentials: Credenciais do usuário
        db: Storage do banco
        
    Returns:
        Token JWT
        
    Raises:
        HTTPException: Se credenciais inválidas
    """
    try:
        # Buscar usuário
        user = await get_user_by_username(user_credentials.username, db)
        
        if not user or not verify_password(user_credentials.password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Username ou senha inválidos",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.get("is_active", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Usuário inativo"
            )
        
        # Criar tokens
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        access_token = jwt_handler.create_access_token(
            data={"sub": user["username"]},
            expires_delta=access_token_expires
        )
        
        refresh_token = jwt_handler.create_refresh_token(
            data={"sub": user["username"]},
            expires_delta=refresh_token_expires
        )
        
        # Atualizar último login
        await update_user_last_login(user["id"], db)
        
        logger.info(f"🔐 Login bem-sucedido: {user['username']}")
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro no login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno na autenticação"
        )

@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: TokenRefresh,
    db: SQLiteStorage = Depends(get_storage)
):
    """
    Renova token de acesso
    
    Args:
        token_data: Token de refresh
        db: Storage do banco
        
    Returns:
        Novo token JWT
        
    Raises:
        HTTPException: Se token inválido
    """
    try:
        # Verificar refresh token
        payload = jwt_handler.decode_refresh_token(token_data.refresh_token)
        username = payload.get("sub")
        
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido"
            )
        
        # Verificar se usuário ainda existe e está ativo
        user = await get_user_by_username(username, db)
        if not user or not user.get("is_active", False):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário inválido"
            )
        
        # Criar novo access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = jwt_handler.create_access_token(
            data={"sub": username},
            expires_delta=access_token_expires
        )
        
        logger.info(f"🔄 Token renovado: {username}")
        
        return Token(
            access_token=access_token,
            refresh_token=token_data.refresh_token,  # Mantém o mesmo refresh token
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro renovando token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno na renovação"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Obtém informações do usuário atual
    
    Args:
        current_user: Usuário autenticado
        
    Returns:
        Dados do usuário
    """
    return UserResponse(
        id=current_user["id"],
        username=current_user["username"],
        email=current_user["email"],
        full_name=current_user.get("full_name"),
        is_active=current_user["is_active"],
        created_at=current_user["created_at"],
        last_login=current_user.get("last_login")
    )

@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    db: SQLiteStorage = Depends(get_storage)
):
    """
    Altera senha do usuário
    
    Args:
        password_data: Dados da senha
        current_user: Usuário autenticado
        db: Storage do banco
        
    Returns:
        Confirmação da alteração
        
    Raises:
        HTTPException: Se erro na alteração
    """
    try:
        # Verificar senha atual
        if not verify_password(password_data.current_password, current_user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Senha atual incorreta"
            )
        
        # Hash da nova senha
        new_password_hash = hash_password(password_data.new_password)
        
        # Atualizar no banco
        # Em produção, atualizaria no banco
        logger.info(f"🔐 Senha alterada: {current_user['username']}")
        
        return {"message": "Senha alterada com sucesso"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro alterando senha: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno na alteração de senha"
        )

@router.post("/logout")
async def logout(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Logout do usuário
    
    Args:
        current_user: Usuário autenticado
        
    Returns:
        Confirmação do logout
    """
    # Em produção, poderia invalidar o token em uma blacklist
    logger.info(f"👋 Logout: {current_user['username']}")
    
    return {"message": "Logout realizado com sucesso"}

@router.get("/verify-token")
async def verify_token(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Verifica se token é válido
    
    Args:
        current_user: Usuário autenticado
        
    Returns:
        Status do token
    """
    return {
        "valid": True,
        "username": current_user["username"],
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.get("/users")
async def list_users(
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    db: SQLiteStorage = Depends(get_storage)
):
    """
    Lista usuários (apenas admin)
    
    Args:
        current_user: Usuário autenticado
        db: Storage do banco
        
    Returns:
        Lista de usuários
        
    Raises:
        HTTPException: Se não for admin
    """
    # Verificar se é admin
    if current_user["username"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado"
        )
    
    try:
        # Em produção, buscaria do banco
        users = [
            {
                "id": 1,
                "username": "admin",
                "email": "admin@omniscient.com",
                "full_name": "Administrador",
                "is_active": True,
                "created_at": datetime.now(),
                "last_login": None
            },
            {
                "id": 2,
                "username": "user",
                "email": "user@omniscient.com",
                "full_name": "Usuário Teste",
                "is_active": True,
                "created_at": datetime.now(),
                "last_login": None
            }
        ]
        
        return {"users": users, "total": len(users)}
        
    except Exception as e:
        logger.error(f"❌ Erro listando usuários: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno na listagem"
        )
