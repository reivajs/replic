#!/usr/bin/env python3
"""
🚀 MIGRACIÓN RÁPIDA A MICROSERVICIOS
===================================
Script simplificado sin errores de indentación

EJECUTAR: python quick_migrate.py
"""

import os
import shutil
from pathlib import Path

def create_file(path, content):
    """Crear archivo de forma segura"""
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content.strip(), encoding='utf-8')
    print(f"✅ {path}")

def backup_files():
    """Backup rápido"""
    backup_dir = Path("backup_original")
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
    backup_dir.mkdir()
    
    files = ["main.py", ".env"]
    for file in files:
        if Path(file).exists():
            shutil.copy2(file, backup_dir / file)
    print("💾 Backup creado")

def create_structure():
    """Crear estructura básica"""
    dirs = [
        "services/message_replicator",
        "services/analytics", 
        "shared/config",
        "shared/utils",
        "frontend/templates",
        "database",
        "scripts",
        "logs"
    ]
    
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
        if "shared" in d or "services" in d:
            (Path(d) / "__init__.py").write_text("")

def create_shared_config():
    """Configuración compartida"""
    config = '''
import os
from dataclasses import dataclass, field
from typing import Dict
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
    
    def __post_init__(self):
        for key, value in os.environ.items():
            if key.startswith('WEBHOOK_'):
                try:
                    group_id = int(key.replace('WEBHOOK_', ''))
                    self.webhooks[group_id] = value
                except ValueError:
                    continue

@dataclass
class Settings:
    telegram: TelegramSettings = field(default_factory=TelegramSettings)
    discord: DiscordSettings = field(default_factory=DiscordSettings)
    debug: bool = os.getenv('DEBUG', 'false').lower() == 'true'
    host: str = os.getenv('HOST', '0.0.0.0')
    port: int = int(os.getenv('PORT', 8000))
    
    @property
    def telegram_api_id(self) -> int:
        return self.telegram.api_id
    
    @property  
    def telegram_api_hash(self) -> str:
        return self.telegram.api_hash
    
    @property
    def telegram_phone(self) -> str:
        return self.telegram.phone

def get_settings() -> Settings:
    return Settings()

settings = get_settings()
'''
    create_file("shared/config/settings.py", config)

def create_logger():
    """Logger simple"""
    logger = '''
import logging
import sys
from pathlib import Path

def setup_logger(name: str, service_name: str = None) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if logger.handlers:
        return logger
    
    formatter = logging.Formatter(f'{service_name or name} - %(levelname)s - %(message)s')
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger
'''
    create_file("shared/utils/logger.py", logger)

def create_message_replicator():
    """Microservicio principal"""
    service = '''
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
    ORIGINAL_AVAILABLE = True
except ImportError:
    from shared.config.settings import get_settings
    ORIGINAL_AVAILABLE = False

from shared.utils.logger import setup_logger

logger = setup_logger(__name__, "message-replicator")
settings = get_settings()
replicator_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global replicator_service
    logger.info("🚀 Iniciando Message Replicator Microservice...")
    
    try:
        if ORIGINAL_AVAILABLE:
            replicator_service = EnhancedReplicatorService()
            success = await replicator_service.initialize()
            if success:
                asyncio.create_task(replicator_service.start_listening())
                logger.info("✅ Enhanced Replicator inicializado")
        yield
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        if replicator_service:
            await replicator_service.stop()

app = FastAPI(title="Message Replicator Microservice", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/")
async def root():
    return {"service": "Message Replicator", "version": "3.0.0", "original_available": ORIGINAL_AVAILABLE}

@app.get("/health")
async def health():
    try:
        if not replicator_service:
            return {"status": "unhealthy", "reason": "Service not initialized"}
        
        if hasattr(replicator_service, 'get_health'):
            health_data = await replicator_service.get_health()
        else:
            health_data = {"status": "healthy"}
        
        health_data["microservice"] = "message-replicator"
        return health_data
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

if __name__ == "__main__":
    print("🚀 Starting Message Replicator on port 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)
'''
    create_file("services/message_replicator/main.py", service)

def create_analytics():
    """Analytics service"""
    analytics = '''
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("📊 Analytics Service started")
    yield
    print("📊 Analytics Service stopped")

app = FastAPI(title="Analytics Microservice", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/")
async def root():
    return {"service": "Analytics", "version": "3.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    print("📊 Starting Analytics on port 8002...")
    uvicorn.run(app, host="0.0.0.0", port=8002, reload=True)
'''
    create_file("services/analytics/main.py", analytics)

def create_main_orchestrator():
    """Main orchestrator"""
    main = '''
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import httpx

from shared.config.settings import get_settings
from shared.utils.logger import setup_logger

settings = get_settings()
logger = setup_logger(__name__, "orchestrator")

services = {
    "message-replicator": {"name": "Message Replicator", "url": "http://localhost:8001", "status": "unknown"},
    "analytics": {"name": "Analytics", "url": "http://localhost:8002", "status": "unknown"}
}

start_time = datetime.now()
http_client = httpx.AsyncClient(timeout=10.0)

async def check_services():
    for name, service in services.items():
        try:
            response = await http_client.get(f"{service['url']}/health")
            service["status"] = "healthy" if response.status_code == 200 else "unhealthy"
        except:
            service["status"] = "unreachable"

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🎭 Iniciando Orchestrator...")
    await check_services()
    
    print("\\n" + "="*50)
    print("🎭 ENTERPRISE ORCHESTRATOR")
    print("="*50)
    print("📊 Dashboard: http://localhost:8000/dashboard")
    print("🏥 Health: http://localhost:8000/health")
    print("📡 Message Replicator: http://localhost:8001")
    print("📈 Analytics: http://localhost:8002")
    print("="*50)
    
    yield
    await http_client.aclose()

app = FastAPI(title="Enterprise Orchestrator", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/")
async def root():
    uptime = (datetime.now() - start_time).total_seconds()
    return {
        "orchestrator": "Enterprise Microservices",
        "uptime_seconds": uptime,
        "services": {name: service["status"] for name, service in services.items()}
    }

@app.get("/health")
async def health():
    await check_services()
    healthy = sum(1 for s in services.values() if s["status"] == "healthy")
    return {
        "status": "healthy" if healthy > 0 else "degraded",
        "services": {"healthy": healthy, "total": len(services), "details": services}
    }

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    await check_services()
    uptime_hours = (datetime.now() - start_time).total_seconds() / 3600
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Enterprise Dashboard</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: linear-gradient(135deg, #667eea, #764ba2); color: white; }}
            .container {{ max-width: 1000px; margin: 0 auto; }}
            .header {{ text-align: center; margin-bottom: 40px; }}
            .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 40px; }}
            .card {{ background: rgba(255,255,255,0.1); padding: 20px; border-radius: 15px; backdrop-filter: blur(10px); }}
            .services {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
            .status-healthy {{ color: #10b981; }}
            .status-unhealthy {{ color: #ef4444; }}
            .status-unknown {{ color: #f59e0b; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎭 Enterprise Microservices Dashboard</h1>
                <p>Tu Enhanced Replicator convertido a arquitectura enterprise</p>
            </div>
            
            <div class="stats">
                <div class="card">
                    <h3>⏱️ Uptime</h3>
                    <div style="font-size: 2rem; font-weight: bold;">{uptime_hours:.1f}h</div>
                </div>
                <div class="card">
                    <h3>🔗 Services</h3>
                    <div style="font-size: 2rem; font-weight: bold;">{len(services)}</div>
                </div>
                <div class="card">
                    <h3>💚 Healthy</h3>
                    <div style="font-size: 2rem; font-weight: bold;">{sum(1 for s in services.values() if s["status"] == "healthy")}</div>
                </div>
            </div>
            
            <div class="services">
    """
    
    for name, service in services.items():
        status_class = f"status-{service['status']}"
        status_icon = "✅" if service["status"] == "healthy" else "❌" if service["status"] == "unhealthy" else "⚠️"
        
        html += f"""
                <div class="card">
                    <h3>{service['name']}</h3>
                    <p><strong>Status:</strong> <span class="{status_class}">{status_icon} {service['status']}</span></p>
                    <p><strong>URL:</strong> <a href="{service['url']}" style="color: #60a5fa;">{service['url']}</a></p>
                    <p><strong>Service:</strong> {name}</p>
                </div>
        """
    
    html += """
            </div>
            <div style="text-align: center; margin-top: 40px;">
                <button onclick="window.location.reload()" style="background: #4285f4; border: none; padding: 15px 30px; color: white; border-radius: 10px; cursor: pointer; font-size: 16px;">
                    🔄 Refresh Dashboard
                </button>
            </div>
        </div>
        <script>setTimeout(() => window.location.reload(), 30000);</script>
    </body>
    </html>
    """
    return html

if __name__ == "__main__":
    print("🎭 Starting Orchestrator on port 8000...")
    uvicorn.run(app, host=settings.host, port=settings.port, reload=settings.debug)
'''
    create_file("main.py", main)

def create_env():
    """Environment file"""
    env = '''# TELEGRAM (de tu .env original)
TELEGRAM_API_ID=18425773
TELEGRAM_API_HASH=1a94c8576994cbb3e60383c94562c91b
TELEGRAM_PHONE=+56985667015
TELEGRAM_SESSION=replicator_session

# DISCORD (de tu .env original)
WEBHOOK_-4989347027=https://discord.com/api/webhooks/1399873931695100005/FByKlMB9JI_eUR-WXaRiFiP8pYdZbS7dCrpyPO66gK09DBnCeAvYBRv4--knBZU5HCBM
WEBHOOK_-1001697798998=https://discord.com/api/webhooks/1399873931695100005/FByKlMB9JI_eUR-WXaRiFiP8pYdZbS7dCrpyPO66gK09DBnCeAvYBRv4--knBZU5HCBM

# MICROSERVICES
PORT=8000
DEBUG=true
HOST=0.0.0.0
MAX_FILE_SIZE_MB=8
WATERMARKS_ENABLED=true
'''
    create_file(".env.microservices", env)

def create_dev_script():
    """Development script"""
    script = '''
import subprocess
import sys
import time
import signal
from pathlib import Path

processes = {}

def start_service(name, script, port):
    print(f"🚀 Starting {name} on port {port}...")
    try:
        process = subprocess.Popen([sys.executable, script])
        processes[name] = process
        return process
    except Exception as e:
        print(f"❌ Error starting {name}: {e}")
        return None

def stop_all():
    print("\\n🛑 Stopping all services...")
    for name, process in processes.items():
        try:
            process.terminate()
            process.wait(timeout=5)
            print(f"   ✅ {name} stopped")
        except:
            process.kill()
            print(f"   🔪 {name} killed")

def signal_handler(signum, frame):
    stop_all()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def main():
    print("🔧 Starting Enterprise SaaS Development Mode")
    print("="*50)
    
    # Create directories
    Path("logs").mkdir(exist_ok=True)
    
    services = [
        ("Main Orchestrator", "main.py", 8000),
        ("Message Replicator", "services/message_replicator/main.py", 8001),
        ("Analytics", "services/analytics/main.py", 8002)
    ]
    
    for name, script, port in services:
        if Path(script).exists():
            start_service(name, script, port)
            time.sleep(2)
    
    print("="*50)
    print("✅ All services started!")
    print("📊 Dashboard: http://localhost:8000/dashboard")
    print("🏥 Health: http://localhost:8000/health")
    print("📡 Message Replicator: http://localhost:8001")
    print("📈 Analytics: http://localhost:8002")
    print("\\nPress Ctrl+C to stop all services")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_all()

if __name__ == "__main__":
    main()
'''
    create_file("scripts/start_dev.py", script)

def create_makefile():
    """Simple Makefile"""
    makefile = '''
.PHONY: setup dev stop

setup:
	@echo "⚙️ Setting up..."
	cp .env.microservices .env || echo ".env exists"
	mkdir -p logs database temp
	pip install fastapi uvicorn httpx python-dotenv jinja2
	@echo "✅ Setup complete"

dev:
	@echo "🚀 Starting development mode..."
	python scripts/start_dev.py

stop:
	@pkill -f "main.py" || echo "No processes to kill"
'''
    create_file("Makefile", makefile)

def main():
    """Ejecutar migración rápida"""
    print("🚀 MIGRACIÓN RÁPIDA A MICROSERVICIOS")
    print("="*50)
    
    try:
        backup_files()
        create_structure()
        create_shared_config()
        create_logger()
        create_message_replicator()
        create_analytics()
        create_main_orchestrator()
        create_env()
        create_dev_script()
        create_makefile()
        
        print("="*50)
        print("✅ MIGRACIÓN COMPLETADA!")
        print()
        print("📋 Próximos pasos:")
        print("1. make setup")
        print("2. make dev")
        print("3. Abrir http://localhost:8000/dashboard")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
