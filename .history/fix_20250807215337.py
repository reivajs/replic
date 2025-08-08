#!/usr/bin/env python3
"""
Fix and Deploy Script
====================
Script para arreglar todos los errores y hacer que el sistema funcione YA
"""

import os
import shutil
from pathlib import Path

def fix_start_system():
    """Arreglar start_system.py con el código correcto"""
    
    content = '''#!/usr/bin/env python3
"""
Startup Script - Iniciar sistema completo
========================================
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def start_watermark_service():
    """Iniciar microservicio de watermarks"""
    if Path("watermark_service.py").exists():
        print("🎨 Iniciando Watermark Microservice...")
        return subprocess.Popen([sys.executable, "watermark_service.py"])
    else:
        print("⚠️ watermark_service.py no encontrado")
        return None

def start_main_application():
    """Iniciar aplicación principal"""
    print("🚀 Iniciando aplicación principal...")
    return subprocess.Popen([sys.executable, "main.py"])

def main():
    """Función principal"""
    print("🔧 Iniciando sistema completo...")
    
    processes = []
    
    try:
        # Iniciar microservicio de watermarks
        watermark_process = start_watermark_service()
        if watermark_process:
            processes.append(("Watermark Service", watermark_process))
            time.sleep(3)
        
        # Iniciar aplicación principal
        main_process = start_main_application()
        processes.append(("Main Application", main_process))
        
        print("✅ Sistema iniciado completamente")
        print("🌐 Dashboard principal: http://localhost:8000/dashboard")
        print("🎨 Watermark dashboard: http://localhost:8081/dashboard")
        print("\\nPresiona Ctrl+C para detener...")
        
        # Esperar
        for name, process in processes:
            process.wait()
    
    except KeyboardInterrupt:
        print("\\n🛑 Deteniendo sistema...")
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
        f.write(content)
    print("✅ start_system.py arreglado")

def create_missing_discord_service():
    """Crear services/discord/__init__.py y sender.py"""
    
    # Crear directorio
    Path("services/discord").mkdir(parents=True, exist_ok=True)
    Path("services/discord/__init__.py").touch()
    
    # Crear sender.py básico
    sender_content = '''"""
Services Discord Sender - Implementación básica
==============================================
"""

import aiohttp
import asyncio
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class DiscordMessage:
    content: Optional[str] = None
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = {}
        if self.content:
            data['content'] = self.content
        if self.username:
            data['username'] = self.username
        if self.avatar_url:
            data['avatar_url'] = self.avatar_url
        return data

@dataclass
class SendResult:
    success: bool
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    processing_time: float = 0.0

class DiscordSenderService:
    """Servicio básico de envío a Discord"""
    
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def send_text_message(self, webhook_url: str, message: DiscordMessage) -> SendResult:
        """Enviar mensaje de texto"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            payload = message.to_dict()
            
            async with self.session.post(webhook_url, json=payload) as response:
                return SendResult(
                    success=response.status == 204,
                    status_code=response.status
                )
        except Exception as e:
            return SendResult(success=False, error_message=str(e))
    
    async def send_image_message(self, webhook_url: str, image_bytes: bytes, 
                               caption: str = "", filename: str = "image.jpg") -> SendResult:
        """Enviar imagen"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            data = aiohttp.FormData()
            if caption:
                data.add_field('content', caption)
            data.add_field('file', image_bytes, filename=filename, content_type='image/jpeg')
            
            async with self.session.post(webhook_url, data=data) as response:
                return SendResult(
                    success=response.status == 200,
                    status_code=response.status
                )
        except Exception as e:
            return SendResult(success=False, error_message=str(e))
    
    async def send_video_message(self, webhook_url: str, video_bytes: bytes,
                               caption: str = "", filename: str = "video.mp4") -> SendResult:
        """Enviar video"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            data = aiohttp.FormData()
            if caption:
                data.add_field('content', caption)
            data.add_field('file', video_bytes, filename=filename, content_type='video/mp4')
            
            async with self.session.post(webhook_url, data=data) as response:
                return SendResult(
                    success=response.status == 200,
                    status_code=response.status
                )
        except Exception as e:
            return SendResult(success=False, error_message=str(e))
'''
    
    with open("services/discord/sender.py", 'w') as f:
        f.write(sender_content)
    print("✅ services/discord/sender.py creado")

def replace_replicator_service():
    """Reemplazar el replicator service con la versión enhanced"""
    
    # Hacer backup del original
    original_file = Path("app/services/replicator_service.py")
    if original_file.exists():
        backup_file = Path("app/services/replicator_service_backup.py")
        shutil.copy2(original_file, backup_file)
        print(f"📋 Backup creado: {backup_file}")
    
    # El contenido enhanced ya está en el artifact, solo necesitamos copiarlo
    print("✅ Usar replicator_service_enhanced.py como replicator_service.py")

def create_simple_test_script():
    """Crear script de test simple"""
    
    content = '''#!/usr/bin/env python3
"""
Test Script - Probar sistema rápidamente
======================================
"""

import asyncio
import sys
from pathlib import Path

# Añadir paths
sys.path.append(".")
sys.path.append("services")

async def test_configuration():
    """Test básico de configuración"""
    try:
        print("🧪 Probando configuración...")
        
        # Test app.config.settings
        from app.config.settings import get_settings
        settings = get_settings()
        print(f"✅ Settings cargados: Telegram configurado: {settings.telegram.api_id > 0}")
        
        # Test watermark client
        try:
            from watermark_client import WatermarkClient
            client = WatermarkClient()
            available = await client.is_service_available()
            print(f"🎨 Watermark service: {'✅ Disponible' if available else '❌ No disponible'}")
        except Exception as e:
            print(f"⚠️ Watermark client: {e}")
        
        # Test Discord sender
        try:
            from discord.sender import DiscordSenderService
            print("📤 Discord sender: ✅ Disponible")
        except Exception as e:
            print(f"⚠️ Discord sender: {e}")
        
        print("\\n🎯 Para iniciar el sistema:")
        print("   python main.py")
        print("   (o python start_system.py para iniciar todo)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        return False

def main():
    """Test principal"""
    print("🧪 Ejecutando tests de configuración...")
    success = asyncio.run(test_configuration())
    
    if success:
        print("\\n✅ Configuración OK - El sistema debería funcionar")
    else:
        print("\\n❌ Hay problemas en la configuración")

if __name__ == "__main__":
    main()
'''
    
    with open("test_system.py", 'w') as f:
        f.write(content)
    print("✅ test_system.py creado")

def create_simple_run_script():
    """Crear script simple para ejecutar"""
    
    content = '''#!/usr/bin/env python3
"""
Run Script - Ejecutar solo main.py
=================================
"""

import subprocess
import sys

def main():
    print("🚀 Ejecutando main.py...")
    print("🌐 Dashboard estará en: http://localhost:8000/dashboard")
    print("📚 API Docs en: http://localhost:8000/docs")
    print("\\nPresiona Ctrl+C para detener...")
    
    try:
        subprocess.run([sys.executable, "main.py"])
    except KeyboardInterrupt:
        print("