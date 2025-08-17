"""
Replicator Service Adapter - FIXED
===================================
"""

import asyncio
from typing import Dict, Any, Optional
import logging

try:
    from app.services.enhanced_replicator_service import EnhancedReplicatorService
    ENHANCED_AVAILABLE = True
except ImportError:
    ENHANCED_AVAILABLE = False
    EnhancedReplicatorService = None

logger = logging.getLogger(__name__)

class ReplicatorServiceAdapter:
    """Adaptador para EnhancedReplicatorService - FIXED"""
    
    def __init__(self):
        self.service: Optional[EnhancedReplicatorService] = None
        self.is_initialized = False
        
    async def initialize(self):
        """Inicializar el servicio"""
        if not ENHANCED_AVAILABLE:
            logger.error("❌ EnhancedReplicatorService not available")
            return False
        
        try:
            self.service = EnhancedReplicatorService()
            await self.service.initialize()
            self.is_initialized = True
            logger.info("✅ ReplicatorServiceAdapter initialized")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize replicator: {e}")
            return False
    
    async def start(self):
        """Iniciar el servicio"""
        if not self.is_initialized:
            await self.initialize()
        
        if self.service:
            asyncio.create_task(self.service.start_listening())
            logger.info("✅ Replicator service started")
    
    async def stop(self):
        """Detener el servicio"""
        if self.service:
            await self.service.stop()
            logger.info("✅ Replicator service stopped")
    
    async def get_health(self) -> Dict[str, Any]:
        """Obtener estado de salud"""
        if not self.service:
            return {"status": "unhealthy", "error": "Service not initialized"}
        
        try:
            return await self.service.get_health()
        except:
            return {"status": "unhealthy"}
    
    async def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas (async)"""
        if not self.service:
            return {}
        
        try:
            # Check if method exists and is async
            if hasattr(self.service, 'get_dashboard_stats'):
                stats = self.service.get_dashboard_stats()
                # If it's a coroutine, await it
                if asyncio.iscoroutine(stats):
                    return await stats
                else:
                    return stats
            else:
                return self.service.stats if hasattr(self.service, 'stats') else {}
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}
    
    def get_stats_sync(self) -> Dict[str, Any]:
        """Obtener estadísticas (sync) - para evitar problemas de await"""
        if not self.service:
            return {}
        
        try:
            if hasattr(self.service, 'stats'):
                return dict(self.service.stats)
            return {}
        except Exception as e:
            logger.error(f"Error getting sync stats: {e}")
            return {}

# Instancia global
replicator_adapter = ReplicatorServiceAdapter()
