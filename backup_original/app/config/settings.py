"""
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