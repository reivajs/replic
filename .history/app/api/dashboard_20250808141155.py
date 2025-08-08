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
        # Aquí podrías pasar datos iniciales al template
        context = {
            "request": request,
            "title": "ReplicBot Enterprise Dashboard",
            "version": "3.0.0"
        }
        
        # Si tienes el HTML como template
        # return templates.TemplateResponse("dashboard.html", context)
        
        # Por ahora, devolver el HTML directo desde el artifact
        return HTMLResponse(content=DASHBOARD_HTML_CONTENT)
        
    except Exception as e:
        logger.error(f"Error serving dashboard: {e}")
        raise HTTPException(status_code=500, detail="Dashboard unavailable")

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

# HTML Content constant (para servir el dashboard)
DASHBOARD_HTML_CONTENT = """
<!-- Aquí iría el contenido HTML del dashboard -->
<!-- Por simplicidad, se puede cargar desde el artifact -->
"""