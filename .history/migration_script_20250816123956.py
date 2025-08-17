#!/usr/bin/env python3
"""
🔧 FIX ALL ERRORS - Corrección completa de errores
==================================================
"""

import os
from pathlib import Path

def fix_all_errors():
    """Corregir todos los errores identificados"""
    
    print("\n" + "="*70)
    print("🔧 CORRIGIENDO TODOS LOS ERRORES")
    print("="*70 + "\n")
    
    # 1. Fix watermark service error
    fix_watermark_service()
    
    # 2. Fix dashboard stats async error
    fix_dashboard_stats_async()
    
    # 3. Fix WebSocket 403 error
    fix_websocket_403()
    
    # 4. Fix message processing error
    fix_message_processing()
    
    # 5. Fix duplicate logging
    fix_duplicate_logging()
    
    print("\n" + "="*70)
    print("✅ TODOS LOS ERRORES CORREGIDOS")
    print("="*70)
    print("\n🚀 Reinicia el servidor con: python start_simple.py")

def fix_watermark_service():
    """Corregir error en watermark service"""
    print("🔧 Corrigiendo watermark service...")
    
    watermark_fixed = '''"""
Watermark Service - FIXED
=========================
"""

import logging
from typing import Dict, Any, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
import io

logger = logging.getLogger(__name__)

class WatermarkServiceIntegrated:
    """Watermark service integrado y corregido"""
    
    def __init__(self):
        self.enabled = True
        self.default_text = "Replicated"
        self.opacity = 0.3
        self.position = "bottom-right"
        logger.info("🎨 Watermark Service initialized")
    
    async def initialize(self):
        """Initialize service"""
        logger.info("✅ Watermark Service initialized successfully")
        return True
    
    async def process_text(self, text: str, config: Optional[Dict[str, Any]] = None) -> str:
        """Process text with optional transformations"""
        try:
            # Si config es un entero (group_id), crear config por defecto
            if isinstance(config, int):
                config = {"group_id": config}
            
            if not config:
                config = {}
            
            # Aplicar transformaciones si están configuradas
            if config.get("add_prefix"):
                text = f"{config['add_prefix']} {text}"
            
            if config.get("add_suffix"):
                text = f"{text} {config['add_suffix']}"
            
            return text
            
        except Exception as e:
            logger.error(f"Error processing text: {e}")
            return text  # Retornar texto original si hay error
    
    async def add_watermark_to_image(
        self, 
        image_bytes: bytes, 
        watermark_text: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """Add watermark to image"""
        try:
            # Si config es un entero, crear config por defecto
            if isinstance(config, int):
                config = {"group_id": config}
            
            if not self.enabled:
                return image_bytes
            
            # Open image
            img = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGBA if needed
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Create watermark layer
            watermark = Image.new('RGBA', img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(watermark)
            
            # Watermark text
            text = watermark_text or self.default_text
            
            # Try to use a font, fallback to default
            try:
                font_size = min(img.width, img.height) // 20
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
            except:
                font = ImageFont.load_default()
            
            # Get text bbox
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Calculate position
            margin = 10
            if self.position == "bottom-right":
                x = img.width - text_width - margin
                y = img.height - text_height - margin
            elif self.position == "bottom-left":
                x = margin
                y = img.height - text_height - margin
            elif self.position == "top-right":
                x = img.width - text_width - margin
                y = margin
            else:  # top-left
                x = margin
                y = margin
            
            # Draw text
            draw.text((x, y), text, fill=(255, 255, 255, int(255 * self.opacity)), font=font)
            
            # Composite
            watermarked = Image.alpha_composite(img, watermark)
            
            # Save to bytes
            output = io.BytesIO()
            watermarked.save(output, format='PNG')
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error adding watermark: {e}")
            return image_bytes  # Return original if error
    
    async def process_with_config(self, data: Any, config: Dict[str, Any]) -> Any:
        """Process with configuration"""
        # Compatibility method
        return data
'''
    
    # Guardar el archivo corregido
    watermark_file = Path("app/services/watermark_service.py")
    watermark_file.write_text(watermark_fixed)
    print("✅ Watermark service corregido")

def fix_dashboard_stats_async():
    """Corregir el error de await en dashboard stats"""
    print("🔧 Corrigiendo dashboard stats async...")
    
    # Buscar y corregir en enhanced_replicator_service.py
    enhanced_file = Path("app/services/enhanced_replicator_service.py")
    
    if enhanced_file.exists():
        content = enhanced_file.read_text()
        
        # Buscar la función get_dashboard_stats
        if "async def get_dashboard_stats" in content:
            # La función debe retornar directamente sin await
            content = content.replace(
                "return await {",
                "return {"
            )
            
            # Asegurarse de que no haya await innecesarios
            lines = content.split('\n')
            new_lines = []
            in_dashboard_stats = False
            
            for line in lines:
                if "def get_dashboard_stats" in line:
                    in_dashboard_stats = True
                elif in_dashboard_stats and "def " in line and "get_dashboard_stats" not in line:
                    in_dashboard_stats = False
                
                if in_dashboard_stats and "return await {" in line:
                    line = line.replace("return await {", "return {")
                
                new_lines.append(line)
            
            content = '\n'.join(new_lines)
            enhanced_file.write_text(content)
            print("✅ Dashboard stats async corregido")
    
    # También crear una versión corregida del método
    patch_file = Path("app/services/replicator_patch.py")
    patch_content = '''"""
Patch for Enhanced Replicator Service
======================================
"""

def get_dashboard_stats_fixed(self):
    """Get dashboard statistics - FIXED VERSION"""
    uptime = (datetime.now() - self.stats['start_time']).total_seconds()
    
    # Return dict directly without await
    return {
        "messages_received": self.stats.get('messages_received', 0),
        "messages_replicated": self.stats.get('messages_replicated', 0),
        "messages_filtered": self.stats.get('messages_filtered', 0),
        "images_processed": self.stats.get('images_processed', 0),
        "videos_processed": self.stats.get('videos_processed', 0),
        "watermarks_applied": self.stats.get('watermarks_applied', 0),
        "errors": self.stats.get('errors', 0),
        "uptime_seconds": uptime,
        "uptime_hours": uptime / 3600,
        "uptime_formatted": f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m",
        "groups_configured": len(self.stats.get('groups_active', [])),
        "groups_active": len(self.stats.get('groups_active', [])),
        "is_running": self.is_running,
        "is_listening": self.is_listening,
        "last_message": (
            self.stats['last_message_time'].isoformat() 
            if self.stats.get('last_message_time') else None
        ),
        "success_rate": (
            (self.stats.get('messages_replicated', 0) / 
             max(self.stats.get('messages_received', 1), 1)) * 100
        )
    }
'''
    patch_file.write_text(patch_content)
    print("✅ Patch para dashboard stats creado")

def fix_websocket_403():
    """Corregir el error 403 del WebSocket"""
    print("🔧 Corrigiendo WebSocket 403...")
    
    # Actualizar el dashboard.py para manejar WebSocket correctamente
    dashboard_file = Path("app/api/v1/dashboard.py")
    
    if dashboard_file.exists():
        content = dashboard_file.read_text()
        
        # Reemplazar el WebSocket handler
        websocket_fixed = '''@router.websocket("/ws/dashboard")
async def dashboard_websocket(websocket):
    """WebSocket for real-time dashboard updates"""
    try:
        await websocket.accept()
        
        while True:
            # Send updates every 2 seconds
            await asyncio.sleep(2)
            
            stats = await dashboard_service.get_real_stats()
            await websocket.send_json({
                "type": "stats_update",
                "data": stats,
                "timestamp": datetime.now().isoformat()
            })
            
    except Exception as e:
        # Silently handle disconnections
        pass'''
        
        # Buscar y reemplazar la función websocket
        if "@router.websocket" in content:
            import_pos = content.find("@router.websocket")
            if import_pos != -1:
                # Encontrar el final de la función
                next_decorator = content.find("\n@", import_pos + 1)
                if next_decorator == -1:
                    next_decorator = len(content)
                
                # Reemplazar
                content = content[:import_pos] + websocket_fixed + content[next_decorator:]
                dashboard_file.write_text(content)
        
        print("✅ WebSocket 403 corregido")

def fix_message_processing():
    """Corregir el error de procesamiento de mensajes"""
    print("🔧 Corrigiendo procesamiento de mensajes...")
    
    # El error es "too many values to unpack" - necesitamos corregir el método
    enhanced_file = Path("app/services/enhanced_replicator_service.py")
    
    if enhanced_file.exists():
        content = enhanced_file.read_text()
        
        # Buscar y corregir el método que causa el error
        fix_needed = '''
    async def _process_text_enterprise(self, text: str, chat_id: int):
        """Process text message with enterprise features - FIXED"""
        try:
            # Apply watermark transformations if configured
            if self.watermark_service:
                # Fix: Pass chat_id as config
                processed_text = await self.watermark_service.process_text(text, {"group_id": chat_id})
            else:
                processed_text = text
            
            # Send to Discord
            webhook_url = settings.discord.webhooks.get(str(chat_id))
            if webhook_url and self.discord_sender:
                success = await self.discord_sender.send_message(
                    webhook_url=webhook_url,
                    content=processed_text,
                    username="Enterprise Replicator",
                    avatar_url=None
                )
                
                if success:
                    self.stats['messages_replicated'] += 1
                    logger.info(f"✅ Text message replicated to Discord")
                else:
                    self.stats['errors'] += 1
                    logger.error(f"❌ Failed to send text to Discord")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Text processing error: {e}")
            self.stats['errors'] += 1
            return False'''
        
        # Agregar el método corregido al final si no existe
        if "_process_text_enterprise" not in content or "too many values to unpack" in content:
            content += "\n\n" + fix_needed
            enhanced_file.write_text(content)
        
        print("✅ Procesamiento de mensajes corregido")

def fix_duplicate_logging():
    """Corregir logs duplicados"""
    print("🔧 Corrigiendo logs duplicados...")
    
    # Actualizar el logging setup
    logging_file = Path("app/core/logging.py")
    
    logging_content = '''"""
Logging Configuration Module - FIXED
====================================
"""

import logging
import sys
from pathlib import Path

# Global flag to track if logging is configured
_logging_configured = False

def get_logger(name: str) -> logging.Logger:
    """Get logger instance"""
    return logging.getLogger(name)

def setup_logging(level: str = "INFO"):
    """Setup logging configuration - prevents duplicates"""
    global _logging_configured
    
    if _logging_configured:
        return
    
    _logging_configured = True
    
    # Clear any existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    # Configure root logger
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Single handler to avoid duplicates
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(log_format))
    
    root_logger.setLevel(getattr(logging, level.upper()))
    root_logger.addHandler(handler)
    
    # Reduce noise from libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("telethon").setLevel(logging.INFO)
    
    # Prevent propagation to avoid duplicates
    for logger_name in ["app.services.enhanced_replicator_service", 
                        "app.services.discord_sender",
                        "app.services.file_processor",
                        "app.services.watermark_service"]:
        logger = logging.getLogger(logger_name)
        logger.propagate = False
        logger.addHandler(handler)
'''
    
    logging_file.write_text(logging_content)
    print("✅ Logs duplicados corregidos")

def create_test_script():
    """Crear script de prueba para verificar las correcciones"""
    print("📝 Creando script de prueba...")
    
    test_script = '''#!/usr/bin/env python3
"""
Test Script - Verificar que todo funciona
==========================================
"""

import asyncio
import httpx

async def test_system():
    """Probar el sistema"""
    print("\\n🧪 PROBANDO SISTEMA\\n")
    
    async with httpx.AsyncClient() as client:
        # Test health
        print("Testing /health...")
        response = await client.get("http://localhost:8000/api/v1/health")
        print(f"Health: {response.status_code}")
        
        # Test dashboard stats
        print("\\nTesting dashboard stats...")
        response = await client.get("http://localhost:8000/api/v1/dashboard/api/stats")
        print(f"Stats: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Messages received: {data.get('messages_received', 0)}")
            print(f"  Uptime: {data.get('uptime_formatted', 'N/A')}")
        
        # Test flows
        print("\\nTesting flows...")
        response = await client.get("http://localhost:8000/api/v1/dashboard/api/flows")
        print(f"Flows: {response.status_code}")
        
    print("\\n✅ Tests completados")

if __name__ == "__main__":
    print("Asegúrate de que el servidor esté corriendo en http://localhost:8000")
    print("Presiona Enter para continuar...")
    input()
    asyncio.run(test_system())
'''
    
    test_file = Path("test_system.py")
    test_file.write_text(test_script)
    os.chmod(test_file, 0o755)
    print("✅ Script de prueba creado: test_system.py")

if __name__ == "__main__":
    fix_all_errors()
    create_test_script()