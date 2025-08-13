#!/usr/bin/env python3
"""
🔧 Dashboard API Fix - Endpoints que faltan para el UI
Agrega estos endpoints a tu main.py o run.py
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import json
from datetime import datetime
from pathlib import Path

# ============= MODELS =============

class GroupConfigModel(BaseModel):
    """Model para configuración de grupos"""
    group_id: int
    group_name: str
    enabled: bool = True
    webhook_url: Optional[str] = None
    filters: Dict[str, Any] = {}
    watermark_enabled: bool = False
    
class GroupUpdateModel(BaseModel):
    """Model para updates de grupos"""
    enabled: Optional[bool] = None
    webhook_url: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    watermark_enabled: Optional[bool] = None

# ============= CONFIGURATION MANAGER =============

class ConfigurationManager:
    """Gestor de configuraciones de grupos"""
    
    def __init__(self):
        self.config_file = Path("data/group_configurations.json")
        self.config_file.parent.mkdir(exist_ok=True)
        self._ensure_config_file()
    
    def _ensure_config_file(self):
        """Asegurar que existe el archivo de configuración"""
        if not self.config_file.exists():
            self.config_file.write_text(json.dumps({}, indent=2))
    
    async def load_configurations(self) -> Dict[str, Any]:
        """Cargar configuraciones desde archivo"""
        try:
            if self.config_file.exists():
                content = self.config_file.read_text()
                return json.loads(content)
            return {}
        except Exception as e:
            print(f"Error loading configurations: {e}")
            return {}
    
    async def save_configurations(self, configs: Dict[str, Any]) -> bool:
        """Guardar configuraciones a archivo"""
        try:
            self.config_file.write_text(json.dumps(configs, indent=2))
            return True
        except Exception as e:
            print(f"Error saving configurations: {e}")
            return False
    
    async def update_group_config(self, group_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Actualizar configuración de grupo"""
        configs = await self.load_configurations()
        
        if group_id not in configs:
            configs[group_id] = {
                "group_id": int(group_id),
                "group_name": f"Group {group_id}",
                "enabled": True,
                "webhook_url": None,
                "filters": {},
                "watermark_enabled": False,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        
        # Aplicar updates
        for key, value in updates.items():
            if key in ["enabled", "webhook_url", "filters", "watermark_enabled", "group_name"]:
                configs[group_id][key] = value
        
        configs[group_id]["updated_at"] = datetime.now().isoformat()
        
        await self.save_configurations(configs)
        return configs[group_id]

# Instancia global
config_manager = ConfigurationManager()

# ============= API ENDPOINTS =============

def add_dashboard_endpoints(app: FastAPI):
    """Agregar endpoints que faltan al dashboard"""
    
    @app.get("/api/groups")
    async def get_groups():
        """Obtener todos los grupos configurados"""
        try:
            # Combinar grupos del discovery con configuraciones
            configs = await config_manager.load_configurations()
            
            # Intentar obtener grupos del discovery service
            discovered_groups = []
            try:
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.get("http://localhost:8002/api/discovery/chats", timeout=5)
                    if response.status_code == 200:
                        discovery_data = response.json()
                        discovered_groups = discovery_data.get("chats", [])
            except Exception as e:
                print(f"Error fetching from discovery: {e}")
            
            # Construir respuesta combinada
            groups = []
            for group in discovered_groups:
                group_id = str(group.get("id", ""))
                config = configs.get(group_id, {})
                
                groups.append({
                    "id": group.get("id"),
                    "title": group.get("title", "Unknown"),
                    "type": group.get("type", "unknown"),
                    "participants": group.get("participants", 0),
                    "enabled": config.get("enabled", False),
                    "configured": group_id in configs,
                    "webhook_url": config.get("webhook_url"),
                    "filters": config.get("filters", {}),
                    "watermark_enabled": config.get("watermark_enabled", False),
                    "last_activity": group.get("last_activity"),
                    "status": "active" if config.get("enabled") else "paused"
                })
            
            return {
                "status": "success",
                "data": {
                    "groups": groups,
                    "total": len(groups),
                    "configured": len([g for g in groups if g["configured"]]),
                    "active": len([g for g in groups if g["enabled"]])
                }
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    @app.post("/api/groups/{group_id}/config")
    async def update_group_config(group_id: str, updates: Dict[str, Any]):
        """Actualizar configuración de un grupo"""
        try:
            config = await config_manager.update_group_config(group_id, updates)
            
            # Notificar al replicator service si está disponible
            try:
                import httpx
                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"http://localhost:8001/api/groups/{group_id}/config",
                        json=updates,
                        timeout=5
                    )
            except Exception as e:
                print(f"Error notifying replicator: {e}")
            
            return {
                "status": "success",
                "data": config,
                "message": f"Group {group_id} updated successfully"
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    @app.post("/api/groups/{group_id}/toggle")
    async def toggle_group(group_id: str):
        """Toggle enable/disable de un grupo"""
        try:
            configs = await config_manager.load_configurations()
            current_status = configs.get(group_id, {}).get("enabled", False)
            
            updates = {"enabled": not current_status}
            config = await config_manager.update_group_config(group_id, updates)
            
            return {
                "status": "success",
                "data": config,
                "message": f"Group {group_id} {'enabled' if config['enabled'] else 'disabled'}"
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    @app.post("/api/groups/bulk")
    async def bulk_group_operation(request: Dict[str, Any]):
        """Operaciones bulk en grupos"""
        try:
            group_ids = request.get("group_ids", [])
            operation = request.get("operation", "")
            config_updates = request.get("config", {})
            
            results = []
            
            for group_id in group_ids:
                try:
                    if operation == "enable":
                        updates = {"enabled": True}
                    elif operation == "disable":  
                        updates = {"enabled": False}
                    elif operation == "configure":
                        updates = config_updates
                    else:
                        continue
                    
                    config = await config_manager.update_group_config(str(group_id), updates)
                    results.append({"group_id": group_id, "status": "success", "config": config})
                    
                except Exception as e:
                    results.append({"group_id": group_id, "status": "error", "message": str(e)})
            
            return {
                "status": "success",
                "data": results,
                "message": f"Bulk operation completed on {len(group_ids)} groups"
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    @app.get("/api/system/status")
    async def get_system_status():
        """Estado completo del sistema"""
        try:
            services_status = {}
            
            # Check cada servicio
            services = {
                "replicator": "http://localhost:8001/health",
                "discovery": "http://localhost:8002/health", 
                "watermark": "http://localhost:8081/health"
            }
            
            import httpx
            async with httpx.AsyncClient() as client:
                for service_name, health_url in services.items():
                    try:
                        response = await client.get(health_url, timeout=3)
                        services_status[service_name] = {
                            "status": "healthy" if response.status_code == 200 else "unhealthy",
                            "response_time": response.elapsed.total_seconds()
                        }
                    except Exception as e:
                        services_status[service_name] = {
                            "status": "unreachable",
                            "error": str(e)
                        }
            
            return {
                "status": "success",
                "data": {
                    "services": services_status,
                    "orchestrator": {
                        "status": "healthy",
                        "uptime": (datetime.now() - datetime.now()).total_seconds(),
                        "version": "5.0"
                    }
                }
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

# ============= WEBSOCKET FIX =============

def serialize_datetime(obj):
    """Serializar datetime objects para JSON"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: serialize_datetime(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_datetime(item) for item in obj]
    return obj

def add_websocket_endpoint(app: FastAPI):
    """Agregar WebSocket endpoint corregido"""
    
    @app.websocket("/ws")
    async def websocket_endpoint(websocket):
        """WebSocket para updates en tiempo real"""
        await websocket.accept()
        print("🔌 Cliente WebSocket conectado")
        
        try:
            while True:
                # Obtener stats de todos los servicios
                stats = {}
                
                try:
                    import httpx
                    async with httpx.AsyncClient() as client:
                        # Stats del replicator
                        try:
                            response = await client.get("http://localhost:8001/stats", timeout=3)
                            if response.status_code == 200:
                                replicator_stats = response.json()
                                stats["replicator"] = serialize_datetime(replicator_stats)
                        except:
                            stats["replicator"] = {"status": "unavailable"}
                        
                        # Stats del discovery
                        try:
                            response = await client.get("http://localhost:8002/api/discovery/status", timeout=3)
                            if response.status_code == 200:
                                discovery_stats = response.json()
                                stats["discovery"] = serialize_datetime(discovery_stats)
                        except:
                            stats["discovery"] = {"status": "unavailable"}
                
                except Exception as e:
                    print(f"Error fetching stats: {e}")
                
                # Enviar update serializado
                await websocket.send_json({
                    "type": "stats_update",
                    "data": stats,
                    "timestamp": datetime.now().isoformat()
                })
                
                await asyncio.sleep(5)
                
        except Exception as e:
            print(f"WebSocket error: {e}")
        finally:
            print("🔌 Cliente WebSocket desconectado")

# ============= USAGE INSTRUCTIONS =============

"""
INSTRUCCIONES DE USO:

1. Agrega esto a tu run.py o main.py:

# Importar las funciones
from fix_dashboard_api import add_dashboard_endpoints, add_websocket_endpoint

# En tu app FastAPI:
app = FastAPI()

# Agregar los endpoints
add_dashboard_endpoints(app)
add_websocket_endpoint(app)

2. O si prefieres, ejecuta este archivo independiente:

if __name__ == "__main__":
    app = FastAPI()
    add_dashboard_endpoints(app)
    add_websocket_endpoint(app)
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""

if __name__ == "__main__":
    # Servidor independiente para testing
    app = FastAPI(title="Dashboard API Fix", version="1.0.0")
    
    # Agregar middleware CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Agregar endpoints
    add_dashboard_endpoints(app)
    add_websocket_endpoint(app)
    
    @app.get("/")
    async def root():
        return {"message": "Dashboard API Fix is running", "status": "healthy"}
    
    print("🚀 Dashboard API Fix running on http://localhost:8003")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)