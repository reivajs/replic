"""
Service Discovery Module
========================
Auto-discovery de servicios para arquitectura modular
"""

import asyncio
import httpx
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class DiscoveredService:
    """Información de servicio descubierto"""
    name: str
    url: str
    port: int
    health_endpoint: str = "/health"
    status: str = "unknown"
    version: Optional[str] = None
    capabilities: List[str] = None

class ServiceDiscovery:
    """
    Service Discovery simplificado para desarrollo
    En producción usar Consul/Etcd/Zookeeper
    """
    
    def __init__(self, consul_host: str = "localhost", consul_port: int = 8500):
        self.consul_host = consul_host
        self.consul_port = consul_port
        self.discovered_services: Dict[str, DiscoveredService] = {}
        self.http_client = httpx.AsyncClient(timeout=10.0)
        
        # Servicios conocidos para desarrollo
        self.known_services = {
            "replicator": DiscoveredService(
                name="Enhanced Replicator",
                url="http://localhost:8001",
                port=8001,
                capabilities=["telegram", "discord", "replication"]
            ),
            "watermark": DiscoveredService(
                name="Watermark Service",
                url="http://localhost:8081",
                port=8081,
                capabilities=["image_processing", "watermarks"]
            ),
            "discovery": DiscoveredService(
                name="Discovery Service",
                url="http://localhost:8002",
                port=8002,
                capabilities=["chat_discovery", "auto_scan"]
            )
        }
    
    async def discover_all(self) -> List[Dict[str, Any]]:
        """Descubrir todos los servicios disponibles"""
        services = []
        
        # En desarrollo, usar servicios conocidos
        for service_name, service in self.known_services.items():
            # Check if service is running
            is_healthy = await self.health_check(service)
            service.status = "healthy" if is_healthy else "unhealthy"
            
            services.append({
                "name": service.name,
                "url": service.url,
                "port": service.port,
                "status": service.status,
                "capabilities": service.capabilities or []
            })
        
        return services
    
    async def health_check(self, service: DiscoveredService) -> bool:
        """Verificar salud de un servicio"""
        try:
            response = await self.http_client.get(
                f"{service.url}{service.health_endpoint}",
                timeout=5.0
            )
            return response.status_code == 200
        except:
            return False
    
    async def register_service(self, name: str, url: str, port: int, capabilities: List[str] = None):
        """Registrar un nuevo servicio"""
        self.known_services[name] = DiscoveredService(
            name=name,
            url=url,
            port=port,
            capabilities=capabilities or []
        )
        logger.info(f"✅ Service registered: {name} at {url}")
    
    async def deregister_service(self, name: str):
        """Desregistrar un servicio"""
        if name in self.known_services:
            del self.known_services[name]
            logger.info(f"❌ Service deregistered: {name}")
    
    async def get_service(self, name: str) -> Optional[DiscoveredService]:
        """Obtener información de un servicio específico"""
        return self.known_services.get(name)
    
    async def close(self):
        """Cerrar conexiones"""
        await self.http_client.aclose()

# Exportar para compatibilidad
__all__ = ['ServiceDiscovery', 'DiscoveredService']
