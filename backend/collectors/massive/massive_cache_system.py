"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - Massive Cache System
Sistema massivo de cache e performance para 100 coletores de dados
"""

import asyncio
import json
import time
import hashlib
import pickle
import gzip
import lzma
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, OrderedDict
from enum import Enum
import threading
import sqlite3
import redis
from pathlib import Path

from ..utils.logger import setup_logger
from ..utils.metrics import MetricsCollector

logger = setup_logger(__name__)
metrics = MetricsCollector()

class CacheLevel(Enum):
    """Níveis de cache"""
    MEMORY = "memory"
    REDIS = "redis"
    DISK = "disk"
    DATABASE = "database"

class CachePolicy(Enum):
    """Políticas de cache"""
    LRU = "lru"
    LFU = "lfu"
    FIFO = "fifo"
    TTL = "ttl"
    ADAPTIVE = "adaptive"

class CompressionType(Enum):
    """Tipos de compressão"""
    NONE = "none"
    GZIP = "gzip"
    LZMA = "lzma"
    AUTO = "auto"

@dataclass
class CacheEntry:
    """Entrada de cache"""
    key: str
    value: Any
    created_at: float
    last_accessed: float
    access_count: int = 0
    size_bytes: int = 0
    ttl: Optional[float] = None
    compression_type: CompressionType = CompressionType.NONE
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CacheStats:
    """Estatísticas do cache"""
    total_entries: int = 0
    total_size_bytes: int = 0
    hit_count: int = 0
    miss_count: int = 0
    eviction_count: int = 0
    compression_ratio: float = 1.0
    average_access_time: float = 0.0
    memory_usage: Dict[str, float] = field(default_factory=dict)

class MemoryCache:
    """Cache em memória com múltiplas políticas"""
    
    def __init__(self, max_size: int = 10000, policy: CachePolicy = CachePolicy.LRU):
        self.max_size = max_size
        self.policy = policy
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.stats = CacheStats()
        self.lock = threading.RLock()
        
        # Para LFU
        self.frequency_counter = defaultdict(int)
        
        logger.info(f" MemoryCache inicializado: max_size={max_size}, policy={policy.value}")
    
    def get(self, key: str) -> Optional[Any]:
        """Obtém valor do cache"""
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                entry.last_accessed = time.time()
                entry.access_count += 1
                
                # Atualizar política
                if self.policy == CachePolicy.LRU:
                    self.cache.move_to_end(key)
                elif self.policy == CachePolicy.LFU:
                    self.frequency_counter[key] += 1
                
                self.stats.hit_count += 1
                return entry.value
            else:
                self.stats.miss_count += 1
                return None
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None, 
            compression: CompressionType = CompressionType.NONE) -> bool:
        """Define valor no cache"""
        with self.lock:
            # Comprimir se necessário
            compressed_value, compression_used = self._compress_value(value, compression)
            
            # Calcular tamanho
            size_bytes = len(pickle.dumps(compressed_value))
            
            # Verificar se precisa evictar
            while len(self.cache) >= self.max_size and key not in self.cache:
                if not self._evict():
                    break  # Não conseguiu evictar, cache cheio
            
            # Criar entrada
            entry = CacheEntry(
                key=key,
                value=compressed_value,
                created_at=time.time(),
                last_accessed=time.time(),
                size_bytes=size_bytes,
                ttl=ttl,
                compression_type=compression_used
            )
            
            # Adicionar ao cache
            self.cache[key] = entry
            self.stats.total_entries = len(self.cache)
            self.stats.total_size_bytes += size_bytes
            
            # Atualizar política
            if self.policy == CachePolicy.LRU:
                self.cache.move_to_end(key)
            elif self.policy == CachePolicy.LFU:
                self.frequency_counter[key] = 1
            
            return True
    
    def _compress_value(self, value: Any, compression: CompressionType) -> Tuple[Any, CompressionType]:
        """Comprime valor se necessário"""
        if compression == CompressionType.NONE:
            return value, CompressionType.NONE
        
        try:
            serialized = pickle.dumps(value)
            
            if compression == CompressionType.GZIP:
                compressed = gzip.compress(serialized)
                if len(compressed) < len(serialized) * 0.8:  # Comprime se reduzir 20%
                    return pickle.loads(compressed), CompressionType.GZIP
            elif compression == CompressionType.LZMA:
                compressed = lzma.compress(serialized)
                if len(compressed) < len(serialized) * 0.8:
                    return pickle.loads(compressed), CompressionType.LZMA
            
        except Exception as e:
            logger.warning(f" Erro na compressão: {str(e)}")
        
        return value, CompressionType.NONE
    
    def _evict(self) -> bool:
        """Remove entrada baseado na política"""
        if not self.cache:
            return False
        
        if self.policy == CachePolicy.LRU:
            # Remove o mais antigo
            key, _ = self.cache.popitem(last=False)
        elif self.policy == CachePolicy.LFU:
            # Remove o menos usado
            key = min(self.frequency_counter.keys(), key=lambda k: self.frequency_counter[k])
            self.cache.pop(key, None)
            del self.frequency_counter[key]
        elif self.policy == CachePolicy.FIFO:
            # Remove o primeiro inserido
            key, _ = self.cache.popitem(last=False)
        else:
            return False
        
        self.stats.eviction_count += 1
        return True
    
    def delete(self, key: str) -> bool:
        """Remove entrada do cache"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                if key in self.frequency_counter:
                    del self.frequency_counter[key]
                return True
            return False
    
    def clear(self):
        """Limpa todo o cache"""
        with self.lock:
            self.cache.clear()
            self.frequency_counter.clear()
            self.stats = CacheStats()
    
    def get_stats(self) -> CacheStats:
        """Obtém estatísticas do cache"""
        with self.lock:
            self.stats.total_entries = len(self.cache)
            self.stats.total_size_bytes = sum(entry.size_bytes for entry in self.cache.values())
            
            if self.stats.hit_count + self.stats.miss_count > 0:
                self.stats.hit_rate = self.stats.hit_count / (self.stats.hit_count + self.stats.miss_count)
            
            return self.stats

class RedisCache:
    """Cache Redis distribuído"""
    
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0,
                 password: Optional[str] = None, prefix: str = "massive_cache:"):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.prefix = prefix
        self.redis_client = None
        self.stats = CacheStats()
        
        try:
            self.redis_client = redis.Redis(
                host=host, port=port, db=db, password=password,
                decode_responses=False, socket_timeout=5
            )
            # Testar conexão
            self.redis_client.ping()
            logger.info(f" RedisCache conectado: {host}:{port}/{db}")
        except Exception as e:
            logger.error(f" Erro conectando ao Redis: {str(e)}")
            self.redis_client = None
    
    def get(self, key: str) -> Optional[Any]:
        """Obtém valor do Redis"""
        if not self.redis_client:
            return None
        
        try:
            redis_key = f"{self.prefix}{key}"
            data = self.redis_client.get(redis_key)
            
            if data:
                entry = pickle.loads(data)
                
                # Verificar TTL
                if entry.ttl and time.time() - entry.created_at > entry.ttl:
                    self.delete(key)
                    self.stats.miss_count += 1
                    return None
                
                entry.last_accessed = time.time()
                entry.access_count += 1
                self.stats.hit_count += 1
                
                # Atualizar acesso no Redis
                self.redis_client.set(redis_key, pickle.dumps(entry), ex=entry.ttl)
                
                return entry.value
            else:
                self.stats.miss_count += 1
                return None
                
        except Exception as e:
            logger.error(f" Erro no Redis GET: {str(e)}")
            self.stats.miss_count += 1
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """Define valor no Redis"""
        if not self.redis_client:
            return False
        
        try:
            redis_key = f"{self.prefix}{key}"
            
            # Comprimir se necessário
            serialized = pickle.dumps(value)
            if len(serialized) > 1024 * 1024:  # 1MB
                serialized = gzip.compress(serialized)
            
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=time.time(),
                last_accessed=time.time(),
                size_bytes=len(serialized),
                ttl=ttl
            )
            
            # Salvar no Redis
            if ttl:
                self.redis_client.setex(redis_key, int(ttl), pickle.dumps(entry))
            else:
                self.redis_client.set(redis_key, pickle.dumps(entry))
            
            self.stats.total_entries += 1
            self.stats.total_size_bytes += len(serialized)
            
            return True
            
        except Exception as e:
            logger.error(f" Erro no Redis SET: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """Remove entrada do Redis"""
        if not self.redis_client:
            return False
        
        try:
            redis_key = f"{self.prefix}{key}"
            result = self.redis_client.delete(redis_key)
            return result > 0
        except Exception as e:
            logger.error(f" Erro no Redis DELETE: {str(e)}")
            return False
    
    def clear(self):
        """Limpa cache Redis"""
        if not self.redis_client:
            return
        
        try:
            pattern = f"{self.prefix}*"
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
            self.stats = CacheStats()
        except Exception as e:
            logger.error(f" Erro limpando Redis: {str(e)}")
    
    def get_stats(self) -> CacheStats:
        """Obtém estatísticas do Redis"""
        if not self.redis_client:
            return self.stats
        
        try:
            info = self.redis_client.info()
            self.stats.memory_usage = {
                'used_memory': info.get('used_memory', 0),
                'used_memory_human': info.get('used_memory_human', '0B'),
                'used_memory_rss': info.get('used_memory_rss', 0)
            }
            
            # Contar entradas
            pattern = f"{self.prefix}*"
            keys = self.redis_client.keys(pattern)
            self.stats.total_entries = len(keys)
            
        except Exception as e:
            logger.error(f" Erro obtendo stats Redis: {str(e)}")
        
        return self.stats

class DiskCache:
    """Cache em disco com SQLite"""
    
    def __init__(self, cache_dir: str = "/tmp/massive_cache", max_size_mb: int = 1000):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.db_path = self.cache_dir / "cache.db"
        self.stats = CacheStats()
        
        # Inicializar banco SQLite
        self._init_database()
        logger.info(f" DiskCache inicializado: {cache_dir}, max_size={max_size_mb}MB")
    
    def _init_database(self):
        """Inicializa banco de dados SQLite"""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS cache_entries (
                key TEXT PRIMARY KEY,
                value BLOB,
                created_at REAL,
                last_accessed REAL,
                access_count INTEGER,
                size_bytes INTEGER,
                ttl REAL,
                metadata TEXT
            )
        ''')
        self.conn.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON cache_entries(created_at)')
        self.conn.execute('CREATE INDEX IF NOT EXISTS idx_last_accessed ON cache_entries(last_accessed)')
        self.conn.commit()
    
    def get(self, key: str) -> Optional[Any]:
        """Obtém valor do disco"""
        try:
            cursor = self.conn.execute(
                'SELECT value, created_at, ttl FROM cache_entries WHERE key = ?',
                (key,)
            )
            row = cursor.fetchone()
            
            if row:
                value_blob, created_at, ttl = row
                
                # Verificar TTL
                if ttl and time.time() - created_at > ttl:
                    self.delete(key)
                    self.stats.miss_count += 1
                    return None
                
                # Atualizar acesso
                self.conn.execute(
                    'UPDATE cache_entries SET last_accessed = ?, access_count = access_count + 1 WHERE key = ?',
                    (time.time(), key)
                )
                self.conn.commit()
                
                self.stats.hit_count += 1
                return pickle.loads(value_blob)
            else:
                self.stats.miss_count += 1
                return None
                
        except Exception as e:
            logger.error(f" Erro no DiskCache GET: {str(e)}")
            self.stats.miss_count += 1
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """Define valor no disco"""
        try:
            # Comprimir valor
            value_blob = pickle.dumps(value)
            size_bytes = len(value_blob)
            
            # Verificar espaço
            if not self._check_space(size_bytes):
                self._cleanup_old_entries()
            
            # Inserir ou atualizar
            metadata = json.dumps({'compression': 'none'})
            
            self.conn.execute('''
                INSERT OR REPLACE INTO cache_entries 
                (key, value, created_at, last_accessed, access_count, size_bytes, ttl, metadata)
                VALUES (?, ?, ?, ?, 1, ?, ?, ?)
            ''', (
                key, value_blob, time.time(), time.time(),
                size_bytes, ttl, metadata
            ))
            self.conn.commit()
            
            self.stats.total_entries += 1
            self.stats.total_size_bytes += size_bytes
            
            return True
            
        except Exception as e:
            logger.error(f" Erro no DiskCache SET: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """Remove entrada do disco"""
        try:
            cursor = self.conn.execute('DELETE FROM cache_entries WHERE key = ?', (key,))
            self.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f" Erro no DiskCache DELETE: {str(e)}")
            return False
    
    def _check_space(self, new_size_bytes: int) -> bool:
        """Verifica se há espaço suficiente"""
        cursor = self.conn.execute('SELECT SUM(size_bytes) FROM cache_entries')
        current_size = cursor.fetchone()[0] or 0
        
        return (current_size + new_size_bytes) <= self.max_size_bytes
    
    def _cleanup_old_entries(self):
        """Remove entradas antigas para liberar espaço"""
        try:
            # Remover 20% das entradas mais antigas
            cursor = self.conn.execute('''
                DELETE FROM cache_entries 
                WHERE key IN (
                    SELECT key FROM cache_entries 
                    ORDER BY last_accessed ASC 
                    LIMIT (SELECT COUNT(*) FROM cache_entries) / 5
                )
            ''')
            self.conn.commit()
            logger.info(" DiskCache: cleanup executado")
        except Exception as e:
            logger.error(f" Erro no cleanup: {str(e)}")
    
    def clear(self):
        """Limpa cache em disco"""
        try:
            self.conn.execute('DELETE FROM cache_entries')
            self.conn.commit()
            self.stats = CacheStats()
        except Exception as e:
            logger.error(f" Erro limpando DiskCache: {str(e)}")
    
    def get_stats(self) -> CacheStats:
        """Obtém estatísticas do disco"""
        try:
            cursor = self.conn.execute('SELECT COUNT(*), SUM(size_bytes) FROM cache_entries')
            count, total_size = cursor.fetchone()
            
            self.stats.total_entries = count or 0
            self.stats.total_size_bytes = total_size or 0
            
            # Tamanho do diretório
            total_dir_size = sum(f.stat().st_size for f in self.cache_dir.rglob('*') if f.is_file())
            self.stats.memory_usage['disk_usage'] = total_dir_size
            
        except Exception as e:
            logger.error(f" Erro obtendo stats DiskCache: {str(e)}")
        
        return self.stats

class MassiveCacheSystem:
    """Sistema massivo de cache multi-nível"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {
            'memory_cache': {
                'enabled': True,
                'max_size': 10000,
                'policy': CachePolicy.LRU
            },
            'redis_cache': {
                'enabled': True,
                'host': 'localhost',
                'port': 6379,
                'db': 0
            },
            'disk_cache': {
                'enabled': True,
                'cache_dir': '/tmp/massive_cache',
                'max_size_mb': 1000
            },
            'compression': {
                'enabled': True,
                'threshold_bytes': 1024,
                'type': CompressionType.AUTO
            },
            'performance': {
                'background_cleanup': True,
                'cleanup_interval': 300,  # 5 minutos
                'stats_interval': 60  # 1 minuto
            }
        }
        
        # Inicializar caches
        self.memory_cache = None
        self.redis_cache = None
        self.disk_cache = None
        
        if self.config['memory_cache']['enabled']:
            self.memory_cache = MemoryCache(
                max_size=self.config['memory_cache']['max_size'],
                policy=self.config['memory_cache']['policy']
            )
        
        if self.config['redis_cache']['enabled']:
            self.redis_cache = RedisCache(
                host=self.config['redis_cache']['host'],
                port=self.config['redis_cache']['port'],
                db=self.config['redis_cache']['db']
            )
        
        if self.config['disk_cache']['enabled']:
            self.disk_cache = DiskCache(
                cache_dir=self.config['disk_cache']['cache_dir'],
                max_size_mb=self.config['disk_cache']['max_size_mb']
            )
        
        # Cache hierarchy: Memory -> Redis -> Disk
        self.cache_hierarchy = []
        if self.memory_cache:
            self.cache_hierarchy.append(('memory', self.memory_cache))
        if self.redis_cache:
            self.cache_hierarchy.append(('redis', self.redis_cache))
        if self.disk_cache:
            self.cache_hierarchy.append(('disk', self.disk_cache))
        
        # Estatísticas globais
        self.global_stats = {
            'total_requests': 0,
            'total_hits': 0,
            'total_misses': 0,
            'cache_level_hits': defaultdict(int),
            'average_response_time': 0.0,
            'compression_savings': 0
        }
        
        # Tarefas em background
        self.background_tasks = []
        self.is_running = False
        
        logger.info(f" MassiveCacheSystem inicializado com {len(self.cache_hierarchy)} níveis")
    
    async def initialize(self):
        """Inicializa o sistema de cache"""
        if self.is_running:
            return
        
        logger.info(" Inicializando MassiveCacheSystem...")
        
        # Iniciar tarefas em background
        if self.config['performance']['background_cleanup']:
            self._start_background_cleanup()
        
        if self.config['performance']['stats_interval']:
            self._start_stats_collection()
        
        self.is_running = True
        logger.info(" MassiveCacheSystem inicializado")
    
    def get(self, key: str) -> Optional[Any]:
        """Obtém valor do cache (multi-nível)"""
        start_time = time.time()
        self.global_stats['total_requests'] += 1
        
        for level_name, cache_instance in self.cache_hierarchy:
            try:
                value = cache_instance.get(key)
                if value is not None:
                    # Hit! Atualizar estatísticas
                    self.global_stats['total_hits'] += 1
                    self.global_stats['cache_level_hits'][level_name] += 1
                    
                    # Promover para níveis superiores (se não for o nível mais alto)
                    if level_name != 'memory' and self.memory_cache:
                        self.memory_cache.set(key, value, ttl=300)  # 5 minutos nos níveis superiores
                    
                    # Atualizar tempo médio
                    response_time = time.time() - start_time
                    self._update_average_response_time(response_time)
                    
                    return value
            except Exception as e:
                logger.error(f" Erro no cache {level_name}: {str(e)}")
                continue
        
        # Miss em todos os níveis
        self.global_stats['total_misses'] += 1
        response_time = time.time() - start_time
        self._update_average_response_time(response_time)
        
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None, 
            level: Optional[str] = None) -> bool:
        """Define valor no cache (multi-nível)"""
        # Determinar compressão
        compression = self._determine_compression(value)
        
        # Se nível específico foi solicitado
        if level:
            cache_instance = self._get_cache_by_level(level)
            if cache_instance:
                return cache_instance.set(key, value, ttl, compression)
            return False
        
        # Adicionar a todos os níveis (com TTLs diferentes)
        success = True
        
        # Memory cache - TTL mais curto
        if self.memory_cache:
            memory_ttl = ttl or 300  # 5 minutos
            success &= self.memory_cache.set(key, value, memory_ttl, compression)
        
        # Redis cache - TTL médio
        if self.redis_cache:
            redis_ttl = ttl or 3600  # 1 hora
            success &= self.redis_cache.set(key, value, redis_ttl)
        
        # Disk cache - TTL mais longo
        if self.disk_cache:
            disk_ttl = ttl or 86400  # 24 horas
            success &= self.disk_cache.set(key, value, disk_ttl)
        
        return success
    
    def delete(self, key: str, level: Optional[str] = None) -> bool:
        """Remove valor do cache"""
        if level:
            cache_instance = self._get_cache_by_level(level)
            if cache_instance:
                return cache_instance.delete(key)
            return False
        
        # Remover de todos os níveis
        success = True
        for _, cache_instance in self.cache_hierarchy:
            try:
                success &= cache_instance.delete(key)
            except Exception as e:
                logger.error(f" Erro deletando do cache: {str(e)}")
                success &= False
        
        return success
    
    def _determine_compression(self, value: Any) -> CompressionType:
        """Determina se deve comprimir o valor"""
        if not self.config['compression']['enabled']:
            return CompressionType.NONE
        
        try:
            serialized_size = len(pickle.dumps(value))
            threshold = self.config['compression']['threshold_bytes']
            
            if serialized_size < threshold:
                return CompressionType.NONE
            
            compression_type = self.config['compression']['type']
            
            if compression_type == CompressionType.AUTO:
                # Testar qual compressão é melhor
                original = pickle.dumps(value)
                gzip_compressed = gzip.compress(original)
                lzma_compressed = lzma.compress(original)
                
                if len(lzma_compressed) < len(gzip_compressed):
                    return CompressionType.LZMA
                elif len(gzip_compressed) < len(original) * 0.8:
                    return CompressionType.GZIP
                else:
                    return CompressionType.NONE
            
            return compression_type
            
        except Exception as e:
            logger.warning(f" Erro determinando compressão: {str(e)}")
            return CompressionType.NONE
    
    def _get_cache_by_level(self, level: str):
        """Obtém instância de cache por nível"""
        for level_name, cache_instance in self.cache_hierarchy:
            if level_name == level:
                return cache_instance
        return None
    
    def _update_average_response_time(self, response_time: float):
        """Atualiza tempo médio de resposta"""
        total = self.global_stats['total_requests']
        current_avg = self.global_stats['average_response_time']
        new_avg = (current_avg * (total - 1) + response_time) / total
        self.global_stats['average_response_time'] = new_avg
    
    def _start_background_cleanup(self):
        """Inicia cleanup em background"""
        async def cleanup_loop():
            while self.is_running:
                try:
                    await asyncio.sleep(self.config['performance']['cleanup_interval'])
                    await self._perform_cleanup()
                except Exception as e:
                    logger.error(f" Erro no cleanup: {str(e)}")
        
        task = asyncio.create_task(cleanup_loop())
        self.background_tasks.append(task)
        logger.info(" Background cleanup iniciado")
    
    def _start_stats_collection(self):
        """Inicia coleta de estatísticas em background"""
        async def stats_loop():
            while self.is_running:
                try:
                    await asyncio.sleep(self.config['performance']['stats_interval'])
                    await self._collect_stats()
                except Exception as e:
                    logger.error(f" Erro na coleta de stats: {str(e)}")
        
        task = asyncio.create_task(stats_loop())
        self.background_tasks.append(task)
        logger.info(" Stats collection iniciado")
    
    async def _perform_cleanup(self):
        """Executa cleanup dos caches"""
        try:
            # Limpar entradas expiradas
            if self.memory_cache:
                # Memory cache já limpa automaticamente pelo LRU/LFU
                pass
            
            if self.redis_cache:
                # Redis já lida com TTL automaticamente
                pass
            
            if self.disk_cache:
                # Disk cache precisa de cleanup manual
                self.disk_cache._cleanup_old_entries()
            
            logger.debug(" Background cleanup concluído")
            
        except Exception as e:
            logger.error(f" Erro no cleanup: {str(e)}")
    
    async def _collect_stats(self):
        """Coleta estatísticas de todos os níveis"""
        try:
            # Coletar estatísticas individuais
            level_stats = {}
            for level_name, cache_instance in self.cache_hierarchy:
                level_stats[level_name] = cache_instance.get_stats()
            
            # Calcular hit rate global
            total_requests = self.global_stats['total_requests']
            if total_requests > 0:
                hit_rate = self.global_stats['total_hits'] / total_requests
            else:
                hit_rate = 0.0
            
            # Atualizar métricas
            metrics.record_gauge('cache_hit_rate', hit_rate)
            metrics.record_gauge('cache_total_requests', total_requests)
            
            for level_name, stats in level_stats.items():
                metrics.record_gauge(f'cache_{level_name}_entries', stats.total_entries)
                metrics.record_gauge(f'cache_{level_name}_size_bytes', stats.total_size_bytes)
            
            logger.debug(f" Stats coletados: hit_rate={hit_rate:.2%}")
            
        except Exception as e:
            logger.error(f" Erro coletando stats: {str(e)}")
    
    def get_global_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas globais do sistema"""
        level_stats = {}
        for level_name, cache_instance in self.cache_hierarchy:
            level_stats[level_name] = cache_instance.get_stats().__dict__
        
        total_requests = self.global_stats['total_requests']
        if total_requests > 0:
            hit_rate = self.global_stats['total_hits'] / total_requests
        else:
            hit_rate = 0.0
        
        return {
            'global_stats': self.global_stats,
            'hit_rate': hit_rate,
            'cache_levels': len(self.cache_hierarchy),
            'level_stats': level_stats,
            'config': self.config,
            'is_running': self.is_running
        }
    
    def clear_all(self, level: Optional[str] = None):
        """Limpa cache(s)"""
        if level:
            cache_instance = self._get_cache_by_level(level)
            if cache_instance:
                cache_instance.clear()
                logger.info(f" Cache {level} limpo")
            return
        
        # Limpar todos os níveis
        for _, cache_instance in self.cache_hierarchy:
            try:
                cache_instance.clear()
            except Exception as e:
                logger.error(f" Erro limpando cache: {str(e)}")
        
        # Resetar estatísticas globais
        self.global_stats = {
            'total_requests': 0,
            'total_hits': 0,
            'total_misses': 0,
            'cache_level_hits': defaultdict(int),
            'average_response_time': 0.0,
            'compression_savings': 0
        }
        
        logger.info(" Todos os caches limpos")
    
    async def cleanup(self):
        """Limpa recursos do sistema de cache"""
        logger.info(" Limpando MassiveCacheSystem...")
        
        self.is_running = False
        
        # Cancelar tarefas em background
        for task in self.background_tasks:
            task.cancel()
        
        # Limpar caches
        self.clear_all()
        
        # Fechar conexões
        if self.disk_cache:
            self.disk_cache.conn.close()
        
        logger.info(" MassiveCacheSystem limpo")

# Instância global do sistema de cache
massive_cache_system = MassiveCacheSystem()
