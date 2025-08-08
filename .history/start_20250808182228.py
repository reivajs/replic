#!/usr/bin/env python3
"""
🚀 MIGRACIÓN COMPLETA A MICROSERVICIOS - CORREGIDA
================================================
Script para migrar tu proyecto actual a arquitectura microservicios
SIN ERRORES DE INDENTACIÓN

EJECUTAR: python migrate_fixed.py
"""

import os
import sys
import shutil
from pathlib import Path

def create_file(file_path: Path, content: str):
    """Crear archivo con contenido"""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding='utf-8')
    print(f"   ✅ Creado: {file_path}")

def backup_original_files():
    """Crear backup de archivos originales"""
    print("💾 Creando backup de archivos originales...")
    
    backup_dir = Path("backup_original")
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
    
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    files_to_backup = [
        "main.py",
        "app/services/enhanced_replicator_service.py",
        "app/config/settings.py",
        "app/api/routes.py", 
        "app/api/websocket.py",
        ".env"
    ]
    
    for file_path in files_to_backup:
        src = Path(file_path)
        if src.exists():
            dst = backup_dir / file_path
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print(f"   📄 Respaldado: {file_path}")

def create_directory_structure():
    """Crear estructura de directorios"""
    print("📁 Creando estructura de microservicios...")
    
    directories = [
        "services/message_replicator/src",
        "services/analytics/src", 
        "shared/config",
        "shared/utils",
        "frontend/templates",
        "frontend/static",
        "database",
        "scripts",
        "logs",
        "temp"
    ]
    
    for directory in directories:
        dir_path = Path(directory)
        dir_path.mkdir(parents=True, exist_ok=True)
        
        if any(part in directory for part in ['src', 'shared', 'services']):
            init_file = dir_path / "__init__.py"
            init_file.write_text("")

def create_shared_config():
    """Crear configuración compartida"""
    print("⚙️ Creando configuración compartida...")
    
    shared_config = '''#!/usr/bin/env python3
"""
⚙️ CONFIGURACIÓN MICROSERVICIOS v3.0
"""

import os
from typing import Dict
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

@dataclass 
class TelegramSettings:
    api_id: int = int(os.getenv('TELEGRAM_API_ID', 0))
    api_hash: str = os.getenv('TELEGRAM_API_HASH', '')
    phone: str = os.getenv('TELEGRAM_PHONE', '')
    session_name: str = os.getenv('TELEGRAM_SESSION', 'replicator_session')

@dataclass
class DiscordSettings:
    webhooks: Dict[int, str] = field(default_factory=dict)
    max_file_size_mb: int = int(os.getenv('MAX_FILE_SIZE_MB', 8))
    timeout: int = int(os.getenv('DISCORD_TIMEOUT', 60))
    
    def __post_init__(self):
        for key, value in os.environ.items():
            if key.startswith('WEBHOOK_'):
                try:
                    group_id = int(key.replace('WEBHOOK_', ''))
                    self.webhooks[group_id] = value
                except ValueError:
                    continue

@dataclass
class DatabaseSettings:
    url: str = os.getenv('DATABASE_URL', 'sqlite:///./database/replicator.db')
    echo: bool = os.getenv('DATABASE_ECHO', 'false').lower() == 'true'

@dataclass
class Settings:
    telegram: TelegramSettings = field(default_factory=TelegramSettings)
    discord: DiscordSettings = field(default_factory=DiscordSettings)
    database: DatabaseSettings = field(default_factory=DatabaseSettings)
    
    debug: bool = os.getenv('DEBUG', 'false').lower() == 'true'
    log_level: str = os.getenv('LOG_LEVEL', 'INFO')
    host: str = os.getenv('HOST', '0.0.0.0')
    port: int = int(os.getenv('PORT', 8000))
    watermarks_enabled: bool = os.getenv('WATERMARKS_ENABLED', 'true').lower() == 'true'
    
    @property
    def telegram_api_id(self) -> int:
        return self.telegram.api_id
    
    @property  
    def telegram_api_hash(self) -> str:
        return self.telegram.api_hash
    
    @property
    def telegram_phone(self) -> str:
        return self.telegram.phone

_settings = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

settings = get_settings()
'''
    
    create_file(Path("shared/config/settings.py"), shared_config)

def create_shared_logger():
    """Crear logger compartido"""
    print("📝 Creando logger compartido...")
    
    shared_logger = '''#!/usr/bin/env python3
"""
📝 SHARED LOGGER
"""

import logging
import sys
from pathlib import Path

def setup_logger(name: str, level: str = "INFO", service_name: str = None) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    if logger.handlers:
        return logger
    
    formatter = logging.Formatter(
        f'%(asctime)s - {service_name or name} - %(levelname)s - %(message)s'
    )
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    service = service_name or name.split('.')[0]
    log_file = log_dir / f"{service}.log"
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger
'''
    
    create_file(Path("shared/utils/logger.py"), shared_logger)

def create_message_replicator_microservice():
    """Crear microservicio del Message Replicator"""
    print("📡 Creando Message Replicator Microservice...")
    
    microservice_code = '''#!/usr/bin/env python3
"""
📡 MESSAGE REPLICATOR MICROSERVICE v3.0
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from app.services.enhanced_replicator_service import EnhancedReplicatorService
    from app.config.settings import get_settings
    from app.utils.logger import setup_logger
    ORIGINAL_SERVICE_AVAILABLE = True
except ImportError:
    from shared.config.settings import get_settings
    from shared.utils.logger import setup_logger
    ORIGINAL_SERVICE_AVAILABLE = False

logger = setup_logger(__name__, service_name="message-replicator")
settings = get_settings()

replicator_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global replicator_service
    
    logger.info("🚀 Iniciando Message Replicator Microservice...")
    
    try:
        if ORIGINAL_SERVICE_AVAILABLE:
            replicator_service = EnhancedReplicatorService()
            success = await replicator_service.initialize()
            
            if success:
                asyncio.create_task(replicator_service.start_listening())
                logger.info("✅ Enhanced Replicator Service inicializado")
            else:
                logger.error("❌ Error inicializando Enhanced Replicator Service")
        else:
            logger.warning("⚠️ Enhanced Replicator Service no disponible - modo degradado")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Error en lifecycle: {e}")
        raise
    finally:
        if replicator_service:
            await replicator_service.stop()
        logger.info("🛑 Message Replicator Microservice detenido")

app = FastAPI(
    title="📡 Message Replicator Microservice",
    description="Tu Enhanced Replicator Service como microservicio enterprise",
    version="3.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True, 
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "service": "Message Replicator Microservice",
        "version": "3.0.0",
        "description": "Enhanced Replicator Service convertido a microservicio",
        "original_service_available": ORIGINAL_SERVICE_AVAILABLE
    }

@app.get("/health")
async def health_check():
    try:
        if not replicator_service:
            return {
                "status": "unhealthy",
                "reason": "Service not initialized",
                "timestamp": datetime.now().isoformat()
            }
        
        if hasattr(replicator_service, 'get_health'):
            health_data = await replicator_service.get_health()
        else:
            health_data = {
                "status": "healthy",
                "service_running": True
            }
        
        health_data.update({
            "microservice": "message-replicator",
            "port": 8001,
            "original_service": ORIGINAL_SERVICE_AVAILABLE
        })
        
        return health_data
        
    except Exception as e:
        logger.error(f"❌ Health check error: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/dashboard-data")
async def get_dashboard_data():
    try:
        if not replicator_service:
            return {"error": "Service not available"}
        
        if hasattr(replicator_service, 'get_dashboard_stats'):
            dashboard_data = await replicator_service.get_dashboard_stats()
        else:
            dashboard_data = {
                "overview": {
                    "messages_received": 0,
                    "messages_replicated": 0,
                    "success_rate": 100.0
                }
            }
        
        return {
            "service_name": "Message Replicator",
            "data": dashboard_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Dashboard data error: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    config = {
        "host": "0.0.0.0",
        "port": 8001,
        "reload": True,
        "log_level": "info"
    }
    
    print("🚀 Starting Message Replicator Microservice...")
    print(f"   📡 Service: Message Replicator")
    print(f"   🌐 URL: http://{config['host']}:{config['port']}")
    print(f"   📚 Docs: http://{config['host']}:{config['port']}/docs")
    print(f"   🏥 Health: http://{config['host']}:{config['port']}/health")
    
    uvicorn.run(app, **config)
'''
    
    create_file(Path("services/message_replicator/main.py"), microservice_code)

def create_analytics_service():
    """Crear Analytics Service"""
    print("📊 Creando Analytics Service...")
    
    analytics_code = '''#!/usr/bin/env python3
"""
📊 ANALYTICS MICROSERVICE v3.0
"""

import sqlite3
from datetime import datetime
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from shared.utils.logger import setup_logger

logger = setup_logger(__name__, service_name="analytics")

class AnalyticsDB:
    def __init__(self, db_path: str = "database/analytics.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        Path("database").mkdir(exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        
        conn.execute('''
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            service_name TEXT NOT NULL,
            metric_name TEXT NOT NULL,
            metric_value REAL NOT NULL,
            group_id INTEGER,
            metadata TEXT
        )
        ''')
        
        conn.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            event_type TEXT NOT NULL,
            service_name TEXT NOT NULL,
            group_id INTEGER,
            data TEXT
        )
        ''')
        
        conn.commit()
        conn.close()

analytics_db = AnalyticsDB()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("📊 Iniciando Analytics Microservice...")
    yield
    logger.info("🛑 Analytics Microservice detenido")

app = FastAPI(
    title="📊 Analytics Microservice",
    description="Servicio de analytics para SaaS",
    version="3.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "service": "Analytics Microservice",
        "version": "3.0.0",
        "description": "Servicio de analytics y métricas para SaaS"
    }

@app.get("/health")
async def health_check():
    try:
        conn = sqlite3.connect(analytics_db.db_path)
        conn.execute("SELECT 1").fetchone()
        conn.close()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/dashboard-data")
async def get_dashboard_data():
    try:
        return {
            "service_name": "Analytics",
            "data": {
                "metrics_collected": 0,
                "events_processed": 0,
                "active_groups": 0
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    config = {
        "host": "0.0.0.0",
        "port": 8002,
        "reload": True,
        "log_level": "info"
    }
    
    print("📊 Starting Analytics Microservice...")
    uvicorn.run(app, **config)
'''
    
    create_file(Path("services/analytics/main.py"), analytics_code)

def create_main_orchestrator():
    """Crear main.py orquestador"""
    print("🎭 Creando Main Orchestrator...")
    
    main_code = '''#!/usr/bin/env python3
"""
🎭 MAIN.PY ORQUESTRADOR ENTERPRISE v3.0
"""

import asyncio
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import httpx

from shared.config.settings import get_settings
from shared.utils.logger import setup_logger

settings = get_settings()
logger = setup_logger(__name__, service_name="orchestrator")

class ServiceRegistry:
    def __init__(self):
        self.services: Dict[str, Dict] = {
            "message-replicator": {
                "name": "Message Replicator",
                "url": "http://localhost:8001",
                "status": "unknown"
            },
            "analytics": {
                "name": "Analytics Service",
                "url": "http://localhost:8002",
                "status": "unknown"
            }
        }
        self.http_client = httpx.AsyncClient(timeout=10.0)
    
    async def check_service_health(self, service_name: str) -> bool:
        try:
            service = self.services.get(service_name)
            if not service:
                return False
            
            response = await self.http_client.get(f"{service['url']}/health")
            
            if response.status_code == 200:
                service["status"] = "healthy"
                return True
            else:
                service["status"] = "unhealthy"
                return False
                
        except Exception:
            self.services[service_name]["status"] = "unreachable"
            return False
    
    async def check_all_services(self):
        tasks = [self.check_service_health(name) for name in self.services.keys()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        healthy_count = sum(1 for result in results if result is True)
        logger.info(f"🏥 Health check: {healthy_count}/{len(self.services)} servicios saludables")
        
        return healthy_count, len(self.services)

service_registry = ServiceRegistry()

orchestrator_stats = {
    "start_time": datetime.now(),
    "requests_proxied": 0,
    "health_checks_performed": 0
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🎭 Iniciando Main Orchestrator Enterprise...")
    
    try:
        healthy, total = await service_registry.check_all_services()
        logger.info(f"📊 Servicios encontrados: {healthy}/{total} saludables")
        
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

app = FastAPI(
    title="🎭 Enterprise Microservices Orchestrator",
    description="Orquestador principal para microservicios SaaS",
    version="3.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
    templates = Jinja2Templates(directory="frontend/templates")
except:
    templates = None

@app.get("/")
async def root():
    uptime = (datetime.now() - orchestrator_stats["start_time"]).total_seconds()
    
    return {
        "orchestrator": "Enterprise Microservices Orchestrator",
        "version": "3.0.0",
        "uptime_seconds": uptime,
        "services": {name: service["status"] for name, service in service_registry.services.items()},
        "stats": orchestrator_stats
    }

@app.get("/health")
async def health_check():
    try:
        healthy, total = await service_registry.check_all_services()
        uptime = (datetime.now() - orchestrator_stats["start_time"]).total_seconds()
        
        return {
            "status": "healthy" if healthy > 0 else "degraded",
            "orchestrator": {
                "status": "healthy",
                "uptime_seconds": uptime,
                "version": "3.0.0"
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
    if not templates:
        return HTMLResponse('''
        <h1>🎭 Dashboard Microservicios</h1>
        <p><strong>Servicios activos:</strong></p>
        <ul>
            <li>Message Replicator: <a href="http://localhost:8001">http://localhost:8001</a></li>
            <li>Analytics: <a href="http://localhost:8002">http://localhost:8002</a></li>
        </ul>
        <p><a href="/health">Ver Health Check</a></p>
        <p><a href="/docs">Ver API Docs</a></p>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            h1 { color: #333; }
            a { color: #0066cc; }
        </style>
        ''')
    
    try:
        uptime = (datetime.now() - orchestrator_stats["start_time"]).total_seconds()
        
        context = {
            "request": request,
            "title": "Enterprise Microservices Dashboard",
            "orchestrator_stats": {
                "uptime_hours": uptime / 3600,
                "requests_proxied": orchestrator_stats["requests_proxied"],
                "services_count": len(service_registry.services)
            },
            "services": service_registry.services
        }
        
        return templates.TemplateResponse("dashboard.html", context)
        
    except Exception as e:
        logger.error(f"❌ Dashboard error: {e}")
        return HTMLResponse(f"<h1>Dashboard Error</h1><p>{e}</p>", status_code=500)

if __name__ == "__main__":
    config = {
        "host": settings.host,
        "port": settings.port,
        "reload": settings.debug,
        "log_level": settings.log_level.lower()
    }
    
    print("🎭 Starting Enterprise Microservices Orchestrator...")
    uvicorn.run(app, **config)
'''
    
    create_file(Path("main.py"), main_code)

def create_dashboard_template():
    """Crear template del dashboard"""
    print("🎨 Creando Dashboard Template...")
    
    dashboard_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        body {
            margin: 0;
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }

        .header {
            text-align: center;
            margin-bottom: 3rem;
        }

        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1.5rem;
            margin-bottom: 3rem;
        }

        .stat-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 16px;
            padding: 1.5rem;
            animation: fadeInUp 0.6s ease forwards;
        }

        .stat-title {
            font-size: 0.9rem;
            opacity: 0.8;
            margin-bottom: 0.5rem;
        }

        .stat-value {
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }

        .services-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
        }

        .service-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 16px;
            padding: 1.5rem;
            transition: transform 0.3s ease;
        }

        .service-card:hover {
            transform: translateY(-4px);
        }

        .service-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }

        .service-name {
            font-weight: 600;
            font-size: 1.1rem;
        }

        .service-status {
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-size: 0.7rem;
            font-weight: 500;
            text-transform: uppercase;
        }

        .service-status.healthy {
            background: rgba(16, 185, 129, 0.3);
            color: #10b981;
        }

        .service-status.unhealthy {
            background: rgba(239, 68, 68, 0.3);
            color: #ef4444;
        }

        .service-status.unknown {
            background: rgba(245, 158, 11, 0.3);
            color: #f59e0b;
        }

        .refresh-btn {
            background: #4285f4;
            border: none;
            padding: 0.8rem 1.5rem;
            border-radius: 12px;
            color: white;
            cursor: pointer;
            font-weight: 500;
            margin-top: 2rem;
            transition: all 0.3s ease;
        }

        .refresh-btn:hover {
            background: #8b5cf6;
            transform: translateY(-2px);
        }

        .links-section {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 16px;
            padding: 2rem;
            margin-top: 2rem;
            text-align: center;
        }

        .links-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }

        .link-card {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 1rem;
            text-decoration: none;
            color: white;
            transition: all 0.3s ease;
        }

        .link-card:hover {
            background: rgba(66, 133, 244, 0.3);
            transform: translateY(-2px);
        }

        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎭 Enterprise Microservices</h1>
            <p>Tu Enhanced Replicator Service convertido a arquitectura enterprise</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-title">Orchestrator Uptime</div>
                <div class="stat-value">{{ "%.1f"|format(orchestrator_stats.uptime_hours) }}h</div>
                <div style="color: #10b981; font-size: 0.8rem;">Running smoothly</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-title">Requests Proxied</div>
                <div class="stat-value">{{ orchestrator_stats.requests_proxied }}</div>
                <div style="color: #4285f4; font-size: 0.8rem;">Total requests</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-title">Active Services</div>
                <div class="stat-value">{{ orchestrator_stats.services_count }}</div>
                <div style="color: #8b5cf6; font-size: 0.8rem;">Microservices running</div>
            </div>
        </div>

        <div class="services-grid">
            {% for service_name, service in services.items() %}
            <div class="service-card">
                <div class="service-header">
                    <h4 class="service-name">{{ service.name }}</h4>
                    <span class="service-status {{ service.status }}">{{ service.status }}</span>
                </div>
                <div style="margin-bottom: 1rem;">
                    <div style="font-size: 0.8rem; opacity: 0.8;">URL: {{ service.url }}</div>
                    <div style="font-size: 0.8rem; opacity: 0.8;">Service: {{ service_name }}</div>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                    <div style="text-align: center;">
                        <div style="font-size: 1.2rem; font-weight: 600;">
                            {% if service.status == 'healthy' %}✅{% else %}❌{% endif %}
                        </div>
                        <div style="font-size: 0.7rem; opacity: 0.7;">STATUS</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 1.2rem; font-weight: 600;">v3.0</div>
                        <div style="font-size: 0.7rem; opacity: 0.7;">VERSION</div>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>

        <div class="links-section">
            <h3>🔗 Quick Access Links</h3>
            <div class="links-grid">
                <a href="/health" class="link-card">
                    <div>🏥 Health Check</div>
                    <div style="font-size: 0.8rem; opacity: 0.7;">System Status</div>
                </a>
                <a href="/docs" class="link-card">
                    <div>📚 API Docs</div>
                    <div style="font-size: 0.8rem; opacity: 0.7;">OpenAPI</div>
                </a>
                <a href="http://localhost:8001" class="link-card">
                    <div>📡 Message Replicator</div>
                    <div style="font-size: 0.8rem; opacity: 0.7;">Port 8001</div>
                </a>
                <a href="http://localhost:8002" class="link-card">
                    <div>📊 Analytics</div>
                    <div style="font-size: 0.8rem; opacity: 0.7;">Port 8002</div>
                </a>
            </div>
        </div>

        <button class="refresh-btn" onclick="window.location.reload()">
            🔄 Refresh Dashboard
        </button>
    </div>

    <script>
        setTimeout(() => {
            window.location.reload();
        }, 30000);
    </script>
</body>
</html>'''
    
    create_file(Path("frontend/templates/dashboard.html"), dashboard_html)

def create_env_file():
    """Crear archivo .env actualizado"""
    print("⚙️ Creando .env para microservicios...")
    
    env_content = '''# TELEGRAM CONFIGURATION (de tu .env original)
TELEGRAM_API_ID=18425773
TELEGRAM_API_HASH=1a94c8576994cbb3e60383c94562c91b
TELEGRAM_PHONE=+56985667015
TELEGRAM_SESSION=replicator_session

# DISCORD WEBHOOKS (de tu .env original)
WEBHOOK_-4989347027=https://discord.com/api/webhooks/1399873931695100005/FByKlMB9JI_eUR-WXaRiFiP8pYdZbS7dCrpyPO66gK09DBnCeAvYBRv4--knBZU5HCBM
WEBHOOK_-1001697798998=https://discord.com/api/webhooks/1399873931695100005/FByKlMB9JI_eUR-WXaRiFiP8pYdZbS7dCrpyPO66gK09DBnCeAvYBRv4--knBZU5HCBM

# MICROSERVICES PORTS
PORT=8000
MESSAGE_REPLICATOR_PORT=8001
ANALYTICS_PORT=8002

# DATABASE CONFIGURATION
DATABASE_URL=sqlite:///./database/replicator.db
DATABASE_ECHO=false

# DEVELOPMENT SETTINGS
DEBUG=true
LOG_LEVEL=INFO
HOST=0.0.0.0

# OPTIONAL SETTINGS (de tu configuración)
MAX_FILE_SIZE_MB=8
WATERMARKS_ENABLED=true
'''
    
    create_file(Path(".env.microservices"), env_content)

def create_requirements():
    """Crear requirements.txt actualizado"""
    print("📦 Creando requirements.txt...")
    
    requirements = '''# Dependencias principales (de tu requirements.txt original)
telethon>=1.24.0
python-dotenv>=0.19.0
aiohttp>=3.8.0
fastapi>=0.68.0
uvicorn[standard]>=0.15.0
jinja2>=3.0.0
python-multipart>=0.0.5
Pillow>=9.0.0
python-dateutil>=2.8.0

# Dependencias nuevas para microservicios
httpx>=0.24.0
pydantic>=1.8.0
'''
    
    create_file(Path("requirements.txt"), requirements)

def create_database_setup():
    """Crear setup de base de datos"""
    print("🗄️ Creando setup de base de datos...")
    
    db_setup = '''#!/usr/bin/env python3
"""
🗄️ DATABASE SETUP v3.0
"""

import sqlite3
from pathlib import Path

def setup_databases():
    print("🗄️ Configurando bases de datos...")
    
    db_dir = Path("database")
    db_dir.mkdir(exist_ok=True)
    
    setup_replicator_db()
    setup_analytics_db()
    
    print("✅ Todas las bases de datos configuradas")

def setup_replicator_db():
    db_path = Path("database/replicator.db")
    
    conn = sqlite3.connect(db_path)
    
    conn.execute('''
    CREATE TABLE IF NOT EXISTS group_configs (
        group_id INTEGER PRIMARY KEY,
        webhook_url TEXT NOT NULL,
        is_active BOOLEAN DEFAULT 1,
        watermark_enabled BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.execute('''
    CREATE TABLE IF NOT EXISTS processed_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message_id TEXT UNIQUE,
        group_id INTEGER,
        message_type TEXT,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    groups = [
        (-4989347027, "https://discord.com/api/webhooks/1399873931695100005/FByKlMB9JI_eUR-WXaRiFiP8pYdZbS7dCrpyPO66gK09DBnCeAvYBRv4--knBZU5HCBM"),
        (-1001697798998, "https://discord.com/api/webhooks/1399873931695100005/FByKlMB9JI_eUR-WXaRiFiP8pYdZbS7dCrpyPO66gK09DBnCeAvYBRv4--knBZU5HCBM")
    ]
    
    for group_id, webhook_url in groups:
        conn.execute('''
        INSERT OR REPLACE INTO group_configs (group_id, webhook_url)
        VALUES (?, ?)
        ''', (group_id, webhook_url))
    
    conn.commit()
    conn.close()
    
    print("✅ Base de datos principal configurada")

def setup_analytics_db():
    db_path = Path("database/analytics.db")
    
    conn = sqlite3.connect(db_path)
    
    conn.execute('''
    CREATE TABLE IF NOT EXISTS metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        service_name TEXT NOT NULL,
        metric_name TEXT NOT NULL,
        metric_value REAL NOT NULL
    )
    ''')
    
    conn.commit()
    conn.close()
    
    print("✅ Base de datos de analytics configurada")

if __name__ == "__main__":
    setup_databases()
'''
    
    create_file(Path("database/setup.py"), db_setup)

def create_development_script():
    """Crear script de desarrollo"""
    print("🔧 Creando script de desarrollo...")
    
    dev_script = '''#!/usr/bin/env python3
"""
🔧 SCRIPT DE DESARROLLO SIN DOCKER
"""

import subprocess
import sys
import time
import signal
import os
from pathlib import Path
from typing import Dict, List

class DevManager:
    def __init__(self):
        self.processes: Dict[str, subprocess.Popen] = {}
        self.base_dir = Path(__file__).parent.parent
        self.services = [
            {
                "name": "Main Orchestrator",
                "script": "main.py",
                "port": 8000,
                "env": {"PORT": "8000", "DEBUG": "true"}
            },
            {
                "name": "Message Replicator",
                "script": "services/message_replicator/main.py", 
                "port": 8001,
                "env": {"PORT": "8001", "DEBUG": "true"}
            },
            {
                "name": "Analytics Service",
                "script": "services/analytics/main.py",
                "port": 8002,
                "env": {"PORT": "8002", "DEBUG": "true"}
            }
        ]
    
    def start_service(self, service: Dict) -> subprocess.Popen:
        script_path = self.base_dir / service["script"]
        
        if not script_path.exists():
            print(f"⚠️ Script no encontrado: {script_path}")
            return None
        
        env = dict(os.environ)
        env.update(service["env"])
        
        print(f"🚀 Iniciando {service['name']} en puerto {service['port']}...")
        
        try:
            process = subprocess.Popen(
                [sys.executable, str(script_path)],
                env=env,
                cwd=self.base_dir
            )
            
            self.processes[service["name"]] = process
            return process
            
        except Exception as e:
            print(f"❌ Error iniciando {service['name']}: {e}")
            return None
    
    def start_all_services(self):
        print("🏗️ Iniciando SaaS Enterprise - Modo Desarrollo")
        print("=" * 60)
        
        for service in self.services:
            process = self.start_service(service)
            if process:
                time.sleep(3)
        
        print("=" * 60)
        print("✅ Todos los servicios iniciados")
        self.show_service_info()
    
    def show_service_info(self):
        print()
        print("🌐 URLs disponibles:")
        print("   📊 Dashboard Principal:  http://localhost:8000/dashboard")
        print("   🏥 Health Check:         http://localhost:8000/health")
        print("   📚 API Docs:             http://localhost:8000/docs")
        print("   📡 Message Replicator:   http://localhost:8001")
        print("   📈 Analytics Service:    http://localhost:8002")
        print()
        print("📱 Tu Enhanced Replicator sigue funcionando igual")
        print("   Pero ahora en arquitectura microservicios enterprise!")
    
    def stop_all_services(self):
        print("\\n🛑 Deteniendo servicios...")
        
        for name, process in self.processes.items():
            try:
                print(f"   Deteniendo {name}...")
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print(f"   Forzando cierre de {name}...")
                process.kill()
            except Exception as e:
                print(f"   Error deteniendo {name}: {e}")
        
        print("👋 SaaS Enterprise detenido")
    
    def monitor_services(self):
        try:
            while True:
                dead_services = []
                for name, process in self.processes.items():
                    if process.poll() is not None:
                        dead_services.append(name)
                
                if dead_services:
                    for name in dead_services:
                        print(f"❌ {name} se detuvo inesperadamente")
                    break
                
                time.sleep(5)
                
        except KeyboardInterrupt:
            self.stop_all_services()

def main():
    print("🔧 SaaS Enterprise - Desarrollo sin Docker")
    
    manager = DevManager()
    
    def signal_handler(signum, frame):
        manager.stop_all_services()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        (manager.base_dir / "logs").mkdir(exist_ok=True)
        (manager.base_dir / "database").mkdir(exist_ok=True)
        
        print("🗄️ Configurando base de datos...")
        db_setup_path = manager.base_dir / "database" / "setup.py"
        if db_setup_path.exists():
            subprocess.run([sys.executable, str(db_setup_path)])
        
        manager.start_all_services()
        manager.monitor_services()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        manager.stop_all_services()
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
    
    create_file(Path("scripts/start_dev.py"), dev_script)

def create_makefile():
    """Crear Makefile para comandos"""
    print("📋 Creando Makefile...")
    
    makefile_content = '''# 🚀 SaaS Enterprise Makefile

.PHONY: help setup dev start stop status

help: ## Mostrar ayuda
	@echo "🚀 SaaS Enterprise - Comandos disponibles:"
	@echo ""
	@echo "  setup    - Configuración inicial"
	@echo "  dev      - Iniciar en modo desarrollo"  
	@echo "  start    - Alias para dev"
	@echo "  stop     - Detener servicios"
	@echo "  status   - Ver estado de servicios"

setup: ## Configuración inicial
	@echo "⚙️ Configurando SaaS Enterprise..."
	cp .env.microservices .env || echo "⚠️ .env ya existe"
	mkdir -p logs database temp
	pip install -r requirements.txt
	python database/setup.py
	@echo "✅ Configuración completada"

dev: ## Iniciar en modo desarrollo
	@echo "🔧 Iniciando SaaS Enterprise..."
	python scripts/start_dev.py

start: dev ## Alias para dev

stop: ## Detener servicios
	@echo "🛑 Deteniendo servicios..."
	@pkill -f "main.py" || echo "Main ya detenido"
	@pkill -f "message_replicator" || echo "Replicator ya detenido"
	@pkill -f "analytics" || echo "Analytics ya detenido"

status: ## Ver estado de servicios
	@echo "📊 Estado de servicios:"
	@curl -s http://localhost:8000/health 2>/dev/null || echo "❌ Orchestrator no responde"
'''
    
    create_file(Path("Makefile"), makefile_content)

def create_readme():
    """Crear README con instrucciones"""
    print("📚 Creando README...")
    
    readme_content = '''# 🚀 SaaS Enterprise - Microservicios

## Tu Enhanced Replicator Service convertido a arquitectura enterprise

### 🎯 ¿Qué cambió?

**ANTES**: main.py monolítico con toda la lógica  
**DESPUÉS**: Arquitectura microservicios enterprise escalable

### 🚀 Inicio Rápido

```bash
# 1. Configurar
make setup

# 2. Iniciar desarrollo
make dev

# 3. Abrir dashboard
http://localhost:8000/dashboard
```

### 📊 URLs Disponibles

- **Dashboard Principal**: http://localhost:8000/dashboard
- **Health Check**: http://localhost:8000/health  
- **API Docs**: http://localhost:8000/docs
- **Message Replicator**: http://localhost:8001
- **Analytics**: http://localhost:8002

### 🎯 Tu Enhanced Replicator

Tu Enhanced Replicator Service ahora funciona como microservicio independiente:
- ✅ Mantiene TODA la funcionalidad original
- ✅ API REST añadida
- ✅ Health checks enterprise

### 🔧 Comandos Útiles

```bash
make setup     # Configuración inicial
make dev       # Desarrollo
make status    # Estado servicios  
make stop      # Detener todo
```

¡Tu Enhanced Replicator ahora es una arquitectura enterprise completa! 🎉
'''
    
    create_file(Path("README.md"), readme_content)

def run_migration():
    """Ejecutar migración completa"""
    
    print("🚀 INICIANDO MIGRACIÓN COMPLETA A MICROSERVICIOS")
    print("=" * 60)
    
    try:
        backup_original_files()
        create_directory_structure()
        create_shared_config()
        create_shared_logger()
        create_message_replicator_microservice()
        create_analytics_service()
        create_main_orchestrator()
        create_dashboard_template()
        create_env_file()
        create_requirements()
        create_database_setup()
        create_development_script()
        create_makefile()
        create_readme()
        
        print("=" * 60)
        print("✅ MIGRACIÓN COMPLETADA EXITOSAMENTE!")
        print()
        print("📋 Próximos pasos:")
        print("1. make setup")
        print("2. make dev") 
        print("3. Abrir http://localhost:8000/dashboard")
        print()
        print("🎉 Tu Enhanced Replicator ahora es una arquitectura enterprise!")
        
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        raise

if __name__ == "__main__":
    run_migration()