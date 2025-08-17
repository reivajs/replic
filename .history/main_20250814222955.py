#!/usr/bin/env python3
"""
🎭 ENTERPRISE MICROSERVICES ORCHESTRATOR v6.0 - MODULAR ARCHITECTURE
====================================================================
Arquitectura modular, escalable y lista para SaaS production
"""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

# Core modules - Arquitectura modular
from app.core.config import settings, Environment
from app.core.logging import get_logger, setup_logging
from app.core.exceptions import setup_exception_handlers
from app.core.middleware import setup_middleware
from app.core.dependencies import get_service_registry, get_cache

# Routers modulares
from app.api.v1 import (
    health_router,
    discovery_router,
    groups_router,
    config_router,
    websocket_router
)
from app.api.v2 import api_v2_router  # Versionado de API

# Services
from app.services import ServiceRegistry, ServiceDiscovery
from app.services.cache import CacheService
from app.services.metrics import MetricsCollector

# Database
from app.database import init_database, get_db_session

# Background tasks
from app.tasks import BackgroundTaskManager

# Initialize
logger = get_logger(__name__)
setup_logging()

# ============= APPLICATION FACTORY PATTERN =============
def create_application() -> FastAPI:
    """
    Factory pattern para crear la aplicación
    Permite testing y múltiples instancias
    """
    
    # Configuración según environment
    if settings.ENVIRONMENT == Environment.PRODUCTION:
        app_config = {
            "title": settings.APP_NAME,
            "version": settings.VERSION,
            "docs_url": None,  # Disable docs in production
            "redoc_url": None,
            "openapi_url": None
        }
    else:
        app_config = {
            "title": f"{settings.APP_NAME} - {settings.ENVIRONMENT.value}",
            "version": settings.VERSION,
            "description": settings.DESCRIPTION,
            "docs_url": "/docs",
            "redoc_url": "/redoc"
        }
    
    app = FastAPI(**app_config, lifespan=lifespan)
    
    # Setup components
    setup_middleware(app)
    setup_exception_handlers(app)
    setup_routes(app)
    setup_static_files(app)
    
    return app

# ============= LIFESPAN MANAGER =============
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestión del ciclo de vida con cleanup automático
    """
    try:
        # Startup
        logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.VERSION}")
        logger.info(f"📍 Environment: {settings.ENVIRONMENT.value}")
        
        # Initialize components
        await startup_sequence(app)
        
        # Service discovery
        if settings.ENABLE_SERVICE_DISCOVERY:
            await discover_services(app)
        
        # Print startup info
        print_startup_banner()
        
        yield
        
    finally:
        # Shutdown
        await shutdown_sequence(app)
        logger.info(f"🛑 {settings.APP_NAME} stopped gracefully")

# ============= STARTUP SEQUENCE =============
async def startup_sequence(app: FastAPI):
    """
    Secuencia de inicio modular y ordenada
    """
    startup_tasks = [
        ("Database", init_database),
        ("Cache", init_cache),
        ("Service Registry", init_service_registry),
        ("Background Tasks", init_background_tasks),
        ("Metrics Collector", init_metrics),
        ("WebSocket Manager", init_websocket_manager)
    ]
    
    for name, task in startup_tasks:
        try:
            logger.info(f"Initializing {name}...")
            await task(app)
            logger.info(f"✅ {name} initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize {name}: {e}")
            if settings.FAIL_FAST:
                raise

# ============= SERVICE DISCOVERY =============
async def discover_services(app: FastAPI):
    """
    Auto-discovery de servicios con health checks
    """
    discovery = ServiceDiscovery(
        consul_host=settings.CONSUL_HOST,
        consul_port=settings.CONSUL_PORT
    )
    
    # Discover available services
    services = await discovery.discover_all()
    
    # Register in app state
    app.state.discovered_services = services
    
    # Health check all services
    healthy_count = 0
    for service in services:
        if await discovery.health_check(service):
            healthy_count += 1
    
    logger.info(f"📊 Discovered {len(services)} services ({healthy_count} healthy)")

# ============= SHUTDOWN SEQUENCE =============
async def shutdown_sequence(app: FastAPI):
    """
    Shutdown ordenado con cleanup
    """
    shutdown_tasks = [
        ("WebSocket connections", close_websockets),
        ("Background tasks", stop_background_tasks),
        ("Cache connections", close_cache),
        ("Database connections", close_database),
        ("Service registry", cleanup_registry)
    ]
    
    for name, task in shutdown_tasks:
        try:
            logger.info(f"Shutting down {name}...")
            await task(app)
        except Exception as e:
            logger.error(f"Error shutting down {name}: {e}")

# ============= ROUTES SETUP =============
def setup_routes(app: FastAPI):
    """
    Configuración modular de rutas con versionado
    """
    # API v1 - Current stable
    app.include_router(
        health_router,
        prefix="/api/v1",
        tags=["health"]
    )
    
    app.include_router(
        discovery_router,
        prefix="/api/v1/discovery",
        tags=["discovery"]
    )
    
    app.include_router(
        groups_router,
        prefix="/api/v1/groups",
        tags=["groups"]
    )
    
    app.include_router(
        config_router,
        prefix="/api/v1/config",
        tags=["configuration"]
    )
    
    app.include_router(
        websocket_router,
        prefix="/ws",
        tags=["websocket"]
    )
    
    # API v2 - Beta features
    if settings.ENABLE_BETA_FEATURES:
        app.include_router(
            api_v2_router,
            prefix="/api/v2",
            tags=["v2-beta"]
        )
    
    # UI Routes
    setup_ui_routes(app)

# ============= UI ROUTES =============
def setup_ui_routes(app: FastAPI):
    """
    UI routes separadas de la API
    """
    from app.ui import dashboard, discovery_ui, groups_hub
    
    app.add_route("/", dashboard.index, methods=["GET"])
    app.add_route("/dashboard", dashboard.main, methods=["GET"])
    app.add_route("/discovery", discovery_ui.main, methods=["GET"])
    app.add_route("/groups", groups_hub.main, methods=["GET"])

# ============= STATIC FILES =============
def setup_static_files(app: FastAPI):
    """
    Configuración de archivos estáticos con CDN fallback
    """
    static_path = Path("frontend/static")
    if static_path.exists():
        app.mount(
            "/static",
            StaticFiles(directory=str(static_path)),
            name="static"
        )
    
    # Templates
    templates_path = Path("frontend/templates")
    if templates_path.exists():
        app.state.templates = Jinja2Templates(directory=str(templates_path))

# ============= HELPER FUNCTIONS =============
async def init_cache(app: FastAPI):
    """Initialize cache service"""
    app.state.cache = CacheService(
        redis_url=settings.REDIS_URL,
        ttl=settings.CACHE_TTL
    )
    await app.state.cache.connect()

async def init_service_registry(app: FastAPI):
    """Initialize service registry"""
    app.state.registry = ServiceRegistry(
        config_path=settings.SERVICES_CONFIG
    )
    await app.state.registry.initialize()

async def init_background_tasks(app: FastAPI):
    """Initialize background task manager"""
    app.state.tasks = BackgroundTaskManager(
        max_workers=settings.MAX_WORKERS
    )
    await app.state.tasks.start()

async def init_metrics(app: FastAPI):
    """Initialize metrics collector"""
    app.state.metrics = MetricsCollector(
        prometheus_enabled=settings.PROMETHEUS_ENABLED
    )
    await app.state.metrics.start()

async def init_websocket_manager(app: FastAPI):
    """Initialize WebSocket manager"""
    from app.websocket import WebSocketManager
    app.state.ws_manager = WebSocketManager()

async def close_websockets(app: FastAPI):
    """Close all WebSocket connections"""
    if hasattr(app.state, 'ws_manager'):
        await app.state.ws_manager.disconnect_all()

async def stop_background_tasks(app: FastAPI):
    """Stop background tasks"""
    if hasattr(app.state, 'tasks'):
        await app.state.tasks.stop()

async def close_cache(app: FastAPI):
    """Close cache connections"""
    if hasattr(app.state, 'cache'):
        await app.state.cache.disconnect()

async def close_database(app: FastAPI):
    """Close database connections"""
    from app.database import close_db_connections
    await close_db_connections()

async def cleanup_registry(app: FastAPI):
    """Cleanup service registry"""
    if hasattr(app.state, 'registry'):
        await app.state.registry.cleanup()

def print_startup_banner():
    """
    Pretty startup banner
    """
    banner = f"""
    {'='*70}
    🎭 {settings.APP_NAME} v{settings.VERSION}
    {'='*70}
    🌐 Main endpoints:
       📊 Dashboard:     {settings.BASE_URL}/dashboard
       🔍 Discovery:     {settings.BASE_URL}/discovery
       🎭 Groups Hub:    {settings.BASE_URL}/groups
       🏥 Health:        {settings.BASE_URL}/api/v1/health
       📚 API Docs:      {settings.BASE_URL}/docs
    
    🔧 Configuration:
       Environment:     {settings.ENVIRONMENT.value}
       Debug Mode:      {settings.DEBUG}
       Workers:         {settings.WORKERS}
       Port:            {settings.PORT}
    {'='*70}
    """
    print(banner)

# ============= APPLICATION INSTANCE =============
app = create_application()

# ============= MAIN ENTRY POINT =============
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        workers=settings.WORKERS,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=settings.ACCESS_LOG,
        use_colors=True
    )