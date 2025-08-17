"""
Cache Service Module
====================
"""

import redis.asyncio as redis
import json
from typing import Any, Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class CacheService:
    def __init__(self, redis_url: str = None, ttl: int = 300):
        self.redis_url = redis_url or settings.REDIS_URL
        self.ttl = ttl
        self.client = None
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.client = await redis.from_url(self.redis_url)
            await self.client.ping()
            logger.info("✅ Redis connected")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.client:
            await self.client.close()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.client:
            return None
        
        try:
            value = await self.client.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
        return None
    
    async def set(self, key: str, value: Any, ttl: int = None):
        """Set value in cache"""
        if not self.client:
            return
        
        try:
            ttl = ttl or self.ttl
            await self.client.set(
                key,
                json.dumps(value),
                ex=ttl
            )
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    async def delete(self, key: str):
        """Delete key from cache"""
        if not self.client:
            return
        
        try:
            await self.client.delete(key)
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
