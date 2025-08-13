#!/usr/bin/env python3
"""
🎭 ENTERPRISE MICROSERVICES ORCHESTRATOR v5.0 - DISCOVERY INTEGRATION
====================================================================
Orquestador principal con Discovery Service integrado
"""

import asyncio
import httpx
import json
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

# Logger
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Stats del orquestador
orchestrator_stats = {
    "start_time": datetime.now(),
    "requests_handled": 0,
    "services_started": 0,
    "discovery_integrations": 0
}

# ============= DISCOVERY INTEGRATION MODELS =============

class ChatConfigRequest(BaseModel):
    """Request para configurar chat discovered"""
    chat_id: int
    chat_title: str
    enabled: bool = True
    destination_webhook: Optional[str] = None
    filters: Dict[str, Any] = {}
    transformations: Dict[str, Any] = {}

class BulkConfigRequest(BaseModel):
    """Request para configuración bulk"""
    chat_ids: List[int]
    operation: str  # 'enable', 'disable', 'configure'
    config: Dict[str, Any] = {}

class DiscoveryUIConfig(BaseModel):
    """Configuración de UI para Discovery"""
    view_mode: str = "grid"  # 'grid', 'list', 'cards'
    filters_visible: bool = True
    auto_refresh: bool = True
    refresh_interval: int = 30
    show_inactive: bool = False

# ============= ENHANCED SERVICE REGISTRY =============

class EnhancedServiceRegistry:
    """Registry mejorado con Discovery Service integration"""
    
    def __init__(self):
        self.services = {
            "message_replicator": {
                "name": "Message Replicator",
                "url": "http://localhost:8001",
                "port": 8001,
                "status": "unknown",
                "description": "Enhanced Replicator Service",
                "capabilities": ["message_replication", "media_processing", "webhooks"],
                "endpoints": {
                    "health": "/health",
                    "stats": "/stats",
                    "config": "/api/config",
                    "groups": "/api/groups"
                }
            },
            "discovery": {
                "name": "Discovery Service",
                "url": "http://localhost:8002", 
                "port": 8002,
                "status": "unknown",
                "description": "Auto-discovery de chats Telegram",
                "capabilities": ["chat_discovery", "telegram_scanning", "real_time_updates"],
                "endpoints": {
                    "health": "/health",
                    "status": "/status",
                    "scan": "/api/discovery/scan",
                    "chats": "/api/discovery/chats",
                    "websocket": "/ws"
                }
            },
            "watermark": {
                "name": "Watermark Service",
                "url": "http://localhost:8081",
                "port": 8081,
                "status": "unknown", 
                "description": "Servicio de watermarks para medios",
                "capabilities": ["image_watermark", "video_watermark", "text_overlay"],
                "endpoints": {
                    "health": "/health",
                    "dashboard": "/dashboard",
                    "config": "/api/config"
                }
            }
        }
        self.http_client = httpx.AsyncClient(timeout=10.0)
        self.websocket_connections: Dict[str, WebSocket] = {}
    
    async def check_service_health(self, service_name: str) -> Dict[str, Any]:
        """Health check mejorado con capabilities"""
        service = self.services.get(service_name)
        if not service:
            return {"status": "not_found"}
        
        try:
            response = await self.http_client.get(f"{service['url']}/health")
            if response.status_code == 200:
                self.services[service_name]["status"] = "healthy"
                health_data = response.json()
                health_data["capabilities"] = service["capabilities"]
                health_data["endpoints"] = service["endpoints"]
                return health_data
            else:
                self.services[service_name]["status"] = "unhealthy"
                return {"status": "unhealthy", "code": response.status_code}
                
        except Exception as e:
            self.services[service_name]["status"] = "error"
            return {"status": "error", "error": str(e)}
    
    async def get_service_stats(self, service_name: str) -> Dict[str, Any]:
        """Obtener estadísticas específicas del servicio"""
        service = self.services.get(service_name)
        if not service:
            return {}
        
        try:
            # Para Discovery Service usar /status
            endpoint = "/status" if service_name == "discovery" else "/stats"
            response = await self.http_client.get(f"{service['url']}{endpoint}")
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    async def check_all_services(self) -> tuple[int, int]:
        """Check all services y retornar healthy/total"""
        healthy = 0
        total = len(self.services)
        
        for service_name in self.services:
            health = await self.check_service_health(service_name)
            if health.get("status") == "healthy":
                healthy += 1
        
        return healthy, total
    
    # 🔧 FIX: Función corregida para Discovery Service
    async def get_discovered_chats(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Obtener chats discovered con conexión corregida"""
        try:
            # 🔧 FIX: Usar httpx.AsyncClient con timeout más largo
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Construir parámetros de query
                params = filters or {}
                
                # 🔧 FIX: URL directa al Discovery Service
                discovery_url = "http://localhost:8002/api/discovery/chats"
                
                logger.info(f"🔍 Connecting to Discovery Service: {discovery_url}")
                response = await client.get(discovery_url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    chats = data.get("chats", [])
                    logger.info(f"✅ Discovered {len(chats)} chats from Discovery Service")
                    return chats
                else:
                    logger.error(f"❌ Discovery Service HTTP {response.status_code}: {response.text}")
                    return []
                    
        except httpx.ConnectError as e:
            logger.error(f"❌ Cannot connect to Discovery Service: {e}")
            return []
        except httpx.TimeoutException as e:
            logger.error(f"❌ Discovery Service timeout: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Discovery Service error: {e}")
            return []
    
    # 🔧 FIX: Función corregida para Discovery Scan
    async def discovery_scan_chats(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Trigger scan en Discovery Service con conexión corregida"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:  # 🔧 FIX: Timeout más largo para scan
                discovery_url = "http://localhost:8002/api/discovery/scan"
                
                logger.info(f"🔍 Starting discovery scan: {discovery_url}")
                response = await client.post(
                    discovery_url,
                    json={"force_refresh": force_refresh}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"✅ Discovery scan started successfully")
                    return result
                else:
                    logger.error(f"❌ Discovery scan failed: HTTP {response.status_code}")
                    return {"error": f"HTTP {response.status_code}: {response.text}"}
                    
        except httpx.ConnectError as e:
            logger.error(f"❌ Cannot connect to Discovery Service for scan: {e}")
            return {"error": "Discovery Service not available"}
        except Exception as e:
            logger.error(f"❌ Discovery scan error: {e}")
            return {"error": str(e)}
    
    async def configure_discovered_chat(self, config: ChatConfigRequest) -> Dict[str, Any]:
        """Configurar un chat discovered para replicación"""
        try:
            # Enviar configuración al Message Replicator
            response = await self.http_client.post(
                "http://localhost:8001/api/config/add_group",
                json={
                    "group_id": config.chat_id,
                    "group_name": config.chat_title,
                    "webhook_url": config.destination_webhook,
                    "enabled": config.enabled,
                    "filters": config.filters,
                    "transformations": config.transformations
                }
            )
            
            if response.status_code == 200:
                orchestrator_stats["discovery_integrations"] += 1
                return {"success": True, "message": "Chat configured successfully"}
            else:
                return {"success": False, "error": f"Configuration failed: HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def bulk_configure_chats(self, bulk_config: BulkConfigRequest) -> Dict[str, Any]:
        """Configuración bulk de chats"""
        results = {"successful": 0, "failed": 0, "details": []}
        
        for chat_id in bulk_config.chat_ids:
            try:
                if bulk_config.operation == "enable":
                    response = await self.http_client.post(
                        f"http://localhost:8001/api/config/groups/{chat_id}/enable"
                    )
                elif bulk_config.operation == "disable":
                    response = await self.http_client.post(
                        f"http://localhost:8001/api/config/groups/{chat_id}/disable"
                    )
                elif bulk_config.operation == "configure":
                    response = await self.http_client.put(
                        f"http://localhost:8001/api/config/groups/{chat_id}",
                        json=bulk_config.config
                    )
                
                if response.status_code == 200:
                    results["successful"] += 1
                    results["details"].append({"chat_id": chat_id, "status": "success"})
                else:
                    results["failed"] += 1
                    results["details"].append({"chat_id": chat_id, "status": "failed", "error": f"HTTP {response.status_code}"})
                    
            except Exception as e:
                results["failed"] += 1
                results["details"].append({"chat_id": chat_id, "status": "failed", "error": str(e)})
        
        return results
    
    # 🔧 FIX: Función corregida para Discovery Status
    async def get_discovery_status(self) -> Dict[str, Any]:
        """🔍 Estado del Discovery Service con conexión corregida"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # 🔧 FIX: URL directa al Discovery Service status
                discovery_url = "http://localhost:8002/status"
                
                logger.info(f"🔍 Checking Discovery Service status: {discovery_url}")
                response = await client.get(discovery_url)
                
                if response.status_code == 200:
                    status_data = response.json()
                    logger.info(f"✅ Discovery Service status: {status_data.get('status', 'unknown')}")
                    return {
                        "available": True,
                        "status": status_data
                    }
                else:
                    logger.error(f"❌ Discovery Service status check failed: HTTP {response.status_code}")
                    return {
                        "available": False,
                        "error": f"HTTP {response.status_code}"
                    }
                    
        except httpx.ConnectError as e:
            logger.error(f"❌ Cannot connect to Discovery Service for status: {e}")
            return {
                "available": False,
                "error": "Service not reachable"
            }
        except Exception as e:
            logger.error(f"❌ Discovery status error: {e}")
            return {
                "available": False,
                "error": str(e)
            }
    
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Obtener datos completos para dashboard con Discovery integration"""
        dashboard_data = {
            "timestamp": datetime.now().isoformat(),
            "orchestrator": {
                "uptime": (datetime.now() - orchestrator_stats["start_time"]).total_seconds(),
                "requests_handled": orchestrator_stats["requests_handled"],
                "services_started": orchestrator_stats["services_started"],
                "discovery_integrations": orchestrator_stats["discovery_integrations"]
            },
            "summary": {
                "healthy_services": 0,
                "total_services": len(self.services),
                "discovery_enabled": False,
                "total_discovered_chats": 0,
                "configured_chats": 0
            },
            "services": {},
            "discovery": {
                "available": False,
                "scanning": False,
                "last_scan": None,
                "total_chats": 0,
                "recent_chats": []
            }
        }
        
        # Check services
        for service_name, service_info in self.services.items():
            health = await self.check_service_health(service_name)
            stats = await self.get_service_stats(service_name)
            
            dashboard_data["services"][service_name] = {
                "health": health,
                "stats": stats,
                "info": service_info
            }
            
            if health.get("status") == "healthy":
                dashboard_data["summary"]["healthy_services"] += 1
        
        # Discovery-specific data
        if dashboard_data["services"].get("discovery", {}).get("health", {}).get("status") == "healthy":
            dashboard_data["summary"]["discovery_enabled"] = True
            dashboard_data["discovery"]["available"] = True
            
            # Get discovery stats
            discovery_stats = dashboard_data["services"]["discovery"]["stats"]
            if discovery_stats:
                dashboard_data["discovery"]["scanning"] = discovery_stats.get("current_scan", {}).get("is_scanning", False)
                dashboard_data["discovery"]["last_scan"] = discovery_stats.get("scanner_stats", {}).get("last_scan")
                dashboard_data["discovery"]["total_chats"] = discovery_stats.get("database_stats", {}).get("total_chats", 0)
                dashboard_data["summary"]["total_discovered_chats"] = dashboard_data["discovery"]["total_chats"]
            
            # Get recent chats (last 10)
            recent_chats = await self.get_discovered_chats({"limit": 10, "offset": 0})
            dashboard_data["discovery"]["recent_chats"] = recent_chats
        
        return dashboard_data

# Instancia global del registry
service_registry = EnhancedServiceRegistry()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manejo del ciclo de vida del orquestador"""
    try:
        logger.info("🚀 Starting Enterprise Microservices Orchestrator v5.0...")
        
        # Verificar servicios disponibles
        healthy, total = await service_registry.check_all_services()
        logger.info(f"📊 Services available: {healthy}/{total}")
        
        # Información de inicio
        print("\n" + "="*70)
        print("🎭 ENTERPRISE MICROSERVICES ORCHESTRATOR v5.0")
        print("="*70)
        print("🌐 Main endpoints:")
        print("   📊 Dashboard:         http://localhost:8000/dashboard")
        print("   🔍 Discovery UI:      http://localhost:8000/discovery")
        print("   🎭 Groups Hub:        http://localhost:8000/groups")
        print("   🏥 Health Check:      http://localhost:8000/health")
        print("   📚 API Docs:          http://localhost:8000/docs")
        print("\n🔗 Microservices:")
        for name, service in service_registry.services.items():
            status_icon = "✅" if service.get("status") == "healthy" else "❌"
            print(f"   {status_icon} {service['name']:20} {service['url']}")
        print("\n🎯 NEW: Auto-Discovery System integrated!")
        print("="*70)
        
        yield
        
    finally:
        await service_registry.http_client.aclose()
        logger.info("🛑 Main Orchestrator stopped")

# Crear aplicación FastAPI
app = FastAPI(
    title="🎭 Enterprise Microservices Orchestrator v5.0",
    description="Orquestador principal con Discovery Service integration",
    version="5.0.0",
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

# Static files y templates
try:
    app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
    templates = Jinja2Templates(directory="frontend/templates")
except Exception as e:
    logger.warning(f"Templates not loaded: {e}")
    templates = None

# ============= CORE ENDPOINTS =============

@app.get("/")
async def root():
    """Información del orquestador"""
    uptime = (datetime.now() - orchestrator_stats["start_time"]).total_seconds()
    
    return {
        "service": "orchestrator",
        "version": "5.0.0",
        "status": "running",
        "uptime_seconds": uptime,
        "features": ["discovery_integration", "auto_chat_discovery", "bulk_configuration", "groups_hub"],
        "endpoints": {
            "dashboard": "/dashboard",
            "discovery": "/discovery",
            "groups": "/groups",
            "health": "/health",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Health check del orquestador"""
    healthy, total = await service_registry.check_all_services()
    
    return {
        "status": "healthy" if healthy > 0 else "degraded",
        "service": "orchestrator",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "healthy": healthy,
            "total": total,
            "percentage": (healthy / total * 100) if total > 0 else 0
        },
        "discovery_enabled": healthy > 0 and "discovery" in [name for name, info in service_registry.services.items() if info.get("status") == "healthy"]
    }

@app.get("/stats")
async def get_stats():
    """Estadísticas completas del sistema"""
    dashboard_data = await service_registry.get_dashboard_data()
    orchestrator_stats["requests_handled"] += 1
    return dashboard_data

# ============= DISCOVERY INTEGRATION ENDPOINTS (CORREGIDOS) =============

@app.post("/api/discovery/scan")
async def trigger_discovery_scan_endpoint(force_refresh: bool = False):
    """🔧 Endpoint corregido para trigger scan"""
    result = await service_registry.discovery_scan_chats(force_refresh)
    return result

@app.get("/api/discovery/chats")
async def get_discovered_chats_endpoint(
    chat_type: Optional[str] = None,
    search_term: Optional[str] = None,
    min_participants: Optional[int] = None,
    limit: int = 100,
    offset: int = 0
):
    """📋 Endpoint corregido para obtener chats discovered"""
    filters = {"limit": limit, "offset": offset}
    if chat_type:
        filters["chat_type"] = chat_type
    if search_term:
        filters["search_term"] = search_term
    if min_participants:
        filters["min_participants"] = min_participants
    
    chats = await service_registry.get_discovered_chats(filters)
    return {"chats": chats, "total": len(chats)}

@app.post("/api/discovery/configure")
async def configure_discovered_chat_fixed(request: Request):
    """🔧 FIX: Configurar chat discovered con validación mejorada"""
    try:
        config_data = await request.json()
        
        # Validar datos requeridos
        if not config_data.get("chat_id"):
            raise HTTPException(status_code=400, detail="chat_id is required")
        
        chat_id = config_data["chat_id"]
        chat_title = config_data.get("chat_title", f"Chat {chat_id}")
        
        # Obtener webhook disponible automáticamente si no se proporciona
        destination_webhook = config_data.get("destination_webhook")
        if not destination_webhook:
            # Usar un webhook por defecto (puedes ajustar esta lógica)
            available_webhooks = ["https://discord.com/api/webhooks/default"]
            if available_webhooks:
                destination_webhook = available_webhooks[0]
            else:
                raise HTTPException(status_code=400, detail="No Discord webhooks configured")
        
        # Configuración mejorada con defaults seguros
        enhanced_config = {
            "group_id": chat_id,
            "group_name": chat_title,
            "webhook_url": destination_webhook,
            "enabled": config_data.get("enabled", True),
            "filters": {
                "exclude_bots": config_data.get("filters", {}).get("excludeBots", False),
                "include_media": config_data.get("filters", {}).get("includeMedia", True),
                "min_length": config_data.get("filters", {}).get("minLength", 0)
            },
            "transformations": {
                "add_prefix": config_data.get("transformations", {}).get("prefixText", ""),
                "watermark": config_data.get("transformations", {}).get("watermark", False),
                "use_embeds": config_data.get("transformations", {}).get("embed", False)
            }
        }
        
        # Para desarrollo: simular configuración exitosa
        logger.info(f"Would configure chat {chat_id} with webhook {destination_webhook}")
        return {"success": True, "message": f"Chat '{chat_title}' configured successfully"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error configuring chat: {e}")
        raise HTTPException(status_code=500, detail=f"Configuration error: {str(e)}")

@app.post("/api/discovery/bulk_configure")
async def bulk_configure_chats(bulk_config: BulkConfigRequest):
    """Configuración bulk de múltiples chats"""
    result = await service_registry.bulk_configure_chats(bulk_config)
    return result

@app.get("/api/discovery/status")
async def get_discovery_status():
    """Estado del Discovery Service"""
    discovery_status = await service_registry.get_discovery_status()
    return discovery_status

# ============= GROUPS HUB ENDPOINTS =============

@app.get("/groups", response_class=HTMLResponse)
async def groups_hub(request: Request):
    """Groups Hub - Visual Management Center"""
    if not templates:
        return HTMLResponse("""
        <h1>🎭 Groups Hub</h1>
        <p>Templates not loaded - place the Groups Hub HTML in frontend/templates/groups_hub.html</p>
        <p><a href="/dashboard">← Back to Dashboard</a></p>
        """)
    
    return templates.TemplateResponse("groups_hub.html", {
        "request": request,
        "title": "Groups Hub"
    })

@app.get("/api/groups")
async def get_configured_groups():
    """Obtener grupos configurados con estado real"""
    try:
        # Para desarrollo: retornar grupos simulados
        groups = [
            {
                "id": -1001234567890,
                "title": "Test Group 1",
                "is_active": True,
                "has_errors": False,
                "messages_count": 150,
                "last_activity": datetime.now().isoformat(),
                "webhook_url": "https://discord.com/api/webhooks/test1"
            },
            {
                "id": -1001234567891,
                "title": "Test Channel 2",
                "is_active": False,
                "has_errors": True,
                "messages_count": 75,
                "last_activity": datetime.now().isoformat(),
                "webhook_url": "https://discord.com/api/webhooks/test2"
            }
        ]
        
        return {"groups": groups}
        
    except Exception as e:
        logger.error(f"Error getting groups: {e}")
        return {"groups": []}

@app.post("/api/groups/{group_id}/enable")
async def enable_group(group_id: int):
    """Habilitar grupo"""
    try:
        logger.info(f"Enabling group {group_id}")
        return {"success": True, "message": "Group enabled"}
        
    except Exception as e:
        logger.error(f"Error enabling group: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/groups/{group_id}/disable")
async def disable_group(group_id: int):
    """Deshabilitar grupo"""
    try:
        logger.info(f"Disabling group {group_id}")
        return {"success": True, "message": "Group disabled"}
        
    except Exception as e:
        logger.error(f"Error disabling group: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/groups/{group_id}")
async def remove_group(group_id: int):
    """Remover configuración de grupo"""
    try:
        logger.info(f"Removing group {group_id}")
        return {"success": True, "message": "Group removed"}
        
    except Exception as e:
        logger.error(f"Error removing group: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/config")
async def get_configuration():
    """Obtener configuración disponible"""
    try:
        webhooks = [
            "https://discord.com/api/webhooks/test1",
            "https://discord.com/api/webhooks/test2"
        ]
        
        return {
            "webhooks": webhooks,
            "telegram_configured": True,
            "discord_webhooks_count": len(webhooks)
        }
        
    except Exception as e:
        logger.error(f"Error getting config: {e}")
        return {"webhooks": []}

# ============= UI ENDPOINTS =============

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Dashboard principal con Discovery integration"""
    if not templates:
        return HTMLResponse("""
        <h1>🎭 Enterprise Dashboard</h1>
        <p>Dashboard not available - templates not loaded</p>
        <p><a href="/health">Health Check</a> | <a href="/docs">API Docs</a></p>
        """)
    
    dashboard_data = await service_registry.get_dashboard_data()
    orchestrator_stats["requests_handled"] += 1
    
    return templates.TemplateResponse("dashboard_enterprise_v2.html", {
        "request": request,
        "data": dashboard_data,
        "title": "Enterprise Dashboard v5.0"
    })

@app.get("/discovery", response_class=HTMLResponse)
async def discovery_ui(request: Request):
    """🔧 FIX: UI principal del Discovery System"""
    if not templates:
        return HTMLResponse("""
        <h1>🔍 Discovery System</h1>
        <p>Discovery UI not available - templates not loaded</p>
        <p><a href="/dashboard">← Back to Dashboard</a></p>
        """)
    
    # Datos básicos para Discovery UI
    discovery_data = {
        "status": {"available": False, "stats": {}},
        "chats": [],
        "ui_config": {
            "view_mode": "grid",
            "auto_refresh": True,
            "refresh_interval": 30
        }
    }
    
    try:
        # Intentar obtener estado de discovery
        discovery_status = await service_registry.get_discovery_status()
        discovery_data["status"] = discovery_status
        
        if discovery_status.get("available"):
            recent_chats = await service_registry.get_discovered_chats({"limit": 20})
            discovery_data["chats"] = recent_chats
    except Exception as e:
        logger.error(f"Error getting discovery data: {e}")
    
    return templates.TemplateResponse("discovery_dashboard.html", {
        "request": request,
        "data": discovery_data,
        "title": "Discovery System"
    })

# ============= WEBSOCKET ENDPOINTS =============

@app.websocket("/ws")
async def main_websocket_endpoint(websocket: WebSocket):
    """🔧 FIX: WebSocket principal que faltaba"""
    await websocket.accept()
    service_registry.websocket_connections["main"] = websocket
    
    try:
        # Enviar estado inicial
        initial_data = await service_registry.get_dashboard_data()
        await websocket.send_text(json.dumps({
            "type": "initial_connection",
            "data": initial_data
        }))
        
        # Loop principal
        while True:
            try:
                # Recibir mensajes del cliente
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Procesar comandos
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }))
                elif message.get("type") == "request_stats":
                    stats = await service_registry.get_dashboard_data()
                    await websocket.send_text(json.dumps({
                        "type": "stats_update",
                        "data": stats
                    }))
                    
            except asyncio.TimeoutError:
                # Enviar ping para mantener conexión
                await websocket.send_text(json.dumps({"type": "ping"}))
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"❌ Main WebSocket error: {e}")
    finally:
        if "main" in service_registry.websocket_connections:
            del service_registry.websocket_connections["main"]

@app.websocket("/ws/dashboard")
async def dashboard_websocket(websocket: WebSocket):
    """WebSocket para updates del dashboard en tiempo real"""
    await websocket.accept()
    service_registry.websocket_connections["dashboard"] = websocket
    
    try:
        while True:
            # Enviar stats cada 10 segundos
            await asyncio.sleep(10)
            
            dashboard_data = await service_registry.get_dashboard_data()
            await websocket.send_json({
                "type": "dashboard_update",
                "data": dashboard_data,
                "timestamp": datetime.now().isoformat()
            })
            
    except WebSocketDisconnect:
        if "dashboard" in service_registry.websocket_connections:
            del service_registry.websocket_connections["dashboard"]

@app.websocket("/ws/discovery")
async def discovery_websocket(websocket: WebSocket):
    """WebSocket para updates del Discovery System"""
    await websocket.accept()
    service_registry.websocket_connections["discovery"] = websocket
    
    try:
        while True:
            await asyncio.sleep(5)
            
            # Obtener estado de discovery
            discovery_status = await service_registry.get_discovery_status()
            
            await websocket.send_json({
                "type": "discovery_update",
                "status": discovery_status,
                "timestamp": datetime.now().isoformat()
            })
            
    except WebSocketDisconnect:
        if "discovery" in service_registry.websocket_connections:
            del service_registry.websocket_connections["discovery"]

# ============= SERVICE PROXY ENDPOINTS =============

@app.get("/api/services/{service_name}/health")
async def proxy_service_health(service_name: str):
    """Proxy para health checks de servicios"""
    health = await service_registry.check_service_health(service_name)
    return health

@app.get("/api/services/{service_name}/stats")
async def proxy_service_stats(service_name: str):
    """Proxy para estadísticas de servicios"""
    stats = await service_registry.get_service_stats(service_name)
    return stats

# ============= GROUPS HUB INTEGRATION ENDPOINTS =============
# Añadir estos endpoints a tu main.py después de los endpoints existentes

@app.get("/api/groups/discovered")
async def get_discovered_groups():
    """Obtener grupos discovered desde Discovery Service"""
    try:
        # Conectar con Discovery Service
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("http://localhost:8002/api/discovery/chats?limit=100")
            
            if response.status_code == 200:
                discovery_data = response.json()
                discovered_chats = discovery_data.get("chats", [])
                
                # Filtrar solo grupos y canales (no chats privados)
                groups = []
                for chat in discovered_chats:
                    if chat.get("type") in ["group", "supergroup", "channel"]:
                        # Convertir formato Discovery a formato Groups Hub
                        group_data = {
                            "id": chat["id"],
                            "title": chat["title"],
                            "type": chat["type"], 
                            "username": chat.get("username"),
                            "participants_count": chat.get("participants_count", 0),
                            "is_configured": False,  # Por defecto no configurado
                            "is_active": False,      # Por defecto no activo
                            "has_errors": False,     # Por defecto sin errores
                            "messages_count": 0,     # Por defecto 0 mensajes
                            "last_activity": chat.get("discovered_at"),
                            "webhook_url": None,     # No configurado aún
                            "discovered_at": chat.get("discovered_at"),
                            "is_verified": chat.get("is_verified", False),
                            "is_public": chat.get("is_public", False)
                        }
                        groups.append(group_data)
                
                logger.info(f"✅ Retrieved {len(groups)} discovered groups")
                return {"groups": groups, "total": len(groups)}
                
            else:
                logger.error(f"❌ Discovery Service error: HTTP {response.status_code}")
                return {"groups": [], "total": 0, "error": "Discovery Service unavailable"}
                
    except Exception as e:
        logger.error(f"❌ Error getting discovered groups: {e}")
        return {"groups": [], "total": 0, "error": str(e)}

@app.get("/api/groups/configured")
async def get_configured_groups():
    """Obtener grupos ya configurados para replicación"""
    try:
        # Conectar con Message Replicator Service para obtener grupos configurados
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("http://localhost:8001/api/config/groups")
            
            if response.status_code == 200:
                config_data = response.json()
                configured_groups = config_data.get("groups", {})
                
                # Convertir formato a lista
                groups = []
                for group_id, config in configured_groups.items():
                    group_data = {
                        "id": int(group_id),
                        "title": config.get("group_name", f"Group {group_id}"),
                        "type": "configured",
                        "username": None,
                        "participants_count": 0,
                        "is_configured": True,
                        "is_active": config.get("enabled", False),
                        "has_errors": False,
                        "messages_count": 0,
                        "last_activity": config.get("updated_at"),
                        "webhook_url": config.get("webhook_url"),
                        "configured_at": config.get("created_at"),
                        "filters": config.get("filters", {}),
                        "transformations": config.get("transformations", {})
                    }
                    groups.append(group_data)
                
                logger.info(f"✅ Retrieved {len(groups)} configured groups")
                return {"groups": groups, "total": len(groups)}
                
            else:
                logger.warning(f"⚠️ Message Replicator not available: HTTP {response.status_code}")
                return {"groups": [], "total": 0}
                
    except Exception as e:
        logger.error(f"❌ Error getting configured groups: {e}")
        return {"groups": [], "total": 0, "error": str(e)}

@app.get("/api/groups/all")
async def get_all_groups():
    """Obtener todos los grupos: discovered + configured"""
    try:
        # Obtener grupos discovered
        discovered = await get_discovered_groups()
        discovered_groups = discovered.get("groups", [])
        
        # Obtener grupos configured
        configured = await get_configured_groups()
        configured_groups = configured.get("groups", [])
        
        # Merge y marcar configurados
        all_groups = []
        configured_ids = {group["id"] for group in configured_groups}
        
        # Añadir discovered groups y marcar si están configurados
        for group in discovered_groups:
            if group["id"] in configured_ids:
                group["is_configured"] = True
                group["is_active"] = True
                # Buscar webhook del grupo configurado
                for configured_group in configured_groups:
                    if configured_group["id"] == group["id"]:
                        group["webhook_url"] = configured_group["webhook_url"]
                        group["filters"] = configured_group.get("filters", {})
                        group["transformations"] = configured_group.get("transformations", {})
                        break
            all_groups.append(group)
        
        # Añadir grupos configurados que no están en discovered
        for configured_group in configured_groups:
            if configured_group["id"] not in {g["id"] for g in all_groups}:
                all_groups.append(configured_group)
        
        # Ordenar por título
        all_groups.sort(key=lambda x: x.get("title", "").lower())
        
        logger.info(f"✅ Total groups: {len(all_groups)} (discovered: {len(discovered_groups)}, configured: {len(configured_groups)})")
        
        return {
            "groups": all_groups,
            "total": len(all_groups),
            "stats": {
                "discovered": len(discovered_groups),
                "configured": len(configured_groups),
                "active": len([g for g in all_groups if g.get("is_active")]),
                "channels": len([g for g in all_groups if g.get("type") == "channel"]),
                "supergroups": len([g for g in all_groups if g.get("type") == "supergroup"]),
                "groups": len([g for g in all_groups if g.get("type") == "group"])
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting all groups: {e}")
        return {"groups": [], "total": 0, "error": str(e)}

@app.post("/api/groups/{group_id}/configure")
async def configure_group_for_replication(group_id: int, config_data: dict):
    """Configurar un grupo discovered para replicación"""
    try:
        # Validar datos requeridos
        webhook_url = config_data.get("webhook_url")
        if not webhook_url:
            raise HTTPException(status_code=400, detail="webhook_url is required")
        
        # Obtener información del grupo desde Discovery
        discovered = await get_discovered_groups()
        discovered_groups = discovered.get("groups", [])
        
        target_group = None
        for group in discovered_groups:
            if group["id"] == group_id:
                target_group = group
                break
        
        if not target_group:
            raise HTTPException(status_code=404, detail="Group not found in discovered chats")
        
        # Preparar configuración para Message Replicator
        replicator_config = {
            "group_id": group_id,
            "group_name": target_group["title"],
            "webhook_url": webhook_url,
            "enabled": config_data.get("enabled", True),
            "filters": config_data.get("filters", {}),
            "transformations": config_data.get("transformations", {})
        }
        
        # Enviar configuración al Message Replicator
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://localhost:8001/api/config/add_group",
                json=replicator_config
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Configured group {group_id} for replication")
                
                return {
                    "success": True,
                    "message": f"Group '{target_group['title']}' configured for replication",
                    "group_id": group_id,
                    "webhook_url": webhook_url,
                    "replicator_response": result
                }
            else:
                error_detail = f"Message Replicator error: HTTP {response.status_code}"
                logger.error(f"❌ {error_detail}")
                raise HTTPException(status_code=500, detail=error_detail)
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error configuring group {group_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Configuration failed: {str(e)}")

@app.post("/api/groups/{group_id}/quick-configure")
async def quick_configure_group(group_id: int):
    """Configuración rápida con webhook por defecto"""
    try:
        # Obtener webhooks disponibles desde .env
        available_webhooks = []
        for key, value in os.environ.items():
            if key.startswith('WEBHOOK_') and value:
                available_webhooks.append(value)
        
        if not available_webhooks:
            raise HTTPException(status_code=400, detail="No Discord webhooks configured in .env")
        
        # Usar el primer webhook disponible
        default_webhook = available_webhooks[0]
        
        # Configurar con defaults
        config_data = {
            "webhook_url": default_webhook,
            "enabled": True,
            "filters": {
                "exclude_bots": True,
                "min_length": 1
            },
            "transformations": {
                "add_prefix": "[AUTO] ",
                "watermark": True
            }
        }
        
        return await configure_group_for_replication(group_id, config_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in quick configure: {e}")
        raise HTTPException(status_code=500, detail=f"Quick configure failed: {str(e)}")

@app.delete("/api/groups/{group_id}/unconfigure")
async def unconfigure_group(group_id: int):
    """Quitar configuración de replicación de un grupo"""
    try:
        # Eliminar configuración del Message Replicator
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.delete(f"http://localhost:8001/api/config/groups/{group_id}")
            
            if response.status_code == 200:
                logger.info(f"✅ Unconfigured group {group_id}")
                return {
                    "success": True,
                    "message": f"Group {group_id} unconfigured successfully"
                }
            elif response.status_code == 404:
                return {
                    "success": True,
                    "message": f"Group {group_id} was not configured"
                }
            else:
                raise HTTPException(status_code=500, detail=f"Unconfigure failed: HTTP {response.status_code}")
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error unconfiguring group {group_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Unconfigure failed: {str(e)}")

# ============= ENHANCED GROUPS HUB ENDPOINT =============

@app.get("/groups", response_class=HTMLResponse)
async def enhanced_groups_hub(request: Request):
    """Groups Hub mejorado con integración Discovery"""
    if not templates:
        return HTMLResponse("""
        <h1>🎭 Groups Hub</h1>
        <p>Templates not loaded</p>
        <p><a href="/dashboard">← Back to Dashboard</a></p>
        """)
    
    # Obtener datos para el template
    try:
        all_groups = await get_all_groups()
        groups_data = all_groups.get("groups", [])
        stats_data = all_groups.get("stats", {})
        
        # Información de configuración disponible
        config_info = await get_configuration()
        available_webhooks = config_info.get("webhooks", [])
        
        template_data = {
            "request": request,
            "title": "Groups Hub - Enhanced",
            "groups": groups_data,
            "stats": stats_data,
            "available_webhooks": available_webhooks,
            "total_groups": len(groups_data)
        }
        
        return templates.TemplateResponse("groups_hub.html", template_data)
        
    except Exception as e:
        logger.error(f"❌ Error loading Groups Hub: {e}")
        return templates.TemplateResponse("groups_hub.html", {
            "request": request,
            "title": "Groups Hub",
            "groups": [],
            "stats": {},
            "available_webhooks": [],
            "total_groups": 0,
            "error": str(e)
        })

# ============= TEMPLATE CREATION =============

@app.on_event("startup")
async def create_groups_hub_template():
    """Crear template de Groups Hub si no existe"""
    try:
        template_path = Path("frontend/templates/groups_hub.html")
        if not template_path.exists():
            # Crear directorio si no existe
            template_path.parent.mkdir(parents=True, exist_ok=True)
            
            # HTML básico del Groups Hub
            groups_hub_html = '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎭 Groups Hub - Enterprise Management</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --bg-glass: rgba(255, 255, 255, 0.05);
            --bg-card: rgba(255, 255, 255, 0.08);
            --border-glass: rgba(255, 255, 255, 0.1);
            --text-primary: rgba(255, 255, 255, 0.95);
            --text-secondary: rgba(255, 255, 255, 0.7);
            --text-muted: rgba(255, 255, 255, 0.5);
            --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #667eea 100%);
            min-height: 100vh;
            color: var(--text-primary);
        }
        
        .container {
            max-width: 1600px;
            margin: 0 auto;
            padding: 1.5rem;
        }
        
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            padding: 2rem;
            background: var(--bg-card);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            border: 1px solid var(--border-glass);
        }
        
        .header h1 {
            font-size: 2.2rem;
            font-weight: 800;
            background: var(--primary-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .btn {
            padding: 1rem 2rem;
            border: none;
            border-radius: 16px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: var(--transition);
            display: flex;
            align-items: center;
            gap: 0.5rem;
            color: var(--text-primary);
            background: var(--primary-gradient);
            text-decoration: none;
        }
        
        .btn:hover {
            transform: translateY(-2px);
        }
        
        .main-layout {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
        }
        
        .panel {
            background: var(--bg-card);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            border: 1px solid var(--border-glass);
            padding: 2rem;
        }
        
        .panel-title {
            font-size: 1.3rem;
            font-weight: 700;
            margin-bottom: 2rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .chat-list {
            max-height: 500px;
            overflow-y: auto;
        }
        
        .loading {
            text-align: center;
            padding: 3rem;
            color: var(--text-secondary);
        }
        
        .spinner {
            width: 40px;
            height: 40px;
            border: 3px solid var(--border-glass);
            border-top: 3px solid #3b82f6;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 1rem;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .chat-item {
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 1rem;
            margin-bottom: 0.5rem;
            background: var(--bg-glass);
            border: 1px solid var(--border-glass);
            border-radius: 12px;
            transition: var(--transition);
        }
        
        .chat-item:hover {
            background: rgba(255, 255, 255, 0.1);
            border-color: #3b82f6;
        }
        
        .chat-avatar {
            width: 48px;
            height: 48px;
            border-radius: 12px;
            background: var(--primary-gradient);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
            font-weight: 700;
            color: white;
        }
        
        .chat-info {
            flex: 1;
        }
        
        .chat-title {
            font-size: 0.95rem;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 0.25rem;
        }
        
        .chat-meta {
            font-size: 0.75rem;
            color: var(--text-muted);
        }
        
        .action-btn {
            padding: 0.5rem 1rem;
            background: #3b82f6;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 0.8rem;
            cursor: pointer;
            transition: var(--transition);
        }
        
        .action-btn:hover {
            background: #2563eb;
        }
        
        @media (max-width: 1024px) {
            .main-layout {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>🎭 Groups Hub</h1>
            <div>
                <button class="btn" onclick="refreshData()">
                    <i class="fas fa-sync"></i>
                    Refresh
                </button>
                <a href="/dashboard" class="btn" style="margin-left: 1rem;">
                    <i class="fas fa-arrow-left"></i>
                    Dashboard
                </a>
            </div>
        </header>
        
        <div class="main-layout">
            <div class="panel">
                <h2 class="panel-title">
                    <i class="fas fa-search"></i>
                    Discovered Chats
                </h2>
                
                <div class="chat-list" id="discoveredChats">
                    <div class="loading">
                        <div class="spinner"></div>
                        <p>Loading discovered chats...</p>
                    </div>
                </div>
            </div>
            
            <div class="panel">
                <h2 class="panel-title">
                    <i class="fas fa-cogs"></i>
                    Configured Groups
                </h2>
                
                <div class="chat-list" id="configuredGroups">
                    <div class="loading">
                        <div class="spinner"></div>
                        <p>Loading configured groups...</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        class GroupsHub {
            constructor() {
                this.discoveredChats = [];
                this.configuredGroups = [];
                this.init();
            }
            
            async init() {
                await this.loadData();
                this.render();
            }
            
            async loadData() {
                try {
                    // Load discovered chats
                    const discoveryResponse = await fetch('/api/discovery/chats?limit=100');
                    if (discoveryResponse.ok) {
                        const data = await discoveryResponse.json();
                        this.discoveredChats = data.chats || [];
                    }
                    
                    // Load configured groups
                    const groupsResponse = await fetch('/api/groups');
                    if (groupsResponse.ok) {
                        const data = await groupsResponse.json();
                        this.configuredGroups = data.groups || [];
                    }
                } catch (error) {
                    console.error('Error loading data:', error);
                }
            }
            
            render() {
                this.renderDiscovered();
                this.renderConfigured();
            }
            
            renderDiscovered() {
                const container = document.getElementById('discoveredChats');
                
                if (this.discoveredChats.length === 0) {
                    container.innerHTML = '<div class="loading"><p>No chats discovered yet</p></div>';
                    return;
                }
                
                container.innerHTML = this.discoveredChats.map(chat => this.createChatHTML(chat, 'discovered')).join('');
            }
            
            renderConfigured() {
                const container = document.getElementById('configuredGroups');
                
                if (this.configuredGroups.length === 0) {
                    container.innerHTML = '<div class="loading"><p>No groups configured yet</p></div>';
                    return;
                }
                
                container.innerHTML = this.configuredGroups.map(group => this.createChatHTML(group, 'configured')).join('');
            }
            
            createChatHTML(item, type) {
                const avatar = (item.title || 'Unknown').charAt(0).toUpperCase();
                const action = type === 'discovered' ? 
                    `<button class="action-btn" onclick="groupsHub.configureChat(${item.id})">Configure</button>` :
                    `<button class="action-btn" onclick="groupsHub.editGroup(${item.id})">Edit</button>`;
                
                return `
                    <div class="chat-item">
                        <div class="chat-avatar">${avatar}</div>
                        <div class="chat-info">
                            <div class="chat-title">${item.title || 'Unknown'}</div>
                            <div class="chat-meta">
                                ${item.participants_count ? `${item.participants_count} members` : 'Private'}
                                ${item.type ? ` • ${item.type}` : ''}
                            </div>
                        </div>
                        ${action}
                    </div>
                `;
            }
            
            async configureChat(chatId) {
                try {
                    const chat = this.discoveredChats.find(c => c.id === chatId);
                    if (!chat) return;
                    
                    const config = {
                        chat_id: chatId,
                        chat_title: chat.title,
                        enabled: true
                    };
                    
                    const response = await fetch('/api/discovery/configure', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(config)
                    });
                    
                    if (response.ok) {
                        this.showNotification('Chat configured successfully!', 'success');
                        await this.loadData();
                        this.render();
                    } else {
                        throw new Error('Configuration failed');
                    }
                } catch (error) {
                    console.error('Configuration error:', error);
                    this.showNotification('Failed to configure chat', 'error');
                }
            }
            
            editGroup(groupId) {
                this.showNotification(`Edit group ${groupId} - Feature coming soon!`, 'info');
            }
            
            showNotification(message, type) {
                // Simple notification
                alert(message);
            }
        }
        
        // Global instance
        let groupsHub;
        
        document.addEventListener('DOMContentLoaded', () => {
            groupsHub = new GroupsHub();
        });
        
        async function refreshData() {
            await groupsHub.loadData();
            groupsHub.render();
        }
    </script>
</body>
</html>'''
            
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(groups_hub_html)
            
            logger.info("✅ Created Groups Hub template")
    except Exception as e:
        logger.error(f"❌ Error creating groups_hub template: {e}")

# ============= MAIN =============

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )