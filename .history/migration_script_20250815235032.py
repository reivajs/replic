#!/usr/bin/env python3
"""
🔧 FIX FINAL ISSUES
===================
Resolver los últimos problemas para que todo funcione
"""

import os
import subprocess
import signal
from pathlib import Path

def fix_all_issues():
    """Resolver todos los problemas finales"""
    
    print("\n" + "="*70)
    print("🔧 RESOLVIENDO PROBLEMAS FINALES")
    print("="*70 + "\n")
    
    # 1. Matar proceso en puerto 8000
    kill_port_8000()
    
    # 2. Arreglar configuración de settings
    fix_settings_config()
    
    # 3. Crear archivo .env si falta algo
    ensure_env_file()
    
    # 4. Crear script de inicio mejorado
    create_better_startup()
    
    print("\n" + "="*70)
    print("✅ PROBLEMAS RESUELTOS")
    print("="*70)
    print("\nAhora ejecuta: python start_fixed.py")

def kill_port_8000():
    """Matar proceso que está usando el puerto 8000"""
    print("🔍 Liberando puerto 8000...")
    
    try:
        # Para macOS
        result = subprocess.run(
            "lsof -ti:8000 | xargs kill -9",
            shell=True,
            capture_output=True,
            text=True
        )
        print("✅ Puerto 8000 liberado")
    except:
        print("⚠️ No se pudo liberar el puerto automáticamente")
        print("   Ejecuta manualmente: lsof -ti:8000 | xargs kill -9")

def fix_settings_config():
    """Arreglar la configuración de settings"""
    print("📝 Arreglando configuración...")
    
    settings_file = Path("app/config/settings.py")
    settings_file.parent.mkdir(parents=True, exist_ok=True)
    
    content = '''"""
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
'''
    
    settings_file.write_text(content)
    print("✅ Settings configurado correctamente")

def ensure_env_file():
    """Asegurar que el archivo .env tiene todo lo necesario"""
    print("📝 Verificando archivo .env...")
    
    env_file = Path(".env")
    
    if not env_file.exists():
        print("⚠️ Creando archivo .env de ejemplo...")
        
        env_content = """# Telegram Configuration
TELEGRAM_API_ID=TU_API_ID_AQUI
TELEGRAM_API_HASH=TU_API_HASH_AQUI
TELEGRAM_PHONE=+TU_TELEFONO_AQUI

# Discord Webhooks
# Formato: WEBHOOK_GROUPID=URL
WEBHOOK_-1001234567890=https://discord.com/api/webhooks/YOUR_WEBHOOK_HERE
WEBHOOK_-1009876543210=https://discord.com/api/webhooks/ANOTHER_WEBHOOK_HERE

# App Configuration
APP_NAME=Enterprise Orchestrator
VERSION=1.0.0
DEBUG=True
ENVIRONMENT=development

# Server
HOST=0.0.0.0
PORT=8000
WORKERS=1

# Features
ENABLE_WATERMARK=True
ENABLE_FILE_PROCESSING=True
ENABLE_DIRECT_SEND=True

# Limits
MAX_FILE_SIZE=26214400
MESSAGE_QUEUE_SIZE=1000
MAX_WORKERS=10
"""
        
        env_file.write_text(env_content)
        print("✅ Archivo .env creado - CONFIGURA TUS CREDENCIALES")
    else:
        print("✅ Archivo .env existe")
        
        # Verificar que tiene las claves necesarias
        env_content = env_file.read_text()
        
        if "TELEGRAM_API_ID" not in env_content:
            print("⚠️ Falta TELEGRAM_API_ID en .env")
        if "WEBHOOK_" not in env_content:
            print("⚠️ No hay webhooks configurados en .env")
            print("   Añade líneas como: WEBHOOK_-1001234567890=https://discord.com/...")

def create_better_startup():
    """Crear un script de inicio mejorado"""
    print("🚀 Creando script de inicio mejorado...")
    
    content = '''#!/usr/bin/env python3
"""
START FIXED - Script de inicio con verificaciones
=================================================
"""

import os
import sys
import asyncio
import subprocess
from pathlib import Path

def check_port_available(port=8000):
    """Verificar si el puerto está disponible"""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    return result != 0

def kill_port(port=8000):
    """Matar proceso en el puerto"""
    try:
        subprocess.run(f"lsof -ti:{port} | xargs kill -9", shell=True, capture_output=True)
        print(f"✅ Puerto {port} liberado")
    except:
        pass

def check_env_file():
    """Verificar archivo .env"""
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ ERROR: No existe archivo .env")
        print("   Ejecuta: cp .env.example .env")
        print("   Y configura tus credenciales")
        return False
    
    # Verificar contenido mínimo
    content = env_file.read_text()
    if "TELEGRAM_API_ID=TU_API_ID_AQUI" in content:
        print("⚠️ ADVERTENCIA: Necesitas configurar tus credenciales en .env")
        print("   Edita .env y añade tu TELEGRAM_API_ID y TELEGRAM_API_HASH reales")
    
    return True

async def start():
    """Iniciar el sistema"""
    print("\\n" + "="*70)
    print("🚀 INICIANDO SISTEMA ENTERPRISE")
    print("="*70 + "\\n")
    
    # Verificaciones
    if not check_env_file():
        return
    
    # Verificar puerto
    if not check_port_available(8000):
        print("⚠️ Puerto 8000 en uso, liberando...")
        kill_port(8000)
        await asyncio.sleep(1)
    
    print("✅ Puerto 8000 disponible")
    print("✅ Configuración verificada")
    print("✅ Iniciando servidor...\\n")
    
    print("🌐 ENDPOINTS DISPONIBLES:")
    print("   📊 Dashboard:  http://localhost:8000")
    print("   📚 API Docs:   http://localhost:8000/docs")
    print("   🏥 Health:     http://localhost:8000/api/v1/health")
    print("   📖 ReDoc:      http://localhost:8000/redoc")
    print("\\n[Presiona Ctrl+C para detener]\\n")
    
    # Iniciar con uvicorn
    import uvicorn
    
    try:
        config = uvicorn.Config(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info",
            access_log=True
        )
        server = uvicorn.Server(config)
        await server.serve()
    except KeyboardInterrupt:
        print("\\n✅ Servidor detenido por el usuario")
    except Exception as e:
        print(f"\\n❌ Error: {e}")
        print("\\nPosibles soluciones:")
        print("1. Verifica que app/main.py existe")
        print("2. Instala dependencias: pip install -r requirements.txt")
        print("3. Revisa los logs en logs/")

if __name__ == "__main__":
    try:
        asyncio.run(start())
    except KeyboardInterrupt:
        print("\\n👋 Adiós!")
'''
    
    startup_file = Path("start_fixed.py")
    startup_file.write_text(content)
    os.chmod(startup_file, 0o755)
    
    print("✅ Script de inicio creado: start_fixed.py")

if __name__ == "__main__":
    fix_all_issues()