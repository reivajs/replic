"""
App API Routes
=============
Rutas de la API REST
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from datetime import datetime

from app.config.settings import get_settings

router = APIRouter()
settings = get_settings()

@router.get("/status")
async def get_api_status():
    """Estado de la API"""
    return {
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }

@router.get("/config")
async def get_configuration():
    """Obtener configuración básica (sin datos sensibles)"""
    return {
        "telegram_configured": bool(settings.telegram.api_id and settings.telegram.api_hash),
        "discord_webhooks_count": len(settings.discord.webhooks),
        "watermarks_enabled": settings.watermarks_enabled,
        "debug_mode": settings.debug
    }

@router.get("/groups")
async def get_configured_groups():
    """Obtener grupos configurados"""
    groups = []
    for group_id in settings.discord.webhooks.keys():
        groups.append({
            "group_id": group_id,
            "configured": True
        })
    
    return {"groups": groups}