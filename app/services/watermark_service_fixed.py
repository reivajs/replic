"""
🎨 WATERMARK SERVICE - VERSION CORREGIDA
========================================
Servicio modular de watermarks con persistencia para SaaS
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class WatermarkType(Enum):
    NONE = "none"
    TEXT = "text"
    PNG = "png"
    BOTH = "both"

@dataclass
class WatermarkConfig:
    """Configuración de watermark por grupo"""
    group_id: int
    enabled: bool = True
    watermark_type: WatermarkType = WatermarkType.TEXT
    
    # Text watermark
    text_enabled: bool = True
    text_content: str = "🔄 Zero Cost"
    text_position: str = "bottom_right"
    text_font_size: int = 20
    text_opacity: float = 0.8
    text_color: str = "#FFFFFF"
    
    # PNG watermark
    png_enabled: bool = False
    png_path: Optional[str] = None
    png_position: str = "bottom_right"
    png_scale: float = 0.2
    png_opacity: float = 0.7
    
    # Video settings
    video_enabled: bool = True
    video_max_size_mb: int = 50
    
    # Metadata
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

class WatermarkServiceFixed:
    """Servicio de watermarks con persistencia mejorada"""
    
    def __init__(self, config_dir: str = "config/watermarks"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.configs: Dict[int, WatermarkConfig] = {}
        self.stats = {
            'watermarks_applied': 0,
            'images_processed': 0,
            'videos_processed': 0,
            'text_processed': 0,
            'errors': 0,
            'start_time': datetime.now()
        }
        
        # Cargar configuraciones existentes
        self._load_all_configs()
        
        # Verificar PIL
        try:
            from PIL import Image, ImageDraw, ImageFont
            self.has_pil = True
        except ImportError:
            self.has_pil = False
            logger.warning("⚠️ PIL no disponible, watermarks deshabilitados")
        
        logger.info("✅ WatermarkServiceFixed inicializado")
    
    def _load_all_configs(self):
        """Cargar todas las configuraciones desde disco"""
        for config_file in self.config_dir.glob("group_*.json"):
            try:
                with open(config_file, 'r') as f:
                    data = json.load(f)
                    group_id = data['group_id']
                    # Convertir strings a datetime
                    if 'created_at' in data:
                        data['created_at'] = datetime.fromisoformat(data['created_at'])
                    if 'updated_at' in data:
                        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
                    # Convertir watermark_type string a enum
                    if 'watermark_type' in data:
                        data['watermark_type'] = WatermarkType(data['watermark_type'])
                    
                    self.configs[group_id] = WatermarkConfig(**data)
                    logger.debug(f"Cargada config para grupo {group_id}")
            except Exception as e:
                logger.error(f"Error cargando {config_file}: {e}")
    
    def _save_config(self, config: WatermarkConfig):
        """Guardar configuración en disco"""
        config_file = self.config_dir / f"group_{config.group_id}.json"
        
        # Convertir a dict para serialización
        data = asdict(config)
        # Convertir datetime a string
        data['created_at'] = config.created_at.isoformat()
        data['updated_at'] = config.updated_at.isoformat()
        # Convertir enum a string
        data['watermark_type'] = config.watermark_type.value
        
        with open(config_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.debug(f"Config guardada para grupo {config.group_id}")
    
    async def apply_image_watermark(
        self, 
        image_bytes: bytes, 
        config: Optional[Any] = None
    ) -> Tuple[bytes, bool]:
        """
        Aplicar watermark a imagen - COMPATIBLE con enhanced_replicator_service
        
        Returns:
            Tuple[bytes, bool]: (imagen_procesada, fue_aplicado_watermark)
        """
        try:
            # Extraer group_id del config
            group_id = None
            if isinstance(config, int):
                group_id = config
            elif isinstance(config, dict):
                group_id = config.get('group_id')
            elif hasattr(config, 'group_id'):
                group_id = config.group_id
            
            if group_id is None:
                return image_bytes, False
            
            # Obtener o crear configuración
            wm_config = self.get_or_create_config(group_id)
            
            if not wm_config.enabled or not self.has_pil:
                return image_bytes, False
            
            # Aplicar watermark
            processed = await self._apply_watermark_to_image(image_bytes, wm_config)
            
            if processed != image_bytes:
                self.stats['watermarks_applied'] += 1
                self.stats['images_processed'] += 1
                return processed, True
            
            return image_bytes, False
            
        except Exception as e:
            logger.error(f"Error aplicando watermark: {e}")
            self.stats['errors'] += 1
            return image_bytes, False
    
    async def _apply_watermark_to_image(
        self, 
        image_bytes: bytes, 
        config: WatermarkConfig
    ) -> bytes:
        """Aplicación real del watermark"""
        if not self.has_pil:
            return image_bytes
        
        try:
            from PIL import Image, ImageDraw, ImageFont
            import io
            
            # Abrir imagen
            img = Image.open(io.BytesIO(image_bytes))
            
            # Si hay watermark de texto
            if config.text_enabled and config.text_content:
                draw = ImageDraw.Draw(img)
                
                # Calcular posición
                text = config.text_content
                bbox = draw.textbbox((0, 0), text)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                # Posiciones disponibles
                positions = {
                    'top_left': (10, 10),
                    'top_right': (img.width - text_width - 10, 10),
                    'bottom_left': (10, img.height - text_height - 10),
                    'bottom_right': (img.width - text_width - 10, 
                                   img.height - text_height - 10),
                    'center': ((img.width - text_width) // 2, 
                             (img.height - text_height) // 2)
                }
                
                pos = positions.get(config.text_position, positions['bottom_right'])
                
                # Dibujar texto con sombra para mejor visibilidad
                shadow_pos = (pos[0] + 1, pos[1] + 1)
                draw.text(shadow_pos, text, fill=(0, 0, 0, 128))
                draw.text(pos, text, fill=config.text_color)
            
            # Convertir de vuelta a bytes
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=95)
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error procesando imagen: {e}")
            return image_bytes
    
    def get_or_create_config(self, group_id: int) -> WatermarkConfig:
        """Obtener configuración existente o crear nueva"""
        if group_id not in self.configs:
            config = WatermarkConfig(group_id=group_id)
            self.configs[group_id] = config
            self._save_config(config)
            logger.info(f"Nueva configuración creada para grupo {group_id}")
        
        return self.configs[group_id]
    
    def update_config(self, group_id: int, **kwargs) -> WatermarkConfig:
        """Actualizar configuración de un grupo"""
        config = self.get_or_create_config(group_id)
        
        # Actualizar campos
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        config.updated_at = datetime.now()
        self._save_config(config)
        
        logger.info(f"Configuración actualizada para grupo {group_id}")
        return config
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del servicio - NO ASYNC"""
        uptime = (datetime.now() - self.stats['start_time']).total_seconds()
        return {
            'watermarks_applied': self.stats['watermarks_applied'],
            'images_processed': self.stats['images_processed'],
            'videos_processed': self.stats['videos_processed'],
            'text_processed': self.stats['text_processed'],
            'errors': self.stats['errors'],
            'uptime_hours': uptime / 3600,
            'configs_loaded': len(self.configs),
            'status': 'running'
        }
    
    async def process_text(
        self, 
        text: str, 
        config: Optional[Any] = None
    ) -> Tuple[str, bool]:
        """Procesar texto con watermark"""
        try:
            # Extraer group_id
            group_id = None
            if isinstance(config, int):
                group_id = config
            elif isinstance(config, dict):
                group_id = config.get('group_id')
            
            if group_id is None:
                return text, False
            
            wm_config = self.get_or_create_config(group_id)
            
            if wm_config.text_enabled and wm_config.text_content:
                processed_text = f"{text}\n\n{wm_config.text_content}"
                self.stats['text_processed'] += 1
                return processed_text, True
            
            return text, False
            
        except Exception as e:
            logger.error(f"Error procesando texto: {e}")
            return text, False
