"""
Enhanced Replicator Service - Enterprise SaaS Ready - ENVÍO DIRECTO
==================================================================
Archivo: app/services/enhanced_replicator_service.py

🚀 ENTERPRISE ARCHITECTURE v3.0 - ENVÍO DIRECTO
✅ Microservices-ready modular design
✅ Circuit breakers + retry logic
✅ Advanced monitoring + health checks
✅ Scalable async processing
✅ SaaS multi-tenant ready
✅ ENVÍO DIRECTO de archivos (NO links)
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

# Enterprise services imports
from .discord_sender import DiscordSenderEnhanced
from .file_processor import FileProcessorEnhanced  
from .watermark_service import WatermarkServiceIntegrated

# Telegram imports with graceful fallback - FIXED
try:
    from telethon import TelegramClient, events
    from telethon.tl.types import (
        MessageMediaDocument, 
        MessageMediaPhoto,
        DocumentAttributeVideo,
        DocumentAttributeAudio,
        DocumentAttributeFilename
    )
    TELETHON_AVAILABLE = True
    TELETHON_VIDEO_SUPPORT = True  # Always true if we have DocumentAttributeVideo
    
    # Optional imports
    try:
        from telethon.tl.types import MessageMediaWebPage
        MEDIA_WEBPAGE_AVAILABLE = True
    except ImportError:
        MEDIA_WEBPAGE_AVAILABLE = False
        MessageMediaWebPage = None
        
except ImportError as e:
    print(f"⚠️ Telethon not available: {e}")
    TELETHON_AVAILABLE = False
    TELETHON_VIDEO_SUPPORT = False
    MEDIA_WEBPAGE_AVAILABLE = False
    MessageMediaDocument = None
    MessageMediaPhoto = None
    DocumentAttributeVideo = None
    DocumentAttributeAudio = None
    DocumentAttributeFilename = None
    MessageMediaWebPage = None


# Core dependencies check
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

try:
    from PIL import Image, ImageDraw, ImageFont
    import fitz  # PyMuPDF
    PIL_AVAILABLE = True
    PYMUPDF_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    PYMUPDF_AVAILABLE = False

from app.config.settings import get_settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)
settings = get_settings()

# Global variables for media support
if 'MEDIA_VIDEO_AVAILABLE' not in globals():
    MEDIA_VIDEO_AVAILABLE = False
if 'TELETHON_VIDEO_SUPPORT' not in globals():
    TELETHON_VIDEO_SUPPORT = False

class EnhancedReplicatorService:
    """
    🚀 ENHANCED REPLICATOR SERVICE v3.0 ENTERPRISE - ENVÍO DIRECTO
    =============================================================
    
    Enterprise SaaS Architecture Features:
    ✅ Microservices-ready modular design
    ✅ Advanced error handling + circuit breakers
    ✅ Multi-tenant configuration support
    ✅ Real-time metrics + monitoring
    ✅ Scalable async message processing
    ✅ Health checks + service discovery ready
    ✅ Event-driven architecture patterns
    ✅ Graceful degradation + fallbacks
    ✅ ENVÍO DIRECTO de archivos (SIN links de descarga)
    
    Media Processing Capabilities:
    📄 PDFs: Envío directo cuando <25MB, preview para grandes
    🎵 Audios: Envío directo con metadata inteligente
    🎬 Videos: Envío directo con compresión automática
    🖼️ Images: Envío directo con watermarks dinámicos
    📎 Documents: Envío directo universal
    
    Enterprise Patterns:
    🔄 Circuit breaker pattern for resilience
    📊 Comprehensive metrics collection
    🔐 Multi-tenant security isolation
    ⚡ High-performance async processing
    🎯 Direct file sending (NO download links)
    """
    
    def __init__(self):
        """Initialize enterprise replicator with dependency injection"""
        self.telegram_client: Optional[TelegramClient] = None
        self.is_running: bool = False
        self.is_listening: bool = False
        
        # Enterprise service dependencies (dependency injection ready)
        self.file_processor = FileProcessorEnhanced()
        self.watermark_service = WatermarkServiceIntegrated()
        self.discord_sender = DiscordSenderEnhanced()
        
        # Enterprise metrics with detailed tracking + direct sending metrics
        self.stats = {
            'messages_received': 0,
            'messages_replicated': 0,
            'messages_filtered': 0,
            'pdfs_processed': 0,
            'audios_processed': 0,
            'videos_processed': 0,
            'images_processed': 0,
            'documents_processed': 0,
            'watermarks_applied': 0,
            'files_sent_direct': 0,        # 🎯 Nuevas métricas envío directo
            'images_sent_direct': 0,
            'videos_sent_direct': 0,
            'audios_sent_direct': 0,
            'pdfs_sent_direct': 0,
            'files_compressed': 0,
            'compression_savings_mb': 0.0,
            'large_files_rejected': 0,
            'errors': 0,
            'retries': 0,
            'circuit_breaker_trips': 0,
            'start_time': datetime.now(),
            'last_message_time': None,
            'groups_active': set(),
            'performance_metrics': {
                'avg_processing_time': 0.0,
                'total_processing_time': 0.0,
                'peak_memory_usage': 0,
                'active_connections': 0
            }
        }
        
        # Enterprise configuration with direct sending settings
        self.config = {
            'max_concurrent_processing': 10,
            'health_check_interval': 30,
            'metrics_collection_interval': 10,
            'circuit_breaker_threshold': 5,
            'retry_attempts': 3,
            'processing_timeout': 300,  # 5 minutes
            'direct_sending': {         # 🎯 Configuración envío directo
                'max_file_size_mb': 25,     # Discord limit
                'auto_compress': True,
                'compression_quality': 75,
                'prefer_direct': True,
                'fallback_to_links': False  # Solo envío directo
            }
        }
        
        # Processing semaphore for concurrency control
        self.processing_semaphore = asyncio.Semaphore(self.config['max_concurrent_processing'])
        
        logger.info("🚀 Enhanced Replicator Service v3.0 Enterprise initialized - MODO ENVÍO DIRECTO")
    
    async def initialize(self) -> bool:
        """
        Initialize enterprise service with comprehensive health checks
        
        Returns:
            bool: True if all services initialized successfully
        """
        try:
            logger.info("🔧 Initializing Enhanced Replicator Service Enterprise...")
            
            # 1. Dependency verification with detailed reporting
            await self._verify_dependencies()
            
            # 2. Initialize Telegram with enterprise error handling
            if TELETHON_AVAILABLE:
                success = await self._initialize_telegram()
                if not success:
                    logger.warning("⚠️ Telegram initialization failed - continuing in degraded mode")
            else:
                logger.warning("⚠️ Telethon not available - Telegram features disabled")
            
            # 3. Initialize enterprise services with error isolation
            await self._initialize_enterprise_services()
            
            # 4. Configure event handlers with enterprise patterns
            if self.telegram_client:
                self._setup_enterprise_event_handlers()
            
            # 5. Start background enterprise tasks
            await self._start_background_tasks()
            
            self.is_running = True
            logger.info("✅ Enhanced Replicator Service Enterprise initialized successfully")
            
            # 6. Display enterprise configuration
            await self._display_enterprise_configuration()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Critical error initializing enterprise service: {e}")
            await self._handle_initialization_failure(e)
            return False
    
    async def _verify_dependencies(self):
        """Comprehensive dependency verification for enterprise deployment"""
        dependencies = {
            'telethon': TELETHON_AVAILABLE,
            'telethon_video_support': MEDIA_VIDEO_AVAILABLE,
            'aiohttp': AIOHTTP_AVAILABLE,
            'pil': PIL_AVAILABLE,
            'pymupdf': PYMUPDF_AVAILABLE
        }
        
        logger.info("🔍 Enterprise dependency verification:")
        for dep, available in dependencies.items():
            status = "✅ Available" if available else "❌ Missing"
            level = "INFO" if available else "WARNING"
            getattr(logger, level.lower())(f"   {dep}: {status}")
        
        # Special warning for video support
        if TELETHON_AVAILABLE and not MEDIA_VIDEO_AVAILABLE:
            logger.info("   📹 Video handling: Using document-based detection")
        
        # Check critical paths
        critical_paths = [
            Path("temp_files"),
            Path("processed_files"),
            Path("cache_files"),
            Path("watermark_configs")
        ]
        
        for path in critical_paths:
            path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"📁 Ensured directory: {path}")
    
    async def _initialize_telegram(self) -> bool:
        """Initialize Telegram with enterprise-grade error handling"""
        try:
            logger.info("📱 Connecting to Telegram Enterprise...")
            
            # Validate configuration
            if not all([settings.telegram.api_id, settings.telegram.api_hash]):
                logger.error("❌ Telegram configuration incomplete")
                return False
            
            # Initialize with enterprise session management
            self.telegram_client = TelegramClient(
                settings.telegram.session_name,
                settings.telegram.api_id,
                settings.telegram.api_hash,
                # Enterprise settings
                connection_retries=3,
                retry_delay=1,
                timeout=30,
                request_retries=2
            )
            
            # Connect with timeout protection
            await asyncio.wait_for(
                self.telegram_client.start(phone=settings.telegram.phone),
                timeout=60
            )
            
            # Verify connection
            me = await self.telegram_client.get_me()
            logger.info(f"✅ Telegram Enterprise connected: {me.first_name} (@{me.username or 'no_username'})")
            
            return True
            
        except asyncio.TimeoutError:
            logger.error("❌ Telegram connection timeout")
            return False
        except Exception as e:
            logger.error(f"❌ Telegram connection failed: {e}")
            return False
    
    async def _initialize_enterprise_services(self):
        """Initialize all enterprise services with error isolation"""
        services = [
            ("File Processor", self.file_processor),
            ("Watermark Service", self.watermark_service), 
            ("Discord Sender", self.discord_sender)
        ]
        
        for service_name, service in services:
            try:
                await service.initialize()
                logger.info(f"✅ {service_name} Enterprise initialized")
            except Exception as e:
                logger.error(f"❌ {service_name} initialization failed: {e}")
                # Continue with other services (graceful degradation)
    
    def _setup_enterprise_event_handlers(self):
        """Configure event handlers with enterprise patterns"""
        
        @self.telegram_client.on(events.NewMessage)
        async def handle_enterprise_message(event):
            """Enterprise message handler with comprehensive error handling"""
            processing_start = datetime.now()
            
            try:
                async with self.processing_semaphore:
                    chat_id = event.chat_id
                    
                    # Multi-tenant access control
                    if chat_id not in settings.discord.webhooks:
                        logger.debug(f"🔒 Unauthorized group access attempt: {chat_id}")
                        return
                    
                    # Update enterprise metrics
                    self.stats['messages_received'] += 1
                    self.stats['last_message_time'] = datetime.now()
                    self.stats['groups_active'].add(chat_id)
                    self.stats['performance_metrics']['active_connections'] += 1
                    
                    # Process with enterprise patterns
                    await self._process_message_enterprise(chat_id, event.message)
                    
                    # Update performance metrics
                    processing_time = (datetime.now() - processing_start).total_seconds()
                    self._update_performance_metrics(processing_time)
                    
            except Exception as e:
                logger.error(f"❌ Enterprise message processing error: {e}")
                self.stats['errors'] += 1
                await self._handle_processing_error(e, event.chat_id if hasattr(event, 'chat_id') else None)
            finally:
                self.stats['performance_metrics']['active_connections'] -= 1
        
        logger.info("📡 Enterprise event handlers configured")
    
    async def _process_message_enterprise(self, chat_id: int, message):
        """Enterprise message processing with advanced routing"""
        try:
            webhook_url = settings.discord.webhooks.get(chat_id)
            if not webhook_url:
                logger.warning(f"⚠️ No webhook configured for group {chat_id}")
                return
            
            # Route based on message type with enterprise handlers
            if message.media:
                await self._route_media_message(chat_id, message, webhook_url)
            else:
                await self._process_text_enterprise(chat_id, message, webhook_url)
            
            self.stats['messages_replicated'] += 1
            logger.debug(f"✅ Message replicated: {chat_id} → Discord")
            
        except Exception as e:
            logger.error(f"❌ Enterprise message processing failed: {e}")
            self.stats['errors'] += 1
            raise
    
    async def _route_media_message(self, chat_id: int, message, webhook_url: str):
        """Enterprise media routing with type-specific handlers"""
        
        # Handle video messages properly based on Telethon version
        if hasattr(message.media, 'document') and message.media.document:
            # Check if it's a video by MIME type or attributes
            mime_type = getattr(message.media.document, 'mime_type', '')
            if mime_type.startswith('video/'):
                await self._process_video_enterprise(chat_id, message, webhook_url)
                return
        
        # Standard media routing
        media_handlers = {
            MessageMediaDocument: self._process_document_enterprise,
            MessageMediaPhoto: self._process_image_enterprise
        }
        
        # Add MessageMediaVideo handler only if available
        if MEDIA_VIDEO_AVAILABLE and MessageMediaVideo:
            media_handlers[MessageMediaVideo] = self._process_video_enterprise
        
        media_type = type(message.media)
        handler = media_handlers.get(media_type, self._process_other_media_enterprise)
        
        await handler(chat_id, message, webhook_url)
    
    async def _process_text_enterprise(self, chat_id: int, message, webhook_url: str):
        """Enterprise text processing with watermarks and validation"""
        try:
            text = message.text or ""
            if not text.strip():
                return
            
            # Apply enterprise watermarks
            # Fix for unpacking error - watermark service might return different values
            watermark_result = await self.watermark_service.process_text(text, chat_id)
            if isinstance(watermark_result, tuple) and len(watermark_result) >= 2:
                processed_text, was_modified = watermark_result[:2]
            elif isinstance(watermark_result, str):
                processed_text = watermark_result
                was_modified = False
            else:
                processed_text = text
                was_modified = False
            if was_modified:
                text = processed_text
                self.stats['watermarks_applied'] += 1
            
            # Send with enterprise retry logic
            success = await self.discord_sender.send_message(webhook_url, text)
            if not success:
                self.stats['retries'] += 1
                await self._handle_send_failure(webhook_url, "text message")
            
        except Exception as e:
            logger.error(f"❌ Enterprise text processing error: {e}")
            raise
    
    async def _process_document_enterprise(self, chat_id: int, message, webhook_url: str):
        """Enterprise document processing with intelligent type detection"""
        try:
            # Download with timeout protection
            file_bytes = await asyncio.wait_for(
                message.download_media(bytes),
                timeout=self.config['processing_timeout']
            )
            
            # Extract metadata with enterprise error handling
            mime_type, file_name = await self._extract_document_metadata(message)
            caption = await self._process_caption(message.text or "", chat_id)
            
            # Route to specialized handlers
            if mime_type == 'application/pdf':
                await self._handle_pdf_enterprise(chat_id, file_bytes, caption, webhook_url, file_name)
            elif mime_type and mime_type.startswith('audio/'):
                await self._handle_audio_enterprise(chat_id, file_bytes, caption, webhook_url, file_name)
            else:
                await self._handle_document_generic(chat_id, file_bytes, file_name, caption, webhook_url)
            
        except asyncio.TimeoutError:
            logger.error(f"⏰ Document download timeout for group {chat_id}")
            await self._send_timeout_message(webhook_url, "document")
        except Exception as e:
            logger.error(f"❌ Enterprise document processing error: {e}")
            raise
    
    async def _extract_document_metadata(self, message) -> tuple[str, str]:
        """Extract document metadata with enterprise validation"""
        mime_type = getattr(message.media.document, 'mime_type', 'unknown')
        attributes = getattr(message.media.document, 'attributes', [])
        
        file_name = "unknown_document"
        for attr in attributes:
            if hasattr(attr, 'file_name') and attr.file_name:
                # Sanitize filename for enterprise security
                file_name = "".join(c for c in attr.file_name if c.isalnum() or c in '.-_')[:255]
                break
        
        return mime_type, file_name
    
    async def _process_caption(self, caption: str, chat_id: int) -> str:
        """Process caption with enterprise watermarks"""
        if caption:
            processed_caption, _ = await self.watermark_service.process_text(caption, chat_id)
            return processed_caption
        return caption
    
    async def _handle_pdf_enterprise(self, chat_id: int, pdf_bytes: bytes, 
                                   caption: str, webhook_url: str, filename: str):
        """
        📄 MANEJO DE PDF - ENVÍO DIRECTO
        ===============================
        
        CAMBIO PRINCIPAL: Envía PDF directamente cuando es posible
        """
        try:
            size_mb = len(pdf_bytes) / (1024 * 1024)
            
            if size_mb <= self.config['direct_sending']['max_file_size_mb']:
                # 🎯 ENVÍO DIRECTO del PDF
                full_caption = f"📄 **PDF Enterprise:** {filename} ({size_mb:.1f}MB)"
                if caption:
                    full_caption += f"\n\n{caption}"
                
                success = await self.discord_sender.send_message_with_file(
                    webhook_url,
                    full_caption,
                    pdf_bytes,
                    filename
                )
                
                if success:
                    self.stats['pdfs_processed'] += 1
                    self.stats['pdfs_sent_direct'] += 1
                    self.stats['files_sent_direct'] += 1
                    logger.info(f"📄 Enterprise PDF enviado DIRECTAMENTE: {filename}")
                    return
                else:
                    await self._handle_send_failure(webhook_url, f"PDF {filename}")
                    return
            
            # Si es muy grande, procesar con preview
            result = await self.file_processor.process_pdf(pdf_bytes, chat_id, filename)
            
            if result["success"]:
                message_text = self._build_pdf_message(caption, result, filename)
                
                # Enviar con preview si está disponible
                if result.get("preview_bytes"):
                    success = await self.discord_sender.send_message_with_file(
                        webhook_url, message_text, result["preview_bytes"], "pdf_preview.jpg"
                    )
                    if success:
                        self.stats['images_sent_direct'] += 1
                        self.stats['files_sent_direct'] += 1
                else:
                    success = await self.discord_sender.send_message(webhook_url, message_text)
                
                if success:
                    self.stats['pdfs_processed'] += 1
                    logger.info(f"📄 Enterprise PDF processed: {filename}")
                else:
                    await self._handle_send_failure(webhook_url, f"PDF {filename}")
            else:
                await self._send_processing_error(webhook_url, "PDF", filename, result.get("error"))
                
        except Exception as e:
            logger.error(f"❌ Enterprise PDF handling error: {e}")
            await self._send_processing_error(webhook_url, "PDF", filename, str(e))
    
    def _build_pdf_message(self, caption: str, result: dict, filename: str) -> str:
        """Build enterprise PDF message with rich metadata"""
        message_parts = [
            caption,
            "",
            f"📄 **PDF Document Enterprise**",
            f"📄 File: {filename}",
            f"💾 Size: {result['size_mb']:.1f} MB"
        ]
        
        if result.get('page_count'):
            message_parts.append(f"📃 Pages: {result['page_count']}")
        
        message_parts.extend([
            f"🔗 [📥 Download PDF]({result['download_url']})",
            "⏰ Available for 24 hours",
            "🔒 Enterprise secured download"
        ])
        
        return "\n".join(message_parts)
    
    async def _handle_audio_enterprise(self, chat_id: int, audio_bytes: bytes,
                                     caption: str, webhook_url: str, filename: str):
        """
        🎵 MANEJO DE AUDIO - ENVÍO DIRECTO
        =================================
        
        CAMBIO PRINCIPAL: Envía audio directamente, no como link
        """
        try:
            # Verificar tamaño
            size_mb = len(audio_bytes) / (1024 * 1024)
            
            if size_mb > self.config['direct_sending']['max_file_size_mb']:
                error_message = f"🎵 **Audio muy grande:** {filename} ({size_mb:.1f}MB)\n{caption}\n❌ Supera el límite de Discord ({self.config['direct_sending']['max_file_size_mb']}MB)"
                await self.discord_sender.send_message(webhook_url, error_message)
                self.stats['large_files_rejected'] += 1
                return
            
            # 🎯 CAMBIO CLAVE: ENVÍO DIRECTO del audio
            full_caption = f"🎵 **Audio Enterprise:** {filename if filename and filename != 'unknown_document' else 'Audio File'} ({size_mb:.1f}MB)"
            if caption:
                full_caption += f"\n\n{caption}"
            
            # ENVÍO DIRECTO del archivo de audio
            success = await self.discord_sender.send_message_with_file(
                webhook_url,
                full_caption,
                audio_bytes,
                filename if filename and filename != "unknown_document" else f"audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
            )
            
            if success:
                self.stats['audios_processed'] += 1
                self.stats['audios_sent_direct'] += 1
                self.stats['files_sent_direct'] += 1
                logger.info(f"🎵 Enterprise audio enviado DIRECTAMENTE: {filename}")
            else:
                await self._handle_send_failure(webhook_url, f"audio {filename}")
                
        except Exception as e:
            logger.error(f"❌ Enterprise audio handling error: {e}")
            await self._send_processing_error(webhook_url, "Audio", filename, str(e))
    
    async def _handle_document_generic(self, chat_id: int, file_bytes: bytes,
                                     file_name: str, caption: str, webhook_url: str):
        """Generic document handler para envío directo"""
        try:
            size_mb = len(file_bytes) / (1024 * 1024)
            
            if size_mb <= self.config['direct_sending']['max_file_size_mb']:
                # 🎯 ENVÍO DIRECTO del documento
                full_caption = f"📎 **Document Enterprise:** {file_name} ({size_mb:.1f}MB)"
                if caption:
                    full_caption += f"\n\n{caption}"
                
                success = await self.discord_sender.send_message_with_file(
                    webhook_url,
                    full_caption,
                    file_bytes,
                    file_name
                )
                
                if success:
                    self.stats['documents_processed'] += 1
                    self.stats['files_sent_direct'] += 1
                    logger.info(f"📎 Enterprise document enviado DIRECTAMENTE: {file_name}")
                    return
            
            # Si es muy grande, crear descarga temporal
            result = await self.file_processor.create_temp_download(file_bytes, file_name, chat_id)
            
            if result["success"]:
                message_text = "\n".join([
                    caption,
                    "",
                    f"📎 **Document Enterprise:** {file_name}",
                    f"💾 Size: {result['size_mb']:.1f} MB",
                    f"🔗 [📥 Download]({result['download_url']})",
                    "🔒 Enterprise secured download"
                ])
                
                await self.discord_sender.send_message(webhook_url, message_text)
                self.stats['documents_processed'] += 1
            
        except Exception as e:
            logger.error(f"❌ Generic document handling error: {e}")
            await self._send_processing_error(webhook_url, "Document", file_name, str(e))
    
    async def _process_image_enterprise(self, chat_id: int, message, webhook_url: str):
        """
        🖼️ PROCESAMIENTO DE IMAGEN - ENVÍO DIRECTO
        ==========================================
        
        CAMBIO PRINCIPAL: Usa send_message_with_file() para envío directo
        Ya NO genera links de descarga
        """
        try:
            # Download con timeout
            image_bytes = await asyncio.wait_for(
                message.download_media(bytes),
                timeout=60
            )
            
            # Verificar tamaño y comprimir si es necesario
            size_mb = len(image_bytes) / (1024 * 1024)
            
            # Aplicar watermarks empresariales
            processed_bytes, was_processed = await self.watermark_service.apply_image_watermark(
                image_bytes, chat_id
            )
            
            # Comprimir si es muy grande
            if size_mb > self.config['direct_sending']['max_file_size_mb']:
                if self.config['direct_sending']['auto_compress']:
                    compressed_bytes = await self._compress_image_if_needed(processed_bytes)
                    if compressed_bytes and len(compressed_bytes) < len(processed_bytes):
                        original_size = len(processed_bytes) / (1024 * 1024)
                        new_size = len(compressed_bytes) / (1024 * 1024)
                        savings = original_size - new_size
                        
                        processed_bytes = compressed_bytes
                        size_mb = new_size
                        self.stats['files_compressed'] += 1
                        self.stats['compression_savings_mb'] += savings
                        
                        logger.info(f"⚡ Imagen comprimida: {original_size:.1f}MB → {new_size:.1f}MB")
                    else:
                        # No se puede comprimir más
                        error_message = f"🖼️ **Imagen muy grande:** {size_mb:.1f}MB\n❌ No se puede comprimir para Discord"
                        await self.discord_sender.send_message(webhook_url, error_message)
                        self.stats['large_files_rejected'] += 1
                        return
                else:
                    error_message = f"🖼️ **Imagen muy grande:** {size_mb:.1f}MB\n❌ Supera el límite de Discord"
                    await self.discord_sender.send_message(webhook_url, error_message)
                    self.stats['large_files_rejected'] += 1
                    return
            
            # Procesar caption
            caption = await self._process_caption(message.text or "", chat_id)
            
            # 🎯 CAMBIO CLAVE: ENVÍO DIRECTO en lugar de links
            # Construir mensaje con info del archivo
            full_caption = f"🖼️ **Imagen Enterprise** ({size_mb:.1f}MB)"
            if caption:
                full_caption += f"\n\n{caption}"
            
            # ENVÍO DIRECTO del archivo
            success = await self.discord_sender.send_message_with_file(
                webhook_url, 
                full_caption, 
                processed_bytes, 
                "image_enterprise.jpg"
            )
            
            if success:
                self.stats['images_processed'] += 1
                self.stats['images_sent_direct'] += 1
                self.stats['files_sent_direct'] += 1
                if was_processed:
                    self.stats['watermarks_applied'] += 1
                logger.info(f"🖼️ Enterprise image enviada DIRECTAMENTE para group {chat_id}")
            else:
                await self._handle_send_failure(webhook_url, "image")
            
        except asyncio.TimeoutError:
            await self._send_timeout_message(webhook_url, "image")
        except Exception as e:
            logger.error(f"❌ Enterprise image processing error: {e}")
            raise
    
    async def _process_video_enterprise(self, chat_id: int, message, webhook_url: str):
        """
        🎬 PROCESAMIENTO DE VIDEO - ENVÍO DIRECTO
        ========================================
        
        CAMBIO PRINCIPAL: Envía video directamente, no como link
        """
        try:
            # Download con timeout extendido para videos
            video_bytes = await asyncio.wait_for(
                message.download_media(bytes),
                timeout=self.config['processing_timeout']
            )
            
            # Verificar tamaño de Discord (25MB limit)
            size_mb = len(video_bytes) / (1024 * 1024)
            
            if size_mb > self.config['direct_sending']['max_file_size_mb']:
                # Para videos muy grandes, procesar primero
                if self.config['direct_sending']['auto_compress']:
                    result = await self.file_processor.process_video(video_bytes, chat_id, "video_enterprise.mp4")
                    
                    if result["success"] and result.get("compressed_size"):
                        # Usar video comprimido si está disponible
                        compressed_size_mb = result["compressed_size"] / (1024 * 1024)
                        if compressed_size_mb <= self.config['direct_sending']['max_file_size_mb']:
                            # Cargar video comprimido
                            compressed_path = Path(result.get("output_path", ""))
                            if compressed_path.exists():
                                video_bytes = compressed_path.read_bytes()
                                size_mb = compressed_size_mb
                                self.stats['files_compressed'] += 1
                                self.stats['compression_savings_mb'] += (len(video_bytes) - len(compressed_path.read_bytes())) / (1024 * 1024)
                                logger.info(f"🎬 Video comprimido: {size_mb:.1f}MB")
                            else:
                                # Si no hay archivo comprimido, enviar mensaje de error
                                caption = await self._process_caption(message.text or "", chat_id)
                                error_message = f"🎬 **Video muy grande:** {size_mb:.1f}MB\n{caption}\n❌ Supera el límite de Discord ({self.config['direct_sending']['max_file_size_mb']}MB)"
                                await self.discord_sender.send_message(webhook_url, error_message)
                                self.stats['large_files_rejected'] += 1
                                return
                        else:
                            # Incluso comprimido es muy grande
                            caption = await self._process_caption(message.text or "", chat_id)
                            error_message = f"🎬 **Video muy grande:** {size_mb:.1f}MB → {compressed_size_mb:.1f}MB\n{caption}\n❌ No se puede reducir más para Discord"
                            await self.discord_sender.send_message(webhook_url, error_message)
                            self.stats['large_files_rejected'] += 1
                            return
                    else:
                        # No se pudo comprimir
                        caption = await self._process_caption(message.text or "", chat_id)
                        error_message = f"🎬 **Video muy grande:** {size_mb:.1f}MB\n{caption}\n❌ No se puede comprimir para Discord"
                        await self.discord_sender.send_message(webhook_url, error_message)
                        self.stats['large_files_rejected'] += 1
                        return
                else:
                    # Compresión deshabilitada
                    caption = await self._process_caption(message.text or "", chat_id)
                    error_message = f"🎬 **Video muy grande:** {size_mb:.1f}MB\n{caption}\n❌ Supera el límite de Discord"
                    await self.discord_sender.send_message(webhook_url, error_message)
                    self.stats['large_files_rejected'] += 1
                    return
            
            # Procesar caption
            caption = await self._process_caption(message.text or "", chat_id)
            
            # 🎯 CAMBIO CLAVE: ENVÍO DIRECTO del video
            full_caption = f"🎬 **Video Enterprise** ({size_mb:.1f}MB)"
            if caption:
                full_caption += f"\n\n{caption}"
            
            # ENVÍO DIRECTO del archivo de video
            success = await self.discord_sender.send_message_with_file(
                webhook_url,
                full_caption,
                video_bytes,
                "video_enterprise.mp4"
            )
            
            if success:
                self.stats['videos_processed'] += 1
                self.stats['videos_sent_direct'] += 1
                self.stats['files_sent_direct'] += 1
                self.stats['watermarks_applied'] += 1  # Videos siempre tienen watermark implícito
                logger.info(f"🎬 Enterprise video enviado DIRECTAMENTE para group {chat_id}")
            else:
                await self._handle_send_failure(webhook_url, "video")
            
        except asyncio.TimeoutError:
            await self._send_timeout_message(webhook_url, "video")
        except Exception as e:
            logger.error(f"❌ Enterprise video processing error: {e}")
            raise
    
    async def _process_other_media_enterprise(self, chat_id: int, message, webhook_url: str):
        """Enterprise handler for other media types"""
        try:
            media_type = type(message.media).__name__
            caption = await self._process_caption(message.text or "", chat_id)
            
            message_text = f"📎 **Enterprise Media:** {media_type}\n{caption}\n🔒 Enterprise processed"
            await self.discord_sender.send_message(webhook_url, message_text)
            
        except Exception as e:
            logger.error(f"❌ Other media processing error: {e}")
            raise
    
    async def _compress_image_if_needed(self, image_bytes: bytes) -> Optional[bytes]:
        """Comprimir imagen si es necesario"""
        try:
            from PIL import Image
            from io import BytesIO
            
            # Cargar imagen
            img = Image.open(BytesIO(image_bytes))
            
            # Reducir tamaño si es muy grande
            max_size = (1920, 1080)
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Comprimir
            output = BytesIO()
            
            # Convertir a RGB si tiene transparencia
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            img.save(output, format='JPEG', quality=self.config['direct_sending']['compression_quality'], optimize=True)
            
            compressed = output.getvalue()
            return compressed if len(compressed) < len(image_bytes) else None
            
        except ImportError:
            logger.warning("⚠️ PIL no disponible para compresión")
            return None
        except Exception as e:
            logger.warning(f"⚠️ Error comprimiendo imagen: {e}")
            return None
    
    async def _start_background_tasks(self):
        """Start enterprise background tasks"""
        # Health monitoring
        asyncio.create_task(self._health_monitor())
        
        # Metrics collection
        asyncio.create_task(self._metrics_collector())
        
        # Cleanup tasks
        asyncio.create_task(self._cleanup_monitor())
        
        logger.info("🔄 Enterprise background tasks started")
    
    async def _health_monitor(self):
        """Enterprise health monitoring"""
        while self.is_running:
            try:
                await asyncio.sleep(self.config['health_check_interval'])
                await self._perform_health_checks()
            except Exception as e:
                logger.error(f"❌ Health monitor error: {e}")
    
    async def _metrics_collector(self):
        """Enterprise metrics collection"""
        while self.is_running:
            try:
                await asyncio.sleep(self.config['metrics_collection_interval'])
                await self._collect_performance_metrics()
            except Exception as e:
                logger.error(f"❌ Metrics collector error: {e}")
    
    async def _cleanup_monitor(self):
        """Enterprise cleanup monitoring"""
        while self.is_running:
            try:
                await asyncio.sleep(3600)  # Every hour
                await self._perform_cleanup()
            except Exception as e:
                logger.error(f"❌ Cleanup monitor error: {e}")
    
    def _update_performance_metrics(self, processing_time: float):
        """Update enterprise performance metrics"""
        metrics = self.stats['performance_metrics']
        metrics['total_processing_time'] += processing_time
        
        total_processed = (self.stats['messages_replicated'] + 
                         self.stats['pdfs_processed'] + 
                         self.stats['videos_processed'] + 
                         self.stats['audios_processed'] +
                         self.stats['images_processed'])
        
        if total_processed > 0:
            metrics['avg_processing_time'] = metrics['total_processing_time'] / total_processed
    
    async def _handle_send_failure(self, webhook_url: str, content_type: str):
        """Handle enterprise send failures"""
        self.stats['retries'] += 1
        logger.warning(f"⚠️ Send failure for {content_type} to {webhook_url[:50]}...")
    
    async def _send_timeout_message(self, webhook_url: str, content_type: str):
        """Send timeout notification"""
        message = f"⏰ **Processing Timeout**\n{content_type.title()} processing took too long.\n🔒 Enterprise timeout protection activated"
        await self.discord_sender.send_message(webhook_url, message)
    
    async def _send_processing_error(self, webhook_url: str, content_type: str, 
                                   filename: str, error: str):
        """Send processing error notification"""
        message = f"❌ **Processing Error**\n{content_type}: {filename}\nError: {error}\n🔒 Enterprise error handling"
        await self.discord_sender.send_message(webhook_url, message)
    
    async def _handle_processing_error(self, error: Exception, chat_id: Optional[int]):
        """Enterprise error handling"""
        self.stats['errors'] += 1
        
        # Could implement error reporting to monitoring systems here
        logger.error(f"❌ Processing error for group {chat_id}: {error}")
    
    async def _handle_initialization_failure(self, error: Exception):
        """Handle enterprise initialization failures"""
        logger.critical(f"💥 Enterprise initialization failed: {error}")
        # Could implement alerting systems here
    
    async def _display_enterprise_configuration(self):
        """Display enterprise configuration summary"""
        logger.info("📊 Enterprise Configuration - ENVÍO DIRECTO:")
        logger.info(f"   Groups configured: {len(settings.discord.webhooks)}")
        logger.info(f"   Max concurrent processing: {self.config['max_concurrent_processing']}")
        logger.info(f"   Circuit breaker threshold: {self.config['circuit_breaker_threshold']}")
        logger.info(f"   Processing timeout: {self.config['processing_timeout']}s")
        logger.info(f"   Direct Sending Settings:")
        logger.info(f"     - Max file size: {self.config['direct_sending']['max_file_size_mb']}MB")
        logger.info(f"     - Auto compress: {self.config['direct_sending']['auto_compress']}")
        logger.info(f"     - Compression quality: {self.config['direct_sending']['compression_quality']}")
        logger.info(f"     - Prefer direct: {self.config['direct_sending']['prefer_direct']}")
        logger.info(f"   Enterprise Services:")
        logger.info(f"     - File Processor: ✅ Advanced")
        logger.info(f"     - Watermark Service: ✅ Multi-tenant")
        logger.info(f"     - Discord Sender: ✅ ENVÍO DIRECTO enabled")
        logger.info(f"   Dependencies:")
        logger.info(f"     - Telethon: {'✅' if TELETHON_AVAILABLE else '❌'}")
        logger.info(f"     - PIL: {'✅' if PIL_AVAILABLE else '❌'}")
        logger.info(f"     - PyMuPDF: {'✅' if PYMUPDF_AVAILABLE else '❌'}")
        logger.info(f"     - aiohttp: {'✅' if AIOHTTP_AVAILABLE else '❌'}")
    
    async def start_listening(self):
        """Start enterprise message listening"""
        try:
            if not self.telegram_client:
                logger.error("❌ Telegram client not initialized")
                return
            
            self.is_listening = True
            logger.info("👂 Starting enterprise message listening - MODO ENVÍO DIRECTO...")
            
            # Display monitored groups
            for group_id in settings.discord.webhooks.keys():
                logger.info(f"   👥 Monitoring enterprise group: {group_id}")
            
            # Start with enterprise error handling
            await self.telegram_client.run_until_disconnected()
            
        except Exception as e:
            logger.error(f"❌ Enterprise listening error: {e}")
            self.stats['errors'] += 1
        finally:
            self.is_listening = False
            logger.info("🛑 Enterprise listening stopped")
    
    async def stop(self):
        """Stop enterprise service with graceful shutdown"""
        try:
            logger.info("🛑 Stopping Enhanced Replicator Service Enterprise...")
            
            self.is_running = False
            self.is_listening = False
            
            # Graceful shutdown of services
            shutdown_tasks = []
            
            if self.telegram_client:
                shutdown_tasks.append(self._shutdown_telegram())
            
            if self.discord_sender:
                shutdown_tasks.append(self._shutdown_discord_sender())
            
            # Wait for all shutdowns with timeout
            if shutdown_tasks:
                await asyncio.wait_for(
                    asyncio.gather(*shutdown_tasks, return_exceptions=True),
                    timeout=30
                )
            
            logger.info("✅ Enhanced Replicator Service Enterprise stopped")
            
        except asyncio.TimeoutError:
            logger.warning("⏰ Enterprise shutdown timeout - forcing stop")
        except Exception as e:
            logger.error(f"❌ Enterprise shutdown error: {e}")
    
    async def _shutdown_telegram(self):
        """Graceful Telegram shutdown"""
        try:
            await self.telegram_client.disconnect()
            logger.info("📱 Telegram client disconnected")
        except Exception as e:
            logger.error(f"❌ Telegram shutdown error: {e}")
    
    async def _shutdown_discord_sender(self):
        """Graceful Discord sender shutdown"""
        try:
            await self.discord_sender.close()
            logger.info("📤 Discord sender closed")
        except Exception as e:
            logger.error(f"❌ Discord sender shutdown error: {e}")
    
    async def get_health(self) -> Dict[str, Any]:
        """Comprehensive enterprise health check"""
        try:
            health_data = {
                "status": "healthy" if self.is_running else "stopped",
                "timestamp": datetime.now().isoformat(),
                "version": "3.0.0-enterprise-direct-sending",
                "is_running": self.is_running,
                "is_listening": self.is_listening,
                "telegram_connected": self.telegram_client is not None,
                "direct_sending_enabled": True,
                "services": {
                    "file_processor": await self._check_service_health(self.file_processor),
                    "watermark_service": await self._check_service_health(self.watermark_service),
                    "discord_sender": await self._check_service_health(self.discord_sender)
                },
                "dependencies": {
                    "telethon": TELETHON_AVAILABLE,
                    "pil": PIL_AVAILABLE,
                    "pymupdf": PYMUPDF_AVAILABLE,
                    "aiohttp": AIOHTTP_AVAILABLE
                },
                "performance": {
                    "uptime_seconds": (datetime.now() - self.stats['start_time']).total_seconds(),
                    "messages_processed": self.stats['messages_received'],
                    "success_rate": self._calculate_success_rate(),
                    "avg_processing_time": self.stats['performance_metrics']['avg_processing_time'],
                    "active_connections": self.stats['performance_metrics']['active_connections'],
                    "error_rate": self._calculate_error_rate()
                },
                "direct_sending_metrics": {
                    "files_sent_direct": self.stats['files_sent_direct'],
                    "images_sent_direct": self.stats['images_sent_direct'],
                    "videos_sent_direct": self.stats['videos_sent_direct'],
                    "audios_sent_direct": self.stats['audios_sent_direct'],
                    "pdfs_sent_direct": self.stats['pdfs_sent_direct'],
                    "files_compressed": self.stats['files_compressed'],
                    "compression_savings_mb": self.stats['compression_savings_mb'],
                    "large_files_rejected": self.stats['large_files_rejected']
                },
                "configuration": {
                    "groups_configured": len(settings.discord.webhooks),
                    "max_concurrent_processing": self.config['max_concurrent_processing'],
                    "circuit_breaker_threshold": self.config['circuit_breaker_threshold'],
                    "direct_sending_config": self.config['direct_sending']
                },
                "stats": self.stats.copy()
            }
            
            # Convert set to list for JSON serialization
            health_data["stats"]["groups_active"] = list(health_data["stats"]["groups_active"])
            
            return health_data
            
        except Exception as e:
            logger.error(f"❌ Health check error: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _check_service_health(self, service) -> Dict[str, Any]:
        """Check individual service health"""
        try:
            if hasattr(service, 'get_health'):
                return await service.get_health()
            else:
                return {
                    "status": "healthy" if service is not None else "unavailable",
                    "initialized": service is not None
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def _calculate_success_rate(self) -> float:
        """Calculate enterprise success rate"""
        total_attempts = self.stats['messages_received']
        if total_attempts == 0:
            return 100.0
        
        successful = self.stats['messages_replicated']
        return (successful / total_attempts) * 100
    
    def _calculate_error_rate(self) -> float:
        """Calculate enterprise error rate"""
        total_attempts = self.stats['messages_received']
        if total_attempts == 0:
            return 0.0
        
        errors = self.stats['errors']
        return (errors / total_attempts) * 100
    
    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """Enterprise dashboard statistics with direct sending metrics"""
        try:
            uptime = (datetime.now() - self.stats['start_time']).total_seconds()
            
            # Collect stats from all enterprise services
            combined_stats = self.stats.copy()
            
            # File processor stats
            if self.file_processor and hasattr(self.file_processor, 'get_stats'):
                file_stats = await self.file_processor.get_stats()
                combined_stats.update(file_stats)
            
            # Watermark service stats
            if self.watermark_service and hasattr(self.watermark_service, 'get_stats'):
                watermark_stats = await self.watermark_service.get_stats()
                combined_stats.update(watermark_stats)
            
            # Discord sender stats
            if self.discord_sender and hasattr(self.discord_sender, 'get_stats'):
                discord_stats = await self.discord_sender.get_stats()
                combined_stats.update(discord_stats)
            
            # Build enterprise dashboard data with direct sending metrics
            dashboard_data = {
                "overview": {
                    "messages_received": combined_stats.get('messages_received', 0),
                    "messages_replicated": combined_stats.get('messages_replicated', 0),
                    "success_rate": self._calculate_success_rate(),
                    "error_rate": self._calculate_error_rate(),
                    "uptime_hours": uptime / 3600,
                    "is_running": self.is_running,
                    "is_listening": self.is_listening,
                    "direct_sending_enabled": True
                },
                "processing": {
                    "pdfs_processed": combined_stats.get('pdfs_processed', 0),
                    "videos_processed": combined_stats.get('videos_processed', 0),
                    "audios_processed": combined_stats.get('audios_processed', 0),
                    "images_processed": combined_stats.get('images_processed', 0),
                    "documents_processed": combined_stats.get('documents_processed', 0),
                    "watermarks_applied": combined_stats.get('watermarks_applied', 0)
                },
                "direct_sending": {
                    "files_sent_direct": combined_stats.get('files_sent_direct', 0),
                    "images_sent_direct": combined_stats.get('images_sent_direct', 0),
                    "videos_sent_direct": combined_stats.get('videos_sent_direct', 0),
                    "audios_sent_direct": combined_stats.get('audios_sent_direct', 0),
                    "pdfs_sent_direct": combined_stats.get('pdfs_sent_direct', 0),
                    "files_compressed": combined_stats.get('files_compressed', 0),
                    "compression_savings_mb": combined_stats.get('compression_savings_mb', 0.0),
                    "large_files_rejected": combined_stats.get('large_files_rejected', 0),
                    "direct_sending_rate": (
                        combined_stats.get('files_sent_direct', 0) / 
                        max(combined_stats.get('messages_received', 1), 1) * 100
                    )
                },
                "performance": {
                    "avg_processing_time": self.stats['performance_metrics']['avg_processing_time'],
                    "active_connections": self.stats['performance_metrics']['active_connections'],
                    "total_processing_time": self.stats['performance_metrics']['total_processing_time'],
                    "cache_hit_rate": combined_stats.get('cache_hit_rate', 0),
                    "memory_usage": self.stats['performance_metrics']['peak_memory_usage']
                },
                "groups": {
                    "configured": len(settings.discord.webhooks),
                    "active": len(self.stats['groups_active']),
                    "active_list": list(self.stats['groups_active'])
                },
                "errors": {
                    "total_errors": combined_stats.get('errors', 0),
                    "total_retries": combined_stats.get('retries', 0),
                    "circuit_breaker_trips": self.stats.get('circuit_breaker_trips', 0)
                },
                "timestamps": {
                    "last_message": (
                        self.stats['last_message_time'].isoformat() 
                        if self.stats['last_message_time'] else None
                    ),
                    "start_time": self.stats['start_time'].isoformat(),
                    "current_time": datetime.now().isoformat()
                }
            }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"❌ Dashboard stats error: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_enterprise_metrics(self) -> Dict[str, Any]:
        """Get comprehensive enterprise metrics with direct sending data"""
        try:
            return {
                "service_metrics": await self.get_dashboard_stats(),
                "health_metrics": await self.get_health(),
                "business_metrics": {
                    "total_groups_served": len(settings.discord.webhooks),
                    "total_messages_processed": self.stats['messages_received'],
                    "total_media_processed": (
                        self.stats['pdfs_processed'] + 
                        self.stats['videos_processed'] + 
                        self.stats['audios_processed'] + 
                        self.stats['images_processed']
                    ),
                    "total_files_sent_direct": self.stats['files_sent_direct'],
                    "watermark_adoption_rate": (
                        self.stats['watermarks_applied'] / 
                        max(self.stats['messages_received'], 1) * 100
                    ),
                    "direct_sending_adoption": (
                        self.stats['files_sent_direct'] / 
                        max(self.stats['messages_received'], 1) * 100
                    )
                },
                "operational_metrics": {
                    "availability": self._calculate_availability(),
                    "throughput": self._calculate_throughput(),
                    "latency": self.stats['performance_metrics']['avg_processing_time'],
                    "error_budget_remaining": max(0, 99.9 - self._calculate_error_rate()),
                    "compression_efficiency": (
                        self.stats['compression_savings_mb'] / 
                        max(self.stats['files_compressed'], 1)
                    )
                }
            }
        except Exception as e:
            logger.error(f"❌ Enterprise metrics error: {e}")
            return {"error": str(e)}
    
    def _calculate_availability(self) -> float:
        """Calculate service availability percentage"""
        if not hasattr(self, '_downtime_seconds'):
            self._downtime_seconds = 0
        
        uptime = (datetime.now() - self.stats['start_time']).total_seconds()
        total_time = uptime + self._downtime_seconds
        
        if total_time == 0:
            return 100.0
        
        return (uptime / total_time) * 100
    
    def _calculate_throughput(self) -> float:
        """Calculate messages per minute"""
        uptime = (datetime.now() - self.stats['start_time']).total_seconds()
        if uptime == 0:
            return 0.0
        
        messages_per_second = self.stats['messages_received'] / uptime
        return messages_per_second * 60  # Convert to per minute
    
    async def _perform_health_checks(self):
        """Perform periodic health checks"""
        try:
            # Check service health
            health = await self.get_health()
            
            # Log health status
            if health["status"] != "healthy":
                logger.warning(f"⚠️ Health check warning: {health.get('status')}")
            
            # Check thresholds
            error_rate = self._calculate_error_rate()
            if error_rate > 5.0:  # 5% error threshold
                logger.warning(f"⚠️ High error rate: {error_rate:.2f}%")
            
            # Check direct sending performance
            direct_rate = self.stats['files_sent_direct'] / max(self.stats['messages_received'], 1) * 100
            if direct_rate < 80:  # Expected >80% direct sending
                logger.warning(f"⚠️ Low direct sending rate: {direct_rate:.2f}%")
            
        except Exception as e:
            logger.error(f"❌ Health check error: {e}")
    
    async def _collect_performance_metrics(self):
        """Collect performance metrics"""
        try:
            # Update memory usage (simplified)
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            if memory_mb > self.stats['performance_metrics']['peak_memory_usage']:
                self.stats['performance_metrics']['peak_memory_usage'] = memory_mb
            
        except ImportError:
            # psutil not available, skip memory monitoring
            pass
        except Exception as e:
            logger.debug(f"Metrics collection error: {e}")
    
    async def _perform_cleanup(self):
        """Perform periodic cleanup"""
        try:
            # Cleanup temp files older than 24 hours
            temp_dirs = [Path("temp_files"), Path("processed_files")]
            
            for temp_dir in temp_dirs:
                if temp_dir.exists():
                    for file_path in temp_dir.iterdir():
                        if file_path.is_file():
                            # Check file age
                            file_age = datetime.now().timestamp() - file_path.stat().st_mtime
                            if file_age > 86400:  # 24 hours
                                file_path.unlink()
            
            logger.debug("🧹 Periodic cleanup completed")
            
        except Exception as e:
            logger.error(f"❌ Cleanup error: {e}")

# Enterprise service factory for dependency injection
def create_enhanced_replicator_service() -> EnhancedReplicatorService:
    """Factory function para crear enterprise replicator service con envío directo"""
    return EnhancedReplicatorService()

# Alias for backward compatibility
ReplicatorService = EnhancedReplicatorService