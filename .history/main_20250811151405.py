# 🎭 Main Orchestrator - FIXED & ENHANCED
# Integración completa con Discovery Service y UI moderna

import asyncio
import logging
import os
import sys
import subprocess
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import httpx

# ============= CONFIGURACIÓN =============

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("orchestrator")

class ServiceRegistry:
    """🏗️ Registry de microservicios enterprise"""
    
    def __init__(self):
        self.services = {}
        self.websocket_connections = {
            "dashboard": set(),
            "discovery": set()
        }
        self.stats = {
            "services_running": 0,
            "total_requests": 0,
            "errors": 0,
            "uptime_start": datetime.now()
        }
        
    async def register_service(self, name: str, url: str, health_endpoint: str = "/health"):
        """Registrar un microservicio"""
        service_info = {
            "name": name,
            "url": url,
            "health_endpoint": health_endpoint,
            "status": "unknown",
            "last_check": None,
            "response_time": None
        }
        
        self.services[name] = service_info
        await self._check_service_health(name)
        logger.info(f"📡 Servicio registrado: {name} -> {url}")
        
    async def _check_service_health(self, service_name: str):
        """Verificar salud de un servicio"""
        service = self.services.get(service_name)
        if not service:
            return False
            
        try:
            start_time = time.time()
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{service['url']}{service['health_endpoint']}")
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    service["status"] = "healthy"
                    service["response_time"] = round(response_time, 2)
                else:
                    service["status"] = "unhealthy"
                    
                service["last_check"] = datetime.now()
                return True
                
        except Exception as e:
            service["status"] = "unreachable"
            service["last_check"] = datetime.now()
            logger.warning(f"⚠️ Servicio {service_name} no disponible: {e}")
            return False
    
    async def health_check_all(self):
        """Health check de todos los servicios"""
        tasks = []
        for service_name in self.services:
            tasks.append(self._check_service_health(service_name))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Actualizar stats
        healthy_services = sum(1 for s in self.services.values() if s["status"] == "healthy")
        self.stats["services_running"] = healthy_services
        
        return {
            "healthy_services": healthy_services,
            "total_services": len(self.services),
            "services": self.services
        }
    
    async def get_dashboard_data(self):
        """🎭 Obtener datos para el dashboard"""
        health_data = await self.health_check_all()
        
        # Stats combinados
        dashboard_stats = {
            "services": health_data,
            "orchestrator": {
                "uptime_seconds": (datetime.now() - self.stats["uptime_start"]).total_seconds(),
                "total_requests": self.stats["total_requests"],
                "errors": self.stats["errors"],
                "websocket_connections": sum(len(conns) for conns in self.websocket_connections.values())
            }
        }
        
        # Intentar obtener stats de servicios específicos
        try:
            # Message Replicator stats
            if "message_replicator" in self.services and self.services["message_replicator"]["status"] == "healthy":
                async with httpx.AsyncClient(timeout=3.0) as client:
                    response = await client.get(f"{self.services['message_replicator']['url']}/api/stats")
                    if response.status_code == 200:
                        dashboard_stats["replicator"] = response.json()
        except:
            pass
            
        try:
            # Discovery Service stats
            if "discovery" in self.services and self.services["discovery"]["status"] == "healthy":
                async with httpx.AsyncClient(timeout=3.0) as client:
                    response = await client.get(f"{self.services['discovery']['url']}/api/discovery/status")
                    if response.status_code == 200:
                        dashboard_stats["discovery"] = response.json()
        except:
            pass
        
        return dashboard_stats
    
    async def get_discovery_status(self):
        """🔍 Obtener estado del Discovery Service"""
        try:
            if "discovery" not in self.services:
                return {"available": False, "error": "Discovery service not registered"}
                
            if self.services["discovery"]["status"] != "healthy":
                return {"available": False, "error": "Discovery service unhealthy"}
                
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.services['discovery']['url']}/api/discovery/status")
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"available": False, "error": f"HTTP {response.status_code}"}
                    
        except Exception as e:
            return {"available": False, "error": str(e)}
    
    async def get_discovered_chats(self, params: Dict = None):
        """📋 Obtener chats descubiertos del Discovery Service"""
        try:
            if "discovery" not in self.services:
                return []
                
            if self.services["discovery"]["status"] != "healthy":
                return []
                
            url = f"{self.services['discovery']['url']}/api/discovery/chats"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params or {})
                if response.status_code == 200:
                    data = response.json()
                    return data.get("chats", [])
                else:
                    return []
                    
        except Exception as e:
            logger.error(f"❌ Error getting discovered chats: {e}")
            return []
    
    async def start_discovery_scan(self, force_refresh: bool = False):
        """🔍 Iniciar escaneo de discovery"""
        try:
            if "discovery" not in self.services:
                raise Exception("Discovery service not available")
                
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.services['discovery']['url']}/api/discovery/scan",
                    params={"force_refresh": force_refresh}
                )
                if response.status_code == 200:
                    return response.json()
                else:
                    raise Exception(f"HTTP {response.status_code}: {response.text}")
                    
        except Exception as e:
            logger.error(f"❌ Error starting discovery scan: {e}")
            raise HTTPException(status_code=500, detail=str(e))

# ============= FASTAPI APP =============

app = FastAPI(
    title="🎭 Enterprise Orchestrator",
    description="Orchestrator principal del sistema de microservicios",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service registry global
service_registry = ServiceRegistry()

# Templates y static files
try:
    templates = Jinja2Templates(directory="frontend/templates")
    app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
except Exception as e:
    logger.warning(f"⚠️ Templates/static files not loaded: {e}")
    templates = None

# ============= STARTUP LOGIC =============

@app.on_event("startup")
async def startup_event():
    """🚀 Inicialización del orchestrator"""
    logger.info("🎭 Iniciando Enterprise Orchestrator...")
    
    # Registrar servicios conocidos
    await register_known_services()
    
    # Iniciar health checks periódicos
    asyncio.create_task(periodic_health_checks())
    
    logger.info("✅ Orchestrator iniciado correctamente")

async def register_known_services():
    """📡 Registrar servicios conocidos"""
    known_services = [
        {
            "name": "message_replicator",
            "url": "http://localhost:8001",
            "health_endpoint": "/health"
        },
        {
            "name": "discovery",
            "url": "http://localhost:8002",
            "health_endpoint": "/health"
        },
        {
            "name": "watermark",
            "url": "http://localhost:8081",
            "health_endpoint": "/health"
        }
    ]
    
    for service in known_services:
        await service_registry.register_service(
            service["name"],
            service["url"],
            service["health_endpoint"]
        )

async def periodic_health_checks():
    """🔄 Health checks periódicos"""
    while True:
        try:
            await service_registry.health_check_all()
            await asyncio.sleep(30)  # Check cada 30 segundos
        except Exception as e:
            logger.error(f"❌ Error en health check periódico: {e}")
            await asyncio.sleep(60)

# ============= ROUTES =============

@app.get("/health")
async def health_check():
    """🏥 Health check del orchestrator"""
    health_data = await service_registry.health_check_all()
    
    return {
        "status": "healthy",
        "orchestrator": "running",
        "timestamp": datetime.now().isoformat(),
        "services": health_data,
        "uptime_seconds": (datetime.now() - service_registry.stats["uptime_start"]).total_seconds()
    }

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """🏠 Página principal"""
    return HTMLResponse("""
    <html>
        <head>
            <title>🎭 Enterprise Orchestrator</title>
            <style>
                body { font-family: system-ui; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                       color: white; text-align: center; padding: 50px; }
                .container { max-width: 800px; margin: 0 auto; }
                .service-card { background: rgba(255,255,255,0.1); padding: 20px; margin: 15px; 
                               border-radius: 15px; backdrop-filter: blur(10px); }
                .btn { background: #4CAF50; color: white; padding: 15px 30px; border: none; 
                       border-radius: 8px; font-size: 16px; cursor: pointer; margin: 10px; }
                .btn:hover { background: #45a049; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎭 Enterprise Orchestrator</h1>
                <p>Sistema de microservicios enterprise para replicación y watermarks</p>
                
                <div class="service-card">
                    <h3>📊 Dashboard Principal</h3>
                    <p>Métricas en tiempo real y gestión de servicios</p>
                    <a href="/dashboard"><button class="btn">Abrir Dashboard</button></a>
                </div>
                
                <div class="service-card">
                    <h3>🔍 Discovery System</h3>
                    <p>Descubrimiento visual de chats de Telegram</p>
                    <a href="/discovery"><button class="btn">Abrir Discovery</button></a>
                </div>
                
                <div class="service-card">
                    <h3>📚 API Documentation</h3>
                    <p>Documentación completa de APIs</p>
                    <a href="/docs"><button class="btn">Ver Docs</button></a>
                </div>
            </div>
        </body>
    </html>
    """)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_ui(request: Request):
    """🎭 Dashboard principal enterprise"""
    if not templates:
        return HTMLResponse("""
        <h1>🎭 Enterprise Dashboard</h1>
        <p>Dashboard not available - templates not loaded</p>
        <p><a href="/health">Health Check</a> | <a href="/docs">API Docs</a></p>
        """)
    
    dashboard_data = await service_registry.get_dashboard_data()
    service_registry.stats["total_requests"] += 1
    
    return templates.TemplateResponse("dashboard_enterprise_v2.html", {
        "request": request,
        "data": dashboard_data,
        "title": "Enterprise Dashboard v5.0"
    })

@app.get("/discovery", response_class=HTMLResponse)
async def discovery_ui(request: Request):
    """🔍 UI principal del Discovery System"""
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

# ============= API ENDPOINTS =============

@app.get("/api/services")
async def get_services_status():
    """📡 Estado de todos los servicios"""
    health_data = await service_registry.health_check_all()
    return health_data

@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """📊 Estadísticas para el dashboard"""
    dashboard_data = await service_registry.get_dashboard_data()
    return dashboard_data

@app.get("/api/discovery/status")
async def discovery_status():
    """🔍 Estado del Discovery Service"""
    status = await service_registry.get_discovery_status()
    return status

@app.post("/api/discovery/scan")
async def start_discovery_scan(force_refresh: bool = False):
    """🔍 Iniciar escaneo de discovery"""
    result = await service_registry.start_discovery_scan(force_refresh)
    return result

@app.get("/api/discovery/chats")
async def get_discovered_chats(
    limit: int = 50,
    offset: int = 0,
    chat_type: Optional[str] = None
):
    """📋 Obtener chats descubiertos"""
    params = {"limit": limit, "offset": offset}
    if chat_type:
        params["chat_type"] = chat_type
        
    chats = await service_registry.get_discovered_chats(params)
    return {"chats": chats, "total": len(chats)}

@app.get("/api/discovery/chats/{chat_id}/preview")
async def get_chat_preview(chat_id: int):
    """🔍 Preview de un chat específico"""
    try:
        if "discovery" not in service_registry.services:
            raise HTTPException(status_code=503, detail="Discovery service not available")
            
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{service_registry.services['discovery']['url']}/api/discovery/chats/{chat_id}/preview"
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail=response.text)
                
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Discovery service unreachable: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/configuration/save")
async def save_configuration(request: Request):
    """💾 Guardar configuración de replicación"""
    try:
        config_data = await request.json()
        
        # Validar datos requeridos
        if not config_data.get("chat_id") or not config_data.get("webhook_url"):
            raise HTTPException(status_code=400, detail="chat_id and webhook_url are required")
        
        # Enviar configuración al Message Replicator
        if "message_replicator" in service_registry.services:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{service_registry.services['message_replicator']['url']}/api/configure",
                    json=config_data
                )
                if response.status_code == 200:
                    # Notificar via WebSocket
                    await broadcast_websocket_message({
                        "type": "configuration_saved",
                        "data": config_data
                    })
                    return {"status": "success", "message": "Configuration saved"}
                else:
                    raise HTTPException(status_code=response.status_code, detail=response.text)
        else:
            raise HTTPException(status_code=503, detail="Message replicator service not available")
            
    except Exception as e:
        logger.error(f"❌ Error saving configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/configuration/test")
async def test_configuration(request: Request):
    """🧪 Probar configuración de replicación"""
    try:
        config_data = await request.json()
        
        # Validar webhook URL
        webhook_url = config_data.get("webhook_url")
        if not webhook_url:
            raise HTTPException(status_code=400, detail="webhook_url is required")
        
        # Test webhook
        async with httpx.AsyncClient(timeout=10.0) as client:
            test_payload = {
                "content": "🧪 Test message from Enterprise Orchestrator",
                "embeds": [{
                    "title": "Configuration Test",
                    "description": "This is a test message to verify webhook configuration",
                    "color": 3447003,
                    "timestamp": datetime.now().isoformat()
                }]
            }
            
            response = await client.post(webhook_url, json=test_payload)
            
            if response.status_code in [200, 204]:
                return {
                    "status": "success",
                    "message": "Webhook test successful",
                    "response_time": response.elapsed.total_seconds()
                }
            else:
                return {
                    "status": "error",
                    "message": f"Webhook test failed: HTTP {response.status_code}",
                    "details": response.text
                }
                
    except httpx.RequestError as e:
        return {
            "status": "error",
            "message": f"Network error: {e}"
        }
    except Exception as e:
        logger.error(f"❌ Error testing configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============= WEBSOCKET ENDPOINTS =============

@app.websocket("/ws/dashboard")
async def dashboard_websocket(websocket: WebSocket):
    """📡 WebSocket para updates del dashboard en tiempo real"""
    await websocket.accept()
    service_registry.websocket_connections["dashboard"].add(websocket)
    
    try:
        # Enviar datos iniciales
        initial_data = await service_registry.get_dashboard_data()
        await websocket.send_text(json.dumps({
            "type": "initial_stats",
            "data": initial_data
        }))
        
        # Mantener conexión activa con ping/pong
        while True:
            try:
                # Esperar mensaje del cliente
                await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
            except asyncio.TimeoutError:
                # Enviar ping para mantener conexión
                await websocket.send_text(json.dumps({"type": "ping"}))
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"❌ Dashboard WebSocket error: {e}")
    finally:
        service_registry.websocket_connections["dashboard"].discard(websocket)

@app.websocket("/ws/discovery")
async def discovery_websocket(websocket: WebSocket):
    """🔍 WebSocket para updates del discovery en tiempo real"""
    await websocket.accept()
    service_registry.websocket_connections["discovery"].add(websocket)
    
    try:
        # Conectar con Discovery Service WebSocket si está disponible
        if "discovery" in service_registry.services and service_registry.services["discovery"]["status"] == "healthy":
            # Proxy WebSocket messages from Discovery Service
            discovery_url = service_registry.services["discovery"]["url"].replace("http", "ws")
            
            import websockets
            async with websockets.connect(f"{discovery_url}/ws") as discovery_ws:
                # Forward messages bidirectionally
                async def forward_to_client():
                    async for message in discovery_ws:
                        await websocket.send_text(message)
                
                async def forward_to_discovery():
                    while True:
                        try:
                            message = await websocket.receive_text()
                            await discovery_ws.send(message)
                        except WebSocketDisconnect:
                            break
                
                # Run both directions concurrently
                await asyncio.gather(
                    forward_to_client(),
                    forward_to_discovery(),
                    return_exceptions=True
                )
        else:
            # Discovery service not available
            await websocket.send_text(json.dumps({
                "type": "service_unavailable",
                "message": "Discovery service not available"
            }))
            await websocket.receive_text()  # Keep connection open
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"❌ Discovery WebSocket error: {e}")
    finally:
        service_registry.websocket_connections["discovery"].discard(websocket)

# ============= UTILITY FUNCTIONS =============

async def broadcast_websocket_message(message: Dict):
    """📡 Broadcast mensaje a todos los WebSockets conectados"""
    message_str = json.dumps(message)
    
    # Broadcast to dashboard connections
    disconnected = set()
    for websocket in service_registry.websocket_connections["dashboard"]:
        try:
            await websocket.send_text(message_str)
        except:
            disconnected.add(websocket)
    
    # Clean up disconnected websockets
    service_registry.websocket_connections["dashboard"] -= disconnected

# ============= BACKGROUND TASKS =============

async def periodic_stats_broadcast():
    """📊 Broadcast periódico de estadísticas"""
    while True:
        try:
            stats = await service_registry.get_dashboard_data()
            await broadcast_websocket_message({
                "type": "stats_update",
                "data": stats
            })
            await asyncio.sleep(10)  # Broadcast cada 10 segundos
        except Exception as e:
            logger.error(f"❌ Error in periodic stats broadcast: {e}")
            await asyncio.sleep(30)

# ============= STARTUP TASKS =============

@app.on_event("startup")
async def start_background_tasks():
    """🚀 Iniciar tareas en background"""
    asyncio.create_task(periodic_stats_broadcast())

# ============= MAIN =============

if __name__ == "__main__":
    print("🎭 Iniciando Enterprise Orchestrator...")
    print("📊 Dashboard: http://localhost:8000/dashboard")
    print("🔍 Discovery: http://localhost:8000/discovery") 
    print("📚 API Docs: http://localhost:8000/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )