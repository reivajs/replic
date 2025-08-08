#!/usr/bin/env python3
import sys
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import asyncio
import json
from datetime import datetime
from contextlib import asynccontextmanager

# Agregar path para imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))
sys.path.append(str(Path(__file__).parent / "services"))

# ✅ IMPORTS NECESARIOS PARA EL DASHBOARD
from app.config.settings import get_settings
from app.models.database import get_db, init_database
from app.services.enhanced_replicator_service import EnhancedReplicatorService
from app.api.routes import router as api_router
from app.api.dashboard import router as dashboard_router  # ← NUEVA LÍNEA
from app.api.websocket import WebSocketManager
from app.utils.logger import setup_logger

# Configuración global
settings = get_settings()
logger = setup_logger(__name__)

# WebSocket manager
websocket_manager = WebSocketManager()

# Servicio del replicador
replicator_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manejo del ciclo de vida de la aplicación"""
    global replicator_service
    
    logger.info("🚀 Iniciando Telegram-Discord Replicator...")
    
    try:
        # Inicializar base de datos
        logger.info("🔧 Inicializando base de datos...")
        await init_database()
        
        # Inicializar servicio del replicador
        logger.info("🔧 Inicializando servicio de replicación...")
        replicator_service = EnhancedReplicatorService()
        await replicator_service.initialize()
        
        # Iniciar escucha en background
        asyncio.create_task(replicator_service.start_listening())
        
        logger.info("✅ Sistema iniciado correctamente")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Error durante inicio: {e}")
        raise
    finally:
        # Cleanup
        logger.info("🛑 Deteniendo servicios...")
        if replicator_service:
            await replicator_service.stop()
        logger.info("👋 Sistema detenido")

# Crear aplicación FastAPI
app = FastAPI(
    title="Telegram-Discord Replicator Enterprise",
    description="Sistema enterprise de replicación con dashboard moderno",
    version="3.0.0",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar archivos estáticos y templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ✅ INCLUIR ROUTERS (AGREGAR LA LÍNEA DEL DASHBOARD)
app.include_router(api_router, prefix="/api", tags=["API"])
app.include_router(dashboard_router, tags=["Dashboard"])  # ← NUEVA LÍNEA

# ==================== RUTAS PRINCIPALES ====================

@app.get("/")
async def root():
    """Ruta raíz - redirige al dashboard"""
    return {"message": "Telegram-Discord Replicator API", "version": "2.0.0"}

@app.get("/health")
async def health_check():
    """Health check del sistema"""
    try:
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0",
            "services": {}
        }
        
        # Verificar estado del replicador
        if replicator_service:
            health_data["services"]["replicator"] = await replicator_service.get_health()
        else:
            health_data["services"]["replicator"] = {"status": "not_initialized"}
        
        # Verificar WebSocket
        health_data["services"]["websocket"] = {
            "status": "running",
            "connected_clients": websocket_manager.get_client_count()
        }
        
        return health_data
        
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "unhealthy", "error": str(e)}
        )

# ==================== RUTAS WEB ====================

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Dashboard principal"""
    try:
        stats = {}
        if replicator_service:
            stats = await replicator_service.get_dashboard_stats()
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "stats": stats
        })
    except Exception as e:
        logger.error(f"Error en dashboard: {e}")
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "stats": {},
            "error": str(e)
        })

@app.get("/routes", response_class=HTMLResponse)
async def routes_page(request: Request):
    """Página de gestión de rutas"""
    if templates:
        return templates.TemplateResponse("routes.html", {"request": request})
    else:
        return HTMLResponse("<h1>Routes Page</h1><p>Templates not available</p>")

@app.get("/accounts", response_class=HTMLResponse)
async def accounts_page(request: Request):
    """Página de gestión de cuentas"""
    if templates:
        return templates.TemplateResponse("accounts.html", {"request": request})
    else:
        return HTMLResponse("<h1>Accounts Page</h1><p>Templates not available</p>")

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Página de configuración"""
    if templates:
        return templates.TemplateResponse("settings.html", {"request": request})
    else:
        return HTMLResponse("<h1>Settings Page</h1><p>Templates not available</p>")

# ==================== WEBSOCKET ====================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket para actualizaciones en tiempo real (TU CÓDIGO ACTUAL)"""
    await websocket_manager.connect(websocket)
    
    try:
        # Enviar mensaje de bienvenida
        await websocket_manager.send_personal_message({
            "type": "welcome",
            "message": "Conectado al sistema Enterprise",
            "timestamp": datetime.now().isoformat(),
            "system_status": await get_system_status() if replicator_service else {}
        }, websocket)
        
        # Loop de mantenimiento de conexión
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                
                # Procesar mensajes del cliente
                if data.strip().lower() == "ping":
                    await websocket_manager.send_personal_message({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }, websocket)
                elif data.strip().lower() == "stats":
                    # Enviar estadísticas actuales
                    if replicator_service:
                        stats = await replicator_service.get_dashboard_stats()
                        await websocket_manager.send_personal_message({
                            "type": "stats_update",
                            "data": stats,
                            "timestamp": datetime.now().isoformat()
                        }, websocket)
                
            except asyncio.TimeoutError:
                # Ping automático cada 30 segundos
                await websocket_manager.send_personal_message({
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat()
                }, websocket)
                
    except WebSocketDisconnect:
        logger.info("Cliente WebSocket desconectado")
    except Exception as e:
        logger.error(f"Error en WebSocket: {e}")
    finally:
        websocket_manager.disconnect(websocket)

# ==================== FUNCIONES AUXILIARES ====================

async def get_system_status():
    """Obtener estado del sistema"""
    if not replicator_service:
        return {"status": "not_initialized"}
    
    return await replicator_service.get_health()

async def on_message_replicated(message_data):
    """Callback cuando se replica un mensaje"""
    # Enviar actualización a clientes WebSocket
    await websocket_manager.broadcast({
        "type": "message_replicated",
        "data": message_data,
        "timestamp": datetime.now().isoformat()
    })

async def on_stats_updated(stats_data):
    """Callback cuando se actualizan las estadísticas"""
    # Enviar actualización a clientes WebSocket
    await websocket_manager.broadcast({
        "type": "stats_updated",
        "data": stats_data,
        "timestamp": datetime.now().isoformat()
    })

# ==================== MAIN ====================

if __name__ == "__main__":
    print("🚀 Iniciando Telegram-Discord Replicator v3.0 Enterprise")
    print("=" * 80)
    print("✅ SOLUCIONES ENTERPRISE IMPLEMENTADAS:")
    print("   📄 PDFs: Preview automático + enlace de descarga funcional")
    print("   🎵 Audios: Transcripción automática + conversión MP3")  
    print("   🎬 Videos: Compresión automática + watermarks aplicados")
    print("   🎨 Watermarks: Texto fijo + marcas visuales en imágenes")
    print("   📊 UI: Dashboard moderno inspirado en tu imagen")
    print("   🏗️ Arquitectura: Servicios integrados modulares")
    print("=" * 80)
    print("🌐 URLs disponibles:")
    print("   Dashboard: http://localhost:8000/dashboard")
    print("   Health: http://localhost:8000/health")
    print("   API Docs: http://localhost:8000/docs")
    print("   Download: http://localhost:8000/download/{filename}")
    print("=" * 80)
    
    try:
        # Verificar configuración básica
        if not settings.telegram.api_id or not settings.telegram.api_hash:
            logger.error("❌ Configura TELEGRAM_API_ID y TELEGRAM_API_HASH en .env")
            print("\n📝 Configura tu archivo .env:")
            print("   TELEGRAM_API_ID=tu_api_id")
            print("   TELEGRAM_API_HASH=tu_api_hash")
            print("   TELEGRAM_PHONE=+1234567890")
            print("   WEBHOOK_-1001234567890=https://discord.com/api/webhooks/tu_webhook")
            sys.exit(1)
        
        logger.info("🌐 Iniciando servidor web enterprise...")
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=settings.debug,
            log_level="info" if not settings.debug else "debug"
        )
        
    except KeyboardInterrupt:
        logger.info("👋 Detenido por el usuario")
    except Exception as e:
        logger.error(f"❌ Error crítico: {e}")
        sys.exit(1)
