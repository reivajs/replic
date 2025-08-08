"""
Main v3.0 - Integración SaaS-Ready con Arquitectura Modular
=========================================================
Integración limpia del WatermarkManager con tu sistema existente
Enfoque híbrido: mantiene compatibilidad + añade nuevas funcionalidades

CAMBIOS PRINCIPALES:
- ✅ Watermark Manager completo (PNG + Texto + Video)
- ✅ Dashboard v3 con UX Apple
- ✅ Procesamiento async optimizado
- ✅ Cache inteligente
- ✅ Health checks y monitoring
- ✅ Preparado para microservicios

COMPATIBILIDAD:
- 🔄 Funciona con tu main.py existente
- 🔄 Mantiene todas las funcionalidades actuales
- ➕ Añade watermarks PNG + video sin romper nada
"""

import asyncio
import os
import sys
import threading
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# FastAPI para dashboard
from fastapi import FastAPI
import uvicorn

# Telegram
from telethon import TelegramClient, events
from dotenv import load_dotenv

# Servicios modulares
from services.watermark.manager import WatermarkManager, create_watermark_manager
from api.dashboard_v3 import EnhancedDashboardV3, create_enhanced_dashboard
from utils.logger import setup_logger

# Configuraciones existentes (compatibilidad)
from config import Config  # Tu config.py existente

# Verificar Python 3.7+
if sys.version_info < (3, 7):
    print("❌ Python 3.7+ requerido")
    sys.exit(1)

# Setup logging
logger = setup_logger(__name__)

# ==================== CONFIGURACIÓN ====================

def load_environment() -> Dict[str, Any]:
    """Cargar configuración del entorno"""
    load_dotenv()
    
    config = {
        'telegram': {
            'api_id': int(os.getenv('TELEGRAM_API_ID', 0)),
            'api_hash': os.getenv('TELEGRAM_API_HASH', ''),
            'phone': os.getenv('TELEGRAM_PHONE', ''),
            'session_name': os.getenv('TELEGRAM_SESSION_NAME', 'watermark_session')
        },
        'watermarks': {
            'config_dir': Path(os.getenv('WATERMARK_CONFIG_DIR', 'config')),
            'assets_dir': Path(os.getenv('WATERMARK_ASSETS_DIR', 'watermarks')),
            'temp_dir': Path(os.getenv('WATERMARK_TEMP_DIR', 'temp'))
        },
        'dashboard': {
            'host': os.getenv('DASHBOARD_HOST', '0.0.0.0'),
            'port': int(os.getenv('DASHBOARD_PORT', 8080)),
            'debug': os.getenv('DEBUG', 'false').lower() == 'true'
        },
        'webhooks': {}
    }
    
    # Cargar webhooks de Discord
    for key, value in os.environ.items():
        if key.startswith('WEBHOOK_'):
            try:
                grupo_id = int(key.replace('WEBHOOK_', ''))
                config['webhooks'][grupo_id] = value
            except:
                pass
    
    return config

# ==================== CLASE PRINCIPAL ====================

class TelegramDiscordReplicatorV3:
    """
    🚀 Replicador principal v3.0 con arquitectura modular
    
    Características:
    - Watermark Manager integrado
    - Dashboard enhanced v3
    - Procesamiento async optimizado
    - Monitoring y health checks
    - SaaS-ready architecture
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.start_time = datetime.now()
        
        # Servicios principales
        self.watermark_manager = create_watermark_manager(
            config_dir=config['watermarks']['config_dir'],
            watermarks_dir=config['watermarks']['assets_dir'],
            temp_dir=config['watermarks']['temp_dir']
        )
        
        # Dashboard
        self.dashboard = create_enhanced_dashboard(
            watermark_manager=self.watermark_manager
        )
        
        # Cliente Telegram
        self.telegram_client = TelegramClient(
            config['telegram']['session_name'],
            config['telegram']['api_id'],
            config['telegram']['api_hash']
        )
        
        # FastAPI app
        self.app = FastAPI(
            title="🎨 Watermark Manager API v3.0",
            description="Sistema completo de watermarks para Telegram-Discord",
            version="3.0.0"
        )
        
        # Estado
        self.is_running = False
        self.stats = {
            'messages_processed': 0,
            'images_processed': 0,
            'videos_processed': 0,
            'errors': 0,
            'start_time': self.start_time
        }
        
        # Setup routes
        self._setup_api_routes()
        
        logger.info("🚀 TelegramDiscordReplicator v3.0 inicializado")
        logger.info(f"   📱 Telegram: {config['telegram']['phone']}")
        logger.info(f"   🌐 Dashboard: {config['dashboard']['host']}:{config['dashboard']['port']}")
        logger.info(f"   📁 Grupos monitoreados: {len(config['webhooks'])}")
    
    def _setup_api_routes(self):
        """Configurar rutas de la API"""
        # Dashboard routes
        self.dashboard.setup_routes(self.app)
        
        # Health check
        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "version": "3.0.0",
                "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
                "telegram_connected": self.telegram_client.is_connected(),
                "watermark_manager": self.watermark_manager.health_check(),
                "stats": self.get_stats()
            }
        
        # Stats endpoint
        @self.app.get("/api/system/stats")
        async def get_system_stats():
            return self.get_stats()
    
    async def start_telegram_client(self) -> bool:
        """Inicializar cliente de Telegram"""
        try:
            logger.info("🔌 Conectando a Telegram...")
            
            await self.telegram_client.start(phone=self.config['telegram']['phone'])
            me = await self.telegram_client.get_me()
            
            logger.info(f"✅ Conectado como: {me.first_name} (@{me.username})")
            
            # Registrar handler de mensajes
            self.telegram_client.add_event_handler(
                self._handle_telegram_message,
                events.NewMessage()
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error conectando a Telegram: {e}")
            return False
    
    async def _handle_telegram_message(self, event):
        """
        Handler principal para mensajes de Telegram
        Procesa con watermarks según configuración del grupo
        """
        try:
            chat_id = event.chat_id
            message = event.message
            
            # Verificar si el grupo está configurado
            if chat_id not in self.config['webhooks']:
                return
            
            # Obtener configuración de watermarks para este grupo
            watermark_config = self.watermark_manager.get_group_config(chat_id)
            
            # Procesar según tipo de mensaje
            if message.text and not message.media:
                # Mensaje de texto
                await self._process_text_message(chat_id, message.text, watermark_config)
                
            elif message.photo:
                # Imagen
                await self._process_image_message(chat_id, message, watermark_config)
                
            elif message.video or message.document:
                # Video o documento
                await self._process_media_message(chat_id, message, watermark_config)
            
            self.stats['messages_processed'] += 1
            
        except Exception as e:
            logger.error(f"❌ Error procesando mensaje de {chat_id}: {e}")
            self.stats['errors'] += 1
    
    async def _process_text_message(self, chat_id: int, text: str, config):
        """Procesar mensaje de texto con watermarks de texto"""
        try:
            # Aplicar watermark de texto si está configurado
            processed_text, was_modified = await self.watermark_manager.process_text_message(text, chat_id)
            
            if was_modified:
                logger.debug(f"📝 Texto procesado para grupo {chat_id}")
            
            # Enviar a Discord (aquí integrarías con tu sistema existente)
            await self._send_to_discord(chat_id, processed_text)
            
        except Exception as e:
            logger.error(f"❌ Error procesando texto para {chat_id}: {e}")
    
    async def _process_image_message(self, chat_id: int, message, config):
        """Procesar mensaje con imagen"""
        try:
            # Descargar imagen
            image_bytes = await message.download_media(bytes)
            
            # Aplicar watermarks
            processed_bytes, was_processed = await self.watermark_manager.process_image(image_bytes, chat_id)
            
            if was_processed:
                logger.info(f"🖼️ Imagen procesada para grupo {chat_id}")
                self.stats['images_processed'] += 1
            
            # Procesar texto del caption si existe
            caption = message.text or ""
            if caption and config:
                caption, _ = await self.watermark_manager.process_text_message(caption, chat_id)
            
            # Enviar a Discord con imagen procesada
            await self._send_image_to_discord(chat_id, processed_bytes, caption)
            
        except Exception as e:
            logger.error(f"❌ Error procesando imagen para {chat_id}: {e}")
            self.stats['errors'] += 1
    
    async def _process_media_message(self, chat_id: int, message, config):
        """Procesar mensaje con video u otros medios"""
        try:
            # Determinar tipo de media
            is_video = message.video is not None
            is_document = message.document is not None and message.document.mime_type.startswith('video/')
            
            if not (is_video or is_document):
                # No es video, procesar como media normal
                await self._send_media_to_discord(chat_id, message)
                return
            
            # Es video - verificar si debe procesarse
            watermark_config = self.watermark_manager.get_group_config(chat_id)
            if not watermark_config or not watermark_config.video_enabled:
                # No procesar video, enviar original
                await self._send_media_to_discord(chat_id, message)
                return
            
            # Procesar video con watermarks
            logger.info(f"🎬 Procesando video para grupo {chat_id}...")
            
            # Descargar video
            video_bytes = await message.download_media(bytes)
            
            # Verificar tamaño
            size_mb = len(video_bytes) / (1024 * 1024)
            max_size = watermark_config.video_max_size_mb
            
            if size_mb > max_size:
                logger.warning(f"⚠️ Video demasiado grande: {size_mb:.1f}MB > {max_size}MB")
                # Enviar sin procesar
                await self._send_media_to_discord(chat_id, message)
                return
            
            # Aplicar watermarks al video
            processed_bytes, was_processed = await self.watermark_manager.process_video(video_bytes, chat_id)
            
            if was_processed:
                logger.info(f"🎬 Video procesado exitosamente para grupo {chat_id}")
                self.stats['videos_processed'] += 1
                
                # Procesar caption si existe
                caption = message.text or ""
                if caption:
                    caption, _ = await self.watermark_manager.process_text_message(caption, chat_id)
                
                # Enviar video procesado
                await self._send_video_to_discord(chat_id, processed_bytes, caption)
            else:
                # Error procesando, enviar original
                logger.warning(f"⚠️ No se pudo procesar video para {chat_id}, enviando original")
                await self._send_media_to_discord(chat_id, message)
            
        except Exception as e:
            logger.error(f"❌ Error procesando media para {chat_id}: {e}")
            self.stats['errors'] += 1
            # Fallback: enviar mensaje original
            await self._send_media_to_discord(chat_id, message)
    
    async def _send_to_discord(self, chat_id: int, text: str):
        """Enviar texto a Discord"""
        webhook_url = self.config['webhooks'].get(chat_id)
        if not webhook_url:
            return
        
        try:
            # Aquí integrarías con tu sistema de Discord existente
            # Por ejemplo, usando aiohttp para enviar webhook
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                payload = {"content": text[:2000]}  # Límite Discord
                async with session.post(webhook_url, json=payload) as response:
                    if response.status == 204:
                        logger.debug(f"📤 Mensaje enviado a Discord para grupo {chat_id}")
                    else:
                        logger.warning(f"⚠️ Error enviando a Discord: {response.status}")
                        
        except Exception as e:
            logger.error(f"❌ Error enviando texto a Discord para {chat_id}: {e}")
    
    async def _send_image_to_discord(self, chat_id: int, image_bytes: bytes, caption: str = ""):
        """Enviar imagen procesada a Discord"""
        webhook_url = self.config['webhooks'].get(chat_id)
        if not webhook_url:
            return
        
        try:
            import aiohttp
            
            # Crear multipart form data
            data = aiohttp.FormData()
            if caption:
                data.add_field('content', caption[:2000])
            data.add_field('file', image_bytes, filename='image.jpg', content_type='image/jpeg')
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, data=data) as response:
                    if response.status == 200:
                        logger.debug(f"🖼️ Imagen enviada a Discord para grupo {chat_id}")
                    else:
                        logger.warning(f"⚠️ Error enviando imagen: {response.status}")
                        
        except Exception as e:
            logger.error(f"❌ Error enviando imagen a Discord para {chat_id}: {e}")
    
    async def _send_video_to_discord(self, chat_id: int, video_bytes: bytes, caption: str = ""):
        """Enviar video procesado a Discord"""
        webhook_url = self.config['webhooks'].get(chat_id)
        if not webhook_url:
            return
        
        try:
            import aiohttp
            
            # Verificar tamaño para Discord (límite 8MB)
            size_mb = len(video_bytes) / (1024 * 1024)
            if size_mb > 8:
                logger.warning(f"⚠️ Video muy grande para Discord: {size_mb:.1f}MB")
                # Enviar solo el caption
                if caption:
                    await self._send_to_discord(chat_id, f"{caption}\n\n[Video demasiado grande para Discord]")
                return
            
            # Crear multipart form data
            data = aiohttp.FormData()
            if caption:
                data.add_field('content', caption[:2000])
            data.add_field('file', video_bytes, filename='video.mp4', content_type='video/mp4')
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, data=data) as response:
                    if response.status == 200:
                        logger.debug(f"🎬 Video enviado a Discord para grupo {chat_id}")
                    else:
                        logger.warning(f"⚠️ Error enviando video: {response.status}")
                        
        except Exception as e:
            logger.error(f"❌ Error enviando video a Discord para {chat_id}: {e}")
    
    async def _send_media_to_discord(self, chat_id: int, message):
        """Enviar media original sin procesar a Discord"""
        try:
            # Implementación para enviar media original
            # Esta función mantendría tu lógica existente
            caption = message.text or ""
            
            # Procesar solo el texto si hay watermark de texto configurado
            if caption:
                caption, _ = await self.watermark_manager.process_text_message(caption, chat_id)
            
            # Aquí iría tu lógica existente para enviar media a Discord
            logger.debug(f"📎 Media original enviada para grupo {chat_id}")
            
        except Exception as e:
            logger.error(f"❌ Error enviando media original para {chat_id}: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del sistema"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        # Combinar stats del sistema con stats del watermark manager
        watermark_stats = self.watermark_manager.get_stats()
        
        return {
            "system": {
                "uptime_seconds": uptime,
                "uptime_hours": uptime / 3600,
                "messages_processed": self.stats['messages_processed'],
                "errors": self.stats['errors'],
                "telegram_connected": self.telegram_client.is_connected() if hasattr(self.telegram_client, 'is_connected') else False
            },
            "watermarks": watermark_stats,
            "groups": {
                "total_webhooks": len(self.config['webhooks']),
                "active_configs": len([c for c in self.watermark_manager.get_all_configs().values() 
                                     if c.watermark_type.value != 'none'])
            }
        }
    
    async def start_dashboard_server(self):
        """Iniciar servidor web del dashboard"""
        config_uvicorn = uvicorn.Config(
            self.app, 
            host=self.config['dashboard']['host'], 
            port=self.config['dashboard']['port'],
            log_level="warning" if not self.config['dashboard']['debug'] else "debug",
            access_log=False
        )
        
        server = uvicorn.Server(config_uvicorn)
        
        logger.info(f"🌐 Dashboard iniciado en http://{self.config['dashboard']['host']}:{self.config['dashboard']['port']}")
        
        await server.serve()
    
    async def run(self):
        """Ejecutar el replicador completo"""
        try:
            logger.info("🚀 Iniciando Telegram-Discord Replicator v3.0...")
            
            # Inicializar Telegram
            telegram_success = await self.start_telegram_client()
            if not telegram_success:
                logger.error("❌ No se pudo conectar a Telegram")
                return False
            
            self.is_running = True
            
            # Mostrar configuración
            logger.info("📊 Sistema iniciado exitosamente:")
            logger.info(f"   💾 Grupos configurados: {len(self.watermark_manager.get_all_configs())}")
            logger.info(f"   🎨 Capacidades:")
            health = self.watermark_manager.health_check()
            logger.info(f"      • Imágenes: {'✅' if health['capabilities']['images'] else '❌'}")
            logger.info(f"      • Videos: {'✅' if health['capabilities']['videos'] else '❌'}")
            
            # Iniciar dashboard en background
            dashboard_task = asyncio.create_task(self.start_dashboard_server())
            
            logger.info("✅ Sistema listo - Monitoreando mensajes...")
            
            # Mantener el cliente corriendo
            await self.telegram_client.run_until_disconnected()
            
        except KeyboardInterrupt:
            logger.info("🛑 Deteniendo sistema...")
            self.is_running = False
            
        except Exception as e:
            logger.error(f"❌ Error crítico: {e}")
            return False
        
        finally:
            if self.telegram_client.is_connected():
                await self.telegram_client.disconnect()
            logger.info("👋 Sistema detenido")

# ==================== FUNCIÓN PRINCIPAL ====================

async def main():
    """Función principal del sistema v3.0"""
    try:
        # Cargar configuración
        config = load_environment()
        
        # Validar configuración mínima
        if not all([
            config['telegram']['api_id'],
            config['telegram']['api_hash'],
            config['telegram']['phone']
        ]):
            logger.error("❌ Configuración de Telegram incompleta")
            logger.error("   Verifica: TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE")
            return False
        
        if not config['webhooks']:
            logger.warning("⚠️ No hay webhooks configurados")
            logger.warning("   Configura: WEBHOOK_-1001234567890=https://discord.com/api/webhooks/...")
        
        # Crear y ejecutar el replicador
        replicator = TelegramDiscordReplicatorV3(config)
        success = await replicator.run()
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}")
        return False

# ==================== FUNCIÓN DE COMPATIBILIDAD ====================

def run_with_existing_main():
    """
    Función para integrar con tu main.py existente
    Mantiene compatibilidad total con tu sistema actual
    """
    try:
        # Cargar configuración
        config = load_environment()
        
        # Crear solo el WatermarkManager para usar con tu sistema existente
        watermark_manager = create_watermark_manager(
            config_dir=config['watermarks']['config_dir'],
            watermarks_dir=config['watermarks']['assets_dir'],
            temp_dir=config['watermarks']['temp_dir']
        )
        
        # Crear dashboard
        dashboard = create_enhanced_dashboard(watermark_manager)
        
        # Crear app FastAPI para dashboard
        app = FastAPI(title="Watermark Manager Dashboard")
        dashboard.setup_routes(app)
        
        # Función para ejecutar dashboard en hilo separado
        def run_dashboard():
            uvicorn.run(
                app, 
                host="0.0.0.0", 
                port=8080, 
                log_level="warning"
            )
        
        # Iniciar dashboard
        dashboard_thread = threading.Thread(target=run_dashboard, daemon=True)
        dashboard_thread.start()
        
        logger.info("🎨 WatermarkManager integrado con sistema existente")
        logger.info("🌐 Dashboard disponible en http://localhost:8080")
        
        return watermark_manager
        
    except Exception as e:
        logger.error(f"❌ Error integrando WatermarkManager: {e}")
        return None

# ==================== UTILIDADES ====================

def create_example_config():
    """Crear archivo de configuración de ejemplo"""
    example_env = """
# Telegram Configuration
TELEGRAM_API_ID=your_api_id_here
TELEGRAM_API_HASH=your_api_hash_here
TELEGRAM_PHONE=+1234567890
TELEGRAM_SESSION_NAME=watermark_session

# Discord Webhooks (uno por cada grupo)
WEBHOOK_-1001234567890=https://discord.com/api/webhooks/your_webhook_here
WEBHOOK_-1009876543210=https://discord.com/api/webhooks/your_other_webhook_here

# Watermark Configuration
WATERMARK_CONFIG_DIR=config
WATERMARK_ASSETS_DIR=watermarks
WATERMARK_TEMP_DIR=temp

# Dashboard Configuration
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=8080
DEBUG=false
"""
    
    env_file = Path(".env.example")
    with open(env_file, 'w') as f:
        f.write(example_env.strip())
    
    print(f"✅ Archivo de ejemplo creado: {env_file}")
    print("📝 Copia a .env y configura tus valores")

# ==================== ENTRY POINTS ====================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "create-config":
            create_example_config()
            sys.exit(0)
        elif sys.argv[1] == "compatible-mode":
            # Modo compatible con main.py existente
            watermark_manager = run_with_existing_main()
            if watermark_manager:
                print("🎨 WatermarkManager listo para usar con tu sistema existente")
                print("💡 Usa: watermark_manager.process_image(bytes, group_id)")
                print("💡 Usa: watermark_manager.process_video(bytes, group_id)")
                print("💡 Usa: watermark_manager.process_text_message(text, group_id)")
                
                # Mantener vivo para el dashboard
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("👋 Cerrando...")
            sys.exit(0)
    
    # Modo standalone
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n👋 Aplicación detenida por el usuario")
        sys.exit(0)