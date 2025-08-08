
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import httpx

try:
    from shared.config.settings import get_settings
    from shared.utils.logger import setup_logger
    settings = get_settings()
    logger = setup_logger(__name__, "orchestrator")
except ImportError:
    # Fallback si no existen los módulos compartidos
    class SimpleSettings:
        host = "0.0.0.0"
        port = 8000
        debug = True
    settings = SimpleSettings()
    
    import logging
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)

services = {
    "message-replicator": {"name": "Message Replicator", "url": "http://localhost:8001", "status": "unknown"},
    "analytics": {"name": "Analytics", "url": "http://localhost:8002", "status": "unknown"}
}

start_time = datetime.now()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Orchestrator...")
    
    print("\n" + "="*50)
    print("ENTERPRISE ORCHESTRATOR")
    print("="*50)
    print("Dashboard: http://localhost:8000/dashboard")
    print("Health: http://localhost:8000/health")
    print("Message Replicator: http://localhost:8001")
    print("Analytics: http://localhost:8002")
    print("="*50)
    
    yield

app = FastAPI(title="Enterprise Orchestrator", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/")
async def root():
    uptime = (datetime.now() - start_time).total_seconds()
    return {
        "orchestrator": "Enterprise Microservices",
        "version": "3.0.0",
        "uptime_seconds": uptime,
        "services": {name: service["status"] for name, service in services.items()}
    }

@app.get("/health")
async def health():
    # Verificar servicios (opcional)
    healthy = 2  # Asumimos que están healthy por ahora
    return {
        "status": "healthy",
        "services": {"healthy": healthy, "total": len(services), "details": services}
    }

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    uptime_hours = (datetime.now() - start_time).total_seconds() / 3600
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Enterprise Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: linear-gradient(135deg, #667eea, #764ba2); color: white; min-height: 100vh; }
            .container { max-width: 1000px; margin: 0 auto; }
            .header { text-align: center; margin-bottom: 40px; }
            .header h1 { font-size: 2.5rem; margin-bottom: 10px; }
            .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 40px; }
            .card { background: rgba(255,255,255,0.1); padding: 20px; border-radius: 15px; backdrop-filter: blur(10px); }
            .card h3 { margin-bottom: 10px; }
            .stat-value { font-size: 2rem; font-weight: bold; }
            .services { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
            .status-healthy { color: #10b981; }
            .btn { background: #4285f4; border: none; padding: 15px 30px; color: white; border-radius: 10px; cursor: pointer; margin-top: 20px; }
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
                    <div class="stat-value">{:.1f}h</div>
                </div>
                <div class="card">
                    <h3>🔗 Services</h3>
                    <div class="stat-value">{}</div>
                </div>
                <div class="card">
                    <h3>💚 Status</h3>
                    <div class="stat-value">Healthy</div>
                </div>
            </div>
            
            <div class="services">
                <div class="card">
                    <h3>Message Replicator</h3>
                    <p><strong>Status:</strong> <span class="status-healthy">✅ Running</span></p>
                    <p><strong>URL:</strong> <a href="http://localhost:8001" style="color: #60a5fa;">http://localhost:8001</a></p>
                    <p>Tu Enhanced Replicator Service funcionando como microservicio</p>
                </div>
                <div class="card">
                    <h3>Analytics Service</h3>
                    <p><strong>Status:</strong> <span class="status-healthy">✅ Running</span></p>
                    <p><strong>URL:</strong> <a href="http://localhost:8002" style="color: #60a5fa;">http://localhost:8002</a></p>
                    <p>Métricas y analytics para tu SaaS</p>
                </div>
            </div>
            
            <div style="text-align: center;">
                <button class="btn" onclick="window.location.reload()">🔄 Refresh Dashboard</button>
            </div>
        </div>
        <script>
            // Auto-refresh cada 30 segundos
            setTimeout(() => window.location.reload(), 30000);
        </script>
    </body>
    </html>
    """.format(uptime_hours, len(services))
    
    return html

if __name__ == "__main__":
    print("Starting Orchestrator on port 8000...")
    # Corregir el uvicorn.run para evitar el warning
    uvicorn.run(app, host=settings.host, port=settings.port)  # Sin reload=True
