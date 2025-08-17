"""Dashboard Service - Modular"""
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
