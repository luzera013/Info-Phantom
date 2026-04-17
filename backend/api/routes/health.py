"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - Health Route
Rota para verificação de saúde do sistema
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import time
import psutil
import asyncio
import logging

from ...core.orchestrator import SystemOrchestrator
from ...utils.sqlite import SQLiteStorage
from ...utils.memory_cache import MemoryCache
from ...utils.ttl_cache import TTLCache
from ...utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()

# Modelos de dados
class HealthStatus(BaseModel):
    """Modelo para status de saúde"""
    status: str = Field(..., description="Status geral do sistema")
    timestamp: float = Field(..., description="Timestamp da verificação")
    uptime: float = Field(..., description="Uptime em segundos")
    version: str = Field(..., description="Versão do sistema")
    components: Dict[str, Any] = Field(..., description="Status dos componentes")
    system_metrics: Dict[str, Any] = Field(..., description="Métricas do sistema")
    checks: Dict[str, bool] = Field(..., description="Verificações de saúde")

class ComponentHealth(BaseModel):
    """Modelo para saúde de componente"""
    name: str
    status: str
    response_time: float
    last_check: float
    error: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None

# Dependencies
def get_orchestrator() -> SystemOrchestrator:
    """Dependency injection para orquestrador"""
    from ...main import app
    if not hasattr(app.state, 'orchestrator'):
        raise HTTPException(status_code=503, detail="Sistema não inicializado")
    return app.state.orchestrator

async def get_storage() -> SQLiteStorage:
    """Dependency injection para storage"""
    storage = SQLiteStorage()
    await storage.initialize()
    return storage

async def get_memory_cache() -> MemoryCache:
    """Dependency injection para memory cache"""
    return MemoryCache()

async def get_ttl_cache() -> TTLCache:
    """Dependency injection para TTL cache"""
    cache = TTLCache()
    await cache.initialize()
    return cache

# Timestamp de inicialização
START_TIME = time.time()
SYSTEM_VERSION = "3.0.0"

@router.get("/health", response_model=HealthStatus)
async def health_check(
    orchestrator: SystemOrchestrator = Depends(get_orchestrator),
    storage: SQLiteStorage = Depends(get_storage),
    memory_cache: MemoryCache = Depends(get_memory_cache),
    ttl_cache: TTLCache = Depends(get_ttl_cache)
):
    """
    Verificação de saúde completa do sistema
    
    Args:
        orchestrator: Orquestrador do sistema
        storage: Storage do banco
        memory_cache: Cache em memória
        ttl_cache: Cache TTL
        
    Returns:
        Status completo de saúde
    """
    start_time = time.time()
    logger.info("🏥 Iniciando verificação de saúde completa")
    
    try:
        # Status geral
        overall_status = "healthy"
        uptime = time.time() - START_TIME
        
        # Verificar componentes
        components = {}
        checks = {}
        
        # Verificar orquestrador
        try:
            orchestrator_health = await orchestrator.health_check()
            components['orchestrator'] = orchestrator_health
            checks['orchestrator'] = orchestrator_health.get('status') == 'healthy'
            
            if orchestrator_health.get('status') != 'healthy':
                overall_status = "degraded"
                
        except Exception as e:
            components['orchestrator'] = {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': time.time()
            }
            checks['orchestrator'] = False
            overall_status = "unhealthy"
        
        # Verificar storage
        try:
            storage_stats = await storage.get_stats()
            components['storage'] = {
                'status': 'healthy',
                'stats': storage_stats,
                'timestamp': time.time()
            }
            checks['storage'] = True
            
        except Exception as e:
            components['storage'] = {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': time.time()
            }
            checks['storage'] = False
            overall_status = "degraded"
        
        # Verificar memory cache
        try:
            cache_stats = await memory_cache.get_stats()
            components['memory_cache'] = {
                'status': 'healthy',
                'stats': cache_stats,
                'timestamp': time.time()
            }
            checks['memory_cache'] = True
            
        except Exception as e:
            components['memory_cache'] = {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': time.time()
            }
            checks['memory_cache'] = False
            overall_status = "degraded"
        
        # Verificar TTL cache
        try:
            ttl_stats = await ttl_cache.get_stats()
            components['ttl_cache'] = {
                'status': 'healthy',
                'stats': ttl_stats,
                'timestamp': time.time()
            }
            checks['ttl_cache'] = True
            
        except Exception as e:
            components['ttl_cache'] = {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': time.time()
            }
            checks['ttl_cache'] = False
            overall_status = "degraded"
        
        # Métricas do sistema
        system_metrics = await get_system_metrics()
        
        # Verificações adicionais
        checks['disk_space'] = system_metrics['disk']['free_percent'] > 10
        checks['memory_usage'] = system_metrics['memory']['percent'] < 90
        checks['cpu_usage'] = system_metrics['cpu']['percent'] < 80
        
        if not all(checks.values()):
            if overall_status == "healthy":
                overall_status = "degraded"
        
        response_time = time.time() - start_time
        
        health_status = HealthStatus(
            status=overall_status,
            timestamp=time.time(),
            uptime=uptime,
            version=SYSTEM_VERSION,
            components=components,
            system_metrics=system_metrics,
            checks=checks
        )
        
        logger.info(f"🏥 Verificação de saúde concluída: {overall_status} ({response_time:.3f}s)")
        return health_status
        
    except Exception as e:
        logger.error(f"❌ Erro na verificação de saúde: {str(e)}")
        
        return HealthStatus(
            status="unhealthy",
            timestamp=time.time(),
            uptime=time.time() - START_TIME,
            version=SYSTEM_VERSION,
            components={'error': str(e)},
            system_metrics=await get_system_metrics(),
            checks={'health_check': False}
        )

@router.get("/health/ready")
async def readiness_check(
    orchestrator: SystemOrchestrator = Depends(get_orchestrator)
):
    """
    Verificação de prontidão (readiness probe)
    
    Args:
        orchestrator: Orquestrador do sistema
        
    Returns:
        Status de prontidão
    """
    try:
        # Verificar se orquestrador está pronto
        if not hasattr(orchestrator, 'is_initialized') or not orchestrator.is_initialized:
            raise HTTPException(
                status_code=503,
                detail="Sistema não inicializado"
            )
        
        # Verificar se pode executar uma busca simples
        test_result = await orchestrator.get_cached_result("health_check_test")
        
        return {
            "status": "ready",
            "timestamp": time.time(),
            "version": SYSTEM_VERSION
        }
        
    except Exception as e:
        logger.error(f"❌ Erro na verificação de prontidão: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Sistema não pronto: {str(e)}"
        )

@router.get("/health/live")
async def liveness_check():
    """
    Verificação de vivacidade (liveness probe)
    
    Returns:
        Status de vivacidade
    """
    try:
        # Verificação básica de que o processo está vivo
        uptime = time.time() - START_TIME
        
        return {
            "status": "alive",
            "timestamp": time.time(),
            "uptime": uptime,
            "version": SYSTEM_VERSION
        }
        
    except Exception as e:
        logger.error(f"❌ Erro na verificação de vivacidade: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Sistema não vivo: {str(e)}"
        )

@router.get("/metrics")
async def get_metrics(
    orchestrator: SystemOrchestrator = Depends(get_orchestrator),
    storage: SQLiteStorage = Depends(get_storage)
):
    """
    Obtém métricas detalhadas do sistema
    
    Args:
        orchestrator: Orquestrador do sistema
        storage: Storage do banco
        
    Returns:
        Métricas detalhadas
    """
    try:
        logger.info("📊 Coletando métricas do sistema")
        
        # Métricas do orquestrador
        orchestrator_stats = orchestrator.get_system_stats()
        
        # Métricas do storage
        storage_stats = await storage.get_stats()
        
        # Métricas do sistema
        system_metrics = await get_system_metrics()
        
        # Métricas de performance
        performance_metrics = await get_performance_metrics()
        
        # Combinar todas as métricas
        all_metrics = {
            "timestamp": time.time(),
            "version": SYSTEM_VERSION,
            "uptime": time.time() - START_TIME,
            "orchestrator": orchestrator_stats,
            "storage": storage_stats,
            "system": system_metrics,
            "performance": performance_metrics
        }
        
        logger.info("✅ Métricas coletadas com sucesso")
        return all_metrics
        
    except Exception as e:
        logger.error(f"❌ Erro coletando métricas: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro coletando métricas: {str(e)}"
        )

@router.get("/health/components")
async def get_component_health():
    """
    Obtém saúde de componentes individuais
    
    Returns:
        Saúde de cada componente
    """
    try:
        logger.info("🔍 Verificando saúde dos componentes")
        
        components = {}
        
        # Verificar cada componente
        component_checks = [
            ("database", check_database_health),
            ("cache", check_cache_health),
            ("disk_space", check_disk_space),
            ("memory", check_memory_health),
            ("network", check_network_health)
        ]
        
        for component_name, check_func in component_checks:
            try:
                start_time = time.time()
                health = await check_func()
                response_time = time.time() - start_time
                
                components[component_name] = ComponentHealth(
                    name=component_name,
                    status=health.get('status', 'unknown'),
                    response_time=response_time,
                    last_check=time.time(),
                    error=health.get('error'),
                    metrics=health.get('metrics')
                )
                
            except Exception as e:
                components[component_name] = ComponentHealth(
                    name=component_name,
                    status='unhealthy',
                    response_time=0.0,
                    last_check=time.time(),
                    error=str(e)
                )
        
        logger.info("✅ Verificação de componentes concluída")
        return {"components": components}
        
    except Exception as e:
        logger.error(f"❌ Erro verificando componentes: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro verificando componentes: {str(e)}"
        )

# Funções auxiliares para verificação de componentes
async def get_system_metrics() -> Dict[str, Any]:
    """Obtém métricas do sistema operacional"""
    try:
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        
        # Memória
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        # Disco
        disk = psutil.disk_usage('/')
        
        # Rede
        network = psutil.net_io_counters()
        
        # Processo
        process = psutil.Process()
        process_memory = process.memory_info()
        process_cpu = process.cpu_percent()
        
        return {
            "cpu": {
                "percent": cpu_percent,
                "count": cpu_count,
                "frequency": {
                    "current": cpu_freq.current if cpu_freq else 0,
                    "min": cpu_freq.min if cpu_freq else 0,
                    "max": cpu_freq.max if cpu_freq else 0
                }
            },
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used,
                "free": memory.free
            },
            "swap": {
                "total": swap.total,
                "used": swap.used,
                "free": swap.free,
                "percent": swap.percent
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": (disk.used / disk.total) * 100,
                "free_percent": (disk.free / disk.total) * 100
            },
            "network": {
                "bytes_sent": network.bytes_sent if network else 0,
                "bytes_recv": network.bytes_recv if network else 0,
                "packets_sent": network.packets_sent if network else 0,
                "packets_recv": network.packets_recv if network else 0
            },
            "process": {
                "pid": process.pid,
                "memory_rss": process_memory.rss,
                "memory_vms": process_memory.vms,
                "cpu_percent": process_cpu,
                "num_threads": process.num_threads(),
                "create_time": process.create_time()
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Erro obtendo métricas do sistema: {str(e)}")
        return {"error": str(e)}

async def get_performance_metrics() -> Dict[str, Any]:
    """Obtém métricas de performance"""
    try:
        # Métricas de performance
        import time
        
        # Teste de performance de CPU
        start_time = time.time()
        await asyncio.sleep(0.001)  # 1ms
        cpu_response_time = time.time() - start_time
        
        # Teste de I/O (simulado)
        io_start = time.time()
        test_data = "x" * 1000
        processed_data = test_data.upper()
        io_response_time = time.time() - io_start
        
        return {
            "response_time": {
                "cpu_test": cpu_response_time,
                "io_test": io_response_time
            },
            "throughput": {
                "data_processed": len(processed_data),
                "processing_rate": len(processed_data) / io_response_time if io_response_time > 0 else 0
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Erro obtendo métricas de performance: {str(e)}")
        return {"error": str(e)}

async def check_database_health() -> Dict[str, Any]:
    """Verifica saúde do banco de dados"""
    try:
        storage = await get_storage()
        stats = await storage.get_stats()
        
        return {
            "status": "healthy",
            "metrics": {
                "total_searches": stats.get("total_searches", 0),
                "total_results": stats.get("total_results", 0),
                "cache_entries": stats.get("cache_entries", 0),
                "database_size": stats.get("database_size_bytes", 0)
            }
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

async def check_cache_health() -> Dict[str, Any]:
    """Verifica saúde do cache"""
    try:
        cache = await get_memory_cache()
        stats = await cache.get_stats()
        
        return {
            "status": "healthy",
            "metrics": {
                "size": stats.get("size", 0),
                "hit_rate": stats.get("hit_rate", 0),
                "memory_usage": stats.get("memory_usage", 0)
            }
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

async def check_disk_space() -> Dict[str, Any]:
    """Verifica espaço em disco"""
    try:
        disk = psutil.disk_usage('/')
        free_percent = (disk.free / disk.total) * 100
        
        status = "healthy"
        if free_percent < 10:
            status = "critical"
        elif free_percent < 20:
            status = "warning"
        
        return {
            "status": status,
            "metrics": {
                "total": disk.total,
                "free": disk.free,
                "used": disk.used,
                "free_percent": free_percent
            }
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

async def check_memory_health() -> Dict[str, Any]:
    """Verifica saúde da memória"""
    try:
        memory = psutil.virtual_memory()
        
        status = "healthy"
        if memory.percent > 90:
            status = "critical"
        elif memory.percent > 80:
            status = "warning"
        
        return {
            "status": status,
            "metrics": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used
            }
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

async def check_network_health() -> Dict[str, Any]:
    """Verificação básica de rede"""
    try:
        # Verificar conexões de rede
        connections = len(psutil.net_connections())
        
        return {
            "status": "healthy",
            "metrics": {
                "active_connections": connections
            }
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
