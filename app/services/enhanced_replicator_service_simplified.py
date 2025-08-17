"""
Enhanced Replicator Service - SIMPLIFIED & FIXED
================================================
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Safe Telethon imports
TELETHON_AVAILABLE = False
MEDIA_VIDEO_AVAILABLE = False
TELETHON_VIDEO_SUPPORT = False

try:
    from telethon import TelegramClient, events
    from telethon.tl.types import MessageMediaDocument, MessageMediaPhoto
    TELETHON_AVAILABLE = True
    print("✅ Telethon base: Available")
    
    # Try video support
    try:
        from telethon.tl.types import DocumentAttributeVideo
        TELETHON_VIDEO_SUPPORT = True
        print("✅ Telethon video support: Available")
    except ImportError:
        print("⚠️ Telethon video support: Not available")
        
except ImportError as e:
    print(f"⚠️ Telethon not available: {e}")

# Import other services
from .discord_sender import DiscordSenderEnhanced
from .file_processor import FileProcessorEnhanced
from .watermark_service import WatermarkServiceIntegrated

from app.config.settings import get_settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)
settings = get_settings()

class EnhancedReplicatorService:
    """
    Enhanced Replicator Service - SIMPLIFIED VERSION
    ================================================
    """
    
    def __init__(self):
        """Initialize the service"""
        self.telegram_client = None
        self.is_running = False
        self.is_listening = False
        
        # Services
        self.file_processor = FileProcessorEnhanced()
        self.watermark_service = WatermarkServiceIntegrated()
        self.discord_sender = DiscordSenderEnhanced()
        
        # Stats
        self.stats = {
            'messages_received': 0,
            'messages_replicated': 0,
            'messages_filtered': 0,
            'errors': 0,
            'start_time': datetime.now(),
            'groups_active': set()
        }
        
        logger.info("✅ Enhanced Replicator Service initialized (simplified)")
    
    async def initialize(self):
        """Initialize the service"""
        try:
            logger.info("🔧 Initializing Enhanced Replicator Service...")
            
            if not TELETHON_AVAILABLE:
                logger.warning("⚠️ Telethon not available - running in limited mode")
                return True
            
            # Initialize Telegram client if credentials available
            if hasattr(settings, 'telegram') and settings.telegram.api_id:
                await self._initialize_telegram()
            else:
                logger.warning("⚠️ Telegram credentials not configured")
            
            self.is_running = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Initialization error: {e}")
            return False
    
    async def _initialize_telegram(self):
        """Initialize Telegram client"""
        try:
            session_name = 'telegram_session'
            self.telegram_client = TelegramClient(
                session_name,
                settings.telegram.api_id,
                settings.telegram.api_hash
            )
            
            await self.telegram_client.connect()
            
            if not await self.telegram_client.is_user_authorized():
                logger.warning("⚠️ Telegram client not authorized - need to login")
            else:
                me = await self.telegram_client.get_me()
                logger.info(f"✅ Telegram connected: {me.first_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Telegram initialization failed: {e}")
            return False
    
    async def start_listening(self):
        """Start listening for messages"""
        if not self.telegram_client:
            logger.error("❌ Telegram client not initialized")
            return
        
        try:
            logger.info("👂 Starting message listening...")
            self.is_listening = True
            
            # Setup event handlers
            @self.telegram_client.on(events.NewMessage)
            async def handle_message(event):
                try:
                    self.stats['messages_received'] += 1
                    logger.info(f"📨 New message from chat {event.chat_id}")
                    
                    # Here you would process and forward the message
                    # For now, just log it
                    
                except Exception as e:
                    logger.error(f"❌ Error handling message: {e}")
                    self.stats['errors'] += 1
            
            # Keep the client running
            await self.telegram_client.run_until_disconnected()
            
        except Exception as e:
            logger.error(f"❌ Listening error: {e}")
        finally:
            self.is_listening = False
            logger.info("🛑 Listening stopped")
    
    async def stop(self):
        """Stop the service"""
        logger.info("🛑 Stopping Enhanced Replicator Service...")
        
        self.is_running = False
        self.is_listening = False
        
        if self.telegram_client:
            await self.telegram_client.disconnect()
        
        logger.info("✅ Service stopped")
    
    async def get_health(self):
        """Get health status"""
        return {
            "status": "healthy" if self.is_running else "stopped",
            "telethon_available": TELETHON_AVAILABLE,
            "video_support": TELETHON_VIDEO_SUPPORT,
            "is_listening": self.is_listening,
            "stats": self.stats
        }
    
    async def get_dashboard_stats(self):
        """Get dashboard statistics"""
        uptime = (datetime.now() - self.stats['start_time']).total_seconds()
        
        return {
            "messages_received": self.stats['messages_received'],
            "messages_replicated": self.stats['messages_replicated'],
            "errors": self.stats['errors'],
            "uptime_seconds": uptime,
            "uptime_formatted": f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m",
            "groups_active": len(self.stats['groups_active']),
            "is_running": self.is_running,
            "is_listening": self.is_listening
        }
