"""
App Services - Enhanced Replicator Service
==========================================
Servicio de replicación que SÍ funciona con arquitectura de microservicios
Replicación real de mensajes entre Telegram y Discord
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
from telethon import TelegramClient, events
from telethon.tl.types import User, Chat, Channel

from app.config.settings import get_settings
from app.utils.logger import setup_logger

# Añadir services al path
sys.path.append(str(Path(__file__).parent.parent.parent / "services"))

# Importar microservicios
try:
    from watermark_client import WatermarkClient
    WATERMARK_CLIENT_AVAILABLE = True
except ImportError:
    WATERMARK_CLIENT_AVAILABLE = False

try:
    from discord.sender import DiscordSenderService, DiscordMessage
    DISCORD_SENDER_AVAILABLE = True
except ImportError:
    # Fallback a implementación básica
    DISCORD_SENDER_AVAILABLE = False

logger = setup_logger(__name__)
settings = get_settings()

class EnhancedReplicatorService:
    """
    🚀 Servicio de replicación enhanced que SÍ replica mensajes
    
    Características:
    - Replicación real Telegram → Discord
    - Integración con microservicio de watermarks
    - Microservicio de Discord con retry logic
    - Filtros de mensajes configurables
    - Métricas detalladas en tiempo real
    - Error handling robusto
    - Soporte para texto, imágenes y videos
    """
    
    def __init__(self):
        self.telegram_client = None
        self.is_running = False
        self.is_listening = False
        
        # Estadísticas detalladas
        self.stats = {
            'messages_received': 0,
            'messages_replicated': 0,
            'messages_filtered': 0,
            'images_processed': 0,
            'videos_processed': 0,
            'watermarks_applied': 0,
            'errors': 0,
            'start_time': datetime.now(),
            'last_message_time': None,
            'groups_active': set()
        }
        
        # Microservicios
        self.watermark_client = None
        self.discord_sender = None
        
        # Configuración de filtros
        self.filters = {
            'min_length': getattr(settings, 'min_text_length', 0),
            'skip_words': getattr(settings, 'skip_words', []),
            'only_words': getattr(settings, 'only_words', []),
            'enabled': True
        }
        
        logger.info("🚀 Enhanced Replicator Service inicializado")
    
    async def initialize(self):
        """Inicializar todos los servicios"""
        try:
            logger.info("🔧 Inicializando Enhanced Replicator Service...")
            
            # 1. Inicializar cliente de Telegram
            success = await self._initialize_telegram()
            if not success:
                return False
            
            # 2. Inicializar microservicios
            await self._initialize_microservices()
            
            # 3. Configurar handlers de eventos
            self._setup_event_handlers()
            
            # 4. Verificar configuración
            validation_result = await self._validate_configuration()
            if not validation_result['valid']:
                logger.error(f"❌ Configuración inválida: {validation_result['errors']}")
                return False
            
            self.is_running = True
            logger.info("✅ Enhanced Replicator Service inicializado correctamente")
            
            # Log de configuración
            logger.info(f"📊 Configuración:")
            logger.info(f"   Grupos configurados: {len(settings.discord.webhooks)}")
            logger.info(f"   Watermarks: {'✅' if self.watermark_client else '❌'}")
            logger.info(f"   Discord sender: {'✅' if self.discord_sender else '❌'}")
            logger.info(f"   Filtros: {'✅' if self.filters['enabled'] else '❌'}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error inicializando replicador: {e}")
            return False
    
    async def _initialize_telegram(self) -> bool:
        """Inicializar cliente de Telegram"""
        try:
            logger.info("📱 Conectando a Telegram...")
            
            # Verificar configuración
            if not settings.telegram.api_id or not settings.telegram.api_hash or not settings.telegram.phone:
                logger.error("❌ Configuración de Telegram incompleta")
                return False
            
            # Crear cliente
            self.telegram_client = TelegramClient(
                settings.telegram.session_name,
                settings.telegram.api_id,
                settings.telegram.api_hash
            )
            
            # Conectar
            await self.telegram_client.start(phone=settings.telegram.phone)
            me = await self.telegram_client.get_me()
            
            logger.info(f"✅ Conectado a Telegram como: {me.first_name} (@{me.username or 'sin_username'})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error conectando a Telegram: {e}")
            return False
    
    async def _initialize_microservices(self):
        """Inicializar microservicios"""
        
        # Watermark Client
        if WATERMARK_CLIENT_AVAILABLE:
            try:
                self.watermark_client = WatermarkClient()
                service_available = await self.watermark_client.is_service_available()
                if service_available:
                    logger.info("🎨 Watermark microservice conectado")
                else:
                    logger.warning("⚠️ Watermark microservice no disponible")
                    self.watermark_client = None
            except Exception as e:
                logger.warning(f"⚠️ Error conectando watermark service: {e}")
                self.watermark_client = None
        else:
            logger.warning("⚠️ Watermark client no disponible")
        
        # Discord Sender
        if DISCORD_SENDER_AVAILABLE:
            try:
                self.discord_sender = DiscordSenderService()
                await self.discord_sender.__aenter__()
                logger.info("📤 Discord sender service inicializado")
            except Exception as e:
                logger.warning(f"⚠️ Error inicializando Discord sender: {e}")
                self.discord_sender = None
        else:
            # Fallback a implementación básica
            logger.warning("⚠️ Usando Discord sender básico")
    
    def _setup_event_handlers(self):
        """Configurar handlers de eventos de Telegram"""
        if not self.telegram_client:
            return
        
        # Handler principal de mensajes
        self.telegram_client.add_event_handler(
            self._handle_new_message,
            events.NewMessage()
        )
        
        # Handler para mensajes editados (opcional)
        self.telegram_client.add_event_handler(
            self._handle_message_edited,
            events.MessageEdited()
        )
        
        logger.info("📡 Event handlers configurados")
    
    async def start_listening(self):
        """Iniciar escucha de mensajes"""
        if not self.is_running:
            logger.error("❌ Servicio no inicializado")
            return
        
        try:
            logger.info("👂 Iniciando escucha de mensajes de Telegram...")
            self.is_listening = True
            
            # Mostrar grupos monitoreados
            for group_id in settings.discord.webhooks.keys():
                logger.info(f"   👥 Monitoreando grupo: {group_id}")
            
            # Ejecutar cliente de Telegram
            await self.telegram_client.run_until_disconnected()
            
        except Exception as e:
            logger.error(f"❌ Error en escucha: {e}")
        finally:
            self.is_listening = False
            logger.info("🛑 Escucha detenida")
    
    async def _handle_new_message(self, event):
        """Handler principal para mensajes nuevos"""
        try:
            chat_id = event.chat_id
            message = event.message
            
            # Actualizar estadísticas
            self.stats['messages_received'] += 1
            self.stats['last_message_time'] = datetime.now()
            self.stats['groups_active'].add(chat_id)
            
            # Verificar si hay webhook configurado para este grupo
            if chat_id not in settings.discord.webhooks:
                logger.debug(f"📋 Grupo {chat_id} no configurado, ignorando mensaje")
                return
            
            # Obtener información del chat
            chat_info = await self._get_chat_info(chat_id)
            logger.debug(f"📨 Mensaje de {chat_info['name']} ({chat_id})")
            
            # Aplicar filtros
            if not await self._should_process_message(message):
                self.stats['messages_filtered'] += 1
                logger.debug(f"🚫 Mensaje filtrado de {chat_id}")
                return
            
            # Procesar según tipo de mensaje
            success = False
            
            if message.text and not message.media:
                success = await self._process_text_message(chat_id, message, chat_info)
            elif message.photo:
                success = await self._process_image_message(chat_id, message, chat_info)
            elif message.video:
                success = await self._process_video_message(chat_id, message, chat_info)
            elif message.document:
                success = await self._process_document_message(chat_id, message, chat_info)
            else:
                success = await self._process_other_message(chat_id, message, chat_info)
            
            # Actualizar estadísticas
            if success:
                self.stats['messages_replicated'] += 1
                logger.info(f"✅ Mensaje replicado: {chat_info['name']} → Discord")
            else:
                self.stats['errors'] += 1
                logger.warning(f"❌ Error replicando mensaje de {chat_info['name']}")
                
        except Exception as e:
            logger.error(f"❌ Error procesando mensaje: {e}")
            self.stats['errors'] += 1
    
    async def _handle_message_edited(self, event):
        """Handler para mensajes editados"""
        # Por ahora, ignoramos mensajes editados
        # Se podría implementar lógica para actualizar mensajes en Discord
        pass
    
    async def _process_text_message(self, chat_id: int, message, chat_info: Dict) -> bool:
        """Procesar mensaje de texto"""
        try:
            text = message.text
            
            # Aplicar watermarks de texto si está disponible
            if self.watermark_client:
                processed_text, was_modified = await self.watermark_client.process_text(chat_id, text)
                if was_modified:
                    text = processed_text
                    self.stats['watermarks_applied'] += 1
                    logger.debug(f"📝 Watermark aplicado a texto para {chat_info['name']}")
            
            # Crear mensaje para Discord
            discord_message = DiscordMessage(
                content=text,
                username=f"📱 {chat_info['name']}",
                avatar_url=chat_info.get('avatar_url')
            )
            
            # Enviar a Discord
            return await self._send_to_discord(chat_id, discord_message)
            
        except Exception as e:
            logger.error(f"❌ Error procesando texto: {e}")
            return False
    
    async def _process_image_message(self, chat_id: int, message, chat_info: Dict) -> bool:
        """Procesar mensaje con imagen"""
        try:
            logger.info(f"🖼️ Procesando imagen de {chat_info['name']}")
            
            # Descargar imagen
            image_bytes = await message.download_media(bytes)
            if not image_bytes:
                logger.error("❌ No se pudo descargar la imagen")
                return False
            
            # Aplicar watermarks si está disponible
            processed_bytes = image_bytes
            if self.watermark_client:
                processed_bytes, was_processed = await self.watermark_client.process_image(chat_id, image_bytes)
                if was_processed:
                    self.stats['watermarks_applied'] += 1
                    logger.debug(f"🎨 Watermark aplicado a imagen para {chat_info['name']}")
            
            # Procesar caption
            caption = message.text or ""
            if caption and self.watermark_client:
                caption, _ = await self.watermark_client.process_text(chat_id, caption)
            
            # Añadir info del canal al caption
            full_caption = f"📷 Imagen de **{chat_info['name']}**"
            if caption:
                full_caption += f"\n\n{caption}"
            
            # Enviar imagen a Discord
            return await self._send_image_to_discord(chat_id, processed_bytes, full_caption)
            
        except Exception as e:
            logger.error(f"❌ Error procesando imagen: {e}")
            return False
    
    async def _process_video_message(self, chat_id: int, message, chat_info: Dict) -> bool:
        """Procesar mensaje con video"""
        try:
            logger.info(f"🎬 Procesando video de {chat_info['name']}")
            
            # Verificar tamaño del video
            if message.video and message.video.size:
                size_mb = message.video.size / (1024 * 1024)
                if size_mb > 8:  # Discord limit
                    logger.warning(f"⚠️ Video demasiado grande: {size_mb:.1f}MB")
                    # Enviar solo caption
                    caption = message.text or ""
                    if caption and self.watermark_client:
                        caption, _ = await self.watermark_client.process_text(chat_id, caption)
                    
                    discord_message = DiscordMessage(
                        content=f"🎬 Video de **{chat_info['name']}** (demasiado grande para Discord)\n\n{caption}",
                        username=f"📱 {chat_info['name']}"
                    )
                    return await self._send_to_discord(chat_id, discord_message)
            
            # Descargar video
            video_bytes = await message.download_media(bytes)
            if not video_bytes:
                logger.error("❌ No se pudo descargar el video")
                return False
            
            # Procesar caption
            caption = message.text or ""
            if caption and self.watermark_client:
                caption, _ = await self.watermark_client.process_text(chat_id, caption)
            
            # Añadir info del canal al caption
            full_caption = f"🎬 Video de **{chat_info['name']}**"
            if caption:
                full_caption += f"\n\n{caption}"
            
            # Enviar video a Discord
            return await self._send_video_to_discord(chat_id, video_bytes, full_caption)
            
        except Exception as e:
            logger.error(f"❌ Error procesando video: {e}")
            return False
    
    async def _process_document_message(self, chat_id: int, message, chat_info: Dict) -> bool:
        """Procesar documento"""
        try:
            # Verificar si es un video
            if message.document and message.document.mime_type and message.document.mime_type.startswith('video/'):
                return await self._process_video_message(chat_id, message, chat_info)
            
            # Para otros documentos, enviar solo descripción
            caption = message.text or ""
            if caption and self.watermark_client:
                caption, _ = await self.watermark_client.process_text(chat_id, caption)
            
            doc_name = getattr(message.document, 'file_name', 'Documento')
            size_mb = getattr(message.document, 'size', 0) / (1024 * 1024)
            
            discord_message = DiscordMessage(
                content=f"📎 **{chat_info['name']}** compartió: {doc_name} ({size_mb:.1f}MB)\n\n{caption}",
                username=f"📱 {chat_info['name']}"
            )
            
            return await self._send_to_discord(chat_id, discord_message)
            
        except Exception as e:
            logger.error(f"❌ Error procesando documento: {e}")
            return False
    
    async def _process_other_message(self, chat_id: int, message, chat_info: Dict) -> bool:
        """Procesar otros tipos de mensajes"""
        try:
            content_type = "mensaje multimedia"
            
            if message.sticker:
                content_type = "sticker"
            elif message.audio:
                content_type = "audio"
            elif message.voice:
                content_type = "nota de voz"
            elif message.gif:
                content_type = "GIF"
            
            caption = message.text or ""
            if caption and self.watermark_client:
                caption, _ = await self.watermark_client.process_text(chat_id, caption)
            
            discord_message = DiscordMessage(
                content=f"📎 **{chat_info['name']}** envió un {content_type}\n\n{caption}",
                username=f"📱 {chat_info['name']}"
            )
            
            return await self._send_to_discord(chat_id, discord_message)
            
        except Exception as e:
            logger.error(f"❌ Error procesando mensaje: {e}")
            return False
    
    async def _send_to_discord(self, chat_id: int, discord_message: DiscordMessage) -> bool:
        """Enviar mensaje a Discord usando microservicio"""
        try:
            webhook_url = settings.discord.webhooks.get(chat_id)
            if not webhook_url:
                logger.error(f"❌ No hay webhook configurado para {chat_id}")
                return False
            
            if self.discord_sender:
                # Usar microservicio Discord
                result = await self.discord_sender.send_text_message(webhook_url, discord_message)
                return result.success
            else:
                # Fallback a implementación básica
                return await self._send_basic_discord(webhook_url, discord_message)
                
        except Exception as e:
            logger.error(f"❌ Error enviando a Discord: {e}")
            return False
    
    async def _send_image_to_discord(self, chat_id: int, image_bytes: bytes, caption: str = "") -> bool:
        """Enviar imagen a Discord"""
        try:
            webhook_url = settings.discord.webhooks.get(chat_id)
            if not webhook_url:
                return False
            
            if self.discord_sender:
                result = await self.discord_sender.send_image_message(
                    webhook_url, image_bytes, caption, "image.jpg"
                )
                if result.success:
                    self.stats['images_processed'] += 1
                return result.success
            else:
                # Fallback básico
                return await self._send_basic_discord_file(webhook_url, image_bytes, caption, "image.jpg")
                
        except Exception as e:
            logger.error(f"❌ Error enviando imagen: {e}")
            return False
    
    async def _send_video_to_discord(self, chat_id: int, video_bytes: bytes, caption: str = "") -> bool:
        """Enviar video a Discord"""
        try:
            webhook_url = settings.discord.webhooks.get(chat_id)
            if not webhook_url:
                return False
            
            if self.discord_sender:
                result = await self.discord_sender.send_video_message(
                    webhook_url, video_bytes, caption, "video.mp4"
                )
                if result.success:
                    self.stats['videos_processed'] += 1
                return result.success
            else:
                # Fallback básico
                return await self._send_basic_discord_file(webhook_url, video_bytes, caption, "video.mp4")
                
        except Exception as e:
            logger.error(f"❌ Error enviando video: {e}")
            return False
    
    async def _send_basic_discord(self, webhook_url: str, discord_message: DiscordMessage) -> bool:
        """Implementación básica de envío a Discord (fallback)"""
        try:
            import aiohttp
            
            payload = discord_message.to_dict()
            
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(webhook_url, json=payload) as response:
                    success = response.status == 204
                    if not success:
                        logger.warning(f"⚠️ Discord response: {response.status}")
                    return success
                    
        except Exception as e:
            logger.error(f"❌ Error en envío básico: {e}")
            return False
    
    async def _send_basic_discord_file(self, webhook_url: str, file_bytes: bytes, 
                                     caption: str, filename: str) -> bool:
        """Envío básico de archivos a Discord"""
        try:
            import aiohttp
            
            data = aiohttp.FormData()
            if caption:
                data.add_field('content', caption)
            
            content_type = 'image/jpeg' if filename.endswith('.jpg') else 'video/mp4'
            data.add_field('file', file_bytes, filename=filename, content_type=content_type)
            
            timeout = aiohttp.ClientTimeout(total=60)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(webhook_url, data=data) as response:
                    success = response.status == 200
                    if not success:
                        logger.warning(f"⚠️ Discord file response: {response.status}")
                    return success
                    
        except Exception as e:
            logger.error(f"❌ Error enviando archivo: {e}")
            return False
    
    async def _get_chat_info(self, chat_id: int) -> Dict[str, Any]:
        """Obtener información del chat"""
        try:
            entity = await self.telegram_client.get_entity(chat_id)
            
            if isinstance(entity, User):
                name = f"{entity.first_name or ''} {entity.last_name or ''}".strip()
                if not name:
                    name = entity.username or f"User {entity.id}"
            elif isinstance(entity, (Chat, Channel)):
                name = entity.title or f"Chat {entity.id}"
            else:
                name = f"Unknown {chat_id}"
            
            return {
                'name': name,
                'type': type(entity).__name__,
                'avatar_url': None  # Se podría implementar descarga de avatar
            }
            
        except Exception as e:
            logger.warning(f"⚠️ No se pudo obtener info de {chat_id}: {e}")
            return {
                'name': f"Chat {chat_id}",
                'type': 'Unknown',
                'avatar_url': None
            }
    
    async def _should_process_message(self, message) -> bool:
        """Aplicar filtros al mensaje"""
        if not self.filters['enabled']:
            return True
        
        text = message.text
        if not text:
            return True  # Procesar media sin texto
        
        text_lower = text.lower()
        
        # Filtro de longitud mínima
        if len(text) < self.filters['min_length']:
            return False
        
        # Filtro de palabras a omitir
        if self.filters['skip_words']:
            for skip_word in self.filters['skip_words']:
                if skip_word.lower() in text_lower:
                    return False
        
        # Filtro de solo ciertas palabras
        if self.filters['only_words']:
            found_word = False
            for only_word in self.filters['only_words']:
                if only_word.lower() in text_lower:
                    found_word = True
                    break
            if not found_word:
                return False
        
        return True
    
    async def _validate_configuration(self) -> Dict[str, Any]:
        """Validar configuración del sistema"""
        errors = []
        warnings = []
        
        # Verificar Telegram
        if not settings.telegram.api_id:
            errors.append("TELEGRAM_API_ID no configurado")
        if not settings.telegram.api_hash:
            errors.append("TELEGRAM_API_HASH no configurado")
        if not settings.telegram.phone:
            errors.append("TELEGRAM_PHONE no configurado")
        
        # Verificar Discord
        if not settings.discord.webhooks:
            errors.append("No hay webhooks de Discord configurados")
        
        # Verificar microservicios
        if not self.watermark_client:
            warnings.append("Watermark microservice no disponible")
        if not self.discord_sender:
            warnings.append("Discord sender microservice no disponible")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    async def stop(self):
        """Detener servicio"""
        try:
            logger.info("🛑 Deteniendo Enhanced Replicator Service...")
            
            self.is_running = False
            self.is_listening = False
            
            # Cerrar cliente de Telegram
            if self.telegram_client and self.telegram_client.is_connected():
                await self.telegram_client.disconnect()
                logger.info("📱 Cliente de Telegram desconectado")
            
            # Cerrar microservicios
            if self.watermark_client and hasattr(self.watermark_client, 'session'):
                if self.watermark_client.session and not self.watermark_client.session.closed:
                    await self.watermark_client.session.close()
            
            if self.discord_sender:
                await self.discord_sender.__aexit__(None, None, None)
                logger.info("📤 Discord sender cerrado")
            
            logger.info("✅ Enhanced Replicator Service detenido")
            
        except Exception as e:
            logger.error(f"❌ Error deteniendo servicio: {e}")
    
    async def get_health(self) -> Dict[str, Any]:
        """Health check del servicio"""
        return {
            "status": "running" if self.is_running else "stopped",
            "listening": self.is_listening,
            "telegram_connected": (
                self.telegram_client.is_connected() 
                if self.telegram_client else False
            ),
            "watermark_service": (
                await self.watermark_client.is_service_available() 
                if self.watermark_client else False
            ),
            "discord_sender": self.discord_sender is not None,
            "stats": self.get_formatted_stats()
        }
    
    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """Estadísticas para dashboard"""
        uptime = (datetime.now() - self.stats['start_time']).total_seconds()
        
        return {
            "total_messages": self.stats['messages_received'],
            "replicated_messages": self.stats['messages_replicated'],
            "filtered_messages": self.stats['messages_filtered'],
            "images_processed": self.stats['images_processed'],
            "videos_processed": self.stats['videos_processed'],
            "watermarks_applied": self.stats['watermarks_applied'],
            "errors": self.stats['errors'],
            "uptime_seconds": uptime,
            "uptime_hours": uptime / 3600,
            "groups_configured": len(settings.discord.webhooks),
            "groups_active": len(self.stats['groups_active']),
            "is_running": self.is_running,
            "is_listening": self.is_listening,
            "last_message": (
                self.stats['last_message_time'].isoformat() 
                if self.stats['last_message_time'] else None
            ),
            "success_rate": (
                (self.stats['messages_replicated'] / 
                 max(self.stats['messages_received'], 1)) * 100
            )
        }
    
    def get_formatted_stats(self) -> Dict[str, Any]:
        """Estadísticas formateadas"""
        uptime = (datetime.now() - self.stats['start_time']).total_seconds()
        
        return {
            **self.stats,
            'groups_active': list(self.stats['groups_active']),
            'uptime_seconds': uptime,
            'uptime_formatted': f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m",
            'last_message_time': (
                self.stats['last_message_time'].isoformat() 
                if self.stats['last_message_time'] else None
            )
        }
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Estado completo del sistema"""
        health = await self.get_health()
        stats = await self.get_dashboard_stats()
        
        return {
            "service": "enhanced_replicator",
            "version": "2.0.0",
            "health": health,
            "stats": stats,
            "microservices": {
                "watermark": self.watermark_client is not None,
                "discord_sender": self.discord_sender is not None
            },
            "configuration": {
                "groups_configured": len(settings.discord.webhooks),
                "filters_enabled": self.filters['enabled'],
                "telegram_configured": bool(
                    settings.telegram.api_id and 
                    settings.telegram.api_hash and 
                    settings.telegram.phone
                )
            }
        }

# ============ ALIAS PARA COMPATIBILIDAD ============

# Para mantener compatibilidad con tu main.py existente
ReplicatorService = EnhancedReplicatorService