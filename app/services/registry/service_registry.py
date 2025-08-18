"""
Service Registry - Arquitectura de Microservicios
=================================================
Gestión centralizada de servicios para Zero Cost SaaS
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from abc import ABC, abstractmethod
import asyncio
from enum import Enum

from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class ServiceStatus(Enum):
    """Estados posibles de un servicio"""
    STARTING = "starting"
    RUNNING = "running"
    DEGRADED = "degraded"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"

class BaseService(ABC):
    """Clase base para todos los servicios"""
    
    def __init__(self, name: str):
        self.name = name
        self.status = ServiceStatus.STOPPED
        self.start_time = None
        self.health_check_interval = 30
        self.metrics = {}
        
    @abstractmethod
    async def start(self):
        """Iniciar servicio"""
        pass
        
    @abstractmethod
    async def stop(self):
        """Detener servicio"""
        pass
        
    @abstractmethod
    async def health_check(self) -> bool:
        """Verificar salud del servicio"""
        pass
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Obtener métricas del servicio"""
        return {
            "name": self.name,
            "status": self.status.value,
            "uptime": self.get_uptime(),
            "metrics": self.metrics
        }
    
    def get_uptime(self) -> float:
        """Obtener tiempo de actividad en segundos"""
        if self.start_time:
            return (datetime.now() - self.start_time).total_seconds()
        return 0

class ServiceRegistry:
    """
    Registry central de microservicios
    Maneja registro, discovery y health checks
    """
    
    def __init__(self):
        self.services: Dict[str, BaseService] = {}
        self.start_time = datetime.now()
        self._health_check_task = None
        logger.info("✅ Service Registry initialized")
    
    def register(self, service: BaseService) -> bool:
        """Registrar un nuevo servicio"""
        try:
            if service.name in self.services:
                logger.warning(f"Service {service.name} already registered")
                return False
                
            self.services[service.name] = service
            logger.info(f"✅ Service registered: {service.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register service {service.name}: {e}")
            return False
    
    def unregister(self, service_name: str) -> bool:
        """Desregistrar un servicio"""
        if service_name in self.services:
            del self.services[service_name]
            logger.info(f"Service unregistered: {service_name}")
            return True
        return False
    
    def get_service(self, name: str) -> Optional[BaseService]:
        """Obtener servicio por nombre"""
        return self.services.get(name)
    
    def list_services(self) -> List[str]:
        """Listar todos los servicios registrados"""
        return list(self.services.keys())
    
    async def start_all(self):
        """Iniciar todos los servicios registrados"""
        logger.info("Starting all registered services...")
        
        tasks = []
        for service in self.services.values():
            tasks.append(self._start_service(service))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Iniciar health checks
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        
        # Reportar resultados
        success = sum(1 for r in results if r is True)
        logger.info(f"✅ Started {success}/{len(self.services)} services")
    
    async def stop_all(self):
        """Detener todos los servicios"""
        logger.info("Stopping all services...")
        
        # Cancelar health checks
        if self._health_check_task:
            self._health_check_task.cancel()
        
        tasks = []
        for service in self.services.values():
            tasks.append(self._stop_service(service))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("✅ All services stopped")
    
    async def _start_service(self, service: BaseService) -> bool:
        """Iniciar un servicio individual"""
        try:
            service.status = ServiceStatus.STARTING
            await service.start()
            service.status = ServiceStatus.RUNNING
            service.start_time = datetime.now()
            logger.info(f"✅ Service started: {service.name}")
            return True
            
        except Exception as e:
            service.status = ServiceStatus.ERROR
            logger.error(f"Failed to start {service.name}: {e}")
            return False
    
    async def _stop_service(self, service: BaseService) -> bool:
        """Detener un servicio individual"""
        try:
            service.status = ServiceStatus.STOPPING
            await service.stop()
            service.status = ServiceStatus.STOPPED
            logger.info(f"Service stopped: {service.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping {service.name}: {e}")
            return False
    
    async def _health_check_loop(self):
        """Loop de health checks periódicos"""
        while True:
            try:
                await asyncio.sleep(30)
                await self.check_all_health()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
    
    async def check_all_health(self) -> Dict[str, bool]:
        """Verificar salud de todos los servicios"""
        results = {}
        
        for name, service in self.services.items():
            try:
                is_healthy = await service.health_check()
                results[name] = is_healthy
                
                # Actualizar estado basado en salud
                if service.status == ServiceStatus.RUNNING:
                    if not is_healthy:
                        service.status = ServiceStatus.DEGRADED
                elif service.status == ServiceStatus.DEGRADED:
                    if is_healthy:
                        service.status = ServiceStatus.RUNNING
                        
            except Exception as e:
                logger.error(f"Health check failed for {name}: {e}")
                results[name] = False
                service.status = ServiceStatus.ERROR
        
        return results
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Obtener estado completo del sistema"""
        health = await self.check_all_health()
        
        return {
            "registry": {
                "uptime": (datetime.now() - self.start_time).total_seconds(),
                "services_count": len(self.services),
                "healthy_count": sum(1 for h in health.values() if h)
            },
            "services": {
                name: {
                    "status": service.status.value,
                    "healthy": health.get(name, False),
                    "uptime": service.get_uptime()
                }
                for name, service in self.services.items()
            },
            "timestamp": datetime.now().isoformat()
        }

# Singleton global
_registry_instance = None

def get_registry() -> ServiceRegistry:
    """Obtener instancia singleton del registry"""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = ServiceRegistry()
    return _registry_instance
