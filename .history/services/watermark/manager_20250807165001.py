"""
Services - Watermark Manager v2.0
=================================
Gestor principal de watermarks con soporte completo para PNG + Texto + Video
Arquitectura modular compatible con SaaS scaling
Diseño Apple minimalista + Clean Code
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, Optional, Tuple, Any, List, Union
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import io

# Importaciones opcionales con fallbacks
try:
    from PIL import Image, ImageDraw, ImageFont, ImageEnhance
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import subprocess
    FFMPEG_AVAILABLE = True
except ImportError:
    FFMPEG_AVAILABLE = False

from utils.logger import setup_logger

logger = setup_logger(__name__)

# ============ ENUMS Y CONFIGURACIONES ============

class WatermarkType(Enum):
    """Tipos de watermark soportados"""
    NONE = "none"
    TEXT = "text"
    PNG = "png"
    BOTH = "both"

class Position(Enum):
    """Posiciones para watermarks"""
    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"
    CENTER = "center"
    CUSTOM = "custom"

@dataclass
class WatermarkConfig:
    """Configuración completa de watermark para un grupo"""
    group_id: int
    
    # Tipo de watermark
    watermark_type: WatermarkType = WatermarkType.NONE
    
    # Configuración PNG
    png_enabled: bool = False
    png_path: Optional[str] = None
    png_position: Position = Position.BOTTOM_RIGHT
    png_opacity: float = 0.7
    png_scale: float = 0.15
    png_custom_x: int = 20
    png_custom_y: int = 20
    
    # Configuración Texto
    text_enabled: bool = False
    text_content: str = ""
    text_position: Position = Position.BOTTOM_RIGHT
    text_font_size: int = 32
    text_color: str = "#FFFFFF"
    text_stroke_color: str = "#000000"
    text_stroke_width: int = 2
    text_custom_x: int = 20
    text_custom_y: int = 60
    
    # Configuración Video
    video_enabled: bool = False
    video_max_size_mb: int = 1024  # 1GB
    video_timeout_sec: int = 60
    video_compress: bool = True
    video_quality_crf: int = 23
    
    # Metadatos
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario para JSON"""
        result = asdict(self)
        # Convertir enums a strings
        result['watermark_type'] = self.watermark_type.value
        result['png_position'] = self.png_position.value
        result['text_position'] = self.text_position.value
        result['created_at'] = self.created_at.isoformat()
        result['updated_at'] = self.updated_at.isoformat()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WatermarkConfig':
        """Crear desde diccionario"""
        # Convertir strings a enums
        if 'watermark_type' in data:
            data['watermark_type'] = WatermarkType(data['watermark_type'])
        if 'png_position' in data:
            data['png_position'] = Position(data['png_position'])
        if 'text_position' in data:
            data['text_position'] = Position(data['text_position'])
        if 'created_at' in data:
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data:
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        
        return cls(**data)

@dataclass
class ProcessingStats:
    """Estadísticas de procesamiento"""
    total_processed: int = 0
    images_processed: int = 0
    videos_processed: int = 0
    text_applied: int = 0
    png_applied: int = 0
    errors: int = 0
    avg_processing_time: float = 0.0
    total_processing_time: float = 0.0
    start_time: datetime = datetime.now()

# ============ WATERMARK MANAGER PRINCIPAL ============

class WatermarkManager:
    """
    🎨 Gestor principal de watermarks
    
    Características:
    - Soporte PNG + Texto + Ambos
    - Configuración por grupo
    - Processing de videos con FFmpeg
    - Cache inteligente
    - Stats detalladas
    - SaaS-ready architecture
    """
    
    def __init__(self, config_dir: Path = Path("config"), 
                 watermarks_dir: Path = Path("watermarks"),
                 temp_dir: Path = Path("temp")):
        
        # Directorios
        self.config_dir = Path(config_dir)
        self.watermarks_dir = Path(watermarks_dir)
        self.temp_dir = Path(temp_dir)
        
        # Crear directorios
        for directory in [self.config_dir, self.watermarks_dir, self.temp_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Estado interno
        self.configs: Dict[int, WatermarkConfig] = {}
        self.stats = ProcessingStats()
        self.png_cache: Dict[str, Image.Image] = {}
        
        # Capabilities
        self.can_process_images = PIL_AVAILABLE
        self.can_process_videos = FFMPEG_AVAILABLE
        
        # Cargar configuraciones existentes
        self._load_configurations()
        
        logger.info(f"🎨 WatermarkManager inicializado")
        logger.info(f"   📷 Imágenes: {'✅' if self.can_process_images else '❌'}")
        logger.info(f"   🎬 Videos: {'✅' if self.can_process_videos else '❌'}")
        logger.info(f"   📁 Configuraciones: {len(self.configs)}")
    
    # ============ GESTIÓN DE CONFIGURACIONES ============
    
    def create_group_config(self, group_id: int, **kwargs) -> WatermarkConfig:
        """Crear configuración para un grupo"""
        config = WatermarkConfig(group_id=group_id, **kwargs)
        self.configs[group_id] = config
        self._save_configuration(config)
        
        logger.info(f"📝 Configuración creada para grupo {group_id}")
        return config
    
    def update_group_config(self, group_id: int, **updates) -> Optional[WatermarkConfig]:
        """Actualizar configuración de grupo"""
        if group_id not in self.configs:
            logger.warning(f"⚠️ Grupo {group_id} no tiene configuración")
            return None
        
        config = self.configs[group_id]
        
        # Aplicar actualizaciones
        for key, value in updates.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        config.updated_at = datetime.now()
        self._save_configuration(config)
        
        logger.info(f"📝 Configuración actualizada para grupo {group_id}")
        return config
    
    def get_group_config(self, group_id: int) -> Optional[WatermarkConfig]:
        """Obtener configuración de grupo"""
        return self.configs.get(group_id)
    
    def get_all_configs(self) -> Dict[int, WatermarkConfig]:
        """Obtener todas las configuraciones"""
        return self.configs.copy()
    
    def delete_group_config(self, group_id: int) -> bool:
        """Eliminar configuración de grupo"""
        if group_id not in self.configs:
            return False
        
        del self.configs[group_id]
        config_file = self.config_dir / f"group_{group_id}.json"
        if config_file.exists():
            config_file.unlink()
        
        logger.info(f"🗑️ Configuración eliminada para grupo {group_id}")
        return True
    
    # ============ PROCESAMIENTO DE WATERMARKS ============
    
    async def process_image(self, image_bytes: bytes, group_id: int) -> Tuple[Optional[bytes], bool]:
        """
        Procesar imagen con watermarks
        
        Returns:
            (image_bytes, was_processed)
        """
        start_time = datetime.now()
        
        try:
            config = self.get_group_config(group_id)
            if not config or config.watermark_type == WatermarkType.NONE:
                return image_bytes, False
            
            if not self.can_process_images:
                logger.warning("⚠️ PIL no disponible para procesamiento de imágenes")
                return image_bytes, False
            
            # Cargar imagen
            image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
            original_size = image.size
            
            # Aplicar watermarks según configuración
            if config.watermark_type in [WatermarkType.PNG, WatermarkType.BOTH]:
                if config.png_enabled and config.png_path:
                    image = await self._apply_png_watermark(image, config)
            
            if config.watermark_type in [WatermarkType.TEXT, WatermarkType.BOTH]:
                if config.text_enabled and config.text_content:
                    image = await self._apply_text_watermark(image, config)
            
            # Convertir de vuelta a bytes
            output = io.BytesIO()
            # Convertir a RGB si es necesario para JPEG
            if image.mode == "RGBA":
                # Crear background blanco y pegar la imagen
                background = Image.new("RGB", image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[-1])
                background.save(output, format="JPEG", quality=85, optimize=True)
            else:
                image.save(output, format="JPEG", quality=85, optimize=True)
            
            processed_bytes = output.getvalue()
            
            # Actualizar estadísticas
            processing_time = (datetime.now() - start_time).total_seconds()
            self._update_stats('image', processing_time)
            
            logger.debug(f"🖼️ Imagen procesada para grupo {group_id} en {processing_time:.2f}s")
            return processed_bytes, True
            
        except Exception as e:
            logger.error(f"❌ Error procesando imagen para grupo {group_id}: {e}")
            self.stats.errors += 1
            return image_bytes, False
    
    async def process_video(self, video_bytes: bytes, group_id: int) -> Tuple[Optional[bytes], bool]:
        """
        Procesar video con watermarks usando FFmpeg
        
        Returns:
            (video_bytes, was_processed)
        """
        start_time = datetime.now()
        
        try:
            config = self.get_group_config(group_id)
            if not config or not config.video_enabled or config.watermark_type == WatermarkType.NONE:
                return video_bytes, False
            
            if not self.can_process_videos:
                logger.warning("⚠️ FFmpeg no disponible para procesamiento de videos")
                return video_bytes, False
            
            # Verificar tamaño
            size_mb = len(video_bytes) / (1024 * 1024)
            if size_mb > config.video_max_size_mb:
                logger.warning(f"⚠️ Video demasiado grande: {size_mb:.1f}MB > {config.video_max_size_mb}MB")
                return video_bytes, False
            
            # Archivos temporales
            input_file = self.temp_dir / f"input_{group_id}_{int(datetime.now().timestamp())}.mp4"
            output_file = self.temp_dir / f"output_{group_id}_{int(datetime.now().timestamp())}.mp4"
            
            try:
                # Escribir video de entrada
                with open(input_file, 'wb') as f:
                    f.write(video_bytes)
                
                # Construir comando FFmpeg
                ffmpeg_cmd = await self._build_ffmpeg_command(input_file, output_file, config)
                
                # Ejecutar FFmpeg con timeout
                process = await asyncio.create_subprocess_exec(
                    *ffmpeg_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(), 
                        timeout=config.video_timeout_sec
                    )
                    
                    if process.returncode != 0:
                        logger.error(f"❌ FFmpeg error: {stderr.decode()}")
                        return video_bytes, False
                    
                    # Leer resultado
                    if output_file.exists():
                        with open(output_file, 'rb') as f:
                            processed_bytes = f.read()
                        
                        # Actualizar estadísticas
                        processing_time = (datetime.now() - start_time).total_seconds()
                        self._update_stats('video', processing_time)
                        
                        logger.info(f"🎬 Video procesado para grupo {group_id} en {processing_time:.2f}s")
                        return processed_bytes, True
                    else:
                        logger.error("❌ Archivo de salida no generado")
                        return video_bytes, False
                        
                except asyncio.TimeoutError:
                    logger.error(f"⏰ Timeout procesando video para grupo {group_id}")
                    process.kill()
                    return video_bytes, False
                    
            finally:
                # Limpiar archivos temporales
                for temp_file in [input_file, output_file]:
                    if temp_file.exists():
                        temp_file.unlink()
                        
        except Exception as e:
            logger.error(f"❌ Error procesando video para grupo {group_id}: {e}")
            self.stats.errors += 1
            return video_bytes, False
    
    async def process_text_message(self, message: str, group_id: int) -> Tuple[str, bool]:
        """
        Procesar mensaje de texto añadiendo suffix personalizado
        
        Returns:
            (processed_message, was_processed)
        """
        try:
            config = self.get_group_config(group_id)
            if not config or not config.text_enabled or not config.text_content:
                return message, False
            
            # Agregar texto personalizado
            if config.text_content.strip():
                processed_message = f"{message}\n\n{config.text_content.strip()}"
                
                self.stats.text_applied += 1
                logger.debug(f"📝 Texto personalizado aplicado para grupo {group_id}")
                return processed_message, True
            
            return message, False
            
        except Exception as e:
            logger.error(f"❌ Error procesando texto para grupo {group_id}: {e}")
            return message, False
    
    # ============ MÉTODOS PRIVADOS ============
    
    async def _apply_png_watermark(self, image: Image.Image, config: WatermarkConfig) -> Image.Image:
        """Aplicar watermark PNG a imagen"""
        try:
            # Cargar PNG desde cache o archivo
            png_watermark = await self._load_png_watermark(config.png_path)
            if not png_watermark:
                return image
            
            # Calcular tamaño del watermark
            img_width, img_height = image.size
            watermark_width = int(img_width * config.png_scale)
            watermark_height = int(png_watermark.size[1] * (watermark_width / png_watermark.size[0]))
            
            # Redimensionar watermark
            watermark_resized = png_watermark.resize(
                (watermark_width, watermark_height), 
                Image.Resampling.LANCZOS
            )
            
            # Aplicar opacidad
            if config.png_opacity < 1.0:
                # Crear máscara de opacidad
                if watermark_resized.mode != "RGBA":
                    watermark_resized = watermark_resized.convert("RGBA")
                
                alpha = watermark_resized.split()[-1]
                alpha = alpha.point(lambda x: int(x * config.png_opacity))
                watermark_resized.putalpha(alpha)
            
            # Calcular posición
            x, y = self._calculate_position(
                image.size, 
                watermark_resized.size, 
                config.png_position,
                config.png_custom_x,
                config.png_custom_y
            )
            
            # Aplicar watermark
            if watermark_resized.mode == "RGBA":
                image.paste(watermark_resized, (x, y), watermark_resized)
            else:
                image.paste(watermark_resized, (x, y))
            
            self.stats.png_applied += 1
            return image
            
        except Exception as e:
            logger.error(f"❌ Error aplicando PNG watermark: {e}")
            return image
    
    async def _apply_text_watermark(self, image: Image.Image, config: WatermarkConfig) -> Image.Image:
        """Aplicar watermark de texto a imagen"""
        try:
            draw = ImageDraw.Draw(image)
            
            # Cargar fuente
            try:
                font = ImageFont.truetype("arial.ttf", config.text_font_size)
            except:
                font = ImageFont.load_default()
            
            # Calcular tamaño del texto
            bbox = draw.textbbox((0, 0), config.text_content, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Calcular posición
            x, y = self._calculate_position(
                image.size, 
                (text_width, text_height), 
                config.text_position,
                config.text_custom_x,
                config.text_custom_y
            )
            
            # Dibujar texto con stroke
            if config.text_stroke_width > 0:
                # Stroke
                for adj_x in range(-config.text_stroke_width, config.text_stroke_width + 1):
                    for adj_y in range(-config.text_stroke_width, config.text_stroke_width + 1):
                        if adj_x != 0 or adj_y != 0:
                            draw.text(
                                (x + adj_x, y + adj_y), 
                                config.text_content, 
                                font=font, 
                                fill=config.text_stroke_color
                            )
            
            # Texto principal
            draw.text((x, y), config.text_content, font=font, fill=config.text_color)
            
            return image
            
        except Exception as e:
            logger.error(f"❌ Error aplicando texto watermark: {e}")
            return image
    
    async def _load_png_watermark(self, png_path: str) -> Optional[Image.Image]:
        """Cargar PNG watermark con cache"""
        if not png_path:
            return None
        
        # Verificar cache
        if png_path in self.png_cache:
            return self.png_cache[png_path]
        
        try:
            # Cargar desde archivo
            full_path = self.watermarks_dir / png_path
            if not full_path.exists():
                logger.warning(f"⚠️ PNG watermark no encontrado: {full_path}")
                return None
            
            png_image = Image.open(full_path).convert("RGBA")
            
            # Guardar en cache
            self.png_cache[png_path] = png_image
            
            return png_image
            
        except Exception as e:
            logger.error(f"❌ Error cargando PNG watermark {png_path}: {e}")
            return None
    
    def _calculate_position(self, image_size: Tuple[int, int], 
                          watermark_size: Tuple[int, int], 
                          position: Position,
                          custom_x: int = 0, 
                          custom_y: int = 0) -> Tuple[int, int]:
        """Calcular posición del watermark"""
        img_width, img_height = image_size
        wm_width, wm_height = watermark_size
        
        margin = 20  # Margen por defecto
        
        position_map = {
            Position.TOP_LEFT: (margin, margin),
            Position.TOP_RIGHT: (img_width - wm_width - margin, margin),
            Position.BOTTOM_LEFT: (margin, img_height - wm_height - margin),
            Position.BOTTOM_RIGHT: (img_width - wm_width - margin, img_height - wm_height - margin),
            Position.CENTER: ((img_width - wm_width) // 2, (img_height - wm_height) // 2),
            Position.CUSTOM: (custom_x, custom_y)
        }
        
        return position_map.get(position, position_map[Position.BOTTOM_RIGHT])
    
    async def _build_ffmpeg_command(self, input_file: Path, output_file: Path, 
                                  config: WatermarkConfig) -> List[str]:
        """Construir comando FFmpeg para video watermark"""
        cmd = ["ffmpeg", "-y", "-i", str(input_file)]
        
        filters = []
        
        # Watermark PNG
        if config.watermark_type in [WatermarkType.PNG, WatermarkType.BOTH] and config.png_path:
            png_path = self.watermarks_dir / config.png_path
            if png_path.exists():
                # Calcular posición para FFmpeg
                pos_x, pos_y = self._get_ffmpeg_position(config.png_position, config.png_custom_x, config.png_custom_y)
                
                filters.append(
                    f"movie={png_path}:loop=0,setpts=N/(FRAME_RATE*TB),"
                    f"scale=iw*{config.png_scale}:-1,format=rgba,"
                    f"colorchannelmixer=aa={config.png_opacity}[wm];"
                    f"[0:v][wm]overlay={pos_x}:{pos_y}"
                )
        
        # Watermark de texto
        if config.watermark_type in [WatermarkType.TEXT, WatermarkType.BOTH] and config.text_content:
            pos_x, pos_y = self._get_ffmpeg_position(config.text_position, config.text_custom_x, config.text_custom_y)
            
            text_filter = (
                f"drawtext=text='{config.text_content}':"
                f"fontcolor={config.text_color}:"
                f"fontsize={config.text_font_size}:"
                f"x={pos_x}:y={pos_y}"
            )
            
            if config.text_stroke_width > 0:
                text_filter += f":borderw={config.text_stroke_width}:bordercolor={config.text_stroke_color}"
            
            if filters:
                filters[-1] += f",{text_filter}"
            else:
                filters.append(text_filter)
        
        # Aplicar filtros si existen
        if filters:
            cmd.extend(["-vf", ";".join(filters)])
        
        # Configuración de compresión
        if config.video_compress:
            cmd.extend([
                "-c:v", "libx264",
                "-crf", str(config.video_quality_crf),
                "-preset", "medium",
                "-c:a", "aac",
                "-b:a", "128k"
            ])
        else:
            cmd.extend(["-c", "copy"])
        
        cmd.append(str(output_file))
        return cmd
    
    def _get_ffmpeg_position(self, position: Position, custom_x: int, custom_y: int) -> Tuple[str, str]:
        """Convertir posición a formato FFmpeg"""
        position_map = {
            Position.TOP_LEFT: ("20", "20"),
            Position.TOP_RIGHT: ("W-w-20", "20"),
            Position.BOTTOM_LEFT: ("20", "H-h-20"),
            Position.BOTTOM_RIGHT: ("W-w-20", "H-h-20"),
            Position.CENTER: ("(W-w)/2", "(H-h)/2"),
            Position.CUSTOM: (str(custom_x), str(custom_y))
        }
        
        return position_map.get(position, position_map[Position.BOTTOM_RIGHT])
    
    def _update_stats(self, media_type: str, processing_time: float):
        """Actualizar estadísticas de procesamiento"""
        self.stats.total_processed += 1
        self.stats.total_processing_time += processing_time
        self.stats.avg_processing_time = self.stats.total_processing_time / self.stats.total_processed
        
        if media_type == 'image':
            self.stats.images_processed += 1
        elif media_type == 'video':
            self.stats.videos_processed += 1
    
    def _save_configuration(self, config: WatermarkConfig):
        """Guardar configuración a archivo"""
        try:
            config_file = self.config_dir / f"group_{config.group_id}.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"❌ Error guardando configuración para grupo {config.group_id}: {e}")
    
    def _load_configurations(self):
        """Cargar todas las configuraciones existentes"""
        try:
            for config_file in self.config_dir.glob("group_*.json"):
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    config = WatermarkConfig.from_dict(data)
                    self.configs[config.group_id] = config
                    
                except Exception as e:
                    logger.error(f"❌ Error cargando {config_file}: {e}")
                    
            logger.info(f"📂 {len(self.configs)} configuraciones cargadas")
            
        except Exception as e:
            logger.error(f"❌ Error cargando configuraciones: {e}")
    
    # ============ API PÚBLICA ============
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas completas"""
        return {
            "processing": asdict(self.stats),
            "capabilities": {
                "images": self.can_process_images,
                "videos": self.can_process_videos
            },
            "groups_configured": len(self.configs),
            "cache_size": len(self.png_cache)
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Health check del servicio"""
        return {
            "status": "healthy",
            "capabilities": {
                "images": self.can_process_images,
                "videos": self.can_process_videos,
                "ffmpeg": FFMPEG_AVAILABLE,
                "pillow": PIL_AVAILABLE
            },
            "uptime_seconds": (datetime.now() - self.stats.start_time).total_seconds(),
            "groups_active": len(self.configs)
        }

# ============ FACTORY FUNCTION ============

def create_watermark_manager(config_dir: Path = None, 
                           watermarks_dir: Path = None,
                           temp_dir: Path = None) -> WatermarkManager:
    """
    Factory function para crear WatermarkManager
    Compatible con la estructura existente del proyecto
    """
    return WatermarkManager(
        config_dir=config_dir or Path("config"),
        watermarks_dir=watermarks_dir or Path("watermarks"),
        temp_dir=temp_dir or Path("temp")
    )