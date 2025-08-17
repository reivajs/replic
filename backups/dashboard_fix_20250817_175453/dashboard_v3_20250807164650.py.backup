"""
API - Dashboard v3.0 (Simplified)
================================ 
Dashboard simplificado para quick setup
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from typing import Any

class EnhancedDashboardV3:
    def __init__(self, watermark_manager, **kwargs):
        self.watermark_manager = watermark_manager
    
    def setup_routes(self, app: FastAPI):
        @app.get("/", response_class=HTMLResponse)
        async def dashboard():
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>🎨 Watermark Manager</title>
                <style>
                    body { 
                        font-family: -apple-system, BlinkMacSystemFont, sans-serif; 
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white; 
                        text-align: center; 
                        padding: 50px;
                        min-height: 100vh;
                        margin: 0;
                    }
                    .container { max-width: 800px; margin: 0 auto; }
                    h1 { font-size: 3rem; margin-bottom: 20px; }
                    .status { 
                        background: rgba(255,255,255,0.1); 
                        padding: 20px; 
                        border-radius: 12px; 
                        margin: 20px 0; 
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🎨 Watermark Manager v3.0</h1>
                    <div class="status">
                        <h2>✅ Sistema Funcionando</h2>
                        <p>Dashboard simplificado activo</p>
                        <p>Watermark Manager integrado con tu main.py</p>
                    </div>
                    <div class="status">
                        <h3>📋 Próximos pasos:</h3>
                        <p>1. Verificar que el sistema funciona correctamente</p>
                        <p>2. Implementar dashboard completo si necesitas más funciones</p>
                        <p>3. Configurar watermarks por grupo</p>
                    </div>
                </div>
            </body>
            </html>
            """
        
        @app.get("/api/health")
        async def health():
            return self.watermark_manager.health_check()

def create_enhanced_dashboard(watermark_manager, **kwargs) -> EnhancedDashboardV3:
    return EnhancedDashboardV3(watermark_manager, **kwargs)
