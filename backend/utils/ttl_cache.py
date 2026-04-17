"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - TTL Cache
Cache com Time-To-Live automático
"""

import time
import asyncio
from typing import Any, Optional, Dict, Callable
from dataclasses import dataclass
import threading
import logging
from datetime import datetime, timedelta

from .logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class TTLCacheEntry:
    """Entrada de cache com TTL"""
    value: Any
    expires_at: float
    created_at: float
    access_count: int = 0
    last_access: float = 0.0
    
    def __post_init__(self):
        self.last_access = self.created_at
    
    def is_expired(self) -> bool:
        """Verifica se a entrada expirou"""
        return time.time() > self.expires_at
    
    def access(self) -> Any:
        """Registra acesso e retorna valor"""
        self.access_count += 1
        self.last_access = time.time()
        return self.value
    
    def ttl_remaining(self) -> float:
        """Retorna TTL restante em segundos"""
        remaining = self.expires_at - time.time()
        return max(0, remaining)

class TTLCache:
    """Cache com TTL automático e limpeza"""
    
    def __init__(self, cleanup_interval: float = 60.0, max_size: int = 10000):
        self.cleanup_interval = cleanup_interval
        self.max_size = max_size
        self.cache: Dict[str, TTLCacheEntry] = {}
        self.lock = threading.RLock()
        self.cleanup_task = None
        self.is_running = False
        
        # Estatísticas
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'expired_cleaned': 0,
            'evictions': 0,
            'cleanup_runs': 0
        }
        
        logger.info(f"⏰ TTL Cache inicializado (cleanup: {cleanup_interval}s, max_size: {max_size})")
    
    async def initialize(self):
        """Inicializa o cache e inicia limpeza automática"""
        if self.is_running:
            return
        
        self.is_running = True
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        logger.info("✅ TTL Cache inicializado")
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Obtém valor do cache
        
        Args:
            key: Chave do cache
            
        Returns:
            Valor armazenado ou None
        """
        with self.lock:
            if key not in self.cache:
                self.stats['misses'] += 1
                return None
            
            entry = self.cache[key]
            
            # Verificar expiração
            if entry.is_expired():
                del self.cache[key]
                self.stats['misses'] += 1
                self.stats['expired_cleaned'] += 1
                logger.debug(f"⏰ Cache expired: {key}")
                return None
            
            # Registrar acesso
            value = entry.access()
            self.stats['hits'] += 1
            
            logger.debug(f"📦 TTL Cache hit: {key} (TTL: {entry.ttl_remaining():.1f}s)")
            return value
    
    async def set(self, key: str, value: Any, ttl: float) -> bool:
        """
        Armazena valor com TTL
        
        Args:
            key: Chave do cache
            value: Valor a ser armazenado
            ttl: Time to live em segundos
            
        Returns:
            True se armazenado com sucesso
        """
        with self.lock:
            current_time = time.time()
            
            # Verificar tamanho máximo
            if key not in self.cache and len(self.cache) >= self.max_size:
                await self._evict_lru()
            
            # Criar entrada
            entry = TTLCacheEntry(
                value=value,
                expires_at=current_time + ttl,
                created_at=current_time
            )
            
            self.cache[key] = entry
            self.stats['sets'] += 1
            
            logger.debug(f"💾 TTL Cache set: {key} (TTL: {ttl}s)")
            return True
    
    async def set_with_callback(self, key: str, value: Any, ttl: float,
                               on_expire: Optional[Callable] = None) -> bool:
        """
        Armazena valor com callback de expiração
        
        Args:
            key: Chave do cache
            value: Valor a ser armazenado
            ttl: Time to live em segundos
            on_expire: Callback chamado na expiração
            
        Returns:
            True se armazenado com sucesso
        """
        return await self.set(key, value, ttl)
    
    async def delete(self, key: str) -> bool:
        """
        Remove chave do cache
        
        Args:
            key: Chave a ser removida
            
        Returns:
            True se removido com sucesso
        """
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                logger.debug(f"🗑️ TTL Cache delete: {key}")
                return True
            return False
    
    async def clear(self) -> bool:
        """
        Limpa todo o cache
        
        Returns:
            True se limpo com sucesso
        """
        with self.lock:
            cache_size = len(self.cache)
            self.cache.clear()
            logger.info(f"🧹 TTL Cache cleared: {cache_size} entradas removidas")
            return True
    
    async def exists(self, key: str) -> bool:
        """
        Verifica se chave existe e não expirou
        
        Args:
            key: Chave a ser verificada
            
        Returns:
            True se chave existe e não expirou
        """
        with self.lock:
            if key not in self.cache:
                return False
            
            entry = self.cache[key]
            
            if entry.is_expired():
                del self.cache[key]
                return False
            
            return True
    
    async def get_ttl(self, key: str) -> Optional[float]:
        """
        Obtém TTL restante de uma chave
        
        Args:
            key: Chave do cache
            
        Returns:
            TTL restante em segundos ou None
        """
        with self.lock:
            if key not in self.cache:
                return None
            
            entry = self.cache[key]
            
            if entry.is_expired():
                return None
            
            return entry.ttl_remaining()
    
    async def extend_ttl(self, key: str, additional_ttl: float) -> bool:
        """
        Estende TTL de uma chave existente
        
        Args:
            key: Chave do cache
            additional_ttl: TTL adicional em segundos
            
        Returns:
            True se estendido com sucesso
        """
        with self.lock:
            if key not in self.cache:
                return False
            
            entry = self.cache[key]
            
            if entry.is_expired():
                return False
            
            entry.expires_at += additional_ttl
            
            logger.debug(f"⏰ TTL extended: {key} (+{additional_ttl}s)")
            return True
    
    async def get_or_set(self, key: str, factory: Callable, ttl: float) -> Any:
        """
        Obtém valor ou cria usando factory
        
        Args:
            key: Chave do cache
            factory: Função para criar valor se não existir
            ttl: TTL em segundos
            
        Returns:
            Valor do cache ou recém-criado
        """
        # Tentar obter do cache
        value = await self.get(key)
        if value is not None:
            return value
        
        # Criar novo valor
        try:
            if asyncio.iscoroutinefunction(factory):
                value = await factory()
            else:
                value = factory()
            
            # Armazenar no cache
            await self.set(key, value, ttl)
            return value
            
        except Exception as e:
            logger.error(f"❌ Erro em factory para {key}: {str(e)}")
            raise
    
    async def get_multiple(self, keys: list) -> Dict[str, Any]:
        """
        Obtém múltiplos valores
        
        Args:
            keys: Lista de chaves
            
        Returns:
            Dicionário com valores encontrados
        """
        results = {}
        
        for key in keys:
            value = await self.get(key)
            if value is not None:
                results[key] = value
        
        return results
    
    async def set_multiple(self, items: Dict[str, Any], ttl: float) -> int:
        """
        Armazena múltiplos valores com mesmo TTL
        
        Args:
            items: Dicionário de chave-valor
            ttl: TTL em segundos
            
        Returns:
            Número de itens armazenados
        """
        stored = 0
        
        for key, value in items.items():
            if await self.set(key, value, ttl):
                stored += 1
        
        logger.debug(f"📦 TTL Cache bulk set: {stored}/{len(items)} itens")
        return stored
    
    async def get_keys_by_pattern(self, pattern: str) -> list:
        """
        Obtém chaves que correspondem ao padrão
        
        Args:
            pattern: Padrão (suporta * e ?)
            
        Returns:
            Lista de chaves correspondentes
        """
        import fnmatch
        
        with self.lock:
            matching_keys = []
            
            for key in self.cache.keys():
                if fnmatch.fnmatch(key, pattern):
                    entry = self.cache[key]
                    if not entry.is_expired():
                        matching_keys.append(key)
            
            return matching_keys
    
    async def get_expired_keys(self) -> list:
        """
        Obtém lista de chaves expiradas
        
        Returns:
            Lista de chaves expiradas
        """
        with self.lock:
            expired_keys = []
            
            for key, entry in self.cache.items():
                if entry.is_expired():
                    expired_keys.append(key)
            
            return expired_keys
    
    async def cleanup_expired(self) -> int:
        """
        Remove todas as entradas expiradas
        
        Returns:
            Número de entradas removidas
        """
        with self.lock:
            expired_keys = []
            
            for key, entry in self.cache.items():
                if entry.is_expired():
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.cache[key]
            
            self.stats['expired_cleaned'] += len(expired_keys)
            
            if expired_keys:
                logger.debug(f"🧹 TTL Cache cleanup: {len(expired_keys)} entradas removidas")
            
            return len(expired_keys)
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Obtém estatísticas detalhadas
        
        Returns:
            Dicionário com estatísticas
        """
        with self.lock:
            total_requests = self.stats['hits'] + self.stats['misses']
            hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
            
            # Análise das entradas
            entries_info = []
            total_ttl_remaining = 0
            
            for key, entry in self.cache.items():
                if not entry.is_expired():
                    entries_info.append({
                        'key': key,
                        'age': time.time() - entry.created_at,
                        'ttl_remaining': entry.ttl_remaining(),
                        'access_count': entry.access_count,
                        'last_access': time.time() - entry.last_access
                    })
                    total_ttl_remaining += entry.ttl_remaining()
            
            # Ordenar por acesso
            entries_info.sort(key=lambda x: x['access_count'], reverse=True)
            
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'cleanup_interval': self.cleanup_interval,
                'is_running': self.is_running,
                'hits': self.stats['hits'],
                'misses': self.stats['misses'],
                'sets': self.stats['sets'],
                'expired_cleaned': self.stats['expired_cleaned'],
                'evictions': self.stats['evictions'],
                'cleanup_runs': self.stats['cleanup_runs'],
                'hit_rate': round(hit_rate, 2),
                'total_ttl_remaining': total_ttl_remaining,
                'avg_ttl_remaining': total_ttl_remaining / len(entries_info) if entries_info else 0,
                'top_entries': entries_info[:10],
                'oldest_entry': min(entries_info, key=lambda x: x['age']) if entries_info else None,
                'newest_entry': max(entries_info, key=lambda x: x['age']) if entries_info else None
            }
    
    async def _cleanup_loop(self):
        """Loop de limpeza automática"""
        logger.info("🔄 TTL Cache cleanup loop iniciado")
        
        while self.is_running:
            try:
                await asyncio.sleep(self.cleanup_interval)
                
                if not self.is_running:
                    break
                
                # Limpar entradas expiradas
                cleaned = await self.cleanup_expired()
                self.stats['cleanup_runs'] += 1
                
                if cleaned > 0:
                    logger.debug(f"🧹 TTL Cache cleanup: {cleaned} entradas removidas")
                
            except asyncio.CancelledError:
                logger.info("🛑 TTL Cache cleanup loop cancelado")
                break
            except Exception as e:
                logger.error(f"❌ Erro cleanup loop: {str(e)}")
                await asyncio.sleep(5)  # Esperar antes de tentar novamente
    
    async def _evict_lru(self):
        """Remove entrada menos recentemente usada"""
        if not self.cache:
            return
        
        # Encontrar entrada LRU
        lru_key = None
        lru_time = float('inf')
        
        for key, entry in self.cache.items():
            if entry.last_access < lru_time:
                lru_time = entry.last_access
                lru_key = key
        
        if lru_key:
            del self.cache[lru_key]
            self.stats['evictions'] += 1
            logger.debug(f"🗑️ TTL Cache LRU eviction: {lru_key}")
    
    async def shutdown(self):
        """Desliga o cache"""
        self.is_running = False
        
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Limpar cache
        await self.clear()
        
        logger.info("🛑 TTL Cache desligado")
    
    def __len__(self) -> int:
        """Retorna número de entradas no cache"""
        return len(self.cache)
    
    def __contains__(self, key: str) -> bool:
        """Verifica se chave existe no cache"""
        return asyncio.run(self.exists(key))
    
    async def __aenter__(self):
        """Context manager entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.shutdown()
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificação de saúde do cache TTL"""
        return {
            'status': 'healthy',
            'component': 'ttl_cache',
            'timestamp': time.time(),
            'cache_size': len(self.cache),
            'max_size': self.max_size,
            'is_running': self.is_running,
            'ttl': self.ttl,
            'cleanup_interval': self.cleanup_interval
        }
