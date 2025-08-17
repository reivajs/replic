"""
Settings Configuration - FIXED
==============================
Configuración centralizada para el sistema
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load .env file
env_path = Path(".env")
if env_path.exists():
    load_dotenv(env_path)

class TelegramSettings:
    """Telegram configuration"""
    def __init__(self):
        self.api_id = int(os.getenv("TELEGRAM_API_ID", "0"))
        self.api_hash = os.getenv("TELEGRAM_API_HASH", "")
        self.phone = os.getenv("TELEGRAM_PHONE", "")
        self.session_name = os.getenv("TELEGRAM_SESSION", "telegram_session")

class DiscordSettings:
    """Discord configuration - FIXED"""
    def __init__(self):
        # Cargar webhooks desde variables de entorno
        self.webhooks = self._load_webhooks()
        self.default_webhook = os.getenv("DISCORD_DEFAULT_WEBHOOK", "")
        self.rate_limit = int(os.getenv("DISCORD_RATE_LIMIT", "5"))
        
    def _load_webhooks(self) -> Dict[int, str]:
        """Cargar webhooks desde variables de entorno"""
        webhooks = {}
        
        # Buscar todas las variables que empiezan con WEBHOOK_
        for key, value in os.environ.items():
            if key.startswith("WEBHOOK_"):
                try:
                    # El formato es WEBHOOK_GROUPID
                    group_id = key.replace("WEBHOOK_", "")
                    
                    # Intentar convertir a int (para IDs de Telegram)
                    if group_id.startswith("-"):
                        group_id_int = int(group_id)
                    else:
                        group_id_int = int(f"-{group_id}")
                    
                    webhooks[group_id_int] = value
                except:
                    pass
        
        # Si no hay webhooks, usar algunos por defecto para testing
        if not webhooks:
            webhooks = {
                -1001234567890: "https://discord.com/api/webhooks/test/test",
            }
        
        return webhooks

class DatabaseSettings:
    """Database configuration"""
    def __init__(self):
        self.url = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")
        self.echo = os.getenv("DB_ECHO", "False").lower() == "true"

class Settings:
    """Main settings class"""
    def __init__(self):
        # App settings
        self.app_name = os.getenv("APP_NAME", "Enterprise Orchestrator")
        self.version = os.getenv("VERSION", "1.0.0")
        self.debug = os.getenv("DEBUG", "True").lower() == "true"
        self.environment = os.getenv("ENVIRONMENT", "development")
        
        # Server settings
        self.host = os.getenv("HOST", "0.0.0.0")
        self.port = int(os.getenv("PORT", "8000"))
        self.workers = int(os.getenv("WORKERS", "1"))
        
        # Services
        self.telegram = TelegramSettings()
        self.discord = DiscordSettings()
        self.database = DatabaseSettings()
        
        # Paths
        self.base_dir = Path(__file__).parent.parent.parent
        self.data_dir = self.base_dir / "data"
        self.logs_dir = self.base_dir / "logs"
        self.temp_dir = self.base_dir / "temp"
        
        # Create directories
        for dir_path in [self.data_dir, self.logs_dir, self.temp_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Features
        self.enable_watermark = os.getenv("ENABLE_WATERMARK", "True").lower() == "true"
        self.enable_file_processing = os.getenv("ENABLE_FILE_PROCESSING", "True").lower() == "true"
        self.enable_direct_send = os.getenv("ENABLE_DIRECT_SEND", "True").lower() == "true"
        
        # Limits
        self.max_file_size = int(os.getenv("MAX_FILE_SIZE", str(25 * 1024 * 1024)))  # 25MB
        self.message_queue_size = int(os.getenv("MESSAGE_QUEUE_SIZE", "1000"))
        self.max_workers = int(os.getenv("MAX_WORKERS", "10"))

# Global instance
_settings = None

def get_settings() -> Settings:
    """Get settings singleton"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

# Para compatibilidad
settings = get_settings()
