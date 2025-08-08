#!/usr/bin/env python3
"""
🔗 Script de Integración con Sistema Existente
============================================
Este script te muestra cómo integrar el Watermark Microservice 
con tu main.py existente sin modificar tu código.

FUNCIONA INDEPENDIENTEMENTE DE TU ESTRUCTURA ACTUAL
"""

import aiohttp
import asyncio
import json
from typing import Optional, Tuple
from pathlib import Path

class WatermarkClient:
    """
    Cliente para conectar con el Watermark Microservice
    Uso en tu main.py existente - SIN MODIFICAR TU CÓDIGO
    """
    
    def __init__(self, microservice_url: str = "http://localhost:8081"):
        self.base_url = microservice_url
        self.session = None
    
    async def __aenter__(self):
        """Context manager para sesión HTTP"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cerrar sesión HTTP"""
        if self.session:
            await self.session.close()
    
    async def is_service_available(self) -> bool:
        """Verificar si el microservicio está disponible"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            async with self.session.get(f"{self.base_url}/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                return response.status == 200
        except:
            return False
    
    async def create_group_config(self, group_id: int, config: dict) -> bool:
        """Crear configuración para un grupo"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            async with self.session.post(
                f"{self.base_url}/api/groups/{group_id}/config",
                json=config
            ) as response:
                return response.status == 200
        except Exception as e:
            print(f"Error creating config for group {group_id}: {e}")
            return False
    
    async def process_text(self, group_id: int, text: str) -> Tuple[str, bool]:
        """
        Procesar mensaje de texto con watermarks
        
        Returns:
            (processed_text, was_modified)
        """
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            data = aiohttp.FormData()
            data.add_field('group_id', str(group_id))
            data.add_field('text', text)
            
            async with self.session.post(f"{self.base_url}/process/text", data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    processed_text = result[1]["processed_text"]
                    was_modified = result[0]["processed"]
                    return processed_text, was_modified
                else:
                    return text, False
        except Exception as e:
            print(f"Error processing text for group {group_id}: {e}")
            return text, False
    
    async def process_image(self, group_id: int, image_bytes: bytes) -> Tuple[bytes, bool]:
        """
        Procesar imagen con watermarks
        
        Returns:
            (processed_image_bytes, was_processed)
        """
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            data = aiohttp.FormData()
            data.add_field('group_id', str(group_id))
            data.add_field('file', image_bytes, filename='image.jpg', content_type='image/jpeg')
            
            async with self.session.post(f"{self.base_url}/process/image", data=data) as response:
                if response.status == 200:
                    processed_bytes = await response.read()
                    was_processed = response.headers.get('X-Processed') == 'True'
                    return processed_bytes, was_processed
                else:
                    return image_bytes, False
        except Exception as e:
            print(f"Error processing image for group {group_id}: {e}")
            return image_bytes, False
    
    async def process_video(self, group_id: int, video_bytes: bytes) -> Tuple[bytes, bool]:
        """
        Procesar video con watermarks
        
        Returns:
            (processed_video_bytes, was_processed)
        """
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            data = aiohttp.FormData()
            data.add_field('group_id', str(group_id))
            data.add_field('file', video_bytes, filename='video.mp4', content_type='video/mp4')
            
            async with self.session.post(f"{self.base_url}/process/video", data=data) as response:
                if response.status == 200:
                    processed_bytes = await response.read()
                    was_processed = response.headers.get('X-Processed') == 'True'
                    return processed_bytes, was_processed
                else:
                    return video_bytes, False
        except Exception as e:
            print(f"Error processing video for group {group_id}: {e}")
            return video_bytes, False
    
    async def upload_watermark(self, group_id: int, image_file: bytes, filename: str) -> bool:
        """Subir watermark PNG para un grupo"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            data = aiohttp.FormData()
            data.add_field('file', image_file, filename=filename, content_type='image/png')
            
            async with self.session.post(f"{self.base_url}/api/groups/{group_id}/upload", data=data) as response:
                return response.status == 200
        except Exception as e:
            print(f"Error uploading watermark for group {group_id}: {e}")
            return False

# ==================== EJEMPLOS DE INTEGRACIÓN ====================

class TelegramIntegrationExample:
    """
    Ejemplo de cómo integrar con tu handler de Telegram existente
    COPIA ESTOS MÉTODOS A TU CLASE PRINCIPAL
    """
    
    def __init__(self):
        self.watermark_client = WatermarkClient()
    
    async def handle_telegram_message_with_watermarks(self, event):
        """
        EJEMPLO: Modifica tu handler existente así
        
        En tu main.py, en tu función handle_message existente, 
        añade estas líneas al final (antes de enviar a Discord)
        """
        chat_id = event.chat_id
        message = event.message
        
        # Verificar si el microservicio está disponible
        service_available = await self.watermark_client.is_service_available()
        if not service_available:
            print("⚠️ Watermark service no disponible, continuando sin watermarks")
            # Continuar con tu lógica original
            return
        
        try:
            if message.text and not message.media:
                # PROCESAR TEXTO
                processed_text, was_modified = await self.watermark_client.process_text(chat_id, message.text)
                
                if was_modified:
                    print(f"📝 Texto procesado para grupo {chat_id}")
                    # Usar processed_text en lugar de message.text al enviar a Discord
                    await self.send_to_discord(chat_id, processed_text)
                else:
                    # Enviar texto original
                    await self.send_to_discord(chat_id, message.text)
            
            elif message.photo:
                # PROCESAR IMAGEN
                print(f"🖼️ Procesando imagen para grupo {chat_id}...")
                
                # Descargar imagen (tu lógica existente)
                image_bytes = await message.download_media(bytes)
                
                # Procesar con watermarks
                processed_bytes, was_processed = await self.watermark_client.process_image(chat_id, image_bytes)
                
                # Procesar caption si existe
                caption = message.text or ""
                if caption:
                    caption, _ = await self.watermark_client.process_text(chat_id, caption)
                
                if was_processed:
                    print(f"✅ Imagen procesada con watermarks para grupo {chat_id}")
                    # Enviar imagen procesada
                    await self.send_image_to_discord(chat_id, processed_bytes, caption)
                else:
                    print(f"📤 Enviando imagen original para grupo {chat_id}")
                    # Enviar imagen original
                    await self.send_image_to_discord(chat_id, image_bytes, caption)
            
            elif message.video or (message.document and message.document.mime_type.startswith('video/')):
                # PROCESAR VIDEO
                print(f"🎬 Procesando video para grupo {chat_id}...")
                
                # Descargar video (tu lógica existente)
                video_bytes = await message.download_media(bytes)
                
                # Procesar con watermarks
                processed_bytes, was_processed = await self.watermark_client.process_video(chat_id, video_bytes)
                
                # Procesar caption si existe
                caption = message.text or ""
                if caption:
                    caption, _ = await self.watermark_client.process_text(chat_id, caption)
                
                if was_processed:
                    print(f"✅ Video procesado con watermarks para grupo {chat_id}")
                    # Enviar video procesado
                    await self.send_video_to_discord(chat_id, processed_bytes, caption)
                else:
                    print(f"📤 Enviando video original para grupo {chat_id}")
                    # Enviar video original
                    await self.send_video_to_discord(chat_id, video_bytes, caption)
            
            else:
                # Otros tipos de mensaje - usar tu lógica existente
                pass
                
        except Exception as e:
            print(f"❌ Error procesando mensaje con watermarks: {e}")
            # Fallback: continuar con tu lógica original
    
    async def send_to_discord(self, chat_id: int, text: str):
        """EJEMPLO: Tu función existente de envío a Discord"""
        # Aquí va tu lógica existente para enviar texto a Discord
        pass
    
    async def send_image_to_discord(self, chat_id: int, image_bytes: bytes, caption: str = ""):
        """EJEMPLO: Tu función existente de envío de imagen a Discord"""
        # Aquí va tu lógica existente para enviar imagen a Discord
        pass
    
    async def send_video_to_discord(self, chat_id: int, video_bytes: bytes, caption: str = ""):
        """EJEMPLO: Tu función existente de envío de video a Discord"""
        # Aquí va tu lógica existente para enviar video a Discord
        pass

# ==================== CONFIGURACIÓN RÁPIDA ====================

async def setup_watermark_configs():
    """
    Script para configurar grupos rápidamente
    EJECUTA ESTO UNA VEZ para configurar tus grupos
    """
    
    # Configuraciones de ejemplo - MODIFICA SEGÚN TUS GRUPOS
    group_configs = {
        -1001234567890: {
            "name": "Mi Canal Principal",
            "watermark_type": "both",  # texto + PNG
            "text_enabled": True,
            "text_content": "📱 Canal: @MiCanal",
            "png_enabled": True,
            "video_enabled": True
        },
        -1009876543210: {
            "name": "Grupo Secundario", 
            "watermark_type": "text",  # solo texto
            "text_enabled": True,
            "text_content": "🎯 Síguenos: @MiCanal",
            "video_enabled": False
        }
    }
    
    async with WatermarkClient() as client:
        # Verificar que el servicio esté disponible
        if not await client.is_service_available():
            print("❌ Watermark microservice no está ejecutándose")
            print("💡 Ejecuta primero: python watermark_service.py")
            return False
        
        print("🎨 Configurando grupos en el Watermark Microservice...")
        
        for group_id, config in group_configs.items():
            success = await client.create_group_config(group_id, config)
            if success:
                print(f"✅ Grupo {group_id} configurado: {config['name']}")
            else:
                print(f"❌ Error configurando grupo {group_id}")
        
        print("🚀 Configuración completada!")
        print("🌐 Dashboard: http://localhost:8081/dashboard")
        return True

# ==================== EJEMPLO DE USO COMPLETO ====================

async def integration_example():
    """
    EJEMPLO COMPLETO de cómo usar el sistema
    """
    
    print("🔗 Ejemplo de Integración con Watermark Microservice")
    print("=" * 60)
    
    # 1. Verificar que el microservicio esté corriendo
    async with WatermarkClient() as client:
        available = await client.is_service_available()
        
        if not available:
            print("❌ Microservicio no disponible")
            print("💡 Inicia el microservicio primero:")
            print("   python watermark_service.py")
            return
        
        print("✅ Microservicio disponible")
        
        # 2. Configurar un grupo de ejemplo
        group_id = -1001234567890
        config = {
            "name": "Grupo de Prueba",
            "watermark_type": "both",
            "text_enabled": True,
            "text_content": "📱 Canal: @TestCanal",
            "png_enabled": True,
            "video_enabled": True
        }
        
        success = await client.create_group_config(group_id, config)
        print(f"📝 Configuración creada: {'✅' if success else '❌'}")
        
        # 3. Ejemplo de procesamiento de texto
        original_text = "Hola mundo, este es un mensaje de prueba"
        processed_text, was_modified = await client.process_text(group_id, original_text)
        
        print(f"\n📝 Procesamiento de Texto:")
        print(f"   Original: {original_text}")
        print(f"   Procesado: {processed_text}")
        print(f"   Modificado: {'✅' if was_modified else '❌'}")
        
        # 4. Ejemplo de procesamiento de imagen (si existe)
        test_image_path = Path("test_image.jpg")
        if test_image_path.exists():
            print(f"\n🖼️ Procesando imagen de prueba...")
            
            with open(test_image_path, 'rb') as f:
                image_bytes = f.read()
            
            processed_bytes, was_processed = await client.process_image(group_id, image_bytes)
            
            if was_processed:
                output_path = Path("test_image_processed.jpg")
                with open(output_path, 'wb') as f:
                    f.write(processed_bytes)
                print(f"   ✅ Imagen procesada guardada en: {output_path}")
            else:
                print(f"   ❌ Imagen no fue procesada")
        
        print(f"\n🌐 Dashboard disponible en: http://localhost:8081/dashboard")

# ==================== INSTRUCCIONES DE USO ====================

USAGE_INSTRUCTIONS = """
🚀 INSTRUCCIONES DE USO - Watermark Microservice
==============================================

PASO 1: Instalar dependencias
-----------------------------
pip install fastapi uvicorn aiohttp python-multipart Pillow

PASO 2: Iniciar el microservicio
-------------------------------
python watermark_service.py

PASO 3: Configurar grupos (OPCIONAL - también se puede hacer desde dashboard)
----------------------------------------------------------------------------
python integrate_with_existing.py --setup

PASO 4: Integrar con tu main.py existente
----------------------------------------
En tu main.py, al INICIO añade:

```python
from integrate_with_existing import WatermarkClient

# Crear cliente global
watermark_client = WatermarkClient()
```

En tu handler de mensajes existente, ANTES de enviar a Discord, añade:

```python
# Para mensajes de texto
if message.text:
    processed_text, modified = await watermark_client.process_text(chat_id, message.text)
    # Usar processed_text en lugar de message.text

# Para imágenes  
if message.photo:
    image_bytes = await message.download_media(bytes)
    processed_bytes, was_processed = await watermark_client.process_image(chat_id, image_bytes)
    # Usar processed_bytes si was_processed=True

# Para videos
if message.video:
    video_bytes = await message.download_media(bytes)
    processed_bytes, was_processed = await watermark_client.process_video(chat_id, video_bytes)
    # Usar processed_bytes si was_processed=True
```

PASO 5: Configurar watermarks
---------------------------
- Ve a: http://localhost:8081/dashboard
- Configura cada grupo con sus watermarks
- Sube archivos PNG si necesitas watermarks de imagen

¡LISTO! Tu sistema funcionará con watermarks sin modificar tu código principal.

VENTAJAS:
✅ Microservicio independiente
✅ No rompe tu código existente  
✅ Dashboard web para configuración
✅ Fácil deployment separado
✅ API REST completa
✅ Escalable horizontalmente

"""

# ==================== MAIN ====================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--setup":
            print("⚙️ Configurando grupos...")
            asyncio.run(setup_watermark_configs())
        elif sys.argv[1] == "--test":
            print("🧪 Ejecutando ejemplo de integración...")
            asyncio.run(integration_example())
        elif sys.argv[1] == "--help":
            print(USAGE_INSTRUCTIONS)
        else:
            print("❌ Opción no reconocida")
            print("Opciones: --setup, --test, --help")
    else:
        print(USAGE_INSTRUCTIONS)
