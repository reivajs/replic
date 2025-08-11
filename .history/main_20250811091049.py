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
    
    async def discovery_scan_chats(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Trigger scan en Discovery Service"""
        try:
            response = await self.http_client.post(
                "http://localhost:8002/api/discovery/scan",
                json={"force_refresh": force_refresh}
            )
            return response.json() if response.status_code == 200 else {"error": "Scan failed"}
        except Exception as e:
            return {"error": str(e)}
    
    async def get_discovered_chats(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Obtener chats discovered"""
        try:
            params = filters or {}
            response = await self.http_client.get(
                "http://localhost:8002/api/discovery/chats",
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("chats", [])
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error getting discovered chats: {e}")
            return []
    
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
                    # Lógica para habilitar
                    response = await self.http_client.post(
                        f"http://localhost:8001/api/config/groups/{chat_id}/enable"
                    )
                elif bulk_config.operation == "disable":
                    # Lógica para deshabilitar
                    response = await self.http_client.post(
                        f"http://localhost:8001/api/config/groups/{chat_id}/disable"
                    )
                elif bulk_config.operation == "configure":
                    # Configuración custom
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
    
    async def get_discovery_status(self) -> Dict[str, Any]:
        """🔧 FIX: Obtener estado del Discovery Service"""
        try:
            discovery_health = await self.check_service_health("discovery")
            discovery_stats = await self.get_service_stats("discovery")
            
            return {
                "available": discovery_health.get("status") == "healthy",
                "health": discovery_health,
                "stats": discovery_stats
            }
        except Exception as e:
            return {
                "available": False,
                "health": {"status": "error", "error": str(e)},
                "stats": {}
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
        "features": ["discovery_integration", "auto_chat_discovery", "bulk_configuration"],
        "endpoints": {
            "dashboard": "/dashboard",
            "discovery": "/discovery", 
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

# ============= DISCOVERY INTEGRATION ENDPOINTS =============

@app.post("/api/discovery/scan")
async def trigger_discovery_scan(force_refresh: bool = False):
    """Trigger manual scan en Discovery Service"""
    result = await service_registry.discovery_scan_chats(force_refresh)
    return result

@app.get("/api/discovery/chats")
async def get_discovered_chats(
    chat_type: Optional[str] = None,
    search_term: Optional[str] = None,
    min_participants: Optional[int] = None,
    limit: int = 100,
    offset: int = 0
):
    """Obtener chats discovered con filtros"""
    filters = {}
    if chat_type:
        filters["chat_type"] = chat_type
    if search_term:
        filters["search_term"] = search_term
    if min_participants:
        filters["min_participants"] = min_participants
    
    filters.update({"limit": limit, "offset": offset})
    
    chats = await service_registry.get_discovered_chats(filters)
    return {"chats": chats, "total": len(chats)}

@app.post("/api/discovery/configure")
async def configure_discovered_chat(config: ChatConfigRequest):
    """Configurar un chat discovered para replicación"""
    result = await service_registry.configure_discovered_chat(config)
    return result

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

# ============= MAIN =============

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )