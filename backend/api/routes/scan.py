"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - Scan Route
Rota principal para execução de buscas
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import asyncio
import time
import logging

from ...core.orchestrator import SystemOrchestrator
from ...utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()

# Modelos de dados
class ScanRequest(BaseModel):
    """Modelo para requisição de scan"""
    query: str = Field(..., min_length=1, max_length=500, description="Termo de busca")
    max_results: Optional[int] = Field(100, ge=1, le=1000, description="Número máximo de resultados")
    sources: Optional[List[str]] = Field(None, description="Fontes específicas para buscar")
    include_cache: Optional[bool] = Field(True, description="Usar resultados em cache")
    deep_scan: Optional[bool] = Field(False, description="Executar scan profundo")
    extract_data: Optional[bool] = Field(True, description="Extrair dados estruturados")
    use_ai: Optional[bool] = Field(True, description="Usar IA para análise")

class ScanResponse(BaseModel):
    """Modelo para resposta de scan"""
    status: str
    query: str
    results: List[Dict[str, Any]]
    summary: str
    stats: Dict[str, Any]
    system_stats: Dict[str, Any]
    processing_time: float
    timestamp: float

class ScanStatus(BaseModel):
    """Modelo para status de scan"""
    scan_id: str
    status: str
    progress: float
    current_step: str
    estimated_time: Optional[float]
    results_count: int
    error: Optional[str]

# Cache global para scans em andamento
active_scans = {}

def get_orchestrator() -> SystemOrchestrator:
    """Dependency injection para orquestrador"""
    # Em produção, isso viria do container DI
    from ...main import app
    if not hasattr(app.state, 'orchestrator'):
        raise HTTPException(status_code=503, detail="Sistema não inicializado")
    return app.state.orchestrator

@router.post("/scan", response_model=ScanResponse)
async def execute_scan(
    request: ScanRequest,
    background_tasks: BackgroundTasks,
    orchestrator: SystemOrchestrator = Depends(get_orchestrator)
):
    """
    Executa busca completa
    
    Args:
        request: Parâmetros da busca
        background_tasks: Tarefas em background
        orchestrator: Orquestrador do sistema
        
    Returns:
        Resultado da busca
    """
    start_time = time.time()
    scan_id = f"scan_{int(start_time * 1000)}"
    
    logger.info(f"🔍 Iniciando scan {scan_id}: '{request.query}'")
    
    try:
        # Verificar cache primeiro
        if request.include_cache:
            cached_result = await orchestrator.get_cached_result(request.query)
            if cached_result:
                logger.info(f"📦 Cache hit para scan {scan_id}")
                return ScanResponse(
                    status="cached",
                    query=request.query,
                    results=cached_result.get('results', []),
                    summary=cached_result.get('summary', ''),
                    stats=cached_result.get('stats', {}),
                    system_stats=cached_result.get('system_stats', {}),
                    processing_time=0.0,
                    timestamp=time.time()
                )
        
        # Registrar scan ativo
        active_scans[scan_id] = {
            'status': 'running',
            'progress': 0.0,
            'current_step': 'Iniciando busca...',
            'start_time': start_time,
            'query': request.query
        }
        
        # Executar busca
        result = await orchestrator.execute_search(
            query=request.query,
            max_results=request.max_results,
            sources=request.sources
        )
        
        # Atualizar status
        if scan_id in active_scans:
            active_scans[scan_id]['status'] = 'completed'
            active_scans[scan_id]['progress'] = 100.0
            active_scans[scan_id]['current_step'] = 'Concluído'
        
        processing_time = time.time() - start_time
        
        # Formatar resposta
        response = ScanResponse(
            status=result.get('status', 'success'),
            query=request.query,
            results=result.get('results', []),
            summary=result.get('summary', ''),
            stats=result.get('stats', {}),
            system_stats=result.get('system_stats', {}),
            processing_time=processing_time,
            timestamp=time.time()
        )
        
        # Limpar scan ativo após algum tempo
        background_tasks.add_task(cleanup_scan, scan_id)
        
        logger.info(f"✅ Scan {scan_id} concluído em {processing_time:.2f}s")
        return response
        
    except Exception as e:
        # Atualizar status com erro
        if scan_id in active_scans:
            active_scans[scan_id]['status'] = 'error'
            active_scans[scan_id]['error'] = str(e)
        
        logger.error(f"❌ Erro no scan {scan_id}: {str(e)}")
        
        raise HTTPException(
            status_code=500,
            detail=f"Erro durante scan: {str(e)}"
        )

@router.get("/scan/{scan_id}/status", response_model=ScanStatus)
async def get_scan_status(scan_id: str):
    """
    Obtém status de scan em andamento
    
    Args:
        scan_id: ID do scan
        
    Returns:
        Status atual do scan
    """
    if scan_id not in active_scans:
        raise HTTPException(
            status_code=404,
            detail="Scan não encontrado"
        )
    
    scan_info = active_scans[scan_id]
    
    # Calcular progresso estimado
    if scan_info['status'] == 'running':
        elapsed = time.time() - scan_info['start_time']
        
        # Estimativa baseada no tempo decorrido
        if elapsed < 5:
            progress = min(elapsed * 20, 90)  # 0-90% em 5s
        else:
            progress = 90 + min((elapsed - 5) * 2, 10)  # 90-100% nos próximos 5s
        
        scan_info['progress'] = min(progress, 99.9)
    
    # Estimar tempo restante
    estimated_time = None
    if scan_info['status'] == 'running' and scan_info['progress'] > 0:
        elapsed = time.time() - scan_info['start_time']
        if scan_info['progress'] < 100:
            estimated_time = (elapsed / scan_info['progress']) * (100 - scan_info['progress'])
    
    return ScanStatus(
        scan_id=scan_id,
        status=scan_info['status'],
        progress=scan_info['progress'],
        current_step=scan_info.get('current_step', ''),
        estimated_time=estimated_time,
        results_count=scan_info.get('results_count', 0),
        error=scan_info.get('error')
    )

@router.delete("/scan/{scan_id}")
async def cancel_scan(scan_id: str):
    """
    Cancela scan em andamento
    
    Args:
        scan_id: ID do scan
        
    Returns:
        Confirmação do cancelamento
    """
    if scan_id not in active_scans:
        raise HTTPException(
            status_code=404,
            detail="Scan não encontrado"
        )
    
    scan_info = active_scans[scan_id]
    
    if scan_info['status'] not in ['running', 'pending']:
        raise HTTPException(
            status_code=400,
            detail=f"Scan não pode ser cancelado. Status atual: {scan_info['status']}"
        )
    
    # Marcar como cancelado
    scan_info['status'] = 'cancelled'
    scan_info['current_step'] = 'Cancelado pelo usuário'
    
    logger.info(f"🛑 Scan {scan_id} cancelado")
    
    return {
        "scan_id": scan_id,
        "status": "cancelled",
        "message": "Scan cancelado com sucesso"
    }

@router.get("/scans/active")
async def get_active_scans():
    """
    Obtém lista de scans ativos
    
    Returns:
        Lista de scans em andamento
    """
    active_list = []
    
    for scan_id, scan_info in active_scans.items():
        if scan_info['status'] in ['running', 'pending']:
            active_list.append({
                'scan_id': scan_id,
                'query': scan_info.get('query', ''),
                'status': scan_info['status'],
                'progress': scan_info.get('progress', 0),
                'current_step': scan_info.get('current_step', ''),
                'start_time': scan_info.get('start_time')
            })
    
    return {
        "active_scans": active_list,
        "total_active": len(active_list)
    }

@router.post("/scan/batch")
async def execute_batch_scan(
    queries: List[str],
    background_tasks: BackgroundTasks,
    orchestrator: SystemOrchestrator = Depends(get_orchestrator)
):
    """
    Executa múltiplos scans em lote
    
    Args:
        queries: Lista de queries para buscar
        background_tasks: Tarefas em background
        orchestrator: Orquestrador do sistema
        
    Returns:
        Resultados dos scans
    """
    if not queries or len(queries) == 0:
        raise HTTPException(
            status_code=400,
            detail="Lista de queries não pode ser vazia"
        )
    
    if len(queries) > 50:
        raise HTTPException(
            status_code=400,
            detail="Máximo de 50 queries por lote"
        )
    
    logger.info(f"🔍 Iniciando batch scan: {len(queries)} queries")
    
    batch_id = f"batch_{int(time.time() * 1000)}"
    results = []
    
    # Executar scans em paralelo (com limite)
    semaphore = asyncio.Semaphore(5)  # Máximo 5 scans simultâneos
    
    async def execute_single_scan(query: str):
        async with semaphore:
            try:
                result = await orchestrator.execute_search(query=query)
                return {
                    'query': query,
                    'status': 'success',
                    'result': result
                }
            except Exception as e:
                logger.error(f"❌ Erro no batch scan para '{query}': {str(e)}")
                return {
                    'query': query,
                    'status': 'error',
                    'error': str(e)
                }
    
    # Executar todas as queries
    tasks = [execute_single_scan(query) for query in queries]
    batch_results = await asyncio.gather(*tasks)
    
    # Processar resultados
    success_count = 0
    error_count = 0
    
    for result in batch_results:
        if result['status'] == 'success':
            success_count += 1
            results.append({
                'query': result['query'],
                'status': 'success',
                'results_count': len(result['result'].get('results', [])),
                'processing_time': result['result'].get('processing_time', 0),
                'summary': result['result'].get('summary', '')
            })
        else:
            error_count += 1
            results.append({
                'query': result['query'],
                'status': 'error',
                'error': result.get('error', 'Erro desconhecido')
            })
    
    logger.info(f"✅ Batch scan {batch_id} concluído: {success_count} sucessos, {error_count} erros")
    
    return {
        'batch_id': batch_id,
        'total_queries': len(queries),
        'success_count': success_count,
        'error_count': error_count,
        'results': results
    }

@router.get("/scan/history")
async def get_scan_history(
    limit: int = 50,
    offset: int = 0,
    orchestrator: SystemOrchestrator = Depends(get_orchestrator)
):
    """
    Obtém histórico de scans
    
    Args:
        limit: Número máximo de resultados
        offset: Offset para paginação
        orchestrator: Orquestrador do sistema
        
    Returns:
        Histórico de scans
    """
    try:
        # Obter buscas recentes do storage
        recent_searches = await orchestrator.get_recent_searches(limit=limit)
        
        history = []
        for search in recent_searches:
            history.append({
                'id': search.get('id'),
                'query': search.get('query'),
                'results_count': search.get('results_count', 0),
                'processing_time': search.get('processing_time', 0),
                'created_at': search.get('created_at')
            })
        
        return {
            'history': history,
            'total': len(history),
            'limit': limit,
            'offset': offset
        }
        
    except Exception as e:
        logger.error(f"❌ Erro obtendo histórico: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro obtendo histórico: {str(e)}"
        )

@router.post("/scan/{scan_id}/retry")
async def retry_scan(
    scan_id: str,
    orchestrator: SystemOrchestrator = Depends(get_orchestrator)
):
    """
    Refaz um scan anterior
    
    Args:
        scan_id: ID do scan original
        orchestrator: Orquestrador do sistema
        
    Returns:
        Novo resultado do scan
    """
    # Buscar informações do scan original
    try:
        # Aqui você buscaria do storage
        original_scan = await orchestrator.get_search_by_id(scan_id)
        
        if not original_scan:
            raise HTTPException(
                status_code=404,
                detail="Scan original não encontrado"
            )
        
        # Reexecutar scan
        result = await orchestrator.execute_search(
            query=original_scan['query'],
            max_results=original_scan.get('max_results', 100),
            sources=original_scan.get('sources')
        )
        
        logger.info(f"🔄 Scan {scan_id} reexecutado com sucesso")
        
        return {
            'original_scan_id': scan_id,
            'new_scan_id': f"retry_{int(time.time() * 1000)}",
            'status': 'success',
            'result': result
        }
        
    except Exception as e:
        logger.error(f"❌ Erro retry scan {scan_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro no retry: {str(e)}"
        )

async def cleanup_scan(scan_id: str):
    """
    Limpa informações de scan após algum tempo
    
    Args:
        scan_id: ID do scan
    """
    await asyncio.sleep(300)  # 5 minutos
    
    if scan_id in active_scans:
        del active_scans[scan_id]
        logger.debug(f"🧹 Scan {scan_id} limpo da memória")

# Middleware para logging
@router.middleware("http")
async def log_requests(request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    
    logger.info(
        f"📊 {request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    
    return response
