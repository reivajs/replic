"""Discovery Router"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict, Any

router = APIRouter()

@router.get("/chats")
async def get_discovered_chats(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
) -> Dict[str, Any]:
    """Get discovered chats"""
    # For now, return empty list
    return {
        "chats": [],
        "total": 0,
        "limit": limit,
        "offset": offset
    }

@router.post("/scan")
async def trigger_scan(force_refresh: bool = False) -> Dict[str, Any]:
    """Trigger discovery scan"""
    return {
        "status": "scan_started",
        "force_refresh": force_refresh,
        "timestamp": datetime.now().isoformat()
    }
