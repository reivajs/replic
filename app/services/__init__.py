"""
Services Module
===============
"""

from .registry import ServiceRegistry
from .discovery import ServiceDiscovery
from .cache import CacheService
from .metrics import MetricsCollector

# Simplified imports to avoid circular dependencies
try:
    from .watermark_service import WatermarkServiceIntegrated
except ImportError:
    WatermarkServiceIntegrated = None

__all__ = [
    'ServiceRegistry',
    'ServiceDiscovery', 
    'CacheService',
    'MetricsCollector',
    'WatermarkServiceIntegrated'
]
