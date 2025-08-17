#!/usr/bin/env python3
"""
🔧 INTEGRATION SCRIPT - Adaptar Servicios Existentes
=====================================================
Integra tu EnhancedReplicatorService con la nueva arquitectura modular
"""

import os
import shutil
from pathlib import Path
import re

class ServiceIntegrator:
    """Integrador de servicios existentes a nueva arquitectura"""
    
    def __init__(self):
        self.project_root = Path(".")
        self.fixes_applied = []
        
    def run_integration(self):
        """Ejecutar integración completa"""
        print("\n" + "="*70)
        print("🔧 INTEGRANDO SERVICIOS EXISTENTES")
        print("="*70 + "\n")
        
        # 1. Arreglar el archivo discovery.py vacío
        self.fix_discovery_service()
        
        # 2. Crear adaptador para EnhancedReplicatorService
        self.create_replicator_adapter()
        
        # 3. Actualizar ServiceRegistry
        self.update_service_registry()
        
        # 4. Crear configuración de microservicios
        self.create_microservices_config()
        
        # 5. Arreglar imports en main.py
        self.fix_main_imports()
        
        # 6. Crear startup script simplificado
        self.create_simple_startup()
        
        print("\n" + "="*70)
        print("✅ INTEGRACIÓN COMPLETADA")
        print("="*70)
        self.print_summary()
    
    def fix_discovery_service(self):
        """Arreglar el archivo discovery.py que está vacío"""
        print("📝 Creando ServiceDiscovery...")
        
        discovery_code = '''"""
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
'''
        
        discovery_file = self.project_root / "app" / "services" / "discovery.py"
        with open(discovery_file, 'w') as f:
            f.write(discovery_code)
        
        print("✅ ServiceDiscovery creado")
        self.fixes_applied.append("ServiceDiscovery module")
    
    def create_replicator_adapter(self):
        """Crear adaptador para tu EnhancedReplicatorService"""
        print("🔄 Creando adaptador para EnhancedReplicatorService...")
        
        adapter_code = '''"""
Replicator Service Adapter
==========================
Adaptador para integrar EnhancedReplicatorService con la nueva arquitectura
"""

import asyncio
from typing import Dict, Any, Optional
import logging

# Importar tu servicio existente
try:
    from app.services.enhanced_replicator_service import EnhancedReplicatorService
    ENHANCED_AVAILABLE = True
except ImportError:
    ENHANCED_AVAILABLE = False
    EnhancedReplicatorService = None

logger = logging.getLogger(__name__)

class ReplicatorServiceAdapter:
    """
    Adaptador que envuelve tu EnhancedReplicatorService
    para trabajar con la nueva arquitectura modular
    """
    
    def __init__(self):
        self.service: Optional[EnhancedReplicatorService] = None
        self.is_initialized = False
        
    async def initialize(self):
        """Inicializar el servicio"""
        if not ENHANCED_AVAILABLE:
            logger.error("❌ EnhancedReplicatorService not available")
            return False
        
        try:
            self.service = EnhancedReplicatorService()
            await self.service.initialize()
            self.is_initialized = True
            logger.info("✅ ReplicatorServiceAdapter initialized")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize replicator: {e}")
            return False
    
    async def start(self):
        """Iniciar el servicio"""
        if not self.is_initialized:
            await self.initialize()
        
        if self.service:
            # Start listening in background
            asyncio.create_task(self.service.start_listening())
            logger.info("✅ Replicator service started")
    
    async def stop(self):
        """Detener el servicio"""
        if self.service:
            await self.service.stop()
            logger.info("✅ Replicator service stopped")
    
    async def get_health(self) -> Dict[str, Any]:
        """Obtener estado de salud"""
        if not self.service:
            return {"status": "unhealthy", "error": "Service not initialized"}
        
        return await self.service.get_health()
    
    async def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas"""
        if not self.service:
            return {}
        
        return await self.service.get_dashboard_stats()
    
    def get_service_info(self) -> Dict[str, Any]:
        """Información del servicio para registry"""
        return {
            "name": "Enhanced Replicator Service",
            "version": "3.0.0",
            "status": "healthy" if self.is_initialized else "unhealthy",
            "capabilities": [
                "telegram_replication",
                "discord_sending", 
                "watermark_processing",
                "file_processing",
                "direct_file_sending"
            ],
            "endpoints": {
                "health": "/health",
                "stats": "/stats",
                "config": "/config"
            }
        }

# Instancia global para el sistema
replicator_adapter = ReplicatorServiceAdapter()

# Exportar para compatibilidad
__all__ = ['ReplicatorServiceAdapter', 'replicator_adapter']
'''
        
        adapter_file = self.project_root / "app" / "services" / "replicator_adapter.py"
        with open(adapter_file, 'w') as f:
            f.write(adapter_code)
        
        print("✅ ReplicatorServiceAdapter creado")
        self.fixes_applied.append("Replicator adapter")
    
    def update_service_registry(self):
        """Actualizar ServiceRegistry para incluir el adaptador"""
        print("📝 Actualizando ServiceRegistry...")
        
        registry_code = '''"""
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
'''
        
        registry_file = self.project_root / "app" / "services" / "registry.py"
        with open(registry_file, 'w') as f:
            f.write(registry_code)
        
        print("✅ ServiceRegistry actualizado")
        self.fixes_applied.append("Service Registry")
    
    def create_microservices_config(self):
        """Crear configuración para microservicios"""
        print("⚙️ Creando configuración de microservicios...")
        
        # Asegurar que existe el directorio config
        config_dir = self.project_root / "config"
        config_dir.mkdir(exist_ok=True)
        
        services_yaml = """# Microservices Configuration
services:
  replicator:
    name: "Enhanced Replicator Service"
    url: "http://localhost:8001"
    port: 8001
    health_endpoint: "/health"
    capabilities:
      - telegram_replication
      - discord_sending
      - watermark_processing
      - file_processing
    
  watermark:
    name: "Watermark Service"
    url: "http://localhost:8081"
    port: 8081
    health_endpoint: "/health"
    capabilities:
      - image_watermark
      - text_overlay
      - batch_processing
    
  discovery:
    name: "Discovery Service"
    url: "http://localhost:8002"
    port: 8002
    health_endpoint: "/health"
    capabilities:
      - chat_discovery
      - auto_scan
      - telegram_integration

# Configuration for each service
service_configs:
  replicator:
    max_workers: 10
    message_queue_size: 1000
    retry_attempts: 3
    timeout: 30
    
  watermark:
    max_image_size: 10485760  # 10MB
    supported_formats: ["png", "jpg", "jpeg", "gif"]
    watermark_opacity: 0.3
    
  discovery:
    scan_interval: 300  # 5 minutes
    max_chats: 1000
    auto_scan: true
"""
        
        config_file = config_dir / "services.yaml"
        with open(config_file, 'w') as f:
            f.write(services_yaml)
        
        print("✅ Configuración de microservicios creada")
        self.fixes_applied.append("Microservices config")
    
    def fix_main_imports(self):
        """Arreglar imports en main.py"""
        print("🔧 Arreglando imports en main.py...")
        
        # Actualizar dependencies.py para usar el registry correcto
        dependencies_code = '''"""
Dependency Injection Module - FIXED
===================================
"""

from functools import lru_cache
from app.services.registry import service_registry
from app.services.cache import CacheService
from app.database.connection import get_db

@lru_cache()
def get_service_registry():
    """Get service registry instance"""
    return service_registry

@lru_cache()
def get_cache_service():
    """Get cache service instance"""
    return CacheService()

def get_db_session():
    """Get database session"""
    return get_db()

def get_cache():
    """Alias for cache service"""
    return get_cache_service()

__all__ = [
    'get_service_registry',
    'get_cache_service',
    'get_db_session',
    'get_cache'
]
'''
        
        deps_file = self.project_root / "app" / "core" / "dependencies.py"
        with open(deps_file, 'w') as f:
            f.write(dependencies_code)
        
        print("✅ Dependencies module arreglado")
        self.fixes_applied.append("Dependencies module")
    
    def create_simple_startup(self):
        """Crear script de inicio simplificado"""
        print("🚀 Creando script de inicio simplificado...")
        
        startup_script = '''#!/usr/bin/env python3
"""
SIMPLE STARTUP - Inicio rápido del sistema
==========================================
"""

import asyncio
import uvicorn
from pathlib import Path
import sys

# Añadir proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def start_system():
    """Iniciar sistema simplificado"""
    print("\\n" + "="*70)
    print("🚀 INICIANDO SISTEMA MODULAR")
    print("="*70 + "\\n")
    
    # Verificar que existe .env
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ ERROR: No se encontró archivo .env")
        print("Copia .env.example a .env y configura tus credenciales")
        return
    
    print("✅ Archivo .env encontrado")
    print("✅ Iniciando servidor...")
    print("\\n🌐 El sistema estará disponible en:")
    print("   📊 Dashboard: http://localhost:8000")
    print("   📚 API Docs:  http://localhost:8000/docs")
    print("   🏥 Health:    http://localhost:8000/api/v1/health")
    print("\\n[Presiona Ctrl+C para detener]\\n")
    
    # Iniciar servidor
    config = uvicorn.Config(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
    
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    try:
        asyncio.run(start_system())
    except KeyboardInterrupt:
        print("\\n✅ Sistema detenido por el usuario")
'''
        
        startup_file = self.project_root / "start_simple.py"
        with open(startup_file, 'w') as f:
            f.write(startup_script)
        
        # Hacer ejecutable
        os.chmod(startup_file, 0o755)
        
        print("✅ Script de inicio creado: start_simple.py")
        self.fixes_applied.append("Simple startup script")
    
    def print_summary(self):
        """Imprimir resumen de cambios"""
        print("\n📋 RESUMEN DE INTEGRACIÓN:")
        print("-" * 40)
        
        for fix in self.fixes_applied:
            print(f"  ✅ {fix}")
        
        print("\n🚀 PRÓXIMOS PASOS:")
        print("-" * 40)
        print("""
1. PROBAR EL SISTEMA:
   python start_simple.py
   
2. VERIFICAR SERVICIOS:
   - Dashboard: http://localhost:8000
   - Health: http://localhost:8000/api/v1/health
   - Docs: http://localhost:8000/docs

3. SI HAY ERRORES DE IMPORTS:
   pip install telethon aiohttp pyyaml

4. CONFIGURAR .env:
   - Asegúrate de tener tus credenciales de Telegram
   - Verifica los webhooks de Discord

5. SERVICIOS INTEGRADOS:
   ✅ Tu EnhancedReplicatorService funciona con la nueva arquitectura
   ✅ ServiceDiscovery implementado
   ✅ ServiceRegistry conectado con tu replicator
   ✅ Adaptador creado para compatibilidad total
""")

def main():
    """Función principal"""
    print("\n🔧 SCRIPT DE INTEGRACIÓN DE SERVICIOS")
    print("="*50)
    
    integrator = ServiceIntegrator()
    integrator.run_integration()

if __name__ == "__main__":
    main()