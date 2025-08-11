#!/usr/bin/env python3
"""
🚀 MAIN.PY ENTERPRISE v4.0 - ARQUITECTURA OPTIMIZADA
====================================================

✅ SOLUCIÓN COMPLETA para envío directo de multimedia
✅ Integración perfecta con microservicios enterprise
✅ Discord Sender corregido (sin error 50109)
✅ Enhanced Replicator optimizado
✅ Dashboard moderno con métricas en tiempo real
✅ Arquitectura escalable y modular

PROBLEMA RESUELTO:
- Error 50109 "Invalid JSON" en Discord API
- Envío directo sin localhost/enlaces
- Replicación real de multimedia (videos, PDFs, audio, imágenes)

CARACTERÍSTICAS ENTERPRISE:
- Microservicios desacoplados
- Circuit breakers y retry logic
- Métricas en tiempo real
- Health checks automáticos
- Configuración dinámica
- Escalabilidad horizontal
"""

import asyncio
import logging
import os
import sys
import signal
from datetime import datetime
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional

# Añadir directorio actual al path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
    from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.templating import Jinja2Templates
    from fastapi import Request
    import uvicorn
    from pydantic import BaseModel
except ImportError as e:
    print(f"❌ Error importing FastAPI dependencies: {e}")
    print("💡 Install: pip install fastapi uvicorn jinja2")
    sys.exit(1)

# Importar configuración y servicios
try:
    from app.config.settings import get_settings
    from app.utils.logger import setup_logger
    from app.services.enhanced_replicator_service import EnhancedReplicatorServiceEnterprise
    from app.services.discord_sender import DiscordSenderEnterprise
except ImportError as e:
    print(f"❌ Error importing app modules: {e}")
    print("💡 Make sure the app structure is created correctly")
    sys.exit(1)

# Configuración
settings = get_settings()
logger = setup_logger(__name__)

# Instancia global del replicador
replicator_service: Optional[EnhancedReplicatorServiceEnterprise] = None


# ================ MODELOS PYDANTIC ================

class ConfigUpdateRequest(BaseModel):
    """Modelo para actualización de configuración"""
    max_concurrent_processing: Optional[int] = None
    processing_timeout: Optional[int] = None
    max_file_size_mb: Optional[int] = None
    enable_watermarks: Optional[bool] = None
    enable_compression: Optional[bool] = None
    enable_preview_generation: Optional[bool] = None

class FilterUpdateRequest(BaseModel):
    """Modelo para actualización de filtros"""
    enabled: Optional[bool] = None
    min_length: Optional[int] = None
    skip_words: Optional[list] = None
    only_words: Optional[list] = None
    skip_users: Optional[list] = None


# ================ LIFECYCLE MANAGEMENT ================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    🔄 GESTIÓN DEL CICLO DE VIDA ENTERPRISE
    ======================================
    """
    global replicator_service
    
    # ============ STARTUP ============
    logger.info("🚀 Iniciando Telegram-Discord Replicator Enterprise...")
    
    try:
        # Inicializar servicio de replicación
        logger.info("🔧 Inicializando Enhanced Replicator Service...")
        replicator_service = EnhancedReplicatorServiceEnterprise()
        
        # Inicializar el servicio
        initialization_success = await replicator_service.initialize()
        
        if initialization_success:
            logger.info("✅ Sistema iniciado correctamente")
            
            # Iniciar escucha en background
            asyncio.create_task(replicator_service.start_listening())
        else:
            logger.error("❌ Falló inicialización del replicador")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Error durante inicio: {e}")
        yield
    
    # ============ SHUTDOWN ============
    logger.info("🛑 Deteniendo servicios...")
    
    try:
        if replicator_service:
            await replicator_service.stop()
    except Exception as e:
        logger.error(f"❌ Error durante shutdown: {e}")
    
    logger.info("👋 Sistema detenido")


# ================ FASTAPI APP ================

app = FastAPI(
    title="🎭 Telegram-Discord Replicator Enterprise",
    description="Sistema enterprise de replicación de mensajes multimedia sin enlaces/localhost",
    version="4.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar templates
templates = Jinja2Templates(directory="templates")

# Configurar archivos estáticos
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except RuntimeError:
    # Crear directorio static si no existe
    Path("static").mkdir(exist_ok=True)
    Path("static/css").mkdir(exist_ok=True)
    Path("static/js").mkdir(exist_ok=True)


# ================ WEBSOCKET MANAGER ================

class WebSocketManager:
    """Gestor de WebSockets para métricas en tiempo real"""
    
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"📡 WebSocket connected: {len(self.active_connections)} total")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"📡 WebSocket disconnected: {len(self.active_connections)} total")
    
    async def broadcast_stats(self, data: dict):
        """Broadcast estadísticas a todos los clientes conectados"""
        if not self.active_connections:
            return
            
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception:
                disconnected.append(connection)
        
        # Limpiar conexiones muertas
        for conn in disconnected:
            self.disconnect(conn)

websocket_manager = WebSocketManager()


# ================ RUTAS API ENTERPRISE ================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Redireccionar al dashboard"""
    return """
    <html>
        <head><title>Telegram-Discord Replicator Enterprise</title></head>
        <body style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; text-align: center; padding: 50px;">
            <h1>🎭 Telegram-Discord Replicator Enterprise v4.0</h1>
            <p>Sistema enterprise de replicación de mensajes multimedia</p>
            <div style="margin: 30px 0;">
                <a href="/dashboard" style="background: rgba(255,255,255,0.2); color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; margin: 10px; display: inline-block; backdrop-filter: blur(10px);">📊 Dashboard</a>
                <a href="/docs" style="background: rgba(255,255,255,0.2); color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; margin: 10px; display: inline-block; backdrop-filter: blur(10px);">📚 API Docs</a>
                <a href="/health" style="background: rgba(255,255,255,0.2); color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; margin: 10px; display: inline-block; backdrop-filter: blur(10px);">🏥 Health</a>
            </div>
            <p style="margin-top: 50px; opacity: 0.8;">✅ Envío directo de multimedia sin localhost/enlaces<br>✅ Discord API corregido (sin error 50109)<br>✅ Arquitectura microservicios enterprise</p>
        </body>
    </html>
    """

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Dashboard enterprise con glassmorphism"""
    return HTMLResponse(content="""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎭 Enterprise Dashboard - Telegram-Discord Replicator</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            min-height: 100vh;
            color: white;
            overflow-x: hidden;
        }
        
        .dashboard-container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            min-height: 100vh;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 30px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            text-shadow: 0 4px 8px rgba(0,0,0,0.3);
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
            animation: pulse 2s infinite;
        }
        
        .status-healthy { background: #4ade80; }
        .status-unhealthy { background: #ef4444; }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .metric-card {
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 25px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .metric-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.2);
        }
        
        .metric-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, #ff6b6b, #4ecdc4, #45b7d1, #f9ca24);
            border-radius: 20px 20px 0 0;
        }
        
        .metric-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 15px;
        }
        
        .metric-icon {
            font-size: 2rem;
            margin-right: 10px;
        }
        
        .metric-title {
            font-size: 1.1rem;
            font-weight: 600;
            opacity: 0.9;
        }
        
        .metric-value {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 5px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }
        
        .metric-subtitle {
            opacity: 0.7;
            font-size: 0.9rem;
        }
        
        .logs-section {
            background: rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 25px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            margin-top: 20px;
        }
        
        .logs-header {
            display: flex;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .logs-content {
            background: rgba(0, 0, 0, 0.5);
            border-radius: 10px;
            padding: 20px;
            font-family: 'Courier New', monospace;
            font-size: 0.9rem;
            max-height: 400px;
            overflow-y: auto;
            line-height: 1.4;
        }
        
        .log-entry {
            margin-bottom: 8px;
            padding: 5px 10px;
            border-radius: 5px;
            transition: background 0.2s ease;
        }
        
        .log-entry:hover {
            background: rgba(255, 255, 255, 0.1);
        }
        
        .log-time {
            color: #64b5f6;
            margin-right: 10px;
        }
        
        .log-level-INFO { color: #4ade80; }
        .log-level-WARNING { color: #fbbf24; }
        .log-level-ERROR { color: #ef4444; }
        
        .controls-section {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        
        .control-panel {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 25px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .control-button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 25px;
            border-radius: 25px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
            margin: 5px;
            min-width: 120px;
        }
        
        .control-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.3);
        }
        
        .control-button.danger {
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
        }
        
        .control-button.success {
            background: linear-gradient(135deg, #4ade80 0%, #22c55e 100%);
        }
        
        .footer {
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            opacity: 0.7;
            font-size: 0.9rem;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .header h1 { font-size: 2rem; }
            .metric-value { font-size: 2rem; }
            .dashboard-container { padding: 10px; }
        }
        
        /* Loading animation */
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top-color: #fff;
            animation: spin 1s ease-in-out infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="dashboard-container">
        <!-- Header -->
        <div class="header">
            <h1>🎭 Enterprise Dashboard</h1>
            <p>Telegram-Discord Replicator v4.0 - Real-time Monitoring</p>
            <p><span id="status-indicator" class="status-indicator status-healthy"></span><span id="status-text">Connecting...</span></p>
        </div>
        
        <!-- Metrics Grid -->
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-header">
                    <div>
                        <span class="metric-icon">📨</span>
                        <span class="metric-title">Messages Processed</span>
                    </div>
                </div>
                <div class="metric-value" id="total-messages">0</div>
                <div class="metric-subtitle">Total messages received</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-header">
                    <div>
                        <span class="metric-icon">✅</span>
                        <span class="metric-title">Successfully Replicated</span>
                    </div>
                </div>
                <div class="metric-value" id="replicated-messages">0</div>
                <div class="metric-subtitle">Messages sent to Discord</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-header">
                    <div>
                        <span class="metric-icon">🖼️</span>
                        <span class="metric-title">Media Processed</span>
                    </div>
                </div>
                <div class="metric-value" id="media-processed">0</div>
                <div class="metric-subtitle">Images, videos, audios, PDFs</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-header">
                    <div>
                        <span class="metric-icon">🎨</span>
                        <span class="metric-title">Watermarks Applied</span>
                    </div>
                </div>
                <div class="metric-value" id="watermarks-applied">0</div>
                <div class="metric-subtitle">Enterprise watermarking</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-header">
                    <div>
                        <span class="metric-icon">⏱️</span>
                        <span class="metric-title">Uptime</span>
                    </div>
                </div>
                <div class="metric-value" id="uptime">0h</div>
                <div class="metric-subtitle">Service running time</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-header">
                    <div>
                        <span class="metric-icon">📊</span>
                        <span class="metric-title">Success Rate</span>
                    </div>
                </div>
                <div class="metric-value" id="success-rate">0%</div>
                <div class="metric-subtitle">Replication efficiency</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-header">
                    <div>
                        <span class="metric-icon">💾</span>
                        <span class="metric-title">Data Processed</span>
                    </div>
                </div>
                <div class="metric-value" id="data-processed">0 MB</div>
                <div class="metric-subtitle">Total bandwidth used</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-header">
                    <div>
                        <span class="metric-icon">🔄</span>
                        <span class="metric-title">Active Tasks</span>
                    </div>
                </div>
                <div class="metric-value" id="active-tasks">0</div>
                <div class="metric-subtitle">Concurrent processing</div>
            </div>
        </div>
        
        <!-- Controls Section -->
        <div class="controls-section">
            <div class="control-panel">
                <h3>🎛️ Service Control</h3>
                <button class="control-button" onclick="refreshStats()">🔄 Refresh</button>
                <button class="control-button success" onclick="restartService()">🚀 Restart</button>
                <button class="control-button danger" onclick="stopService()">🛑 Stop</button>
            </div>
            
            <div class="control-panel">
                <h3>📊 Quick Actions</h3>
                <button class="control-button" onclick="exportStats()">📥 Export Stats</button>
                <button class="control-button" onclick="clearStats()">🗑️ Clear Stats</button>
                <button class="control-button" onclick="viewLogs()">📋 View Logs</button>
            </div>
            
            <div class="control-panel">
                <h3>🔗 Quick Links</h3>
                <button class="control-button" onclick="window.open('/docs', '_blank')">📚 API Docs</button>
                <button class="control-button" onclick="window.open('/health', '_blank')">🏥 Health Check</button>
                <button class="control-button" onclick="window.open('/metrics', '_blank')">📈 Metrics</button>
            </div>
        </div>
        
        <!-- Logs Section -->
        <div class="logs-section">
            <div class="logs-header">
                <h3>📋 Real-time Logs</h3>
                <div class="loading" id="logs-loading" style="display: none;"></div>
            </div>
            <div class="logs-content" id="logs-content">
                <div class="log-entry">
                    <span class="log-time">Connecting to real-time stream...</span>
                </div>
            </div>
        </div>
        
        <!-- Footer -->
        <div class="footer">
            <p>🎭 Telegram-Discord Replicator Enterprise v4.0</p>
            <p>✅ Direct multimedia replication • ✅ Discord API fixed • ✅ Enterprise microservices</p>
        </div>
    </div>
    
    <script>
        let ws = null;
        let reconnectAttempts = 0;
        const maxReconnectAttempts = 5;
        
        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            ws = new WebSocket(wsUrl);
            
            ws.onopen = function() {
                console.log('✅ WebSocket connected');
                reconnectAttempts = 0;
                updateStatusIndicator(true, 'Connected - Real-time updates active');
            };
            
            ws.onmessage = function(event) {
                try {
                    const data = JSON.parse(event.data);
                    updateDashboard(data);
                } catch (e) {
                    console.error('Error parsing WebSocket data:', e);
                }
            };
            
            ws.onclose = function() {
                console.log('❌ WebSocket disconnected');
                updateStatusIndicator(false, 'Disconnected - Attempting to reconnect...');
                
                if (reconnectAttempts < maxReconnectAttempts) {
                    setTimeout(() => {
                        reconnectAttempts++;
                        connectWebSocket();
                    }, 2000 * reconnectAttempts);
                } else {
                    updateStatusIndicator(false, 'Connection failed - Please refresh the page');
                }
            };
            
            ws.onerror = function(error) {
                console.error('WebSocket error:', error);
            };
        }
        
        function updateStatusIndicator(connected, text) {
            const indicator = document.getElementById('status-indicator');
            const statusText = document.getElementById('status-text');
            
            if (connected) {
                indicator.className = 'status-indicator status-healthy';
            } else {
                indicator.className = 'status-indicator status-unhealthy';
            }
            
            statusText.textContent = text;
        }
        
        function updateDashboard(data) {
            if (data.dashboard_stats) {
                const stats = data.dashboard_stats;
                
                // Update metrics
                document.getElementById('total-messages').textContent = stats.total_messages || 0;
                document.getElementById('replicated-messages').textContent = stats.replicated_messages || 0;
                
                const mediaTotal = (stats.images_processed || 0) + (stats.videos_processed || 0) + 
                                 (stats.audios_processed || 0) + (stats.pdfs_processed || 0);
                document.getElementById('media-processed').textContent = mediaTotal;
                
                document.getElementById('watermarks-applied').textContent = stats.watermarks_applied || 0;
                document.getElementById('uptime').textContent = `${stats.uptime_hours || 0}h`;
                document.getElementById('success-rate').textContent = `${Math.round(stats.success_rate || 0)}%`;
                document.getElementById('data-processed').textContent = `${stats.total_mb_processed || 0} MB`;
                document.getElementById('active-tasks').textContent = stats.active_tasks || 0;
                
                // Update status
                updateStatusIndicator(stats.is_running && stats.is_listening, 
                    stats.is_running ? 'Service Running - Real-time monitoring' : 'Service Stopped');
            }
            
            if (data.logs) {
                updateLogs(data.logs);
            }
        }
        
        function updateLogs(logs) {
            const logsContent = document.getElementById('logs-content');
            
            logs.forEach(log => {
                const logEntry = document.createElement('div');
                logEntry.className = 'log-entry';
                
                const time = new Date(log.timestamp).toLocaleTimeString();
                const level = log.level || 'INFO';
                
                logEntry.innerHTML = `
                    <span class="log-time">${time}</span>
                    <span class="log-level-${level}">[${level}]</span>
                    <span>${log.message}</span>
                `;
                
                logsContent.appendChild(logEntry);
            });
            
            // Keep only last 50 entries
            while (logsContent.children.length > 50) {
                logsContent.removeChild(logsContent.firstChild);
            }
            
            // Auto-scroll to bottom
            logsContent.scrollTop = logsContent.scrollHeight;
        }
        
        async function refreshStats() {
            try {
                const response = await fetch('/api/stats');
                const data = await response.json();
                updateDashboard({dashboard_stats: data});
            } catch (error) {
                console.error('Error refreshing stats:', error);
            }
        }
        
        async function restartService() {
            if (confirm('¿Estás seguro de que quieres reiniciar el servicio?')) {
                try {
                    const response = await fetch('/api/restart', {method: 'POST'});
                    const result = await response.json();
                    alert(result.message || 'Service restart initiated');
                } catch (error) {
                    alert('Error restarting service: ' + error.message);
                }
            }
        }
        
        async function stopService() {
            if (confirm('¿Estás seguro de que quieres detener el servicio?')) {
                try {
                    const response = await fetch('/api/stop', {method: 'POST'});
                    const result = await response.json();
                    alert(result.message || 'Service stop initiated');
                } catch (error) {
                    alert('Error stopping service: ' + error.message);
                }
            }
        }
        
        async function exportStats() {
            try {
                const response = await fetch('/api/export-stats');
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `replicator_stats_${new Date().toISOString().split('T')[0]}.json`;
                a.click();
                window.URL.revokeObjectURL(url);
            } catch (error) {
                alert('Error exporting stats: ' + error.message);
            }
        }
        
        async function clearStats() {
            if (confirm('¿Estás seguro de que quieres limpiar las estadísticas?')) {
                try {
                    const response = await fetch('/api/clear-stats', {method: 'POST'});
                    const result = await response.json();
                    alert(result.message || 'Stats cleared');
                    refreshStats();
                } catch (error) {
                    alert('Error clearing stats: ' + error.message);
                }
            }
        }
        
        function viewLogs() {
            window.open('/api/logs', '_blank');
        }
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            connectWebSocket();
            refreshStats();
            
            // Refresh stats every 30 seconds as fallback
            setInterval(refreshStats, 30000);
        });
    </script>
</body>
</html>
    """)

# ================ API ROUTES ================

@app.get("/health")
async def health_check():
    """Health check enterprise completo"""
    if not replicator_service:
        return JSONResponse(
            status_code=503,
            content={
                "status": "service_not_initialized",
                "timestamp": datetime.now().isoformat()
            }
        )
    
    health_data = await replicator_service.get_health()
    status_code = 200 if health_data.get('status') == 'healthy' else 503
    
    return JSONResponse(status_code=status_code, content=health_data)

@app.get("/api/stats")
async def get_stats():
    """Obtener estadísticas enterprise"""
    if not replicator_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return replicator_service.get_dashboard_stats()

@app.get("/api/stats/detailed")
async def get_detailed_stats():
    """Obtener estadísticas detalladas enterprise"""
    if not replicator_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return replicator_service.get_stats()

@app.get("/api/health/detailed")
async def get_detailed_health():
    """Health check detallado enterprise"""
    if not replicator_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return await replicator_service.get_health()

@app.post("/api/restart")
async def restart_service(background_tasks: BackgroundTasks):
    """Reiniciar servicio enterprise"""
    if not replicator_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    async def restart_background():
        try:
            await replicator_service.stop()
            await asyncio.sleep(2)
            await replicator_service.initialize()
            asyncio.create_task(replicator_service.start_listening())
        except Exception as e:
            logger.error(f"❌ Error in restart: {e}")
    
    background_tasks.add_task(restart_background)
    return {"message": "Service restart initiated"}

@app.post("/api/stop")
async def stop_service():
    """Detener servicio enterprise"""
    if not replicator_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        await replicator_service.stop()
        return {"message": "Service stopped successfully"}
    except Exception as e:
        logger.error(f"❌ Error stopping service: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/config")
async def update_config(config: ConfigUpdateRequest):
    """Actualizar configuración enterprise"""
    if not replicator_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    success = replicator_service.update_config(config.dict(exclude_unset=True))
    if success:
        return {"message": "Configuration updated successfully"}
    else:
        raise HTTPException(status_code=400, detail="Failed to update configuration")

@app.put("/api/filters")
async def update_filters(filters: FilterUpdateRequest):
    """Actualizar filtros enterprise"""
    if not replicator_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    success = replicator_service.update_filters(filters.dict(exclude_unset=True))
    if success:
        return {"message": "Filters updated successfully"}
    else:
        raise HTTPException(status_code=400, detail="Failed to update filters")

@app.get("/api/export-stats")
async def export_stats():
    """Exportar estadísticas enterprise"""
    if not replicator_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    stats = replicator_service.get_stats()
    stats['export_timestamp'] = datetime.now().isoformat()
    stats['export_version'] = '4.0'
    
    import json
    from fastapi.responses import Response
    
    content = json.dumps(stats, indent=2, ensure_ascii=False)
    filename = f"replicator_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.post("/api/clear-stats")
async def clear_stats():
    """Limpiar estadísticas enterprise"""
    if not replicator_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    # Reset stats
    replicator_service.stats = replicator_service.stats.__class__()
    return {"message": "Statistics cleared successfully"}

@app.get("/api/logs")
async def get_logs():
    """Obtener logs recientes"""
    try:
        log_file = f"logs/replicator_{datetime.now().strftime('%Y%m%d')}.log"
        if Path(log_file).exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()[-100:]  # Últimas 100 líneas
            
            return {"logs": [line.strip() for line in lines]}
        else:
            return {"logs": ["No log file found for today"]}
    except Exception as e:
        return {"logs": [f"Error reading logs: {str(e)}"]}

# ================ WEBSOCKET ROUTE ================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket para métricas en tiempo real"""
    await websocket_manager.connect(websocket)
    
    try:
        while True:
            # Enviar estadísticas cada 5 segundos
            if replicator_service:
                stats = replicator_service.get_dashboard_stats()
                await websocket.send_json({
                    "dashboard_stats": stats,
                    "timestamp": datetime.now().isoformat()
                })
            
            await asyncio.sleep(5)
            
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
        websocket_manager.disconnect(websocket)

# ================ BACKGROUND TASKS ================

async def broadcast_stats_periodically():
    """Broadcast estadísticas cada 10 segundos"""
    while True:
        try:
            if replicator_service and websocket_manager.active_connections:
                stats = replicator_service.get_dashboard_stats()
                await websocket_manager.broadcast_stats({
                    "dashboard_stats": stats,
                    "timestamp": datetime.now().isoformat()
                })
        except Exception as e:
            logger.error(f"❌ Error broadcasting stats: {e}")
        
        await asyncio.sleep(10)

# ================ SIGNAL HANDLERS ================

def signal_handler(signum, frame):
    """Manejar señales del sistema"""
    logger.info(f"🛑 Received signal {signum}, shutting down gracefully...")
    asyncio.create_task(shutdown_gracefully())

def setup_signal_handlers():
    """Configurar manejadores de señales"""
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

async def shutdown_gracefully():
    """Shutdown graceful del sistema"""
    global replicator_service
    
    if replicator_service:
        await replicator_service.stop()
    
    # Cerrar conexiones WebSocket
    for connection in websocket_manager.active_connections.copy():
        try:
            await connection.close()
        except:
            pass
    
    logger.info("👋 Graceful shutdown completed")

# ================ MAIN EXECUTION ================

if __name__ == "__main__":
    # Configurar manejadores de señales
    setup_signal_handlers()
    
    # Crear directorios necesarios
    Path("logs").mkdir(exist_ok=True)
    Path("temp").mkdir(exist_ok=True)
    Path("templates").mkdir(exist_ok=True)
    
    # Iniciar tarea de background para broadcasting
    asyncio.create_task(broadcast_stats_periodically())
    
    logger.info("🌐 Iniciando servidor web enterprise...")
    
    # Configuración del servidor
    config = {
        "host": settings.host if hasattr(settings, 'host') else "0.0.0.0",
        "port": settings.port if hasattr(settings, 'port') else 8000,
        "log_level": "info",
        "access_log": True,
        "reload": settings.debug if hasattr(settings, 'debug') else False
    }
    
    uvicorn.run(app, **config)
# Background task para broadcasting
async def background_broadcast_task():
    """Background task para enviar estadísticas via WebSocket"""
    while True:
        try:
            if replicator_service and websocket_manager.active_connections:
                stats = replicator_service.get_dashboard_stats()
                await websocket_manager.broadcast_stats({
                    "dashboard_stats": stats,
                    "timestamp": datetime.now().isoformat(),
                    "logs": []  # Placeholder para logs
                })
        except Exception as e:
            logger.error(f"❌ Error in background broadcast: {e}")
        
        await asyncio.sleep(10)  # Broadcast cada 10 segundos

# ================ CREAR DIRECTORIOS NECESARIOS ================

def ensure_directories():
    """Crear directorios necesarios si no existen"""
    directories = [
        "logs",
        "temp", 
        "templates",
        "static",
        "static/css",
        "static/js",
        "app",
        "app/config",
        "app/services",
        "app/utils"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    # Crear archivos __init__.py necesarios
    init_files = [
        "app/__init__.py",
        "app/config/__init__.py", 
        "app/services/__init__.py",
        "app/utils/__init__.py"
    ]
    
    for init_file in init_files:
        init_path = Path(init_file)
        if not init_path.exists():
            init_path.touch()

# ================ MANEJO GRACEFUL DE SHUTDOWN ================

async def graceful_shutdown():
    """Shutdown graceful del sistema completo"""
    global replicator_service
    
    logger.info("🛑 Iniciando shutdown graceful...")
    
    try:
        # Detener replicator service
        if replicator_service:
            await replicator_service.stop()
            logger.info("✅ Replicator service detenido")
        
        # Cerrar conexiones WebSocket
        for connection in websocket_manager.active_connections.copy():
            try:
                await connection.close()
            except Exception:
                pass
        
        logger.info("✅ WebSocket connections cerradas")
        
    except Exception as e:
        logger.error(f"❌ Error durante shutdown: {e}")
    
    logger.info("👋 Shutdown graceful completado")

# ================ SIGNAL HANDLERS ================

def setup_signal_handlers():
    """Configurar manejadores de señales para shutdown graceful"""
    import signal
    
    def signal_handler(signum, frame):
        logger.info(f"🛑 Received signal {signum}")
        asyncio.create_task(graceful_shutdown())
    
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, signal_handler)
    if hasattr(signal, 'SIGINT'):
        signal.signal(signal.SIGINT, signal_handler)

# ================ MAIN EXECUTION ================

if __name__ == "__main__":
    try:
        # Asegurar que existen los directorios
        ensure_directories()
        
        # Configurar signal handlers
        setup_signal_handlers()
        
        logger.info("🌐 Iniciando servidor web enterprise...")
        
        # Configuración del servidor
        server_config = {
            "host": getattr(settings, 'host', '0.0.0.0'),
            "port": getattr(settings, 'port', 8000),
            "log_level": "info",
            "access_log": True,
            "reload": getattr(settings, 'debug', False)
        }
        
        # Iniciar background task
        asyncio.create_task(background_broadcast_task())
        
        # Iniciar servidor
        uvicorn.run(app, **server_config)
        
    except KeyboardInterrupt:
        logger.info("🛑 Interrupted by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)
    finally:
        logger.info("👋 Application terminated")    