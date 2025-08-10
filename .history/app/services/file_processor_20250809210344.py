"""
FILE PROCESSOR BRIDGE
=====================
Archivo: app/services/file_processor.py

Este archivo conecta tu sistema actual con la nueva arquitectura
Sin romper ninguna importación existente
"""

import asyncio
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import logging

# Intentar importar la versión V2 si existe
try:
    from app.services.file_processor_v2 import (
        FileProcessorAPI,
        FileProcessorMicroservice,
        get_file_processor
    )
    V2_AVAILABLE = True
except ImportError:
    V2_AVAILABLE = False

# Import configuración y logger
try:
    from app.config.settings import get_settings
    settings = get_settings()
except:
    class Settings:
        CACHE_DIR = "cache"
        TEMP_DIR = "temp"
        OUTPUT_DIR = "processed_files"
    settings = Settings()

try:
    from app.utils.logger import setup_logger
    logger = setup_logger(__name__)
except:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

# Imports opcionales
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False


class FileCache:
    """Cache compatible con tu código actual"""
    
    def __init__(self, cache_dir: Path, max_cache_size_gb: float = 2.0):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_cache_size = max_cache_size_gb * 1024 * 1024 * 1024
        self.cache_index_file = cache_dir / "cache_index.json"
        self.cache_index = self._load_cache_index()
    
    def _load_cache_index(self) -> Dict[str, Any]:
        """Cargar índice de cache con manejo robusto"""
        if self.cache_index_file.exists():
            try:
                with open(self.cache_index_file, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                    if content.strip():
                        return json.loads(content)
            except Exception as e:
                logger.warning(f"Error cargando cache index: {e}")
        return {}
    
    def _save_cache_index(self):
        """Guardar índice de cache"""
        try:
            # Limpiar datos no serializables
            clean_index = {}
            for key, value in self.cache_index.items():
                if isinstance(value, dict):
                    # Remover bytes y otros tipos no serializables
                    clean_value = {
                        k: v for k, v in value.items() 
                        if not isinstance(v, bytes)
                    }
                    clean_index[key] = clean_value
                else:
                    clean_index[key] = value
            
            with open(self.cache_index_file, 'w', encoding='utf-8') as f:
                json.dump(clean_index, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error guardando cache index: {e}")
    
    def get_file_hash(self, file_bytes: bytes) -> str:
        """Generar hash de archivo"""
        return hashlib.sha256(file_bytes).hexdigest()[:16]
    
    def add_to_cache(self, cache_key: str, cache_info: Dict[str, Any], 
                     cache_filename: str) -> str:
        """Añadir al cache"""
        self.cache_index[cache_key] = {
            'filename': cache_filename,
            'created': datetime.now().isoformat(),
            'last_accessed': datetime.now().isoformat(),
            'size_bytes': cache_info.get('size_bytes', 0)
        }
        self._save_cache_index()
        return cache_filename
    
    def _cleanup_cache_if_needed(self):
        """Limpiar cache si es necesario"""
        try:
            total_size = sum(
                info.get('size_bytes', 0) 
                for info in self.cache_index.values()
            )
            
            if total_size > self.max_cache_size:
                # Limpiar archivos más antiguos
                sorted_entries = sorted(
                    self.cache_index.items(),
                    key=lambda x: x[1].get('last_accessed', '1970-01-01')
                )
                
                removed_size = 0
                target_remove = total_size - (self.max_cache_size * 0.8)
                
                for cache_key, cache_info in sorted_entries:
                    if removed_size >= target_remove:
                        break
                    
                    cache_file = self.cache_dir / cache_info.get('filename', '')
                    if cache_file.exists():
                        cache_file.unlink()
                        removed_size += cache_info.get('size_bytes', 0)
                    
                    del self.cache_index[cache_key]
                
                self._save_cache_index()
                logger.info(f"Cache limpiado: {removed_size / (1024*1024):.1f}MB liberados")
        except Exception as e:
            logger.error(f"Error en cleanup: {e}")


class FileProcessorEnhanced:
    """
    Procesador de archivos compatible con tu código actual
    Usa V2 internamente si está disponible
    """
    
    def __init__(self):
        # Paths compatibles
        self.cache_dir = Path(getattr(settings, 'CACHE_DIR', 'cache'))
        self.temp_dir = Path(getattr(settings, 'TEMP_DIR', 'temp'))
        self.output_dir = Path(getattr(settings, 'OUTPUT_DIR', 'processed_files'))
        
        # Crear directorios
        for dir_path in [self.cache_dir, self.temp_dir, self.output_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Cache
        self.file_cache = FileCache(self.cache_dir)
        
        # Stats compatibles
        self.stats = {
            'images_processed': 0,
            'videos_processed': 0,
            'pdfs_processed': 0,
            'audios_processed': 0,
            'total_size_processed': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'errors': 0
        }
        
        # Configuración
        self.compression_settings = {
            'image_quality': 85,
            'video_crf': 23,
            'audio_bitrate': '128k',
            'max_image_size': (1920, 1080),
            'max_video_size': (1280, 720)
        }
        
        # V2 processor si está disponible
        self.v2_processor = None
        self._initialized = False
        
        logger.info("🚀 File Processor Enterprise inicializado")
    
    async def initialize(self):
        """Inicializar el procesador"""
        if self._initialized:
            return
        
        # Intentar usar V2 si está disponible
        if V2_AVAILABLE:
            try:
                self.v2_processor = await get_file_processor()
                logger.info("✅ Using File Processor V2 (microservices)")
            except Exception as e:
                logger.warning(f"⚠️ V2 not available: {e}, using legacy mode")
        
        await self._check_dependencies()
        self._initialized = True
        logger.info("✅ File Processor Enterprise inicializado correctamente")
    
    async def _check_dependencies(self):
        """Verificar dependencias del sistema"""
        dependencies = {
            'ffmpeg': await self._check_ffmpeg(),
            'pymupdf': PYMUPDF_AVAILABLE,
            'pil': PIL_AVAILABLE
        }
        
        logger.info("📦 Dependencias verificadas:")
        for dep, available in dependencies.items():
            status = "✅" if available else "❌"
            logger.info(f"   {dep}: {status}")
    
    async def _check_ffmpeg(self) -> bool:
        """Verificar si ffmpeg está disponible"""
        try:
            proc = await asyncio.create_subprocess_exec(
                'ffmpeg', '-version',
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await proc.wait()
            return proc.returncode == 0
        except:
            return False
    
    async def process_image(self, image_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Procesar imagen - compatible con tu código"""
        # Usar V2 si está disponible
        if self.v2_processor:
            try:
                result = await self.v2_processor.process_image(
                    image_bytes, filename, chat_id=0
                )
                if result.get('success'):
                    self.stats['images_processed'] += 1
                    self.stats['total_size_processed'] += len(image_bytes)
                return result
            except Exception as e:
                logger.error(f"V2 processor failed: {e}")
        
        # Fallback a procesamiento básico
        if not PIL_AVAILABLE:
            return {'success': False, 'error': 'PIL no disponible'}
        
        try:
            from io import BytesIO
            
            img = Image.open(BytesIO(image_bytes))
            original_size = len(image_bytes)
            
            # Comprimir si es necesario
            max_size = self.compression_settings['max_image_size']
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Guardar
            output_buffer = BytesIO()
            img.save(
                output_buffer, 
                format='JPEG',
                quality=self.compression_settings['image_quality'],
                optimize=True
            )
            
            compressed_bytes = output_buffer.getvalue()
            
            # Guardar archivo
            output_filename = f"img_{self.file_cache.get_file_hash(image_bytes)}_{filename}"
            output_path = self.output_dir / output_filename
            output_path.write_bytes(compressed_bytes)
            
            self.stats['images_processed'] += 1
            
            logger.info(f"🖼️ Imagen procesada: {filename}")
            
            return {
                'success': True,
                'filename': filename,
                'output_path': str(output_path),
                'original_size': original_size,
                'compressed_size': len(compressed_bytes)
            }
            
        except Exception as e:
            logger.error(f"Error procesando imagen: {e}")
            self.stats['errors'] += 1
            return {'success': False, 'error': str(e)}
    
    async def process_video(self, video_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Procesar video - compatible con tu código"""
        # Usar V2 si está disponible
        if self.v2_processor:
            try:
                result = await self.v2_processor.process_video(
                    video_bytes, filename, chat_id=0
                )
                if result.get('success'):
                    self.stats['videos_processed'] += 1
                return result
            except Exception as e:
                logger.error(f"V2 video processing failed: {e}")
        
        # Fallback básico
        logger.warning("Video processing not available in legacy mode")
        return {
            'success': False,
            'error': 'Video processing requires ffmpeg'
        }
    
    async def process_pdf(self, pdf_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Procesar PDF - compatible con tu código"""
        # Usar V2 si está disponible
        if self.v2_processor:
            try:
                result = await self.v2_processor.process_pdf(
                    pdf_bytes, filename, chat_id=0
                )
                if result.get('success'):
                    self.stats['pdfs_processed'] += 1
                return result
            except Exception as e:
                logger.error(f"V2 PDF processing failed: {e}")
        
        # Fallback básico
        if not PYMUPDF_AVAILABLE:
            return {'success': False, 'error': 'PyMuPDF no disponible'}
        
        try:
            pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
            page_count = len(pdf_document)
            
            # Guardar
            output_filename = f"pdf_{self.file_cache.get_file_hash(pdf_bytes)}_{filename}"
            output_path = self.output_dir / output_filename
            output_path.write_bytes(pdf_bytes)
            
            pdf_document.close()
            
            self.stats['pdfs_processed'] += 1
            
            logger.info(f"📄 PDF procesado: {filename} ({page_count} páginas)")
            
            return {
                'success': True,
                'filename': filename,
                'output_path': str(output_path),
                'page_count': page_count,
                'file_size': len(pdf_bytes)
            }
            
        except Exception as e:
            logger.error(f"Error procesando PDF: {e}")
            return {'success': False, 'error': str(e)}
    
    async def process_audio(self, audio_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Procesar audio - compatible con tu código"""
        # Usar V2 si está disponible
        if self.v2_processor:
            try:
                result = await self.v2_processor.process_audio(
                    audio_bytes, filename, chat_id=0
                )
                if result.get('success'):
                    self.stats['audios_processed'] += 1
                return result
            except Exception as e:
                logger.error(f"V2 audio processing failed: {e}")
        
        # Fallback básico
        logger.warning("Audio processing not available in legacy mode")
        return {
            'success': False,
            'error': 'Audio processing requires ffmpeg'
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas"""
        return {
            'processor_stats': self.stats,
            'directories': {
                'cache': str(self.cache_dir),
                'temp': str(self.temp_dir),
                'output': str(self.output_dir)
            },
            'mode': 'v2' if self.v2_processor else 'legacy'
        }


# Función helper para compatibilidad
def create_file_processor() -> FileProcessorEnhanced:
    """Factory function para crear FileProcessorEnhanced"""
    return FileProcessorEnhanced()


# Exportar clases para compatibilidad total
__all__ = ['FileCache', 'FileProcessorEnhanced', 'create_file_processor']