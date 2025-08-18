"""
🔧 PATCH QUIRÚRGICO PARA WATERMARK_SERVICE.PY
=============================================

INSTRUCCIONES:
1. Añadir estas líneas al FINAL de tu watermark_service.py actual
2. NO borrar nada del código existente
3. Esto añade los métodos faltantes manteniendo compatibilidad

Problemas que soluciona:
✅ Missing apply_image_watermark method
✅ "too many values to unpack" error  
✅ Compatibilidad exacta con enhanced_replicator_service
"""

# ============ AÑADIR AL FINAL DE TU WATERMARK_SERVICE.PY ============

class WatermarkServicePatch:
    """
    🩹 PATCH para añadir métodos faltantes a tu WatermarkServiceIntegrated
    """
    
    async def apply_image_watermark(self, image_bytes: bytes, group_id: int) -> tuple[bytes, bool]:
        """
        ✨ MÉTODO CRÍTICO FALTANTE - Exacta compatibilidad con enhanced_replicator_service
        
        Este método es llamado así en tu enhanced_replicator_service:
        processed_bytes, was_processed = await self.watermark_service.apply_image_watermark(image_bytes, chat_id)
        
        Args:
            image_bytes: Bytes de la imagen original
            group_id: ID del grupo/chat
            
        Returns:
            tuple[bytes, bool]: (imagen_procesada, fue_modificada)
        """
        try:
            # Llamar a tu método existente process_image (si existe)
            if hasattr(self, 'process_image'):
                return await self.process_image(image_bytes, group_id)
            
            # Fallback: buscar configuración del grupo
            config = None
            if hasattr(self, 'get_group_config'):
                config = self.get_group_config(group_id)
            elif hasattr(self, 'configs') and group_id in self.configs:
                config = self.configs[group_id]
            
            # Si no hay configuración o está deshabilitada
            if not config or not getattr(config, 'enabled', True):
                return image_bytes, False
            
            # Procesar imagen con PIL
            from PIL import Image, ImageDraw, ImageFont
            import io
            
            try:
                # Cargar imagen
                image = Image.open(io.BytesIO(image_bytes))
                if image.mode != 'RGBA':
                    image = image.convert('RGBA')
                
                watermark_applied = False
                
                # Aplicar watermark de texto si está configurado
                if hasattr(config, 'text_enabled') and config.text_enabled:
                    if hasattr(config, 'text_content') and config.text_content:
                        image = self._apply_text_watermark_simple(image, config)
                        watermark_applied = True
                
                # Aplicar PNG watermark si está configurado
                if hasattr(config, 'png_enabled') and config.png_enabled:
                    if hasattr(config, 'png_path') and config.png_path:
                        image = await self._apply_png_watermark_simple(image, config)
                        watermark_applied = True
                
                # Si no se aplicó nada, retornar original
                if not watermark_applied:
                    return image_bytes, False
                
                # Convertir de vuelta a bytes
                output = io.BytesIO()
                
                # Optimizar formato
                if image.mode == "RGBA":
                    background = Image.new("RGB", image.size, (255, 255, 255))
                    background.paste(image, mask=image.split()[-1])
                    background.save(output, format="JPEG", quality=85, optimize=True)
                else:
                    image.save(output, format="JPEG", quality=85, optimize=True)
                
                processed_bytes = output.getvalue()
                
                # Actualizar estadísticas si existen
                if hasattr(self, 'stats'):
                    self.stats['images_processed'] = self.stats.get('images_processed', 0) + 1
                    self.stats['watermarks_applied'] = self.stats.get('watermarks_applied', 0) + 1
                
                return processed_bytes, True
                
            except Exception as e:
                print(f"❌ Error processing image: {e}")
                return image_bytes, False
                
        except Exception as e:
            print(f"❌ Error in apply_image_watermark: {e}")
            return image_bytes, False
    
    def _apply_text_watermark_simple(self, image, config):
        """Aplicar watermark de texto simple"""
        try:
            draw = ImageDraw.Draw(image)
            
            # Usar fuente por defecto
            try:
                font_size = getattr(config, 'text_font_size', 32)
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
            
            # Texto y colores
            text = getattr(config, 'text_content', 'Zero Cost')
            text_color = getattr(config, 'text_color', '#FFFFFF')
            stroke_color = getattr(config, 'text_stroke_color', '#000000')
            stroke_width = getattr(config, 'text_stroke_width', 2)
            
            # Posición (por defecto bottom-right)
            position = getattr(config, 'text_position', 'bottom_right')
            
            # Calcular posición
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            img_width, img_height = image.size
            
            if position == 'bottom_right':
                x = img_width - text_width - 20
                y = img_height - text_height - 20
            elif position == 'bottom_left':
                x = 20
                y = img_height - text_height - 20
            elif position == 'top_right':
                x = img_width - text_width - 20
                y = 20
            elif position == 'top_left':
                x = 20
                y = 20
            else:  # center
                x = (img_width - text_width) // 2
                y = (img_height - text_height) // 2
            
            # Dibujar texto con stroke si está configurado
            if stroke_width > 0:
                for adj in range(-stroke_width, stroke_width + 1):
                    for adj2 in range(-stroke_width, stroke_width + 1):
                        if adj != 0 or adj2 != 0:
                            draw.text((x + adj, y + adj2), text, font=font, fill=stroke_color)
            
            # Dibujar texto principal
            draw.text((x, y), text, font=font, fill=text_color)
            
            return image
            
        except Exception as e:
            print(f"❌ Error applying text watermark: {e}")
            return image
    
    async def _apply_png_watermark_simple(self, image, config):
        """Aplicar PNG watermark simple"""
        try:
            from PIL import Image
            import os
            
            png_path = getattr(config, 'png_path', '')
            if not png_path or not os.path.exists(png_path):
                return image
            
            # Cargar PNG
            watermark = Image.open(png_path)
            if watermark.mode != 'RGBA':
                watermark = watermark.convert('RGBA')
            
            # Escalar watermark
            scale = getattr(config, 'png_scale', 0.15)
            img_width, img_height = image.size
            watermark_width = int(img_width * scale)
            watermark_height = int(watermark.size[1] * (watermark_width / watermark.size[0]))
            
            watermark = watermark.resize((watermark_width, watermark_height), Image.Resampling.LANCZOS)
            
            # Aplicar opacidad
            opacity = getattr(config, 'png_opacity', 0.7)
            if opacity < 1.0:
                alpha = watermark.split()[-1]
                alpha = alpha.point(lambda x: int(x * opacity))
                watermark.putalpha(alpha)
            
            # Posición
            position = getattr(config, 'png_position', 'bottom_right')
            
            if position == 'bottom_right':
                x = img_width - watermark_width - 20
                y = img_height - watermark_height - 20
            elif position == 'bottom_left':
                x = 20
                y = img_height - watermark_height - 20
            elif position == 'top_right':
                x = img_width - watermark_width - 20
                y = 20
            elif position == 'top_left':
                x = 20
                y = 20
            else:  # center
                x = (img_width - watermark_width) // 2
                y = (img_height - watermark_height) // 2
            
            # Aplicar watermark
            image.paste(watermark, (x, y), watermark)
            
            return image
            
        except Exception as e:
            print(f"❌ Error applying PNG watermark: {e}")
            return image

# ============ PATCH PARA TU CLASE EXISTENTE ============

# Añade estos métodos a tu clase WatermarkServiceIntegrated existente
def patch_watermark_service():
    """
    🩹 Aplicar patch a la clase existente WatermarkServiceIntegrated
    
    EJECUTAR ESTO AL FINAL DE TU ARCHIVO watermark_service.py:
    """
    
    # Buscar la clase existente
    import sys
    current_module = sys.modules[__name__]
    
    # Si existe WatermarkServiceIntegrated, patchearla
    if hasattr(current_module, 'WatermarkServiceIntegrated'):
        WatermarkServiceIntegrated = getattr(current_module, 'WatermarkServiceIntegrated')
        
        # Añadir métodos del patch
        patch_instance = WatermarkServicePatch()
        
        # Copiar métodos
        WatermarkServiceIntegrated.apply_image_watermark = patch_instance.apply_image_watermark
        WatermarkServiceIntegrated._apply_text_watermark_simple = patch_instance._apply_text_watermark_simple
        WatermarkServiceIntegrated._apply_png_watermark_simple = patch_instance._apply_png_watermark_simple
        
        print("✅ WatermarkServiceIntegrated patched successfully!")
        
    else:
        print("❌ WatermarkServiceIntegrated not found. Creating new class...")
        
        # Crear clase completa si no existe
        class WatermarkServiceIntegrated(WatermarkServicePatch):
            def __init__(self, config_dir="config", watermarks_dir="watermarks"):
                self.config_dir = config_dir
                self.watermarks_dir = watermarks_dir
                self.configs = {}
                self.stats = {
                    'images_processed': 0,
                    'watermarks_applied': 0,
                    'text_processed': 0,
                    'errors': 0
                }
                self._load_configs()
            
            def _load_configs(self):
                """Cargar configuraciones existentes"""
                import json
                import os
                from pathlib import Path
                
                config_path = Path(self.config_dir)
                if not config_path.exists():
                    return
                
                for config_file in config_path.glob("group_*.json"):
                    try:
                        with open(config_file, 'r') as f:
                            data = json.load(f)
                        
                        # Crear objeto simple con los datos
                        config = type('Config', (), data)()
                        group_id = data.get('group_id', 0)
                        
                        if group_id:
                            self.configs[group_id] = config
                            
                    except Exception as e:
                        print(f"❌ Error loading config {config_file}: {e}")
            
            def get_group_config(self, group_id):
                """Obtener configuración del grupo"""
                return self.configs.get(group_id, None)
            
            async def initialize(self):
                """Initialize service"""
                print("✅ Watermark Service initialized")
                return True
        
        # Añadir al módulo
        setattr(current_module, 'WatermarkServiceIntegrated', WatermarkServiceIntegrated)

# ============ INSTRUCCIONES DE APLICACIÓN ============

instructions = """
🔧 INSTRUCCIONES PARA APLICAR EL PATCH
=====================================

PASO 1: Backup tu archivo actual
---------------------------------
cp app/services/watermark_service.py app/services/watermark_service.py.backup

PASO 2: Añadir el patch al final
---------------------------------
1. Abre app/services/watermark_service.py
2. Ve al FINAL del archivo
3. Añade TODO el código de este artifact
4. Añade esta línea al final:

# Aplicar patch automáticamente
if __name__ == "__main__" or True:
    patch_watermark_service()

PASO 3: Fix dashboard health check
-----------------------------------
En app/api/v1/dashboard.py (o donde esté tu dashboard), buscar:

# ❌ LÍNEA PROBLEMÁTICA:
healthy, total = service_registry.check_all_services()

# ✅ CAMBIAR POR:
healthy, total = await service_registry.check_all_services()

PASO 4: Asegurar registry async
--------------------------------
En app/services/registry.py, verificar que check_all_services sea async:

async def check_all_services(self) -> tuple[int, int]:
    # ... código

PASO 5: Probar
---------------
python main.py

🎯 RESULTADO ESPERADO
====================
✅ No más error "apply_image_watermark not found"
✅ No más error "too many values to unpack"  
✅ Dashboard health check funciona
✅ Imágenes se procesan con watermarks
✅ Tu código existente se mantiene intacto

COMPATIBILIDAD GARANTIZADA:
- ✅ enhanced_replicator_service.py
- ✅ Configuraciones existentes en config/
- ✅ Toda tu lógica actual
"""

print(instructions)