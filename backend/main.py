"""
OMNISCIENT_ULTIMATE_SYSTEM_FINAL - Backend Main
Ponto inicial da API FastAPI
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import asyncio
from contextlib import asynccontextmanager

from api.routes.scan import router as scan_router
from api.routes.auth import router as auth_router
from api.routes.results import router as results_router
from api.routes.health import router as health_router
from core.orchestrator import SystemOrchestrator
from utils.logger import setup_logger
from utils.metrics import MetricsCollector

logger = setup_logger(__name__)
metrics = MetricsCollector()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia ciclo de vida da aplicação"""
    logger.info("🚀 Iniciando OMNISCIENT_ULTIMATE_SYSTEM_FINAL")
    
    # Inicializa orquestrador
    orchestrator = SystemOrchestrator()
    await orchestrator.initialize()
    
    # Armazena no estado da app
    app.state.orchestrator = orchestrator
    
    logger.info("✅ Sistema inicializado com sucesso")
    yield
    
    # Cleanup
    logger.info("🔄 Desligando sistema...")
    await orchestrator.shutdown()

# Criar app FastAPI
app = FastAPI(
    title="OMNISCIENT_ULTIMATE_SYSTEM_FINAL",
    description="Sistema avançado de coleta e análise de informações em larga escala",
    version="3.0.0",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínios
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Registrar rotas
app.include_router(scan_router, prefix="/api/v1", tags=["scan"])
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(results_router, prefix="/api/v1", tags=["results"])
app.include_router(health_router, prefix="/api/v1", tags=["health"])

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handler global de exceções"""
    logger.error(f"Erro não tratado: {str(exc)}")
    metrics.increment_error_count()
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Erro interno do servidor",
            "details": str(exc) if app.debug else "Contacte o administrador"
        }
    )

@app.get("/")
async def root():
    """Endpoint raiz"""
    return {
        "system": "OMNISCIENT_ULTIMATE_SYSTEM_FINAL",
        "status": "online",
        "version": "3.0.0",
        "endpoints": {
            "scan": "/api/v1/scan",
            "auth": "/api/v1/auth",
            "results": "/api/v1/results",
            "health": "/api/v1/health"
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
