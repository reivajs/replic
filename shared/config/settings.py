import os
from dataclasses import dataclass, field
from typing import Dict
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
    
    def __post_init__(self):
        for key, value in os.environ.items():
            if key.startswith('WEBHOOK_'):
                try:
                    group_id = int(key.replace('WEBHOOK_', ''))
                    self.webhooks[group_id] = value
                except ValueError:
                    continue

@dataclass
class Settings:
    telegram: TelegramSettings = field(default_factory=TelegramSettings)
    discord: DiscordSettings = field(default_factory=DiscordSettings)
    debug: bool = os.getenv('DEBUG', 'false').lower() == 'true'
    host: str = os.getenv('HOST', '0.0.0.0')
    port: int = int(os.getenv('PORT', 8000))
    
    @property
    def telegram_api_id(self) -> int:
        return self.telegram.api_id
    
    @property  
    def telegram_api_hash(self) -> str:
        return self.telegram.api_hash
    
    @property
    def telegram_phone(self) -> str:
        return self.telegram.phone

def get_settings() -> Settings:
    return Settings()

settings = get_settings()