"""
Application Main Module - MICROSERVICES PURE ARCHITECTURE
=========================================================
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import logging
from datetime import datetime
from pathlib import Path

from app.core.config import settings
from app.core.logging import setup_logging

logger = logging.getLogger(__name__)

# Templates
templates_dir = Path("frontend/templates")
if templates_dir.exists():
    templates = Jinja2Templates(directory=str(templates_dir))
else:
    templates = None

# 🎯 MICROSERVICES INSTANCES - DIRECT INJECTION
replicator_service = None
watermark_service = None
discord_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - MICROSERVICES PURE"""
    global replicator_service, watermark_service, discord_service
    
    # Startup
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.VERSION}")
    
    # Initialize microservices directly
    try:
        from app.services.enhanced_replicator_service import EnhancedReplicatorService
        from app.services.watermark_service import WatermarkServiceIntegrated
        from app.services.discord_sender import DiscordSenderEnhanced
        
        # Direct instantiation - NO ADAPTERS
        replicator_service = EnhancedReplicatorService()
        watermark_service = WatermarkServiceIntegrated()
        discord_service = DiscordSenderEnhanced()
        
        # Initialize each service
        await replicator_service.initialize()
        await watermark_service.initialize()
        await discord_service.initialize()
        
        # Start replicator listening
        import asyncio
        asyncio.create_task(replicator_service.start_listening())
        
        logger.info("✅ Microservices initialized - PURE ARCHITECTURE")
    except Exception as e:
        logger.error(f"⚠️ Service initialization error: {e}")
    
    yield
    
    # Shutdown
    try:
        if replicator_service:
            await replicator_service.stop()
        if discord_service:
            await discord_service.close()
        logger.info("✅ Microservices stopped cleanly")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
    
    logger.info("👋 Application shutdown complete")

def create_app() -> FastAPI:
    """Create FastAPI application"""
    
    # Setup logging
    setup_logging(settings.LOG_LEVEL)
    
    # Create app
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Mount static files if they exist
    static_dir = Path("frontend/static")
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    
    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "name": settings.APP_NAME,
            "version": settings.VERSION,
            "status": "running",
            "dashboard": "/dashboard",
            "docs": "/docs",
            "architecture": "microservices_pure"
        }
    
    # Dashboard endpoint
    @app.get("/dashboard", response_class=HTMLResponse)
    async def dashboard(request: Request):
        if templates:
            return templates.TemplateResponse("dashboard.html", {"request": request})
        else:
            return HTMLResponse("""
            <h1>Dashboard Template Not Found</h1>
            <p>Please create frontend/templates/dashboard.html</p>
            <p><a href="/docs">Go to API Docs</a></p>
            """)
    
    # Health endpoint direct
    @app.get("/api/v1/health")
    async def health_check():
        """Direct health check - NO ADAPTER"""
        try:
            health_data = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "services": {}
            }
            
            if replicator_service:
                health_data["services"]["replicator"] = await replicator_service.get_health()
            if watermark_service:
                health_data["services"]["watermark"] = watermark_service.get_stats()
            if discord_service:
                health_data["services"]["discord"] = await discord_service.get_health() if hasattr(discord_service, 'get_health') else {"status": "running"}
            
            return health_data
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    # Include routers
    try:
        from app.api.v1 import discovery, groups, config, websocket, dashboard as dashboard_api
        
        app.include_router(discovery.router, prefix="/api/v1/discovery", tags=["discovery"])
        app.include_router(groups.router, prefix="/api/v1/groups", tags=["groups"])
        app.include_router(config.router, prefix="/api/v1/config", tags=["config"])
        app.include_router(websocket.router, prefix="/ws", tags=["websocket"])
        app.include_router(dashboard_api.router, prefix="/api/v1/dashboard", tags=["dashboard"])
        
        logger.info("✅ All API routes registered - MICROSERVICES PURE")
    except Exception as e:
        logger.warning(f"Could not register all routes: {e}")
    
    return app

# Create application instance
app = create_app()

# Export services for other modules
def get_replicator_service():
    return replicator_service

def get_watermark_service():
    return watermark_service

def get_discord_service():
    return discord_service

