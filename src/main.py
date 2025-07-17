from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import uvicorn

from src.api.routers import router as api_router
from src.core.config import settings
from src.core.logging import setup_logging, get_logger
from src.middleware.rate_limiting import RateLimitMiddleware, TokenUsageMiddleware
from src.services.database import init_db
from src.services.checkpointer import checkpointer_service
from src.agents.support_graph import create_support_graph
import src.agents.support_graph as graph_module
import uuid 

# Configurar logging
setup_logging(debug=settings.DEBUG)
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación"""
    logger.info("app_startup_initiated")
    
    try:
        # Inicializar base de datos
        await init_db()
        logger.info("database_ready")
        
        # Inicializar checkpointer
        await checkpointer_service.initialize()
        logger.info("checkpointer_ready")
        
        # Crear grafo del agente
        graph_module.support_agent_graph = create_support_graph()
        logger.info("agent_graph_ready")
        
        logger.info("app_startup_complete")
        
    except Exception as e:
        logger.error("startup_failed", error=str(e))
        raise
    
    yield
    
    # Cleanup
    logger.info("app_shutdown_initiated")
    await checkpointer_service.close()
    logger.info("app_shutdown_complete")

# Crear aplicación FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configurar según necesidades
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(TokenUsageMiddleware)

# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())

    # Crea un nuevo logger con el request_id atado
    log = logger.bind(request_id=request_id)

    # Usa la nueva variable 'log' para todos los mensajes
    log.info("request_started", 
           method=request.method, 
           path=request.url.path)

    response = await call_next(request)

    log.info("request_completed", 
           status_code=response.status_code)

    response.headers["X-Request-ID"] = request_id
    return response

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Incluir routers
app.include_router(api_router)

# Rutas frontend
@app.get("/")
async def home(request: Request):
    """Página principal"""
    return templates.TemplateResponse(
        "chatbot_fullscreen.html", 
        {"request": request, "app_name": settings.APP_NAME}
    )

@app.get("/admin")
async def admin(request: Request):
    """Panel de administración"""
    return templates.TemplateResponse(
        "admin.html", 
        {"request": request}
    )

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.DEBUG,
        log_config=None  # Usamos nuestro propio logging
    )