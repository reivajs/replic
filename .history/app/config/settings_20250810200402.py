"""
🔧 SETTINGS.PY ENTERPRISE v4.0 - CONFIGURACIÓN OPTIMIZADA
=========================================================
Archivo: app/config/settings.py

✅ Configuración centralizada enterprise
✅ Soporte para microservicios
✅ Variables de entorno optimizadas
✅ Validación de configuración
✅ Configuración dinámica en tiempo real
"""

import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
import logging

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logging.warning("python-dotenv not available, using environment variables only")

# ================ CONFIGURACIONES BASE ================

@dataclass
class TelegramSettings:
    """Configuración de Telegram enterprise"""
    api_id: int = int(os.getenv('TELEGRAM_API_ID', 0))
    api_hash: str = os.getenv('TELEGRAM_API_HASH', '')
    phone: str = os.getenv('TELEGRAM_PHONE', '')
    session_name: str = os.getenv('TELEGRAM_SESSION', 'replicator_enterprise_session')
    device_model: str = os.getenv('TELEGRAM_DEVICE_MODEL', 'Enterprise Replicator v4.0')
    system_version: str = os.getenv('TELEGRAM_SYSTEM_VERSION', 'Enterprise')
    app_version: str = os.getenv('TELEGRAM_APP_VERSION', '4.0')
    lang_code: str = os.getenv('TELEGRAM_LANG_CODE', 'es')
    system_lang_code: str = os.getenv('TELEGRAM_SYSTEM_LANG_CODE', 'es')
    
    def __post_init__(self):
        """Validación de configuración de Telegram"""
        if not self.api_id:
            logging.warning("❌ TELEGRAM_API_ID not configured")
        if not self.api_hash:
            logging.warning("❌ TELEGRAM_API_HASH not configured") 
        if not self.phone:
            logging.warning("❌ TELEGRAM_PHONE not configured")
    
    def is_valid(self) -> bool:
        """Verificar si la configuración es válida"""
        return bool(self.api_id and self.api_hash and self.phone)

@dataclass
class DiscordSettings:
    """Configuración de Discord enterprise"""
    webhooks: Dict[int, str] = field(default_factory=dict)
    max_file_size_mb: int = int(os.getenv('DISCORD_MAX_FILE_SIZE_MB', 8))
    timeout: int = int(os.getenv('DISCORD_TIMEOUT', 120))
    max_retries: int = int(os.getenv('DISCORD_MAX_RETRIES', 5))
    base_delay: float = float(os.getenv('DISCORD_BASE_DELAY', 2.0))
    max_delay: float = float(os.getenv('DISCORD_MAX_DELAY', 30.0))
    rate_limit_buffer: float = float(os.getenv('DISCORD_RATE_LIMIT_BUFFER', 1.5))
    concurrent_requests: int = int(os.getenv('DISCORD_CONCURRENT_REQUESTS', 3))
    
    def __post_init__(self):
        """Cargar webhooks desde variables de entorno"""
        for key, value in os.environ.items():
            if key.startswith('WEBHOOK_'):
                try:
                    # Extraer group_id del formato WEBHOOK_-1234567890
                    group_id_str = key.replace('WEBHOOK_', '')
                    group_id = int(group_id_str)
                    
                    # Validar formato del webhook
                    if value.startswith('https://discord.com/api/webhooks/'):
                        self.webhooks[group_id] = value
                    else:
                        logging.warning(f"❌ Invalid webhook format for {key}: {value[:50]}...")
                        
                except ValueError as e:
                    logging.warning(f"❌ Invalid group ID in {key}: {e}")
    
    def is_valid(self) -> bool:
        """Verificar si la configuración es válida"""
        return len(self.webhooks) > 0
    
    def get_webhook_count(self) -> int:
        """Obtener número de webhooks configurados"""
        return len(self.webhooks)

@dataclass
class DatabaseSettings:
    """Configuración de base de datos enterprise"""
    url: str = os.getenv('DATABASE_URL', 'sqlite:///./replicator_enterprise.db')
    echo: bool = os.getenv('DATABASE_ECHO', 'false').lower() == 'true'
    pool_size: int = int(os.getenv('DATABASE_POOL_SIZE', 5))
    max_overflow: int = int(os.getenv('DATABASE_MAX_OVERFLOW', 10))
    pool_timeout: int = int(os.getenv('DATABASE_POOL_TIMEOUT', 30))
    pool_recycle: int = int(os.getenv('DATABASE_POOL_RECYCLE', 3600))

@dataclass 
class WatermarkSettings:
    """Configuración de watermarks enterprise"""
    enabled: bool = os.getenv('WATERMARKS_ENABLED', 'true').lower() == 'true'
    service_url: str = os.getenv('WATERMARK_SERVICE_URL', 'http://localhost:8081')
    default_text_watermark: str = os.getenv('WATERMARK_DEFAULT_TEXT', 'Enterprise Bot')
    opacity: float = float(os.getenv('WATERMARK_OPACITY', 0.7))
    position: str = os.getenv('WATERMARK_POSITION', 'bottom-right')
    font_size: int = int(os.getenv('WATERMARK_FONT_SIZE', 24))
    font_color: str = os.getenv('WATERMARK_FONT_COLOR', 'white')
    background_color: str = os.getenv('WATERMARK_BACKGROUND_COLOR', 'black')
    
    # Configuración por grupo
    group_watermarks: Dict[int, str] = field(default_factory=dict)
    
    def __post_init__(self):
        """Cargar watermarks por grupo"""
        for key, value in os.environ.items():
            if key.startswith('WATERMARK_GROUP_'):
                try:
                    group_id_str = key.replace('WATERMARK_GROUP_', '')
                    group_id = int(group_id_str)
                    self.group_watermarks[group_id] = value
                except ValueError:
                    logging.warning(f"❌ Invalid group ID in watermark config: {key}")

@dataclass
class FileProcessorSettings:
    """Configuración del procesador de archivos enterprise"""
    enabled: bool = os.getenv('FILE_PROCESSOR_ENABLED', 'true').lower() == 'true'
    service_url: str = os.getenv('FILE_PROCESSOR_SERVICE_URL', 'http://localhost:8082')
    temp_dir: str = os.getenv('FILE_PROCESSOR_TEMP_DIR', './temp')
    max_file_size_mb: int = int(os.getenv('FILE_PROCESSOR_MAX_SIZE_MB', 50))
    video_quality: str = os.getenv('VIDEO_QUALITY', 'medium')  # low, medium, high
    image_quality: int = int(os.getenv('IMAGE_QUALITY', 85))  # 1-100
    pdf_preview_enabled: bool = os.getenv('PDF_PREVIEW_ENABLED', 'true').lower() == 'true'
    audio_bitrate: int = int(os.getenv('AUDIO_BITRATE', 128))  # kbps
    
    def __post_init__(self):
        """Crear directorio temporal si no existe"""
        Path(self.temp_dir).mkdir(parents=True, exist_ok=True)

@dataclass
class LoggingSettings:
    """Configuración de logging enterprise"""
    level: str = os.getenv('LOG_LEVEL', 'INFO').upper()
    format: str = os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s')
    file_enabled: bool = os.getenv('LOG_FILE_ENABLED', 'true').lower() == 'true'
    file_path: str = os.getenv('LOG_FILE_PATH', './logs')
    file_rotation: str = os.getenv('LOG_FILE_ROTATION', 'daily')  # daily, weekly, size
    max_file_size_mb: int = int(os.getenv('LOG_MAX_FILE_SIZE_MB', 10))
    backup_count: int = int(os.getenv('LOG_BACKUP_COUNT', 7))
    console_enabled: bool = os.getenv('LOG_CONSOLE_ENABLED', 'true').lower() == 'true'
    
    def __post_init__(self):
        """Crear directorio de logs si no existe"""
        Path(self.file_path).mkdir(parents=True, exist_ok=True)

@dataclass
class SecuritySettings:
    """Configuración de seguridad enterprise"""
    api_key_required: bool = os.getenv('API_KEY_REQUIRED', 'false').lower() == 'true'
    api_key: str = os.getenv('API_KEY', '')
    cors_origins: List[str] = field(default_factory=lambda: os.getenv('CORS_ORIGINS', '*').split(','))
    rate_limit_enabled: bool = os.getenv('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
    rate_limit_requests: int = int(os.getenv('RATE_LIMIT_REQUESTS', 100))
    rate_limit_window: int = int(os.getenv('RATE_LIMIT_WINDOW', 60))  # seconds
    max_concurrent_connections: int = int(os.getenv('MAX_CONCURRENT_CONNECTIONS', 50))

@dataclass
class PerformanceSettings:
    """Configuración de rendimiento enterprise"""
    max_concurrent_processing: int = int(os.getenv('MAX_CONCURRENT_PROCESSING', 10))
    processing_timeout: int = int(os.getenv('PROCESSING_TIMEOUT', 300))  # seconds
    circuit_breaker_threshold: int = int(os.getenv('CIRCUIT_BREAKER_THRESHOLD', 5))
    circuit_breaker_recovery_timeout: int = int(os.getenv('CIRCUIT_BREAKER_RECOVERY_TIMEOUT', 60))
    retry_attempts: int = int(os.getenv('RETRY_ATTEMPTS', 3))
    retry_base_delay: float = float(os.getenv('RETRY_BASE_DELAY', 1.0))
    retry_max_delay: float = float(os.getenv('RETRY_MAX_DELAY', 30.0))
    memory_limit_mb: int = int(os.getenv('MEMORY_LIMIT_MB', 512))
    cpu_limit_percent: int = int(os.getenv('CPU_LIMIT_PERCENT', 80))

@dataclass
class MonitoringSettings:
    """Configuración de monitoreo enterprise"""
    metrics_enabled: bool = os.getenv('METRICS_ENABLED', 'true').lower() == 'true'
    health_check_interval: int = int(os.getenv('HEALTH_CHECK_INTERVAL', 30))  # seconds
    stats_retention_days: int = int(os.getenv('STATS_RETENTION_DAYS', 30))
    prometheus_enabled: bool = os.getenv('PROMETHEUS_ENABLED', 'false').lower() == 'true'
    prometheus_port: int = int(os.getenv('PROMETHEUS_PORT', 9090))
    alerting_enabled: bool = os.getenv('ALERTING_ENABLED', 'false').lower() == 'true'
    alert_webhook_url: str = os.getenv('ALERT_WEBHOOK_URL', '')

@dataclass
class Settings:
    """
    🔧 CONFIGURACIÓN PRINCIPAL ENTERPRISE
    ====================================
    
    Configuración centralizada para todo el sistema enterprise
    con validación, configuración dinámica y optimizaciones
    """
    
    # ================ CONFIGURACIONES POR MÓDULO ================
    telegram: TelegramSettings = field(default_factory=TelegramSettings)
    discord: DiscordSettings = field(default_factory=DiscordSettings)
    database: DatabaseSettings = field(default_factory=DatabaseSettings)
    watermarks: WatermarkSettings = field(default_factory=WatermarkSettings)
    file_processor: FileProcessorSettings = field(default_factory=FileProcessorSettings)
    logging: LoggingSettings = field(default_factory=LoggingSettings)
    security: SecuritySettings = field(default_factory=SecuritySettings)
    performance: PerformanceSettings = field(default_factory=PerformanceSettings)
    monitoring: MonitoringSettings = field(default_factory=MonitoringSettings)
    
    # ================ CONFIGURACIONES GENERALES ================
    
    # Servidor web
    host: str = os.getenv('HOST', '0.0.0.0')
    port: int = int(os.getenv('PORT', 8000))
    debug: bool = os.getenv('DEBUG', 'false').lower() == 'true'
    environment: str = os.getenv('ENVIRONMENT', 'production')
    
    # Aplicación
    app_name: str = os.getenv('APP_NAME', 'Telegram-Discord Replicator Enterprise')
    app_version: str = os.getenv('APP_VERSION', '4.0.0')
    app_description: str = os.getenv('APP_DESCRIPTION', 'Sistema enterprise de replicación de mensajes multimedia')
    
    # Características enterprise
    watermarks_enabled: bool = os.getenv('WATERMARKS_ENABLED', 'true').lower() == 'true'
    compression_enabled: bool = os.getenv('COMPRESSION_ENABLED', 'true').lower() == 'true'
    preview_generation_enabled: bool = os.getenv('PREVIEW_GENERATION_ENABLED', 'true').lower() == 'true'
    filters_enabled: bool = os.getenv('FILTERS_ENABLED', 'true').lower() == 'true'
    analytics_enabled: bool = os.getenv('ANALYTICS_ENABLED', 'true').lower() == 'true'
    
    # Filtros por defecto
    default_filters: Dict[str, Any] = field(default_factory=lambda: {
        'enabled': os.getenv('FILTERS_ENABLED', 'true').lower() == 'true',
        'min_length': int(os.getenv('FILTER_MIN_LENGTH', 0)),
        'skip_words': [word.strip() for word in os.getenv('FILTER_SKIP_WORDS', '').split(',') if word.strip()],
        'only_words': [word.strip() for word in os.getenv('FILTER_ONLY_WORDS', '').split(',') if word.strip()],
        'skip_users': [int(uid) for uid in os.getenv('FILTER_SKIP_USERS', '').split(',') if uid.strip().isdigit()]
    })
    
    # ================ MÉTODOS DE VALIDACIÓN ================
    
    def validate(self) -> Dict[str, Any]:
        """
        🔍 VALIDACIÓN COMPLETA DE CONFIGURACIÓN
        =======================================
        """
        errors = []
        warnings = []
        
        # Validar Telegram
        if not self.telegram.is_valid():
            errors.append("Telegram configuration is incomplete")
            if not self.telegram.api_id:
                errors.append("TELEGRAM_API_ID is required")
            if not self.telegram.api_hash:
                errors.append("TELEGRAM_API_HASH is required")
            if not self.telegram.phone:
                errors.append("TELEGRAM_PHONE is required")
        
        # Validar Discord
        if not self.discord.is_valid():
            errors.append("Discord configuration is incomplete - no webhooks configured")
        else:
            for group_id, webhook in self.discord.webhooks.items():
                if not webhook.startswith('https://discord.com/api/webhooks/'):
                    warnings.append(f"Invalid webhook format for group {group_id}")
        
        # Validar directorio temporal
        if not Path(self.file_processor.temp_dir).exists():
            try:
                Path(self.file_processor.temp_dir).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create temp directory: {e}")
        
        # Validar directorio de logs
        if not Path(self.logging.file_path).exists():
            try:
                Path(self.logging.file_path).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create logs directory: {e}")
        
        # Validar configuración de seguridad
        if self.security.api_key_required and not self.security.api_key:
            errors.append("API_KEY is required when API_KEY_REQUIRED is true")
        
        # Validar límites de rendimiento
        if self.performance.max_concurrent_processing < 1:
            warnings.append("MAX_CONCURRENT_PROCESSING should be at least 1")
        
        if self.performance.processing_timeout < 30:
            warnings.append("PROCESSING_TIMEOUT should be at least 30 seconds")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'groups_configured': len(self.discord.webhooks),
            'features_enabled': {
                'watermarks': self.watermarks_enabled,
                'compression': self.compression_enabled,
                'preview_generation': self.preview_generation_enabled,
                'filters': self.filters_enabled,
                'analytics': self.analytics_enabled
            }
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """
        📊 RESUMEN DE CONFIGURACIÓN ENTERPRISE
        =====================================
        """
        return {
            'app': {
                'name': self.app_name,
                'version': self.app_version,
                'environment': self.environment,
                'debug': self.debug
            },
            'server': {
                'host': self.host,
                'port': self.port
            },
            'telegram': {
                'configured': self.telegram.is_valid(),
                'api_id': bool(self.telegram.api_id),
                'api_hash': bool(self.telegram.api_hash),
                'phone': bool(self.telegram.phone)
            },
            'discord': {
                'configured': self.discord.is_valid(),
                'webhooks_count': len(self.discord.webhooks),
                'max_file_size_mb': self.discord.max_file_size_mb
            },
            'features': {
                'watermarks': self.watermarks_enabled,
                'compression': self.compression_enabled,
                'preview_generation': self.preview_generation_enabled,
                'filters': self.filters_enabled,
                'analytics': self.analytics_enabled
            },
            'performance': {
                'max_concurrent': self.performance.max_concurrent_processing,
                'timeout': self.performance.processing_timeout,
                'circuit_breaker_threshold': self.performance.circuit_breaker_threshold
            },
            'monitoring': {
                'metrics_enabled': self.monitoring.metrics_enabled,
                'health_check_interval': self.monitoring.health_check_interval,
                'prometheus_enabled': self.monitoring.prometheus_enabled
            }
        }
    
    def update_runtime_config(self, updates: Dict[str, Any]) -> bool:
        """
        🔄 ACTUALIZACIÓN DE CONFIGURACIÓN EN TIEMPO REAL
        ===============================================
        """
        try:
            for key, value in updates.items():
                if hasattr(self, key):
                    setattr(self, key, value)
                elif '.' in key:
                    # Soporte para configuración anidada (ej: "performance.max_concurrent_processing")
                    parts = key.split('.')
                    obj = self
                    for part in parts[:-1]:
                        if hasattr(obj, part):
                            obj = getattr(obj, part)
                        else:
                            return False
                    
                    if hasattr(obj, parts[-1]):
                        setattr(obj, parts[-1], value)
                    else:
                        return False
                else:
                    return False
            
            return True
            
        except Exception as e:
            logging.error(f"❌ Error updating runtime config: {e}")
            return False
    
    def export_config(self) -> Dict[str, Any]:
        """
        📤 EXPORTAR CONFIGURACIÓN COMPLETA (SIN SECRETOS)
        ================================================
        """
        config = {}
        
        # Telegram (sin secretos)
        config['telegram'] = {
            'api_id_configured': bool(self.telegram.api_id),
            'api_hash_configured': bool(self.telegram.api_hash),
            'phone_configured': bool(self.telegram.phone),
            'session_name': self.telegram.session_name,
            'device_model': self.telegram.device_model
        }
        
        # Discord (sin webhooks completos)
        config['discord'] = {
            'webhooks_count': len(self.discord.webhooks),
            'webhook_groups': list(self.discord.webhooks.keys()),
            'max_file_size_mb': self.discord.max_file_size_mb,
            'timeout': self.discord.timeout,
            'max_retries': self.discord.max_retries
        }
        
        # Otras configuraciones (sin datos sensibles)
        config['features'] = {
            'watermarks': self.watermarks_enabled,
            'compression': self.compression_enabled,
            'preview_generation': self.preview_generation_enabled,
            'filters': self.filters_enabled,
            'analytics': self.analytics_enabled
        }
        
        config['performance'] = {
            'max_concurrent_processing': self.performance.max_concurrent_processing,
            'processing_timeout': self.performance.processing_timeout,
            'circuit_breaker_threshold': self.performance.circuit_breaker_threshold
        }
        
        config['server'] = {
            'host': self.host,
            'port': self.port,
            'debug': self.debug,
            'environment': self.environment
        }
        
        return config


# ================ INSTANCIA GLOBAL ================

_settings_instance: Optional[Settings] = None

def get_settings() -> Settings:
    """
    🔧 OBTENER INSTANCIA SINGLETON DE CONFIGURACIÓN
    ===============================================
    """
    global _settings_instance
    
    if _settings_instance is None:
        _settings_instance = Settings()
        
        # Validar configuración al cargar
        validation = _settings_instance.validate()
        if validation['errors']:
            logging.error("❌ Configuration errors found:")
            for error in validation['errors']:
                logging.error(f"   - {error}")
        
        if validation['warnings']:
            logging.warning("⚠️ Configuration warnings:")
            for warning in validation['warnings']:
                logging.warning(f"   - {warning}")
        
        logging.info(f"✅ Configuration loaded - {validation['groups_configured']} groups configured")
    
    return _settings_instance

def reload_settings() -> Settings:
    """
    🔄 RECARGAR CONFIGURACIÓN DESDE VARIABLES DE ENTORNO
    ===================================================
    """
    global _settings_instance
    _settings_instance = None
    return get_settings()

def update_settings(updates: Dict[str, Any]) -> bool:
    """
    🔄 ACTUALIZAR CONFIGURACIÓN EN TIEMPO REAL
    ==========================================
    """
    settings = get_settings()
    return settings.update_runtime_config(updates)


# ================ CONFIGURACIÓN DE LOGGING ================

def setup_logging_from_settings():
    """Configurar logging basado en settings"""
    settings = get_settings()
    
    # Configurar nivel de logging
    level = getattr(logging, settings.logging.level)
    
    # Configurar formato
    formatter = logging.Formatter(settings.logging.format)
    
    # Configurar handlers
    handlers = []
    
    # Console handler
    if settings.logging.console_enabled:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        handlers.append(console_handler)
    
    # File handler
    if settings.logging.file_enabled:
        from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
        
        log_file = Path(settings.logging.file_path) / f"replicator_{datetime.now().strftime('%Y%m%d')}.log"
        
        if settings.logging.file_rotation == 'size':
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=settings.logging.max_file_size_mb * 1024 * 1024,
                backupCount=settings.logging.backup_count
            )
        else:  # daily
            file_handler = TimedRotatingFileHandler(
                log_file,
                when='D',
                interval=1,
                backupCount=settings.logging.backup_count
            )
        
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    
    # Configurar logging root
    logging.basicConfig(
        level=level,
        handlers=handlers,
        force=True
    )

# Importar datetime para logging
from datetime import datetime

# ================ CONFIGURACIÓN AUTOMÁTICA ================

# Configurar logging desde settings al importar
def _auto_configure_logging():
    """Auto-configurar logging al importar el módulo"""
    try:
        setup_logging_from_settings()
    except Exception as e:
        # Fallback a configuración básica si falla
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        logging.getLogger(__name__).warning(f"Failed to setup logging from settings: {e}")

# Auto-configurar al importar
_auto_configure_logging()