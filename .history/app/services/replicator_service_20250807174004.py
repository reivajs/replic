"""
App Services Replicator Service
==============================
Servicio principal de replicación integrado con watermarks
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional
from telethon import TelegramClient, events

from app.config.settings import get_settings
from app.utils.logger import setup_logger

# Importar cliente de watermarks
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent / "services"))

try:
    from watermark_client import WatermarkClient
    WATERMARK_CLIENT_AVAILABLE = True
except ImportError:
    WATERMARK_CLIENT_AVAILABLE = False

logger = setup_logger(__name__)
settings = get_settings()

class ReplicatorService:
    """Servicio principal de replicación con soporte de watermarks"""
    
    def __init__(self):
        self.client = None
        self.is_running = False
        self.is_listening = False
        self.stats = {
            'messages_processed': 0,
            'messages_replicated': 0,
            'errors': 0,
            'start_time': datetime.now(),
            'watermarks_applied': 0
        }
        
        # Cliente de watermarks
        if WATERMARK_CLIENT_AVAILABLE:
            self.watermark_client = WatermarkClient()
        else:
            self.watermark_client = None
            logger.warning("⚠️ Watermark client no disponible")
    
    async def initialize(self):
        """Inicializar servicio de replicación"""
        try:
            logger.info("🔧 Inicializando cliente de Telegram...")
            
            # Crear cliente de Telegram
            self.client = TelegramClient(
                settings.telegram.session_name,
                settings.telegram.api_id,
                settings.telegram.api_hash
            )
            
            # Conectar
            await self.client.start(phone=settings.telegram.phone)
            me = await self.client.get_me()
            
            logger.info(f"✅ Conectado a Telegram como: {me.first_name}")
            
            # Registrar handlers
            self.client.add_event_handler(self._handle_message, events.NewMessage())
            
            self.is_running = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Error inicializando replicador: {e}")
            return False
    
    async def start_listening(self):
        """Iniciar escucha de mensajes"""
        if not self.is_running:
            logger.error("❌ Servicio no inicializado")
            return
        
        try:
            logger.info("👂 Iniciando escucha de mensajes...")
            self.is_listening = True
            
            # Verificar watermark service
            if self.watermark_client:
                service_available = await self.watermark_client.is_service_available()
                if service_available:
                    logger.info("🎨 Watermark service disponible")
                else:
                    logger.warning("⚠️ Watermark service no disponible")
            
            # Ejecutar cliente de Telegram
            await self.client.run_until_disconnected()
            
        except Exception as e:
            logger.error(f"❌ Error en escucha: {e}")
        finally:
            self.is_listening = False
    
    async def _handle_message(self, event):
        """Handler principal de mensajes"""
        try:
            chat_id = event.chat_id
            message = event.message
            
            # Verificar si hay webhook configurado para este grupo
            if chat_id not in settings.discord.webhooks:
                return
            
            logger.debug(f"📨 Procesando mensaje de {chat_id}")
            
            # Procesar según tipo de mensaje
            if message.text and not message.media:
                await self._process_text_message(chat_id, message)
            elif message.photo:
                await self._process_image_message(chat_id, message)
            elif message.video:
                await self._process_video_message(chat_id, message)
            else:
                await self._process_other_message(chat_id, message)
            
            self.stats['messages_processed'] += 1
            
        except Exception as e:
            logger.error(f"❌ Error procesando mensaje: {e}")
            self.stats['errors'] += 1
    
    async def _process_text_message(self, chat_id: int, message):
        """Procesar mensaje de texto con watermarks"""
        try:
            text = message.text
            
            # Aplicar watermarks si está disponible
            if self.watermark_client:
                processed_text, was_modified = await self.watermark_client.process_text(chat_id, text)
                if was_modified:
                    text = processed_text
                    self.stats['watermarks_applied'] += 1
                    logger.debug(f"📝 Watermark aplicado a texto para grupo {chat_id}")
            
            # Enviar a Discord (simplificado)
            await self._send_to_discord(chat_id, {"content": text})
            
        except Exception as e:
            logger.error(f"❌ Error procesando texto: {e}")
    
    async def _process_image_message(self, chat_id: int, message):
        """Procesar mensaje con imagen"""
        try:
            # Descargar imagen
            image_bytes = await message.download_media(bytes)
            
            # Aplicar watermarks si está disponible
            if self.watermark_client:
                processed_bytes, was_processed = await self.watermark_client.process_image(chat_id, image_bytes)
                if was_processed:
                    image_bytes = processed_bytes
                    self.stats['watermarks_applied'] += 1
                    logger.debug(f"🖼️ Watermark aplicado a imagen para grupo {chat_id}")
            
            # Procesar caption
            caption = message.text or ""
            if caption and self.watermark_client:
                caption, _ = await self.watermark_client.process_text(chat_id, caption)
            
            # Enviar a Discord (simplificado)
            await self._send_image_to_discord(chat_id, image_bytes, caption)
            
        except Exception as e:
            logger.error(f"❌ Error procesando imagen: {e}")
    
    async def _process_video_message(self, chat_id: int, message):
        """Procesar mensaje con video"""
        try:
            # Por ahora, enviar sin procesar (video watermarks son más complejos)
            logger.debug(f"🎬 Procesando video para grupo {chat_id}")
            
            # Aquí se podría integrar procesamiento de video con watermarks
            # pero lo dejamos simple por ahora
            
            caption = message.text or ""
            if caption and self.watermark_client:
                caption, _ = await self.watermark_client.process_text(chat_id, caption)
            
            await self._send_to_discord(chat_id, {"content": f"📹 Video: {caption}"})
            
        except Exception as e:
            logger.error(f"❌ Error procesando video: {e}")
    
    async def _process_other_message(self, chat_id: int, message):
        """Procesar otros tipos de mensajes"""
        try:
            content = f"📎 Contenido multimedia de tipo: {type(message.media).__name__}"
            await self._send_to_discord(chat_id, {"content": content})
        except Exception as e:
            logger.error(f"❌ Error procesando mensaje: {e}")
    
    async def _send_to_discord(self, chat_id: int, payload: Dict[str, Any]):
        """Enviar mensaje a Discord (implementación simplificada)"""
        try:
            webhook_url = settings.discord.webhooks.get(chat_id)
            if not webhook_url:
                return
            
            # Aquí iría la implementación real de envío a Discord
            # Por ahora solo logueamos
            logger.debug(f"📤 Enviando a Discord: {payload}")
            self.stats['messages_replicated'] += 1
            
        except Exception as e:
            logger.error(f"❌ Error enviando a Discord: {e}")
    
    async def _send_image_to_discord(self, chat_id: int, image_bytes: bytes, caption: str = ""):
        """Enviar imagen a Discord"""
        try:
            # Implementación simplificada
            logger.debug(f"🖼️ Enviando imagen a Discord para grupo {chat_id}")
            self.stats['messages_replicated'] += 1
        except Exception as e:
            logger.error(f"❌ Error enviando imagen: {e}")
    
    async def stop(self):
        """Detener servicio"""
        try:
            self.is_running = False
            self.is_listening = False
            
            if self.client and self.client.is_connected():
                await self.client.disconnect()
                logger.info("🛑 Cliente de Telegram desconectado")
            
            if self.watermark_client and hasattr(self.watermark_client, 'session'):
                if self.watermark_client.session:
                    await self.watermark_client.session.close()
            
        except Exception as e:
            logger.error(f"❌ Error deteniendo servicio: {e}")
    
    async def get_health(self) -> Dict[str, Any]:
        """Obtener estado de salud del servicio"""
        return {
            "status": "running" if self.is_running else "stopped",
            "listening": self.is_listening,
            "telegram_connected": self.client.is_connected() if self.client else False,
            "watermark_service": await self.watermark_client.is_service_available() if self.watermark_client else False,
            "stats": self.stats.copy()
        }
    
    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas para el dashboard"""
        uptime = (datetime.now() - self.stats['start_time']).total_seconds()
        
        return {
            "total_messages": self.stats['messages_processed'],
            "replicated_messages": self.stats['messages_replicated'],
            "watermarks_applied": self.stats['watermarks_applied'],
            "errors": self.stats['errors'],
            "uptime_seconds": uptime,
            "uptime_hours": uptime / 3600,
            "groups_configured": len(settings.discord.webhooks),
            "is_running": self.is_running,
            "is_listening": self.is_listening
        }
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Obtener estado completo del sistema"""
        return await self.get_health()