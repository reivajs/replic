"""
Enterprise Watermark Service
===========================
Servicio enterprise para aplicación de watermarks

Archivo: app/services/watermark_service.py
"""

import asyncio
import io
import json
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path
from dataclasses import dataclass, field

try:
    from PIL import Image, ImageDraw, ImageFont, ImageEnhance
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from app.utils.logger import setup_logger
from app.config.settings import get_settings

logger = setup_logger(__name__)
settings = get_settings()

@dataclass
class WatermarkConfig:
    """Configuración de watermark por grupo"""
    text_enabled: bool = True
    image_enabled: bool = True
    footer_text: str = "📱 Powered by ReplicBot Enterprise"
    image_text: str = "📱 ReplicBot"
    image_position: str = "bottom-right"  # bottom-right, bottom-left, top-right, top-left, center
    image_opacity: float = 0.7
    text_color: str = "white"
    text_size: int = 24
    text_font: str = "arial"
    background_enabled: bool = False
    background_color: str = "black"
    background_opacity: float = 0.3

@dataclass
class WatermarkStats:
    """Estadísticas de watermarks por grupo"""
    texts_processed: int = 0
    images_processed: int = 0
    videos_processed: int = 0
    total_applied: int = 0
    last_applied: Optional[datetime] = None
    avg_processing_time: float = 0.0

class WatermarkServiceEnterprise:

    """
    🚀 WATERMARK SERVICE ENTERPRISE
    ===============================
    
    Características Enterprise:
    ✅ Configuración per-group granular
    ✅ Múltiples posiciones de watermark
    ✅ Soporte para texto + imagen + fondo
    ✅ Cache de fuentes y configuraciones
    ✅ Procesamiento optimizado con PIL
    ✅ Estadísticas detalladas por grupo
    ✅ Configuración persistente en JSON
    ✅ Fallbacks para dependencias faltantes
    """
    
    def __init__(self):
        self.config_dir = Path("watermark_configs")
        self.assets_dir = Path("watermark_assets")
        self.config_dir.mkdir(exist_ok=True)
        self.assets_dir.mkdir(exist_ok=True)
        
        # Configuraciones por grupo
        self.group_configs: Dict[int, WatermarkConfig] = {}
        self.group_stats: Dict[int, WatermarkStats] = {}
        
        # Cache de fuentes
        self.font_cache: Dict[str, Any] = {}
        
        # Estadísticas globales
        self.global_stats = {
            'total_watermarks_applied': 0,
            'texts_processed': 0,
            'images_processed': 0,
            'videos_processed': 0,
            'groups_configured': 0,
            'start_time': datetime.now(),
            'errors': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        logger.info("🎨 Watermark Service Enterprise inicializado")
    
    async def initialize(self):
        """Inicializar servicio enterprise"""
        try:
            # Cargar configuraciones existentes
            await self._load_configurations()
            
            # Precargar fuentes comunes
            await self._preload_fonts()
            
            # Crear assets básicos si no existen
            await self._create_default_assets()
            
            logger.info("✅ Watermark Service Enterprise inicializado correctamente")
            logger.info(f"   Grupos configurados: {len(self.group_configs)}")
            logger.info(f"   PIL disponible: {'✅' if PIL_AVAILABLE else '❌'}")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando Watermark Service: {e}")
            raise
    
    async def _load_configurations(self):
        """Cargar configuraciones desde archivos"""
        try:
            config_file = self.config_dir / "group_configs.json"
            if config_file.exists():
                with open(config_file, 'r') as f:
                    configs_data = json.load(f)
                
                for group_id_str, config_data in configs_data.items():
                    group_id = int(group_id_str)
                    self.group_configs[group_id] = WatermarkConfig(**config_data)
                
                logger.info(f"📁 Cargadas {len(self.group_configs)} configuraciones")
                
        except Exception as e:
            logger.warning(f"⚠️ Error cargando configuraciones: {e}")
    
    async def _save_configurations(self):
        """Guardar configuraciones en archivo"""
        try:
            config_file = self.config_dir / "group_configs.json"
            configs_data = {}
            
            for group_id, config in self.group_configs.items():
                configs_data[str(group_id)] = {
                    'text_enabled': config.text_enabled,
                    'image_enabled': config.image_enabled,
                    'footer_text': config.footer_text,
                    'image_text': config.image_text,
                    'image_position': config.image_position,
                    'image_opacity': config.image_opacity,
                    'text_color': config.text_color,
                    'text_size': config.text_size,
                    'text_font': config.text_font,
                    'background_enabled': config.background_enabled,
                    'background_color': config.background_color,
                    'background_opacity': config.background_opacity
                }
            
            with open(config_file, 'w') as f:
                json.dump(configs_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"❌ Error guardando configuraciones: {e}")
    
    async def _preload_fonts(self):
        """Precargar fuentes comunes"""
        if not PIL_AVAILABLE:
            return
        
        try:
            common_fonts = [
                ("arial", 24), ("arial", 18), ("arial", 32),
                ("calibri", 24), ("times", 24), ("helvetica", 24)
            ]
            
            for font_name, size in common_fonts:
                cache_key = f"{font_name}_{size}"
                try:
                    if font_name.lower() == "arial":
                        font = ImageFont.truetype("arial.ttf", size)
                    else:
                        font = ImageFont.load_default()
                    
                    self.font_cache[cache_key] = font
                    
                except Exception:
                    # Fallback a fuente por defecto
                    self.font_cache[cache_key] = ImageFont.load_default()
            
            logger.info(f"🔤 Precargadas {len(self.font_cache)} fuentes")
            
        except Exception as e:
            logger.warning(f"⚠️ Error precargando fuentes: {e}")
    
    async def _create_default_assets(self):
        """Crear assets por defecto"""
        try:
            # Crear watermark por defecto si no existe
            default_watermark = self.assets_dir / "default_watermark.png"
            if not default_watermark.exists() and PIL_AVAILABLE:
                # Crear imagen simple de watermark
                img = Image.new('RGBA', (200, 50), (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                
                try:
                    font = ImageFont.truetype("arial.ttf", 20)
                except:
                    font = ImageFont.load_default()
                
                draw.text((10, 15), "ReplicBot", fill=(255, 255, 255, 180), font=font)
                img.save(default_watermark)
                
                logger.info("🖼️ Creado watermark por defecto")
                
        except Exception as e:
            logger.warning(f"⚠️ Error creando assets por defecto: {e}")
    
    def get_group_config(self, chat_id: int) -> WatermarkConfig:
        """Obtener configuración de un grupo"""
        if chat_id not in self.group_configs:
            # Crear configuración por defecto
            self.group_configs[chat_id] = WatermarkConfig()
            asyncio.create_task(self._save_configurations())
        
        return self.group_configs[chat_id]
    
    def get_group_stats(self, chat_id: int) -> WatermarkStats:
        """Obtener estadísticas de un grupo"""
        if chat_id not in self.group_stats:
            self.group_stats[chat_id] = WatermarkStats()
        
        return self.group_stats[chat_id]
    
    async def process_text(self, text: str, chat_id: int) -> Tuple[str, bool]:
        """✅ Procesar texto con watermark enterprise"""
        start_time = datetime.now()
        
        try:
            config = self.get_group_config(chat_id)
            stats = self.get_group_stats(chat_id)
            
            if not config.text_enabled or not text.strip():
                return text, False
            
            # Verificar si ya tiene watermark
            if config.footer_text and config.footer_text in text:
                return text, False
            
            # Aplicar watermark de texto
            if config.footer_text:
                processed_text = f"{text}\n\n{config.footer_text}"
                
                # Actualizar estadísticas
                stats.texts_processed += 1
                stats.total_applied += 1
                stats.last_applied = datetime.now()
                
                self.global_stats['texts_processed'] += 1
                self.global_stats['total_watermarks_applied'] += 1
                
                processing_time = (datetime.now() - start_time).total_seconds()
                self._update_avg_processing_time(stats, processing_time)
                
                logger.debug(f"📝 Texto procesado para grupo {chat_id}")
                return processed_text, True
            
            return text, False
            
        except Exception as e:
            self.global_stats['errors'] += 1
            logger.error(f"❌ Error procesando texto para grupo {chat_id}: {e}")
            return text, False
    
    async def apply_image_watermark(self, image_bytes: bytes, chat_id: int) -> Tuple[bytes, bool]:
        """✅ Aplicar watermark a imagen enterprise"""
        start_time = datetime.now()
        
        try:
            config = self.get_group_config(chat_id)
            stats = self.get_group_stats(chat_id)
            
            if not config.image_enabled or not PIL_AVAILABLE:
                return image_bytes, False
            
            # Verificar cache
            cache_key = f"img_{chat_id}_{config.image_text}_{config.image_position}"
            if cache_key in self.font_cache:
                self.global_stats['cache_hits'] += 1
            else:
                self.global_stats['cache_misses'] += 1
            
            # Abrir imagen
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convertir a RGBA si no lo es
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            
            # Crear overlay para watermark
            overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            
            # Configurar fuente
            font_key = f"{config.text_font}_{config.text_size}"
            if font_key in self.font_cache:
                font = self.font_cache[font_key]
            else:
                try:
                    font = ImageFont.truetype(f"{config.text_font}.ttf", config.text_size)
                    self.font_cache[font_key] = font
                except:
                    font = ImageFont.load_default()
                    self.font_cache[font_key] = font
            
            # Calcular posición del texto
            text_bbox = draw.textbbox((0, 0), config.image_text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            # Márgenes
            margin = 20
            
            # Determinar posición
            if config.image_position == "bottom-right":
                x = image.width - text_width - margin
                y = image.height - text_height - margin
            elif config.image_position == "bottom-left":
                x = margin
                y = image.height - text_height - margin
            elif config.image_position == "top-right":
                x = image.width - text_width - margin
                y = margin
            elif config.image_position == "top-left":
                x = margin
                y = margin
            elif config.image_position == "center":
                x = (image.width - text_width) // 2
                y = (image.height - text_height) // 2
            else:
                # Default bottom-right
                x = image.width - text_width - margin
                y = image.height - text_height - margin
            
            # Dibujar fondo si está habilitado
            if config.background_enabled:
                background_padding = 10
                bg_color = self._hex_to_rgba(config.background_color, config.background_opacity)
                
                bg_coords = [
                    x - background_padding,
                    y - background_padding,
                    x + text_width + background_padding,
                    y + text_height + background_padding
                ]
                draw.rectangle(bg_coords, fill=bg_color)
            
            # Dibujar texto con opacidad
            text_color = self._hex_to_rgba(config.text_color, config.image_opacity)
            draw.text((x, y), config.image_text, fill=text_color, font=font)
            
            # Combinar imagen original con overlay
            watermarked = Image.alpha_composite(image, overlay)
            
            # Convertir de vuelta a bytes
            output = io.BytesIO()
            
            # Mantener formato original si es posible
            if image_bytes[:4] == b'\x89PNG':
                watermarked.save(output, format='PNG', optimize=True)
            else:
                # Convertir RGBA a RGB para JPEG
                if watermarked.mode == 'RGBA':
                    rgb_image = Image.new('RGB', watermarked.size, (255, 255, 255))
                    rgb_image.paste(watermarked, mask=watermarked.split()[-1])
                    rgb_image.save(output, format='JPEG', quality=90, optimize=True)
                else:
                    watermarked.save(output, format='JPEG', quality=90, optimize=True)
            
            output.seek(0)
            processed_bytes = output.getvalue()
            
            # Actualizar estadísticas
            stats.images_processed += 1
            stats.total_applied += 1
            stats.last_applied = datetime.now()
            
            self.global_stats['images_processed'] += 1
            self.global_stats['total_watermarks_applied'] += 1
            
            processing_time = (datetime.now() - start_time).total_seconds()
            self._update_avg_processing_time(stats, processing_time)
            
            logger.debug(f"🖼️ Imagen procesada para grupo {chat_id}")
            return processed_bytes, True
            
        except Exception as e:
            self.global_stats['errors'] += 1
            logger.error(f"❌ Error aplicando watermark a imagen para grupo {chat_id}: {e}")
            return image_bytes, False
    
    def _hex_to_rgba(self, hex_color: str, opacity: float) -> Tuple[int, int, int, int]:
        """Convertir color hex a RGBA con opacidad"""
        try:
            # Remover # si existe
            hex_color = hex_color.lstrip('#')
            
            # Convertir a RGB
            if len(hex_color) == 6:
                r = int(hex_color[0:2], 16)
                g = int(hex_color[2:4], 16)
                b = int(hex_color[4:6], 16)
            elif hex_color.lower() == "white":
                r, g, b = 255, 255, 255
            elif hex_color.lower() == "black":
                r, g, b = 0, 0, 0
            elif hex_color.lower() == "red":
                r, g, b = 255, 0, 0
            elif hex_color.lower() == "blue":
                r, g, b = 0, 0, 255
            elif hex_color.lower() == "green":
                r, g, b = 0, 255, 0
            else:
                r, g, b = 255, 255, 255  # Default white
            
            # Aplicar opacidad
            alpha = int(255 * opacity)
            
            return (r, g, b, alpha)
            
        except Exception:
            return (255, 255, 255, int(255 * opacity))  # Default white
    
    def _update_avg_processing_time(self, stats: WatermarkStats, processing_time: float):
        """Actualizar tiempo promedio de procesamiento"""
        if stats.avg_processing_time == 0:
            stats.avg_processing_time = processing_time
        else:
            # Media móvil simple
            stats.avg_processing_time = (stats.avg_processing_time + processing_time) / 2
    
    async def update_group_config(self, chat_id: int, config_updates: Dict[str, Any]) -> bool:
        """Actualizar configuración de un grupo"""
        try:
            config = self.get_group_config(chat_id)
            
            # Actualizar campos válidos
            valid_fields = {
                'text_enabled', 'image_enabled', 'footer_text', 'image_text',
                'image_position', 'image_opacity', 'text_color', 'text_size',
                'text_font', 'background_enabled', 'background_color', 'background_opacity'
            }
            
            for field, value in config_updates.items():
                if field in valid_fields:
                    setattr(config, field, value)
            
            # Guardar configuraciones
            await self._save_configurations()
            
            logger.info(f"⚙️ Configuración actualizada para grupo {chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error actualizando configuración grupo {chat_id}: {e}")
            return False
    
    async def get_group_config_dict(self, chat_id: int) -> Dict[str, Any]:
        """Obtener configuración de grupo como diccionario"""
        config = self.get_group_config(chat_id)
        
        return {
            'text_enabled': config.text_enabled,
            'image_enabled': config.image_enabled,
            'footer_text': config.footer_text,
            'image_text': config.image_text,
            'image_position': config.image_position,
            'image_opacity': config.image_opacity,
            'text_color': config.text_color,
            'text_size': config.text_size,
            'text_font': config.text_font,
            'background_enabled': config.background_enabled,
            'background_color': config.background_color,
            'background_opacity': config.background_opacity
        }
    
    async def get_available_positions(self) -> List[str]:
        """Obtener posiciones disponibles para watermarks"""
        return [
            "top-left", "top-right", "center", 
            "bottom-left", "bottom-right"
        ]
    
    async def get_available_fonts(self) -> List[str]:
        """Obtener fuentes disponibles"""
        return ["arial", "calibri", "times", "helvetica", "default"]
    
    async def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas enterprise completas"""
        uptime = (datetime.now() - self.global_stats['start_time']).total_seconds()
        
        # Estadísticas por grupo
        group_stats_summary = {}
        for group_id, stats in self.group_stats.items():
            group_stats_summary[str(group_id)] = {
                'texts_processed': stats.texts_processed,
                'images_processed': stats.images_processed,
                'total_applied': stats.total_applied,
                'last_applied': stats.last_applied.isoformat() if stats.last_applied else None,
                'avg_processing_time': stats.avg_processing_time
            }
        
        return {
            **self.global_stats,
            'uptime_seconds': uptime,
            'uptime_hours': uptime / 3600,
            'groups_configured': len(self.group_configs),
            'groups_with_stats': len(self.group_stats),
            'cache_hit_rate': (
                (self.global_stats['cache_hits'] / 
                 max(self.global_stats['cache_hits'] + self.global_stats['cache_misses'], 1)) * 100
            ),
            'fonts_cached': len(self.font_cache),
            'pil_available': PIL_AVAILABLE,
            'group_stats': group_stats_summary
        }
    
    async def get_health(self) -> Dict[str, Any]:
        """Health check del servicio"""
        return {
            "status": "healthy",
            "pil_available": PIL_AVAILABLE,
            "groups_configured": len(self.group_configs),
            "fonts_loaded": len(self.font_cache),
            "config_files": {
                "config_dir_exists": self.config_dir.exists(),
                "assets_dir_exists": self.assets_dir.exists(),
                "config_file_exists": (self.config_dir / "group_configs.json").exists()
            },
            "recent_activity": {
                "total_watermarks_applied": self.global_stats['total_watermarks_applied'],
                "errors": self.global_stats['errors']
            }
        }
    
    async def export_configurations(self) -> Dict[str, Any]:
        """Exportar todas las configuraciones"""
        try:
            export_data = {
                'timestamp': datetime.now().isoformat(),
                'version': '3.0',
                'groups': {},
                'global_stats': self.global_stats
            }
            
            for group_id, config in self.group_configs.items():
                export_data['groups'][str(group_id)] = await self.get_group_config_dict(group_id)
            
            return export_data
            
        except Exception as e:
            logger.error(f"❌ Error exportando configuraciones: {e}")
            return {}
    
    async def import_configurations(self, import_data: Dict[str, Any]) -> bool:
        """Importar configuraciones"""
        try:
            if 'groups' not in import_data:
                return False
            
            for group_id_str, config_data in import_data['groups'].items():
                group_id = int(group_id_str)
                await self.update_group_config(group_id, config_data)
            
            logger.info(f"📥 Importadas configuraciones para {len(import_data['groups'])} grupos")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error importando configuraciones: {e}")
            return False
    
    async def reset_group_config(self, chat_id: int) -> bool:
        """Resetear configuración de grupo a valores por defecto"""
        try:
            self.group_configs[chat_id] = WatermarkConfig()
            await self._save_configurations()
            
            logger.info(f"🔄 Configuración reseteada para grupo {chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error reseteando configuración grupo {chat_id}: {e}")
            return False
    
    async def get_preview_image(self, chat_id: int, sample_text: str = "Sample Text") -> Optional[bytes]:
        """Generar preview de watermark para un grupo"""
        if not PIL_AVAILABLE:
            return None
        
        try:
            config = self.get_group_config(chat_id)
            
            # Crear imagen de ejemplo
            preview_img = Image.new('RGBA', (400, 300), (100, 150, 200, 255))
            
            # Añadir texto de ejemplo en el centro
            draw = ImageDraw.Draw(preview_img)
            try:
                center_font = ImageFont.truetype("arial.ttf", 20)
            except:
                center_font = ImageFont.load_default()
            
            draw.text((200, 120), sample_text, fill=(255, 255, 255, 255), 
                     font=center_font, anchor="mm")
            
            # Aplicar watermark usando la función existente
            preview_bytes = io.BytesIO()
            preview_img.save(preview_bytes, format='PNG')
            preview_bytes.seek(0)
            
            watermarked_bytes, _ = await self.apply_image_watermark(
                preview_bytes.getvalue(), chat_id
            )
            
            return watermarked_bytes
            
        except Exception as e:
            logger.error(f"❌ Error generando preview para grupo {chat_id}: {e}")
            return None