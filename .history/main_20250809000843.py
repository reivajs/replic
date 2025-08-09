#!/usr/bin/env python3
"""
🎭 ENTERPRISE MICROSERVICES ORCHESTRATOR v4.0 - COMPLETO
========================================================
Orquestador principal con todos los servicios enterprise
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
    """Registry de microservicios completo"""
    
    def __init__(self):
        self.services = {
            "message_replicator": {
                "name": "Message Replicator",
                "url": "http://localhost:8001",
                "port": 8001,
                "status": "unknown",
                "description": "Tu Enhanced Replicator como microservicio"
            },
            "analytics": {
                "name": "Analytics Service", 
                "url": "http://localhost:8002",
                "port": 8002,
                "status": "unknown",
                "description": "Métricas y analytics SaaS"
            },
            "file_manager": {
                "name": "File Manager",
                "url": "http://localhost:8003", 
                "port": 8003,
                "status": "unknown",
                "description": "Gestión de archivos y multimedia"
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
    
    async def get_service_stats(self, service_name: str) -> Dict[str, Any]:
        """Obtener estadísticas de un servicio"""
        service = self.services.get(service_name)
        if not service:
            return {}
        
        try:
            response = await self.http_client.get(f"{service['url']}/stats")
            if response.status_code == 200:
                return response.json()
        except:
            pass
        
        return {}
    
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Obtener datos consolidados para dashboard"""
        dashboard_data = {
            "orchestrator": {
                "uptime": (datetime.now() - orchestrator_stats["start_time"]).total_seconds(),
                "requests": orchestrator_stats["requests_handled"],
                "version": "4.0.0"
            },
            "services": {},
            "summary": {
                "total_services": len(self.services),
                "healthy_services": 0,
                "analytics_data": {}
            }
        }
        
        # Obtener datos de analytics si está disponible
        try:
            response = await self.http_client.get("http://localhost:8002/dashboard-data")
            if response.status_code == 200:
                dashboard_data["summary"]["analytics_data"] = response.json()
        except:
            pass
        
        # Verificar cada servicio
        for service_name, service_info in self.services.items():
            health = await self.check_service_health(service_name)
            stats = await self.get_service_stats(service_name)
            
            dashboard_data["services"][service_name] = {
                "health": health,
                "stats": stats,
                "info": service_info
            }
            
            if health.get("status") == "healthy":
                dashboard_data["summary"]["healthy_services"] += 1
        
        return dashboard_data

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
        print("\n" + "="*60)
        print("🎭 ENTERPRISE MICROSERVICES ORCHESTRATOR")
        print("="*60)
        print("🌐 Endpoints principales:")
        print("   📊 Dashboard:         http://localhost:8000/dashboard")
        print("   🏥 Health Check:      http://localhost:8000/health")
        print("   📚 API Docs:          http://localhost:8000/docs")
        print("\n🔗 Microservicios:")
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

@app.get("/services")
async def list_services():
    """Listar todos los servicios"""
    await service_registry.check_all_services()
    
    return {
        "services": service_registry.services,
        "summary": {
            "total": len(service_registry.services),
            "healthy": sum(1 for s in service_registry.services.values() if s["status"] == "healthy"),
            "unhealthy": sum(1 for s in service_registry.services.values() if s["status"] in ["unhealthy", "unavailable"])
        }
    }

@app.get("/dashboard-data")
async def get_dashboard_data():
    """Datos consolidados para el dashboard"""
    try:
        return await service_registry.get_dashboard_data()
    except Exception as e:
        return {"error": str(e)}

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Dashboard enterprise"""
    return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>🎭 Enterprise Dashboard</title>
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; margin: 0; padding: 20px; }
                .container { max-width: 1200px; margin: 0 auto; }
                .header { text-align: center; margin-bottom: 40px; padding: 30px; background: rgba(255,255,255,0.1); border-radius: 20px; backdrop-filter: blur(10px); }
                .header h1 { font-size: 48px; font-weight: 700; margin-bottom: 15px; }
                .header p { font-size: 18px; opacity: 0.8; }
                .services-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 20px; margin-bottom: 30px; }
                .service-card { background: rgba(255,255,255,0.1); padding: 25px; border-radius: 15px; backdrop-filter: blur(10px); transition: transform 0.3s; }
                .service-card:hover { transform: translateY(-5px); }
                .service-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
                .service-name { font-size: 20px; font-weight: 600; }
                .service-status { padding: 6px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; text-transform: uppercase; }
                .healthy { background: rgba(76, 175, 80, 0.3); color: #4CAF50; }
                .unavailable { background: rgba(158, 158, 158, 0.3); color: #9E9E9E; }
                .checking { background: rgba(255, 193, 7, 0.3); color: #ffca28; }
                .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-bottom: 30px; }
                .metric-card { background: rgba(255,255,255,0.1); padding: 20px; border-radius: 15px; backdrop-filter: blur(10px); }
                .metric-title { font-size: 14px; opacity: 0.8; margin-bottom: 10px; }
                .metric-value { font-size: 28px; font-weight: 700; margin-bottom: 8px; }
                .metric-change { font-size: 12px; padding: 4px 8px; border-radius: 15px; }
                .positive { background: rgba(76, 175, 80, 0.3); color: #4CAF50; }
                .negative { background: rgba(244, 67, 54, 0.3); color: #F44336; }
                .refresh-btn { position: fixed; bottom: 30px; right: 30px; width: 60px; height: 60px; border-radius: 50%; background: rgba(255,255,255,0.2); border: none; color: white; font-size: 24px; cursor: pointer; transition: all 0.3s; }
                .refresh-btn:hover { background: rgba(255,255,255,0.3); transform: scale(1.1); }
                .loading { animation: spin 1s linear infinite; }
                @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎭 Enterprise SaaS Dashboard</h1>
                    <p>Arquitectura de microservicios escalable</p>
                </div>
                
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-title">💰 Total Revenue</div>
                        <div class="metric-value" id="total-revenue">$12,278.35</div>
                        <span class="metric-change positive">+5%</span>
                    </div>
                    
                    <div class="metric-card">
                        <div class="metric-title">📊 New Orders</div>
                        <div class="metric-value" id="new-orders">4,673</div>
                        <span class="metric-change negative">-2%</span>
                    </div>
                    
                    <div class="metric-card">
                        <div class="metric-title">✅ Completed</div>
                        <div class="metric-value" id="completed-orders">5,342</div>
                        <span class="metric-change positive">+18%</span>
                    </div>
                    
                    <div class="metric-card">
                        <div class="metric-title">💸 Spending</div>
                        <div class="metric-value" id="spending">$10,365.32</div>
                        <span class="metric-change negative">-17%</span>
                    </div>
                </div>
                
                <div class="services-grid">
                    <div class="service-card">
                        <div class="service-header">
                            <div class="service-name">📡 Message Replicator</div>
                            <div class="service-status checking" id="replicator-status">Checking...</div>
                        </div>
                        <p>Tu Enhanced Replicator Service como microservicio</p>
                        <div style="margin-top: 15px;">
                            <strong>Puerto:</strong> 8001<br>
                            <strong>URL:</strong> <a href="http://localhost:8001" style="color: #fff;">http://localhost:8001</a>
                        </div>
                    </div>
                    
                    <div class="service-card">
                        <div class="service-header">
                            <div class="service-name">📊 Analytics Service</div>
                            <div class="service-status checking" id="analytics-status">Checking...</div>
                        </div>
                        <p>Métricas y analytics enterprise para tu SaaS</p>
                        <div style="margin-top: 15px;">
                            <strong>Puerto:</strong> 8002<br>
                            <strong>URL:</strong> <a href="http://localhost:8002" style="color: #fff;">http://localhost:8002</a>
                        </div>
                    </div>
                    
                    <div class="service-card">
                        <div class="service-header">
                            <div class="service-name">💾 File Manager</div>
                            <div class="service-status checking" id="filemanager-status">Checking...</div>
                        </div>
                        <p>Gestión de archivos y multimedia enterprise</p>
                        <div style="margin-top: 15px;">
                            <strong>Puerto:</strong> 8003<br>
                            <strong>URL:</strong> <a href="http://localhost:8003" style="color: #fff;">http://localhost:8003</a>
                        </div>
                    </div>
                    
                    <div class="service-card">
                        <div class="service-header">
                            <div class="service-name">🎭 Main Orchestrator</div>
                            <div class="service-status healthy">Healthy</div>
                        </div>
                        <p>Orquestador principal que coordina todos los microservicios</p>
                        <div style="margin-top: 15px;">
                            <strong>Puerto:</strong> 8000<br>
                            <strong>Health:</strong> <a href="http://localhost:8000/health" style="color: #fff;">Health Check</a>
                        </div>
                    </div>
                </div>
            </div>
            
            <button class="refresh-btn" onclick="refreshData()" id="refresh-btn">🔄</button>
            
            <script>
                async function refreshData() {
                    const refreshBtn = document.getElementById('refresh-btn');
                    refreshBtn.classList.add('loading');
                    
                    try {
                        const healthResponse = await fetch('/health');
                        const healthData = await healthResponse.json();
                        
                        updateServiceStatus('replicator-status', healthData.services?.details?.message_replicator || 'unavailable');
                        updateServiceStatus('analytics-status', healthData.services?.details?.analytics || 'unavailable');
                        updateServiceStatus('filemanager-status', healthData.services?.details?.file_manager || 'unavailable');
                        
                        try {
                            const analyticsResponse = await fetch('http://localhost:8002/dashboard-data');
                            if (analyticsResponse.ok) {
                                const analyticsData = await analyticsResponse.json();
                                updateDashboardWithAnalytics(analyticsData);
                            }
                        } catch (e) {
                            console.log('Analytics service not available');
                        }
                        
                        console.log('🎭 Dashboard actualizado:', new Date().toLocaleTimeString());
                        
                    } catch (error) {
                        console.error('Error actualizando dashboard:', error);
                    } finally {
                        refreshBtn.classList.remove('loading');
                    }
                }
                
                function updateServiceStatus(elementId, status) {
                    const element = document.getElementById(elementId);
                    if (!element) return;
                    
                    let statusClass = 'checking';
                    let statusText = 'Checking...';
                    
                    switch (status) {
                        case 'healthy':
                            statusClass = 'healthy';
                            statusText = 'Healthy';
                            break;
                        case 'unhealthy':
                            statusClass = 'negative';
                            statusText = 'Unhealthy';
                            break;
                        case 'unavailable':
                            statusClass = 'unavailable';
                            statusText = 'Unavailable';
                            break;
                    }
                    
                    element.className = 'service-status ' + statusClass;
                    element.textContent = statusText;
                }
                
                function updateDashboardWithAnalytics(data) {
                    if (data.revenue) {
                        document.getElementById('total-revenue').textContent = '$' + data.revenue.total.toLocaleString();
                    }
                    if (data.new_orders) {
                        document.getElementById('new-orders').textContent = data.new_orders.total.toLocaleString();
                    }
                    if (data.completed_orders) {
                        document.getElementById('completed-orders').textContent = data.completed_orders.total.toLocaleString();
                    }
                    if (data.spending) {
                        document.getElementById('spending').textContent = '$' + data.spending.total.toLocaleString();
                    }
                }
                
                setInterval(refreshData, 30000);
                setTimeout(refreshData, 2000);
                
                console.log('🎭 Enterprise Dashboard Loaded - Full Architecture');
            </script>
        </body>
        </html>
        """)

if __name__ == "__main__":
    config = {
        "host": "0.0.0.0",
        "port": 8000,
        "reload": False,
        "log_level": "info"
    }
    
    print("🚀 Starting Enterprise Microservices Orchestrator...")
    print(f"   🎭 Main Orchestrator: http://{config['host']}:{config['port']}")
    print(f"   📊 Dashboard: http://{config['host']}:{config['port']}/dashboard")
    print(f"   📚 Docs: http://{config['host']}:{config['port']}/docs")
    
    uvicorn.run(app, **config)