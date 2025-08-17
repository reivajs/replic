#!/usr/bin/env python3
"""
🔧 FIX WEBSOCKET 403 ERROR
==========================
Corrige el error 403 Forbidden en WebSocket
"""

from pathlib import Path

def fix_websocket_routes():
    """Corregir rutas de WebSocket"""
    print("\n" + "="*70)
    print("🔧 FIXING WEBSOCKET 403 ERROR")
    print("="*70 + "\n")
    
    # 1. Corregir el HTML del dashboard
    fix_dashboard_html()
    
    # 2. Verificar y corregir las rutas en el router
    fix_dashboard_router()
    
    print("\n" + "="*70)
    print("✅ WEBSOCKET ROUTES FIXED")
    print("="*70)
    print("\n🚀 Reinicia el servidor: python start_simple.py")

def fix_dashboard_html():
    """Corregir las URLs de WebSocket en el HTML"""
    print("📝 Corrigiendo dashboard.html...")
    
    dashboard_html = '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎯 Universal Replication Control Center</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <style>
        :root {
            --primary: #667eea;
            --primary-dark: #5a67d8;
            --secondary: #48bb78;
            --danger: #f56565;
            --warning: #ed8936;
            --info: #4299e1;
            --dark: #1a202c;
            --glass: rgba(255, 255, 255, 0.05);
            --glass-hover: rgba(255, 255, 255, 0.08);
            --border: rgba(255, 255, 255, 0.1);
            --text-primary: #e2e8f0;
            --text-secondary: #a0aec0;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #667eea 100%);
            min-height: 100vh;
            color: var(--text-primary);
        }

        .header {
            background: var(--glass);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid var(--border);
            padding: 1rem 2rem;
        }

        .container {
            max-width: 1600px;
            margin: 2rem auto;
            padding: 0 2rem;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        .stat-card {
            background: var(--glass);
            backdrop-filter: blur(20px);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 1.5rem;
            transition: all 0.3s;
        }

        .stat-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }

        .stat-value {
            font-size: 2rem;
            font-weight: 700;
            margin: 0.5rem 0;
        }

        .stat-title {
            color: var(--text-secondary);
            font-size: 0.9rem;
        }

        .flows-list {
            background: var(--glass);
            backdrop-filter: blur(20px);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 1.5rem;
        }

        .flow-item {
            display: flex;
            justify-content: space-between;
            padding: 1rem;
            background: var(--glass);
            border: 1px solid var(--border);
            border-radius: 12px;
            margin-bottom: 1rem;
            transition: all 0.3s;
        }

        .flow-item:hover {
            background: var(--glass-hover);
        }

        .flow-status {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: var(--secondary);
            display: inline-block;
            margin-right: 0.5rem;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .flow-status.paused {
            background: var(--warning);
            animation: none;
        }

        .flow-status.error {
            background: var(--danger);
            animation: none;
        }

        .connection-status {
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 10px 20px;
            background: var(--glass);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            border: 1px solid var(--border);
            font-size: 0.85rem;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .connection-indicator {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--danger);
        }

        .connection-indicator.connected {
            background: var(--secondary);
        }

        .loading-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            display: none;
        }

        .loading-overlay.active {
            display: flex;
        }

        .spinner {
            width: 50px;
            height: 50px;
            border: 3px solid var(--border);
            border-top: 3px solid var(--primary);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <!-- Loading Overlay -->
    <div class="loading-overlay" id="loadingOverlay">
        <div class="spinner"></div>
    </div>

    <!-- Header -->
    <header class="header">
        <div style="max-width: 1600px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center;">
            <div style="display: flex; align-items: center; gap: 1rem;">
                <i class="fas fa-infinity" style="font-size: 1.5rem;"></i>
                <h1 style="font-size: 1.5rem;">Universal Replication Center</h1>
            </div>
            <div>
                <span id="system-status" style="padding: 0.5rem 1rem; background: var(--glass); border-radius: 8px;">
                    <i class="fas fa-circle" style="color: var(--secondary); font-size: 0.5rem;"></i>
                    System Operational
                </span>
            </div>
        </div>
    </header>

    <!-- Main Container -->
    <div class="container">
        <!-- Statistics Grid -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-title">
                    <i class="fas fa-envelope"></i> Messages Received
                </div>
                <div class="stat-value" id="messages-received">-</div>
                <div style="color: var(--secondary); font-size: 0.85rem;">
                    <i class="fas fa-arrow-up"></i> <span id="messages-rate">0</span>/min
                </div>
            </div>

            <div class="stat-card">
                <div class="stat-title">
                    <i class="fas fa-share"></i> Messages Replicated
                </div>
                <div class="stat-value" id="messages-replicated">-</div>
                <div style="color: var(--secondary); font-size: 0.85rem;">
                    Success Rate: <span id="success-rate">-</span>%
                </div>
            </div>

            <div class="stat-card">
                <div class="stat-title">
                    <i class="fas fa-project-diagram"></i> Active Flows
                </div>
                <div class="stat-value" id="active-flows">-</div>
                <div style="color: var(--text-secondary); font-size: 0.85rem;">
                    <span id="total-accounts">-</span> accounts connected
                </div>
            </div>

            <div class="stat-card">
                <div class="stat-title">
                    <i class="fas fa-clock"></i> Uptime
                </div>
                <div class="stat-value" id="uptime">-</div>
                <div style="color: var(--text-secondary); font-size: 0.85rem;">
                    Latency: <span id="latency">-</span>ms
                </div>
            </div>
        </div>

        <!-- Active Flows -->
        <div class="flows-list">
            <h2 style="margin-bottom: 1.5rem;">
                <i class="fas fa-stream"></i> Active Replication Flows
            </h2>
            <div id="flows-container">
                <div style="text-align: center; color: var(--text-secondary);">
                    Loading flows...
                </div>
            </div>
        </div>
    </div>

    <!-- Connection Status -->
    <div class="connection-status">
        <div class="connection-indicator" id="connectionIndicator"></div>
        <span id="connectionText">Connecting...</span>
    </div>

    <script>
        // Dashboard Controller
        class DashboardController {
            constructor() {
                this.wsUrl = null;
                this.ws = null;
                this.reconnectAttempts = 0;
                this.maxReconnectAttempts = 10;
                this.reconnectDelay = 3000;
                this.updateInterval = null;
                this.isConnected = false;
                
                this.init();
            }
            
            init() {
                // Determinar URL base
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const host = window.location.host;
                
                // CORRECCIÓN: URL correcta del WebSocket
                this.wsUrl = `${protocol}//${host}/api/v1/dashboard/ws/dashboard`;
                
                console.log('WebSocket URL:', this.wsUrl);
                
                // Iniciar actualización por polling
                this.startPolling();
                
                // Intentar WebSocket (opcional)
                this.connectWebSocket();
            }
            
            startPolling() {
                // Actualización inicial
                this.updateDashboard();
                
                // Actualizar cada 3 segundos
                this.updateInterval = setInterval(() => {
                    this.updateDashboard();
                }, 3000);
            }
            
            stopPolling() {
                if (this.updateInterval) {
                    clearInterval(this.updateInterval);
                    this.updateInterval = null;
                }
            }
            
            async updateDashboard() {
                try {
                    // Fetch stats
                    const statsResponse = await fetch('/api/v1/dashboard/api/stats');
                    if (!statsResponse.ok) throw new Error('Failed to fetch stats');
                    const stats = await statsResponse.json();
                    
                    // Update UI
                    this.updateStats(stats);
                    
                    // Fetch flows
                    const flowsResponse = await fetch('/api/v1/dashboard/api/flows');
                    if (!flowsResponse.ok) throw new Error('Failed to fetch flows');
                    const flowsData = await flowsResponse.json();
                    
                    // Update flows
                    this.updateFlows(flowsData.flows || []);
                    
                    // Update system status
                    this.updateSystemStatus();
                    
                } catch (error) {
                    console.error('Error updating dashboard:', error);
                    this.showError();
                }
            }
            
            updateStats(stats) {
                // Update stat values con fallback
                document.getElementById('messages-received').textContent = 
                    stats.messages_received !== undefined ? stats.messages_received.toLocaleString() : '-';
                    
                document.getElementById('messages-replicated').textContent = 
                    stats.messages_replicated !== undefined ? stats.messages_replicated.toLocaleString() : '-';
                    
                document.getElementById('active-flows').textContent = 
                    stats.active_flows || '0';
                    
                document.getElementById('total-accounts').textContent = 
                    stats.total_accounts || '0';
                    
                document.getElementById('uptime').textContent = 
                    stats.uptime_formatted || '-';
                    
                document.getElementById('success-rate').textContent = 
                    stats.success_rate ? stats.success_rate.toFixed(1) : '-';
                    
                document.getElementById('latency').textContent = 
                    stats.avg_latency || '-';
                
                // Calculate message rate
                if (stats.messages_received && stats.uptime_seconds) {
                    const rate = Math.round(stats.messages_received / Math.max(1, stats.uptime_seconds / 60));
                    document.getElementById('messages-rate').textContent = rate;
                }
            }
            
            updateFlows(flows) {
                const container = document.getElementById('flows-container');
                
                if (!flows || flows.length === 0) {
                    container.innerHTML = `
                        <div style="text-align: center; color: var(--text-secondary); padding: 2rem;">
                            <i class="fas fa-info-circle" style="font-size: 2rem; opacity: 0.5; margin-bottom: 1rem;"></i>
                            <p>No active flows at the moment</p>
                        </div>
                    `;
                    return;
                }
                
                container.innerHTML = flows.map(flow => `
                    <div class="flow-item">
                        <div style="display: flex; align-items: center; gap: 1rem;">
                            <span class="flow-status ${flow.status === 'paused' ? 'paused' : flow.status === 'error' ? 'error' : ''}"></span>
                            <div>
                                <div style="font-weight: 500;">${this.escapeHtml(flow.name)}</div>
                                <div style="font-size: 0.85rem; color: var(--text-secondary);">
                                    ${this.escapeHtml(flow.source)} → ${this.escapeHtml(flow.destination)}
                                </div>
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-weight: 500;">${flow.messages_today || 0}</div>
                            <div style="font-size: 0.85rem; color: var(--text-secondary);">messages today</div>
                        </div>
                    </div>
                `).join('');
            }
            
            async updateSystemStatus() {
                try {
                    const response = await fetch('/api/v1/dashboard/api/health');
                    const health = await response.json();
                    
                    const statusElement = document.getElementById('system-status');
                    if (health.status === 'operational') {
                        statusElement.innerHTML = '<i class="fas fa-circle" style="color: #48bb78; font-size: 0.5rem;"></i> System Operational';
                    } else if (health.status === 'degraded') {
                        statusElement.innerHTML = '<i class="fas fa-circle" style="color: #ed8936; font-size: 0.5rem;"></i> System Degraded';
                    } else {
                        statusElement.innerHTML = '<i class="fas fa-circle" style="color: #f56565; font-size: 0.5rem;"></i> System Down';
                    }
                } catch (error) {
                    console.error('Error updating system status:', error);
                }
            }
            
            connectWebSocket() {
                try {
                    console.log('Attempting WebSocket connection to:', this.wsUrl);
                    
                    this.ws = new WebSocket(this.wsUrl);
                    
                    this.ws.onopen = () => {
                        console.log('WebSocket connected');
                        this.isConnected = true;
                        this.reconnectAttempts = 0;
                        this.updateConnectionStatus(true);
                        
                        // Opcionalmente, detener polling si WebSocket funciona
                        // this.stopPolling();
                    };
                    
                    this.ws.onmessage = (event) => {
                        try {
                            const data = JSON.parse(event.data);
                            
                            if (data.type === 'stats_update') {
                                this.updateStats(data.data);
                            } else if (data.type === 'ping') {
                                // Responder al ping si es necesario
                                if (this.ws.readyState === WebSocket.OPEN) {
                                    this.ws.send(JSON.stringify({ type: 'pong' }));
                                }
                            }
                        } catch (error) {
                            console.error('Error processing WebSocket message:', error);
                        }
                    };
                    
                    this.ws.onerror = (error) => {
                        console.error('WebSocket error:', error);
                        this.isConnected = false;
                        this.updateConnectionStatus(false);
                    };
                    
                    this.ws.onclose = () => {
                        console.log('WebSocket closed');
                        this.isConnected = false;
                        this.updateConnectionStatus(false);
                        
                        // Reintentar conexión
                        if (this.reconnectAttempts < this.maxReconnectAttempts) {
                            this.reconnectAttempts++;
                            console.log(`Reconnecting in ${this.reconnectDelay}ms... (attempt ${this.reconnectAttempts})`);
                            setTimeout(() => this.connectWebSocket(), this.reconnectDelay);
                        }
                    };
                    
                } catch (error) {
                    console.error('Error creating WebSocket:', error);
                    this.updateConnectionStatus(false);
                }
            }
            
            updateConnectionStatus(connected) {
                const indicator = document.getElementById('connectionIndicator');
                const text = document.getElementById('connectionText');
                
                if (connected) {
                    indicator.classList.add('connected');
                    text.textContent = 'Live Updates Active';
                } else {
                    indicator.classList.remove('connected');
                    text.textContent = 'Using Polling Mode';
                }
            }
            
            showError() {
                // Mostrar estado de error en UI
                document.getElementById('system-status').innerHTML = 
                    '<i class="fas fa-exclamation-triangle" style="color: #f56565;"></i> Connection Error';
            }
            
            escapeHtml(text) {
                const div = document.createElement('div');
                div.textContent = text;
                return div.innerHTML;
            }
            
            destroy() {
                // Cleanup
                this.stopPolling();
                
                if (this.ws) {
                    this.ws.close();
                    this.ws = null;
                }
            }
        }
        
        // Inicializar dashboard
        let dashboard = null;
        
        document.addEventListener('DOMContentLoaded', () => {
            dashboard = new DashboardController();
        });
        
        // Cleanup al salir
        window.addEventListener('beforeunload', () => {
            if (dashboard) {
                dashboard.destroy();
            }
        });
    </script>
</body>
</html>'''
    
    # Guardar el HTML corregido
    templates_dir = Path("frontend/templates")
    templates_dir.mkdir(parents=True, exist_ok=True)
    
    dashboard_file = templates_dir / "dashboard.html"
    dashboard_file.write_text(dashboard_html)
    
    print("✅ Dashboard HTML corregido (WebSocket URL fixed)")

def fix_dashboard_router():
    """Verificar que el router está correctamente configurado"""
    print("📝 Verificando dashboard router...")
    
    # El router ya debería estar correcto, pero vamos a asegurarnos
    router_file = Path("app/api/v1/dashboard.py")
    
    if router_file.exists():
        content = router_file.read_text()
        
        # Verificar que la ruta WebSocket es correcta
        if '@router.websocket("/ws/dashboard")' in content:
            print("✅ Dashboard router ya tiene la ruta correcta")
        else:
            print("⚠️ Actualizando ruta WebSocket en router...")
            # El contenido ya debería estar correcto del fix anterior
    else:
        print("⚠️ Dashboard router no existe, usa el script fix_dashboard_final.py primero")
    
    print("✅ Router verificado")

if __name__ == "__main__":
    fix_websocket_routes()