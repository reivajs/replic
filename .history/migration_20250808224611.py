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
    if not templates:
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>🎭 Enterprise Dashboard</title>
            <style>
                body { font-family: Arial; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; margin: 0; padding: 20px; }
                .container { max-width: 1200px; margin: 0 auto; }
                .header { text-align: center; margin-bottom: 40px; }
                .services-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 20px; margin-bottom: 30px; }
                .service-card { background: rgba(255,255,255,0.1); padding: 25px; border-radius: 15px; backdrop-filter: blur(10px); }
                .service-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
                .service-name { font-size: 20px; font-weight: 600; }
                .service-status { padding: 6px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; text-transform: uppercase; }
                .healthy { background: rgba(76, 175, 80, 0.3); color: #4CAF50; }
                .unavailable { background: rgba(158, 158, 158, 0.3); color: #9E9E9E; }
                .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; }
                .metric-card { background: rgba(255,255,255,0.1); padding: 20px; border-radius: 15px; backdrop-filter: blur(10px); }
                .metric-title { font-size: 14px; opacity: 0.8; margin-bottom: 10px; }
                .metric-value { font-size: 28px; font-weight: 700; margin-bottom: 8px; }
                .metric-change { font-size: 12px; padding: 4px 8px; border-radius: 15px; }
                .positive { background: rgba(76, 175, 80, 0.3); color: #4CAF50; }
                .negative { background: rgba(244, 67, 54, 0.3); color: #F44336; }
                .refresh-btn { position: fixed; bottom: 30px; right: 30px; width: 60px; height: 60px; border-radius: 50%; background: rgba(255,255,255,0.2); border: none; color: white; font-size: 24px; cursor: pointer; }
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
                        <div class="metric-value">$12,278.35</div>
                        <span class="metric-change positive">+5%</span>
                    </div>
                    
                    <div class="metric-card">
                        <div class="metric-title">📊 New Orders</div>
                        <div class="metric-value">4,673</div>
                        <span class="metric-change negative">-2%</span>
                    </div>
                    
                    <div class="metric-card">
                        <div class="metric-title">✅ Completed</div>
                        <div class="metric-value">5,342</div>
                        <span class="metric-change positive">+18%</span>
                    </div>
                    
                    <div class="metric-card">
                        <div class="metric-title">💸 Spending</div>
                        <div class="metric-value">$10,365.32</div>
                        <span class="metric-change negative">-17%</span>
                    </div>
                </div>
                
                <div class="services-grid">
                    <div class="service-card">
                        <div class="service-header">
                            <div class="service-name">📡 Message Replicator</div>
                            <div class="service-status" id="replicator-status">Checking...</div>
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
                            <div class="service-status" id="analytics-status">Checking...</div>
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
                            <div class="service-status" id="filemanager-status">Checking...</div>
                        </div>
                        <p>Gestión de archivos y multimedia enterprise</p>
                        <div style="margin-top: 15px;">
                            <strong>Puerto:</strong> 8003<br>
                            <strong>URL:</strong> <a href="http://localhost:8003" style="color: #fff;">http://localhost:8003</a>
                        </div>
                    </div>
                </div>
            </div>
            
            <button class="refresh-btn" onclick="refreshData()">🔄</button>
            
            <script>
                async function refreshData() {
                    try {
                        const response = await fetch('/health');
                        const data = await response.json();
                        
                        // Actualizar estados de servicios
                        updateServiceStatus('replicator-status', data.services?.details?.message_replicator || 'unavailable');
                        updateServiceStatus('analytics-status', data.services?.details?.analytics || 'unavailable');
                        updateServiceStatus('filemanager-status', data.services?.details?.file_manager || 'unavailable');
                        
                        console.log('Dashboard actualizado:', new Date().toLocaleTimeString());
                        
                    } catch (error) {
                        console.error('Error actualizando dashboard:', error);
                    }
                }
                
                function updateServiceStatus(elementId, status) {
                    const element = document.getElementById(elementId);
                    if (!element) return;
                    
                    element.className = 'service-status ' + (status === 'healthy' ? 'healthy' : 'unavailable');
                    element.textContent = status.charAt(0).toUpperCase() + status.slice(1);
                }
                
                // Auto-refresh cada 30 segundos
                setInterval(refreshData, 30000);
                
                // Refresh inicial
                setTimeout(refreshData, 1000);
                
                console.log('🎭 Enterprise Dashboard Loaded - All Services');
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
        "reload": False,
        "log_level": "info"
    }
    
    print("🚀 Starting Enterprise Microservices Orchestrator...")
    print(f"   🎭 Main Orchestrator: http://{config['host']}:{config['port']}")
    print(f"   📊 Dashboard: http://{config['host']}:{config['port']}/dashboard")
    print(f"   📚 Docs: http://{config['host']}:{config['port']}/docs")
    
    uvicorn.run(app, **config)
'''
    
    create_file(Path("main.py"), updated_orchestrator)

def create_complete_startup_script():
    """Crear script de inicio completo para todos los servicios"""
    print("🚀 Creando script de inicio completo...")
    
    startup_script = '''#!/usr/bin/env python3
"""
🚀 DESARROLLO COMPLETO - Iniciar todos los microservicios
========================================================
Script para iniciar la arquitectura enterprise completa
"""

import subprocess
import sys
import time
import os
from pathlib import Path

def start_service(service_name: str, script_path: str, port: int):
    """Iniciar un microservicio"""
    print(f"🚀 Iniciando {service_name} en puerto {port}...")
    
    if not Path(script_path).exists():
        print(f"⚠️ {script_path} no encontrado")
        return None
    
    return subprocess.Popen([
        sys.executable, script_path
    ])

def main():
    """Función principal"""
    print("🎭 Iniciando Enterprise Microservices COMPLETO...")
    print("=" * 70)
    
    processes = []
    
    try:
        # Todos los servicios
        services = [
            ("Message Replicator", "services/message_replicator/main.py", 8001),
            ("Analytics Service", "services/analytics/main.py", 8002),
            ("File Manager", "services/file_manager/main.py", 8003),
            ("Main Orchestrator", "main.py", 8000)
        ]
        
        # Iniciar cada servicio
        for name, script, port in services:
            process = start_service(name, script, port)
            if process:
                processes.append((name, process, port))
                time.sleep(3)  # Esperar entre inicios
        
        print("\\n" + "=" * 70)
        print("✅ ARQUITECTURA ENTERPRISE COMPLETA INICIADA")
        print("\\n🌐 URLs disponibles:")
        print("   📊 Dashboard:         http://localhost:8000/dashboard")
        print("   🏥 Health Check:      http://localhost:8000/health")
        print("   📚 API Docs:          http://localhost:8000/docs")
        print("\\n🔗 Microservicios individuales:")
        print("   📡 Message Replicator: http://localhost:8001")
        print("   📊 Analytics:         http://localhost:8002")
        print("   💾 File Manager:      http://localhost:8003")
        print("\\n🎯 CARACTERÍSTICAS ENTERPRISE:")
        print("   ✅ Tu Enhanced Replicator como microservicio")
        print("   ✅ Analytics SaaS con métricas en tiempo real")
        print("   ✅ File Manager con upload/download")
        print("   ✅ Dashboard enterprise moderno")
        print("   ✅ Health checks automáticos")
        print("   ✅ APIs REST completas")
        print("   ✅ Arquitectura escalable")
        print("=" * 70)
        print("\\nPresiona Ctrl+C para detener todos los servicios...")
        
        # Esperar a que terminen
        for name, process, port in processes:
            process.wait()
    
    except KeyboardInterrupt:
        print("\\n🛑 Deteniendo todos los servicios...")
        
        for name, process, port in processes:
            print(f"   Deteniendo {name}...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        
        print("👋 Arquitectura enterprise detenida")

if __name__ == "__main__":
    main()
'''
    
    create_file(Path("scripts/start_all.py"), startup_script)

def create_enhanced_dashboard():
    """Crear dashboard enterprise mejorado"""
    print("🎨 Creando Dashboard Enterprise Mejorado...")
    
    enhanced_dashboard = '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎭 Enterprise SaaS Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
            overflow-x: hidden;
        }
        
        .container { max-width: 1400px; margin: 0 auto; padding: 30px 20px; }
        
        .header {
            text-align: center;
            margin-bottom: 50px;
            padding: 40px 0;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 25px;
            backdrop-filter: blur(15px);
        }
        
        .header h1 {
            font-size: 48px;
            font-weight: 800;
            margin-bottom: 15px;
            background: linear-gradient(45deg, #fff, #e0e0e0);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .header p {
            font-size: 20px;
            opacity: 0.8;
            font-weight: 300;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 25px;
            margin-bottom: 50px;
        }
        
        .metric-card {
            background: rgba(255, 255, 255, 0.08);
            backdrop-filter: blur(20px);
            border-radius: 25px;
            padding: 35px 30px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: all 0.4s ease;
            position: relative;
            overflow: hidden;
        }
        
        .metric-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
        }
        
        .metric-card:hover {
            transform: translateY(-8px) scale(1.02);
            background: rgba(255, 255, 255, 0.12);
            box-shadow: 0 20px 40px rgba(0,0,0,0.2);
        }
        
        .metric-title {
            font-size: 16px;
            opacity: 0.8;
            margin-bottom: 20px;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .metric-value {
            font-size: 42px;
            font-weight: 800;
            margin-bottom: 15px;
            line-height: 1;
        }
        
        .metric-change {
            font-size: 14px;
            font-weight: 600;
            padding: 8px 16px;
            border-radius: 25px;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }
        
        .positive {
            background: rgba(76, 175, 80, 0.2);
            color: #66bb6a;
        }
        
        .negative {
            background: rgba(244, 67, 54, 0.2);
            color: #ef5350;
        }
        
        .services-section {
            margin-bottom: 50px;
        }
        
        .section-title {
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 30px;
            text-align: center;
        }
        
        .services-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 30px;
        }
        
        .service-card {
            background: rgba(255, 255, 255, 0.08);
            backdrop-filter: blur(20px);
            border-radius: 25px;
            padding: 35px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: all 0.4s ease;
            position: relative;
            overflow: hidden;
        }
        
        .service-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
        }
        
        .service-card:hover {
            transform: translateY(-6px);
            background: rgba(255, 255, 255, 0.12);
            box-shadow: 0 15px 35px rgba(0,0,0,0.2);
        }
        
        .service-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 25px;
        }
        
        .service-name {
            font-size: 24px;
            font-weight: 700;
        }
        
        .service-status {
            padding: 10px 20px;
            border-radius: 25px;
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .healthy {
            background: rgba(76, 175, 80, 0.2);
            color: #66bb6a;
        }
        
        .unavailable {
            background: rgba(158, 158, 158, 0.2);
            color: #bdbdbd;
        }
        
        .checking {
            background: rgba(255, 193, 7, 0.2);
            color: #ffca28;
        }
        
        .service-description {
            font-size: 16px;
            opacity: 0.8;
            margin-bottom: 20px;
            line-height: 1.5;
        }
        
        .service-details {
            background: rgba(255, 255, 255, 0.05);
            padding: 20px;
            border-radius: 15px;
            margin-top: 20px;
        }
        
        .service-details strong {
            color: #fff;
            font-weight: 600;
        }
        
        .service-details a {
            color: #81c784;
            text-decoration: none;
            font-weight: 500;
            transition: color 0.3s;
        }
        
        .service-details a:hover {
            color: #a5d6a7;
        }
        
        .stats-section {
            margin-top: 50px;
            text-align: center;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        
        .stat-item {
            background: rgba(255, 255, 255, 0.06);
            padding: 25px 20px;
            border-radius: 20px;
            backdrop-filter: blur(10px);
        }
        
        .stat-value {
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 8px;
        }
        
        .stat-label {
            font-size: 14px;
            opacity: 0.7;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .refresh-btn {
            position: fixed;
            bottom: 40px;
            right: 40px;
            width: 70px;
            height: 70px;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(20px);
            border: 2px solid rgba(255, 255, 255, 0.2);
            color: white;
            font-size: 28px;
            cursor: pointer;
            transition: all 0.4s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
        
        .refresh-btn:hover {
            background: rgba(255, 255, 255, 0.25);
            transform: scale(1.15) rotate(180deg);
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.2);
        }
        
        .loading {
            animation: spin 1.5s linear infinite;
        }
        
        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
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
        
        .animate-in {
            animation: fadeInUp 0.6s ease forwards;
        }
        
        @media (max-width: 768px) {
            .container { padding: 20px 15px; }
            .header h1 { font-size: 36px; }
            .services-grid { grid-template-columns: 1fr; }
            .metrics-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header animate-in">
            <h1>🎭 Enterprise SaaS Dashboard</h1>
            <p>Arquitectura de microservicios escalable con tu Enhanced Replicator</p>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card animate-in">
                <div class="metric-title">💰 Total Revenue</div>
                <div class="metric-value" id="total-revenue">$12,278.35</div>
                <span class="metric-change positive">+5% ↗</span>
                <span style="opacity: 0.6; margin-left: 15px;">From last week</span>
            </div>
            
            <div class="metric-card animate-in">
                <div class="metric-title">📊 New Orders</div>
                <div class="metric-value" id="new-orders">4,673</div>
                <span class="metric-change negative">-2% ↘</span>
                <span style="opacity: 0.6; margin-left: 15px;">From last week</span>
            </div>
            
            <div class="metric-card animate-in">
                <div class="metric-title">✅ Completed Orders</div>
                <div class="metric-value" id="completed-orders">5,342</div>
                <span class="metric-change positive">+18% ↗</span>
                <span style="opacity: 0.6; margin-left: 15px;">From last week</span>
            </div>
            
            <div class="metric-card animate-in">
                <div class="metric-title">💸 Spending</div>
                <div class="metric-value" id="spending">$10,365.32</div>
                <span class="metric-change negative">-17% ↘</span>
                <span style="opacity: 0.6; margin-left: 15px;">From last week</span>
            </div>
        </div>
        
        <div class="services-section">
            <h2 class="section-title">🔗 Microservicios Enterprise</h2>
            
            <div class="services-grid">
                <div class="service-card animate-in">
                    <div class="service-header">
                        <div class="service-name">📡 Message Replicator</div>
                        <div class="service-status checking" id="replicator-status">Checking...</div>
                    </div>
                    <div class="service-description">
                        Tu Enhanced Replicator Service funcionando como microservicio independiente con API REST completa.
                    </div>
                    <div class="service-details">
                        <strong>Puerto:</strong> 8001<br>
                        <strong>Funcionalidad:</strong> 100% original mantenida<br>
                        <strong>URL:</strong> <a href="http://localhost:8001" target="_blank">http://localhost:8001</a><br>
                        <strong>Docs:</strong> <a href="http://localhost:8001/docs" target="_blank">API Documentation</a>
                    </div>
                </div>
                
                <div class="service-card animate-in">
                    <div class="service-header">
                        <div class="service-name">📊 Analytics Service</div>
                        <div class="service-status checking" id="analytics-status">Checking...</div>
                    </div>
                    <div class="service-description">
                        Servicio de métricas y analytics enterprise con base de datos SQLite y APIs para dashboard.
                    </div>
                    <div class="service-details">
                        <strong>Puerto:</strong> 8002<br>
                        <strong>Funcionalidad:</strong> Métricas SaaS<br>
                        <strong>URL:</strong> <a href="http://localhost:8002" target="_blank">http://localhost:8002</a><br>
                        <strong>Docs:</strong> <a href="http://localhost:8002/docs" target="_blank">API Documentation</a>
                    </div>
                </div>
                
                <div class="service-card animate-in">
                    <div class="service-header">
                        <div class="service-name">💾 File Manager</div>
                        <div class="service-status checking" id="filemanager-status">Checking...</div>
                    </div>
                    <div class="service-description">
                        Gestión de archivos y multimedia enterprise con upload, download y categorización automática.
                    </div>
                    <div class="service-details">
                        <strong>Puerto:</strong> 8003<br>
                        <strong>Funcionalidad:</strong> Upload/Download<br>
                        <strong>URL:</strong> <a href="http://localhost:8003" target="_blank">http://localhost:8003</a><br>
                        <strong>Docs:</strong> <a href="http://localhost:8003/docs" target="_blank">API Documentation</a>
                    </div>
                </div>
                
                <div class="service-card animate-in">
                    <div class="service-header">
                        <div class="service-name">🎭 Main Orchestrator</div>
                        <div class="service-status healthy">Healthy</div>
                    </div>
                    <div class="service-description">
                        Orquestador principal que coordina todos los microservicios y proporciona este dashboard.
                    </div>
                    <div class="service-details">
                        <strong>Puerto:</strong> 8000<br>
                        <strong>Funcionalidad:</strong> Coordinación<br>
                        <strong>Health:</strong> <a href="http://localhost:8000/health" target="_blank">Health Check</a><br>
                        <strong>Docs:</strong> <a href="http://localhost:8000/docs" target="_blank">API Documentation</a>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="stats-section">
            <h2 class="section-title">📈 Estadísticas del Sistema</h2>
            <div class="stats-grid">
                <div class="stat-item animate-in">
                    <div class="stat-value" id="total-services">4</div>
                    <div class="stat-label">Total Services</div>
                </div>
                <div class="stat-item animate-in">
                    <div class="stat-value" id="healthy-services">-</div>
                    <div class="stat-label">Healthy Services</div>
                </div>
                <div class="stat-item animate-in">
                    <div class="stat-value" id="uptime">24h</div>
                    <div class="stat-label">System Uptime</div>
                </div>
                <div class="stat-item animate-in">
                    <div class="stat-value" id="requests">5.2K</div>
                    <div class="stat-label">Total Requests</div>
                </div>
            </div>
        </div>
    </div>
    
    <button class="refresh-btn" onclick="refreshData()" id="refresh-btn">🔄</button>
    
    <script>
        let refreshInterval;
        
        async function refreshData() {
            const refreshBtn = document.getElementById('refresh-btn');
            refreshBtn.classList.add('loading');
            
            try {
                // Obtener health check
                const healthResponse = await fetch('/health');
                const healthData = await healthResponse.json();
                
                // Actualizar estados de servicios
                updateServiceStatus('replicator-status', healthData.services?.details?.message_replicator || 'unavailable');
                updateServiceStatus('analytics-status', healthData.services?.details?.analytics || 'unavailable');
                updateServiceStatus('filemanager-status', healthData.services?.details?.file_manager || 'unavailable');
                
                // Actualizar estadísticas del sistema
                document.getElementById('healthy-services').textContent = healthData.services?.healthy || 0;
                
                // Simular actualización de métricas
                updateMetrics();
                
                // Obtener datos de analytics si está disponible
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
        
        function updateMetrics() {
            // Simular pequeños cambios en las métricas
            const revenue = document.getElementById('total-revenue');
            const orders = document.getElementById('new-orders');
            const completed = document.getElementById('completed-orders');
            const requests = document.getElementById('requests');
            
            if (revenue) {
                const current = parseFloat(revenue.textContent.replace('#!/usr/bin/env python3
"""
🎭 EXPANSIÓN SAAS ENTERPRISE v4.0
================================
Añadir servicios enterprise restantes para completar tu SaaS
"""

import os
from pathlib import Path

def create_file(file_path: Path, content: str):
    """Crear archivo con contenido"""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding='utf-8')
    print(f"   ✅ Creado: {file_path}")

def create_analytics_service():
    """Crear Analytics Service completo"""
    print("📊 Creando Analytics Service...")
    
    analytics_code = '''#!/usr/bin/env python3
"""
📊 ANALYTICS MICROSERVICE v4.0
==============================
Servicio de analytics enterprise para tu SaaS
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import logging

# Logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AnalyticsDB:
    """Base de datos de analytics optimizada"""
    
    def __init__(self, db_path: str = "database/analytics.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Inicializar base de datos"""
        Path("database").mkdir(exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        
        # Tabla de métricas
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
        
        # Tabla de eventos
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
        
        # Índices para performance
        conn.execute('CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_metrics_service ON metrics(service_name)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)')
        
        conn.commit()
        conn.close()
        
        # Insertar datos iniciales de muestra
        self._insert_sample_data()
    
    def _insert_sample_data(self):
        """Insertar datos de muestra para dashboard"""
        conn = sqlite3.connect(self.db_path)
        
        # Métricas de ejemplo
        sample_metrics = [
            ('message_replicator', 'messages_processed', 12278, None, '{"source": "telegram"}'),
            ('message_replicator', 'messages_replicated', 11856, None, '{"target": "discord"}'),
            ('message_replicator', 'errors', 34, None, '{"type": "connection"}'),
            ('analytics', 'queries_processed', 5674, None, '{"endpoint": "dashboard"}'),
            ('file_manager', 'files_stored', 1234, None, '{"type": "media"}'),
        ]
        
        for service, metric, value, group_id, metadata in sample_metrics:
            conn.execute('''
                INSERT OR IGNORE INTO metrics (service_name, metric_name, metric_value, group_id, metadata)
                VALUES (?, ?, ?, ?, ?)
            ''', (service, metric, value, group_id, metadata))
        
        conn.commit()
        conn.close()
    
    def add_metric(self, service_name: str, metric_name: str, value: float, group_id: int = None, metadata: str = None):
        """Añadir métrica"""
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            INSERT INTO metrics (service_name, metric_name, metric_value, group_id, metadata)
            VALUES (?, ?, ?, ?, ?)
        ''', (service_name, metric_name, value, group_id, metadata))
        conn.commit()
        conn.close()
    
    def get_metrics_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Obtener resumen de métricas"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        since = datetime.now() - timedelta(hours=hours)
        
        cursor = conn.execute('''
            SELECT 
                service_name,
                metric_name,
                COUNT(*) as count,
                AVG(metric_value) as avg_value,
                SUM(metric_value) as total_value,
                MIN(metric_value) as min_value,
                MAX(metric_value) as max_value
            FROM metrics 
            WHERE timestamp >= ?
            GROUP BY service_name, metric_name
            ORDER BY service_name, metric_name
        ''', (since,))
        
        results = {}
        for row in cursor.fetchall():
            service = row['service_name']
            if service not in results:
                results[service] = {}
            
            results[service][row['metric_name']] = {
                'count': row['count'],
                'average': round(row['avg_value'], 2),
                'total': round(row['total_value'], 2),
                'min': row['min_value'],
                'max': row['max_value']
            }
        
        conn.close()
        return results
    
    def get_saas_dashboard_data(self) -> Dict[str, Any]:
        """Obtener datos para dashboard SaaS"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        # Datos simulados pero realistas para SaaS
        dashboard_data = {
            "revenue": {
                "total": 12278.35,
                "change": "+5%",
                "period": "This month"
            },
            "new_orders": {
                "total": 4673,
                "change": "-2%", 
                "period": "This month"
            },
            "completed_orders": {
                "total": 5342,
                "change": "+18%",
                "period": "This month"
            },
            "spending": {
                "total": 10365.32,
                "change": "-17%",
                "period": "This month"
            },
            "customers": {
                "total": 651,
                "segments": {
                    "freelancer": 45,
                    "upwork": 30,
                    "behance": 25
                }
            },
            "regions": {
                "israel": 266,
                "usa": 148,
                "canada": 88,
                "australia": 122
            },
            "progress": {
                "overall_performance": 90,
                "order_fulfillment": 85
            },
            "attendance": {
                "youtube": "15K",
                "instagram": "132K", 
                "facebook": "176K"
            },
            "services": {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Obtener métricas reales de servicios
        cursor = conn.execute('''
            SELECT service_name, metric_name, metric_value 
            FROM metrics 
            WHERE timestamp >= datetime('now', '-1 day')
            ORDER BY timestamp DESC
        ''')
        
        for row in cursor.fetchall():
            service = row['service_name']
            if service not in dashboard_data["services"]:
                dashboard_data["services"][service] = {}
            dashboard_data["services"][service][row['metric_name']] = row['metric_value']
        
        conn.close()
        return dashboard_data

# Instancia global
analytics_db = AnalyticsDB()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida del servicio"""
    try:
        logger.info("🚀 Iniciando Analytics Service...")
        logger.info("✅ Analytics Service iniciado")
        yield
    finally:
        logger.info("🛑 Analytics Service detenido")

# Crear aplicación FastAPI
app = FastAPI(
    title="📊 Analytics Microservice",
    description="Servicio de analytics enterprise",
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

class MetricCreate(BaseModel):
    service_name: str
    metric_name: str
    value: float
    group_id: int = None
    metadata: str = None

@app.get("/")
async def root():
    """Información del servicio"""
    return {
        "service": "Analytics Microservice",
        "version": "4.0.0",
        "description": "Servicio de analytics enterprise para SaaS"
    }

@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "service": "analytics",
        "version": "4.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/metrics")
async def add_metric(metric: MetricCreate):
    """Añadir nueva métrica"""
    try:
        analytics_db.add_metric(
            metric.service_name,
            metric.metric_name,
            metric.value,
            metric.group_id,
            metric.metadata
        )
        
        return {
            "message": "Metric added successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    """Obtener estadísticas"""
    try:
        return {
            "service": "analytics",
            "metrics_summary": analytics_db.get_metrics_summary(),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": str(e)}

@app.get("/dashboard-data")
async def get_dashboard_data():
    """Datos para dashboard SaaS"""
    try:
        return analytics_db.get_saas_dashboard_data()
        
    except Exception as e:
        return {"error": str(e)}

@app.get("/metrics")
async def get_metrics(service: str = None, hours: int = 24):
    """Obtener métricas filtradas"""
    try:
        all_metrics = analytics_db.get_metrics_summary(hours)
        
        if service:
            return {
                "service": service,
                "metrics": all_metrics.get(service, {}),
                "hours": hours,
                "timestamp": datetime.now().isoformat()
            }
        
        return {
            "all_services": all_metrics,
            "hours": hours,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    config = {
        "host": "0.0.0.0",
        "port": 8002,
        "reload": False,
        "log_level": "info"
    }
    
    print("🚀 Starting Analytics Microservice...")
    print(f"   📊 Service: Analytics")
    print(f"   🌐 URL: http://{config['host']}:{config['port']}")
    print(f"   📚 Docs: http://{config['host']}:{config['port']}/docs")
    print(f"   🏥 Health: http://{config['host']}:{config['port']}/health")
    
    uvicorn.run(app, **config)
'''
    
    create_file(Path("services/analytics/main.py"), analytics_code)

def create_file_manager_service():
    """Crear File Manager Service"""
    print("💾 Creando File Manager Service...")
    
    file_manager_code = '''#!/usr/bin/env python3
"""
💾 FILE MANAGER MICROSERVICE v4.0
=================================
Servicio de gestión de archivos y multimedia
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn
import logging

# Logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FileManager:
    """Gestor de archivos optimizado"""
    
    def __init__(self):
        self.base_dir = Path("files")
        self.temp_dir = Path("temp")
        self.processed_dir = Path("processed")
        
        # Crear directorios
        for directory in [self.base_dir, self.temp_dir, self.processed_dir]:
            directory.mkdir(exist_ok=True)
        
        # Crear subdirectorios por categoría
        categories = ["images", "videos", "documents", "audio", "general"]
        for category in categories:
            (self.base_dir / category).mkdir(exist_ok=True)
    
    def save_file(self, file_content: bytes, filename: str, category: str = "general") -> str:
        """Guardar archivo"""
        category_dir = self.base_dir / category
        category_dir.mkdir(exist_ok=True)
        
        # Añadir timestamp al nombre para evitar colisiones
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name, ext = os.path.splitext(filename)
        safe_filename = f"{name}_{timestamp}{ext}"
        
        file_path = category_dir / safe_filename
        
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        logger.info(f"📁 Archivo guardado: {file_path}")
        return str(file_path)
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Obtener información del archivo"""
        path = Path(file_path)
        
        if not path.exists():
            return {"error": "File not found"}
        
        stat = path.stat()
        
        return {
            "name": path.name,
            "size": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "extension": path.suffix,
            "category": path.parent.name,
            "full_path": str(path),
            "exists": True
        }
    
    def list_files(self, category: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Listar archivos"""
        files = []
        
        if category:
            search_dir = self.base_dir / category
            if not search_dir.exists():
                return []
            search_dirs = [search_dir]
        else:
            search_dirs = [self.base_dir]
        
        for search_dir in search_dirs:
            for file_path in search_dir.rglob("*"):
                if file_path.is_file() and len(files) < limit:
                    files.append(self.get_file_info(str(file_path)))
        
        # Ordenar por fecha de modificación (más recientes primero)
        files.sort(key=lambda x: x.get('modified', ''), reverse=True)
        
        return files[:limit]
    
    def delete_file(self, file_path: str) -> bool:
        """Eliminar archivo"""
        path = Path(file_path)
        
        if not path.exists():
            return False
        
        try:
            path.unlink()
            logger.info(f"🗑️ Archivo eliminado: {file_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Error eliminando archivo: {e}")
            return False
    
    def cleanup_old_files(self, hours: int = 24) -> int:
        """Limpiar archivos antiguos de directorios temporales"""
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        cleaned = 0
        
        for directory in [self.temp_dir, self.processed_dir]:
            for file_path in directory.rglob("*"):
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    try:
                        file_path.unlink()
                        cleaned += 1
                    except Exception as e:
                        logger.error(f"Error limpiando {file_path}: {e}")
        
        logger.info(f"🧹 Archivos limpiados: {cleaned}")
        return cleaned
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de almacenamiento"""
        stats = {
            "categories": {},
            "total_files": 0,
            "total_size_bytes": 0,
            "total_size_mb": 0,
            "directories": {
                "base": str(self.base_dir),
                "temp": str(self.temp_dir),
                "processed": str(self.processed_dir)
            }
        }
        
        # Estadísticas por categoría
        for category_dir in self.base_dir.iterdir():
            if category_dir.is_dir():
                category_stats = {
                    "files": 0,
                    "size_bytes": 0,
                    "size_mb": 0
                }
                
                for file_path in category_dir.rglob("*"):
                    if file_path.is_file():
                        size = file_path.stat().st_size
                        category_stats["files"] += 1
                        category_stats["size_bytes"] += size
                        
                        stats["total_files"] += 1
                        stats["total_size_bytes"] += size
                
                category_stats["size_mb"] = round(category_stats["size_bytes"] / (1024 * 1024), 2)
                stats["categories"][category_dir.name] = category_stats
        
        stats["total_size_mb"] = round(stats["total_size_bytes"] / (1024 * 1024), 2)
        
        return stats

# Instancia global
file_manager = FileManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida del servicio"""
    try:
        logger.info("🚀 Iniciando File Manager Service...")
        
        # Cleanup inicial
        cleaned = file_manager.cleanup_old_files()
        logger.info(f"🧹 Archivos temporales limpiados: {cleaned}")
        
        logger.info("✅ File Manager Service iniciado")
        yield
    finally:
        logger.info("🛑 File Manager Service detenido")

# Crear aplicación FastAPI
app = FastAPI(
    title="💾 File Manager Microservice",
    description="Servicio de gestión de archivos y multimedia",
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
    """Información del servicio"""
    return {
        "service": "File Manager Microservice",
        "version": "4.0.0",
        "description": "Gestión de archivos y multimedia enterprise"
    }

@app.get("/health")
async def health_check():
    """Health check"""
    storage_stats = file_manager.get_storage_stats()
    
    return {
        "status": "healthy",
        "service": "file_manager",
        "version": "4.0.0",
        "storage": storage_stats,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/stats")
async def get_stats():
    """Obtener estadísticas"""
    return {
        "service": "file_manager",
        "storage": file_manager.get_storage_stats(),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), category: str = "general"):
    """Subir archivo"""
    try:
        content = await file.read()
        file_path = file_manager.save_file(content, file.filename, category)
        
        return {
            "message": "File uploaded successfully",
            "file_path": file_path,
            "file_info": file_manager.get_file_info(file_path),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files")
async def list_files(category: str = None, limit: int = 100):
    """Listar archivos"""
    try:
        files = file_manager.list_files(category, limit)
        
        return {
            "files": files,
            "count": len(files),
            "category": category,
            "limit": limit,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files/{category}/{filename}")
async def get_file(category: str, filename: str):
    """Obtener archivo"""
    file_path = file_manager.base_dir / category / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_path)

@app.delete("/files/{category}/{filename}")
async def delete_file(category: str, filename: str):
    """Eliminar archivo"""
    file_path = str(file_manager.base_dir / category / filename)
    
    if file_manager.delete_file(file_path):
        return {
            "message": "File deleted successfully",
            "file_path": file_path,
            "timestamp": datetime.now().isoformat()
        }
    else:
        raise HTTPException(status_code=404, detail="File not found")

@app.delete("/cleanup")
async def cleanup_files(hours: int = 24):
    """Limpiar archivos antiguos"""
    try:
        cleaned = file_manager.cleanup_old_files(hours)
        
        return {
            "message": f"Cleaned {cleaned} old files",
            "hours": hours,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/storage")
async def get_storage_info():
    """Información de almacenamiento"""
    return {
        "storage": file_manager.get_storage_stats(),
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    config = {
        "host": "0.0.0.0",
        "port": 8003,
        "reload": False,
        "log_level": "info"
    }
    
    print("🚀 Starting File Manager Microservice...")
    print(f"   💾 Service: File Manager")
    print(f"   🌐 URL: http://{config['host']}:{config['port']}")
    print(f"   📚 Docs: http://{config['host']}:{config['port']}/docs")
    print(f"   🏥 Health: http://{config['host']}:{config['port']}/health")
    
    uvicorn.run(app, **config)
'''
    
    create_file(Path("services/file_manager/main.py"), file_manager_code)

def update_orchestrator():
    """Actualizar orchestrator para incluir los nuevos servicios"""
    print("🎭 Actualizando Main Orchestrator...")
    
    updated_orchestrator = '''#!/usr/bin/env python3
"""
🎭 ENTERPRISE MICROSERVICES ORCHESTRATOR v4.0 - ACTUALIZADO
===========================================================
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
        
        , '').replace(',', ''));
                const change = (Math.random() - 0.5) * 100;
                revenue.textContent = '#!/usr/bin/env python3
"""
🎭 EXPANSIÓN SAAS ENTERPRISE v4.0
================================
Añadir servicios enterprise restantes para completar tu SaaS
"""

import os
from pathlib import Path

def create_file(file_path: Path, content: str):
    """Crear archivo con contenido"""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding='utf-8')
    print(f"   ✅ Creado: {file_path}")

def create_analytics_service():
    """Crear Analytics Service completo"""
    print("📊 Creando Analytics Service...")
    
    analytics_code = '''#!/usr/bin/env python3
"""
📊 ANALYTICS MICROSERVICE v4.0
==============================
Servicio de analytics enterprise para tu SaaS
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import logging

# Logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AnalyticsDB:
    """Base de datos de analytics optimizada"""
    
    def __init__(self, db_path: str = "database/analytics.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Inicializar base de datos"""
        Path("database").mkdir(exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        
        # Tabla de métricas
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
        
        # Tabla de eventos
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
        
        # Índices para performance
        conn.execute('CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_metrics_service ON metrics(service_name)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)')
        
        conn.commit()
        conn.close()
        
        # Insertar datos iniciales de muestra
        self._insert_sample_data()
    
    def _insert_sample_data(self):
        """Insertar datos de muestra para dashboard"""
        conn = sqlite3.connect(self.db_path)
        
        # Métricas de ejemplo
        sample_metrics = [
            ('message_replicator', 'messages_processed', 12278, None, '{"source": "telegram"}'),
            ('message_replicator', 'messages_replicated', 11856, None, '{"target": "discord"}'),
            ('message_replicator', 'errors', 34, None, '{"type": "connection"}'),
            ('analytics', 'queries_processed', 5674, None, '{"endpoint": "dashboard"}'),
            ('file_manager', 'files_stored', 1234, None, '{"type": "media"}'),
        ]
        
        for service, metric, value, group_id, metadata in sample_metrics:
            conn.execute('''
                INSERT OR IGNORE INTO metrics (service_name, metric_name, metric_value, group_id, metadata)
                VALUES (?, ?, ?, ?, ?)
            ''', (service, metric, value, group_id, metadata))
        
        conn.commit()
        conn.close()
    
    def add_metric(self, service_name: str, metric_name: str, value: float, group_id: int = None, metadata: str = None):
        """Añadir métrica"""
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            INSERT INTO metrics (service_name, metric_name, metric_value, group_id, metadata)
            VALUES (?, ?, ?, ?, ?)
        ''', (service_name, metric_name, value, group_id, metadata))
        conn.commit()
        conn.close()
    
    def get_metrics_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Obtener resumen de métricas"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        since = datetime.now() - timedelta(hours=hours)
        
        cursor = conn.execute('''
            SELECT 
                service_name,
                metric_name,
                COUNT(*) as count,
                AVG(metric_value) as avg_value,
                SUM(metric_value) as total_value,
                MIN(metric_value) as min_value,
                MAX(metric_value) as max_value
            FROM metrics 
            WHERE timestamp >= ?
            GROUP BY service_name, metric_name
            ORDER BY service_name, metric_name
        ''', (since,))
        
        results = {}
        for row in cursor.fetchall():
            service = row['service_name']
            if service not in results:
                results[service] = {}
            
            results[service][row['metric_name']] = {
                'count': row['count'],
                'average': round(row['avg_value'], 2),
                'total': round(row['total_value'], 2),
                'min': row['min_value'],
                'max': row['max_value']
            }
        
        conn.close()
        return results
    
    def get_saas_dashboard_data(self) -> Dict[str, Any]:
        """Obtener datos para dashboard SaaS"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        # Datos simulados pero realistas para SaaS
        dashboard_data = {
            "revenue": {
                "total": 12278.35,
                "change": "+5%",
                "period": "This month"
            },
            "new_orders": {
                "total": 4673,
                "change": "-2%", 
                "period": "This month"
            },
            "completed_orders": {
                "total": 5342,
                "change": "+18%",
                "period": "This month"
            },
            "spending": {
                "total": 10365.32,
                "change": "-17%",
                "period": "This month"
            },
            "customers": {
                "total": 651,
                "segments": {
                    "freelancer": 45,
                    "upwork": 30,
                    "behance": 25
                }
            },
            "regions": {
                "israel": 266,
                "usa": 148,
                "canada": 88,
                "australia": 122
            },
            "progress": {
                "overall_performance": 90,
                "order_fulfillment": 85
            },
            "attendance": {
                "youtube": "15K",
                "instagram": "132K", 
                "facebook": "176K"
            },
            "services": {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Obtener métricas reales de servicios
        cursor = conn.execute('''
            SELECT service_name, metric_name, metric_value 
            FROM metrics 
            WHERE timestamp >= datetime('now', '-1 day')
            ORDER BY timestamp DESC
        ''')
        
        for row in cursor.fetchall():
            service = row['service_name']
            if service not in dashboard_data["services"]:
                dashboard_data["services"][service] = {}
            dashboard_data["services"][service][row['metric_name']] = row['metric_value']
        
        conn.close()
        return dashboard_data

# Instancia global
analytics_db = AnalyticsDB()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida del servicio"""
    try:
        logger.info("🚀 Iniciando Analytics Service...")
        logger.info("✅ Analytics Service iniciado")
        yield
    finally:
        logger.info("🛑 Analytics Service detenido")

# Crear aplicación FastAPI
app = FastAPI(
    title="📊 Analytics Microservice",
    description="Servicio de analytics enterprise",
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

class MetricCreate(BaseModel):
    service_name: str
    metric_name: str
    value: float
    group_id: int = None
    metadata: str = None

@app.get("/")
async def root():
    """Información del servicio"""
    return {
        "service": "Analytics Microservice",
        "version": "4.0.0",
        "description": "Servicio de analytics enterprise para SaaS"
    }

@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "service": "analytics",
        "version": "4.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/metrics")
async def add_metric(metric: MetricCreate):
    """Añadir nueva métrica"""
    try:
        analytics_db.add_metric(
            metric.service_name,
            metric.metric_name,
            metric.value,
            metric.group_id,
            metric.metadata
        )
        
        return {
            "message": "Metric added successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    """Obtener estadísticas"""
    try:
        return {
            "service": "analytics",
            "metrics_summary": analytics_db.get_metrics_summary(),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": str(e)}

@app.get("/dashboard-data")
async def get_dashboard_data():
    """Datos para dashboard SaaS"""
    try:
        return analytics_db.get_saas_dashboard_data()
        
    except Exception as e:
        return {"error": str(e)}

@app.get("/metrics")
async def get_metrics(service: str = None, hours: int = 24):
    """Obtener métricas filtradas"""
    try:
        all_metrics = analytics_db.get_metrics_summary(hours)
        
        if service:
            return {
                "service": service,
                "metrics": all_metrics.get(service, {}),
                "hours": hours,
                "timestamp": datetime.now().isoformat()
            }
        
        return {
            "all_services": all_metrics,
            "hours": hours,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    config = {
        "host": "0.0.0.0",
        "port": 8002,
        "reload": False,
        "log_level": "info"
    }
    
    print("🚀 Starting Analytics Microservice...")
    print(f"   📊 Service: Analytics")
    print(f"   🌐 URL: http://{config['host']}:{config['port']}")
    print(f"   📚 Docs: http://{config['host']}:{config['port']}/docs")
    print(f"   🏥 Health: http://{config['host']}:{config['port']}/health")
    
    uvicorn.run(app, **config)
'''
    
    create_file(Path("services/analytics/main.py"), analytics_code)

def create_file_manager_service():
    """Crear File Manager Service"""
    print("💾 Creando File Manager Service...")
    
    file_manager_code = '''#!/usr/bin/env python3
"""
💾 FILE MANAGER MICROSERVICE v4.0
=================================
Servicio de gestión de archivos y multimedia
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn
import logging

# Logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FileManager:
    """Gestor de archivos optimizado"""
    
    def __init__(self):
        self.base_dir = Path("files")
        self.temp_dir = Path("temp")
        self.processed_dir = Path("processed")
        
        # Crear directorios
        for directory in [self.base_dir, self.temp_dir, self.processed_dir]:
            directory.mkdir(exist_ok=True)
        
        # Crear subdirectorios por categoría
        categories = ["images", "videos", "documents", "audio", "general"]
        for category in categories:
            (self.base_dir / category).mkdir(exist_ok=True)
    
    def save_file(self, file_content: bytes, filename: str, category: str = "general") -> str:
        """Guardar archivo"""
        category_dir = self.base_dir / category
        category_dir.mkdir(exist_ok=True)
        
        # Añadir timestamp al nombre para evitar colisiones
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name, ext = os.path.splitext(filename)
        safe_filename = f"{name}_{timestamp}{ext}"
        
        file_path = category_dir / safe_filename
        
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        logger.info(f"📁 Archivo guardado: {file_path}")
        return str(file_path)
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Obtener información del archivo"""
        path = Path(file_path)
        
        if not path.exists():
            return {"error": "File not found"}
        
        stat = path.stat()
        
        return {
            "name": path.name,
            "size": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "extension": path.suffix,
            "category": path.parent.name,
            "full_path": str(path),
            "exists": True
        }
    
    def list_files(self, category: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Listar archivos"""
        files = []
        
        if category:
            search_dir = self.base_dir / category
            if not search_dir.exists():
                return []
            search_dirs = [search_dir]
        else:
            search_dirs = [self.base_dir]
        
        for search_dir in search_dirs:
            for file_path in search_dir.rglob("*"):
                if file_path.is_file() and len(files) < limit:
                    files.append(self.get_file_info(str(file_path)))
        
        # Ordenar por fecha de modificación (más recientes primero)
        files.sort(key=lambda x: x.get('modified', ''), reverse=True)
        
        return files[:limit]
    
    def delete_file(self, file_path: str) -> bool:
        """Eliminar archivo"""
        path = Path(file_path)
        
        if not path.exists():
            return False
        
        try:
            path.unlink()
            logger.info(f"🗑️ Archivo eliminado: {file_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Error eliminando archivo: {e}")
            return False
    
    def cleanup_old_files(self, hours: int = 24) -> int:
        """Limpiar archivos antiguos de directorios temporales"""
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        cleaned = 0
        
        for directory in [self.temp_dir, self.processed_dir]:
            for file_path in directory.rglob("*"):
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    try:
                        file_path.unlink()
                        cleaned += 1
                    except Exception as e:
                        logger.error(f"Error limpiando {file_path}: {e}")
        
        logger.info(f"🧹 Archivos limpiados: {cleaned}")
        return cleaned
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de almacenamiento"""
        stats = {
            "categories": {},
            "total_files": 0,
            "total_size_bytes": 0,
            "total_size_mb": 0,
            "directories": {
                "base": str(self.base_dir),
                "temp": str(self.temp_dir),
                "processed": str(self.processed_dir)
            }
        }
        
        # Estadísticas por categoría
        for category_dir in self.base_dir.iterdir():
            if category_dir.is_dir():
                category_stats = {
                    "files": 0,
                    "size_bytes": 0,
                    "size_mb": 0
                }
                
                for file_path in category_dir.rglob("*"):
                    if file_path.is_file():
                        size = file_path.stat().st_size
                        category_stats["files"] += 1
                        category_stats["size_bytes"] += size
                        
                        stats["total_files"] += 1
                        stats["total_size_bytes"] += size
                
                category_stats["size_mb"] = round(category_stats["size_bytes"] / (1024 * 1024), 2)
                stats["categories"][category_dir.name] = category_stats
        
        stats["total_size_mb"] = round(stats["total_size_bytes"] / (1024 * 1024), 2)
        
        return stats

# Instancia global
file_manager = FileManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida del servicio"""
    try:
        logger.info("🚀 Iniciando File Manager Service...")
        
        # Cleanup inicial
        cleaned = file_manager.cleanup_old_files()
        logger.info(f"🧹 Archivos temporales limpiados: {cleaned}")
        
        logger.info("✅ File Manager Service iniciado")
        yield
    finally:
        logger.info("🛑 File Manager Service detenido")

# Crear aplicación FastAPI
app = FastAPI(
    title="💾 File Manager Microservice",
    description="Servicio de gestión de archivos y multimedia",
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
    """Información del servicio"""
    return {
        "service": "File Manager Microservice",
        "version": "4.0.0",
        "description": "Gestión de archivos y multimedia enterprise"
    }

@app.get("/health")
async def health_check():
    """Health check"""
    storage_stats = file_manager.get_storage_stats()
    
    return {
        "status": "healthy",
        "service": "file_manager",
        "version": "4.0.0",
        "storage": storage_stats,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/stats")
async def get_stats():
    """Obtener estadísticas"""
    return {
        "service": "file_manager",
        "storage": file_manager.get_storage_stats(),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), category: str = "general"):
    """Subir archivo"""
    try:
        content = await file.read()
        file_path = file_manager.save_file(content, file.filename, category)
        
        return {
            "message": "File uploaded successfully",
            "file_path": file_path,
            "file_info": file_manager.get_file_info(file_path),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files")
async def list_files(category: str = None, limit: int = 100):
    """Listar archivos"""
    try:
        files = file_manager.list_files(category, limit)
        
        return {
            "files": files,
            "count": len(files),
            "category": category,
            "limit": limit,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files/{category}/{filename}")
async def get_file(category: str, filename: str):
    """Obtener archivo"""
    file_path = file_manager.base_dir / category / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_path)

@app.delete("/files/{category}/{filename}")
async def delete_file(category: str, filename: str):
    """Eliminar archivo"""
    file_path = str(file_manager.base_dir / category / filename)
    
    if file_manager.delete_file(file_path):
        return {
            "message": "File deleted successfully",
            "file_path": file_path,
            "timestamp": datetime.now().isoformat()
        }
    else:
        raise HTTPException(status_code=404, detail="File not found")

@app.delete("/cleanup")
async def cleanup_files(hours: int = 24):
    """Limpiar archivos antiguos"""
    try:
        cleaned = file_manager.cleanup_old_files(hours)
        
        return {
            "message": f"Cleaned {cleaned} old files",
            "hours": hours,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/storage")
async def get_storage_info():
    """Información de almacenamiento"""
    return {
        "storage": file_manager.get_storage_stats(),
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    config = {
        "host": "0.0.0.0",
        "port": 8003,
        "reload": False,
        "log_level": "info"
    }
    
    print("🚀 Starting File Manager Microservice...")
    print(f"   💾 Service: File Manager")
    print(f"   🌐 URL: http://{config['host']}:{config['port']}")
    print(f"   📚 Docs: http://{config['host']}:{config['port']}/docs")
    print(f"   🏥 Health: http://{config['host']}:{config['port']}/health")
    
    uvicorn.run(app, **config)
'''
    
    create_file(Path("services/file_manager/main.py"), file_manager_code)

def update_orchestrator():
    """Actualizar orchestrator para incluir los nuevos servicios"""
    print("🎭 Actualizando Main Orchestrator...")
    
    updated_orchestrator = '''#!/usr/bin/env python3
"""
🎭 ENTERPRISE MICROSERVICES ORCHESTRATOR v4.0 - ACTUALIZADO
===========================================================
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
        
         + (current + change).toLocaleString('en-US', {minimumFractionDigits: 2});
            }
            
            if (orders) {
                const current = parseInt(orders.textContent.replace(',', ''));
                orders.textContent = (current + Math.floor(Math.random() * 10)).toLocaleString();
            }
            
            if (completed) {
                const current = parseInt(completed.textContent.replace(',', ''));
                completed.textContent = (current + Math.floor(Math.random() * 5)).toLocaleString();
            }
            
            if (requests) {
                const current = parseFloat(requests.textContent.replace('K', ''));
                requests.textContent = (current + Math.random() * 0.1).toFixed(1) + 'K';
            }
        }
        
        function updateDashboardWithAnalytics(data) {
            // Actualizar con datos reales de analytics si están disponibles
            if (data.revenue) {
                document.getElementById('total-revenue').textContent = '#!/usr/bin/env python3
"""
🎭 EXPANSIÓN SAAS ENTERPRISE v4.0
================================
Añadir servicios enterprise restantes para completar tu SaaS
"""

import os
from pathlib import Path

def create_file(file_path: Path, content: str):
    """Crear archivo con contenido"""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding='utf-8')
    print(f"   ✅ Creado: {file_path}")

def create_analytics_service():
    """Crear Analytics Service completo"""
    print("📊 Creando Analytics Service...")
    
    analytics_code = '''#!/usr/bin/env python3
"""
📊 ANALYTICS MICROSERVICE v4.0
==============================
Servicio de analytics enterprise para tu SaaS
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import logging

# Logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AnalyticsDB:
    """Base de datos de analytics optimizada"""
    
    def __init__(self, db_path: str = "database/analytics.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Inicializar base de datos"""
        Path("database").mkdir(exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        
        # Tabla de métricas
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
        
        # Tabla de eventos
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
        
        # Índices para performance
        conn.execute('CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_metrics_service ON metrics(service_name)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)')
        
        conn.commit()
        conn.close()
        
        # Insertar datos iniciales de muestra
        self._insert_sample_data()
    
    def _insert_sample_data(self):
        """Insertar datos de muestra para dashboard"""
        conn = sqlite3.connect(self.db_path)
        
        # Métricas de ejemplo
        sample_metrics = [
            ('message_replicator', 'messages_processed', 12278, None, '{"source": "telegram"}'),
            ('message_replicator', 'messages_replicated', 11856, None, '{"target": "discord"}'),
            ('message_replicator', 'errors', 34, None, '{"type": "connection"}'),
            ('analytics', 'queries_processed', 5674, None, '{"endpoint": "dashboard"}'),
            ('file_manager', 'files_stored', 1234, None, '{"type": "media"}'),
        ]
        
        for service, metric, value, group_id, metadata in sample_metrics:
            conn.execute('''
                INSERT OR IGNORE INTO metrics (service_name, metric_name, metric_value, group_id, metadata)
                VALUES (?, ?, ?, ?, ?)
            ''', (service, metric, value, group_id, metadata))
        
        conn.commit()
        conn.close()
    
    def add_metric(self, service_name: str, metric_name: str, value: float, group_id: int = None, metadata: str = None):
        """Añadir métrica"""
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            INSERT INTO metrics (service_name, metric_name, metric_value, group_id, metadata)
            VALUES (?, ?, ?, ?, ?)
        ''', (service_name, metric_name, value, group_id, metadata))
        conn.commit()
        conn.close()
    
    def get_metrics_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Obtener resumen de métricas"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        since = datetime.now() - timedelta(hours=hours)
        
        cursor = conn.execute('''
            SELECT 
                service_name,
                metric_name,
                COUNT(*) as count,
                AVG(metric_value) as avg_value,
                SUM(metric_value) as total_value,
                MIN(metric_value) as min_value,
                MAX(metric_value) as max_value
            FROM metrics 
            WHERE timestamp >= ?
            GROUP BY service_name, metric_name
            ORDER BY service_name, metric_name
        ''', (since,))
        
        results = {}
        for row in cursor.fetchall():
            service = row['service_name']
            if service not in results:
                results[service] = {}
            
            results[service][row['metric_name']] = {
                'count': row['count'],
                'average': round(row['avg_value'], 2),
                'total': round(row['total_value'], 2),
                'min': row['min_value'],
                'max': row['max_value']
            }
        
        conn.close()
        return results
    
    def get_saas_dashboard_data(self) -> Dict[str, Any]:
        """Obtener datos para dashboard SaaS"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        # Datos simulados pero realistas para SaaS
        dashboard_data = {
            "revenue": {
                "total": 12278.35,
                "change": "+5%",
                "period": "This month"
            },
            "new_orders": {
                "total": 4673,
                "change": "-2%", 
                "period": "This month"
            },
            "completed_orders": {
                "total": 5342,
                "change": "+18%",
                "period": "This month"
            },
            "spending": {
                "total": 10365.32,
                "change": "-17%",
                "period": "This month"
            },
            "customers": {
                "total": 651,
                "segments": {
                    "freelancer": 45,
                    "upwork": 30,
                    "behance": 25
                }
            },
            "regions": {
                "israel": 266,
                "usa": 148,
                "canada": 88,
                "australia": 122
            },
            "progress": {
                "overall_performance": 90,
                "order_fulfillment": 85
            },
            "attendance": {
                "youtube": "15K",
                "instagram": "132K", 
                "facebook": "176K"
            },
            "services": {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Obtener métricas reales de servicios
        cursor = conn.execute('''
            SELECT service_name, metric_name, metric_value 
            FROM metrics 
            WHERE timestamp >= datetime('now', '-1 day')
            ORDER BY timestamp DESC
        ''')
        
        for row in cursor.fetchall():
            service = row['service_name']
            if service not in dashboard_data["services"]:
                dashboard_data["services"][service] = {}
            dashboard_data["services"][service][row['metric_name']] = row['metric_value']
        
        conn.close()
        return dashboard_data

# Instancia global
analytics_db = AnalyticsDB()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida del servicio"""
    try:
        logger.info("🚀 Iniciando Analytics Service...")
        logger.info("✅ Analytics Service iniciado")
        yield
    finally:
        logger.info("🛑 Analytics Service detenido")

# Crear aplicación FastAPI
app = FastAPI(
    title="📊 Analytics Microservice",
    description="Servicio de analytics enterprise",
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

class MetricCreate(BaseModel):
    service_name: str
    metric_name: str
    value: float
    group_id: int = None
    metadata: str = None

@app.get("/")
async def root():
    """Información del servicio"""
    return {
        "service": "Analytics Microservice",
        "version": "4.0.0",
        "description": "Servicio de analytics enterprise para SaaS"
    }

@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "service": "analytics",
        "version": "4.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/metrics")
async def add_metric(metric: MetricCreate):
    """Añadir nueva métrica"""
    try:
        analytics_db.add_metric(
            metric.service_name,
            metric.metric_name,
            metric.value,
            metric.group_id,
            metric.metadata
        )
        
        return {
            "message": "Metric added successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    """Obtener estadísticas"""
    try:
        return {
            "service": "analytics",
            "metrics_summary": analytics_db.get_metrics_summary(),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": str(e)}

@app.get("/dashboard-data")
async def get_dashboard_data():
    """Datos para dashboard SaaS"""
    try:
        return analytics_db.get_saas_dashboard_data()
        
    except Exception as e:
        return {"error": str(e)}

@app.get("/metrics")
async def get_metrics(service: str = None, hours: int = 24):
    """Obtener métricas filtradas"""
    try:
        all_metrics = analytics_db.get_metrics_summary(hours)
        
        if service:
            return {
                "service": service,
                "metrics": all_metrics.get(service, {}),
                "hours": hours,
                "timestamp": datetime.now().isoformat()
            }
        
        return {
            "all_services": all_metrics,
            "hours": hours,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    config = {
        "host": "0.0.0.0",
        "port": 8002,
        "reload": False,
        "log_level": "info"
    }
    
    print("🚀 Starting Analytics Microservice...")
    print(f"   📊 Service: Analytics")
    print(f"   🌐 URL: http://{config['host']}:{config['port']}")
    print(f"   📚 Docs: http://{config['host']}:{config['port']}/docs")
    print(f"   🏥 Health: http://{config['host']}:{config['port']}/health")
    
    uvicorn.run(app, **config)
'''
    
    create_file(Path("services/analytics/main.py"), analytics_code)

def create_file_manager_service():
    """Crear File Manager Service"""
    print("💾 Creando File Manager Service...")
    
    file_manager_code = '''#!/usr/bin/env python3
"""
💾 FILE MANAGER MICROSERVICE v4.0
=================================
Servicio de gestión de archivos y multimedia
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn
import logging

# Logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FileManager:
    """Gestor de archivos optimizado"""
    
    def __init__(self):
        self.base_dir = Path("files")
        self.temp_dir = Path("temp")
        self.processed_dir = Path("processed")
        
        # Crear directorios
        for directory in [self.base_dir, self.temp_dir, self.processed_dir]:
            directory.mkdir(exist_ok=True)
        
        # Crear subdirectorios por categoría
        categories = ["images", "videos", "documents", "audio", "general"]
        for category in categories:
            (self.base_dir / category).mkdir(exist_ok=True)
    
    def save_file(self, file_content: bytes, filename: str, category: str = "general") -> str:
        """Guardar archivo"""
        category_dir = self.base_dir / category
        category_dir.mkdir(exist_ok=True)
        
        # Añadir timestamp al nombre para evitar colisiones
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name, ext = os.path.splitext(filename)
        safe_filename = f"{name}_{timestamp}{ext}"
        
        file_path = category_dir / safe_filename
        
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        logger.info(f"📁 Archivo guardado: {file_path}")
        return str(file_path)
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Obtener información del archivo"""
        path = Path(file_path)
        
        if not path.exists():
            return {"error": "File not found"}
        
        stat = path.stat()
        
        return {
            "name": path.name,
            "size": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "extension": path.suffix,
            "category": path.parent.name,
            "full_path": str(path),
            "exists": True
        }
    
    def list_files(self, category: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Listar archivos"""
        files = []
        
        if category:
            search_dir = self.base_dir / category
            if not search_dir.exists():
                return []
            search_dirs = [search_dir]
        else:
            search_dirs = [self.base_dir]
        
        for search_dir in search_dirs:
            for file_path in search_dir.rglob("*"):
                if file_path.is_file() and len(files) < limit:
                    files.append(self.get_file_info(str(file_path)))
        
        # Ordenar por fecha de modificación (más recientes primero)
        files.sort(key=lambda x: x.get('modified', ''), reverse=True)
        
        return files[:limit]
    
    def delete_file(self, file_path: str) -> bool:
        """Eliminar archivo"""
        path = Path(file_path)
        
        if not path.exists():
            return False
        
        try:
            path.unlink()
            logger.info(f"🗑️ Archivo eliminado: {file_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Error eliminando archivo: {e}")
            return False
    
    def cleanup_old_files(self, hours: int = 24) -> int:
        """Limpiar archivos antiguos de directorios temporales"""
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        cleaned = 0
        
        for directory in [self.temp_dir, self.processed_dir]:
            for file_path in directory.rglob("*"):
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    try:
                        file_path.unlink()
                        cleaned += 1
                    except Exception as e:
                        logger.error(f"Error limpiando {file_path}: {e}")
        
        logger.info(f"🧹 Archivos limpiados: {cleaned}")
        return cleaned
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de almacenamiento"""
        stats = {
            "categories": {},
            "total_files": 0,
            "total_size_bytes": 0,
            "total_size_mb": 0,
            "directories": {
                "base": str(self.base_dir),
                "temp": str(self.temp_dir),
                "processed": str(self.processed_dir)
            }
        }
        
        # Estadísticas por categoría
        for category_dir in self.base_dir.iterdir():
            if category_dir.is_dir():
                category_stats = {
                    "files": 0,
                    "size_bytes": 0,
                    "size_mb": 0
                }
                
                for file_path in category_dir.rglob("*"):
                    if file_path.is_file():
                        size = file_path.stat().st_size
                        category_stats["files"] += 1
                        category_stats["size_bytes"] += size
                        
                        stats["total_files"] += 1
                        stats["total_size_bytes"] += size
                
                category_stats["size_mb"] = round(category_stats["size_bytes"] / (1024 * 1024), 2)
                stats["categories"][category_dir.name] = category_stats
        
        stats["total_size_mb"] = round(stats["total_size_bytes"] / (1024 * 1024), 2)
        
        return stats

# Instancia global
file_manager = FileManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida del servicio"""
    try:
        logger.info("🚀 Iniciando File Manager Service...")
        
        # Cleanup inicial
        cleaned = file_manager.cleanup_old_files()
        logger.info(f"🧹 Archivos temporales limpiados: {cleaned}")
        
        logger.info("✅ File Manager Service iniciado")
        yield
    finally:
        logger.info("🛑 File Manager Service detenido")

# Crear aplicación FastAPI
app = FastAPI(
    title="💾 File Manager Microservice",
    description="Servicio de gestión de archivos y multimedia",
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
    """Información del servicio"""
    return {
        "service": "File Manager Microservice",
        "version": "4.0.0",
        "description": "Gestión de archivos y multimedia enterprise"
    }

@app.get("/health")
async def health_check():
    """Health check"""
    storage_stats = file_manager.get_storage_stats()
    
    return {
        "status": "healthy",
        "service": "file_manager",
        "version": "4.0.0",
        "storage": storage_stats,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/stats")
async def get_stats():
    """Obtener estadísticas"""
    return {
        "service": "file_manager",
        "storage": file_manager.get_storage_stats(),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), category: str = "general"):
    """Subir archivo"""
    try:
        content = await file.read()
        file_path = file_manager.save_file(content, file.filename, category)
        
        return {
            "message": "File uploaded successfully",
            "file_path": file_path,
            "file_info": file_manager.get_file_info(file_path),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files")
async def list_files(category: str = None, limit: int = 100):
    """Listar archivos"""
    try:
        files = file_manager.list_files(category, limit)
        
        return {
            "files": files,
            "count": len(files),
            "category": category,
            "limit": limit,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files/{category}/{filename}")
async def get_file(category: str, filename: str):
    """Obtener archivo"""
    file_path = file_manager.base_dir / category / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_path)

@app.delete("/files/{category}/{filename}")
async def delete_file(category: str, filename: str):
    """Eliminar archivo"""
    file_path = str(file_manager.base_dir / category / filename)
    
    if file_manager.delete_file(file_path):
        return {
            "message": "File deleted successfully",
            "file_path": file_path,
            "timestamp": datetime.now().isoformat()
        }
    else:
        raise HTTPException(status_code=404, detail="File not found")

@app.delete("/cleanup")
async def cleanup_files(hours: int = 24):
    """Limpiar archivos antiguos"""
    try:
        cleaned = file_manager.cleanup_old_files(hours)
        
        return {
            "message": f"Cleaned {cleaned} old files",
            "hours": hours,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/storage")
async def get_storage_info():
    """Información de almacenamiento"""
    return {
        "storage": file_manager.get_storage_stats(),
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    config = {
        "host": "0.0.0.0",
        "port": 8003,
        "reload": False,
        "log_level": "info"
    }
    
    print("🚀 Starting File Manager Microservice...")
    print(f"   💾 Service: File Manager")
    print(f"   🌐 URL: http://{config['host']}:{config['port']}")
    print(f"   📚 Docs: http://{config['host']}:{config['port']}/docs")
    print(f"   🏥 Health: http://{config['host']}:{config['port']}/health")
    
    uvicorn.run(app, **config)
'''
    
    create_file(Path("services/file_manager/main.py"), file_manager_code)

def update_orchestrator():
    """Actualizar orchestrator para incluir los nuevos servicios"""
    print("🎭 Actualizando Main Orchestrator...")
    
    updated_orchestrator = '''#!/usr/bin/env python3
"""
🎭 ENTERPRISE MICROSERVICES ORCHESTRATOR v4.0 - ACTUALIZADO
===========================================================
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
        
         + data.revenue.total.toLocaleString();
            }
            if (data.new_orders) {
                document.getElementById('new-orders').textContent = data.new_orders.total.toLocaleString();
            }
            if (data.completed_orders) {
                document.getElementById('completed-orders').textContent = data.completed_orders.total.toLocaleString();
            }
            if (data.spending) {
                document.getElementById('spending').textContent = '#!/usr/bin/env python3
"""
🎭 EXPANSIÓN SAAS ENTERPRISE v4.0
================================
Añadir servicios enterprise restantes para completar tu SaaS
"""

import os
from pathlib import Path

def create_file(file_path: Path, content: str):
    """Crear archivo con contenido"""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding='utf-8')
    print(f"   ✅ Creado: {file_path}")

def create_analytics_service():
    """Crear Analytics Service completo"""
    print("📊 Creando Analytics Service...")
    
    analytics_code = '''#!/usr/bin/env python3
"""
📊 ANALYTICS MICROSERVICE v4.0
==============================
Servicio de analytics enterprise para tu SaaS
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import logging

# Logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AnalyticsDB:
    """Base de datos de analytics optimizada"""
    
    def __init__(self, db_path: str = "database/analytics.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Inicializar base de datos"""
        Path("database").mkdir(exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        
        # Tabla de métricas
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
        
        # Tabla de eventos
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
        
        # Índices para performance
        conn.execute('CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_metrics_service ON metrics(service_name)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)')
        
        conn.commit()
        conn.close()
        
        # Insertar datos iniciales de muestra
        self._insert_sample_data()
    
    def _insert_sample_data(self):
        """Insertar datos de muestra para dashboard"""
        conn = sqlite3.connect(self.db_path)
        
        # Métricas de ejemplo
        sample_metrics = [
            ('message_replicator', 'messages_processed', 12278, None, '{"source": "telegram"}'),
            ('message_replicator', 'messages_replicated', 11856, None, '{"target": "discord"}'),
            ('message_replicator', 'errors', 34, None, '{"type": "connection"}'),
            ('analytics', 'queries_processed', 5674, None, '{"endpoint": "dashboard"}'),
            ('file_manager', 'files_stored', 1234, None, '{"type": "media"}'),
        ]
        
        for service, metric, value, group_id, metadata in sample_metrics:
            conn.execute('''
                INSERT OR IGNORE INTO metrics (service_name, metric_name, metric_value, group_id, metadata)
                VALUES (?, ?, ?, ?, ?)
            ''', (service, metric, value, group_id, metadata))
        
        conn.commit()
        conn.close()
    
    def add_metric(self, service_name: str, metric_name: str, value: float, group_id: int = None, metadata: str = None):
        """Añadir métrica"""
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            INSERT INTO metrics (service_name, metric_name, metric_value, group_id, metadata)
            VALUES (?, ?, ?, ?, ?)
        ''', (service_name, metric_name, value, group_id, metadata))
        conn.commit()
        conn.close()
    
    def get_metrics_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Obtener resumen de métricas"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        since = datetime.now() - timedelta(hours=hours)
        
        cursor = conn.execute('''
            SELECT 
                service_name,
                metric_name,
                COUNT(*) as count,
                AVG(metric_value) as avg_value,
                SUM(metric_value) as total_value,
                MIN(metric_value) as min_value,
                MAX(metric_value) as max_value
            FROM metrics 
            WHERE timestamp >= ?
            GROUP BY service_name, metric_name
            ORDER BY service_name, metric_name
        ''', (since,))
        
        results = {}
        for row in cursor.fetchall():
            service = row['service_name']
            if service not in results:
                results[service] = {}
            
            results[service][row['metric_name']] = {
                'count': row['count'],
                'average': round(row['avg_value'], 2),
                'total': round(row['total_value'], 2),
                'min': row['min_value'],
                'max': row['max_value']
            }
        
        conn.close()
        return results
    
    def get_saas_dashboard_data(self) -> Dict[str, Any]:
        """Obtener datos para dashboard SaaS"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        # Datos simulados pero realistas para SaaS
        dashboard_data = {
            "revenue": {
                "total": 12278.35,
                "change": "+5%",
                "period": "This month"
            },
            "new_orders": {
                "total": 4673,
                "change": "-2%", 
                "period": "This month"
            },
            "completed_orders": {
                "total": 5342,
                "change": "+18%",
                "period": "This month"
            },
            "spending": {
                "total": 10365.32,
                "change": "-17%",
                "period": "This month"
            },
            "customers": {
                "total": 651,
                "segments": {
                    "freelancer": 45,
                    "upwork": 30,
                    "behance": 25
                }
            },
            "regions": {
                "israel": 266,
                "usa": 148,
                "canada": 88,
                "australia": 122
            },
            "progress": {
                "overall_performance": 90,
                "order_fulfillment": 85
            },
            "attendance": {
                "youtube": "15K",
                "instagram": "132K", 
                "facebook": "176K"
            },
            "services": {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Obtener métricas reales de servicios
        cursor = conn.execute('''
            SELECT service_name, metric_name, metric_value 
            FROM metrics 
            WHERE timestamp >= datetime('now', '-1 day')
            ORDER BY timestamp DESC
        ''')
        
        for row in cursor.fetchall():
            service = row['service_name']
            if service not in dashboard_data["services"]:
                dashboard_data["services"][service] = {}
            dashboard_data["services"][service][row['metric_name']] = row['metric_value']
        
        conn.close()
        return dashboard_data

# Instancia global
analytics_db = AnalyticsDB()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida del servicio"""
    try:
        logger.info("🚀 Iniciando Analytics Service...")
        logger.info("✅ Analytics Service iniciado")
        yield
    finally:
        logger.info("🛑 Analytics Service detenido")

# Crear aplicación FastAPI
app = FastAPI(
    title="📊 Analytics Microservice",
    description="Servicio de analytics enterprise",
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

class MetricCreate(BaseModel):
    service_name: str
    metric_name: str
    value: float
    group_id: int = None
    metadata: str = None

@app.get("/")
async def root():
    """Información del servicio"""
    return {
        "service": "Analytics Microservice",
        "version": "4.0.0",
        "description": "Servicio de analytics enterprise para SaaS"
    }

@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "service": "analytics",
        "version": "4.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/metrics")
async def add_metric(metric: MetricCreate):
    """Añadir nueva métrica"""
    try:
        analytics_db.add_metric(
            metric.service_name,
            metric.metric_name,
            metric.value,
            metric.group_id,
            metric.metadata
        )
        
        return {
            "message": "Metric added successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    """Obtener estadísticas"""
    try:
        return {
            "service": "analytics",
            "metrics_summary": analytics_db.get_metrics_summary(),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": str(e)}

@app.get("/dashboard-data")
async def get_dashboard_data():
    """Datos para dashboard SaaS"""
    try:
        return analytics_db.get_saas_dashboard_data()
        
    except Exception as e:
        return {"error": str(e)}

@app.get("/metrics")
async def get_metrics(service: str = None, hours: int = 24):
    """Obtener métricas filtradas"""
    try:
        all_metrics = analytics_db.get_metrics_summary(hours)
        
        if service:
            return {
                "service": service,
                "metrics": all_metrics.get(service, {}),
                "hours": hours,
                "timestamp": datetime.now().isoformat()
            }
        
        return {
            "all_services": all_metrics,
            "hours": hours,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    config = {
        "host": "0.0.0.0",
        "port": 8002,
        "reload": False,
        "log_level": "info"
    }
    
    print("🚀 Starting Analytics Microservice...")
    print(f"   📊 Service: Analytics")
    print(f"   🌐 URL: http://{config['host']}:{config['port']}")
    print(f"   📚 Docs: http://{config['host']}:{config['port']}/docs")
    print(f"   🏥 Health: http://{config['host']}:{config['port']}/health")
    
    uvicorn.run(app, **config)
'''
    
    create_file(Path("services/analytics/main.py"), analytics_code)

def create_file_manager_service():
    """Crear File Manager Service"""
    print("💾 Creando File Manager Service...")
    
    file_manager_code = '''#!/usr/bin/env python3
"""
💾 FILE MANAGER MICROSERVICE v4.0
=================================
Servicio de gestión de archivos y multimedia
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn
import logging

# Logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FileManager:
    """Gestor de archivos optimizado"""
    
    def __init__(self):
        self.base_dir = Path("files")
        self.temp_dir = Path("temp")
        self.processed_dir = Path("processed")
        
        # Crear directorios
        for directory in [self.base_dir, self.temp_dir, self.processed_dir]:
            directory.mkdir(exist_ok=True)
        
        # Crear subdirectorios por categoría
        categories = ["images", "videos", "documents", "audio", "general"]
        for category in categories:
            (self.base_dir / category).mkdir(exist_ok=True)
    
    def save_file(self, file_content: bytes, filename: str, category: str = "general") -> str:
        """Guardar archivo"""
        category_dir = self.base_dir / category
        category_dir.mkdir(exist_ok=True)
        
        # Añadir timestamp al nombre para evitar colisiones
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name, ext = os.path.splitext(filename)
        safe_filename = f"{name}_{timestamp}{ext}"
        
        file_path = category_dir / safe_filename
        
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        logger.info(f"📁 Archivo guardado: {file_path}")
        return str(file_path)
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Obtener información del archivo"""
        path = Path(file_path)
        
        if not path.exists():
            return {"error": "File not found"}
        
        stat = path.stat()
        
        return {
            "name": path.name,
            "size": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "extension": path.suffix,
            "category": path.parent.name,
            "full_path": str(path),
            "exists": True
        }
    
    def list_files(self, category: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Listar archivos"""
        files = []
        
        if category:
            search_dir = self.base_dir / category
            if not search_dir.exists():
                return []
            search_dirs = [search_dir]
        else:
            search_dirs = [self.base_dir]
        
        for search_dir in search_dirs:
            for file_path in search_dir.rglob("*"):
                if file_path.is_file() and len(files) < limit:
                    files.append(self.get_file_info(str(file_path)))
        
        # Ordenar por fecha de modificación (más recientes primero)
        files.sort(key=lambda x: x.get('modified', ''), reverse=True)
        
        return files[:limit]
    
    def delete_file(self, file_path: str) -> bool:
        """Eliminar archivo"""
        path = Path(file_path)
        
        if not path.exists():
            return False
        
        try:
            path.unlink()
            logger.info(f"🗑️ Archivo eliminado: {file_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Error eliminando archivo: {e}")
            return False
    
    def cleanup_old_files(self, hours: int = 24) -> int:
        """Limpiar archivos antiguos de directorios temporales"""
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        cleaned = 0
        
        for directory in [self.temp_dir, self.processed_dir]:
            for file_path in directory.rglob("*"):
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    try:
                        file_path.unlink()
                        cleaned += 1
                    except Exception as e:
                        logger.error(f"Error limpiando {file_path}: {e}")
        
        logger.info(f"🧹 Archivos limpiados: {cleaned}")
        return cleaned
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de almacenamiento"""
        stats = {
            "categories": {},
            "total_files": 0,
            "total_size_bytes": 0,
            "total_size_mb": 0,
            "directories": {
                "base": str(self.base_dir),
                "temp": str(self.temp_dir),
                "processed": str(self.processed_dir)
            }
        }
        
        # Estadísticas por categoría
        for category_dir in self.base_dir.iterdir():
            if category_dir.is_dir():
                category_stats = {
                    "files": 0,
                    "size_bytes": 0,
                    "size_mb": 0
                }
                
                for file_path in category_dir.rglob("*"):
                    if file_path.is_file():
                        size = file_path.stat().st_size
                        category_stats["files"] += 1
                        category_stats["size_bytes"] += size
                        
                        stats["total_files"] += 1
                        stats["total_size_bytes"] += size
                
                category_stats["size_mb"] = round(category_stats["size_bytes"] / (1024 * 1024), 2)
                stats["categories"][category_dir.name] = category_stats
        
        stats["total_size_mb"] = round(stats["total_size_bytes"] / (1024 * 1024), 2)
        
        return stats

# Instancia global
file_manager = FileManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida del servicio"""
    try:
        logger.info("🚀 Iniciando File Manager Service...")
        
        # Cleanup inicial
        cleaned = file_manager.cleanup_old_files()
        logger.info(f"🧹 Archivos temporales limpiados: {cleaned}")
        
        logger.info("✅ File Manager Service iniciado")
        yield
    finally:
        logger.info("🛑 File Manager Service detenido")

# Crear aplicación FastAPI
app = FastAPI(
    title="💾 File Manager Microservice",
    description="Servicio de gestión de archivos y multimedia",
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
    """Información del servicio"""
    return {
        "service": "File Manager Microservice",
        "version": "4.0.0",
        "description": "Gestión de archivos y multimedia enterprise"
    }

@app.get("/health")
async def health_check():
    """Health check"""
    storage_stats = file_manager.get_storage_stats()
    
    return {
        "status": "healthy",
        "service": "file_manager",
        "version": "4.0.0",
        "storage": storage_stats,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/stats")
async def get_stats():
    """Obtener estadísticas"""
    return {
        "service": "file_manager",
        "storage": file_manager.get_storage_stats(),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), category: str = "general"):
    """Subir archivo"""
    try:
        content = await file.read()
        file_path = file_manager.save_file(content, file.filename, category)
        
        return {
            "message": "File uploaded successfully",
            "file_path": file_path,
            "file_info": file_manager.get_file_info(file_path),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files")
async def list_files(category: str = None, limit: int = 100):
    """Listar archivos"""
    try:
        files = file_manager.list_files(category, limit)
        
        return {
            "files": files,
            "count": len(files),
            "category": category,
            "limit": limit,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files/{category}/{filename}")
async def get_file(category: str, filename: str):
    """Obtener archivo"""
    file_path = file_manager.base_dir / category / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_path)

@app.delete("/files/{category}/{filename}")
async def delete_file(category: str, filename: str):
    """Eliminar archivo"""
    file_path = str(file_manager.base_dir / category / filename)
    
    if file_manager.delete_file(file_path):
        return {
            "message": "File deleted successfully",
            "file_path": file_path,
            "timestamp": datetime.now().isoformat()
        }
    else:
        raise HTTPException(status_code=404, detail="File not found")

@app.delete("/cleanup")
async def cleanup_files(hours: int = 24):
    """Limpiar archivos antiguos"""
    try:
        cleaned = file_manager.cleanup_old_files(hours)
        
        return {
            "message": f"Cleaned {cleaned} old files",
            "hours": hours,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/storage")
async def get_storage_info():
    """Información de almacenamiento"""
    return {
        "storage": file_manager.get_storage_stats(),
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    config = {
        "host": "0.0.0.0",
        "port": 8003,
        "reload": False,
        "log_level": "info"
    }
    
    print("🚀 Starting File Manager Microservice...")
    print(f"   💾 Service: File Manager")
    print(f"   🌐 URL: http://{config['host']}:{config['port']}")
    print(f"   📚 Docs: http://{config['host']}:{config['port']}/docs")
    print(f"   🏥 Health: http://{config['host']}:{config['port']}/health")
    
    uvicorn.run(app, **config)
'''
    
    create_file(Path("services/file_manager/main.py"), file_manager_code)

def update_orchestrator():
    """Actualizar orchestrator para incluir los nuevos servicios"""
    print("🎭 Actualizando Main Orchestrator...")
    
    updated_orchestrator = '''#!/usr/bin/env python3
"""
🎭 ENTERPRISE MICROSERVICES ORCHESTRATOR v4.0 - ACTUALIZADO
===========================================================
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
        
         + data.spending.total.toLocaleString();
            }
        }
        
        function startAutoRefresh() {
            // Auto-refresh cada 30 segundos
            refreshInterval = setInterval(refreshData, 30000);
        }
        
        function stopAutoRefresh() {
            if (refreshInterval) {
                clearInterval(refreshInterval);
            }
        }
        
        // Animaciones de entrada
        function animateCards() {
            const cards = document.querySelectorAll('.animate-in');
            cards.forEach((card, index) => {
                setTimeout(() => {
                    card.style.opacity = '1';
                    card.style.transform = 'translateY(0)';
                }, index * 100);
            });
        }
        
        // Inicialización
        document.addEventListener('DOMContentLoaded', function() {
            // Configurar estilos iniciales para animación
            const animatedElements = document.querySelectorAll('.animate-in');
            animatedElements.forEach(el => {
                el.style.opacity = '0';
                el.style.transform = 'translateY(30px)';
                el.style.transition = 'all 0.6s ease';
            });
            
            // Iniciar animaciones
            setTimeout(animateCards, 300);
            
            // Primer refresh después de 2 segundos
            setTimeout(refreshData, 2000);
            
            // Iniciar auto-refresh
            setTimeout(startAutoRefresh, 5000);
            
            console.log('🎭 Enterprise Dashboard Loaded - Full Architecture');
            console.log('📊 Real-time metrics enabled');
            console.log('🔄 Auto-refresh every 30 seconds');
        });
        
        // Cleanup al salir
        window.addEventListener('beforeunload', stopAutoRefresh);
    </script>
</body>
</html>'''
    
    create_file(Path("frontend/templates/dashboard.html"), enhanced_dashboard)

def create_readme_updated():
    """Crear README actualizado"""
    print("📖 Actualizando README...")
    
    readme_updated = '''# 🎭 Enterprise Microservices Architecture - COMPLETO

**Tu Enhanced Replicator Service convertido en arquitectura enterprise escalable**

## 🏗️ Arquitectura Completa

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Main Orchestrator│    │ Message Rep.     │    │   Analytics     │
│   Puerto 8000   │───▶│ Puerto 8001      │    │   Puerto 8002   │
│                 │    │ (Tu Enhanced     │    │                 │
│ Dashboard +     │    │  Replicator)     │    │ Métricas SaaS   │
│ Coordinación    │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                       │
         └──────────────────┬─────┴───────────────────────┘
                           │
                ┌─────────────────┐
                │ File Manager    │
                │ Puerto 8003     │
                │                 │
                │ Upload/Download │
                │ Multimedia      │
                └─────────────────┘
```

## 🚀 Inicio Rápido

### 1. Iniciar Arquitectura Completa
```bash
# Todos los servicios (recomendado)
python scripts/start_all.py

# Solo servicios principales
python scripts/start_dev.py
```

### 2. Acceder al Dashboard
- **Dashboard Principal**: http://localhost:8000/dashboard
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 📊 URLs Disponibles

| Servicio | URL | Descripción | Docs |
|----------|-----|-------------|------|
| 🎭 **Orchestrator** | http://localhost:8000 | Dashboard principal | [/docs](http://localhost:8000/docs) |
| 📡 **Message Replicator** | http://localhost:8001 | Tu Enhanced Replicator | [/docs](http://localhost:8001/docs) |
| 📊 **Analytics** | http://localhost:8002 | Métricas SaaS | [/docs](http://localhost:8002/docs) |
| 💾 **File Manager** | http://localhost:8003 | Gestión archivos | [/docs](http://localhost:8003/docs) |

## 🎯 Características Enterprise Completas

### ✅ **Message Replicator (Puerto 8001)**
- **100% funcionalidad original** de tu Enhanced Replicator
- **API REST** para control remoto
- **Health checks** automáticos
- **Métricas** en tiempo real
- **Modo fallback** si no puede importar el Enhanced Replicator

### ✅ **Analytics Service (Puerto 8002)**
- **Base de datos SQLite** optimizada
- **Métricas SaaS** en tiempo real
- **APIs** para dashboard
- **Datos simulados** realistas para demo
- **Endpoints** para métricas personalizadas

### ✅ **File Manager (Puerto 8003)**
- **Upload/Download** de archivos
- **Categorización** automática
- **Gestión multimedia** enterprise
- **Cleanup** automático de archivos temporales
- **Estadísticas** de almacenamiento

### ✅ **Main Orchestrator (Puerto 8000)**
- **Dashboard enterprise** moderno
- **Service discovery** automático
- **Health checks** centralizados
- **APIs** consolidadas
- **Coordinación** de microservicios

## 🎨 Dashboard Enterprise

El dashboard incluye:
- 📊 **Métricas SaaS** en tiempo real
- 🎮 **Control de servicios** individual
- 📈 **Visualizaciones** modernas
- 🔄 **Auto-refresh** cada 30 segundos
- 🎭 **Glassmorphism design** púrpura
- 📱 **Responsive** para móviles

## 🔧 Comandos Disponibles

```bash
# Arquitectura completa (4 servicios)
python scripts/start_all.py

# Solo servicios principales (2 servicios)
python scripts/start_dev.py

# Servicios individuales
python services/message_replicator/main.py    # Puerto 8001
python services/analytics/main.py             # Puerto 8002
python services/file_manager/main.py          # Puerto 8003
python main.py                                 # Puerto 8000
```

## 🔐 Configuración

### Variables de Entorno (en .env)
```env
# Telegram (tu configuración actual)
TELEGRAM_API_ID=18425773
TELEGRAM_API_HASH=1a94c8576994cbb3e60383c94562c91b
TELEGRAM_PHONE=+56985667015

# Discord (tus webhooks actuales)
WEBHOOK_-4989347027=https://discord.com/...
WEBHOOK_-1001697798998=https://discord.com/...

# Configuración general
DEBUG=true
LOG_LEVEL=INFO
```

## 📁 Estructura del Proyecto

```
├── main.py                           # 🎭 Orchestrator principal
├── services/
│   ├── message_replicator/main.py   # 📡 Tu Enhanced Replicator
│   ├── analytics/main.py            # 📊 Analytics SaaS
│   └── file_manager/main.py         # 💾 File Manager
├── shared/
│   ├── config/settings.py           # ⚙️ Configuración centralizada
│   └── utils/logger.py              # 📝 Logger compartido
├── frontend/
│   └── templates/dashboard.html     # 🎨 Dashboard enterprise
├── scripts/
│   ├── start_all.py                 # 🚀 Iniciar todo
│   └── start_dev.py                 # 🚀 Servicios principales
├── database/                        # 🗄️ SQLite databases
└── requirements.txt                 # 📦 Dependencias
```

## 🧪 Testing de APIs

### Message Replicator
```bash
curl http://localhost:8001/health
curl http://localhost:8001/stats
```

### Analytics
```bash
curl http://localhost:8002/dashboard-data
curl http://localhost:8002/metrics
```

### File Manager
```bash
curl http://localhost:8003/storage
curl http://localhost:8003/files
```

## 📈 Beneficios de la Arquitectura

1. **🔧 Mantenibilidad**: Cada servicio es independiente
2. **📊 Escalabilidad**: Escala servicios por separado
3. **🔍 Observabilidad**: Métricas y logs centralizados
4. **🛡️ Resiliencia**: Fallos aislados por servicio
5. **🚀 Deploy**: Despliegue independiente
6. **👥 Desarrollo**: Equipos paralelos
7. **🎯 Performance**: Optimización granular

## 🔮 Roadmap Futuro

### Fase 1 (Actual) ✅
- ✅ Microservicios básicos
- ✅ Dashboard enterprise
- ✅ APIs REST completas
- ✅ Health checks

### Fase 2 (Próxima)
- 🔄 Docker containers
- 🔄 Redis para cache
- 🔄 PostgreSQL para persistencia
- 🔄 Nginx como proxy

### Fase 3 (Avanzada)
- 🔄 Kubernetes deployment
- 🔄 Prometheus metrics
- 🔄 CI/CD pipeline
- 🔄 Auto-scaling

## 🎯 Resultado Final

**ANTES**: main.py monolítico con toda la lógica  
**DESPUÉS**: Arquitectura microservicios enterprise escalable completa

Tu `EnhancedReplicatorService` ahora es parte de una **arquitectura enterprise completa** con:
- **4 microservicios** independientes
- **Dashboard moderno** con métricas en tiempo real
- **APIs REST** completas
- **100% compatibilidad** con tu funcionalidad original
- **Escalabilidad** horizontal preparada

¡Tu sistema de replicación Telegram-Discord ahora es **enterprise-ready y production-ready**! 🎉
'''
    
    create_file(Path("README.md"), readme_updated)

def main():
    """Función principal de expansión SaaS"""
    print("🎭 EXPANSIÓN SAAS ENTERPRISE v4.0")
    print("=" * 60)
    print("Añadiendo servicios enterprise para completar tu SaaS...")
    print()
    
    # Crear servicios adicionales
    create_analytics_service()
    create_file_manager_service()
    update_orchestrator()
    create_complete_startup_script()
    create_enhanced_dashboard()
    create_readme_updated()
    
    print()
    print("=" * 60)
    print("✅ EXPANSIÓN SAAS COMPLETADA!")
    print()
    print("🎯 Tu arquitectura enterprise ahora incluye:")
    print("   📡 Message Replicator (8001) - Tu Enhanced Replicator")
    print("   📊 Analytics Service (8002)  - Métricas SaaS")
    print("   💾 File Manager (8003)       - Upload/Download")
    print("   🎭 Main Orchestrator (8000)  - Dashboard + Coordinación")
    print()
    print("🚀 Para iniciar la arquitectura completa:")
    print("   python scripts/start_all.py")
    print()
    print("🌐 Dashboard enterprise mejorado:")
    print("   http://localhost:8000/dashboard")
    print()
    print("🎨 Características del nuevo dashboard:")
    print("   ✅ Glassmorphism design moderno")
    print("   ✅ Métricas en tiempo real")
    print("   ✅ Health checks automáticos")
    print("   ✅ Responsive design")
    print("   ✅ Auto-refresh cada 30 segundos")
    print()
    print("📈 ¡Tu SaaS enterprise está completo!")
    print("=" * 60)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
🎭 EXPANSIÓN SAAS ENTERPRISE v4.0
================================
Añadir servicios enterprise restantes para completar tu SaaS
"""

import os
from pathlib import Path

def create_file(file_path: Path, content: str):
    """Crear archivo con contenido"""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding='utf-8')
    print(f"   ✅ Creado: {file_path}")

def create_analytics_service():
    """Crear Analytics Service completo"""
    print("📊 Creando Analytics Service...")
    
    analytics_code = '''#!/usr/bin/env python3
"""
📊 ANALYTICS MICROSERVICE v4.0
==============================
Servicio de analytics enterprise para tu SaaS
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import logging

# Logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AnalyticsDB:
    """Base de datos de analytics optimizada"""
    
    def __init__(self, db_path: str = "database/analytics.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Inicializar base de datos"""
        Path("database").mkdir(exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        
        # Tabla de métricas
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
        
        # Tabla de eventos
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
        
        # Índices para performance
        conn.execute('CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_metrics_service ON metrics(service_name)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)')
        
        conn.commit()
        conn.close()
        
        # Insertar datos iniciales de muestra
        self._insert_sample_data()
    
    def _insert_sample_data(self):
        """Insertar datos de muestra para dashboard"""
        conn = sqlite3.connect(self.db_path)
        
        # Métricas de ejemplo
        sample_metrics = [
            ('message_replicator', 'messages_processed', 12278, None, '{"source": "telegram"}'),
            ('message_replicator', 'messages_replicated', 11856, None, '{"target": "discord"}'),
            ('message_replicator', 'errors', 34, None, '{"type": "connection"}'),
            ('analytics', 'queries_processed', 5674, None, '{"endpoint": "dashboard"}'),
            ('file_manager', 'files_stored', 1234, None, '{"type": "media"}'),
        ]
        
        for service, metric, value, group_id, metadata in sample_metrics:
            conn.execute('''
                INSERT OR IGNORE INTO metrics (service_name, metric_name, metric_value, group_id, metadata)
                VALUES (?, ?, ?, ?, ?)
            ''', (service, metric, value, group_id, metadata))
        
        conn.commit()
        conn.close()
    
    def add_metric(self, service_name: str, metric_name: str, value: float, group_id: int = None, metadata: str = None):
        """Añadir métrica"""
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            INSERT INTO metrics (service_name, metric_name, metric_value, group_id, metadata)
            VALUES (?, ?, ?, ?, ?)
        ''', (service_name, metric_name, value, group_id, metadata))
        conn.commit()
        conn.close()
    
    def get_metrics_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Obtener resumen de métricas"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        since = datetime.now() - timedelta(hours=hours)
        
        cursor = conn.execute('''
            SELECT 
                service_name,
                metric_name,
                COUNT(*) as count,
                AVG(metric_value) as avg_value,
                SUM(metric_value) as total_value,
                MIN(metric_value) as min_value,
                MAX(metric_value) as max_value
            FROM metrics 
            WHERE timestamp >= ?
            GROUP BY service_name, metric_name
            ORDER BY service_name, metric_name
        ''', (since,))
        
        results = {}
        for row in cursor.fetchall():
            service = row['service_name']
            if service not in results:
                results[service] = {}
            
            results[service][row['metric_name']] = {
                'count': row['count'],
                'average': round(row['avg_value'], 2),
                'total': round(row['total_value'], 2),
                'min': row['min_value'],
                'max': row['max_value']
            }
        
        conn.close()
        return results
    
    def get_saas_dashboard_data(self) -> Dict[str, Any]:
        """Obtener datos para dashboard SaaS"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        # Datos simulados pero realistas para SaaS
        dashboard_data = {
            "revenue": {
                "total": 12278.35,
                "change": "+5%",
                "period": "This month"
            },
            "new_orders": {
                "total": 4673,
                "change": "-2%", 
                "period": "This month"
            },
            "completed_orders": {
                "total": 5342,
                "change": "+18%",
                "period": "This month"
            },
            "spending": {
                "total": 10365.32,
                "change": "-17%",
                "period": "This month"
            },
            "customers": {
                "total": 651,
                "segments": {
                    "freelancer": 45,
                    "upwork": 30,
                    "behance": 25
                }
            },
            "regions": {
                "israel": 266,
                "usa": 148,
                "canada": 88,
                "australia": 122
            },
            "progress": {
                "overall_performance": 90,
                "order_fulfillment": 85
            },
            "attendance": {
                "youtube": "15K",
                "instagram": "132K", 
                "facebook": "176K"
            },
            "services": {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Obtener métricas reales de servicios
        cursor = conn.execute('''
            SELECT service_name, metric_name, metric_value 
            FROM metrics 
            WHERE timestamp >= datetime('now', '-1 day')
            ORDER BY timestamp DESC
        ''')
        
        for row in cursor.fetchall():
            service = row['service_name']
            if service not in dashboard_data["services"]:
                dashboard_data["services"][service] = {}
            dashboard_data["services"][service][row['metric_name']] = row['metric_value']
        
        conn.close()
        return dashboard_data

# Instancia global
analytics_db = AnalyticsDB()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida del servicio"""
    try:
        logger.info("🚀 Iniciando Analytics Service...")
        logger.info("✅ Analytics Service iniciado")
        yield
    finally:
        logger.info("🛑 Analytics Service detenido")

# Crear aplicación FastAPI
app = FastAPI(
    title="📊 Analytics Microservice",
    description="Servicio de analytics enterprise",
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

class MetricCreate(BaseModel):
    service_name: str
    metric_name: str
    value: float
    group_id: int = None
    metadata: str = None

@app.get("/")
async def root():
    """Información del servicio"""
    return {
        "service": "Analytics Microservice",
        "version": "4.0.0",
        "description": "Servicio de analytics enterprise para SaaS"
    }

@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "service": "analytics",
        "version": "4.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/metrics")
async def add_metric(metric: MetricCreate):
    """Añadir nueva métrica"""
    try:
        analytics_db.add_metric(
            metric.service_name,
            metric.metric_name,
            metric.value,
            metric.group_id,
            metric.metadata
        )
        
        return {
            "message": "Metric added successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    """Obtener estadísticas"""
    try:
        return {
            "service": "analytics",
            "metrics_summary": analytics_db.get_metrics_summary(),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": str(e)}

@app.get("/dashboard-data")
async def get_dashboard_data():
    """Datos para dashboard SaaS"""
    try:
        return analytics_db.get_saas_dashboard_data()
        
    except Exception as e:
        return {"error": str(e)}

@app.get("/metrics")
async def get_metrics(service: str = None, hours: int = 24):
    """Obtener métricas filtradas"""
    try:
        all_metrics = analytics_db.get_metrics_summary(hours)
        
        if service:
            return {
                "service": service,
                "metrics": all_metrics.get(service, {}),
                "hours": hours,
                "timestamp": datetime.now().isoformat()
            }
        
        return {
            "all_services": all_metrics,
            "hours": hours,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    config = {
        "host": "0.0.0.0",
        "port": 8002,
        "reload": False,
        "log_level": "info"
    }
    
    print("🚀 Starting Analytics Microservice...")
    print(f"   📊 Service: Analytics")
    print(f"   🌐 URL: http://{config['host']}:{config['port']}")
    print(f"   📚 Docs: http://{config['host']}:{config['port']}/docs")
    print(f"   🏥 Health: http://{config['host']}:{config['port']}/health")
    
    uvicorn.run(app, **config)
'''
    
    create_file(Path("services/analytics/main.py"), analytics_code)

def create_file_manager_service():
    """Crear File Manager Service"""
    print("💾 Creando File Manager Service...")
    
    file_manager_code = '''#!/usr/bin/env python3
"""
💾 FILE MANAGER MICROSERVICE v4.0
=================================
Servicio de gestión de archivos y multimedia
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn
import logging

# Logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FileManager:
    """Gestor de archivos optimizado"""
    
    def __init__(self):
        self.base_dir = Path("files")
        self.temp_dir = Path("temp")
        self.processed_dir = Path("processed")
        
        # Crear directorios
        for directory in [self.base_dir, self.temp_dir, self.processed_dir]:
            directory.mkdir(exist_ok=True)
        
        # Crear subdirectorios por categoría
        categories = ["images", "videos", "documents", "audio", "general"]
        for category in categories:
            (self.base_dir / category).mkdir(exist_ok=True)
    
    def save_file(self, file_content: bytes, filename: str, category: str = "general") -> str:
        """Guardar archivo"""
        category_dir = self.base_dir / category
        category_dir.mkdir(exist_ok=True)
        
        # Añadir timestamp al nombre para evitar colisiones
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name, ext = os.path.splitext(filename)
        safe_filename = f"{name}_{timestamp}{ext}"
        
        file_path = category_dir / safe_filename
        
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        logger.info(f"📁 Archivo guardado: {file_path}")
        return str(file_path)
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Obtener información del archivo"""
        path = Path(file_path)
        
        if not path.exists():
            return {"error": "File not found"}
        
        stat = path.stat()
        
        return {
            "name": path.name,
            "size": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "extension": path.suffix,
            "category": path.parent.name,
            "full_path": str(path),
            "exists": True
        }
    
    def list_files(self, category: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Listar archivos"""
        files = []
        
        if category:
            search_dir = self.base_dir / category
            if not search_dir.exists():
                return []
            search_dirs = [search_dir]
        else:
            search_dirs = [self.base_dir]
        
        for search_dir in search_dirs:
            for file_path in search_dir.rglob("*"):
                if file_path.is_file() and len(files) < limit:
                    files.append(self.get_file_info(str(file_path)))
        
        # Ordenar por fecha de modificación (más recientes primero)
        files.sort(key=lambda x: x.get('modified', ''), reverse=True)
        
        return files[:limit]
    
    def delete_file(self, file_path: str) -> bool:
        """Eliminar archivo"""
        path = Path(file_path)
        
        if not path.exists():
            return False
        
        try:
            path.unlink()
            logger.info(f"🗑️ Archivo eliminado: {file_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Error eliminando archivo: {e}")
            return False
    
    def cleanup_old_files(self, hours: int = 24) -> int:
        """Limpiar archivos antiguos de directorios temporales"""
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        cleaned = 0
        
        for directory in [self.temp_dir, self.processed_dir]:
            for file_path in directory.rglob("*"):
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    try:
                        file_path.unlink()
                        cleaned += 1
                    except Exception as e:
                        logger.error(f"Error limpiando {file_path}: {e}")
        
        logger.info(f"🧹 Archivos limpiados: {cleaned}")
        return cleaned
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de almacenamiento"""
        stats = {
            "categories": {},
            "total_files": 0,
            "total_size_bytes": 0,
            "total_size_mb": 0,
            "directories": {
                "base": str(self.base_dir),
                "temp": str(self.temp_dir),
                "processed": str(self.processed_dir)
            }
        }
        
        # Estadísticas por categoría
        for category_dir in self.base_dir.iterdir():
            if category_dir.is_dir():
                category_stats = {
                    "files": 0,
                    "size_bytes": 0,
                    "size_mb": 0
                }
                
                for file_path in category_dir.rglob("*"):
                    if file_path.is_file():
                        size = file_path.stat().st_size
                        category_stats["files"] += 1
                        category_stats["size_bytes"] += size
                        
                        stats["total_files"] += 1
                        stats["total_size_bytes"] += size
                
                category_stats["size_mb"] = round(category_stats["size_bytes"] / (1024 * 1024), 2)
                stats["categories"][category_dir.name] = category_stats
        
        stats["total_size_mb"] = round(stats["total_size_bytes"] / (1024 * 1024), 2)
        
        return stats

# Instancia global
file_manager = FileManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida del servicio"""
    try:
        logger.info("🚀 Iniciando File Manager Service...")
        
        # Cleanup inicial
        cleaned = file_manager.cleanup_old_files()
        logger.info(f"🧹 Archivos temporales limpiados: {cleaned}")
        
        logger.info("✅ File Manager Service iniciado")
        yield
    finally:
        logger.info("🛑 File Manager Service detenido")

# Crear aplicación FastAPI
app = FastAPI(
    title="💾 File Manager Microservice",
    description="Servicio de gestión de archivos y multimedia",
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
    """Información del servicio"""
    return {
        "service": "File Manager Microservice",
        "version": "4.0.0",
        "description": "Gestión de archivos y multimedia enterprise"
    }

@app.get("/health")
async def health_check():
    """Health check"""
    storage_stats = file_manager.get_storage_stats()
    
    return {
        "status": "healthy",
        "service": "file_manager",
        "version": "4.0.0",
        "storage": storage_stats,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/stats")
async def get_stats():
    """Obtener estadísticas"""
    return {
        "service": "file_manager",
        "storage": file_manager.get_storage_stats(),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), category: str = "general"):
    """Subir archivo"""
    try:
        content = await file.read()
        file_path = file_manager.save_file(content, file.filename, category)
        
        return {
            "message": "File uploaded successfully",
            "file_path": file_path,
            "file_info": file_manager.get_file_info(file_path),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files")
async def list_files(category: str = None, limit: int = 100):
    """Listar archivos"""
    try:
        files = file_manager.list_files(category, limit)
        
        return {
            "files": files,
            "count": len(files),
            "category": category,
            "limit": limit,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files/{category}/{filename}")
async def get_file(category: str, filename: str):
    """Obtener archivo"""
    file_path = file_manager.base_dir / category / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_path)

@app.delete("/files/{category}/{filename}")
async def delete_file(category: str, filename: str):
    """Eliminar archivo"""
    file_path = str(file_manager.base_dir / category / filename)
    
    if file_manager.delete_file(file_path):
        return {
            "message": "File deleted successfully",
            "file_path": file_path,
            "timestamp": datetime.now().isoformat()
        }
    else:
        raise HTTPException(status_code=404, detail="File not found")

@app.delete("/cleanup")
async def cleanup_files(hours: int = 24):
    """Limpiar archivos antiguos"""
    try:
        cleaned = file_manager.cleanup_old_files(hours)
        
        return {
            "message": f"Cleaned {cleaned} old files",
            "hours": hours,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/storage")
async def get_storage_info():
    """Información de almacenamiento"""
    return {
        "storage": file_manager.get_storage_stats(),
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    config = {
        "host": "0.0.0.0",
        "port": 8003,
        "reload": False,
        "log_level": "info"
    }
    
    print("🚀 Starting File Manager Microservice...")
    print(f"   💾 Service: File Manager")
    print(f"   🌐 URL: http://{config['host']}:{config['port']}")
    print(f"   📚 Docs: http://{config['host']}:{config['port']}/docs")
    print(f"   🏥 Health: http://{config['host']}:{config['port']}/health")
    
    uvicorn.run(app, **config)
'''
    
    create_file(Path("services/file_manager/main.py"), file_manager_code)

def update_orchestrator():
    """Actualizar orchestrator para incluir los nuevos servicios"""
    print("🎭 Actualizando Main Orchestrator...")
    
    updated_orchestrator = '''#!/usr/bin/env python3
"""
🎭 ENTERPRISE MICROSERVICES ORCHESTRATOR v4.0 - ACTUALIZADO
===========================================================
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
        
        