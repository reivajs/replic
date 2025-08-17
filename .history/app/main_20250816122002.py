"""
Application Main Module - WITH DASHBOARD
=========================================
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.VERSION}")
    
    # Initialize services
    try:
        from app.services.registry import service_registry
        await service_registry.initialize()
        await service_registry.start_services()
        logger.info("✅ Services initialized")
    except Exception as e:
        logger.error(f"⚠️ Service initialization error: {e}")
    
    yield
    
    # Shutdown
    try:
        from app.services.registry import service_registry
        await service_registry.stop_services()
        await service_registry.cleanup()
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
            "docs": "/docs"
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
    
    # Include routers
    try:
        from app.api.v1 import health, discovery, groups, config, websocket, dashboard as dashboard_api
        
        app.include_router(health.router, prefix="/api/v1", tags=["health"])
        app.include_router(discovery.router, prefix="/api/v1/discovery", tags=["discovery"])
        app.include_router(groups.router, prefix="/api/v1/groups", tags=["groups"])
        app.include_router(config.router, prefix="/api/v1/config", tags=["config"])
        app.include_router(websocket.router, prefix="/ws", tags=["websocket"])
        app.include_router(dashboard_api.router, prefix="/api/v1/dashboard", tags=["dashboard"])
        
        logger.info("✅ All API routes registered including dashboard")
    except Exception as e:
        logger.warning(f"Could not register all routes: {e}")
    
    return app

# Create application instance
app = create_app()
