"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - SQLite Storage
Armazenamento persistente com SQLite
"""

import sqlite3
import asyncio
import json
import time
from typing import Any, Optional, Dict, List, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import threading
import logging
from pathlib import Path

from .logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class StorageConfig:
    """Configuração do storage SQLite"""
    db_path: str = "./data/omniscient.db"
    max_connections: int = 10
    connection_timeout: float = 30.0
    enable_wal: bool = True
    enable_foreign_keys: bool = True
    vacuum_interval: int = 3600  # segundos
    
class SQLiteStorage:
    """Storage persistente com SQLite"""
    
    def __init__(self, config: Optional[StorageConfig] = None):
        self.config = config or StorageConfig()
        self.db_path = Path(self.config.db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.connections = {}
        self.connection_lock = threading.Lock()
        self.is_initialized = False
        
        logger.info(f"💾 SQLite Storage inicializado (db: {self.db_path})")
    
    async def initialize(self):
        """Inicializa o storage"""
        if self.is_initialized:
            return
        
        try:
            # Criar tabelas
            await self._create_tables()
            
            # Configurar otimizações
            await self._configure_database()
            
            self.is_initialized = True
            logger.info("✅ SQLite Storage pronto")
            
        except Exception as e:
            logger.error(f"❌ Erro inicializando storage: {str(e)}")
            raise
    
    def _get_connection(self) -> sqlite3.Connection:
        """Obtém conexão com o banco"""
        thread_id = threading.current_thread().ident
        
        with self.connection_lock:
            if thread_id not in self.connections:
                conn = sqlite3.connect(
                    self.db_path,
                    timeout=self.config.connection_timeout,
                    check_same_thread=False
                )
                
                # Configurar conexão
                conn.row_factory = sqlite3.Row
                
                self.connections[thread_id] = conn
                logger.debug(f"🔌 Nova conexão SQLite para thread {thread_id}")
            
            return self.connections[thread_id]
    
    async def _create_tables(self):
        """Cria tabelas do banco"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Tabela de buscas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS searches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                results_count INTEGER DEFAULT 0,
                processing_time REAL DEFAULT 0.0,
                sources_used TEXT,
                summary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de resultados
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                search_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                description TEXT,
                source TEXT NOT NULL,
                relevance_score REAL DEFAULT 0.0,
                timestamp REAL DEFAULT 0.0,
                extracted_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (search_id) REFERENCES searches (id) ON DELETE CASCADE
            )
        ''')
        
        # Tabela de cache
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                ttl REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                access_count INTEGER DEFAULT 0
            )
        ''')
        
        # Tabela de métricas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                tags TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de configurações
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                module TEXT,
                extra_data TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Índices para performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_searches_query ON searches(query)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_searches_created ON searches(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_results_search_id ON search_results(search_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_results_source ON search_results(source)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_results_relevance ON search_results(relevance_score)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_cache_ttl ON cache(ttl)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics(metric_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp)')
        
        conn.commit()
        logger.debug("📋 Tabelas SQLite criadas/verificadas")
    
    async def _configure_database(self):
        """Configura otimizações do banco"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Configurações de performance
        if self.config.enable_wal:
            cursor.execute('PRAGMA journal_mode=WAL')
        
        if self.config.enable_foreign_keys:
            cursor.execute('PRAGMA foreign_keys=ON')
        
        cursor.execute('PRAGMA synchronous=NORMAL')
        cursor.execute('PRAGMA cache_size=10000')
        cursor.execute('PRAGMA temp_store=MEMORY')
        cursor.execute('PRAGMA mmap_size=268435456')  # 256MB
        
        conn.commit()
        logger.debug("⚙️ Banco SQLite configurado")
    
    async def save_search(self, query: str, results: List[Dict[str, Any]], 
                          summary: str, processing_time: float,
                          sources_used: List[str]) -> int:
        """
        Salva busca e resultados
        
        Args:
            query: Query da busca
            results: Lista de resultados
            summary: Resumo gerado
            processing_time: Tempo de processamento
            sources_used: Fontes utilizadas
            
        Returns:
            ID da busca salva
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Inserir busca
            cursor.execute('''
                INSERT INTO searches (query, results_count, processing_time, 
                                   sources_used, summary)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                query,
                len(results),
                processing_time,
                json.dumps(sources_used),
                summary
            ))
            
            search_id = cursor.lastrowid
            
            # Inserir resultados
            for result in results:
                extracted_data = json.dumps(result.get('extracted_data', {}))
                
                cursor.execute('''
                    INSERT INTO search_results (search_id, title, url, description,
                                            source, relevance_score, timestamp,
                                            extracted_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    search_id,
                    result.get('title', ''),
                    result.get('url', ''),
                    result.get('description', ''),
                    result.get('source', ''),
                    result.get('relevance_score', 0.0),
                    result.get('timestamp', time.time()),
                    extracted_data
                ))
            
            conn.commit()
            logger.info(f"💾 Busca salva: {search_id} ({len(results)} resultados)")
            return search_id
            
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Erro salvando busca: {str(e)}")
            raise
    
    async def get_search(self, search_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtém busca por ID
        
        Args:
            search_id: ID da busca
            
        Returns:
            Dados da busca ou None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Obter dados da busca
            cursor.execute('''
                SELECT * FROM searches WHERE id = ?
            ''', (search_id,))
            
            search_row = cursor.fetchone()
            if not search_row:
                return None
            
            # Obter resultados
            cursor.execute('''
                SELECT * FROM search_results WHERE search_id = ?
                ORDER BY relevance_score DESC
            ''', (search_id,))
            
            result_rows = cursor.fetchall()
            
            # Montar resposta
            search_data = {
                'id': search_row['id'],
                'query': search_row['query'],
                'results_count': search_row['results_count'],
                'processing_time': search_row['processing_time'],
                'sources_used': json.loads(search_row['sources_used'] or '[]'),
                'summary': search_row['summary'],
                'created_at': search_row['created_at'],
                'updated_at': search_row['updated_at'],
                'results': []
            }
            
            for row in result_rows:
                result = {
                    'id': row['id'],
                    'title': row['title'],
                    'url': row['url'],
                    'description': row['description'],
                    'source': row['source'],
                    'relevance_score': row['relevance_score'],
                    'timestamp': row['timestamp'],
                    'extracted_data': json.loads(row['extracted_data'] or '{}'),
                    'created_at': row['created_at']
                }
                search_data['results'].append(result)
            
            return search_data
            
        except Exception as e:
            logger.error(f"❌ Erro obtendo busca {search_id}: {str(e)}")
            return None
    
    async def search_queries(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Busca queries anteriores
        
        Args:
            query: Termo de busca
            limit: Número máximo de resultados
            
        Returns:
            Lista de buscas encontradas
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT id, query, results_count, processing_time, created_at
                FROM searches
                WHERE query LIKE ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (f'%{query}%', limit))
            
            rows = cursor.fetchall()
            
            searches = []
            for row in rows:
                search = {
                    'id': row['id'],
                    'query': row['query'],
                    'results_count': row['results_count'],
                    'processing_time': row['processing_time'],
                    'created_at': row['created_at']
                }
                searches.append(search)
            
            return searches
            
        except Exception as e:
            logger.error(f"❌ Erro buscando queries: {str(e)}")
            return []
    
    async def get_recent_searches(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Obtém buscas recentes
        
        Args:
            limit: Número máximo de resultados
            
        Returns:
            Lista de buscas recentes
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT id, query, results_count, processing_time, created_at
                FROM searches
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            
            searches = []
            for row in rows:
                search = {
                    'id': row['id'],
                    'query': row['query'],
                    'results_count': row['results_count'],
                    'processing_time': row['processing_time'],
                    'created_at': row['created_at']
                }
                searches.append(search)
            
            return searches
            
        except Exception as e:
            logger.error(f"❌ Erro obtendo buscas recentes: {str(e)}")
            return []
    
    async def cache_set(self, key: str, value: Any, ttl: float) -> bool:
        """
        Armazena valor no cache
        
        Args:
            key: Chave do cache
            value: Valor a ser armazenado
            ttl: Time to live em segundos
            
        Returns:
            True se armazenado com sucesso
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            expires_at = time.time() + ttl
            value_json = json.dumps(value)
            
            cursor.execute('''
                INSERT OR REPLACE INTO cache (key, value, ttl, accessed_at)
                VALUES (?, ?, ?, ?)
            ''', (key, value_json, expires_at, time.time()))
            
            conn.commit()
            logger.debug(f"💾 Cache set: {key} (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Erro cache set {key}: {str(e)}")
            return False
    
    async def cache_get(self, key: str) -> Optional[Any]:
        """
        Obtém valor do cache
        
        Args:
            key: Chave do cache
            
        Returns:
            Valor armazenado ou None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT value, ttl FROM cache WHERE key = ?
            ''', (key,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            # Verificar expiração
            if time.time() > row['ttl']:
                # Remover entrada expirada
                cursor.execute('DELETE FROM cache WHERE key = ?', (key,))
                conn.commit()
                return None
            
            # Atualizar acesso
            cursor.execute('''
                UPDATE cache 
                SET accessed_at = ?, access_count = access_count + 1
                WHERE key = ?
            ''', (time.time(), key))
            
            conn.commit()
            
            # Deserializar valor
            value = json.loads(row['value'])
            logger.debug(f"📦 Cache hit: {key}")
            return value
            
        except Exception as e:
            logger.error(f"❌ Erro cache get {key}: {str(e)}")
            return None
    
    async def cache_delete(self, key: str) -> bool:
        """
        Remove chave do cache
        
        Args:
            key: Chave a ser removida
            
        Returns:
            True se removida com sucesso
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM cache WHERE key = ?', (key,))
            conn.commit()
            
            deleted = cursor.rowcount > 0
            if deleted:
                logger.debug(f"🗑️ Cache delete: {key}")
            
            return deleted
            
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Erro cache delete {key}: {str(e)}")
            return False
    
    async def cache_cleanup(self) -> int:
        """
        Limpa entradas expiradas do cache
        
        Returns:
            Número de entradas removidas
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            current_time = time.time()
            cursor.execute('DELETE FROM cache WHERE ttl < ?', (current_time,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            if deleted_count > 0:
                logger.info(f"🧹 Cache cleanup: {deleted_count} entradas removidas")
            
            return deleted_count
            
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Erro cache cleanup: {str(e)}")
            return 0
    
    async def save_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """
        Salva métrica
        
        Args:
            name: Nome da métrica
            value: Valor da métrica
            tags: Tags adicionais
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            tags_json = json.dumps(tags) if tags else None
            
            cursor.execute('''
                INSERT INTO metrics (metric_name, metric_value, tags)
                VALUES (?, ?, ?)
            ''', (name, value, tags_json))
            
            conn.commit()
            logger.debug(f"📊 Métrica salva: {name} = {value}")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Erro salvando métrica {name}: {str(e)}")
    
    async def get_metrics(self, name: Optional[str] = None, 
                          start_time: Optional[float] = None,
                          end_time: Optional[float] = None,
                          limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Obtém métricas
        
        Args:
            name: Nome da métrica (opcional)
            start_time: Tempo inicial (opcional)
            end_time: Tempo final (opcional)
            limit: Número máximo de resultados
            
        Returns:
            Lista de métricas
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            query = 'SELECT * FROM metrics WHERE 1=1'
            params = []
            
            if name:
                query += ' AND metric_name = ?'
                params.append(name)
            
            if start_time:
                query += ' AND timestamp >= ?'
                params.append(start_time)
            
            if end_time:
                query += ' AND timestamp <= ?'
                params.append(end_time)
            
            query += ' ORDER BY timestamp DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            metrics = []
            for row in rows:
                metric = {
                    'id': row['id'],
                    'name': row['metric_name'],
                    'value': row['metric_value'],
                    'tags': json.loads(row['tags'] or '{}'),
                    'timestamp': row['timestamp']
                }
                metrics.append(metric)
            
            return metrics
            
        except Exception as e:
            logger.error(f"❌ Erro obtendo métricas: {str(e)}")
            return []
    
    async def save_setting(self, key: str, value: str) -> bool:
        """
        Salva configuração
        
        Args:
            key: Chave da configuração
            value: Valor da configuração
            
        Returns:
            True se salvo com sucesso
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO settings (key, value, updated_at)
                VALUES (?, ?, ?)
            ''', (key, value, datetime.now()))
            
            conn.commit()
            logger.debug(f"⚙️ Configuração salva: {key}")
            return True
            
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Erro salvando configuração {key}: {str(e)}")
            return False
    
    async def get_setting(self, key: str) -> Optional[str]:
        """
        Obtém configuração
        
        Args:
            key: Chave da configuração
            
        Returns:
            Valor da configuração ou None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
            row = cursor.fetchone()
            
            return row['value'] if row else None
            
        except Exception as e:
            logger.error(f"❌ Erro obtendo configuração {key}: {str(e)}")
            return None
    
    async def log_message(self, level: str, message: str, module: Optional[str] = None,
                         extra_data: Optional[Dict[str, Any]] = None):
        """
        Salva mensagem de log
        
        Args:
            level: Nível do log
            message: Mensagem
            module: Módulo de origem
            extra_data: Dados adicionais
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            extra_json = json.dumps(extra_data) if extra_data else None
            
            cursor.execute('''
                INSERT INTO logs (level, message, module, extra_data)
                VALUES (?, ?, ?, ?)
            ''', (level, message, module, extra_json))
            
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Erro salvando log: {str(e)}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Obtém estatísticas do storage
        
        Returns:
            Estatísticas detalhadas
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            stats = {}
            
            # Estatísticas de buscas
            cursor.execute('SELECT COUNT(*) as count FROM searches')
            stats['total_searches'] = cursor.fetchone()['count']
            
            cursor.execute('SELECT COUNT(*) as count FROM search_results')
            stats['total_results'] = cursor.fetchone()['count']
            
            # Estatísticas de cache
            cursor.execute('SELECT COUNT(*) as count FROM cache')
            stats['cache_entries'] = cursor.fetchone()['count']
            
            cursor.execute('SELECT COUNT(*) as count FROM cache WHERE ttl > ?', (time.time(),))
            stats['cache_valid_entries'] = cursor.fetchone()['count']
            
            # Estatísticas de métricas
            cursor.execute('SELECT COUNT(*) as count FROM metrics')
            stats['total_metrics'] = cursor.fetchone()['count']
            
            # Estatísticas de logs
            cursor.execute('SELECT COUNT(*) as count FROM logs')
            stats['total_logs'] = cursor.fetchone()['count']
            
            # Tamanho do banco
            cursor.execute('SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()')
            size_row = cursor.fetchone()
            stats['database_size_bytes'] = size_row['size'] if size_row else 0
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Erro obtendo estatísticas: {str(e)}")
            return {}
    
    async def vacuum(self):
        """Executa VACUUM no banco"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('VACUUM')
            conn.commit()
            logger.info("🧹 VACUUM executado no banco")
            
        except Exception as e:
            logger.error(f"❌ Erro VACUUM: {str(e)}")
    
    async def cleanup(self):
        """Limpa recursos"""
        with self.connection_lock:
            for thread_id, conn in self.connections.items():
                try:
                    conn.close()
                    logger.debug(f"🔌 Conexão fechada: thread {thread_id}")
                except:
                    pass
            
            self.connections.clear()
            self.is_initialized = False
            
            logger.info("🧹 SQLite Storage limpo")
    
    def __del__(self):
        """Destrutor"""
        if hasattr(self, 'connections'):
            try:
                asyncio.run(self.cleanup())
            except:
                pass
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificação de saúde do storage SQLite"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Verificar se tabelas existem
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name IN (
                    'searches', 'results', 'cache', 'metrics', 'settings', 'logs'
                )
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            # Verificar integridade do banco
            cursor.execute("PRAGMA integrity_check")
            integrity = cursor.fetchone()[0]
            
            return {
                'status': 'healthy' if integrity == 'ok' else 'error',
                'component': 'sqlite_storage',
                'timestamp': time.time(),
                'database_path': self.db_path,
                'tables_exist': len(tables) == 6,
                'tables': tables,
                'integrity_check': integrity,
                'connections_active': len(self.connections)
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'component': 'sqlite_storage',
                'timestamp': time.time(),
                'error': str(e)
            }
