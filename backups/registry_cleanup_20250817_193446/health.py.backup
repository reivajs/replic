"""Health Check Router"""
from fastapi import APIRouter, Depends
from datetime import datetime
from typing import Dict, Any

router = APIRouter()

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Basic health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "orchestrator",
        "version": "1.0.0"
    }

@router.get("/health/detailed")
async def health_detailed() -> Dict[str, Any]:
    """Detailed health check"""
    try:
        from app.services.registry import service_registry
        healthy, total = await service_registry.check_all_services()
        
        return {
            "status": "healthy" if healthy > 0 else "degraded",
            "services": {
                "healthy": healthy,
                "total": total,
                "percentage": (healthy / total * 100) if total > 0 else 0
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
