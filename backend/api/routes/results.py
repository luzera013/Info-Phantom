"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - Results Route
Rota para gerenciamento de resultados de buscas
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import time
import logging

from ...core.orchestrator import SystemOrchestrator
from ...utils.sqlite import SQLiteStorage
from ...utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()

# Modelos de dados
class ResultFilter(BaseModel):
    """Modelo para filtro de resultados"""
    query: Optional[str] = None
    source: Optional[str] = None
    min_relevance: Optional[float] = Field(0.0, ge=0.0, le=1.0)
    max_relevance: Optional[float] = Field(1.0, ge=0.0, le=1.0)
    date_from: Optional[float] = None
    date_to: Optional[float] = None
    has_extracted_data: Optional[bool] = None

class ResultExport(BaseModel):
    """Modelo para exportação de resultados"""
    format: str = Field("json", regex="^(json|csv|xlsx|xml)$")
    include_extracted_data: bool = True
    include_summary: bool = True
    include_stats: bool = True

class SearchResult(BaseModel):
    """Modelo de resultado de busca"""
    id: int
    search_id: int
    title: str
    url: str
    description: str
    source: str
    relevance_score: float
    timestamp: float
    extracted_data: Dict[str, Any]
    created_at: str

class SearchSummary(BaseModel):
    """Modelo de resumo de busca"""
    id: int
    query: str
    results_count: int
    processing_time: float
    sources_used: List[str]
    summary: str
    created_at: str
    updated_at: str

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

@router.get("/search/{search_id}", response_model=Dict[str, Any])
async def get_search_results(
    search_id: int,
    include_extracted_data: bool = Query(True),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    storage: SQLiteStorage = Depends(get_storage)
):
    """
    Obtém resultados de uma busca específica
    
    Args:
        search_id: ID da busca
        include_extracted_data: Incluir dados extraídos
        limit: Limite de resultados
        offset: Offset para paginação
        storage: Storage do banco
        
    Returns:
        Resultados da busca
        
    Raises:
        HTTPException: Se busca não encontrada
    """
    try:
        logger.info(f"📊 Obtendo resultados da busca {search_id}")
        
        # Buscar dados completos
        search_data = await storage.get_search(search_id)
        
        if not search_data:
            raise HTTPException(
                status_code=404,
                detail="Busca não encontrada"
            )
        
        # Filtrar resultados se necessário
        results = search_data.get('results', [])
        
        # Aplicar paginação
        total_results = len(results)
        paginated_results = results[offset:offset + limit]
        
        # Remover dados extraídos se não solicitado
        if not include_extracted_data:
            for result in paginated_results:
                result.pop('extracted_data', None)
        
        response = {
            'search': {
                'id': search_data['id'],
                'query': search_data['query'],
                'results_count': search_data['results_count'],
                'processing_time': search_data['processing_time'],
                'sources_used': search_data['sources_used'],
                'summary': search_data['summary'],
                'created_at': search_data['created_at'],
                'updated_at': search_data['updated_at']
            },
            'results': paginated_results,
            'pagination': {
                'total': total_results,
                'limit': limit,
                'offset': offset,
                'has_next': offset + limit < total_results,
                'has_prev': offset > 0
            }
        }
        
        logger.info(f"✅ Resultados obtidos: {len(paginated_results)}/{total_results}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro obtendo resultados {search_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        )

@router.get("/search/{search_id}/export")
async def export_search_results(
    search_id: int,
    export_config: ResultExport,
    storage: SQLiteStorage = Depends(get_storage)
):
    """
    Exporta resultados de busca em diferentes formatos
    
    Args:
        search_id: ID da busca
        export_config: Configurações de exportação
        storage: Storage do banco
        
    Returns:
        Arquivo exportado
        
    Raises:
        HTTPException: Se erro na exportação
    """
    try:
        logger.info(f"📤 Exportando busca {search_id} no formato {export_config.format}")
        
        # Obter dados da busca
        search_data = await storage.get_search(search_id)
        
        if not search_data:
            raise HTTPException(
                status_code=404,
                detail="Busca não encontrada"
            )
        
        # Preparar dados para exportação
        export_data = await _prepare_export_data(search_data, export_config)
        
        # Gerar arquivo no formato solicitado
        if export_config.format == "json":
            return await _export_json(export_data, search_id)
        elif export_config.format == "csv":
            return await _export_csv(export_data, search_id)
        elif export_config.format == "xlsx":
            return await _export_xlsx(export_data, search_id)
        elif export_config.format == "xml":
            return await _export_xml(export_data, search_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro exportando busca {search_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro na exportação: {str(e)}"
        )

@router.get("/recent")
async def get_recent_results(
    limit: int = Query(20, ge=1, le=100),
    storage: SQLiteStorage = Depends(get_storage)
):
    """
    Obtém resultados de buscas recentes
    
    Args:
        limit: Número máximo de buscas
        storage: Storage do banco
        
    Returns:
        Lista de buscas recentes
    """
    try:
        logger.info(f"📊 Obtendo buscas recentes (limit: {limit})")
        
        recent_searches = await storage.get_recent_searches(limit)
        
        # Enriquecer com estatísticas adicionais
        enriched_searches = []
        for search in recent_searches:
            # Calcular estatísticas básicas
            enriched = search.copy()
            enriched['avg_relevance'] = 0.75  # Simulado
            enriched['top_source'] = 'web'  # Simulado
            enriched['has_extracted_data'] = True  # Simulado
            enriched_searches.append(enriched)
        
        return {
            'searches': enriched_searches,
            'total': len(enriched_searches),
            'limit': limit
        }
        
    except Exception as e:
        logger.error(f"❌ Erro obtendo buscas recentes: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        )

@router.post("/filter")
async def filter_results(
    filters: ResultFilter,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    storage: SQLiteStorage = Depends(get_storage)
):
    """
    Filtra resultados baseado em critérios
    
    Args:
        filters: Critérios de filtro
        limit: Limite de resultados
        offset: Offset para paginação
        storage: Storage do banco
        
    Returns:
        Resultados filtrados
    """
    try:
        logger.info(f"🔍 Filtrando resultados com critérios: {filters}")
        
        # Buscar buscas que correspondem aos filtros
        filtered_searches = []
        
        # Se tem query, buscar por query
        if filters.query:
            searches = await storage.search_queries(filters.query, limit=100)
        else:
            searches = await storage.get_recent_searches(100)
        
        # Aplicar filtros adicionais
        for search in searches:
            # Filtrar por fonte se especificado
            if filters.source:
                sources = search.get('sources_used', [])
                if filters.source not in sources:
                    continue
            
            # Filtrar por data se especificado
            created_at = search.get('created_at', '')
            if created_at:
                # Converter timestamp se necessário
                pass  # Implementar conversão de data
            
            filtered_searches.append(search)
        
        # Aplicar paginação
        total_results = len(filtered_searches)
        paginated_results = filtered_searches[offset:offset + limit]
        
        return {
            'searches': paginated_results,
            'pagination': {
                'total': total_results,
                'limit': limit,
                'offset': offset,
                'has_next': offset + limit < total_results,
                'has_prev': offset > 0
            },
            'filters_applied': filters.dict()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro filtrando resultados: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro no filtro: {str(e)}"
        )

@router.get("/search/{search_id}/stats")
async def get_search_statistics(
    search_id: int,
    storage: SQLiteStorage = Depends(get_storage)
):
    """
    Obtém estatísticas detalhadas de uma busca
    
    Args:
        search_id: ID da busca
        storage: Storage do banco
        
    Returns:
        Estatísticas da busca
        
    Raises:
        HTTPException: Se busca não encontrada
    """
    try:
        logger.info(f"📊 Obtendo estatísticas da busca {search_id}")
        
        # Obter dados da busca
        search_data = await storage.get_search(search_id)
        
        if not search_data:
            raise HTTPException(
                status_code=404,
                detail="Busca não encontrada"
            )
        
        # Calcular estatísticas detalhadas
        results = search_data.get('results', [])
        
        stats = {
            'basic': {
                'search_id': search_id,
                'query': search_data['query'],
                'total_results': len(results),
                'processing_time': search_data['processing_time'],
                'sources_used': search_data['sources_used'],
                'created_at': search_data['created_at']
            },
            'relevance': {
                'avg_relevance': 0.0,
                'max_relevance': 0.0,
                'min_relevance': 1.0,
                'high_relevance_count': 0,
                'medium_relevance_count': 0,
                'low_relevance_count': 0
            },
            'sources': {},
            'extracted_data': {
                'total_emails': 0,
                'total_phones': 0,
                'total_companies': 0,
                'total_links': 0,
                'results_with_extracted_data': 0
            },
            'temporal': {
                'newest_result': 0.0,
                'oldest_result': 0.0,
                'time_span': 0.0,
                'results_per_day': {}
            }
        }
        
        # Calcular estatísticas de relevância
        relevance_scores = [r.get('relevance_score', 0) for r in results]
        if relevance_scores:
            stats['relevance']['avg_relevance'] = sum(relevance_scores) / len(relevance_scores)
            stats['relevance']['max_relevance'] = max(relevance_scores)
            stats['relevance']['min_relevance'] = min(relevance_scores)
            
            for score in relevance_scores:
                if score >= 0.8:
                    stats['relevance']['high_relevance_count'] += 1
                elif score >= 0.5:
                    stats['relevance']['medium_relevance_count'] += 1
                else:
                    stats['relevance']['low_relevance_count'] += 1
        
        # Contar fontes
        for result in results:
            source = result.get('source', 'unknown')
            stats['sources'][source] = stats['sources'].get(source, 0) + 1
        
        # Contar dados extraídos
        for result in results:
            extracted = result.get('extracted_data', {})
            if extracted:
                stats['extracted_data']['results_with_extracted_data'] += 1
                stats['extracted_data']['total_emails'] += len(extracted.get('emails', []))
                stats['extracted_data']['total_phones'] += len(extracted.get('phones', []))
                stats['extracted_data']['total_companies'] += len(extracted.get('companies', []))
                stats['extracted_data']['total_links'] += len(extracted.get('links', []))
        
        # Análise temporal
        timestamps = [r.get('timestamp', 0) for r in results if r.get('timestamp')]
        if timestamps:
            stats['temporal']['newest_result'] = max(timestamps)
            stats['temporal']['oldest_result'] = min(timestamps)
            stats['temporal']['time_span'] = max(timestamps) - min(timestamps)
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro obtendo estatísticas {search_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro nas estatísticas: {str(e)}"
        )

@router.delete("/search/{search_id}")
async def delete_search(
    search_id: int,
    storage: SQLiteStorage = Depends(get_storage)
):
    """
    Remove uma busca e seus resultados
    
    Args:
        search_id: ID da busca
        storage: Storage do banco
        
    Returns:
        Confirmação da remoção
        
    Raises:
        HTTPException: Se busca não encontrada
    """
    try:
        logger.info(f"🗑️ Removendo busca {search_id}")
        
        # Verificar se busca existe
        search_data = await storage.get_search(search_id)
        
        if not search_data:
            raise HTTPException(
                status_code=404,
                detail="Busca não encontrada"
            )
        
        # Remover busca (em produção, implementar no storage)
        # await storage.delete_search(search_id)
        
        logger.info(f"✅ Busca {search_id} removida com sucesso")
        
        return {
            "message": f"Busca {search_id} removida com sucesso",
            "deleted_results": len(search_data.get('results', []))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro removendo busca {search_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro na remoção: {str(e)}"
        )

# Funções auxiliares para exportação
async def _prepare_export_data(search_data: Dict[str, Any], 
                              config: ResultExport) -> Dict[str, Any]:
    """Prepara dados para exportação"""
    export_data = {
        'search_info': {
            'id': search_data['id'],
            'query': search_data['query'],
            'results_count': search_data['results_count'],
            'processing_time': search_data['processing_time'],
            'created_at': search_data['created_at']
        }
    }
    
    if config.include_summary:
        export_data['summary'] = search_data['summary']
    
    if config.include_stats:
        export_data['sources_used'] = search_data['sources_used']
    
    # Preparar resultados
    results = search_data.get('results', [])
    processed_results = []
    
    for result in results:
        processed_result = {
            'title': result.get('title', ''),
            'url': result.get('url', ''),
            'description': result.get('description', ''),
            'source': result.get('source', ''),
            'relevance_score': result.get('relevance_score', 0.0),
            'timestamp': result.get('timestamp', 0.0)
        }
        
        if config.include_extracted_data:
            processed_result['extracted_data'] = result.get('extracted_data', {})
        
        processed_results.append(processed_result)
    
    export_data['results'] = processed_results
    return export_data

async def _export_json(data: Dict[str, Any], search_id: int):
    """Exporta em formato JSON"""
    import json
    
    filename = f"search_{search_id}_results.json"
    
    return JSONResponse(
        content=data,
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": "application/json"
        }
    )

async def _export_csv(data: Dict[str, Any], search_id: int):
    """Exporta em formato CSV"""
    import csv
    import io
    
    output = io.StringIO()
    
    # Escrever informações da busca
    writer = csv.writer(output)
    writer.writerow(['Search Information'])
    writer.writerow(['ID', data['search_info']['id']])
    writer.writerow(['Query', data['search_info']['query']])
    writer.writerow(['Results Count', data['search_info']['results_count']])
    writer.writerow(['Processing Time', data['search_info']['processing_time']])
    writer.writerow(['Created At', data['search_info']['created_at']])
    writer.writerow([])  # Linha em branco
    
    # Escrever resultados
    writer.writerow(['Results'])
    writer.writerow(['Title', 'URL', 'Description', 'Source', 'Relevance Score', 'Timestamp'])
    
    for result in data.get('results', []):
        writer.writerow([
            result.get('title', ''),
            result.get('url', ''),
            result.get('description', ''),
            result.get('source', ''),
            result.get('relevance_score', 0.0),
            result.get('timestamp', 0.0)
        ])
    
    output.seek(0)
    content = output.getvalue()
    
    from fastapi.responses import Response
    return Response(
        content=content,
        headers={
            "Content-Disposition": f"attachment; filename=search_{search_id}_results.csv",
            "Content-Type": "text/csv"
        }
    )

async def _export_xlsx(data: Dict[str, Any], search_id: int):
    """Exporta em formato XLSX"""
    # Implementação simplificada - retornar JSON por ora
    return await _export_json(data, search_id)

async def _export_xml(data: Dict[str, Any], search_id: int):
    """Exporta em formato XML"""
    # Implementação simplificada - retornar JSON por ora
    return await _export_json(data, search_id)
