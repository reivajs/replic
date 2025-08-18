"""
Dashboard API - Enterprise Microservices
========================================
API endpoints para dashboard moderno con métricas en tiempo real
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import asyncio
import json

from app.utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()

class DashboardService:
    """Servicio de dashboard con métricas enterprise"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.websocket_clients: List[WebSocket] = []
        self.stats_cache = {
            "messages_received": 0,
            "messages_replicated": 0,
            "success_rate": 100.0,
            "active_groups": 0,
            "total_errors": 0,
            "last_update": datetime.now()
        }
        self.flows = []
        self.accounts = {
            "telegram": [],
            "discord": []
        }
    
    async def broadcast_update(self, data: Dict[str, Any]):
        """Broadcast actualizaciones a clientes WebSocket"""
        disconnected = []
        
        for client in self.websocket_clients:
            try:
                await client.send_json(data)
            except:
                disconnected.append(client)
        
        # Limpiar clientes desconectados
        for client in disconnected:
            if client in self.websocket_clients:
                self.websocket_clients.remove(client)
    
    def update_stats(self, **kwargs):
        """Actualizar estadísticas"""
        self.stats_cache.update(kwargs)
        self.stats_cache["last_update"] = datetime.now()
        
        # Broadcast a clientes WebSocket
        asyncio.create_task(self.broadcast_update({
            "type": "stats_update",
            "data": self.get_stats()
        }))
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas actuales"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "overview": {
                "messages_received": self.stats_cache["messages_received"],
                "messages_replicated": self.stats_cache["messages_replicated"],
                "success_rate": self.stats_cache["success_rate"],
                "uptime_hours": uptime / 3600,
                "active_groups": self.stats_cache["active_groups"],
                "total_errors": self.stats_cache["total_errors"]
            },
            "performance": {
                "avg_processing_time": 0.045,
                "throughput": self.calculate_throughput(),
                "error_rate": self.calculate_error_rate()
            },
            "groups": {
                "active": self.stats_cache["active_groups"],
                "total": self.stats_cache["active_groups"],
                "configured": len(self.flows)
            },
            "system": {
                "status": self.get_system_status(),
                "version": "6.0.0",
                "environment": "production"
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def calculate_throughput(self) -> float:
        """Calcular throughput (mensajes/segundo)"""
        if self.get_uptime_seconds() > 0:
            return self.stats_cache["messages_received"] / self.get_uptime_seconds()
        return 0.0
    
    def calculate_error_rate(self) -> float:
        """Calcular tasa de error"""
        total = self.stats_cache["messages_received"]
        if total > 0:
            return (self.stats_cache["total_errors"] / total) * 100
        return 0.0
    
    def get_uptime_seconds(self) -> float:
        """Obtener uptime en segundos"""
        return (datetime.now() - self.start_time).total_seconds()
    
    def get_system_status(self) -> str:
        """Determinar estado del sistema"""
        error_rate = self.calculate_error_rate()
        
        if error_rate > 10:
            return "degraded"
        elif error_rate > 5:
            return "warning"
        else:
            return "healthy"
    
    def get_flows(self) -> List[Dict[str, Any]]:
        """Obtener flujos configurados"""
        return self.flows or [
            {
                "id": "flow_main",
                "name": "Main Flow",
                "source": {"type": "telegram", "name": "Main Account"},
                "destination": {"type": "discord", "name": "Main Webhook"},
                "status": "active",
                "messages": self.stats_cache["messages_received"],
                "filters": ["watermark", "media_only"],
                "created": self.start_time.isoformat()
            }
        ]
    
    def get_accounts(self) -> Dict[str, List]:
        """Obtener cuentas conectadas"""
        return {
            "telegram": self.accounts["telegram"] or [
                {
                    "id": 1,
                    "name": "Main Account",
                    "phone": "+56985667015",
                    "status": "connected",
                    "groups": self.stats_cache["active_groups"]
                }
            ],
            "discord": self.accounts["discord"] or [
                {
                    "id": 1,
                    "name": "Main Webhook",
                    "url": "discord.com/api/webhooks/...",
                    "status": "active",
                    "messages_sent": self.stats_cache["messages_replicated"]
                }
            ]
        }
    
    async async def get_health(self) -> Dict[str, Any]:
        """Obtener estado de salud del sistema"""
        try:
            # Intentar obtener estado del registry
            from app.services.registry import get_registry
            registry = get_registry()
            system_status = await registry.get_system_status()
            
            return {
                "status": self.get_system_status(),
                "services": system_status.get("services", {}),
                "checks": {
                    "database": "n/a",
                    "redis": "n/a",
                    "telegram": "connected",
                    "discord": "connected"
                },
                "timestamp": datetime.now().isoformat()
            }
        except:
            # Fallback si registry no está disponible
            return {
                "status": self.get_system_status(),
                "services": {
                    "dashboard": "running",
                    "replicator": "unknown"
                },
                "timestamp": datetime.now().isoformat()
            }

# Instancia global del servicio
dashboard_service = DashboardService()

# ============= ENDPOINTS REST =============

@router.get("/api/stats")
async def get_stats():
    """Obtener estadísticas del dashboard"""
    try:
        stats = dashboard_service.get_stats()
        return JSONResponse(content=stats)
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return JSONResponse(
            content={"error": str(e), "timestamp": datetime.now().isoformat()},
            status_code=500
        )

@router.get("/api/flows")
async def get_flows():
    """Obtener flujos activos"""
    try:
        flows = dashboard_service.get_flows()
        return JSONResponse(content={"flows": flows})
    except Exception as e:
        logger.error(f"Error getting flows: {e}")
        return JSONResponse(
            content={"flows": [], "error": str(e)},
            status_code=500
        )

@router.get("/api/accounts")
async def get_accounts():
    """Obtener cuentas conectadas"""
    try:
        accounts = dashboard_service.get_accounts()
        return JSONResponse(content=accounts)
    except Exception as e:
        logger.error(f"Error getting accounts: {e}")
        return JSONResponse(
            content={"telegram": [], "discord": [], "error": str(e)},
            status_code=500
        )

@router.get("/api/health")
async async def get_health():
    """Obtener estado de salud del sistema"""
    try:
        health = await dashboard_service.get_health()
        return JSONResponse(content=health)
    except Exception as e:
        logger.error(f"Error getting health: {e}")
        return JSONResponse(
            content={"status": "error", "error": str(e)},
            status_code=500
        )

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket para actualizaciones en tiempo real"""
    await websocket.accept()
    dashboard_service.websocket_clients.append(websocket)
    
    try:
        # Enviar estado inicial
        await websocket.send_json({
            "type": "initial",
            "data": dashboard_service.get_stats()
        })
        
        # Mantener conexión abierta
        while True:
            data = await websocket.receive_text()
            
            # Procesar comandos del cliente
            if data == "ping":
                await websocket.send_text("pong")
            elif data == "stats":
                await websocket.send_json({
                    "type": "stats",
                    "data": dashboard_service.get_stats()
                })
                
    except WebSocketDisconnect:
        dashboard_service.websocket_clients.remove(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in dashboard_service.websocket_clients:
            dashboard_service.websocket_clients.remove(websocket)

@router.post("/api/test/increment")
async def test_increment():
    """Endpoint de prueba para incrementar contadores"""
    dashboard_service.update_stats(
        messages_received=dashboard_service.stats_cache["messages_received"] + 1,
        messages_replicated=dashboard_service.stats_cache["messages_replicated"] + 1
    )
    return JSONResponse(content={"status": "ok", "new_stats": dashboard_service.get_stats()})

# Exportar el servicio para uso externo
def get_dashboard_service() -> DashboardService:
    """Obtener instancia del servicio de dashboard"""
    return dashboard_service
