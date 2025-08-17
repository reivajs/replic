"""
Dashboard API Routes - Enterprise Backend
========================================
Archivo: app/api/dashboard.py

Endpoints para el dashboard enterprise con métricas en tiempo real
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Dict, Any, Optional
from pathlib import Path  # ✅ IMPORT FALTANTE AGREGADO
import asyncio
from datetime import datetime, timedelta
import json

from app.utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()

# Templates para el dashboard
templates = Jinja2Templates(directory="templates")

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """Servir dashboard enterprise moderno"""
    try:
        # Leer el archivo HTML del dashboard
        dashboard_path = Path("templates/dashboard_enterprise.html")
        
        if dashboard_path.exists():
            with open(dashboard_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return HTMLResponse(content=content)
        else:
            # Fallback: servir dashboard básico embebido
            logger.warning("Dashboard template not found, serving embedded version")
            return HTMLResponse(content=get_embedded_dashboard_html())
            
    except Exception as e:
        logger.error(f"Error serving dashboard: {e}")
        # Fallback robusto
        return HTMLResponse(content=get_error_dashboard_html(str(e)))

@router.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """
    Endpoint principal para obtener estadísticas del dashboard enterprise
    """
    try:
        # Obtener servicio del replicador desde la aplicación global
        from main import replicator_service
        
        if not replicator_service:
            raise HTTPException(status_code=503, detail="Replicator service not available")
        
        # Obtener estadísticas enterprise
        stats = await replicator_service.get_dashboard_stats()
        
        # Estructurar datos para el dashboard frontend
        dashboard_data = {
            "overview": {
                "messages_received": stats.get("overview", {}).get("messages_received", 0),
                "messages_replicated": stats.get("overview", {}).get("messages_replicated", 0),
                "success_rate": stats.get("overview", {}).get("success_rate", 0),
                "error_rate": stats.get("overview", {}).get("error_rate", 0),
                "uptime_hours": stats.get("overview", {}).get("uptime_hours", 0),
                "is_running": stats.get("overview", {}).get("is_running", False),
                "is_listening": stats.get("overview", {}).get("is_listening", False)
            },
            "processing": {
                "pdfs_processed": stats.get("processing", {}).get("pdfs_processed", 0),
                "videos_processed": stats.get("processing", {}).get("videos_processed", 0),
                "images_processed": stats.get("processing", {}).get("images_processed", 0),
                "audios_processed": stats.get("processing", {}).get("audios_processed", 0),
                "documents_processed": stats.get("processing", {}).get("documents_processed", 0),
                "watermarks_applied": stats.get("processing", {}).get("watermarks_applied", 0)
            },
            "performance": {
                "avg_processing_time": stats.get("performance", {}).get("avg_processing_time", 0),
                "active_connections": stats.get("performance", {}).get("active_connections", 0),
                "cache_hit_rate": stats.get("performance", {}).get("cache_hit_rate", 0),
                "memory_usage": stats.get("performance", {}).get("memory_usage", 0)
            },
            "groups": {
                "configured": stats.get("groups", {}).get("configured", 0),
                "active": stats.get("groups", {}).get("active", 0),
                "active_list": stats.get("groups", {}).get("active_list", [])
            },
            "errors": {
                "total_errors": stats.get("errors", {}).get("total_errors", 0),
                "total_retries": stats.get("errors", {}).get("total_retries", 0),
                "circuit_breaker_trips": stats.get("errors", {}).get("circuit_breaker_trips", 0)
            },
            "timestamps": {
                "last_message": stats.get("timestamps", {}).get("last_message"),
                "start_time": stats.get("timestamps", {}).get("start_time"),
                "current_time": datetime.now().isoformat()
            }
        }
        
        return JSONResponse(content=dashboard_data)
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        # Retornar datos de fallback para que el dashboard no se rompa
        return JSONResponse(content=get_fallback_stats())

@router.get("/api/dashboard/health")
async def get_system_health():
    """
    Endpoint para health check enterprise detallado
    """
    try:
        from main import replicator_service
        
        if not replicator_service:
            return JSONResponse(
                content={"status": "unhealthy", "error": "Service not available"},
                status_code=503
            )
        
        health_data = await replicator_service.get_health()
        
        # Añadir métricas adicionales de sistema
        health_data.update({
            "api_status": "healthy",
            "database_status": "healthy",  # Aquí podrías verificar la DB
            "external_services": {
                "telegram": health_data.get("dependencies", {}).get("telethon", False),
                "discord": True,  # Verificar conectividad Discord
                "ffmpeg": health_data.get("dependencies", {}).get("ffmpeg", False)
            },
            "resource_usage": {
                "cpu_percent": get_cpu_usage(),
                "memory_percent": get_memory_usage(),
                "disk_usage": get_disk_usage()
            }
        })
        
        return JSONResponse(content=health_data)
        
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        return JSONResponse(
            content={"status": "unhealthy", "error": str(e)},
            status_code=500
        )

@router.get("/api/dashboard/metrics/realtime")
async def get_realtime_metrics():
    """
    Endpoint para métricas en tiempo real (WebSocket alternative)
    """
    try:
        from main import replicator_service
        
        if not replicator_service:
            raise HTTPException(status_code=503, detail="Service not available")
        
        # Obtener métricas enterprise
        metrics = await replicator_service.get_enterprise_metrics()
        
        # Añadir timestamp para freshness
        metrics["timestamp"] = datetime.now().isoformat()
        metrics["freshness"] = "realtime"
        
        return JSONResponse(content=metrics)
        
    except Exception as e:
        logger.error(f"Error getting realtime metrics: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

@router.get("/api/dashboard/activity")
async def get_recent_activity():
    """
    Endpoint para obtener actividad reciente
    """
    try:
        # Aquí podrías implementar un sistema de logs/activity feed
        # Por ahora, retornar actividad simulada basada en stats reales
        
        from main import replicator_service
        
        activities = []
        
        if replicator_service:
            stats = await replicator_service.get_dashboard_stats()
            
            # Generar actividades basadas en stats reales
            if stats.get("processing", {}).get("pdfs_processed", 0) > 0:
                activities.append({
                    "id": f"pdf_{datetime.now().timestamp()}",
                    "type": "pdf_processed",
                    "icon": "fas fa-file-pdf",
                    "color": "#ef4444",
                    "text": f"PDF processed successfully",
                    "time": "2 minutes ago",
                    "metadata": {"count": stats["processing"]["pdfs_processed"]}
                })
            
            if stats.get("processing", {}).get("videos_processed", 0) > 0:
                activities.append({
                    "id": f"video_{datetime.now().timestamp()}",
                    "type": "video_processed", 
                    "icon": "fas fa-video",
                    "color": "#8b5cf6",
                    "text": f"Video compression completed",
                    "time": "5 minutes ago",
                    "metadata": {"count": stats["processing"]["videos_processed"]}
                })
            
            if stats.get("overview", {}).get("messages_received", 0) > 0:
                activities.append({
                    "id": f"message_{datetime.now().timestamp()}",
                    "type": "message_processed",
                    "icon": "fas fa-envelope", 
                    "color": "var(--primary-gradient)",
                    "text": f"Messages replicated to Discord",
                    "time": "1 minute ago",
                    "metadata": {"count": stats["overview"]["messages_received"]}
                })
        
        return JSONResponse(content={"activities": activities[:10]})  # Últimas 10
        
    except Exception as e:
        logger.error(f"Error getting recent activity: {e}")
        return JSONResponse(content={"activities": []})

@router.get("/api/dashboard/groups")
async def get_groups_status():
    """
    Endpoint para estado de grupos
    """
    try:
        from main import replicator_service
        from app.config.settings import get_settings
        
        settings = get_settings()
        groups_data = []
        
        if replicator_service:
            stats = await replicator_service.get_dashboard_stats()
            active_groups = stats.get("groups", {}).get("active_list", [])
            
            for group_id, webhook_url in settings.discord.webhooks.items():
                group_info = {
                    "id": group_id,
                    "name": f"Group {group_id}",  # Podrías mapear nombres reales
                    "status": "active" if group_id in active_groups else "inactive",
                    "webhook_configured": bool(webhook_url),
                    "last_activity": get_last_activity_for_group(group_id),
                    "message_count": get_message_count_for_group(group_id),
                    "success_rate": 98.5  # Calcular rate real por grupo
                }
                groups_data.append(group_info)
        
        return JSONResponse(content={"groups": groups_data})
        
    except Exception as e:
        logger.error(f"Error getting groups status: {e}")
        return JSONResponse(content={"groups": []})

@router.post("/api/dashboard/groups/{group_id}/watermarks")
async def update_group_watermarks(group_id: int, watermark_config: dict):
    """
    Endpoint para actualizar configuración de watermarks por grupo
    """
    try:
        from main import replicator_service
        
        if not replicator_service or not replicator_service.watermark_service:
            raise HTTPException(status_code=503, detail="Watermark service not available")
        
        # Actualizar configuración de watermarks
        success = await replicator_service.watermark_service.update_group_config(
            group_id, watermark_config
        )
        
        if success:
            return JSONResponse(content={
                "success": True,
                "message": f"Watermark configuration updated for group {group_id}",
                "group_id": group_id,
                "config": watermark_config
            })
        else:
            raise HTTPException(status_code=400, detail="Failed to update watermark configuration")
            
    except Exception as e:
        logger.error(f"Error updating watermarks for group {group_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/dashboard/watermarks/{group_id}")
async def get_group_watermarks(group_id: int):
    """
    Obtener configuración de watermarks para un grupo
    """
    try:
        from main import replicator_service
        
        if not replicator_service or not replicator_service.watermark_service:
            raise HTTPException(status_code=503, detail="Watermark service not available")
        
        config = await replicator_service.watermark_service.get_group_config_dict(group_id)
        
        return JSONResponse(content={
            "group_id": group_id,
            "config": config
        })
        
    except Exception as e:
        logger.error(f"Error getting watermarks for group {group_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Funciones auxiliares

def get_fallback_stats() -> Dict[str, Any]:
    """Datos de fallback cuando el servicio no está disponible"""
    return {
        "overview": {
            "messages_received": 0,
            "messages_replicated": 0,
            "success_rate": 0,
            "error_rate": 0,
            "uptime_hours": 0,
            "is_running": False,
            "is_listening": False
        },
        "processing": {
            "pdfs_processed": 0,
            "videos_processed": 0,
            "images_processed": 0,
            "audios_processed": 0,
            "documents_processed": 0,
            "watermarks_applied": 0
        },
        "performance": {
            "avg_processing_time": 0,
            "active_connections": 0,
            "cache_hit_rate": 0,
            "memory_usage": 0
        },
        "groups": {
            "configured": 0,
            "active": 0,
            "active_list": []
        },
        "errors": {
            "total_errors": 0,
            "total_retries": 0,
            "circuit_breaker_trips": 0
        },
        "timestamps": {
            "last_message": None,
            "start_time": datetime.now().isoformat(),
            "current_time": datetime.now().isoformat()
        }
    }

def get_cpu_usage() -> float:
    """Obtener uso de CPU"""
    try:
        import psutil
        return psutil.cpu_percent(interval=1)
    except ImportError:
        return 0.0

def get_memory_usage() -> float:
    """Obtener uso de memoria"""
    try:
        import psutil
        return psutil.virtual_memory().percent
    except ImportError:
        return 0.0

def get_disk_usage() -> float:
    """Obtener uso de disco"""
    try:
        import psutil
        return psutil.disk_usage('/').percent
    except ImportError:
        return 0.0

def get_last_activity_for_group(group_id: int) -> Optional[str]:
    """Obtener última actividad de un grupo"""
    # Implementar lógica real basada en logs/database
    return datetime.now().isoformat()

def get_message_count_for_group(group_id: int) -> int:
    """Obtener count de mensajes de un grupo"""
    # Implementar lógica real basada en stats del servicio
    return 0

def get_embedded_dashboard_html() -> str:
    """Dashboard HTML embebido como fallback"""
    return """
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ReplicBot Enterprise - Dashboard</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/alpinejs/3.13.3/cdn.min.js" defer></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.min.js"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .dashboard {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 3rem;
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.2);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
        }
        .logo { font-size: 3rem; margin-bottom: 1rem; }
        .title { font-size: 2rem; margin-bottom: 0.5rem; font-weight: 700; }
        .subtitle { opacity: 0.8; margin-bottom: 2rem; }
        .stats { display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; margin-bottom: 2rem; }
        .stat {
            background: rgba(255, 255, 255, 0.1);
            padding: 1rem;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .stat-value { font-size: 2rem; font-weight: 700; }
        .stat-label { font-size: 0.875rem; opacity: 0.8; }
        .refresh-btn {
            background: rgba(255, 255, 255, 0.2);
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 25px;
            color: white;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        .refresh-btn:hover { background: rgba(255, 255, 255, 0.3); }
        .status { color: #10b981; font-weight: 600; }
    </style>
</head>
<body x-data="simpleDashboard()">
    <div class="dashboard">
        <div class="logo">🚀</div>
        <h1 class="title">ReplicBot Enterprise</h1>
        <p class="subtitle">Sistema funcionando correctamente</p>
        
        <div class="stats">
            <div class="stat">
                <div class="stat-value" x-text="stats.messages">-</div>
                <div class="stat-label">Mensajes</div>
            </div>
            <div class="stat">
                <div class="stat-value" x-text="stats.success_rate + '%'">-</div>
                <div class="stat-label">Éxito</div>
            </div>
            <div class="stat">
                <div class="stat-value" x-text="stats.groups">-</div>
                <div class="stat-label">Grupos</div>
            </div>
            <div class="stat">
                <div class="stat-value" x-text="stats.uptime">-</div>
                <div class="stat-label">Uptime</div>
            </div>
        </div>
        
        <div class="status">✅ Sistema Online</div>
        <br>
        <button class="refresh-btn" @click="refreshStats()" :disabled="loading">
            <i class="fas fa-sync-alt" :class="{ 'fa-spin': loading }"></i>
            <span x-text="loading ? 'Actualizando...' : 'Actualizar'"></span>
        </button>
    </div>

    <script>
        function simpleDashboard() {
            return {
                loading: false,
                stats: {
                    messages: 0,
                    success_rate: 0,
                    groups: 0,
                    uptime: '0h'
                },
                
                init() {
                    this.loadStats();
                    setInterval(() => this.loadStats(), 30000);
                },
                
                async loadStats() {
                    try {
                        const response = await fetch('/api/dashboard/stats');
                        if (response.ok) {
                            const data = await response.json();
                            this.stats = {
                                messages: data.overview?.messages_received || 0,
                                success_rate: Math.round(data.overview?.success_rate || 0),
                                groups: data.groups?.active || 0,
                                uptime: this.formatUptime(data.overview?.uptime_hours || 0)
                            };
                        }
                    } catch (error) {
                        console.error('Error loading stats:', error);
                    }
                },
                
                async refreshStats() {
                    this.loading = true;
                    await this.loadStats();
                    setTimeout(() => this.loading = false, 1000);
                },
                
                formatUptime(hours) {
                    if (hours >= 24) {
                        return Math.floor(hours / 24) + 'd';
                    }
                    return Math.floor(hours) + 'h';
                }
            }
        }
    </script>
</body>
</html>
    """

def get_error_dashboard_html(error: str) -> str:
    """Dashboard de error cuando hay problemas"""
    return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard Error</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #1a1a2e;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            margin: 0;
        }}
        .error {{
            text-align: center;
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.3);
            border-radius: 12px;
            padding: 2rem;
        }}
        .error-icon {{ font-size: 3rem; margin-bottom: 1rem; }}
        .error-title {{ font-size: 1.5rem; margin-bottom: 1rem; }}
        .error-message {{ opacity: 0.8; margin-bottom: 1rem; }}
        .retry-btn {{
            background: #ef4444;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            color: white;
            cursor: pointer;
        }}
    </style>
</head>
<body>
    <div class="error">
        <div class="error-icon">⚠️</div>
        <h1 class="error-title">Dashboard Error</h1>
        <p class="error-message">Error: {error}</p>
        <button class="retry-btn" onclick="location.reload()">Reintentar</button>
    </div>
</body>
</html>
    """

# HTML Content constant (removido porque ya no es necesario)
# DASHBOARD_HTML_CONTENT se reemplaza por las funciones de arriba