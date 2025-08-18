#!/usr/bin/env python3
"""
🎭 ZERO COST PROJECT - MAIN ORCHESTRATOR COMPLETO
===============================================
Orchestrator con Enhanced Replicator Service integrado
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Import services
from app.services.enhanced_replicator_service import EnhancedReplicatorService
from app.services.registry.service_registry import ServiceRegistry

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============ FASTAPI APP ============

app = FastAPI(
    title="Zero Cost Orchestrator",
    description="Sistema de replicación completo con watermarks",
    version="3.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Templates y Static files
templates = Jinja2Templates(directory="frontend/templates")

if Path("frontend/static").exists():
    app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# ============ GLOBAL SERVICES ============

replicator_service: Optional[EnhancedReplicatorService] = None
service_registry: Optional[ServiceRegistry] = None

# ============ STARTUP/SHUTDOWN ============

@app.on_event("startup")
async def startup_event():
    """Inicialización completa del sistema"""
    global replicator_service, service_registry
    
    logger.info("🚀 Zero Cost Orchestrator iniciando...")
    
    # Crear directorios
    directories = ["config", "logs", "watermarks", "temp", "frontend/templates/admin", "data"]
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    try:
        # Inicializar Enhanced Replicator Service
        logger.info("📡 Inicializando Enhanced Replicator Service...")
        replicator_service = EnhancedReplicatorService()
        await replicator_service.initialize()
        
        # Iniciar listening en background
        asyncio.create_task(replicator_service.start_listening())
        logger.info("✅ Enhanced Replicator Service iniciado")
        
        # Inicializar Service Registry
        service_registry = ServiceRegistry()
        logger.info("✅ Service Registry iniciado")
        
    except Exception as e:
        logger.error(f"❌ Error en startup: {e}")
        import traceback
        traceback.print_exc()
    
    logger.info("🎉 Zero Cost Orchestrator listo!")

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown limpio"""
    global replicator_service
    
    logger.info("🛑 Shutting down...")
    
    if replicator_service:
        try:
            await replicator_service.stop()
            logger.info("✅ Replicator stopped")
        except Exception as e:
            logger.error(f"❌ Error stopping replicator: {e}")
    
    logger.info("✅ Shutdown complete")

# ============ HEALTH CHECK ============

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    global replicator_service
    
    system_health = {
        "status": "healthy",
        "service": "zero_cost_orchestrator",
        "version": "3.0.0",
        "timestamp": datetime.now().isoformat()
    }
    
    if replicator_service:
        try:
            replicator_health = await replicator_service.get_health()
            system_health["replicator"] = replicator_health
        except Exception as e:
            system_health["replicator"] = {"status": "error", "error": str(e)}
            system_health["status"] = "degraded"
    else:
        system_health["replicator"] = {"status": "not_initialized"}
        system_health["status"] = "degraded"
    
    return system_health

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Zero Cost Orchestrator", 
        "status": "running",
        "version": "3.0.0"
    }

# ============ DASHBOARD ROUTES ============

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Dashboard principal"""
    try:
        return templates.TemplateResponse("dashboard.html", {"request": request})
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        return HTMLResponse(f"<h1>Dashboard</h1><p>Error: {e}</p>")

# ============ DASHBOARD API ROUTES (para arreglar 404s) ============

@app.get("/api/v1/dashboard/api/stats")
async def get_dashboard_stats():
    """API stats para dashboard - FIX 404"""
    global replicator_service
    
    try:
        if not replicator_service:
            return {
                "status": "error",
                "message": "Replicator service not initialized",
                "stats": {
                    "messages_replicated": 0,
                    "images_processed": 0,
                    "videos_processed": 0,
                    "watermarks_applied": 0,
                    "errors": 0,
                    "uptime_hours": 0,
                    "groups_active": 0,
                    "success_rate": 0
                }
            }
        
        # Obtener stats del replicator
        stats = await replicator_service.get_dashboard_stats()
        
        return {
            "status": "success",
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        return {
            "status": "error",
            "message": str(e),
            "stats": {
                "messages_replicated": 0,
                "images_processed": 0,
                "videos_processed": 0,
                "watermarks_applied": 0,
                "errors": 0,
                "uptime_hours": 0,
                "groups_active": 0,
                "success_rate": 0
            }
        }

@app.get("/api/v1/dashboard/api/health")
async def get_dashboard_health():
    """API health para dashboard - FIX 404"""
    global replicator_service, service_registry
    
    try:
        health_data = {
            "status": "healthy",
            "services": {},
            "summary": {
                "healthy_services": 0,
                "total_services": 0,
                "system_status": "online"
            }
        }
        
        # Check replicator
        if replicator_service:
            try:
                replicator_health = await replicator_service.get_health()
                health_data["services"]["replicator"] = replicator_health
                if replicator_health.get("status") == "healthy":
                    health_data["summary"]["healthy_services"] += 1
                health_data["summary"]["total_services"] += 1
            except Exception as e:
                health_data["services"]["replicator"] = {"status": "error", "error": str(e)}
                health_data["summary"]["total_services"] += 1
                health_data["status"] = "degraded"
        
        # Check service registry
        if service_registry:
            try:
                healthy, total = await service_registry.check_all_services()
                health_data["summary"]["healthy_services"] += healthy
                health_data["summary"]["total_services"] += total
            except Exception as e:
                logger.error(f"Error checking service registry: {e}")
        
        # Update system status
        if health_data["summary"]["healthy_services"] == 0:
            health_data["summary"]["system_status"] = "down"
            health_data["status"] = "unhealthy"
        elif health_data["summary"]["healthy_services"] < health_data["summary"]["total_services"]:
            health_data["summary"]["system_status"] = "degraded"
            health_data["status"] = "degraded"
        
        return health_data
        
    except Exception as e:
        logger.error(f"Error getting dashboard health: {e}")
        return {
            "status": "error",
            "message": str(e),
            "services": {},
            "summary": {
                "healthy_services": 0,
                "total_services": 0,
                "system_status": "down"
            }
        }

@app.get("/api/v1/dashboard/api/flows")
async def get_dashboard_flows():
    """API flows para dashboard - FIX 404"""
    global replicator_service
    
    try:
        if not replicator_service:
            return {
                "status": "error",
                "message": "Replicator service not initialized",
                "flows": []
            }
        
        # Obtener información de flujos/grupos
        stats = await replicator_service.get_dashboard_stats()
        
        flows = []
        if "groups_active" in stats:
            for group_id in stats["groups_active"]:
                flows.append({
                    "id": str(group_id),
                    "name": f"Group {group_id}",
                    "status": "active",
                    "messages_count": stats.get("messages_replicated", 0),
                    "last_activity": datetime.now().isoformat()
                })
        
        return {
            "status": "success",
            "flows": flows,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard flows: {e}")
        return {
            "status": "error",
            "message": str(e),
            "flows": []
        }

# ============ WATERMARK ADMIN PANEL ============

@app.get("/admin/watermarks", response_class=HTMLResponse)
async def watermark_admin_panel(request: Request):
    """Panel de administración de watermarks"""
    try:
        return templates.TemplateResponse("admin/watermarks.html", {"request": request})
    except Exception as e:
        logger.error(f"Error loading watermark panel: {e}")
        return HTMLResponse(f"""
        <h1>🎨 Panel de Watermarks</h1>
        <p>Error: {e}</p>
        <p>Asegúrate de que el archivo watermarks.html esté en frontend/templates/admin/</p>
        <a href="/dashboard">← Volver al Dashboard</a>
        """)

@app.get("/api/watermark/groups")
async def get_watermark_groups():
    """API para obtener grupos configurados - FIX para panel"""
    try:
        config_dir = Path("config")
        groups = []
        
        if config_dir.exists():
            for config_file in config_dir.glob("group_*.json"):
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    groups.append(data)
                except Exception as e:
                    logger.error(f"Error loading {config_file}: {e}")
        
        return {"groups": groups, "status": "success"}
    except Exception as e:
        logger.error(f"Error getting groups: {e}")
        return {"error": str(e), "status": "error"}

@app.post("/api/watermark/groups/{group_id}/config")
async def save_group_config(group_id: int, config: dict):
    """Guardar configuración de grupo - FIX para panel"""
    try:
        config_dir = Path("config")
        config_dir.mkdir(exist_ok=True)
        
        # Añadir metadata
        config.update({
            "group_id": group_id,
            "updated_at": datetime.now().isoformat()
        })
        
        # Si es nuevo grupo, añadir created_at
        config_file = config_dir / f"group_{group_id}.json"
        if not config_file.exists():
            config["created_at"] = datetime.now().isoformat()
        
        # Guardar configuración
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Configuración guardada para grupo {group_id}")
        
        # Si el replicator está corriendo, recargar configs
        global replicator_service
        if replicator_service and hasattr(replicator_service, 'watermark_service'):
            try:
                await replicator_service.watermark_service.reload_configurations()
                logger.info("✅ Configuraciones recargadas en replicator")
            except Exception as e:
                logger.warning(f"⚠️ No se pudieron recargar configs en replicator: {e}")
        
        return {"status": "success", "message": "Configuración guardada"}
        
    except Exception as e:
        logger.error(f"Error saving config: {e}")
        return {"error": str(e), "status": "error"}

@app.get("/api/replicator/status")
async def get_replicator_status():
    """Status detallado del replicator"""
    global replicator_service
    
    if not replicator_service:
        return {"status": "not_initialized", "message": "Replicator service not initialized"}
    
    try:
        status = await replicator_service.get_system_status()
        return status
    except Exception as e:
        logger.error(f"Error getting replicator status: {e}")
        return {"status": "error", "error": str(e)}

@app.post("/api/replicator/restart")
async def restart_replicator():
    """Reiniciar replicator service"""
    global replicator_service
    
    try:
        if replicator_service:
            await replicator_service.stop()
            logger.info("🛑 Replicator stopped")
        
        # Reiniciar
        replicator_service = EnhancedReplicatorService()
        await replicator_service.initialize()
        asyncio.create_task(replicator_service.start_listening())
        
        logger.info("✅ Replicator restarted")
        return {"status": "success", "message": "Replicator reiniciado"}
        
    except Exception as e:
        logger.error(f"Error restarting replicator: {e}")
        return {"status": "error", "error": str(e)}

# ============ MAIN ============

if __name__ == "__main__":
    import uvicorn
    
    logger.info("🎭 Iniciando Zero Cost Orchestrator Completo...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
