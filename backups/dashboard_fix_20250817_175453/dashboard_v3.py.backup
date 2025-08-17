"""
API - Enhanced Dashboard v3.0 SaaS-Ready
=======================================
Dashboard completo con soporte PNG + Texto + Video watermarks
Diseño Apple minimalista + UX intuitivo + Performance optimizada
"""

import asyncio
import json
import base64
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import logging

from services.watermark.manager import WatermarkManager, WatermarkConfig, WatermarkType, Position

logger = logging.getLogger(__name__)

# ============ PYDANTIC MODELS ============

class GroupConfigRequest(BaseModel):
    """Request para configuración de grupo"""
    group_id: int
    watermark_type: str = "none"
    
    # PNG Settings
    png_enabled: bool = False
    png_position: str = "bottom_right"
    png_opacity: float = 0.7
    png_scale: float = 0.15
    png_custom_x: int = 20
    png_custom_y: int = 20
    
    # Text Settings
    text_enabled: bool = False
    text_content: str = ""
    text_position: str = "bottom_right"
    text_font_size: int = 32
    text_color: str = "#FFFFFF"
    text_stroke_color: str = "#000000"
    text_stroke_width: int = 2
    text_custom_x: int = 20
    text_custom_y: int = 60
    
    # Video Settings
    video_enabled: bool = False
    video_max_size_mb: int = 1024
    video_timeout_sec: int = 60
    video_compress: bool = True
    video_quality_crf: int = 23

class StatsResponse(BaseModel):
    """Response de estadísticas"""
    total_groups: int
    active_configs: int
    total_processed: int
    images_processed: int
    videos_processed: int
    text_applied: int
    png_applied: int
    errors: int
    uptime_hours: float

# ============ ENHANCED DASHBOARD CLASS ============

class EnhancedDashboardV3:
    """
    🍎 Dashboard SaaS-Ready v3.0
    
    Características:
    - UI Apple minimalista
    - Soporte completo PNG + Texto + Video
    - Preview en tiempo real
    - Upload de archivos optimizado
    - WebSocket para updates en vivo
    - Mobile-responsive
    """
    
    def __init__(self, watermark_manager: WatermarkManager, stats_service=None):
        self.watermark_manager = watermark_manager
        self.stats_service = stats_service
        self.connected_clients: set = set()
        self.start_time = datetime.now()
        
        # Directorio para static files
        self.static_dir = Path("static")
        self.static_dir.mkdir(exist_ok=True)
        
        logger.info("🎨 Enhanced Dashboard v3.0 inicializado")

    def setup_routes(self, app: FastAPI):
        """Setup todas las rutas del dashboard"""
        
        # Static files
        app.mount("/static", StaticFiles(directory="static"), name="static")
        
        # Main dashboard
        @app.get("/", response_class=HTMLResponse)
        async def dashboard():
            return self._get_dashboard_html()
        
        # API Routes
        @app.get("/api/health")
        async def health():
            return self.watermark_manager.health_check()
        
        @app.get("/api/stats")
        async def get_stats():
            stats = self.watermark_manager.get_stats()
            uptime_hours = (datetime.now() - self.start_time).total_seconds() / 3600
            
            return StatsResponse(
                total_groups=len(self.watermark_manager.get_all_configs()),
                active_configs=len([c for c in self.watermark_manager.get_all_configs().values() 
                                 if c.watermark_type != WatermarkType.NONE]),
                total_processed=stats["processing"]["total_processed"],
                images_processed=stats["processing"]["images_processed"],
                videos_processed=stats["processing"]["videos_processed"],
                text_applied=stats["processing"]["text_applied"],
                png_applied=stats["processing"]["png_applied"],
                errors=stats["processing"]["errors"],
                uptime_hours=uptime_hours
            )
        
        @app.get("/api/groups")
        async def get_groups():
            """Obtener todas las configuraciones de grupos"""
            configs = self.watermark_manager.get_all_configs()
            return {
                str(group_id): {
                    "group_id": config.group_id,
                    "watermark_type": config.watermark_type.value,
                    "png_enabled": config.png_enabled,
                    "png_path": config.png_path,
                    "png_position": config.png_position.value,
                    "png_opacity": config.png_opacity,
                    "png_scale": config.png_scale,
                    "text_enabled": config.text_enabled,
                    "text_content": config.text_content,
                    "text_position": config.text_position.value,
                    "text_color": config.text_color,
                    "video_enabled": config.video_enabled,
                    "updated_at": config.updated_at.isoformat()
                }
                for group_id, config in configs.items()
            }
        
        @app.post("/api/groups/{group_id}/config")
        async def update_group_config(group_id: int, config_request: GroupConfigRequest):
            """Actualizar configuración de grupo"""
            try:
                # Convertir request a kwargs para el manager
                updates = {
                    "watermark_type": WatermarkType(config_request.watermark_type),
                    "png_enabled": config_request.png_enabled,
                    "png_position": Position(config_request.png_position),
                    "png_opacity": config_request.png_opacity,
                    "png_scale": config_request.png_scale,
                    "png_custom_x": config_request.png_custom_x,
                    "png_custom_y": config_request.png_custom_y,
                    "text_enabled": config_request.text_enabled,
                    "text_content": config_request.text_content,
                    "text_position": Position(config_request.text_position),
                    "text_font_size": config_request.text_font_size,
                    "text_color": config_request.text_color,
                    "text_stroke_color": config_request.text_stroke_color,
                    "text_stroke_width": config_request.text_stroke_width,
                    "text_custom_x": config_request.text_custom_x,
                    "text_custom_y": config_request.text_custom_y,
                    "video_enabled": config_request.video_enabled,
                    "video_max_size_mb": config_request.video_max_size_mb,
                    "video_timeout_sec": config_request.video_timeout_sec,
                    "video_compress": config_request.video_compress,
                    "video_quality_crf": config_request.video_quality_crf
                }
                
                # Actualizar o crear configuración
                config = self.watermark_manager.get_group_config(group_id)
                if config:
                    updated_config = self.watermark_manager.update_group_config(group_id, **updates)
                else:
                    updated_config = self.watermark_manager.create_group_config(group_id, **updates)
                
                if not updated_config:
                    raise HTTPException(status_code=500, detail="Error updating configuration")
                
                # Notificar a clientes conectados
                await self._broadcast_update(f"group_{group_id}_updated", updated_config.to_dict())
                
                return {"status": "success", "message": f"Configuración actualizada para grupo {group_id}"}
                
            except Exception as e:
                logger.error(f"Error updating group {group_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.post("/api/groups/{group_id}/watermark/upload")
        async def upload_watermark(group_id: int, file: UploadFile = File(...)):
            """Subir archivo PNG para watermark"""
            try:
                # Validar archivo
                if not file.content_type or not file.content_type.startswith('image/'):
                    raise HTTPException(status_code=400, detail="Solo se permiten archivos de imagen")
                
                # Generar nombre de archivo único
                file_extension = Path(file.filename).suffix.lower()
                if file_extension not in ['.png', '.jpg', '.jpeg']:
                    raise HTTPException(status_code=400, detail="Solo se permiten archivos PNG, JPG o JPEG")
                
                filename = f"watermark_{group_id}_{int(datetime.now().timestamp())}{file_extension}"
                file_path = self.watermark_manager.watermarks_dir / filename
                
                # Guardar archivo
                content = await file.read()
                with open(file_path, 'wb') as f:
                    f.write(content)
                
                # Actualizar configuración del grupo
                self.watermark_manager.update_group_config(
                    group_id, 
                    png_path=filename,
                    png_enabled=True
                )
                
                logger.info(f"📁 Watermark subido para grupo {group_id}: {filename}")
                
                return {
                    "status": "success",
                    "filename": filename,
                    "message": f"Watermark subido exitosamente para grupo {group_id}"
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error uploading watermark for group {group_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.delete("/api/groups/{group_id}")
        async def delete_group_config(group_id: int):
            """Eliminar configuración de grupo"""
            try:
                success = self.watermark_manager.delete_group_config(group_id)
                if not success:
                    raise HTTPException(status_code=404, detail=f"Grupo {group_id} no encontrado")
                
                await self._broadcast_update(f"group_{group_id}_deleted", {"group_id": group_id})
                
                return {"status": "success", "message": f"Configuración eliminada para grupo {group_id}"}
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error deleting group {group_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/api/watermarks/{filename}")
        async def get_watermark_file(filename: str):
            """Servir archivo de watermark"""
            file_path = self.watermark_manager.watermarks_dir / filename
            if not file_path.exists():
                raise HTTPException(status_code=404, detail="Archivo no encontrado")
            
            return FileResponse(file_path)
        
        # WebSocket para updates en tiempo real
        @app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            self.connected_clients.add(websocket)
            
            try:
                # Enviar estado inicial
                stats = self.watermark_manager.get_stats()
                await websocket.send_json({
                    "type": "initial_stats",
                    "data": stats
                })
                
                # Mantener conexión viva
                while True:
                    try:
                        # Ping cada 30 segundos
                        await asyncio.sleep(30)
                        await websocket.send_json({"type": "ping"})
                    except:
                        break
                        
            except WebSocketDisconnect:
                pass
            finally:
                self.connected_clients.discard(websocket)
    
    async def _broadcast_update(self, update_type: str, data: Any):
        """Broadcast update a todos los clientes conectados"""
        if not self.connected_clients:
            return
        
        message = {
            "type": update_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        # Enviar a todos los clientes conectados
        disconnected = set()
        for client in self.connected_clients:
            try:
                await client.send_json(message)
            except:
                disconnected.add(client)
        
        # Remover clientes desconectados
        self.connected_clients -= disconnected
    
    def _get_dashboard_html(self) -> str:
        """Generar HTML del dashboard"""
        return '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎨 Watermark Manager v3.0</title>
    <style>
        /* Apple-inspired CSS */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }

        .header {
            text-align: center;
            margin-bottom: 40px;
            color: white;
        }

        .header h1 {
            font-size: 3rem;
            font-weight: 300;
            margin-bottom: 10px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .header p {
            font-size: 1.2rem;
            opacity: 0.9;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }

        .stat-card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 16px;
            padding: 24px;
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }

        .stat-value {
            font-size: 2.5rem;
            font-weight: 700;
            color: #667eea;
            display: block;
        }

        .stat-label {
            font-size: 0.9rem;
            color: #666;
            margin-top: 8px;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .groups-section {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 24px;
            padding: 32px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }

        .section-title {
            font-size: 1.8rem;
            font-weight: 600;
            margin-bottom: 24px;
            color: #333;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .add-group-btn {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 12px 24px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-bottom: 24px;
        }

        .add-group-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
        }

        .groups-list {
            display: grid;
            gap: 16px;
        }

        .group-card {
            border: 2px solid #e1e5e9;
            border-radius: 16px;
            padding: 24px;
            background: #fafbfc;
            transition: all 0.3s ease;
        }

        .group-card.active {
            border-color: #667eea;
            background: linear-gradient(135deg, #f8f9ff, #f0f4ff);
        }

        .group-header {
            display: flex;
            justify-content: between;
            align-items: center;
            margin-bottom: 20px;
        }

        .group-id {
            font-size: 1.2rem;
            font-weight: 700;
            color: #333;
        }

        .group-status {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .status-active {
            background: #e8f5e8;
            color: #2e7d2e;
        }

        .status-inactive {
            background: #f5f5f5;
            color: #666;
        }

        .config-form {
            display: grid;
            gap: 20px;
        }

        .form-section {
            border: 1px solid #e1e5e9;
            border-radius: 12px;
            padding: 20px;
            background: white;
        }

        .form-section h4 {
            margin-bottom: 16px;
            color: #333;
            font-size: 1.1rem;
            font-weight: 600;
        }

        .form-row {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 16px;
        }

        .form-group {
            display: flex;
            flex-direction: column;
        }

        .form-group label {
            font-size: 0.9rem;
            font-weight: 600;
            color: #555;
            margin-bottom: 6px;
        }

        .form-control {
            padding: 12px 16px;
            border: 2px solid #e1e5e9;
            border-radius: 8px;
            font-size: 1rem;
            transition: border-color 0.3s ease;
            background: white;
        }

        .form-control:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .toggle-switch {
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }

        .switch {
            position: relative;
            width: 50px;
            height: 28px;
            background: #e1e5e9;
            border-radius: 14px;
            cursor: pointer;
            transition: background 0.3s ease;
        }

        .switch.active {
            background: #667eea;
        }

        .switch-handle {
            position: absolute;
            top: 2px;
            left: 2px;
            width: 24px;
            height: 24px;
            background: white;
            border-radius: 50%;
            transition: transform 0.3s ease;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .switch.active .switch-handle {
            transform: translateX(22px);
        }

        .upload-area {
            border: 2px dashed #e1e5e9;
            border-radius: 12px;
            padding: 32px;
            text-align: center;
            transition: all 0.3s ease;
            cursor: pointer;
            background: #fafbfc;
        }

        .upload-area:hover {
            border-color: #667eea;
            background: #f8f9ff;
        }

        .upload-area.dragover {
            border-color: #667eea;
            background: #f0f4ff;
        }

        .save-btn {
            background: linear-gradient(135deg, #28a745, #20c997);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 14px 28px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-top: 20px;
        }

        .save-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(40, 167, 69, 0.4);
        }

        .delete-btn {
            background: linear-gradient(135deg, #dc3545, #c82333);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 8px 16px;
            font-size: 0.9rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .delete-btn:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 15px rgba(220, 53, 69, 0.4);
        }

        .preview-section {
            margin-top: 20px;
            padding: 20px;
            border: 1px solid #e1e5e9;
            border-radius: 12px;
            background: #f8f9fa;
        }

        .preview-image {
            max-width: 100%;
            max-height: 200px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }

        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }

        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 0 auto 16px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .toast {
            position: fixed;
            top: 20px;
            right: 20px;
            background: white;
            border: 1px solid #e1e5e9;
            border-radius: 12px;
            padding: 16px 20px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            transform: translateX(400px);
            transition: transform 0.3s ease;
            z-index: 1000;
        }

        .toast.show {
            transform: translateX(0);
        }

        .toast.success {
            border-left: 4px solid #28a745;
        }

        .toast.error {
            border-left: 4px solid #dc3545;
        }

        @media (max-width: 768px) {
            .container {
                padding: 16px;
            }

            .header h1 {
                font-size: 2rem;
            }

            .stats-grid {
                grid-template-columns: 1fr;
            }

            .form-row {
                grid-template-columns: 1fr;
            }
        }

        /* Estilos para el modal de agregar grupo */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            backdrop-filter: blur(8px);
            z-index: 2000;
            align-items: center;
            justify-content: center;
        }

        .modal.show {
            display: flex;
        }

        .modal-content {
            background: white;
            border-radius: 20px;
            padding: 32px;
            max-width: 500px;
            width: 90%;
            max-height: 80vh;
            overflow-y: auto;
            box-shadow: 0 20px 60px rgba(0,0,0,0.2);
        }

        .modal-header {
            margin-bottom: 24px;
            text-align: center;
        }

        .modal-header h3 {
            font-size: 1.5rem;
            font-weight: 600;
            color: #333;
        }

        .close-btn {
            position: absolute;
            top: 16px;
            right: 16px;
            background: none;
            border: none;
            font-size: 1.5rem;
            cursor: pointer;
            color: #999;
            transition: color 0.3s ease;
        }

        .close-btn:hover {
            color: #333;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎨 Watermark Manager</h1>
            <p>Panel de Control v3.0 - PNG + Texto + Video</p>
        </div>

        <div class="stats-grid" id="statsGrid">
            <div class="stat-card">
                <span class="stat-value" id="totalGroups">0</span>
                <span class="stat-label">Grupos Totales</span>
            </div>
            <div class="stat-card">
                <span class="stat-value" id="activeConfigs">0</span>
                <span class="stat-label">Configuraciones Activas</span>
            </div>
            <div class="stat-card">
                <span class="stat-value" id="totalProcessed">0</span>
                <span class="stat-label">Media Procesados</span>
            </div>
            <div class="stat-card">
                <span class="stat-value" id="uptimeHours">0</span>
                <span class="stat-label">Horas Uptime</span>
            </div>
        </div>

        <div class="groups-section">
            <div class="section-title">
                🔧 Configuración de Grupos
                <button class="add-group-btn" onclick="showAddGroupModal()">
                    ➕ Agregar Grupo
                </button>
            </div>

            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>Cargando configuraciones...</p>
            </div>

            <div class="groups-list" id="groupsList" style="display: none;">
                <!-- Los grupos se cargarán dinámicamente -->
            </div>
        </div>
    </div>

    <!-- Modal para agregar nuevo grupo -->
    <div class="modal" id="addGroupModal">
        <div class="modal-content">
            <button class="close-btn" onclick="hideAddGroupModal()">&times;</button>
            <div class="modal-header">
                <h3>➕ Agregar Nuevo Grupo</h3>
            </div>
            <div class="form-group">
                <label>ID del Grupo de Telegram:</label>
                <input type="number" id="newGroupId" class="form-control" placeholder="-1001234567890">
            </div>
            <button class="save-btn" onclick="addNewGroup()" style="width: 100%; margin-top: 20px;">
                Crear Grupo
            </button>
        </div>
    </div>

    <script>
        // Estado global
        let groups = {};
        let stats = {};
        let websocket = null;

        // Inicializar aplicación
        document.addEventListener('DOMContentLoaded', function() {
            initWebSocket();
            loadStats();
            loadGroups();
        });

        // WebSocket para updates en tiempo real
        function initWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            websocket = new WebSocket(`${protocol}//${window.location.host}/ws`);

            websocket.onmessage = function(event) {
                const message = JSON.parse(event.data);
                
                if (message.type === 'initial_stats') {
                    stats = message.data;
                    updateStatsDisplay();
                } else if (message.type.includes('group_') && message.type.includes('_updated')) {
                    loadGroups(); // Recargar grupos cuando hay updates
                    showToast('Configuración actualizada exitosamente', 'success');
                }
            };

            websocket.onclose = function() {
                console.log('WebSocket connection closed');
                // Reconectar después de 5 segundos
                setTimeout(initWebSocket, 5000);
            };
        }

        // Cargar estadísticas
        async function loadStats() {
            try {
                const response = await fetch('/api/stats');
                const data = await response.json();
                stats = data;
                updateStatsDisplay();
            } catch (error) {
                console.error('Error loading stats:', error);
            }
        }

        // Actualizar display de estadísticas
        function updateStatsDisplay() {
            document.getElementById('totalGroups').textContent = stats.total_groups || 0;
            document.getElementById('activeConfigs').textContent = stats.active_configs || 0;
            document.getElementById('totalProcessed').textContent = stats.total_processed || 0;
            document.getElementById('uptimeHours').textContent = Math.round(stats.uptime_hours || 0);
        }

        // Cargar grupos
        async function loadGroups() {
            try {
                const response = await fetch('/api/groups');
                const data = await response.json();
                groups = data;
                
                document.getElementById('loading').style.display = 'none';
                document.getElementById('groupsList').style.display = 'block';
                
                renderGroups();
            } catch (error) {
                console.error('Error loading groups:', error);
                showToast('Error cargando grupos', 'error');
            }
        }

        // Renderizar lista de grupos
        function renderGroups() {
            const container = document.getElementById('groupsList');
            container.innerHTML = '';

            if (Object.keys(groups).length === 0) {
                container.innerHTML = `
                    <div style="text-align: center; padding: 40px; color: #666;">
                        <p>No hay grupos configurados</p>
                        <p>Haz clic en "Agregar Grupo" para comenzar</p>
                    </div>
                `;
                return;
            }

            Object.values(groups).forEach(group => {
                const groupCard = createGroupCard(group);
                container.appendChild(groupCard);
            });
        }

        // Crear card de grupo
        function createGroupCard(group) {
            const isActive = group.watermark_type !== 'none';
            const card = document.createElement('div');
            card.className = `group-card ${isActive ? 'active' : ''}`;
            
            card.innerHTML = `
                <div class="group-header">
                    <div>
                        <div class="group-id">Grupo ${group.group_id}</div>
                        <div class="group-status ${isActive ? 'status-active' : 'status-inactive'}">
                            ${isActive ? 'Activo' : 'Inactivo'}
                        </div>
                    </div>
                    <button class="delete-btn" onclick="deleteGroup(${group.group_id})">
                        🗑️ Eliminar
                    </button>
                </div>

                <div class="config-form">
                    <!-- Tipo de Watermark -->
                    <div class="form-section">
                        <h4>🎨 Tipo de Watermark</h4>
                        <div class="form-group">
                            <label>Seleccionar tipo:</label>
                            <select class="form-control" onchange="updateWatermarkType(${group.group_id}, this.value)">
                                <option value="none" ${group.watermark_type === 'none' ? 'selected' : ''}>🚫 Sin watermark</option>
                                <option value="text" ${group.watermark_type === 'text' ? 'selected' : ''}>📝 Solo texto</option>
                                <option value="png" ${group.watermark_type === 'png' ? 'selected' : ''}>🖼️ Solo PNG</option>
                                <option value="both" ${group.watermark_type === 'both' ? 'selected' : ''}>🎯 Texto + PNG</option>
                            </select>
                        </div>
                    </div>

                    <!-- Configuración PNG -->
                    <div class="form-section" id="pngSection_${group.group_id}" style="display: ${group.watermark_type === 'png' || group.watermark_type === 'both' ? 'block' : 'none'}">
                        <h4>🖼️ Configuración PNG</h4>
                        
                        <div class="upload-area" onclick="document.getElementById('fileInput_${group.group_id}').click()">
                            <input type="file" id="fileInput_${group.group_id}" style="display: none" accept="image/*" onchange="uploadWatermark(${group.group_id}, this.files[0])">
                            ${group.png_path ? 
                                `<div>
                                    <img src="/api/watermarks/${group.png_path}" class="preview-image" alt="Current watermark">
                                    <p>Haz clic para cambiar watermark</p>
                                </div>` :
                                `<div>
                                    <p>📁 Haz clic para subir PNG</p>
                                    <p>Formatos: PNG, JPG, JPEG</p>
                                </div>`
                            }
                        </div>

                        <div class="form-row">
                            <div class="form-group">
                                <label>Posición:</label>
                                <select class="form-control" onchange="updateGroupConfig(${group.group_id})">
                                    <option value="top_left" ${group.png_position === 'top_left' ? 'selected' : ''}>↖️ Superior Izquierda</option>
                                    <option value="top_right" ${group.png_position === 'top_right' ? 'selected' : ''}>↗️ Superior Derecha</option>
                                    <option value="bottom_left" ${group.png_position === 'bottom_left' ? 'selected' : ''}>↙️ Inferior Izquierda</option>
                                    <option value="bottom_right" ${group.png_position === 'bottom_right' ? 'selected' : ''}>↘️ Inferior Derecha</option>
                                    <option value="center" ${group.png_position === 'center' ? 'selected' : ''}>🎯 Centro</option>
                                    <option value="custom" ${group.png_position === 'custom' ? 'selected' : ''}>⚙️ Personalizada</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label>Opacidad: ${Math.round(group.png_opacity * 100)}%</label>
                                <input type="range" class="form-control" min="0" max="1" step="0.1" value="${group.png_opacity}" oninput="updateOpacityDisplay(this, ${group.group_id})" onchange="updateGroupConfig(${group.group_id})">
                            </div>
                            <div class="form-group">
                                <label>Escala: ${Math.round(group.png_scale * 100)}%</label>
                                <input type="range" class="form-control" min="0.05" max="0.5" step="0.05" value="${group.png_scale}" oninput="updateScaleDisplay(this, ${group.group_id})" onchange="updateGroupConfig(${group.group_id})">
                            </div>
                        </div>
                    </div>

                    <!-- Configuración Texto -->
                    <div class="form-section" id="textSection_${group.group_id}" style="display: ${group.watermark_type === 'text' || group.watermark_type === 'both' ? 'block' : 'none'}">
                        <h4>📝 Configuración Texto</h4>
                        
                        <div class="form-group">
                            <label>Texto personalizado:</label>
                            <textarea class="form-control" rows="3" placeholder="Texto que se agregará a los mensajes..." onchange="updateGroupConfig(${group.group_id})">${group.text_content}</textarea>
                        </div>

                        <div class="form-row">
                            <div class="form-group">
                                <label>Posición en imagen:</label>
                                <select class="form-control" onchange="updateGroupConfig(${group.group_id})">
                                    <option value="top_left" ${group.text_position === 'top_left' ? 'selected' : ''}>↖️ Superior Izquierda</option>
                                    <option value="top_right" ${group.text_position === 'top_right' ? 'selected' : ''}>↗️ Superior Derecha</option>
                                    <option value="bottom_left" ${group.text_position === 'bottom_left' ? 'selected' : ''}>↙️ Inferior Izquierda</option>
                                    <option value="bottom_right" ${group.text_position === 'bottom_right' ? 'selected' : ''}>↘️ Inferior Derecha</option>
                                    <option value="center" ${group.text_position === 'center' ? 'selected' : ''}>🎯 Centro</option>
                                    <option value="custom" ${group.text_position === 'custom' ? 'selected' : ''}>⚙️ Personalizada</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label>Tamaño fuente:</label>
                                <input type="number" class="form-control" min="12" max="72" value="${group.text_font_size}" onchange="updateGroupConfig(${group.group_id})">
                            </div>
                            <div class="form-group">
                                <label>Color texto:</label>
                                <input type="color" class="form-control" value="${group.text_color}" onchange="updateGroupConfig(${group.group_id})">
                            </div>
                        </div>
                    </div>

                    <!-- Configuración Video -->
                    <div class="form-section">
                        <h4>🎬 Configuración Video</h4>
                        <div class="toggle-switch">
                            <span>Procesar videos:</span>
                            <div class="switch ${group.video_enabled ? 'active' : ''}" onclick="toggleVideoProcessing(${group.group_id})">
                                <div class="switch-handle"></div>
                            </div>
                        </div>

                        <div id="videoOptions_${group.group_id}" style="display: ${group.video_enabled ? 'block' : 'none'}; margin-top: 16px;">
                            <div class="form-row">
                                <div class="form-group">
                                    <label>Tamaño máximo (MB):</label>
                                    <input type="number" class="form-control" min="1" max="2048" value="${group.video_max_size_mb}" onchange="updateGroupConfig(${group.group_id})">
                                </div>
                                <div class="form-group">
                                    <label>Timeout (segundos):</label>
                                    <input type="number" class="form-control" min="10" max="300" value="${group.video_timeout_sec}" onchange="updateGroupConfig(${group.group_id})">
                                </div>
                                <div class="form-group">
                                    <div class="toggle-switch">
                                        <span>Comprimir:</span>
                                        <div class="switch ${group.video_compress ? 'active' : ''}" onclick="toggleVideoCompression(${group.group_id})">
                                            <div class="switch-handle"></div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <button class="save-btn" onclick="saveGroupConfig(${group.group_id})">
                        💾 Guardar Configuración
                    </button>
                </div>
            `;

            return card;
        }

        // Actualizar tipo de watermark
        function updateWatermarkType(groupId, type) {
            groups[groupId].watermark_type = type;
            
            // Mostrar/ocultar secciones
            document.getElementById(`pngSection_${groupId}`).style.display = 
                (type === 'png' || type === 'both') ? 'block' : 'none';
            document.getElementById(`textSection_${groupId}`).style.display = 
                (type === 'text' || type === 'both') ? 'block' : 'none';
                
            // Actualizar visual del card
            const card = document.querySelector(`[data-group-id="${groupId}"]`);
            if (card) {
                card.className = `group-card ${type !== 'none' ? 'active' : ''}`;
            }
        }

        // Toggle procesamiento de video
        function toggleVideoProcessing(groupId) {
            groups[groupId].video_enabled = !groups[groupId].video_enabled;
            
            const switchEl = document.querySelector(`#videoOptions_${groupId}`).previousElementSibling.querySelector('.switch');
            const optionsEl = document.getElementById(`videoOptions_${groupId}`);
            
            if (groups[groupId].video_enabled) {
                switchEl.classList.add('active');
                optionsEl.style.display = 'block';
            } else {
                switchEl.classList.remove('active');
                optionsEl.style.display = 'none';
            }
        }

        // Toggle compresión de video
        function toggleVideoCompression(groupId) {
            groups[groupId].video_compress = !groups[groupId].video_compress;
            
            const switchEl = event.target.closest('.switch');
            if (groups[groupId].video_compress) {
                switchEl.classList.add('active');
            } else {
                switchEl.classList.remove('active');
            }
        }

        // Actualizar displays de sliders
        function updateOpacityDisplay(slider, groupId) {
            const label = slider.previousElementSibling;
            label.textContent = `Opacidad: ${Math.round(slider.value * 100)}%`;
        }

        function updateScaleDisplay(slider, groupId) {
            const label = slider.previousElementSibling;
            label.textContent = `Escala: ${Math.round(slider.value * 100)}%`;
        }

        // Subir watermark
        async function uploadWatermark(groupId, file) {
            if (!file) return;

            const formData = new FormData();
            formData.append('file', file);

            try {
                showToast('Subiendo archivo...', 'info');
                
                const response = await fetch(`/api/groups/${groupId}/watermark/upload`, {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();
                
                if (response.ok) {
                    showToast(result.message, 'success');
                    groups[groupId].png_path = result.filename;
                    loadGroups(); // Recargar para mostrar la nueva imagen
                } else {
                    showToast(result.detail || 'Error subiendo archivo', 'error');
                }
            } catch (error) {
                console.error('Error uploading watermark:', error);
                showToast('Error subiendo archivo', 'error');
            }
        }

        // Guardar configuración de grupo
        async function saveGroupConfig(groupId) {
            try {
                const groupData = groups[groupId];
                
                const response = await fetch(`/api/groups/${groupId}/config`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        group_id: groupId,
                        watermark_type: groupData.watermark_type,
                        png_enabled: groupData.watermark_type === 'png' || groupData.watermark_type === 'both',
                        png_position: groupData.png_position,
                        png_opacity: groupData.png_opacity,
                        png_scale: groupData.png_scale,
                        text_enabled: groupData.watermark_type === 'text' || groupData.watermark_type === 'both',
                        text_content: groupData.text_content,
                        text_position: groupData.text_position,
                        text_font_size: groupData.text_font_size,
                        text_color: groupData.text_color,
                        video_enabled: groupData.video_enabled,
                        video_max_size_mb: groupData.video_max_size_mb,
                        video_timeout_sec: groupData.video_timeout_sec,
                        video_compress: groupData.video_compress
                    })
                });

                const result = await response.json();
                
                if (response.ok) {
                    showToast(result.message, 'success');
                    loadStats(); // Recargar stats
                } else {
                    showToast(result.detail || 'Error guardando configuración', 'error');
                }
            } catch (error) {
                console.error('Error saving config:', error);
                showToast('Error guardando configuración', 'error');
            }
        }

        // Actualizar configuración (para cambios en tiempo real)
        function updateGroupConfig(groupId) {
            // Esta función se puede usar para updates inmediatos sin necesidad de hacer clic en guardar
            setTimeout(() => saveGroupConfig(groupId), 1000); // Auto-save después de 1 segundo
        }

        // Eliminar grupo
        async function deleteGroup(groupId) {
            if (!confirm(`¿Estás seguro de que quieres eliminar la configuración del grupo ${groupId}?`)) {
                return;
            }

            try {
                const response = await fetch(`/api/groups/${groupId}`, {
                    method: 'DELETE'
                });

                const result = await response.json();
                
                if (response.ok) {
                    showToast(result.message, 'success');
                    delete groups[groupId];
                    loadGroups();
                    loadStats();
                } else {
                    showToast(result.detail || 'Error eliminando grupo', 'error');
                }
            } catch (error) {
                console.error('Error deleting group:', error);
                showToast('Error eliminando grupo', 'error');
            }
        }

        // Modal para agregar nuevo grupo
        function showAddGroupModal() {
            document.getElementById('addGroupModal').classList.add('show');
        }

        function hideAddGroupModal() {
            document.getElementById('addGroupModal').classList.remove('show');
            document.getElementById('newGroupId').value = '';
        }

        async function addNewGroup() {
            const groupId = document.getElementById('newGroupId').value;
            
            if (!groupId || groupId === '') {
                showToast('Por favor ingresa un ID de grupo válido', 'error');
                return;
            }

            const numericGroupId = parseInt(groupId);
            if (isNaN(numericGroupId)) {
                showToast('El ID del grupo debe ser un número', 'error');
                return;
            }

            if (groups[numericGroupId]) {
                showToast('Este grupo ya existe', 'error');
                return;
            }

            try {
                // Crear configuración básica para el nuevo grupo
                const response = await fetch(`/api/groups/${numericGroupId}/config`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        group_id: numericGroupId,
                        watermark_type: 'none'
                    })
                });

                const result = await response.json();
                
                if (response.ok) {
                    showToast(result.message, 'success');
                    hideAddGroupModal();
                    loadGroups();
                    loadStats();
                } else {
                    showToast(result.detail || 'Error creando grupo', 'error');
                }
            } catch (error) {
                console.error('Error adding group:', error);
                showToast('Error creando grupo', 'error');
            }
        }

        // Sistema de toast notifications
        function showToast(message, type = 'info') {
            // Remover toast existente
            const existingToast = document.querySelector('.toast');
            if (existingToast) {
                existingToast.remove();
            }

            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            toast.innerHTML = `<p>${message}</p>`;
            
            document.body.appendChild(toast);
            
            // Mostrar toast
            setTimeout(() => toast.classList.add('show'), 100);
            
            // Ocultar después de 4 segundos
            setTimeout(() => {
                toast.classList.remove('show');
                setTimeout(() => toast.remove(), 300);
            }, 4000);
        }

        // Cerrar modal con ESC
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape') {
                hideAddGroupModal();
            }
        });

        // Actualizar stats cada 30 segundos
        setInterval(loadStats, 30000);
    </script>
</body>
</html>'''

# ============ FACTORY FUNCTION ============

def create_enhanced_dashboard(watermark_manager: WatermarkManager, 
                            stats_service=None) -> EnhancedDashboardV3:
    """
    Factory function para crear el dashboard enhanced
    Compatible con la estructura existente del proyecto
    """
    return EnhancedDashboardV3(
        watermark_manager=watermark_manager,
        stats_service=stats_service
    )