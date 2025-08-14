#!/usr/bin/env python3
"""
Crear Estructura Completa para Main.py Existente
===============================================
Este script crea todos los módulos que tu main.py necesita manteniendo
arquitectura modular y microservicios.
"""

import os
from pathlib import Path

def create_complete_structure():
    """Crear estructura completa de directorios"""
    
    directories = [
        "app",
        "app/config",
        "app/models", 
        "app/services",
        "app/api",
        "app/utils",
        "services",
        "services/watermark",
        "api",
        "utils", 
        "templates",
        "static",
        "static/css",
        "static/js",
        "logs",
        "config",
        "watermarks",
        "temp",
        "watermark_data",
        "watermark_data/config",
        "watermark_data/assets",
        "watermark_data/temp"
    ]
    
    print("📁 Creando estructura completa...")
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        
        # Crear __init__.py para packages Python
        if any(part in directory for part in ['app', 'services', 'api', 'utils']):
            init_file = Path(directory) / "__init__.py"
            if not init_file.exists():
                init_file.touch()
    
    print("✅ Estructura de directorios creada")

def create_app_config_settings():
    """Crear app/config/settings.py completo"""
    
    content = '''"""
App Config Settings
==================
Configuración centralizada para el sistema
"""

import os
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

@dataclass 
class TelegramSettings:
    api_id: int = int(os.getenv('TELEGRAM_API_ID', 0))
    api_hash: str = os.getenv('TELEGRAM_API_HASH', '')
    phone: str = os.getenv('TELEGRAM_PHONE', '')
    session_name: str = os.getenv('TELEGRAM_SESSION', 'replicator_session')

@dataclass
class DiscordSettings:
    webhooks: Dict[int, str] = field(default_factory=dict)
    max_file_size_mb: int = int(os.getenv('MAX_FILE_SIZE_MB', 8))
    timeout: int = int(os.getenv('DISCORD_TIMEOUT', 60))
    
    def __post_init__(self):
        # Cargar webhooks
        for key, value in os.environ.items():
            if key.startswith('WEBHOOK_'):
                try:
                    group_id = int(key.replace('WEBHOOK_', ''))
                    self.webhooks[group_id] = value
                except ValueError:
                    continue

@dataclass
class DatabaseSettings:
    url: str = os.getenv('DATABASE_URL', 'sqlite:///./replicator.db')
    echo: bool = os.getenv('DATABASE_ECHO', 'false').lower() == 'true'

@dataclass
class Settings:
    """Configuración principal de la aplicación"""
    
    # Configuraciones por módulo
    telegram: TelegramSettings = field(default_factory=TelegramSettings)
    discord: DiscordSettings = field(default_factory=DiscordSettings)
    database: DatabaseSettings = field(default_factory=DatabaseSettings)
    
    # Configuración general
    debug: bool = os.getenv('DEBUG', 'false').lower() == 'true'
    log_level: str = os.getenv('LOG_LEVEL', 'INFO')
    
    # API y servidor
    host: str = os.getenv('HOST', '0.0.0.0')
    port: int = int(os.getenv('PORT', 8000))
    
    # Watermarks
    watermarks_enabled: bool = os.getenv('WATERMARKS_ENABLED', 'true').lower() == 'true'
    watermark_service_url: str = os.getenv('WATERMARK_SERVICE_URL', 'http://localhost:8081')
    
    @property
    def telegram_api_id(self) -> int:
        return self.telegram.api_id
    
    @property  
    def telegram_api_hash(self) -> str:
        return self.telegram.api_hash
    
    @property
    def telegram_phone(self) -> str:
        return self.telegram.phone

# Instancia global
_settings = None

def get_settings() -> Settings:
    """Obtener configuración global"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

# Para compatibilidad
settings = get_settings()
'''
    
    with open("app/config/settings.py", 'w', encoding='utf-8') as f:
        f.write(content.strip())
    print("✅ app/config/settings.py creado")

def create_app_models_database():
    """Crear app/models/database.py"""
    
    content = '''"""
App Models Database
==================
Configuración de base de datos simplificada
"""

import asyncio
from typing import AsyncGenerator
import sqlite3
from pathlib import Path

# Base de datos SQLite simple
DATABASE_PATH = Path("replicator.db")

class DatabaseManager:
    """Gestor de base de datos simplificado"""
    
    def __init__(self):
        self.db_path = DATABASE_PATH
        self._ensure_database()
    
    def _ensure_database(self):
        """Crear base de datos si no existe"""
        if not self.db_path.exists():
            conn = sqlite3.connect(self.db_path)
            
            # Crear tablas básicas
            conn.execute("""
                CREATE TABLE IF NOT EXISTS replication_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    group_id INTEGER,
                    message_type TEXT,
                    status TEXT,
                    processing_time REAL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS configurations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id INTEGER UNIQUE,
                    config_json TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            conn.close()
    
    def get_connection(self):
        """Obtener conexión a la base de datos"""
        return sqlite3.connect(self.db_path)

# Instancia global
db_manager = DatabaseManager()

async def get_db() -> AsyncGenerator:
    """Obtener conexión a base de datos (async)"""
    conn = db_manager.get_connection()
    try:
        yield conn
    finally:
        conn.close()

async def init_database():
    """Inicializar base de datos"""
    try:
        db_manager._ensure_database()
        print("✅ Base de datos inicializada")
        return True
    except Exception as e:
        print(f"❌ Error inicializando base de datos: {e}")
        return False
'''
    
    with open("app/models/database.py", 'w', encoding='utf-8') as f:
        f.write(content.strip())
    print("✅ app/models/database.py creado")

def create_app_services_replicator():
    """Crear app/services/replicator_service.py"""
    
    content = '''"""
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
'''
    
    with open("app/services/replicator_service.py", 'w', encoding='utf-8') as f:
        f.write(content.strip())
    print("✅ app/services/replicator_service.py creado")

def create_app_api_routes():
    """Crear app/api/routes.py"""
    
    content = '''"""
App API Routes
=============
Rutas de la API REST
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from datetime import datetime

from app.config.settings import get_settings

router = APIRouter()
settings = get_settings()

@router.get("/status")
async def get_api_status():
    """Estado de la API"""
    return {
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }

@router.get("/config")
async def get_configuration():
    """Obtener configuración básica (sin datos sensibles)"""
    return {
        "telegram_configured": bool(settings.telegram.api_id and settings.telegram.api_hash),
        "discord_webhooks_count": len(settings.discord.webhooks),
        "watermarks_enabled": settings.watermarks_enabled,
        "debug_mode": settings.debug
    }

@router.get("/groups")
async def get_configured_groups():
    """Obtener grupos configurados"""
    groups = []
    for group_id in settings.discord.webhooks.keys():
        groups.append({
            "group_id": group_id,
            "configured": True
        })
    
    return {"groups": groups}
'''
    
    with open("app/api/routes.py", 'w', encoding='utf-8') as f:
        f.write(content.strip())
    print("✅ app/api/routes.py creado")

def create_app_api_websocket():
    """Crear app/api/websocket.py"""
    
    content = '''"""
App API WebSocket
================
Gestor de WebSocket para comunicación en tiempo real
"""

import json
import asyncio
from typing import List, Dict, Any
from fastapi import WebSocket

class WebSocketManager:
    """Gestor de conexiones WebSocket"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Conectar nuevo cliente"""
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Desconectar cliente"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Enviar mensaje a cliente específico"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception:
            self.disconnect(websocket)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Enviar mensaje a todos los clientes conectados"""
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                disconnected.append(connection)
        
        # Remover conexiones desconectadas
        for connection in disconnected:
            self.disconnect(connection)
    
    def get_client_count(self) -> int:
        """Obtener número de clientes conectados"""
        return len(self.active_connections)
'''
    
    with open("app/api/websocket.py", 'w', encoding='utf-8') as f:
        f.write(content.strip())
    print("✅ app/api/websocket.py creado")

def create_app_utils_logger():
    """Crear app/utils/logger.py"""
    
    content = '''"""
App Utils Logger
===============
Configuración de logging para el sistema
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """Configurar logger para el sistema"""
    
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # Crear directorio de logs si no existe
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # Handler para consola
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        # Handler para archivo
        file_handler = logging.FileHandler(
            logs_dir / f"replicator_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        
        # Añadir handlers
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
        # Configurar nivel
        logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    return logger
'''
    
    with open("app/utils/logger.py", 'w', encoding='utf-8') as f:
        f.write(content.strip())
    print("✅ app/utils/logger.py creado")

def create_templates():
    """Crear templates HTML básicos"""
    
    # Dashboard template
    dashboard_html = '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Telegram-Discord Replicator Dashboard</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            margin: 0;
            padding: 20px;
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        .stat-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(20px);
            border-radius: 16px;
            padding: 20px;
            text-align: center;
        }
        .stat-value {
            font-size: 2rem;
            font-weight: bold;
            display: block;
            margin-bottom: 8px;
        }
        .stat-label {
            font-size: 0.9rem;
            opacity: 0.8;
        }
        .status {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        .status.running { background: rgba(40, 167, 69, 0.8); }
        .status.stopped { background: rgba(220, 53, 69, 0.8); }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📡 Telegram-Discord Replicator</h1>
            <p>Dashboard de Control v2.0</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <span class="stat-value">{{ stats.total_messages or 0 }}</span>
                <span class="stat-label">Mensajes Procesados</span>
            </div>
            <div class="stat-card">
                <span class="stat-value">{{ stats.replicated_messages or 0 }}</span>
                <span class="stat-label">Mensajes Replicados</span>
            </div>
            <div class="stat-card">
                <span class="stat-value">{{ stats.watermarks_applied or 0 }}</span>
                <span class="stat-label">Watermarks Aplicados</span>
            </div>
            <div class="stat-card">
                <span class="stat-value">{{ stats.groups_configured or 0 }}</span>
                <span class="stat-label">Grupos Configurados</span>
            </div>
            <div class="stat-card">
                <span class="stat-value">
                    <span class="status {{ 'running' if stats.is_running else 'stopped' }}">
                        {{ '🟢 Activo' if stats.is_running else '🔴 Detenido' }}
                    </span>
                </span>
                <span class="stat-label">Estado del Sistema</span>
            </div>
        </div>
        
        <div style="text-align: center; margin-top: 40px;">
            <p>🎨 Watermark Service: <a href="http://localhost:8081/dashboard" target="_blank" style="color: #fff;">Abrir Dashboard</a></p>
            <p>📚 API Docs: <a href="/docs" target="_blank" style="color: #fff;">Ver Documentación</a></p>
        </div>
    </div>

    <script>
        // WebSocket para actualizaciones en tiempo real
        const ws = new WebSocket(`ws://${window.location.host}/ws`);
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            console.log('WebSocket message:', data);
            
            if (data.type === 'stats_updated') {
                // Actualizar estadísticas en tiempo real
                location.reload();
            }
        };
        
        ws.onopen = function() {
            console.log('WebSocket conectado');
        };
        
        ws.onclose = function() {
            console.log('WebSocket desconectado');
        };
    </script>
</body>
</html>'''
    
    with open("templates/dashboard.html", 'w', encoding='utf-8') as f:
        f.write(dashboard_html)
    
    # Crear templates adicionales vacíos
    for template in ["routes.html", "accounts.html", "settings.html"]:
        template_content = f'''<!DOCTYPE html>
<html>
<head>
    <title>{template.replace('.html', '').title()}</title>
</head>
<body>
    <h1>{template.replace('.html', '').title()} - En construcción</h1>
    <p><a href="/dashboard">Volver al Dashboard</a></p>
</body>
</html>'''
        with open(f"templates/{template}", 'w', encoding='utf-8') as f:
            f.write(template_content)
    
    print("✅ Templates HTML creados")

def create_services_watermark_client():
    """Crear services/watermark_client.py mejorado"""
    
    content = '''"""
Services - Watermark Client
==========================
Cliente para conectar con el microservicio de watermarks
"""

import aiohttp
import asyncio
from typing import Tuple, Optional

class WatermarkClient:
    """Cliente para el microservicio de watermarks"""
    
    def __init__(self, base_url: str = "http://localhost:8081"):
        self.base_url = base_url
        self.session = None
        self._last_check = None
        self._service_available = False
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def is_service_available(self) -> bool:
        """Verificar si el microservicio está disponible (con cache)"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            async with self.session.get(
                f"{self.base_url}/health", 
                timeout=aiohttp.ClientTimeout(total=3)
            ) as response:
                self._service_available = response.status == 200
                return self._service_available
        except:
            self._service_available = False
            return False
    
    async def process_text(self, group_id: int, text: str) -> Tuple[str, bool]:
        """Procesar texto con watermarks"""
        try:
            if not await self.is_service_available():
                return text, False
            
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            data = aiohttp.FormData()
            data.add_field('group_id', str(group_id))
            data.add_field('text', text)
            
            async with self.session.post(
                f"{self.base_url}/process/text", 
                data=data,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    processed_text = result[1]["processed_text"]
                    was_modified = result[0]["processed"]
                    return processed_text, was_modified
                else:
                    return text, False
        except Exception as e:
            print(f"Error processing text: {e}")
            return text, False
    
    async def process_image(self, group_id: int, image_bytes: bytes) -> Tuple[bytes, bool]:
        """Procesar imagen con watermarks"""
        try:
            if not await self.is_service_available():
                return image_bytes, False
            
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            data = aiohttp.FormData()
            data.add_field('group_id', str(group_id))
            data.add_field('file', image_bytes, filename='image.jpg', content_type='image/jpeg')
            
            async with self.session.post(
                f"{self.base_url}/process/image", 
                data=data,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    processed_bytes = await response.read()
                    was_processed = response.headers.get('X-Processed') == 'True'
                    return processed_bytes, was_processed
                else:
                    return image_bytes, False
        except Exception as e:
            print(f"Error processing image: {e}")
            return image_bytes, False
    
    async def process_video(self, group_id: int, video_bytes: bytes) -> Tuple[bytes, bool]:
        """Procesar video con watermarks"""
        try:
            if not await self.is_service_available():
                return video_bytes, False
            
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            data = aiohttp.FormData()
            data.add_field('group_id', str(group_id))
            data.add_field('file', video_bytes, filename='video.mp4', content_type='video/mp4')
            
            async with self.session.post(
                f"{self.base_url}/process/video", 
                data=data,
                timeout=aiohttp.ClientTimeout(total=120)  # 2 minutos para videos
            ) as response:
                if response.status == 200:
                    processed_bytes = await response.read()
                    was_processed = response.headers.get('X-Processed') == 'True'
                    return processed_bytes, was_processed
                else:
                    return video_bytes, False
        except Exception as e:
            print(f"Error processing video: {e}")
            return video_bytes, False

# Cliente global para uso fácil
watermark_client = WatermarkClient()
'''
    
    with open("services/watermark_client.py", 'w', encoding='utf-8') as f:
        f.write(content.strip())
    print("✅ services/watermark_client.py creado")

def create_requirements():
    """Crear requirements.txt completo"""
    
    content = '''# Dependencias principales del sistema
telethon>=1.24.0
python-dotenv>=0.19.0
aiohttp>=3.8.0

# FastAPI y servidor web
fastapi>=0.68.0
uvicorn[standard]>=0.15.0
jinja2>=3.0.0
python-multipart>=0.0.5

# Base de datos
sqlite3

# Watermarks y multimedia
Pillow>=9.0.0

# Utilidades
python-dateutil>=2.8.0

# Desarrollo (opcional)
pytest>=6.2.0
black>=22.0.0
isort>=5.10.0
'''
    
    with open("requirements.txt", 'w') as f:
        f.write(content.strip())
    print("✅ requirements.txt actualizado")

def create_env_example():
    """Crear .env.example completo"""
    
    content = '''# Configuración de Telegram
TELEGRAM_API_ID=tu_api_id_aqui
TELEGRAM_API_HASH=tu_api_hash_aqui
TELEGRAM_PHONE=+1234567890
TELEGRAM_SESSION=replicator_session

# Webhooks de Discord (uno por cada grupo)
WEBHOOK_-1001234567890=https://discord.com/api/webhooks/tu_webhook_aqui
WEBHOOK_-1009876543210=https://discord.com/api/webhooks/otro_webhook_aqui

# Configuración del servidor
HOST=0.0.0.0
PORT=8000
DEBUG=false

# Base de datos
DATABASE_URL=sqlite:///./replicator.db
DATABASE_ECHO=false

# Configuración de Discord
MAX_FILE_SIZE_MB=8
DISCORD_TIMEOUT=60

# Watermarks
WATERMARKS_ENABLED=true
WATERMARK_SERVICE_URL=http://localhost:8081

# Logging
LOG_LEVEL=INFO

# Filtros (opcional)
SKIP_WORDS=spam,promocion,anuncio
ONLY_WORDS=
MIN_TEXT_LENGTH=0
'''
    
    with open(".env.example", 'w') as f:
        f.write(content.strip())
    print("✅ .env.example creado")
    print("💡 Copia .env.example a .env y configura tus valores")

def create_init_files():
    """Crear todos los archivos __init__.py necesarios"""
    
    init_files = [
        "app/__init__.py",
        "app/config/__init__.py", 
        "app/models/__init__.py",
        "app/services/__init__.py",
        "app/api/__init__.py",
        "app/utils/__init__.py",
        "services/__init__.py",
        "services/watermark/__init__.py",
        "api/__init__.py",
        "utils/__init__.py"
    ]
    
    for init_file in init_files:
        Path(init_file).touch()
    
    print("✅ Archivos __init__.py creados")

def create_startup_script():
    """Crear script de inicio completo"""
    
    content = '''#!/usr/bin/env python3
"""
Startup Script - Iniciar sistema completo
========================================
Script para iniciar tanto el main.py como el microservicio de watermarks
"""

import os
import sys
import subprocess
import time
import signal
from pathlib import Path

def start_watermark_service():
    """Iniciar microservicio de watermarks"""
    if Path("watermark_service.py").exists():
        print("🎨 Iniciando Watermark Microservice...")
        return subprocess.Popen([
            sys.executable, "watermark_service.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        print("⚠️ watermark_service.py no encontrado")
        return None

def start_main_application():
    """Iniciar aplicación principal"""
    print("🚀 Iniciando aplicación principal...")
    return subprocess.Popen([
        sys.executable, "main.py"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def main():
    """Función principal"""
    print("🔧 Iniciando sistema completo...")
    
    processes = []
    
    try:
        # Iniciar microservicio de watermarks
        watermark_process = start_watermark_service()
        if watermark_process:
            processes.append(("Watermark Service", watermark_process))
            time.sleep(3)  # Esperar a que inicie
        
        # Iniciar aplicación principal
        main_process = start_main_application()
        processes.append(("Main Application", main_process))
        
        print("✅ Sistema iniciado completamente")
        print("🌐 Dashboard principal: http://localhost:8000/dashboard")
        print("🎨 Watermark dashboard: http://localhost:8081/dashboard")
        print("📚 API Docs: http://localhost:8000/docs")
        print("\nPresiona Ctrl+C para detener...")
        
        # Esperar a que terminen los procesos
        for name, process in processes:
            process.wait()
    
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo sistema...")
        
        for name, process in processes:
            print(f"   Deteniendo {name}...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        
        print("👋 Sistema detenido")

if __name__ == "__main__":
    main()
'''
    
    with open("start_system.py", 'w') as f:
        f.write(content.strip())
    
    # Hacer ejecutable en sistemas Unix
    try:
        os.chmod("start_system.py", 0o755)
    except:
        pass
    
    print("✅ start_system.py creado")

def main():
    """Función principal del setup"""
    print("🚀 Creando estructura completa para tu main.py...")
    print("=" * 70)
    
    # Crear estructura completa
    create_complete_structure()
    create_app_config_settings()
    create_app_models_database()
    create_app_services_replicator()
    create_app_api_routes()
    create_app_api_websocket()
    create_app_utils_logger()
    create_templates()
    create_services_watermark_client()
    create_requirements()
    create_env_example()
    create_init_files()
    create_startup_script()
    
    print("=" * 70)
    print("✅ Estructura completa creada exitosamente!")
    print()
    print("📋 Pasos siguientes:")
    print("1. Configurar .env: cp .env.example .env && nano .env")
    print("2. Instalar dependencias: pip install -r requirements.txt")
    print("3. Probar main.py: python main.py")
    print("4. (Opcional) Crear microservicio: [copiar watermark_service.py]")
    print("5. (Opcional) Iniciar todo: python start_system.py")
    print()
    print("🌐 URLs después del inicio:")
    print("   Dashboard principal: http://localhost:8000/dashboard")
    print("   Watermark dashboard: http://localhost:8081/dashboard")
    print("   API Docs: http://localhost:8000/docs")
    print()
    print("💡 Tu main.py ahora debería funcionar sin errores!")

if __name__ == "__main__":
    main()
