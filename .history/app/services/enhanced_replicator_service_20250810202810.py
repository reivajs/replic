"""
🚀 ENHANCED REPLICATOR SERVICE v4.0 - ENTERPRISE OPTIMIZED
==========================================================
Archivo: app/services/enhanced_replicator_service.py

✅ REPLICACIÓN DIRECTA de multimedia sin localhost/enlaces
✅ Integración perfecta con Discord Sender corregido
✅ Envío directo de videos, PDFs, audios, imágenes
✅ Procesamiento enterprise con watermarks
✅ Circuit breakers y retry logic
✅ Métricas en tiempo real
✅ Arquitectura modular y escalable

OPTIMIZACIONES PRINCIPALES:
- Envío directo sin almacenamiento temporal
- Procesamiento en memoria para mejor performance
- Error handling robusto con fallbacks
- Integración seamless con microservicios
"""

import asyncio
import logging
import time
import io
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Set, Union
from dataclasses import dataclass, field
from pathlib import Path

try:
    from telethon import TelegramClient, events
    from telethon.tl.types import User, Chat, Channel, MessageMediaPhoto, MessageMediaDocument
    TELETHON_AVAILABLE = True
except ImportError:
    TELETHON_AVAILABLE = False
    logger.error("❌ Telethon no disponible")

from app.config.settings import get_settings
from app.utils.logger import setup_logger
from app.services.discord_sender import DiscordSenderEnterprise
from app.services.file_processor import FileProcessorEnhanced
from app.services.watermark_service import WatermarkServiceEnterprise

logger = setup_logger(__name__)
settings = get_settings()

@dataclass
class ProcessingStats:
    """Estadísticas detalladas de procesamiento"""
    messages_received: int = 0
    messages_replicated: int = 0
    messages_filtered: int = 0
    images_processed: int = 0
    videos_processed: int = 0
    audios_processed: int = 0
    pdfs_processed: int = 0
    watermarks_applied: int = 0
    errors: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    last_message_time: Optional[datetime] = None
    groups_active: Set[int] = field(default_factory=set)
    total_bytes_processed: int = 0

@dataclass
class ReplicatorConfig:
    """Configuración enterprise del replicador"""
    max_concurrent_processing: int = 10
    processing_timeout: int = 300  # 5 minutos
    max_file_size_mb: int = 25  # Aumentado para enterprise
    retry_attempts: int = 3
    circuit_breaker_threshold: int = 5
    enable_watermarks: bool = True
    enable_compression: bool = True
    enable_preview_generation: bool = True
    filters_enabled: bool = True


class EnhancedReplicatorServiceEnterprise:
    """
    🚀 ENHANCED REPLICATOR SERVICE v4.0 - ENTERPRISE OPTIMIZED
    ===========================================================
    
    Servicio de replicación enterprise que SÍ replica mensajes multimedia
    directamente sin localhost ni enlaces temporales.
    
    CARACTERÍSTICAS ENTERPRISE:
    ✅ Replicación directa Telegram → Discord
    ✅ Envío directo de multimedia en memoria
    ✅ Integración con microservicios enterprise
    ✅ Procesamiento paralelo optimizado
    ✅ Circuit breakers y retry logic
    ✅ Watermarks y compresión inteligente
    ✅ Métricas en tiempo real
    ✅ Error handling robusto
    """
    
    def __init__(self):
        self.telegram_client: Optional[TelegramClient] = None
        self.discord_sender: Optional[DiscordSenderEnterprise] = None
        self.file_processor: Optional[FileProcessorEnterprise] = None
        self.watermark_service: Optional[WatermarkServiceEnterprise] = None
        
        # Estado del servicio
        self.is_running = False
        self.is_listening = False
        self.initialization_complete = False
        
        # Configuración enterprise
        self.config = ReplicatorConfig()
        
        # Estadísticas detalladas
        self.stats = ProcessingStats()
        
        # Control de concurrencia
        self.processing_semaphore = asyncio.Semaphore(self.config.max_concurrent_processing)
        self.active_tasks: Set[asyncio.Task] = set()
        
        # Filtros configurables
        self.filters = {
            'enabled': self.config.filters_enabled,
            'min_length': 0,
            'skip_words': [],
            'only_words': [],
            'skip_users': set(),
            'allowed_file_types': {'.jpg', '.jpeg', '.png', '.gif', '.mp4', '.avi', '.mov', 
                                 '.pdf', '.mp3', '.wav', '.ogg', '.m4a', '.webm', '.mkv'}
        }
        
        logger.info("🚀 Enhanced Replicator Service v4.0 Enterprise initialized")
    
    async def initialize(self) -> bool:
        """
        🔧 INICIALIZACIÓN ENTERPRISE COMPLETA
        =====================================
        """
        try:
            logger.info("🔧 Initializing Enhanced Replicator Service Enterprise...")
            
            # 1. Verificar dependencias críticas
            if not TELETHON_AVAILABLE:
                logger.error("❌ Telethon no disponible - Replicación deshabilitada")
                return False
            
            # 2. Inicializar cliente Telegram
            if not await self._initialize_telegram():
                logger.error("❌ Falló inicialización de Telegram")
                return False
            
            # 3. Inicializar microservicios enterprise
            await self._initialize_enterprise_services()
            
            # 4. Configurar event handlers
            self._setup_event_handlers()
            
            # 5. Validar configuración
            validation_result = await self._validate_configuration()
            if validation_result['errors']:
                logger.warning(f"⚠️ Errores de configuración: {validation_result['errors']}")
            
            self.initialization_complete = True
            self.is_running = True
            
            # 6. Mostrar configuración enterprise
            await self._display_enterprise_configuration()
            
            logger.info("✅ Enhanced Replicator Service Enterprise initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error durante inicialización: {e}")
            return False
    
    async def _initialize_telegram(self) -> bool:
        """Inicializar cliente de Telegram enterprise"""
        try:
            if not all([settings.telegram.api_id, settings.telegram.api_hash, settings.telegram.phone]):
                logger.error("❌ Configuración de Telegram incompleta")
                return False
            
            logger.info("📱 Connecting to Telegram Enterprise...")
            
            self.telegram_client = TelegramClient(
                settings.telegram.session_name,
                settings.telegram.api_id,
                settings.telegram.api_hash,
                device_model="Enterprise Replicator",
                system_version="4.0",
                app_version="Enterprise",
                lang_code="es",
                system_lang_code="es"
            )
            
            await self.telegram_client.start(phone=settings.telegram.phone)
            
            # Obtener información del usuario
            me = await self.telegram_client.get_me()
            username = f"@{me.username}" if me.username else "sin_username"
            display_name = f"{me.first_name or ''} {me.last_name or ''}".strip()
            
            logger.info(f"✅ Connected to Telegram as: {display_name} ({username})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error conectando a Telegram: {e}")
            return False
    
    async def _initialize_enterprise_services(self):
        """Inicializar microservicios enterprise"""
        try:
            # Inicializar File Processor
            self.file_processor = FileProcessorEnterprise()
            await self.file_processor.initialize()
            
            # Inicializar Watermark Service  
            self.watermark_service = WatermarkServiceEnterprise()
            await self.watermark_service.initialize()
            
            # Inicializar Discord Sender (CORREGIDO)
            self.discord_sender = DiscordSenderEnterprise()
            await self.discord_sender.initialize()
            
            logger.info("✅ Enterprise microservices initialized")
            
        except Exception as e:
            logger.warning(f"⚠️ Error inicializando microservicios: {e}")
            # Continuar sin microservicios si fallan (modo fallback)
    
    def _setup_event_handlers(self):
        """Configurar event handlers de Telegram"""
        if not self.telegram_client:
            return
        
        @self.telegram_client.on(events.NewMessage)
        async def handle_new_message(event):
            """Handler principal de mensajes"""
            try:
                await self._handle_new_message_enterprise(event)
            except Exception as e:
                logger.error(f"❌ Error en handler de mensajes: {e}")
                self.stats.errors += 1
        
        logger.info("📡 Enterprise event handlers configured")
    
    async def _handle_new_message_enterprise(self, event):
        """
        🎯 HANDLER PRINCIPAL DE MENSAJES ENTERPRISE
        ===========================================
        
        Maneja todos los tipos de mensajes con procesamiento optimizado
        """
        try:
            message = event.message
            chat_id = event.chat_id
            
            # Verificar si el grupo está configurado
            if chat_id not in settings.discord.webhooks:
                return
            
            # Aplicar filtros
            if not await self._should_process_message(message):
                self.stats.messages_filtered += 1
                return
            
            # Actualizar estadísticas
            self.stats.messages_received += 1
            self.stats.last_message_time = datetime.now()
            self.stats.groups_active.add(chat_id)
            
            # Obtener webhook URL
            webhook_url = settings.discord.webhooks[chat_id]
            
            # Procesamiento paralelo con semáforo
            async with self.processing_semaphore:
                # Crear tarea de procesamiento
                task = asyncio.create_task(
                    self._process_message_by_type(chat_id, message, webhook_url)
                )
                self.active_tasks.add(task)
                
                # Cleanup al completar
                task.add_done_callback(self.active_tasks.discard)
                
                # Procesar con timeout
                try:
                    await asyncio.wait_for(task, timeout=self.config.processing_timeout)
                    self.stats.messages_replicated += 1
                except asyncio.TimeoutError:
                    logger.warning(f"⏰ Timeout procesando mensaje de {chat_id}")
                    task.cancel()
                    self.stats.errors += 1
            
        except Exception as e:
            logger.error(f"❌ Error en handle_new_message_enterprise: {e}")
            self.stats.errors += 1
    
    async def _process_message_by_type(self, chat_id: int, message, webhook_url: str):
        """
        🎭 PROCESAMIENTO POR TIPO DE MENSAJE
        ====================================
        
        Rutea cada tipo de mensaje al procesador especializado
        """
        try:
            # Obtener información del chat
            chat_info = await self._get_chat_info(chat_id)
            
            # Procesar según tipo de media
            if message.photo:
                await self._process_image_enterprise(chat_id, message, webhook_url, chat_info)
            
            elif message.video:
                await self._process_video_enterprise(chat_id, message, webhook_url, chat_info)
            
            elif message.document:
                await self._process_document_enterprise(chat_id, message, webhook_url, chat_info)
            
            elif message.audio or message.voice:
                await self._process_audio_enterprise(chat_id, message, webhook_url, chat_info)
            
            elif message.text:
                await self._process_text_enterprise(chat_id, message, webhook_url, chat_info)
            
            else:
                await self._process_other_multimedia(chat_id, message, webhook_url, chat_info)
                
        except Exception as e:
            logger.error(f"❌ Error procesando mensaje tipo: {e}")
            await self._send_error_notification(webhook_url, str(e))
            raise
    
    async def _process_image_enterprise(self, chat_id: int, message, webhook_url: str, chat_info: Dict):
        """
        🖼️ PROCESAMIENTO ENTERPRISE DE IMÁGENES
        =======================================
        
        ✅ Descarga directa en memoria
        ✅ Aplicación de watermarks
        ✅ Envío directo sin almacenamiento temporal
        """
        try:
            logger.info(f"🖼️ Processing enterprise image for group {chat_id}")
            
            # Descargar imagen directamente en memoria
            image_bytes = await asyncio.wait_for(
                message.download_media(bytes),
                timeout=60
            )
            
            if not image_bytes:
                raise Exception("Failed to download image")
            
            # Aplicar watermarks enterprise si está habilitado
            if self.config.enable_watermarks and self.watermark_service:
                try:
                    processed_bytes, was_processed = await self.watermark_service.apply_image_watermark(
                        image_bytes, chat_id
                    )
                    if was_processed:
                        image_bytes = processed_bytes
                        self.stats.watermarks_applied += 1
                except Exception as e:
                    logger.warning(f"⚠️ Watermark failed, using original: {e}")
            
            # Procesar caption
            caption = await self._process_caption(message.text or "", chat_id, chat_info)
            
            # ✅ ENVÍO DIRECTO SIN LOCALHOST/ENLACES
            result = await self.discord_sender.send_image_message(
                webhook_url, image_bytes, caption, "image_enterprise.jpg"
            )
            
            if result.success:
                self.stats.images_processed += 1
                self.stats.total_bytes_processed += len(image_bytes)
                logger.info(f"✅ Enterprise image sent: {len(image_bytes)} bytes")
            else:
                await self._handle_send_failure(webhook_url, "image", result.error_message)
            
        except asyncio.TimeoutError:
            await self._send_timeout_message(webhook_url, "image")
        except Exception as e:
            logger.error(f"❌ Enterprise image processing error: {e}")
            await self._send_error_notification(webhook_url, f"Image processing error: {str(e)}")
            raise
    
    async def _process_video_enterprise(self, chat_id: int, message, webhook_url: str, chat_info: Dict):
        """
        🎬 PROCESAMIENTO ENTERPRISE DE VIDEOS
        ====================================
        
        ✅ Descarga directa en memoria
        ✅ Compresión inteligente si es necesario
        ✅ Watermarks de video
        ✅ Envío directo optimizado
        """
        try:
            logger.info(f"🎬 Processing enterprise video for group {chat_id}")
            
            # Verificar tamaño antes de descargar
            video_size = getattr(message.video, 'size', 0) or getattr(message.document, 'size', 0)
            if video_size > self.config.max_file_size_mb * 1024 * 1024:
                caption = await self._process_caption(message.text or "", chat_id, chat_info)
                warning_msg = f"🎬 Video from **{chat_info['name']}** is too large ({video_size/(1024*1024):.1f}MB)\n\n{caption}"
                await self.discord_sender.send_text_message(webhook_url, warning_msg)
                return
            
            # Descargar video directamente en memoria
            video_bytes = await asyncio.wait_for(
                message.download_media(bytes),
                timeout=self.config.processing_timeout
            )
            
            if not video_bytes:
                raise Exception("Failed to download video")
            
            # Procesar con File Processor si está disponible
            if self.config.enable_compression and self.file_processor:
                try:
                    result = await self.file_processor.process_video(
                        video_bytes, chat_id, "video_enterprise.mp4"
                    )
                    if result["success"] and result.get("processed_bytes"):
                        video_bytes = result["processed_bytes"]
                        self.stats.watermarks_applied += 1
                except Exception as e:
                    logger.warning(f"⚠️ Video processing failed, using original: {e}")
            
            # Procesar caption
            caption = await self._process_caption(message.text or "", chat_id, chat_info)
            
            # ✅ ENVÍO DIRECTO DE VIDEO SIN LOCALHOST/ENLACES  
            result = await self.discord_sender.send_video_message(
                webhook_url, video_bytes, caption, "video_enterprise.mp4"
            )
            
            if result.success:
                self.stats.videos_processed += 1
                self.stats.total_bytes_processed += len(video_bytes)
                logger.info(f"✅ Enterprise video sent: {len(video_bytes)} bytes")
            else:
                await self._handle_send_failure(webhook_url, "video", result.error_message)
            
        except asyncio.TimeoutError:
            await self._send_timeout_message(webhook_url, "video")
        except Exception as e:
            logger.error(f"❌ Enterprise video processing error: {e}")
            await self._send_error_notification(webhook_url, f"Video processing error: {str(e)}")
            raise
    
    async def _process_document_enterprise(self, chat_id: int, message, webhook_url: str, chat_info: Dict):
        """
        📄 PROCESAMIENTO ENTERPRISE DE DOCUMENTOS
        =========================================
        
        ✅ Soporte para PDFs, documentos, archivos
        ✅ Preview generation para PDFs
        ✅ Envío directo sin storage temporal
        """
        try:
            document = message.document
            filename = getattr(document, 'file_name', 'unknown_document')
            file_size = getattr(document, 'size', 0)
            mime_type = getattr(document, 'mime_type', '')
            
            logger.info(f"📄 Processing enterprise document: {filename}")
            
            # Verificar si es un video disfrazado
            if mime_type and mime_type.startswith('video/'):
                return await self._process_video_enterprise(chat_id, message, webhook_url, chat_info)
            
            # Verificar tamaño
            if file_size > self.config.max_file_size_mb * 1024 * 1024:
                caption = await self._process_caption(message.text or "", chat_id, chat_info)
                warning_msg = f"📎 Document from **{chat_info['name']}**: {filename} ({file_size/(1024*1024):.1f}MB) - Too large for direct upload\n\n{caption}"
                await self.discord_sender.send_text_message(webhook_url, warning_msg)
                return
            
            # Descargar documento
            doc_bytes = await asyncio.wait_for(
                message.download_media(bytes),
                timeout=120
            )
            
            if not doc_bytes:
                raise Exception("Failed to download document")
            
            # Procesamiento especializado para PDFs
            if filename.lower().endswith('.pdf') and self.file_processor:
                await self._handle_pdf_enterprise(chat_id, doc_bytes, message.text or "", webhook_url, filename, chat_info)
            else:
                # Otros documentos - envío directo
                caption = await self._process_caption(message.text or "", chat_id, chat_info)
                full_caption = f"📎 Document from **{chat_info['name']}**: {filename}\n\n{caption}"
                
                # ✅ ENVÍO DIRECTO DE DOCUMENTO
                result = await self.discord_sender.send_file_message(
                    webhook_url, doc_bytes, filename, full_caption
                )
                
                if result.success:
                    self.stats.total_bytes_processed += len(doc_bytes)
                    logger.info(f"✅ Enterprise document sent: {filename}")
                else:
                    await self._handle_send_failure(webhook_url, f"document {filename}", result.error_message)
            
        except asyncio.TimeoutError:
            await self._send_timeout_message(webhook_url, "document")
        except Exception as e:
            logger.error(f"❌ Enterprise document processing error: {e}")
            await self._send_error_notification(webhook_url, f"Document processing error: {str(e)}")
            raise
    
    async def _handle_pdf_enterprise(self, chat_id: int, pdf_bytes: bytes, caption: str, 
                                   webhook_url: str, filename: str, chat_info: Dict):
        """Manejo especializado de PDFs enterprise"""
        try:
            # Procesar PDF con File Processor si está disponible
            if self.file_processor:
                result = await self.file_processor.process_pdf(pdf_bytes, chat_id, filename)
                
                if result["success"]:
                    processed_caption = await self._process_caption(caption, chat_id, chat_info)
                    message_text = self._build_pdf_message(processed_caption, result, filename, chat_info)
                    
                    # Enviar con preview si está disponible
                    if result.get("preview_bytes") and self.config.enable_preview_generation:
                        preview_result = await self.discord_sender.send_image_message(
                            webhook_url, result["preview_bytes"], message_text, "pdf_preview.jpg"
                        )
                        success = preview_result.success
                    else:
                        text_result = await self.discord_sender.send_text_message(webhook_url, message_text)
                        success = text_result.success
                    
                    if success:
                        self.stats.pdfs_processed += 1
                        logger.info(f"📄 Enterprise PDF processed: {filename}")
                    else:
                        await self._handle_send_failure(webhook_url, f"PDF {filename}")
                else:
                    await self._send_processing_error(webhook_url, "PDF", filename, result.get("error"))
            else:
                # Fallback sin File Processor
                processed_caption = await self._process_caption(caption, chat_id, chat_info)
                fallback_msg = f"📄 PDF from **{chat_info['name']}**: {filename}\n\n{processed_caption}"
                await self.discord_sender.send_text_message(webhook_url, fallback_msg)
                
        except Exception as e:
            logger.error(f"❌ Enterprise PDF handling error: {e}")
            await self._send_processing_error(webhook_url, "PDF", filename, str(e))
    
    async def _process_audio_enterprise(self, chat_id: int, message, webhook_url: str, chat_info: Dict):
        """
        🎵 PROCESAMIENTO ENTERPRISE DE AUDIO
        ===================================
        
        ✅ Soporte para audio y voice messages
        ✅ Envío directo sin conversión
        """
        try:
            is_voice = bool(message.voice)
            audio_type = "voice note" if is_voice else "audio"
            
            # Obtener información del archivo
            media = message.voice or message.audio or message.document
            duration = getattr(media, 'duration', 0)
            file_size = getattr(media, 'size', 0)
            
            logger.info(f"🎵 Processing enterprise {audio_type} for group {chat_id}")
            
            # Verificar tamaño
            if file_size > self.config.max_file_size_mb * 1024 * 1024:
                caption = await self._process_caption(message.text or "", chat_id, chat_info)
                warning_msg = f"🎵 {audio_type.title()} from **{chat_info['name']}** is too large ({file_size/(1024*1024):.1f}MB)\n\n{caption}"
                await self.discord_sender.send_text_message(webhook_url, warning_msg)
                return
            
            # Descargar audio
            audio_bytes = await asyncio.wait_for(
                message.download_media(bytes),
                timeout=90
            )
            
            if not audio_bytes:
                raise Exception("Failed to download audio")
            
            # Procesar caption
            caption = await self._process_caption(message.text or "", chat_id, chat_info)
            duration_text = f" ({duration}s)" if duration else ""
            full_caption = f"🎵 {audio_type.title()} from **{chat_info['name']}**{duration_text}\n\n{caption}"
            
            # Determinar extensión
            filename = f"{audio_type.replace(' ', '_')}_enterprise"
            if is_voice:
                filename += ".ogg"
            else:
                filename += ".mp3"
            
            # ✅ ENVÍO DIRECTO DE AUDIO SIN LOCALHOST/ENLACES
            result = await self.discord_sender.send_audio_message(
                webhook_url, audio_bytes, full_caption, filename
            )
            
            if result.success:
                self.stats.audios_processed += 1
                self.stats.total_bytes_processed += len(audio_bytes)
                logger.info(f"✅ Enterprise {audio_type} sent: {len(audio_bytes)} bytes")
            else:
                await self._handle_send_failure(webhook_url, audio_type, result.error_message)
            
        except asyncio.TimeoutError:
            await self._send_timeout_message(webhook_url, "audio")
        except Exception as e:
            logger.error(f"❌ Enterprise audio processing error: {e}")
            await self._send_error_notification(webhook_url, f"Audio processing error: {str(e)}")
            raise
    
    async def _process_text_enterprise(self, chat_id: int, message, webhook_url: str, chat_info: Dict):
        """Procesamiento de mensajes de texto enterprise"""
        try:
            text = message.text
            if not text or not text.strip():
                return
            
            # Aplicar watermarks de texto si está habilitado
            if self.config.enable_watermarks and self.watermark_service:
                try:
                    processed_text, was_processed = await self.watermark_service.process_text(text, chat_id)
                    if was_processed:
                        text = processed_text
                        self.stats.watermarks_applied += 1
                except Exception as e:
                    logger.warning(f"⚠️ Text watermark failed: {e}")
            
            # Añadir información del canal
            full_message = f"💬 **{chat_info['name']}**\n\n{text}"
            
            # Enviar mensaje de texto
            result = await self.discord_sender.send_text_message(webhook_url, full_message)
            
            if not result.success:
                await self._handle_send_failure(webhook_url, "text", result.error_message)
                
        except Exception as e:
            logger.error(f"❌ Text processing error: {e}")
            await self._send_error_notification(webhook_url, f"Text processing error: {str(e)}")
    
    async def _process_other_multimedia(self, chat_id: int, message, webhook_url: str, chat_info: Dict):
        """Procesamiento de otros tipos de multimedia"""
        try:
            content_type = "multimedia content"
            
            if message.sticker:
                content_type = "sticker"
            elif message.gif:
                content_type = "GIF"
            elif message.contact:
                content_type = "contact"
            elif message.location:
                content_type = "location"
            
            caption = await self._process_caption(message.text or "", chat_id, chat_info)
            full_message = f"📎 **{chat_info['name']}** shared {content_type}\n\n{caption}"
            
            result = await self.discord_sender.send_text_message(webhook_url, full_message)
            
            if not result.success:
                await self._handle_send_failure(webhook_url, content_type, result.error_message)
                
        except Exception as e:
            logger.error(f"❌ Other multimedia processing error: {e}")
    
    # ================ MÉTODOS DE UTILIDAD ENTERPRISE ================
    
    async def _process_caption(self, caption: str, chat_id: int, chat_info: Dict) -> str:
        """Procesar caption con watermarks enterprise"""
        if not caption:
            return ""
            
        if self.config.enable_watermarks and self.watermark_service:
            try:
                processed_caption, _ = await self.watermark_service.process_text(caption, chat_id)
                return processed_caption
            except Exception as e:
                logger.warning(f"⚠️ Caption watermark failed: {e}")
        
        return caption
    
    def _build_pdf_message(self, caption: str, result: dict, filename: str, chat_info: Dict) -> str:
        """Construir mensaje enterprise para PDFs"""
        message_parts = [
            f"📄 **PDF from {chat_info['name']}**",
            f"📄 File: {filename}",
            f"💾 Size: {result.get('size_mb', 0):.1f} MB"
        ]
        
        if result.get('page_count'):
            message_parts.append(f"📃 Pages: {result['page_count']}")
        
        if caption:
            message_parts.extend(["", caption])
        
        if result.get('download_url'):
            message_parts.extend([
                "",
                f"🔗 [📥 Download PDF]({result['download_url']})",
                "⏰ Available for 24 hours"
            ])
        
        return "\n".join(message_parts)
    
    async def _get_chat_info(self, chat_id: int) -> Dict[str, Any]:
        """Obtener información del chat enterprise"""
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
                'id': chat_id
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Could not get info for {chat_id}: {e}")
            return {
                'name': f"Chat {chat_id}",
                'type': 'Unknown',
                'id': chat_id
            }
    
    async def _should_process_message(self, message) -> bool:
        """Aplicar filtros enterprise al mensaje"""
        if not self.filters['enabled']:
            return True
        
        # Filtro por usuario
        user_id = getattr(message.sender, 'id', None)
        if user_id in self.filters['skip_users']:
            return False
        
        text = message.text
        if text:
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
    
    async def _handle_send_failure(self, webhook_url: str, content_type: str, error_msg: str = ""):
        """Manejar fallos de envío enterprise"""
        self.stats.errors += 1
        logger.warning(f"⚠️ Send failure for {content_type} to {webhook_url[:50]}...")
        
        # Implementar fallback strategies aquí si es necesario
        
    async def _send_timeout_message(self, webhook_url: str, content_type: str):
        """Enviar mensaje de timeout"""
        timeout_msg = f"⏰ {content_type.title()} processing timed out after {self.config.processing_timeout}s"
        try:
            await self.discord_sender.send_text_message(webhook_url, timeout_msg)
        except Exception as e:
            logger.error(f"❌ Error sending timeout message: {e}")
    
    async def _send_error_notification(self, webhook_url: str, error_msg: str):
        """Enviar notificación de error"""
        error_notification = f"❌ Processing error: {error_msg[:500]}"
        try:
            await self.discord_sender.send_text_message(webhook_url, error_notification)
        except Exception as e:
            logger.error(f"❌ Error sending error notification: {e}")
    
    async def _send_processing_error(self, webhook_url: str, file_type: str, filename: str, error: str):
        """Enviar mensaje de error de procesamiento"""
        error_msg = f"❌ Failed to process {file_type}: {filename}\nError: {error[:200]}"
        try:
            await self.discord_sender.send_text_message(webhook_url, error_msg)
        except Exception as e:
            logger.error(f"❌ Error sending processing error: {e}")
    
    async def _validate_configuration(self) -> Dict[str, Any]:
        """Validar configuración enterprise completa"""
        errors = []
        warnings = []
        
        # Verificar Telegram
        if not settings.telegram.api_id:
            errors.append("TELEGRAM_API_ID not configured")
        if not settings.telegram.api_hash:
            errors.append("TELEGRAM_API_HASH not configured")
        if not settings.telegram.phone:
            errors.append("TELEGRAM_PHONE not configured")
        
        # Verificar Discord webhooks
        if not settings.discord.webhooks:
            errors.append("No Discord webhooks configured")
        else:
            for group_id, webhook in settings.discord.webhooks.items():
                if not webhook.startswith('https://discord.com/api/webhooks/'):
                    warnings.append(f"Invalid webhook format for group {group_id}")
        
        # Verificar microservicios
        if not self.discord_sender:
            warnings.append("Discord Sender service not available")
        if not self.file_processor:
            warnings.append("File Processor service not available")
        if not self.watermark_service:
            warnings.append("Watermark service not available")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    async def _display_enterprise_configuration(self):
        """Mostrar configuración enterprise"""
        logger.info("📊 Enterprise Configuration:")
        logger.info(f"   Groups configured: {len(settings.discord.webhooks)}")
        logger.info(f"   Max concurrent processing: {self.config.max_concurrent_processing}")
        logger.info(f"   Circuit breaker threshold: {self.config.circuit_breaker_threshold}")
        logger.info(f"   Processing timeout: {self.config.processing_timeout}s")
        logger.info(f"   Max file size: {self.config.max_file_size_mb}MB")
        logger.info("   Enterprise Services:")
        logger.info(f"     - File Processor: {'✅ Advanced' if self.file_processor else '❌ Unavailable'}")
        logger.info(f"     - Watermark Service: {'✅ Multi-tenant' if self.watermark_service else '❌ Unavailable'}")
        logger.info(f"     - Discord Sender: {'✅ Circuit breaker enabled' if self.discord_sender else '❌ Unavailable'}")
        logger.info("   Features:")
        logger.info(f"     - Watermarks: {'✅' if self.config.enable_watermarks else '❌'}")
        logger.info(f"     - Compression: {'✅' if self.config.enable_compression else '❌'}")
        logger.info(f"     - Preview Generation: {'✅' if self.config.enable_preview_generation else '❌'}")
        logger.info(f"     - Filters: {'✅' if self.config.filters_enabled else '❌'}")
    
    # ================ CONTROL DEL SERVICIO ================
    
    async def start_listening(self):
        """
        👂 INICIAR ESCUCHA ENTERPRISE
        ============================
        
        Inicia la escucha de mensajes de Telegram con configuración enterprise
        """
        if not self.initialization_complete:
            logger.error("❌ Service not initialized")
            return False
        
        if not self.telegram_client:
            logger.error("❌ Telegram client not available")
            return False
        
        try:
            self.is_listening = True
            logger.info("👂 Starting enterprise message listening...")
            
            # Mostrar grupos monitoreados
            for group_id in settings.discord.webhooks.keys():
                logger.info(f"   👥 Monitoring enterprise group: {group_id}")
            
            # Iniciar el cliente de Telegram (bucle principal)
            await self.telegram_client.run_until_disconnected()
            
        except Exception as e:
            logger.error(f"❌ Error in listening: {e}")
            self.is_listening = False
            return False
        finally:
            self.is_listening = False
            logger.info("🛑 Enterprise listening stopped")
    
    async def stop(self):
        """Detener servicio enterprise"""
        try:
            logger.info("🛑 Stopping Enhanced Replicator Service Enterprise...")
            
            self.is_running = False
            self.is_listening = False
            
            # Cancelar tareas activas
            if self.active_tasks:
                logger.info(f"🔄 Cancelling {len(self.active_tasks)} active tasks...")
                for task in self.active_tasks.copy():
                    task.cancel()
                
                # Esperar a que se cancelen
                if self.active_tasks:
                    await asyncio.gather(*self.active_tasks, return_exceptions=True)
            
            # Cerrar microservicios
            if self.discord_sender:
                await self.discord_sender.close()
                logger.info("📤 Discord sender closed")
            
            if self.file_processor and hasattr(self.file_processor, 'close'):
                await self.file_processor.close()
                logger.info("📁 File processor closed")
            
            if self.watermark_service and hasattr(self.watermark_service, 'close'):
                await self.watermark_service.close()
                logger.info("🎨 Watermark service closed")
            
            # Desconectar Telegram
            if self.telegram_client and self.telegram_client.is_connected():
                await self.telegram_client.disconnect()
                logger.info("📱 Telegram client disconnected")
            
            logger.info("✅ Enhanced Replicator Service Enterprise stopped")
            
        except Exception as e:
            logger.error(f"❌ Error stopping service: {e}")
    
    # ================ MÉTODOS DE API ENTERPRISE ================
    
    async def get_health(self) -> Dict[str, Any]:
        """Health check enterprise completo"""
        try:
            telegram_connected = (
                self.telegram_client and 
                self.telegram_client.is_connected() if self.telegram_client else False
            )
            
            discord_health = None
            if self.discord_sender:
                discord_health = await self.discord_sender.get_health()
            
            return {
                'status': 'healthy' if (self.is_running and telegram_connected) else 'unhealthy',
                'service_version': '4.0 Enterprise',
                'initialization_complete': self.initialization_complete,
                'is_running': self.is_running,
                'is_listening': self.is_listening,
                'telegram': {
                    'connected': telegram_connected,
                    'client_available': self.telegram_client is not None
                },
                'discord': discord_health or {'status': 'unavailable'},
                'microservices': {
                    'file_processor': self.file_processor is not None,
                    'watermark_service': self.watermark_service is not None,
                    'discord_sender': self.discord_sender is not None
                },
                'configuration': {
                    'groups_configured': len(settings.discord.webhooks),
                    'max_concurrent': self.config.max_concurrent_processing,
                    'features': {
                        'watermarks': self.config.enable_watermarks,
                        'compression': self.config.enable_compression,
                        'preview_generation': self.config.enable_preview_generation,
                        'filters': self.config.filters_enabled
                    }
                },
                'active_tasks': len(self.active_tasks),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas enterprise completas"""
        uptime = (datetime.now() - self.stats.start_time).total_seconds()
        
        # Calcular tasas
        messages_per_hour = 0
        if uptime > 0:
            messages_per_hour = (self.stats.messages_received / uptime) * 3600
        
        success_rate = 0
        if self.stats.messages_received > 0:
            success_rate = (self.stats.messages_replicated / self.stats.messages_received) * 100
        
        stats_dict = {
            'processing_stats': {
                'messages_received': self.stats.messages_received,
                'messages_replicated': self.stats.messages_replicated,
                'messages_filtered': self.stats.messages_filtered,
                'images_processed': self.stats.images_processed,
                'videos_processed': self.stats.videos_processed,
                'audios_processed': self.stats.audios_processed,
                'pdfs_processed': self.stats.pdfs_processed,
                'watermarks_applied': self.stats.watermarks_applied,
                'errors': self.stats.errors,
                'total_bytes_processed': self.stats.total_bytes_processed,
                'total_mb_processed': round(self.stats.total_bytes_processed / (1024 * 1024), 2)
            },
            'performance_metrics': {
                'uptime_seconds': uptime,
                'uptime_hours': round(uptime / 3600, 2),
                'messages_per_hour': round(messages_per_hour, 2),
                'success_rate_percent': round(success_rate, 2),
                'active_tasks': len(self.active_tasks),
                'groups_active': len(self.stats.groups_active),
                'last_message_time': (
                    self.stats.last_message_time.isoformat() 
                    if self.stats.last_message_time else None
                )
            },
            'service_info': {
                'is_running': self.is_running,
                'is_listening': self.is_listening,
                'initialization_complete': self.initialization_complete,
                'version': '4.0 Enterprise',
                'start_time': self.stats.start_time.isoformat()
            },
            'configuration': {
                'groups_configured': len(settings.discord.webhooks),
                'groups_active_list': list(self.stats.groups_active),
                'max_concurrent_processing': self.config.max_concurrent_processing,
                'processing_timeout': self.config.processing_timeout,
                'max_file_size_mb': self.config.max_file_size_mb,
                'features_enabled': {
                    'watermarks': self.config.enable_watermarks,
                    'compression': self.config.enable_compression,
                    'preview_generation': self.config.enable_preview_generation,
                    'filters': self.config.filters_enabled
                }
            }
        }
        
        # Añadir estadísticas de Discord Sender si está disponible
        if self.discord_sender:
            discord_stats = self.discord_sender.get_stats()
            stats_dict['discord_sender_stats'] = discord_stats
        
        return stats_dict
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Estadísticas optimizadas para dashboard"""
        uptime = (datetime.now() - self.stats.start_time).total_seconds()
        
        return {
            'total_messages': self.stats.messages_received,
            'replicated_messages': self.stats.messages_replicated,
            'filtered_messages': self.stats.messages_filtered,
            'images_processed': self.stats.images_processed,
            'videos_processed': self.stats.videos_processed,
            'audios_processed': self.stats.audios_processed,
            'pdfs_processed': self.stats.pdfs_processed,
            'watermarks_applied': self.stats.watermarks_applied,
            'errors': self.stats.errors,
            'uptime_seconds': uptime,
            'uptime_hours': round(uptime / 3600, 2),
            'groups_configured': len(settings.discord.webhooks),
            'groups_active': len(self.stats.groups_active),
            'is_running': self.is_running,
            'is_listening': self.is_listening,
            'last_message': (
                self.stats.last_message_time.isoformat() 
                if self.stats.last_message_time else None
            ),
            'success_rate': (
                (self.stats.messages_replicated / 
                 max(self.stats.messages_received, 1)) * 100
            ),
            'total_mb_processed': round(self.stats.total_bytes_processed / (1024 * 1024), 2),
            'active_tasks': len(self.active_tasks)
        }
    
    def update_filters(self, new_filters: Dict[str, Any]):
        """Actualizar filtros enterprise en tiempo real"""
        try:
            if 'enabled' in new_filters:
                self.filters['enabled'] = bool(new_filters['enabled'])
            if 'min_length' in new_filters:
                self.filters['min_length'] = max(0, int(new_filters['min_length']))
            if 'skip_words' in new_filters:
                self.filters['skip_words'] = [word.strip().lower() for word in new_filters['skip_words'] if word.strip()]
            if 'only_words' in new_filters:
                self.filters['only_words'] = [word.strip().lower() for word in new_filters['only_words'] if word.strip()]
            if 'skip_users' in new_filters:
                self.filters['skip_users'] = set(new_filters['skip_users'])
            
            logger.info("✅ Filters updated successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Error updating filters: {e}")
            return False
    
    def update_config(self, new_config: Dict[str, Any]):
        """Actualizar configuración enterprise en tiempo real"""
        try:
            if 'max_concurrent_processing' in new_config:
                self.config.max_concurrent_processing = max(1, int(new_config['max_concurrent_processing']))
                self.processing_semaphore = asyncio.Semaphore(self.config.max_concurrent_processing)
            
            if 'processing_timeout' in new_config:
                self.config.processing_timeout = max(30, int(new_config['processing_timeout']))
            
            if 'max_file_size_mb' in new_config:
                self.config.max_file_size_mb = max(1, int(new_config['max_file_size_mb']))
            
            if 'enable_watermarks' in new_config:
                self.config.enable_watermarks = bool(new_config['enable_watermarks'])
            
            if 'enable_compression' in new_config:
                self.config.enable_compression = bool(new_config['enable_compression'])
            
            if 'enable_preview_generation' in new_config:
                self.config.enable_preview_generation = bool(new_config['enable_preview_generation'])
            
            logger.info("✅ Configuration updated successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Error updating configuration: {e}")
            return False


# ============ COMPATIBILIDAD CON TU CÓDIGO EXISTENTE ============

# Para mantener total compatibilidad con tu main.py
EnhancedReplicatorService = EnhancedReplicatorServiceEnterprise

# También mantener el patrón original si lo usas
class ReplicatorService(EnhancedReplicatorServiceEnterprise):
    """Alias de compatibilidad"""
    pass

        # ================ MÉTODOS DE MONITOREO ENTERPRISE ================
    
    async def _monitor_performance(self):
        """Monitor de performance en tiempo real"""
        while self.is_running:
            try:
                # Calcular métricas de performance
                current_time = datetime.now()
                uptime = (current_time - self.stats.start_time).total_seconds()
                
                # Rate de procesamiento
                if uptime > 0:
                    messages_per_hour = (self.stats.messages_received / uptime) * 3600
                    
                    # Log performance metrics cada 5 minutos
                    if int(uptime) % 300 == 0:  # Cada 5 minutos
                        logger.info(f"📊 Performance: {messages_per_hour:.1f} msg/hour, "
                                  f"{len(self.active_tasks)} active tasks, "
                                  f"{self.stats.errors} errors")
                
                # Verificar thresholds de alarma
                error_rate = 0
                if self.stats.messages_received > 0:
                    error_rate = (self.stats.errors / self.stats.messages_received) * 100
                
                if error_rate > 5.0:  # 5% error rate threshold
                    logger.warning(f"⚠️ High error rate: {error_rate:.2f}%")
                
                # Monitor memory usage (simplified)
                if len(self.active_tasks) > self.config.max_concurrent_processing * 0.8:
                    logger.warning(f"⚠️ High task load: {len(self.active_tasks)}/{self.config.max_concurrent_processing}")
                
                await asyncio.sleep(30)  # Monitor cada 30 segundos
                
            except Exception as e:
                logger.error(f"❌ Performance monitoring error: {e}")
                await asyncio.sleep(60)  # Retry after 1 minute
    
    def _calculate_success_rate(self) -> float:
        """Calcular tasa de éxito"""
        if self.stats.messages_received == 0:
            return 100.0
        return (self.stats.messages_replicated / self.stats.messages_received) * 100
    
    def _calculate_throughput(self) -> float:
        """Calcular throughput en mensajes por minuto"""
        uptime = (datetime.now() - self.stats.start_time).total_seconds()
        if uptime == 0:
            return 0.0
        return (self.stats.messages_received / uptime) * 60
    
    async def _health_check_background(self):
        """Background health check cada 30 segundos"""
        while self.is_running:
            try:
                health = await self.get_health()
                
                # Log si hay problemas
                if health['status'] != 'healthy':
                    logger.warning(f"⚠️ Health check warning: {health}")
                
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"❌ Background health check error: {e}")
                await asyncio.sleep(60)
    
    async def _cleanup_background(self):
        """Background cleanup cada hora"""
        while self.is_running:
            try:
                # Cleanup completed tasks
                completed_tasks = [task for task in self.active_tasks if task.done()]
                for task in completed_tasks:
                    self.active_tasks.discard(task)
                
                # Cleanup temp files si existen
                temp_dirs = [Path("temp"), Path("temp_files")]
                for temp_dir in temp_dirs:
                    if temp_dir.exists():
                        for file_path in temp_dir.glob("*"):
                            if file_path.is_file():
                                # Delete files older than 1 hour
                                file_age = datetime.now().timestamp() - file_path.stat().st_mtime
                                if file_age > 3600:  # 1 hour
                                    try:
                                        file_path.unlink()
                                    except Exception:
                                        pass
                
                await asyncio.sleep(3600)  # Cleanup cada hora
                
            except Exception as e:
                logger.error(f"❌ Background cleanup error: {e}")
                await asyncio.sleep(3600)
    
    # ================ MÉTODOS DE EXPORTACIÓN ================
    
    def export_configuration(self) -> Dict[str, Any]:
        """Exportar configuración completa (sin secretos)"""
        return {
            'service_version': '4.0 Enterprise',
            'export_timestamp': datetime.now().isoformat(),
            'configuration': {
                'max_concurrent_processing': self.config.max_concurrent_processing,
                'processing_timeout': self.config.processing_timeout,
                'max_file_size_mb': self.config.max_file_size_mb,
                'circuit_breaker_threshold': self.config.circuit_breaker_threshold,
                'features': {
                    'watermarks': self.config.enable_watermarks,
                    'compression': self.config.enable_compression,
                    'preview_generation': self.config.enable_preview_generation,
                    'filters': self.config.filters_enabled
                }
            },
            'filters': {
                'enabled': self.filters['enabled'],
                'min_length': self.filters['min_length'],
                'skip_words_count': len(self.filters['skip_words']),
                'only_words_count': len(self.filters['only_words']),
                'skip_users_count': len(self.filters['skip_users'])
            },
            'groups_configured': len(settings.discord.webhooks)
        }
    
    def export_stats_detailed(self) -> Dict[str, Any]:
        """Exportar estadísticas detalladas para análisis"""
        stats = self.get_stats()
        
        # Añadir información adicional para análisis
        stats['export_info'] = {
            'export_timestamp': datetime.now().isoformat(),
            'service_version': '4.0 Enterprise',
            'export_type': 'detailed_stats'
        }
        
        # Añadir métricas calculadas
        stats['calculated_metrics'] = {
            'success_rate': self._calculate_success_rate(),
            'throughput_per_minute': self._calculate_throughput(),
            'average_processing_time': 0.0,  # Placeholder
            'error_rate': (self.stats.errors / max(self.stats.messages_received, 1)) * 100
        }
        
        return stats

# ============ FACTORY FUNCTIONS ============

def create_enhanced_replicator_service() -> EnhancedReplicatorServiceEnterprise:
    """Factory function para crear instancia del servicio"""
    return EnhancedReplicatorServiceEnterprise()

# ============ COMPATIBILIDAD CON CÓDIGO EXISTENTE ============

# Para mantener total compatibilidad con tu main.py
EnhancedReplicatorService = EnhancedReplicatorServiceEnterprise

# También mantener el patrón original si lo usas
class ReplicatorService(EnhancedReplicatorServiceEnterprise):
    """Alias de compatibilidad para código legacy"""
    pass

# ============ CONFIGURACIÓN DE LOGGING ESPECÍFICA ============

# Configurar logger específico para este módulo
_module_logger = setup_logger(__name__)

# ============ INICIALIZACIÓN DEL MÓDULO ============

def _module_initialization():
    """Inicialización del módulo al importar"""
    try:
        _module_logger.info("📦 Enhanced Replicator Service module loaded")
        _module_logger.info(f"📊 Available classes: {[cls.__name__ for cls in [EnhancedReplicatorServiceEnterprise, ReplicatorService]]}")
    except Exception as e:
        print(f"Warning: Module initialization failed: {e}")

# Ejecutar inicialización
_module_initialization()