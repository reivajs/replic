"""
Service Registry Module - FIXED
===============================
Registry centralizado con soporte para EnhancedReplicatorService
"""

import asyncio
import httpx
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import yaml
import logging

logger = logging.getLogger(__name__)

@dataclass
class ServiceInfo:
    """Información de servicio"""
    name: str
    url: str
    port: int
    health_endpoint: str = "/health"
    status: str = "unknown"
    capabilities: List[str] = None

class ServiceRegistry:
    """Registry de servicios mejorado"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path
        self.services: Dict[str, ServiceInfo] = {}
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        # Servicios por defecto
        self._init_default_services()
        
        # Adaptador del replicator
        self.replicator_adapter = None
        
    def _init_default_services(self):
        """Inicializar servicios por defecto"""
        self.services = {
            "replicator": ServiceInfo(
                name="Enhanced Replicator",
                url="http://localhost:8001",
                port=8001,
                capabilities=["replication", "telegram", "discord"]
            ),
            "watermark": ServiceInfo(
                name="Watermark Service",
                url="http://localhost:8081",
                port=8081,
                capabilities=["watermarks", "image_processing"]
            ),
            "discovery": ServiceInfo(
                name="Discovery Service",
                url="http://localhost:8002",
                port=8002,
                capabilities=["chat_discovery"]
            )
        }
    
    async def initialize(self):
        """Inicializar registry y servicios"""
        logger.info("🚀 Initializing Service Registry...")
        
        # Intentar cargar configuración si existe
        if self.config_path:
            await self._load_config()
        
        # Inicializar adaptador del replicator
        try:
            from app.services.replicator_adapter import replicator_adapter
            self.replicator_adapter = replicator_adapter
            await self.replicator_adapter.initialize()
            logger.info("✅ Replicator adapter initialized in registry")
        except Exception as e:
            logger.error(f"❌ Could not initialize replicator adapter: {e}")
    
    async def _load_config(self):
        """Cargar configuración desde archivo"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
                
            for name, details in config.get('services', {}).items():
                self.services[name] = ServiceInfo(**details)
                
            logger.info(f"✅ Loaded {len(self.services)} services from config")
        except Exception as e:
            logger.warning(f"Could not load config: {e}")
    
    async def check_service_health(self, service_name: str) -> Dict[str, Any]:
        """Verificar salud de un servicio"""
        # Para el replicator, usar el adaptador
        if service_name == "replicator" and self.replicator_adapter:
            return await self.replicator_adapter.get_health()
        
        # Para otros servicios, hacer HTTP check
        service = self.services.get(service_name)
        if not service:
            return {"status": "not_found"}
        
        try:
            response = await self.http_client.get(
                f"{service.url}{service.health_endpoint}"
            )
            if response.status_code == 200:
                service.status = "healthy"
                return {"status": "healthy", "data": response.json()}
            else:
                service.status = "unhealthy"
                return {"status": "unhealthy", "code": response.status_code}
        except Exception as e:
            service.status = "error"
            return {"status": "error", "error": str(e)}
    
    async def get_service_stats(self, service_name: str) -> Dict[str, Any]:
        """Obtener estadísticas de un servicio"""
        # Para el replicator, usar el adaptador
        if service_name == "replicator" and self.replicator_adapter:
            return await self.replicator_adapter.get_stats()
        
        # Para otros servicios
        service = self.services.get(service_name)
        if not service:
            return {}
        
        try:
            response = await self.http_client.get(f"{service.url}/stats")
            if response.status_code == 200:
                return response.json()
        except:
            pass
        
        return {}
    
    async def check_all_services(self) -> tuple[int, int]:
        """Verificar todos los servicios"""
        healthy = 0
        total = len(self.services)
        
        for service_name in self.services:
            health = await self.check_service_health(service_name)
            if health.get("status") == "healthy":
                healthy += 1
        
        return healthy, total
    
    async def start_services(self):
        """Iniciar servicios gestionados"""
        if self.replicator_adapter:
            await self.replicator_adapter.start()
            logger.info("✅ Replicator service started from registry")
    
    async def stop_services(self):
        """Detener servicios gestionados"""
        if self.replicator_adapter:
            await self.replicator_adapter.stop()
            logger.info("✅ Replicator service stopped from registry")
    
    async def cleanup(self):
        """Limpiar recursos"""
        await self.stop_services()
        await self.http_client.aclose()

# Instancia global
service_registry = ServiceRegistry()

__all__ = ['ServiceRegistry', 'service_registry', 'ServiceInfo']
