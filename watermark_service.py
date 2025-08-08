#!/usr/bin/env python3
"""
🎨 Watermark Microservice v3.0 - Completamente Independiente
==========================================================
Microservicio standalone que funciona independientemente de tu main.py
Expone API REST para que cualquier aplicación lo use

Características:
- ✅ Watermarks PNG personalizables
- ✅ Watermarks de texto por grupo  
- ✅ Procesamiento de videos con FFmpeg
- ✅ Dashboard Apple-style independiente
- ✅ API REST completa
- ✅ Arquitectura microservicio pura
- ✅ No depende de tu código existente
"""

import asyncio
import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from contextlib import asynccontextmanager

# Dependencias externas
try:
    from fastapi import FastAPI, HTTPException, UploadFile, File, Form, WebSocket, WebSocketDisconnect
    from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    from pydantic import BaseModel
except ImportError:
    print("❌ Dependencias faltantes. Instala con:")
    print("pip install fastapi uvicorn python-multipart")
    sys.exit(1)

try:
    from PIL import Image, ImageDraw, ImageFont, ImageEnhance
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️ PIL no disponible - watermarks de imagen deshabilitados")

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    print("⚠️ aiohttp no disponible - algunas funciones limitadas")

# Verificar FFmpeg
try:
    subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    FFMPEG_AVAILABLE = True
except (subprocess.CalledProcessError, FileNotFoundError):
    FFMPEG_AVAILABLE = False
    print("⚠️ FFmpeg no disponible - watermarks de video deshabilitados")

# ==================== CONFIGURACIÓN ====================

# Configuración del microservicio
SERVICE_CONFIG = {
    'name': 'watermark-service',
    'version': '3.0.0',
    'host': os.getenv('WATERMARK_HOST', '0.0.0.0'),
    'port': int(os.getenv('WATERMARK_PORT', 8081)),  # Puerto diferente para no chocar
    'debug': os.getenv('DEBUG', 'false').lower() == 'true',
    'data_dir': Path(os.getenv('WATERMARK_DATA_DIR', 'watermark_data')),
    'max_file_size_mb': int(os.getenv('MAX_FILE_SIZE_MB', 100)),
    'video_timeout_sec': int(os.getenv('VIDEO_TIMEOUT_SEC', 60))
}

# Crear directorios
SERVICE_CONFIG['data_dir'].mkdir(exist_ok=True)
(SERVICE_CONFIG['data_dir'] / 'config').mkdir(exist_ok=True)
(SERVICE_CONFIG['data_dir'] / 'assets').mkdir(exist_ok=True)
(SERVICE_CONFIG['data_dir'] / 'temp').mkdir(exist_ok=True)

# ==================== MODELOS ====================

class WatermarkType(Enum):
    NONE = "none"
    TEXT = "text"
    PNG = "png"
    BOTH = "both"

class Position(Enum):
    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"
    CENTER = "center"
    CUSTOM = "custom"

@dataclass
class GroupConfig:
    """Configuración de watermarks por grupo"""
    group_id: int
    name: str = ""
    
    # Tipo de watermark
    watermark_type: WatermarkType = WatermarkType.NONE
    
    # PNG Settings
    png_enabled: bool = False
    png_filename: Optional[str] = None
    png_position: Position = Position.BOTTOM_RIGHT
    png_opacity: float = 0.7
    png_scale: float = 0.15
    png_custom_x: int = 20
    png_custom_y: int = 20
    
    # Text Settings
    text_enabled: bool = False
    text_content: str = ""
    text_position: Position = Position.BOTTOM_RIGHT
    text_font_size: int = 32
    text_color: str = "#FFFFFF"
    text_stroke_color: str = "#000000"
    text_stroke_width: int = 2
    
    # Video Settings
    video_enabled: bool = False
    video_max_size_mb: int = 100
    video_timeout_sec: int = 60
    video_compress: bool = True
    video_quality: int = 23
    
    # Metadata
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['watermark_type'] = self.watermark_type.value
        result['png_position'] = self.png_position.value
        result['text_position'] = self.text_position.value
        result['created_at'] = self.created_at.isoformat()
        result['updated_at'] = self.updated_at.isoformat()
        return result

# ==================== PYDANTIC MODELS ====================

class GroupConfigRequest(BaseModel):
    group_id: int
    name: str = ""
    watermark_type: str = "none"
    
    # PNG
    png_enabled: bool = False
    png_position: str = "bottom_right"
    png_opacity: float = 0.7
    png_scale: float = 0.15
    png_custom_x: int = 20
    png_custom_y: int = 20
    
    # Text
    text_enabled: bool = False
    text_content: str = ""
    text_position: str = "bottom_right"
    text_font_size: int = 32
    text_color: str = "#FFFFFF"
    text_stroke_color: str = "#000000"
    text_stroke_width: int = 2
    
    # Video
    video_enabled: bool = False
    video_max_size_mb: int = 100
    video_timeout_sec: int = 60
    video_compress: bool = True
    video_quality: int = 23

class ProcessRequest(BaseModel):
    group_id: int
    content_type: str  # "text", "image", "video"
    # Para text
    text: Optional[str] = None
    # Para archivos, se envían como multipart

class ProcessResponse(BaseModel):
    success: bool
    processed: bool
    message: str = ""
    processing_time_ms: int = 0

# ==================== WATERMARK SERVICE ====================

class WatermarkMicroservice:
    """
    Microservicio de watermarks completamente independiente
    """
    
    def __init__(self):
        self.configs: Dict[int, GroupConfig] = {}
        self.png_cache: Dict[str, Image.Image] = {}
        self.stats = {
            'total_processed': 0,
            'images_processed': 0,
            'videos_processed': 0,
            'texts_processed': 0,
            'errors': 0,
            'start_time': datetime.now()
        }
        
        # Cargar configuraciones existentes
        self._load_configurations()
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("🎨 Watermark Microservice inicializado")
        self.logger.info(f"   📷 Imágenes: {'✅' if PIL_AVAILABLE else '❌'}")
        self.logger.info(f"   🎬 Videos: {'✅' if FFMPEG_AVAILABLE else '❌'}")
        self.logger.info(f"   📁 Puerto: {SERVICE_CONFIG['port']}")
    
    # ============ GESTIÓN DE CONFIGURACIONES ============
    
    def create_or_update_config(self, config_request: GroupConfigRequest) -> GroupConfig:
        """Crear o actualizar configuración de grupo"""
        try:
            config = GroupConfig(
                group_id=config_request.group_id,
                name=config_request.name,
                watermark_type=WatermarkType(config_request.watermark_type),
                png_enabled=config_request.png_enabled,
                png_position=Position(config_request.png_position),
                png_opacity=config_request.png_opacity,
                png_scale=config_request.png_scale,
                png_custom_x=config_request.png_custom_x,
                png_custom_y=config_request.png_custom_y,
                text_enabled=config_request.text_enabled,
                text_content=config_request.text_content,
                text_position=Position(config_request.text_position),
                text_font_size=config_request.text_font_size,
                text_color=config_request.text_color,
                text_stroke_color=config_request.text_stroke_color,
                text_stroke_width=config_request.text_stroke_width,
                video_enabled=config_request.video_enabled,
                video_max_size_mb=config_request.video_max_size_mb,
                video_timeout_sec=config_request.video_timeout_sec,
                video_compress=config_request.video_compress,
                video_quality=config_request.video_quality,
                updated_at=datetime.now()
            )
            
            # Si es actualización, mantener algunos datos
            if config_request.group_id in self.configs:
                existing = self.configs[config_request.group_id]
                config.png_filename = existing.png_filename
                config.created_at = existing.created_at
            
            self.configs[config_request.group_id] = config
            self._save_configuration(config)
            
            self.logger.info(f"📝 Configuración {'actualizada' if config_request.group_id in self.configs else 'creada'} para grupo {config_request.group_id}")
            return config
            
        except Exception as e:
            self.logger.error(f"❌ Error configurando grupo {config_request.group_id}: {e}")
            raise
    
    def get_config(self, group_id: int) -> Optional[GroupConfig]:
        """Obtener configuración de grupo"""
        return self.configs.get(group_id)
    
    def get_all_configs(self) -> Dict[int, GroupConfig]:
        """Obtener todas las configuraciones"""
        return {k: v for k, v in self.configs.items()}
    
    def delete_config(self, group_id: int) -> bool:
        """Eliminar configuración de grupo"""
        if group_id not in self.configs:
            return False
        
        # Eliminar archivos asociados
        config = self.configs[group_id]
        if config.png_filename:
            png_path = SERVICE_CONFIG['data_dir'] / 'assets' / config.png_filename
            if png_path.exists():
                png_path.unlink()
        
        # Eliminar configuración
        del self.configs[group_id]
        
        # Eliminar archivo de configuración
        config_file = SERVICE_CONFIG['data_dir'] / 'config' / f"group_{group_id}.json"
        if config_file.exists():
            config_file.unlink()
        
        self.logger.info(f"🗑️ Configuración eliminada para grupo {group_id}")
        return True
    
    # ============ PROCESAMIENTO ==============
    
    async def process_text(self, text: str, group_id: int) -> Tuple[str, bool]:
        """Procesar mensaje de texto"""
        start_time = datetime.now()
        
        try:
            config = self.get_config(group_id)
            if not config or not config.text_enabled or not config.text_content:
                return text, False
            
            # Añadir texto personalizado
            processed_text = f"{text}\n\n{config.text_content.strip()}"
            
            self.stats['texts_processed'] += 1
            self.stats['total_processed'] += 1
            
            processing_time = (datetime.now() - start_time).total_seconds()
            self.logger.debug(f"📝 Texto procesado para grupo {group_id} en {processing_time:.3f}s")
            
            return processed_text, True
            
        except Exception as e:
            self.logger.error(f"❌ Error procesando texto para grupo {group_id}: {e}")
            self.stats['errors'] += 1
            return text, False
    
    async def process_image(self, image_bytes: bytes, group_id: int) -> Tuple[bytes, bool]:
        """Procesar imagen con watermarks"""
        start_time = datetime.now()
        
        try:
            config = self.get_config(group_id)
            if not config or config.watermark_type == WatermarkType.NONE:
                return image_bytes, False
            
            if not PIL_AVAILABLE:
                self.logger.warning("⚠️ PIL no disponible")
                return image_bytes, False
            
            # Cargar imagen
            image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
            
            # Aplicar watermarks según configuración
            if config.watermark_type in [WatermarkType.PNG, WatermarkType.BOTH]:
                if config.png_enabled and config.png_filename:
                    image = await self._apply_png_watermark(image, config)
            
            if config.watermark_type in [WatermarkType.TEXT, WatermarkType.BOTH]:
                if config.text_enabled and config.text_content:
                    image = await self._apply_text_watermark(image, config)
            
            # Convertir de vuelta a bytes
            output = io.BytesIO()
            if image.mode == "RGBA":
                # Convertir a RGB para JPEG
                background = Image.new("RGB", image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[-1])
                background.save(output, format="JPEG", quality=85, optimize=True)
            else:
                image.save(output, format="JPEG", quality=85, optimize=True)
            
            processed_bytes = output.getvalue()
            
            self.stats['images_processed'] += 1
            self.stats['total_processed'] += 1
            
            processing_time = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"🖼️ Imagen procesada para grupo {group_id} en {processing_time:.3f}s")
            
            return processed_bytes, True
            
        except Exception as e:
            self.logger.error(f"❌ Error procesando imagen para grupo {group_id}: {e}")
            self.stats['errors'] += 1
            return image_bytes, False
    
    async def process_video(self, video_bytes: bytes, group_id: int) -> Tuple[bytes, bool]:
        """Procesar video con watermarks usando FFmpeg"""
        start_time = datetime.now()
        
        try:
            config = self.get_config(group_id)
            if not config or not config.video_enabled or config.watermark_type == WatermarkType.NONE:
                return video_bytes, False
            
            if not FFMPEG_AVAILABLE:
                self.logger.warning("⚠️ FFmpeg no disponible")
                return video_bytes, False
            
            # Verificar tamaño
            size_mb = len(video_bytes) / (1024 * 1024)
            if size_mb > config.video_max_size_mb:
                self.logger.warning(f"⚠️ Video demasiado grande: {size_mb:.1f}MB > {config.video_max_size_mb}MB")
                return video_bytes, False
            
            # Archivos temporales
            temp_dir = SERVICE_CONFIG['data_dir'] / 'temp'
            input_file = temp_dir / f"input_{group_id}_{int(datetime.now().timestamp())}.mp4"
            output_file = temp_dir / f"output_{group_id}_{int(datetime.now().timestamp())}.mp4"
            
            try:
                # Escribir video de entrada
                with open(input_file, 'wb') as f:
                    f.write(video_bytes)
                
                # Construir comando FFmpeg
                ffmpeg_cmd = await self._build_ffmpeg_command(input_file, output_file, config)
                
                # Ejecutar FFmpeg
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
                        self.logger.error(f"❌ FFmpeg error: {stderr.decode()}")
                        return video_bytes, False
                    
                    # Leer resultado
                    if output_file.exists():
                        with open(output_file, 'rb') as f:
                            processed_bytes = f.read()
                        
                        self.stats['videos_processed'] += 1
                        self.stats['total_processed'] += 1
                        
                        processing_time = (datetime.now() - start_time).total_seconds()
                        self.logger.info(f"🎬 Video procesado para grupo {group_id} en {processing_time:.3f}s")
                        
                        return processed_bytes, True
                    else:
                        self.logger.error("❌ Archivo de salida no generado")
                        return video_bytes, False
                        
                except asyncio.TimeoutError:
                    self.logger.error(f"⏰ Timeout procesando video para grupo {group_id}")
                    process.kill()
                    return video_bytes, False
                    
            finally:
                # Limpiar archivos temporales
                for temp_file in [input_file, output_file]:
                    if temp_file.exists():
                        temp_file.unlink()
                        
        except Exception as e:
            self.logger.error(f"❌ Error procesando video para grupo {group_id}: {e}")
            self.stats['errors'] += 1
            return video_bytes, False
    
    # ============ MÉTODOS AUXILIARES ============
    
    async def _apply_png_watermark(self, image: Image.Image, config: GroupConfig) -> Image.Image:
        """Aplicar watermark PNG"""
        try:
            # Cargar PNG
            png_watermark = await self._load_png_watermark(config.png_filename)
            if not png_watermark:
                return image
            
            # Calcular tamaño
            img_width, img_height = image.size
            watermark_width = int(img_width * config.png_scale)
            watermark_height = int(png_watermark.size[1] * (watermark_width / png_watermark.size[0]))
            
            # Redimensionar
            watermark_resized = png_watermark.resize(
                (watermark_width, watermark_height),
                Image.Resampling.LANCZOS
            )
            
            # Aplicar opacidad
            if config.png_opacity < 1.0:
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
            
            return image
            
        except Exception as e:
            self.logger.error(f"❌ Error aplicando PNG watermark: {e}")
            return image
    
    async def _apply_text_watermark(self, image: Image.Image, config: GroupConfig) -> Image.Image:
        """Aplicar watermark de texto"""
        try:
            import io
            
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
                20, 60  # Offset por defecto para texto
            )
            
            # Dibujar stroke
            if config.text_stroke_width > 0:
                for adj_x in range(-config.text_stroke_width, config.text_stroke_width + 1):
                    for adj_y in range(-config.text_stroke_width, config.text_stroke_width + 1):
                        if adj_x != 0 or adj_y != 0:
                            draw.text(
                                (x + adj_x, y + adj_y),
                                config.text_content,
                                font=font,
                                fill=config.text_stroke_color
                            )
            
            # Dibujar texto principal
            draw.text((x, y), config.text_content, font=font, fill=config.text_color)
            
            return image
            
        except Exception as e:
            self.logger.error(f"❌ Error aplicando texto watermark: {e}")
            return image
    
    async def _load_png_watermark(self, filename: str) -> Optional[Image.Image]:
        """Cargar PNG watermark con cache"""
        if not filename:
            return None
        
        # Verificar cache
        if filename in self.png_cache:
            return self.png_cache[filename]
        
        try:
            png_path = SERVICE_CONFIG['data_dir'] / 'assets' / filename
            if not png_path.exists():
                self.logger.warning(f"⚠️ PNG watermark no encontrado: {png_path}")
                return None
            
            png_image = Image.open(png_path).convert("RGBA")
            
            # Guardar en cache
            self.png_cache[filename] = png_image
            
            return png_image
            
        except Exception as e:
            self.logger.error(f"❌ Error cargando PNG watermark {filename}: {e}")
            return None
    
    def _calculate_position(self, image_size: Tuple[int, int],
                          watermark_size: Tuple[int, int],
                          position: Position,
                          custom_x: int = 0,
                          custom_y: int = 0) -> Tuple[int, int]:
        """Calcular posición del watermark"""
        img_width, img_height = image_size
        wm_width, wm_height = watermark_size
        
        margin = 20
        
        position_map = {
            Position.TOP_LEFT: (margin, margin),
            Position.TOP_RIGHT: (img_width - wm_width - margin, margin),
            Position.BOTTOM_LEFT: (margin, img_height - wm_height - margin),
            Position.BOTTOM_RIGHT: (img_width - wm_width - margin, img_height - wm_height - margin),
            Position.CENTER: ((img_width - wm_width) // 2, (img_height - wm_height) // 2),
            Position.CUSTOM: (custom_x, custom_y)
        }
        
        return position_map.get(position, position_map[Position.BOTTOM_RIGHT])
    
    async def _build_ffmpeg_command(self, input_file: Path, output_file: Path, config: GroupConfig) -> List[str]:
        """Construir comando FFmpeg"""
        cmd = ["ffmpeg", "-y", "-i", str(input_file)]
        
        filters = []
        
        # Watermark PNG
        if config.watermark_type in [WatermarkType.PNG, WatermarkType.BOTH] and config.png_filename:
            png_path = SERVICE_CONFIG['data_dir'] / 'assets' / config.png_filename
            if png_path.exists():
                pos_x, pos_y = self._get_ffmpeg_position(config.png_position, config.png_custom_x, config.png_custom_y)
                
                filters.append(
                    f"movie={png_path}:loop=0,setpts=N/(FRAME_RATE*TB),"
                    f"scale=iw*{config.png_scale}:-1,format=rgba,"
                    f"colorchannelmixer=aa={config.png_opacity}[wm];"
                    f"[0:v][wm]overlay={pos_x}:{pos_y}"
                )
        
        # Watermark de texto
        if config.watermark_type in [WatermarkType.TEXT, WatermarkType.BOTH] and config.text_content:
            pos_x, pos_y = self._get_ffmpeg_position(config.text_position, 20, 60)
            
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
        
        # Aplicar filtros
        if filters:
            cmd.extend(["-vf", ";".join(filters)])
        
        # Configuración de video
        if config.video_compress:
            cmd.extend([
                "-c:v", "libx264",
                "-crf", str(config.video_quality),
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
    
    def _save_configuration(self, config: GroupConfig):
        """Guardar configuración a archivo"""
        try:
            config_file = SERVICE_CONFIG['data_dir'] / 'config' / f"group_{config.group_id}.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"❌ Error guardando configuración: {e}")
    
    def _load_configurations(self):
        """Cargar configuraciones existentes"""
        try:
            config_dir = SERVICE_CONFIG['data_dir'] / 'config'
            
            for config_file in config_dir.glob("group_*.json"):
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Convertir de vuelta a objetos
                    data['watermark_type'] = WatermarkType(data['watermark_type'])
                    data['png_position'] = Position(data['png_position'])
                    data['text_position'] = Position(data['text_position'])
                    data['created_at'] = datetime.fromisoformat(data['created_at'])
                    data['updated_at'] = datetime.fromisoformat(data['updated_at'])
                    
                    config = GroupConfig(**data)
                    self.configs[config.group_id] = config
                    
                except Exception as e:
                    self.logger.error(f"❌ Error cargando {config_file}: {e}")
                    
            self.logger.info(f"📂 {len(self.configs)} configuraciones cargadas")
            
        except Exception as e:
            self.logger.error(f"❌ Error cargando configuraciones: {e}")
    
    def get_health(self) -> Dict[str, Any]:
        """Health check del microservicio"""
        uptime = (datetime.now() - self.stats['start_time']).total_seconds()
        
        return {
            "service": SERVICE_CONFIG['name'],
            "version": SERVICE_CONFIG['version'],
            "status": "healthy",
            "uptime_seconds": uptime,
            "capabilities": {
                "images": PIL_AVAILABLE,
                "videos": FFMPEG_AVAILABLE,
                "http_client": AIOHTTP_AVAILABLE
            },
            "stats": self.stats.copy(),
            "groups_configured": len(self.configs)
        }

# ==================== MICROSERVICIO FASTAPI ====================

# Instancia global del servicio
watermark_service = WatermarkMicroservice()

# Conectados WebSocket
connected_clients = set()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle del microservicio"""
    # Startup
    print(f"🚀 Watermark Microservice v{SERVICE_CONFIG['version']} iniciando...")
    yield
    # Shutdown
    print("👋 Watermark Microservice cerrando...")

# Crear aplicación FastAPI
app = FastAPI(
    title="🎨 Watermark Microservice",
    description="Microservicio independiente para procesamiento de watermarks",
    version=SERVICE_CONFIG['version'],
    lifespan=lifespan
)

# CORS para permitir acceso desde cualquier aplicación
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== API ENDPOINTS ====================

@app.get("/")
async def root():
    """Endpoint raíz con información del servicio"""
    return {
        "service": "Watermark Microservice",
        "version": SERVICE_CONFIG['version'],
        "status": "running",
        "endpoints": {
            "health": "/health",
            "dashboard": "/dashboard",
            "api_docs": "/docs",
            "process_text": "POST /process/text",
            "process_image": "POST /process/image", 
            "process_video": "POST /process/video",
            "config": "/api/config",
            "groups": "/api/groups"
        }
    }

@app.get("/health")
async def health_check():
    """Health check del microservicio"""
    return watermark_service.get_health()

# ============ CONFIGURACIÓN DE GRUPOS ============

@app.get("/api/groups")
async def get_all_groups():
    """Obtener todas las configuraciones de grupos"""
    configs = watermark_service.get_all_configs()
    return {
        str(group_id): config.to_dict()
        for group_id, config in configs.items()
    }

@app.get("/api/groups/{group_id}")
async def get_group_config(group_id: int):
    """Obtener configuración específica de un grupo"""
    config = watermark_service.get_config(group_id)
    if not config:
        raise HTTPException(status_code=404, detail=f"Grupo {group_id} no encontrado")
    
    return config.to_dict()

@app.post("/api/groups/{group_id}/config")
async def update_group_config(group_id: int, config_request: GroupConfigRequest):
    """Crear o actualizar configuración de grupo"""
    try:
        # Asegurar que el group_id coincida
        config_request.group_id = group_id
        
        config = watermark_service.create_or_update_config(config_request)
        
        # Notificar a clientes WebSocket
        await broadcast_update("group_updated", {
            "group_id": group_id,
            "config": config.to_dict()
        })
        
        return {
            "success": True,
            "message": f"Configuración {'creada' if group_id not in watermark_service.configs else 'actualizada'} para grupo {group_id}",
            "config": config.to_dict()
        }
        
    except Exception as e:
        watermark_service.logger.error(f"Error updating group {group_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/groups/{group_id}")
async def delete_group_config(group_id: int):
    """Eliminar configuración de grupo"""
    success = watermark_service.delete_config(group_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Grupo {group_id} no encontrado")
    
    await broadcast_update("group_deleted", {"group_id": group_id})
    
    return {
        "success": True,
        "message": f"Configuración eliminada para grupo {group_id}"
    }

# ============ UPLOAD DE ARCHIVOS ============

@app.post("/api/groups/{group_id}/upload")
async def upload_watermark_file(group_id: int, file: UploadFile = File(...)):
    """Subir archivo PNG para watermark"""
    try:
        # Validar archivo
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Solo se permiten archivos de imagen")
        
        # Validar extensión
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in ['.png', '.jpg', '.jpeg']:
            raise HTTPException(status_code=400, detail="Solo se permiten archivos PNG, JPG o JPEG")
        
        # Generar nombre único
        timestamp = int(datetime.now().timestamp())
        filename = f"watermark_{group_id}_{timestamp}{file_extension}"
        file_path = SERVICE_CONFIG['data_dir'] / 'assets' / filename
        
        # Guardar archivo
        content = await file.read()
        
        # Validar tamaño
        size_mb = len(content) / (1024 * 1024)
        if size_mb > SERVICE_CONFIG['max_file_size_mb']:
            raise HTTPException(
                status_code=400, 
                detail=f"Archivo demasiado grande: {size_mb:.1f}MB > {SERVICE_CONFIG['max_file_size_mb']}MB"
            )
        
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # Actualizar configuración del grupo
        config = watermark_service.get_config(group_id)
        if config:
            # Eliminar archivo anterior si existe
            if config.png_filename:
                old_path = SERVICE_CONFIG['data_dir'] / 'assets' / config.png_filename
                if old_path.exists():
                    old_path.unlink()
            
            # Actualizar configuración
            config.png_filename = filename
            config.png_enabled = True
            config.updated_at = datetime.now()
            watermark_service._save_configuration(config)
        else:
            # Crear nueva configuración básica
            config_request = GroupConfigRequest(
                group_id=group_id,
                watermark_type="png",
                png_enabled=True
            )
            config = watermark_service.create_or_update_config(config_request)
            config.png_filename = filename
            watermark_service._save_configuration(config)
        
        # Limpiar cache PNG
        if filename in watermark_service.png_cache:
            del watermark_service.png_cache[filename]
        
        watermark_service.logger.info(f"📁 Watermark subido para grupo {group_id}: {filename}")
        
        return {
            "success": True,
            "filename": filename,
            "message": f"Watermark subido exitosamente para grupo {group_id}",
            "file_size_mb": round(size_mb, 2)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        watermark_service.logger.error(f"Error uploading watermark for group {group_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/assets/{filename}")
async def get_asset_file(filename: str):
    """Servir archivo de asset"""
    file_path = SERVICE_CONFIG['data_dir'] / 'assets' / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    return FileResponse(file_path)

# ============ PROCESAMIENTO ============

@app.post("/process/text")
async def process_text_endpoint(group_id: int = Form(...), text: str = Form(...)):
    """Procesar mensaje de texto"""
    try:
        start_time = datetime.now()
        
        processed_text, was_processed = await watermark_service.process_text(text, group_id)
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return ProcessResponse(
            success=True,
            processed=was_processed,
            message="Texto procesado exitosamente" if was_processed else "Texto sin cambios",
            processing_time_ms=int(processing_time)
        ), {"processed_text": processed_text}
        
    except Exception as e:
        watermark_service.logger.error(f"Error processing text: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process/image")
async def process_image_endpoint(group_id: int = Form(...), file: UploadFile = File(...)):
    """Procesar imagen con watermarks"""
    try:
        start_time = datetime.now()
        
        # Leer archivo
        image_bytes = await file.read()
        
        # Procesar
        processed_bytes, was_processed = await watermark_service.process_image(image_bytes, group_id)
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Retornar imagen procesada
        from fastapi.responses import Response
        
        return Response(
            content=processed_bytes,
            media_type="image/jpeg",
            headers={
                "X-Processed": str(was_processed),
                "X-Processing-Time-Ms": str(int(processing_time)),
                "X-Original-Size": str(len(image_bytes)),
                "X-Processed-Size": str(len(processed_bytes))
            }
        )
        
    except Exception as e:
        watermark_service.logger.error(f"Error processing image: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process/video")
async def process_video_endpoint(group_id: int = Form(...), file: UploadFile = File(...)):
    """Procesar video con watermarks"""
    try:
        start_time = datetime.now()
        
        # Leer archivo
        video_bytes = await file.read()
        
        # Procesar
        processed_bytes, was_processed = await watermark_service.process_video(video_bytes, group_id)
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Retornar video procesado
        from fastapi.responses import Response
        
        return Response(
            content=processed_bytes,
            media_type="video/mp4",
            headers={
                "X-Processed": str(was_processed),
                "X-Processing-Time-Ms": str(int(processing_time)),
                "X-Original-Size": str(len(video_bytes)),
                "X-Processed-Size": str(len(processed_bytes))
            }
        )
        
    except Exception as e:
        watermark_service.logger.error(f"Error processing video: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============ WEBSOCKET ============

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket para updates en tiempo real"""
    await websocket.accept()
    connected_clients.add(websocket)
    
    try:
        # Enviar estado inicial
        await websocket.send_json({
            "type": "initial_state",
            "data": {
                "health": watermark_service.get_health(),
                "groups": {
                    str(k): v.to_dict() 
                    for k, v in watermark_service.get_all_configs().items()
                }
            }
        })
        
        # Mantener conexión
        while True:
            try:
                await asyncio.sleep(30)
                await websocket.send_json({"type": "ping"})
            except:
                break
                
    except WebSocketDisconnect:
        pass
    finally:
        connected_clients.discard(websocket)

async def broadcast_update(update_type: str, data: Any):
    """Broadcast update a todos los clientes WebSocket"""
    if not connected_clients:
        return
    
    message = {
        "type": update_type,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }
    
    disconnected = set()
    for client in connected_clients:
        try:
            await client.send_json(message)
        except:
            disconnected.add(client)
    
    # Remover clientes desconectados
    connected_clients -= disconnected

# ============ DASHBOARD WEB ============

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Dashboard web minimalista"""
    return '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎨 Watermark Microservice</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 40px;
        }
        
        .header h1 {
            font-size: 3rem;
            font-weight: 300;
            margin-bottom: 10px;
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        
        .stat-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(20px);
            border-radius: 16px;
            padding: 24px;
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .stat-value {
            font-size: 2.5rem;
            font-weight: 700;
            display: block;
            margin-bottom: 8px;
        }
        
        .stat-label {
            font-size: 0.9rem;
            opacity: 0.8;
        }
        
        .section {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(20px);
            border-radius: 24px;
            padding: 32px;
            margin-bottom: 20px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .section h2 {
            margin-bottom: 20px;
            font-size: 1.5rem;
        }
        
        .capability {
            display: inline-block;
            padding: 8px 16px;
            margin: 4px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 600;
        }
        
        .capability.enabled {
            background: rgba(40, 167, 69, 0.8);
        }
        
        .capability.disabled {
            background: rgba(220, 53, 69, 0.8);
        }
        
        .api-section {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        
        .api-group {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 20px;
        }
        
        .api-group h3 {
            margin-bottom: 12px;
            color: #fff;
        }
        
        .endpoint {
            margin-bottom: 8px;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 0.9rem;
            padding: 8px 12px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 6px;
            border-left: 3px solid #667eea;
        }
        
        .method {
            color: #28a745;
            font-weight: 600;
        }
        
        .method.post { color: #ffc107; }
        .method.delete { color: #dc3545; }
        
        .status {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        
        .status.healthy {
            background: rgba(40, 167, 69, 0.8);
        }
        
        .btn {
            display: inline-block;
            padding: 12px 24px;
            background: rgba(255, 255, 255, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 8px;
            color: white;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.3s ease;
            margin: 8px 4px;
        }
        
        .btn:hover {
            background: rgba(255, 255, 255, 0.3);
            transform: translateY(-2px);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎨 Watermark Microservice</h1>
            <p>Microservicio independiente v3.0</p>
            <span class="status healthy">🟢 Healthy</span>
        </div>
        
        <div class="stats" id="stats">
            <!-- Stats se cargan dinámicamente -->
        </div>
        
        <div class="section">
            <h2>🔧 Capacidades del Sistema</h2>
            <div id="capabilities">
                <!-- Capabilities se cargan dinámicamente -->
            </div>
        </div>
        
        <div class="section">
            <h2>📡 API Endpoints</h2>
            <div class="api-section">
                <div class="api-group">
                    <h3>🏥 Health & Info</h3>
                    <div class="endpoint">
                        <span class="method">GET</span> /health
                    </div>
                    <div class="endpoint">
                        <span class="method">GET</span> /
                    </div>
                </div>
                
                <div class="api-group">
                    <h3>👥 Gestión de Grupos</h3>
                    <div class="endpoint">
                        <span class="method">GET</span> /api/groups
                    </div>
                    <div class="endpoint">
                        <span class="method post">POST</span> /api/groups/{id}/config
                    </div>
                    <div class="endpoint">
                        <span class="method delete">DELETE</span> /api/groups/{id}
                    </div>
                    <div class="endpoint">
                        <span class="method post">POST</span> /api/groups/{id}/upload
                    </div>
                </div>
                
                <div class="api-group">
                    <h3>⚙️ Procesamiento</h3>
                    <div class="endpoint">
                        <span class="method post">POST</span> /process/text
                    </div>
                    <div class="endpoint">
                        <span class="method post">POST</span> /process/image
                    </div>
                    <div class="endpoint">
                        <span class="method post">POST</span> /process/video
                    </div>
                </div>
                
                <div class="api-group">
                    <h3>🔗 Otros</h3>
                    <div class="endpoint">
                        <span class="method">WS</span> /ws
                    </div>
                    <div class="endpoint">
                        <span class="method">GET</span> /docs
                    </div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>🔗 Enlaces Útiles</h2>
            <a href="/docs" class="btn">📚 Documentación API</a>
            <a href="/health" class="btn">🏥 Health Check</a>
            <a href="/api/groups" class="btn">👥 Ver Grupos</a>
        </div>
    </div>
    
    <script>
        // Cargar stats dinámicamente
        async function loadStats() {
            try {
                const response = await fetch('/health');
                const health = await response.json();
                
                const statsHtml = `
                    <div class="stat-card">
                        <span class="stat-value">${health.stats.total_processed}</span>
                        <span class="stat-label">Total Procesados</span>
                    </div>
                    <div class="stat-card">
                        <span class="stat-value">${health.stats.images_processed}</span>
                        <span class="stat-label">Imágenes</span>
                    </div>
                    <div class="stat-card">
                        <span class="stat-value">${health.stats.videos_processed}</span>
                        <span class="stat-label">Videos</span>
                    </div>
                    <div class="stat-card">
                        <span class="stat-value">${health.groups_configured}</span>
                        <span class="stat-label">Grupos Configurados</span>
                    </div>
                    <div class="stat-card">
                        <span class="stat-value">${Math.round(health.uptime_seconds / 3600 * 10) / 10}h</span>
                        <span class="stat-label">Uptime</span>
                    </div>
                `;
                
                document.getElementById('stats').innerHTML = statsHtml;
                
                const capabilitiesHtml = `
                    <span class="capability ${health.capabilities.images ? 'enabled' : 'disabled'}">
                        📷 Imágenes ${health.capabilities.images ? '✅' : '❌'}
                    </span>
                    <span class="capability ${health.capabilities.videos ? 'enabled' : 'disabled'}">
                        🎬 Videos ${health.capabilities.videos ? '✅' : '❌'}
                    </span>
                    <span class="capability ${health.capabilities.http_client ? 'enabled' : 'disabled'}">
                        🌐 HTTP Client ${health.capabilities.http_client ? '✅' : '❌'}
                    </span>
                `;
                
                document.getElementById('capabilities').innerHTML = capabilitiesHtml;
                
            } catch (error) {
                console.error('Error loading stats:', error);
            }
        }
        
        // Cargar stats al inicio
        loadStats();
        
        // Recargar cada 30 segundos
        setInterval(loadStats, 30000);
    </script>
</body>
</html>'''

# ==================== CLIENTE PYTHON EXAMPLE ============

example_client_code = '''"""
Ejemplo de cliente Python para usar el Watermark Microservice
===========================================================
"""

import aiohttp
import asyncio

class WatermarkClient:
    def __init__(self, base_url="http://localhost:8081"):
        self.base_url = base_url
    
    async def process_text(self, group_id: int, text: str) -> tuple[str, bool]:
        """Procesar texto con watermarks"""
        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field('group_id', str(group_id))
            data.add_field('text', text)
            
            async with session.post(f"{self.base_url}/process/text", data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    processed_text = result[1]["processed_text"]
                    return processed_text, result[0]["processed"]
                else:
                    raise Exception(f"Error: {response.status}")
    
    async def process_image(self, group_id: int, image_bytes: bytes) -> tuple[bytes, bool]:
        """Procesar imagen con watermarks"""
        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field('group_id', str(group_id))
            data.add_field('file', image_bytes, filename='image.jpg', content_type='image/jpeg')
            
            async with session.post(f"{self.base_url}/process/image", data=data) as response:
                if response.status == 200:
                    processed_bytes = await response.read()
                    was_processed = response.headers.get('X-Processed') == 'True'
                    return processed_bytes, was_processed
                else:
                    raise Exception(f"Error: {response.status}")

# Ejemplo de uso:
async def main():
    client = WatermarkClient()
    
    # Procesar texto
    processed_text, modified = await client.process_text(-1001234567890, "Hola mundo")
    print(f"Texto: {processed_text}, Modificado: {modified}")
    
    # Procesar imagen
    with open("imagen.jpg", "rb") as f:
        image_bytes = f.read()
    
    processed_image, was_processed = await client.process_image(-1001234567890, image_bytes)
    
    if was_processed:
        with open("imagen_procesada.jpg", "wb") as f:
            f.write(processed_image)

# asyncio.run(main())
'''

# ==================== MAIN ====================

if __name__ == "__main__":
    import io
    
    print("🎨 Iniciando Watermark Microservice...")
    print(f"📍 Puerto: {SERVICE_CONFIG['port']}")
    print(f"📁 Datos: {SERVICE_CONFIG['data_dir']}")
    print(f"🔧 Capacidades:")
    print(f"   📷 Imágenes: {'✅' if PIL_AVAILABLE else '❌'}")
    print(f"   🎬 Videos: {'✅' if FFMPEG_AVAILABLE else '❌'}")
    print(f"   🌐 HTTP: {'✅' if AIOHTTP_AVAILABLE else '❌'}")
    print()
    print("🌐 Endpoints disponibles:")
    print(f"   Dashboard: http://localhost:{SERVICE_CONFIG['port']}/dashboard")
    print(f"   API Docs: http://localhost:{SERVICE_CONFIG['port']}/docs")
    print(f"   Health: http://localhost:{SERVICE_CONFIG['port']}/health")
    print()
    
    # Crear archivo de ejemplo del cliente
    client_file = Path("watermark_client_example.py")
    with open(client_file, 'w') as f:
        f.write(example_client_code)
    print(f"📝 Cliente de ejemplo creado: {client_file}")
    print()
    
    try:
        uvicorn.run(
            app,
            host=SERVICE_CONFIG['host'],
            port=SERVICE_CONFIG['port'],
            log_level="info" if SERVICE_CONFIG['debug'] else "warning"
        )
    except KeyboardInterrupt:
        print("\n👋 Microservicio detenido")
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        sys.exit(1)