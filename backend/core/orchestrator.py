"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - System Orchestrator
Controla execução geral do sistema
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from .pipeline import SearchPipeline
from .scheduler import TaskScheduler
from .ranking import RankingEngine
from utils.logger import setup_logger
from utils.metrics import MetricsCollector

logger = setup_logger(__name__)
metrics = MetricsCollector()

class SystemOrchestrator:
    """Orquestrador principal do sistema"""
    
    def __init__(self):
        self.pipeline = SearchPipeline()
        self.scheduler = TaskScheduler()
        self.ranking_engine = RankingEngine()
        self.is_initialized = False
        self.startup_time = None
        self.system_stats = {
            'total_searches': 0,
            'successful_searches': 0,
            'failed_searches': 0,
            'average_processing_time': 0.0,
            'active_tasks': 0,
            'cache_hits': 0
        }
        
    async def initialize(self):
        """Inicializa todos os componentes do sistema"""
        try:
            logger.info("🚀 Inicializando orquestrador do sistema...")
            self.startup_time = datetime.now()
            
            # Inicializar pipeline
            await self.pipeline.initialize()
            
            # Inicializar scheduler
            await self.scheduler.initialize()
            
            # Inicializar ranking engine
            await self.ranking_engine.initialize()
            
            # Iniciar tarefas agendadas
            await self.scheduler.start_scheduled_tasks()
            
            self.is_initialized = True
            logger.info("✅ Orquestrador inicializado com sucesso")
            
        except Exception as e:
            logger.error(f"❌ Erro na inicialização: {str(e)}")
            raise
    
    async def shutdown(self):
        """Desliga o sistema de forma graceful"""
        try:
            logger.info("🔄 Desligando orquestrador...")
            
            # Parar scheduler
            await self.scheduler.stop()
            
            # Limpar recursos
            await self.pipeline.cleanup()
            
            self.is_initialized = False
            logger.info("✅ Sistema desligado com sucesso")
            
        except Exception as e:
            logger.error(f"❌ Erro no desligamento: {str(e)}")
    
    async def execute_search(self, query: str, **kwargs) -> Dict[str, Any]:
        """Executa busca completa"""
        if not self.is_initialized:
            raise RuntimeError("Sistema não inicializado")
        
        start_time = datetime.now()
        self.system_stats['active_tasks'] += 1
        
        try:
            logger.info(f"🔍 Executando busca: '{query}'")
            
            # Executar pipeline
            result = await self.pipeline.execute_search(query, **kwargs)
            
            # Atualizar estatísticas
            self.system_stats['total_searches'] += 1
            self.system_stats['successful_searches'] += 1
            
            # Calcular tempo médio
            processing_time = result.get('processing_stats', {}).get('total_search_time', 0.0)
            total_time = self.system_stats['average_processing_time'] * (self.system_stats['total_searches'] - 1)
            self.system_stats['average_processing_time'] = (total_time + processing_time) / self.system_stats['total_searches']
            
            # Retornar resultado formatado
            return {
                'status': 'success',
                'query': query,
                'results': result.get('data', []),
                'summary': result.get('summary', ''),
                'stats': {
                    'total_results': result.get('total', 0),
                    'processing_time': processing_time,
                    'sources_used': result.get('sources_used', []),
                    'extracted_data': result.get('extracted_data', {})
                },
                'system_stats': self.get_system_stats()
            }
            
        except Exception as e:
            self.system_stats['total_searches'] += 1
            self.system_stats['failed_searches'] += 1
            logger.error(f"❌ Erro na busca: {str(e)}")
            
            return {
                'status': 'error',
                'query': query,
                'error': str(e),
                'system_stats': self.get_system_stats()
            }
        
        finally:
            self.system_stats['active_tasks'] -= 1
    
    async def schedule_search(self, query: str, schedule_time: datetime, **kwargs):
        """Agenda uma busca para execução futura"""
        if not self.is_initialized:
            raise RuntimeError("Sistema não inicializado")
        
        await self.scheduler.schedule_task(
            task_type='search',
            execute_at=schedule_time,
            params={'query': query, **kwargs}
        )
        
        logger.info(f"⏰ Busca agendada: '{query}' para {schedule_time}")
    
    async def get_cached_result(self, query: str) -> Optional[Dict[str, Any]]:
        """Retorna resultado em cache se disponível"""
        try:
            cache_key = f"search:{query}:500:None"
            result = await self.pipeline.cache.get(cache_key)
            
            if result:
                self.system_stats['cache_hits'] += 1
                return {
                    'status': 'cached',
                    'query': query,
                    'results': result.get('data', []),
                    'summary': result.get('summary', ''),
                    'stats': {
                        'total_results': result.get('total', 0),
                        'processing_time': result.get('processing_stats', {}).get('total_search_time', 0.0),
                        'sources_used': result.get('sources_used', []),
                        'extracted_data': result.get('extracted_data', {})
                    }
                }
            
            return None
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao buscar cache: {str(e)}")
            return None
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do sistema"""
        uptime = None
        if self.startup_time:
            uptime = datetime.now() - self.startup_time
        
        return {
            **self.system_stats,
            'uptime_seconds': uptime.total_seconds() if uptime else 0,
            'uptime_formatted': str(uptime) if uptime else '00:00:00',
            'is_initialized': self.is_initialized,
            'success_rate': (
                self.system_stats['successful_searches'] / max(1, self.system_stats['total_searches']) * 100
            )
        }
    
    def _format_result(self, result) -> Dict[str, Any]:
        """Formata resultado para saída JSON"""
        return {
            'title': result.title,
            'url': result.url,
            'description': result.description,
            'source': result.source,
            'timestamp': result.timestamp,
            'relevance_score': result.relevance_score,
            'extracted_data': result.extracted_data or {}
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificação de saúde do sistema"""
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'components': {}
        }
        
        try:
            # Verificar pipeline
            pipeline_health = await self.pipeline.health_check()
            health_status['components']['pipeline'] = pipeline_health
            
            # Verificar scheduler
            scheduler_health = await self.scheduler.health_check()
            health_status['components']['scheduler'] = scheduler_health
            
            # Verificar ranking engine
            ranking_health = await self.ranking_engine.health_check()
            health_status['components']['ranking'] = ranking_health
            
            # Verificar se algum componente está unhealthy
            for component, status in health_status['components'].items():
                if status.get('status') != 'healthy':
                    health_status['status'] = 'degraded'
                    break
            
        except Exception as e:
            logger.error(f"❌ Erro no health check: {str(e)}")
            health_status['status'] = 'unhealthy'
            health_status['error'] = str(e)
        
        return health_status
