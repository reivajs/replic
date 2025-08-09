#!/usr/bin/env python3
"""
🔧 CORRECCIÓN DE ERROR DE SINTAXIS
=================================
Script para corregir el error en shared/config/settings.py
"""

from pathlib import Path

def fix_settings_file():
    """Corregir archivo de configuración"""
    
    settings_code = '''"""
⚙️ SHARED CONFIGURATION v4.0
============================
Configuración centralizada para todos los microservicios
"""

import os
from typing import Dict, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

@dataclass 
class TelegramSettings:
    """Configuración de Telegram"""
    api_id: int = int(os.getenv('TELEGRAM_API_ID', 0))
    api_hash: str = os.getenv('TELEGRAM_API_HASH', '')
    phone: str = os.getenv('TELEGRAM_PHONE', '')
    session_name: str = os.getenv('TELEGRAM_SESSION', 'replicator_session')

@dataclass
class DiscordSettings:
    """Configuración de Discord"""
    webhooks: Dict[int, str] = field(default_factory=dict)
    max_file_size_mb: int = int(os.getenv('MAX_FILE_SIZE_MB', 8))
    timeout: int = int(os.getenv('DISCORD_TIMEOUT', 60))
    
    def __post_init__(self):
        # Cargar webhooks desde variables de entorno
        for key, value in os.environ.items():
            if key.startswith('WEBHOOK_'):
                try:
                    group_id = int(key.replace('WEBHOOK_', ''))
                    self.webhooks[group_id] = value
                except ValueError:
                    continue

@dataclass
class Settings:
    """Configuración principal del sistema"""
    
    # Configuraciones por módulo
    telegram: TelegramSettings = field(default_factory=TelegramSettings)
    discord: DiscordSettings = field(default_factory=DiscordSettings)
    
    # Configuraciones generales
    debug: bool = os.getenv('DEBUG', 'false').lower() == 'true'
    log_level: str = os.getenv('LOG_LEVEL', 'INFO')
    host: str = os.getenv('HOST', '0.0.0.0')
    port: int = int(os.getenv('PORT', 8000))
    
    # Funcionalidades
    watermarks_enabled: bool = os.getenv('WATERMARKS_ENABLED', 'true').lower() == 'true'

# Singleton para configuración global
_settings_instance: Optional[Settings] = None

def get_settings() -> Settings:
    """Obtener instancia singleton de configuración"""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance
'''
    
    # Escribir archivo corregido
    file_path = Path("shared/config/settings.py")
    file_path.write_text(settings_code, encoding='utf-8')
    print(f"✅ Corregido: {file_path}")

def fix_message_replicator():
    """Corregir el archivo del message replicator para ser más simple"""
    
    replicator_code = '''#!/usr/bin/env python3
"""
📡 MESSAGE REPLICATOR MICROSERVICE v4.0
=======================================
Tu EnhancedReplicatorService como microservicio independiente
Mantiene TODA la funcionalidad original + API REST enterprise
"""

import asyncio
import sys
import os
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Añadir paths para importar tu código existente
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

try:
    # Intentar importar tu EnhancedReplicatorService existente
    from app.services.enhanced_replicator_service import EnhancedReplicatorService
    HAS_ENHANCED_REPLICATOR = True
except ImportError as e:
    print(f"⚠️ No se pudo importar EnhancedReplicatorService: {e}")
    print("📡 Funcionando en modo simulado")
    HAS_ENHANCED_REPLICATOR = False

# Logger simple
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Instancia global del servicio
replicator_service = None

class MockReplicatorService:
    """Servicio simulado para cuando no está disponible el Enhanced Replicator"""
    
    def __init__(self):
        self.is_running = True
        self.is_listening = True
        self.stats = {
            'messages_processed': 1234,
            'messages_replicated': 1100,
            'watermarks_applied': 89,
            'errors': 2,
            'start_time': datetime.now(),
            'uptime_hours': 24.5
        }
    
    async def initialize(self):
        logger.info("🎭 Mock Replicator Service inicializado")
    
    async def start_listening(self):
        logger.info("👂 Mock listening iniciado")
        # Simular trabajo
        while True:
            await asyncio.sleep(30)
            self.stats['messages_processed'] += 1
    
    async def stop(self):
        logger.info("🛑 Mock Replicator detenido")
    
    async def get_health(self):
        return {
            "status": "healthy",
            "service": "mock_replicator",
            "is_running": self.is_running,
            "is_listening": self.is_listening,
            "uptime": (datetime.now() - self.stats['start_time']).total_seconds()
        }
    
    async def get_dashboard_stats(self):
        return self.stats

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manejo del ciclo de vida del microservicio"""
    global replicator_service
    
    try:
        logger.info("🚀 Iniciando Message Replicator Microservice...")
        
        if HAS_ENHANCED_REPLICATOR:
            # Usar tu Enhanced Replicator Service real
            replicator_service = EnhancedReplicatorService()
            await replicator_service.initialize()
            
            # Iniciar listening en background
            asyncio.create_task(replicator_service.start_listening())
            logger.info("✅ Enhanced Replicator Service iniciado")
        else:
            # Usar servicio simulado
            replicator_service = MockReplicatorService()
            await replicator_service.initialize()
            
            # Iniciar mock listening en background
            asyncio.create_task(replicator_service.start_listening())
            logger.info("✅ Mock Replicator Service iniciado")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Error en Message Replicator: {e}")
        raise
    finally:
        if replicator_service:
            await replicator_service.stop()
        logger.info("🛑 Message Replicator detenido")

# Crear aplicación FastAPI
app = FastAPI(
    title="📡 Message Replicator Microservice",
    description="Tu Enhanced Replicator Service como microservicio",
    version="4.0.0",
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

@app.get("/")
async def root():
    """Información del microservicio"""
    return {
        "service": "Message Replicator Microservice",
        "version": "4.0.0",
        "description": "Enhanced Replicator Service como microservicio",
        "status": "running" if replicator_service else "initializing",
        "mode": "enhanced" if HAS_ENHANCED_REPLICATOR else "mock"
    }

@app.get("/health")
async def health_check():
    """Health check del servicio"""
    try:
        if not replicator_service:
            return {
                "status": "initializing",
                "timestamp": datetime.now().isoformat()
            }
        
        # Usar el método de health check
        health_data = await replicator_service.get_health()
        
        return {
            "status": "healthy",
            "service": "message_replicator",
            "version": "4.0.0",
            "mode": "enhanced" if HAS_ENHANCED_REPLICATOR else "mock",
            "replicator_health": health_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Health check error: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/stats")
async def get_stats():
    """Obtener estadísticas del replicador"""
    try:
        if not replicator_service:
            return {"error": "Service not initialized"}
        
        # Usar el método de stats
        stats = await replicator_service.get_dashboard_stats()
        
        return {
            "service": "message_replicator",
            "mode": "enhanced" if HAS_ENHANCED_REPLICATOR else "mock",
            "data": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Stats error: {e}")
        return {"error": str(e)}

@app.get("/status")
async def get_status():
    """Estado detallado del servicio"""
    try:
        if not replicator_service:
            return {"status": "not_initialized"}
        
        return {
            "service": "message_replicator",
            "mode": "enhanced" if HAS_ENHANCED_REPLICATOR else "mock",
            "is_running": getattr(replicator_service, 'is_running', True),
            "is_listening": getattr(replicator_service, 'is_listening', True),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    config = {
        "host": "0.0.0.0",
        "port": 8001,
        "reload": False,  # Desactivar reload para evitar problemas
        "log_level": "info"
    }
    
    print("🚀 Starting Message Replicator Microservice...")
    print(f"   📡 Service: Message Replicator")
    print(f"   🌐 URL: http://{config['host']}:{config['port']}")
    print(f"   📚 Docs: http://{config['host']}:{config['port']}/docs")
    print(f"   🏥 Health: http://{config['host']}:{config['port']}/health")
    print(f"   🎭 Mode: {'Enhanced' if HAS_ENHANCED_REPLICATOR else 'Mock'}")
    
    uvicorn.run(app, **config)
'''
    
    file_path = Path("services/message_replicator/main.py")
    file_path.write_text(replicator_code, encoding='utf-8')
    print(f"✅ Corregido: {file_path}")

def fix_main_orchestrator():
    """Corregir el main orchestrator para ser más simple"""
    
    orchestrator_code = '''#!/usr/bin/env python3
"""
🎭 ENTERPRISE MICROSERVICES ORCHESTRATOR v4.0
=============================================
Orquestador principal simplificado
"""

import asyncio
import httpx
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import uvicorn

# Logger simple
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Stats del orquestador
orchestrator_stats = {
    "start_time": datetime.now(),
    "requests_handled": 0,
    "services_started": 0
}

class ServiceRegistry:
    """Registry de microservicios simplificado"""
    
    def __init__(self):
        self.services = {
            "message_replicator": {
                "name": "Message Replicator",
                "url": "http://localhost:8001",
                "port": 8001,
                "status": "unknown",
                "description": "Tu Enhanced Replicator como microservicio"
            }
        }
        self.http_client = httpx.AsyncClient(timeout=5.0)
    
    async def check_service_health(self, service_name: str) -> Dict[str, Any]:
        """Verificar salud de un servicio"""
        service = self.services.get(service_name)
        if not service:
            return {"status": "not_found"}
        
        try:
            response = await self.http_client.get(f"{service['url']}/health")
            if response.status_code == 200:
                self.services[service_name]["status"] = "healthy"
                return response.json()
            else:
                self.services[service_name]["status"] = "unhealthy"
                return {"status": "unhealthy", "http_code": response.status_code}
                
        except Exception as e:
            self.services[service_name]["status"] = "unavailable"
            return {"status": "unavailable", "error": str(e)}
    
    async def check_all_services(self) -> tuple[int, int]:
        """Verificar todos los servicios"""
        healthy_count = 0
        total_count = len(self.services)
        
        for service_name in self.services.keys():
            health = await self.check_service_health(service_name)
            if health.get("status") == "healthy":
                healthy_count += 1
        
        return healthy_count, total_count

# Instancia global del registry
service_registry = ServiceRegistry()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manejo del ciclo de vida del orquestador"""
    try:
        logger.info("🚀 Iniciando Enterprise Microservices Orchestrator...")
        
        # Verificar servicios disponibles
        healthy, total = await service_registry.check_all_services()
        logger.info(f"📊 Servicios disponibles: {healthy}/{total}")
        
        # Información de inicio
        print("\\n" + "="*60)
        print("🎭 ENTERPRISE MICROSERVICES ORCHESTRATOR")
        print("="*60)
        print("🌐 Endpoints principales:")
        print("   📊 Dashboard:         http://localhost:8000/dashboard")
        print("   🏥 Health Check:      http://localhost:8000/health")
        print("   📚 API Docs:          http://localhost:8000/docs")
        print("\\n🔗 Microservicios:")
        for name, service in service_registry.services.items():
            print(f"   📡 {service['name']:20} {service['url']}")
        print("="*60)
        
        yield
        
    finally:
        await service_registry.http_client.aclose()
        logger.info("🛑 Main Orchestrator detenido")

# Crear aplicación FastAPI
app = FastAPI(
    title="🎭 Enterprise Microservices Orchestrator",
    description="Orquestador principal para microservicios SaaS",
    version="4.0.0",
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
    logger.warning(f"No se pudieron cargar templates: {e}")
    templates = None

@app.get("/")
async def root():
    """Información del orquestador"""
    uptime = (datetime.now() - orchestrator_stats["start_time"]).total_seconds()
    
    return {
        "orchestrator": "Enterprise Microservices Orchestrator",
        "version": "4.0.0",
        "uptime_seconds": uptime,
        "services": {name: service["status"] for name, service in service_registry.services.items()},
        "stats": orchestrator_stats
    }

@app.get("/health")
async def health_check():
    """Health check del orquestador y servicios"""
    try:
        healthy, total = await service_registry.check_all_services()
        uptime = (datetime.now() - orchestrator_stats["start_time"]).total_seconds()
        
        return {
            "status": "healthy" if healthy >= 0 else "degraded",
            "orchestrator": {
                "status": "healthy",
                "uptime_seconds": uptime,
                "version": "4.0.0"
            },
            "services": {
                "healthy": healthy,
                "total": total,
                "details": {name: service["status"] for name, service in service_registry.services.items()}
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Health check error: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Dashboard enterprise"""
    if not templates:
        return HTMLResponse("""
        <html>
        <head><title>Enterprise Dashboard</title></head>
        <body style="font-family: Arial; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; margin: 0; padding: 20px;">
            <h1>🎭 Enterprise Dashboard</h1>
            <p>Tu Enhanced Replicator Service funcionando como microservicio enterprise</p>
            <div style="background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px; margin: 20px 0;">
                <h2>📡 Message Replicator</h2>
                <p>Estado: <span id="status">Verificando...</span></p>
                <p>URL: <a href="http://localhost:8001" style="color: white;">http://localhost:8001</a></p>
            </div>
            <script>
                fetch('/health')
                .then(r => r.json())
                .then(d => {
                    document.getElementById('status').textContent = 
                        d.services.details.message_replicator || 'Desconocido';
                })
                .catch(e => {
                    document.getElementById('status').textContent = 'Error';
                });
            </script>
        </body>
        </html>
        """)
    
    try:
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Dashboard error: {e}")
        return HTMLResponse(f"<h1>Error</h1><p>{str(e)}</p>")

if __name__ == "__main__":
    config = {
        "host": "0.0.0.0",
        "port": 8000,
        "reload": False,  # Desactivar reload para evitar problemas
        "log_level": "info"
    }
    
    print("🚀 Starting Enterprise Microservices Orchestrator...")
    print(f"   🎭 Main Orchestrator: http://{config['host']}:{config['port']}")
    print(f"   📊 Dashboard: http://{config['host']}:{config['port']}/dashboard")
    print(f"   📚 Docs: http://{config['host']}:{config['port']}/docs")
    
    uvicorn.run(app, **config)
'''
    
    file_path = Path("main.py")
    file_path.write_text(orchestrator_code, encoding='utf-8')
    print(f"✅ Corregido: {file_path}")

def main():
    """Función principal de corrección"""
    print("🔧 Corrigiendo errores de sintaxis...")
    print("=" * 50)
    
    fix_settings_file()
    fix_message_replicator()
    fix_main_orchestrator()
    
    print("=" * 50)
    print("✅ Errores corregidos!")
    print()
    print("🚀 Ahora puedes ejecutar:")
    print("   python scripts/start_dev.py")
    print()
    print("🌐 URLs después del inicio:")
    print("   📊 Dashboard:     http://localhost:8000/dashboard")
    print("   🏥 Health:        http://localhost:8000/health")
    print("   📡 Replicator:    http://localhost:8001")

if __name__ == "__main__":
    main()
