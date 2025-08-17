"""
Metrics Collector (Simplified)
===============================
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class MetricsCollector:
    """Simplified metrics collector"""
    
    def __init__(self, prometheus_enabled: bool = False):
        self.prometheus_enabled = prometheus_enabled
        self.start_time = datetime.now()
        self.request_count = 0
        logger.info("Metrics Collector initialized")
    
    async def start(self):
        """Start metrics collection"""
        logger.info("Metrics collection started")
    
    async def stop(self):
        """Stop metrics collection"""
        logger.info("Metrics collection stopped")
    
    def record_request(self):
        """Record a request"""
        self.request_count += 1
    
    def get_metrics(self):
        """Get current metrics"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        return {
            "uptime_seconds": uptime,
            "request_count": self.request_count
        }
