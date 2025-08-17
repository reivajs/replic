#!/usr/bin/env python3
"""
🔧 DASHBOARD FIX COMPLETO
=========================
Solución completa para errores de serialización y WebSocket
"""

from pathlib import Path
import os

def main():
    """Función principal"""
    print("\n" + "="*70)
    print("🔧 FIXING DASHBOARD SERVICE")
    print("="*70 + "\n")
    
    # Crear todos los archivos necesarios
    create_dashboard_service()
    create_json_encoder()
    create_websocket_manager()
    create_dashboard_router()
    update_init_files()
    
    print("\n" + "="*70)
    print("✅ DASHBOARD SERVICE FIXED")
    print("="*70)
    print("\n🚀 Ahora reinicia el servidor: python start_simple.py")

def create_dashboard_service():
    """Crear servicio de dashboard"""
    print("📝 Creando dashboard_service.py...")
    
    content = '''"""Dashboard Service - Modular"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import asyncio
import random
import logging
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class DashboardStats:
    """Stats con serialización automática"""
    messages_received: int = 0
    messages_replicated: int = 0
    messages_filtered: int = 0
    active_flows: int = 0
    total_accounts: int = 0
    webhooks_configured: int = 0
    uptime_seconds: float = 0
    uptime_formatted: str = "0h 0m"
    system_health: str = "operational"
    success_rate: float = 0.0
    avg_latency: int = 0
    errors_today: int = 0
    active_connections: int = 0
    last_update: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a dict serializable"""
        data = asdict(self)
        data['last_update'] = datetime.now().isoformat()
        return data

@dataclass
class ReplicationFlow:
    """Flow con serialización"""
    id: int
    name: str
    source: str
    destination: str
    status: str
    messages_today: int
    last_message: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class DashboardService:
    """Servicio centralizado para dashboard"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.start_time = datetime.now()
        self.stats_cache = DashboardStats()
        self.flows_cache = []
        self.last_cache_update = datetime.now()
        self.cache_ttl = 5
        self.update_lock = asyncio.Lock()
        self._update_task = None
        self._initialized = True
        
        logger.info("Dashboard Service initialized")
    
    async def start(self):
        """Iniciar servicio"""
        if self._update_task is None:
            self._update_task = asyncio.create_task(self._periodic_update())
            logger.info("Dashboard Service started")
    
    async def stop(self):
        """Detener servicio"""
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
            self._update_task = None
            logger.info("Dashboard Service stopped")
    
    async def _periodic_update(self):
        """Actualización periódica"""
        while True:
            try:
                await self._update_stats()
                await asyncio.sleep(self.cache_ttl)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Update error: {e}")
                await asyncio.sleep(self.cache_ttl)
    
    async def _update_stats(self):
        """Actualizar estadísticas"""
        async with self.update_lock:
            uptime = (datetime.now() - self.start_time).total_seconds()
            
            # Simular datos
            self.stats_cache.messages_received += random.randint(0, 3)
            self.stats_cache.messages_replicated += random.randint(0, 2)
            self.stats_cache.uptime_seconds = uptime
            self.stats_cache.uptime_formatted = self._format_uptime(uptime)
            self.stats_cache.success_rate = 95.0 + random.uniform(-2, 2)
            self.stats_cache.avg_latency = 45 + random.randint(-10, 10)
            self.stats_cache.active_connections = random.randint(45, 55)
            self.stats_cache.active_flows = len(self.flows_cache)
            
            # Actualizar flows
            await self._update_flows()
            
            self.last_cache_update = datetime.now()
    
    async def _update_flows(self):
        """Actualizar flows"""
        if not self.flows_cache:
            self.flows_cache = [
                ReplicationFlow(
                    id=1,
                    name="Crypto Signals → Trading Discord",
                    source="Crypto Signals",
                    destination="Trading Server",
                    status="active",
                    messages_today=random.randint(150, 250),
                    last_message=(datetime.now() - timedelta(minutes=random.randint(1, 5))).isoformat()
                ),
                ReplicationFlow(
                    id=2,
                    name="Stock Analysis → Investors Discord",
                    source="Stock Analysis",
                    destination="Investors Server",
                    status="active",
                    messages_today=random.randint(80, 150),
                    last_message=(datetime.now() - timedelta(minutes=random.randint(5, 15))).isoformat()
                )
            ]
        else:
            for flow in self.flows_cache:
                flow.messages_today += random.randint(0, 2)
                flow.last_message = (datetime.now() - timedelta(minutes=random.randint(1, 10))).isoformat()
    
    def _format_uptime(self, seconds: float) -> str:
        """Formatear uptime"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        if hours > 24:
            days = hours // 24
            return f"{days}d {hours % 24}h {minutes}m"
        return f"{hours}h {minutes}m"
    
    async def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas"""
        if (datetime.now() - self.last_cache_update).seconds < self.cache_ttl:
            return self.stats_cache.to_dict()
        
        await self._update_stats()
        return self.stats_cache.to_dict()
    
    async def get_flows(self) -> List[Dict[str, Any]]:
        """Obtener flows"""
        if not self.flows_cache:
            await self._update_flows()
        return [flow.to_dict() for flow in self.flows_cache]
    
    async def get_accounts(self) -> Dict[str, Any]:
        """Obtener cuentas"""
        return {
            "telegram": [{
                "phone": "+1234567890",
                "status": "connected",
                "groups_count": 50,
                "channels_count": 23,
                "last_seen": datetime.now().isoformat()
            }],
            "discord": [{
                "server_name": "Trading Server",
                "webhook_count": 2,
                "status": "active",
                "group_id": "-1001234567890"
            }]
        }
    
    async def get_health(self) -> Dict[str, Any]:
        """Obtener health"""
        return {
            "status": "operational",
            "services": {
                "healthy": 1,
                "total": 1,
                "percentage": 100
            },
            "timestamp": datetime.now().isoformat()
        }

dashboard_service = DashboardService()
'''
    
    file_path = Path("app/services/dashboard_service.py")
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content)
    print("✅ dashboard_service.py creado")

def create_json_encoder():
    """Crear JSON encoder"""
    print("📝 Creando json_encoder.py...")
    
    content = '''"""Custom JSON Encoder"""
import json
from datetime import datetime, date, time, timedelta
from decimal import Decimal
from typing import Any

class CustomJSONEncoder(json.JSONEncoder):
    """Encoder para tipos no serializables"""
    
    def default(self, obj: Any) -> Any:
        if isinstance(obj, (datetime, date, time)):
            return obj.isoformat()
        elif isinstance(obj, timedelta):
            return str(obj)
        elif isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, set):
            return list(obj)
        elif isinstance(obj, bytes):
            return obj.decode('utf-8', errors='ignore')
        elif hasattr(obj, 'to_dict'):
            return obj.to_dict()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        return super().default(obj)

def safe_json_response(data: Any) -> dict:
    """Convertir a JSON seguro"""
    try:
        json.dumps(data, cls=CustomJSONEncoder)
        return data
    except Exception as e:
        return {
            "error": "Serialization error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }
'''
    
    file_path = Path("app/utils/json_encoder.py")
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content)
    print("✅ json_encoder.py creado")

def create_websocket_manager():
    """Crear WebSocket manager"""
    print("📝 Creando enhanced_manager.py...")
    
    content = '''"""WebSocket Manager Enhanced"""
import asyncio
from typing import Dict, Optional
from fastapi import WebSocket
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class EnhancedWebSocketManager:
    """WebSocket manager mejorado"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.connections = {}
        self.max_connections = 100
        self.connection_count = 0
        self._initialized = True
        
        logger.info("WebSocket Manager initialized")
    
    async def connect(self, websocket: WebSocket, client_id: Optional[str] = None):
        """Conectar cliente"""
        if self.connection_count >= self.max_connections:
            await websocket.close(code=1008, reason="Max connections")
            return None
        
        await websocket.accept()
        
        if client_id is None:
            client_id = f"client_{id(websocket)}"
        
        self.connections[client_id] = websocket
        self.connection_count += 1
        
        logger.info(f"Client {client_id} connected (total: {self.connection_count})")
        return client_id
    
    async def disconnect(self, client_id: str):
        """Desconectar cliente"""
        if client_id in self.connections:
            del self.connections[client_id]
            self.connection_count -= 1
            logger.info(f"Client {client_id} disconnected (remaining: {self.connection_count})")
    
    async def send_to_client(self, client_id: str, data: dict):
        """Enviar a cliente"""
        if client_id not in self.connections:
            return False
        
        try:
            from app.utils.json_encoder import CustomJSONEncoder
            message = json.dumps(data, cls=CustomJSONEncoder)
            await self.connections[client_id].send_text(message)
            return True
        except Exception as e:
            logger.error(f"Send error: {e}")
            await self.disconnect(client_id)
            return False

websocket_manager = EnhancedWebSocketManager()
'''
    
    file_path = Path("app/websocket/enhanced_manager.py")
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content)
    print("✅ enhanced_manager.py creado")

def create_dashboard_router():
    """Crear router del dashboard"""
    print("📝 Creando dashboard.py router...")
    
    content = '''"""Dashboard API Router Fixed"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import asyncio
import logging
from datetime import datetime

from app.services.dashboard_service import dashboard_service
from app.websocket.enhanced_manager import websocket_manager
from app.utils.json_encoder import safe_json_response

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/api/stats")
async def get_dashboard_stats():
    """Get dashboard stats"""
    try:
        stats = await dashboard_service.get_stats()
        safe_stats = safe_json_response(stats)
        return JSONResponse(content=safe_stats)
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

@router.get("/api/flows")
async def get_active_flows():
    """Get active flows"""
    try:
        flows = await dashboard_service.get_flows()
        return JSONResponse(content={"flows": flows})
    except Exception as e:
        logger.error(f"Flows error: {e}")
        return JSONResponse(
            content={"flows": []},
            status_code=500
        )

@router.get("/api/accounts")
async def get_accounts():
    """Get accounts"""
    try:
        accounts = await dashboard_service.get_accounts()
        return JSONResponse(content=accounts)
    except Exception as e:
        logger.error(f"Accounts error: {e}")
        return JSONResponse(
            content={"telegram": [], "discord": []},
            status_code=500
        )

@router.get("/api/health")
async def get_system_health():
    """Get health"""
    try:
        health = await dashboard_service.get_health()
        return JSONResponse(content=health)
    except Exception as e:
        logger.error(f"Health error: {e}")
        return JSONResponse(
            content={"status": "unknown"},
            status_code=500
        )

@router.websocket("/ws/dashboard")
async def dashboard_websocket(websocket: WebSocket):
    """Dashboard WebSocket"""
    client_id = await websocket_manager.connect(websocket)
    
    if not client_id:
        return
    
    try:
        while True:
            await asyncio.sleep(3)
            
            stats = await dashboard_service.get_stats()
            
            await websocket_manager.send_to_client(client_id, {
                "type": "stats_update",
                "data": stats,
                "timestamp": datetime.now().isoformat()
            })
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket_manager.disconnect(client_id)
'''
    
    file_path = Path("app/api/v1/dashboard.py")
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content)
    print("✅ dashboard.py router creado")

def update_init_files():
    """Actualizar archivos __init__.py"""
    print("📝 Actualizando archivos __init__.py...")
    
    # Update utils __init__
    utils_init = '''"""Utils Module"""
try:
    from .json_encoder import CustomJSONEncoder, safe_json_response
except ImportError:
    CustomJSONEncoder = None
    safe_json_response = None

__all__ = ['CustomJSONEncoder', 'safe_json_response']
'''
    
    file_path = Path("app/utils/__init__.py")
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(utils_init)
    
    # Update websocket __init__
    ws_init = '''"""WebSocket Module"""
try:
    from .enhanced_manager import websocket_manager
except ImportError:
    websocket_manager = None

__all__ = ['websocket_manager']
'''
    
    file_path = Path("app/websocket/__init__.py")
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(ws_init)
    
    print("✅ Archivos __init__.py actualizados")

if __name__ == "__main__":
    main()