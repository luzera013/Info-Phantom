"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - Logger Utility
Utilitário para logging centralizado
"""

import logging
import sys
import os
from typing import Optional
from datetime import datetime
from pathlib import Path
import json
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from enum import Enum

class LogLevel(Enum):
    """Níveis de log customizados"""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

class ColoredFormatter(logging.Formatter):
    """Formatter com cores para console"""
    
    # Códigos de cor ANSI
    COLORS = {
        'DEBUG': '\033[36m',      # Ciano
        'INFO': '\033[32m',       # Verde
        'WARNING': '\033[33m',    # Amarelo
        'ERROR': '\033[31m',      # Vermelho
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    # Emojis para cada nível
    EMOJIS = {
        'DEBUG': '🔍',
        'INFO': 'ℹ️',
        'WARNING': '⚠️',
        'ERROR': '❌',
        'CRITICAL': '🔥'
    }
    
    def format(self, record):
        # Obter cor e emoji
        color = self.COLORS.get(record.levelname, '')
        emoji = self.EMOJIS.get(record.levelname, '')
        reset = self.COLORS['RESET']
        
        # Formatar mensagem
        log_message = super().format(record)
        
        # Adicionar cor e emoji
        if hasattr(record, 'no_color') and record.no_color:
            return f"{emoji} {log_message}"
        else:
            return f"{color}{emoji} {log_message}{reset}"

class JSONFormatter(logging.Formatter):
    """Formatter para saída JSON"""
    
    def format(self, record):
        # Criar dicionário com dados do log
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Adicionar dados extras se existirem
        if hasattr(record, 'extra_data'):
            log_data['extra'] = record.extra_data
        
        # Adicionar exceção se existir
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)

class LoggerManager:
    """Gerenciador centralizado de loggers"""
    
    def __init__(self):
        self.loggers = {}
        self.handlers = {}
        self.config = {
            'level': LogLevel.INFO,
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'date_format': '%Y-%m-%d %H:%M:%S',
            'enable_console': True,
            'enable_file': True,
            'enable_json': False,
            'log_dir': './logs',
            'max_file_size': 10 * 1024 * 1024,  # 10MB
            'backup_count': 5,
            'enable_rotation': True
        }
        
        # Criar diretório de logs
        Path(self.config['log_dir']).mkdir(parents=True, exist_ok=True)
    
    def configure(self, **kwargs):
        """Configura o gerenciador de loggers"""
        self.config.update(kwargs)
        
        # Reconfigurar loggers existentes
        for logger in self.loggers.values():
            self._configure_logger(logger)
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        Obtém logger configurado
        
        Args:
            name: Nome do logger
            
        Returns:
            Logger configurado
        """
        if name not in self.loggers:
            logger = logging.getLogger(name)
            self._configure_logger(logger)
            self.loggers[name] = logger
        
        return self.loggers[name]
    
    def _configure_logger(self, logger: logging.Logger):
        """Configura um logger específico"""
        logger.setLevel(self.config['level'].value)
        
        # Remover handlers existentes
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Adicionar handlers
        if self.config['enable_console']:
            logger.addHandler(self._get_console_handler())
        
        if self.config['enable_file']:
            logger.addHandler(self._get_file_handler())
        
        if self.config['enable_json']:
            logger.addHandler(self._get_json_handler())
        
        # Evitar duplicação
        logger.propagate = False
    
    def _get_console_handler(self) -> logging.Handler:
        """Obtém handler para console"""
        handler_id = 'console'
        
        if handler_id not in self.handlers:
            handler = logging.StreamHandler(sys.stdout)
            
            # Usar formatter colorido
            formatter = ColoredFormatter(
                fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt=self.config['date_format']
            )
            
            handler.setFormatter(formatter)
            self.handlers[handler_id] = handler
        
        return self.handlers[handler_id]
    
    def _get_file_handler(self) -> logging.Handler:
        """Obtém handler para arquivo"""
        handler_id = 'file'
        
        if handler_id not in self.handlers:
            log_file = os.path.join(
                self.config['log_dir'],
                'omniscient.log'
            )
            
            if self.config['enable_rotation']:
                # Handler com rotação por tamanho
                handler = RotatingFileHandler(
                    log_file,
                    maxBytes=self.config['max_file_size'],
                    backupCount=self.config['backup_count'],
                    encoding='utf-8'
                )
            else:
                # Handler simples
                handler = logging.FileHandler(
                    log_file,
                    encoding='utf-8'
                )
            
            formatter = logging.Formatter(
                fmt=self.config['format'],
                datefmt=self.config['date_format']
            )
            
            handler.setFormatter(formatter)
            self.handlers[handler_id] = handler
        
        return self.handlers[handler_id]
    
    def _get_json_handler(self) -> logging.Handler:
        """Obtém handler para JSON"""
        handler_id = 'json'
        
        if handler_id not in self.handlers:
            log_file = os.path.join(
                self.config['log_dir'],
                'omniscient.json'
            )
            
            if self.config['enable_rotation']:
                # Handler com rotação por tempo
                handler = TimedRotatingFileHandler(
                    log_file,
                    when='midnight',
                    interval=1,
                    backupCount=30,
                    encoding='utf-8'
                )
            else:
                handler = logging.FileHandler(
                    log_file,
                    encoding='utf-8'
                )
            
            formatter = JSONFormatter()
            handler.setFormatter(formatter)
            self.handlers[handler_id] = handler
        
        return self.handlers[handler_id]
    
    def set_level(self, level: LogLevel):
        """Define nível global de log"""
        self.config['level'] = level
        
        for logger in self.loggers.values():
            logger.setLevel(level.value)
    
    def add_custom_handler(self, name: str, handler: logging.Handler):
        """Adiciona handler customizado"""
        self.handlers[name] = handler
        
        # Adicionar a todos os loggers existentes
        for logger in self.loggers.values():
            logger.addHandler(handler)
    
    def remove_handler(self, name: str):
        """Remove handler"""
        if name in self.handlers:
            handler = self.handlers[name]
            
            # Remover de todos os loggers
            for logger in self.loggers.values():
                logger.removeHandler(handler)
            
            del self.handlers[name]
    
    def get_stats(self) -> dict:
        """Obtém estatísticas dos loggers"""
        stats = {
            'total_loggers': len(self.loggers),
            'total_handlers': len(self.handlers),
            'loggers': {},
            'handlers': list(self.handlers.keys()),
            'config': self.config.copy()
        }
        
        # Estatísticas por logger
        for name, logger in self.loggers.items():
            stats['loggers'][name] = {
                'level': logger.level,
                'handlers': len(logger.handlers),
                'disabled': logger.disabled
            }
        
        return stats

# Instância global do gerenciador
_logger_manager = None

def setup_logger(name: str, level: Optional[LogLevel] = None) -> logging.Logger:
    """
    Função principal para obter logger configurado
    
    Args:
        name: Nome do logger
        level: Nível de log (opcional)
        
    Returns:
        Logger configurado
    """
    global _logger_manager
    
    if _logger_manager is None:
        _logger_manager = LoggerManager()
        
        # Configurar nível se fornecido
        if level:
            _logger_manager.set_level(level)
    
    return _logger_manager.get_logger(name)

def configure_logging(**kwargs):
    """
    Configura o sistema de logging
    
    Args:
        **kwargs: Parâmetros de configuração
    """
    global _logger_manager
    
    if _logger_manager is None:
        _logger_manager = LoggerManager()
    
    _logger_manager.configure(**kwargs)

def get_logger_manager() -> LoggerManager:
    """
    Obtém instância do gerenciador
    
    Returns:
        LoggerManager
    """
    global _logger_manager
    
    if _logger_manager is None:
        _logger_manager = LoggerManager()
    
    return _logger_manager

# Funções de conveniência
def debug(name: str, message: str, **kwargs):
    """Log de nível DEBUG"""
    logger = setup_logger(name)
    logger.debug(message, extra=kwargs)

def info(name: str, message: str, **kwargs):
    """Log de nível INFO"""
    logger = setup_logger(name)
    logger.info(message, extra=kwargs)

def warning(name: str, message: str, **kwargs):
    """Log de nível WARNING"""
    logger = setup_logger(name)
    logger.warning(message, extra=kwargs)

def error(name: str, message: str, **kwargs):
    """Log de nível ERROR"""
    logger = setup_logger(name)
    logger.error(message, extra=kwargs)

def critical(name: str, message: str, **kwargs):
    """Log de nível CRITICAL"""
    logger = setup_logger(name)
    logger.critical(message, extra=kwargs)

# Decorators para logging
def log_function_call(logger_name: Optional[str] = None):
    """
    Decorator para logar chamadas de função
    
    Args:
        logger_name: Nome do logger (opcional)
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Obter logger
            if logger_name:
                logger = setup_logger(logger_name)
            else:
                logger = setup_logger(func.__module__)
            
            # Logar início
            logger.debug(f"🔄 Iniciando {func.__name__}")
            
            try:
                result = func(*args, **kwargs)
                logger.debug(f"✅ {func.__name__} concluído com sucesso")
                return result
            except Exception as e:
                logger.error(f"❌ Erro em {func.__name__}: {str(e)}")
                raise
        
        return wrapper
    return decorator

def log_method_call(logger_name: Optional[str] = None):
    """
    Decorator para logar chamadas de método
    
    Args:
        logger_name: Nome do logger (opcional)
    """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            # Obter logger
            if logger_name:
                logger = setup_logger(logger_name)
            else:
                logger = setup_logger(self.__class__.__module__)
            
            # Logar início
            logger.debug(f"🔄 Iniciando {self.__class__.__name__}.{func.__name__}")
            
            try:
                result = func(self, *args, **kwargs)
                logger.debug(f"✅ {self.__class__.__name__}.{func.__name__} concluído com sucesso")
                return result
            except Exception as e:
                logger.error(f"❌ Erro em {self.__class__.__name__}.{func.__name__}: {str(e)}")
                raise
        
        return wrapper
    return decorator

def log_performance(logger_name: Optional[str] = None):
    """
    Decorator para medir performance de função
    
    Args:
        logger_name: Nome do logger (opcional)
    """
    import time
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Obter logger
            if logger_name:
                logger = setup_logger(logger_name)
            else:
                logger = setup_logger(func.__module__)
            
            # Medir tempo
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                logger.info(f"⏱️ {func.__name__} executado em {execution_time:.3f}s")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"❌ {func.__name__} falhou após {execution_time:.3f}s: {str(e)}")
                raise
        
        return wrapper
    return decorator

# Context manager para logging
class LoggingContext:
    """Context manager para logging contextualizado"""
    
    def __init__(self, logger_name: str, context: dict):
        """
        Inicializa context manager
        
        Args:
            logger_name: Nome do logger
            context: Contexto adicional
        """
        self.logger = setup_logger(logger_name)
        self.context = context
        self.old_adapter = None
    
    def __enter__(self):
        # Criar adapter com contexto
        class ContextAdapter(logging.LoggerAdapter):
            def process(self, msg, kwargs):
                return msg, kwargs
        
        self.old_adapter = self.logger
        self.logger = ContextAdapter(self.logger, self.context)
        
        self.logger.info(f"📍 Contexto iniciado: {self.context}")
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.logger.error(f"❌ Erro no contexto: {exc_val}")
        else:
            self.logger.info("📍 Contexto concluído com sucesso")
        
        # Restaurar logger original
        self.logger = self.old_adapter

# Funções de configuração rápida
def enable_debug_mode():
    """Ativa modo debug"""
    configure_logging(
        level=LogLevel.DEBUG,
        enable_console=True,
        enable_file=True,
        enable_json=False
    )

def enable_production_mode():
    """Ativa modo produção"""
    configure_logging(
        level=LogLevel.INFO,
        enable_console=False,
        enable_file=True,
        enable_json=True,
        enable_rotation=True
    )

def enable_development_mode():
    """Ativa modo desenvolvimento"""
    configure_logging(
        level=LogLevel.DEBUG,
        enable_console=True,
        enable_file=True,
        enable_json=False,
        enable_rotation=False
    )
