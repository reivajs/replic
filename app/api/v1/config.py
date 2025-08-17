"""Configuration Router"""
from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter()

@router.get("/")
async def get_configuration() -> Dict[str, Any]:
    """Get current configuration"""
    return {
        "webhooks": [],
        "telegram_configured": False,
        "discord_webhooks_count": 0
    }

@router.post("/reload")
async def reload_configuration() -> Dict[str, Any]:
    """Reload configuration"""
    return {"status": "configuration reloaded"}
