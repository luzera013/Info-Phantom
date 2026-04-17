"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - Memory Cache
Cache em memória para armazenamento temporário
"""

import time
import asyncio
from typing import Any, Optional, Dict, List
from dataclasses import dataclass
import threading
import logging
from collections import OrderedDict

from .logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class CacheEntry:
    """Entrada de cache"""
    value: Any
    timestamp: float
    ttl: float
    access_count: int = 0
    last_access: float = 0.0
    
    def __post_init__(self):
        self.last_access = self.timestamp
    
    def is_expired(self) -> bool:
        """Verifica se a entrada expirou"""
        return time.time() > (self.timestamp + self.ttl)
    
    def access(self) -> Any:
        """Registra acesso e retorna valor"""
        self.access_count += 1
        self.last_access = time.time()
        return self.value

class MemoryCache:
    """Cache em memória com TTL e LRU"""
    
    def __init__(self, max_size: int = 1000, default_ttl: float = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.lock = threading.RLock()
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'sets': 0
        }
        
        logger.info(f"🧠 Memory Cache inicializado (max_size: {max_size}, ttl: {default_ttl}s)")
    
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
                return None
            
            # Mover para o final (LRU)
            self.cache.move_to_end(key)
            
            # Registrar acesso
            value = entry.access()
            self.stats['hits'] += 1
            
            logger.debug(f"📦 Cache hit: {key}")
            return value
    
    async def set(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """
        Armazena valor no cache
        
        Args:
            key: Chave do cache
            value: Valor a ser armazenado
            ttl: Time to live (segundos)
            
        Returns:
            True se armazenado com sucesso
        """
        with self.lock:
            current_time = time.time()
            cache_ttl = ttl or self.default_ttl
            
            # Verificar se precisa remover entradas antigas
            if (key not in self.cache and 
                len(self.cache) >= self.max_size):
                await self._evict_lru()
            
            # Criar nova entrada
            entry = CacheEntry(
                value=value,
                timestamp=current_time,
                ttl=cache_ttl
            )
            
            self.cache[key] = entry
            self.cache.move_to_end(key)
            self.stats['sets'] += 1
            
            logger.debug(f"💾 Cache set: {key} (ttl: {cache_ttl}s)")
            return True
    
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
                logger.debug(f"🗑️ Cache delete: {key}")
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
            logger.info(f"🧹 Cache cleared: {cache_size} entradas removidas")
            return True
    
    async def exists(self, key: str) -> bool:
        """
        Verifica se chave existe no cache
        
        Args:
            key: Chave a ser verificada
            
        Returns:
            True se chave existe e não expirou
        """
        with self.lock:
            if key not in self.cache:
                return False
            
            entry = self.cache[key]
            
            # Verificar expiração
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
            
            remaining = (entry.timestamp + entry.ttl) - time.time()
            return max(0, remaining)
    
    async def set_ttl(self, key: str, ttl: float) -> bool:
        """
        Define TTL para uma chave existente
        
        Args:
            key: Chave do cache
            ttl: Novo TTL em segundos
            
        Returns:
            True se definido com sucesso
        """
        with self.lock:
            if key not in self.cache:
                return False
            
            entry = self.cache[key]
            entry.timestamp = time.time()
            entry.ttl = ttl
            
            logger.debug(f"⏰ TTL set: {key} ({ttl}s)")
            return True
    
    async def get_keys(self, pattern: Optional[str] = None) -> List[str]:
        """
        Obtém lista de chaves do cache
        
        Args:
            pattern: Padrão para filtrar chaves (opcional)
            
        Returns:
            Lista de chaves
        """
        with self.lock:
            keys = list(self.cache.keys())
            
            # Remover chaves expiradas
            valid_keys = []
            for key in keys:
                entry = self.cache[key]
                if not entry.is_expired():
                    valid_keys.append(key)
                else:
                    del self.cache[key]
            
            # Aplicar filtro de padrão se fornecido
            if pattern:
                import fnmatch
                valid_keys = [k for k in valid_keys if fnmatch.fnmatch(k, pattern)]
            
            return valid_keys
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Obtém estatísticas do cache
        
        Returns:
            Dicionário com estatísticas
        """
        with self.lock:
            total_requests = self.stats['hits'] + self.stats['misses']
            hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
            
            # Calcular estatísticas das entradas
            entries_info = []
            for key, entry in self.cache.items():
                if not entry.is_expired():
                    entries_info.append({
                        'key': key,
                        'age': time.time() - entry.timestamp,
                        'ttl_remaining': max(0, (entry.timestamp + entry.ttl) - time.time()),
                        'access_count': entry.access_count,
                        'last_access': time.time() - entry.last_access
                    })
            
            # Ordenar por acesso
            entries_info.sort(key=lambda x: x['access_count'], reverse=True)
            
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'default_ttl': self.default_ttl,
                'hits': self.stats['hits'],
                'misses': self.stats['misses'],
                'evictions': self.stats['evictions'],
                'sets': self.stats['sets'],
                'hit_rate': round(hit_rate, 2),
                'memory_usage': self._estimate_memory_usage(),
                'top_entries': entries_info[:10],
                'oldest_entry': min(entries_info, key=lambda x: x['age']) if entries_info else None,
                'newest_entry': max(entries_info, key=lambda x: x['age']) if entries_info else None
            }
    
    async def cleanup_expired(self) -> int:
        """
        Remove entradas expiradas
        
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
            
            if expired_keys:
                logger.info(f"🧹 Cleanup: {len(expired_keys)} entradas expiradas removidas")
            
            return len(expired_keys)
    
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
            logger.debug(f"🗑️ LRU eviction: {lru_key}")
    
    def _estimate_memory_usage(self) -> int:
        """Estima uso de memória em bytes"""
        import sys
        
        total_size = 0
        for key, entry in self.cache.items():
            total_size += sys.getsizeof(key)
            total_size += sys.getsizeof(entry)
            total_size += sys.getsizeof(entry.value)
        
        return total_size
    
    async def get_entry_info(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Obtém informações detalhadas de uma entrada
        
        Args:
            key: Chave do cache
            
        Returns:
            Informações da entrada ou None
        """
        with self.lock:
            if key not in self.cache:
                return None
            
            entry = self.cache[key]
            
            return {
                'key': key,
                'exists': not entry.is_expired(),
                'age': time.time() - entry.timestamp,
                'ttl': entry.ttl,
                'ttl_remaining': max(0, (entry.timestamp + entry.ttl) - time.time()),
                'access_count': entry.access_count,
                'last_access': time.time() - entry.last_access,
                'size': sys.getsizeof(entry.value)
            }
    
    async def bulk_set(self, items: Dict[str, Any], ttl: Optional[float] = None) -> int:
        """
        Armazena múltiplos valores
        
        Args:
            items: Dicionário de chave-valor
            ttl: TTL para todas as entradas
            
        Returns:
            Número de entradas armazenadas
        """
        stored = 0
        
        for key, value in items.items():
            if await self.set(key, value, ttl):
                stored += 1
        
        logger.info(f"📦 Bulk set: {stored}/{len(items)} entradas armazenadas")
        return stored
    
    async def bulk_get(self, keys: List[str]) -> Dict[str, Any]:
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
        
        logger.debug(f"📦 Bulk get: {len(results)}/{len(keys)} valores encontrados")
        return results
    
    async def bulk_delete(self, keys: List[str]) -> int:
        """
        Remove múltiplas chaves
        
        Args:
            keys: Lista de chaves
            
        Returns:
            Número de chaves removidas
        """
        deleted = 0
        
        for key in keys:
            if await self.delete(key):
                deleted += 1
        
        logger.info(f"📦 Bulk delete: {deleted}/{len(keys)} chaves removidas")
        return deleted
    
    def __len__(self) -> int:
        """Retorna número de entradas no cache"""
        return len(self.cache)
    
    def __contains__(self, key: str) -> bool:
        """Verifica se chave existe no cache"""
        return asyncio.run(self.exists(key))
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificação de saúde do cache"""
        return {
            'status': 'healthy',
            'component': 'memory_cache',
            'timestamp': time.time(),
            'cache_size': len(self.cache),
            'max_size': self.max_size,
            'stats': self.stats
        }
