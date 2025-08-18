
# ============ LAZY SERVICE ACCESS HELPERS ============

def __get_replicator_service():
    """Lazy access to replicator service"""
    try:
        from app.main import get_replicator_service
        return _get_replicator_service()
    except Exception:
        return None

def _get_watermark_service():
    """Lazy access to watermark service"""
    try:
        from app.main import get_watermark_service
        return get_watermark_service()
    except Exception:
        return None

def _get_discord_service():
    """Lazy access to discord service"""
    try:
        from app.main import get_discord_service
        return get_discord_service()
    except Exception:
        return None

"""
Dependency Injection Module - FIXED
===================================
"""

from functools import lru_cache
from app.services.cache import CacheService
from app.database.connection import get_db

@lru_cache()
def get_service_registry():
    """Get service registry instance"""
    return service_registry

@lru_cache()
def get_cache_service():
    """Get cache service instance"""
    return CacheService()

def get_db_session():
    """Get database session"""
    return get_db()

def get_cache():
    """Alias for cache service"""
    return get_cache_service()

__all__ = [
    'get_service_registry',
    'get_cache_service',
    'get_db_session',
    'get_cache'
]
