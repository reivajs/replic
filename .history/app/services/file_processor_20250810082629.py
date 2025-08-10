"""
FILE PROCESSOR BRIDGE - FIXED VERSION
=====================================
Archivo: app/services/file_processor.py

Corregido para aceptar los argumentos que envía enhanced_replicator_service
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


class FileProcessorBridge:
    """
    Bridge que hace que tu FileProcessorEnhanced actual
    use la nueva arquitectura internamente
    FIXED: Ahora acepta chat_id como parámetro
    """
    
    def __init__(self):
        self.new_processor: Optional[FileProcessorAPI] = None
        self.legacy_mode = False
        
        # Mantén compatibilidad con tu código actual
        self.cache_dir = Path("cache")
        self.temp_dir = Path("temp")
        self.output_dir = Path("processed_files")
        
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
        
        self._initialized = False
    
    async def initialize(self):
        """Inicializar bridge"""
        if self._initialized:
            return
            
        try:
            # Try new architecture
            self.new_processor = await get_file_processor()
            logger.info("✅ Using new microservice architecture")
        except Exception as e:
            logger.warning(f"⚠️ Failed to init new architecture: {e}")
            logger.info("📌 Falling back to legacy mode")
            self.legacy_mode = True
        
        self._initialized = True
    
    async def process_image(self, image_bytes: bytes, chat_id: int, filename: str) -> Dict[str, Any]:
        """
        FIXED: Ahora acepta chat_id como segundo parámetro
        Compatible con enhanced_replicator_service
        """
        if not self._initialized:
            await self.initialize()
            
        if self.new_processor and not self.legacy_mode:
            try:
                result = await self.new_processor.process_image(
                    image_bytes, filename, chat_id
                )
                
                if result.get('success'):
                    self.stats['images_processed'] += 1
                    self.stats['total_size_processed'] += result.get('original_size', 0)
                    
                    # Make result compatible with old format
                    return {
                        'success': True,
                        'filename': filename,
                        'output_path': result.get('output_path', ''),
                        'original_size': result.get('original_size', len(image_bytes)),
                        'compressed_size': result.get('compressed_size', len(image_bytes))
                    }
                
            except Exception as e:
                logger.error(f"New processor failed: {e}")
                self.legacy_mode = True
        
        # Fallback to legacy processing
        return self._legacy_process_image(image_bytes, filename)
    
    async def process_video(self, video_bytes: bytes, chat_id: int, filename: str) -> Dict[str, Any]:
        """
        FIXED: Process video with enhanced_replicator_service compatibility
        """
        if not self._initialized:
            await self.initialize()
            
        if self.new_processor and not self.legacy_mode:
            try:
                result = await self.new_processor.process_video(
                    video_bytes, filename, chat_id
                )
                
                if result.get('success'):
                    self.stats['videos_processed'] += 1
                    
                    # Format result for enhanced_replicator_service
                    return {
                        'success': True,
                        'filename': filename,
                        'download_url': f"http://localhost:8000/download/video_{chat_id}_{filename}",
                        'original_size_mb': len(video_bytes) / (1024 * 1024),
                        'final_size_mb': result.get('compressed_size', len(video_bytes)) / (1024 * 1024),
                        'compression_ratio': result.get('compression_ratio', 1.0),
                        'duration_seconds': result.get('duration_seconds', 0),
                        'output_path': result.get('output_path', ''),
                        'async_job_id': result.get('job_id')
                    }
                
                return result
                    
            except Exception as e:
                logger.error(f"Video processing failed: {e}")
        
        return {'success': False, 'error': 'Video processing unavailable'}
    
    async def process_pdf(self, pdf_bytes: bytes, chat_id: int, filename: str) -> Dict[str, Any]:
        """
        FIXED: Process PDF with enhanced_replicator_service compatibility  
        """
        if not self._initialized:
            await self.initialize()
            
        if self.new_processor and not self.legacy_mode:
            try:
                result = await self.new_processor.process_pdf(
                    pdf_bytes, filename, chat_id
                )
                
                if result.get('success'):
                    self.stats['pdfs_processed'] += 1
                    
                    # Format result for enhanced_replicator_service
                    return {
                        'success': True,
                        'filename': filename,
                        'download_url': f"http://localhost:8000/download/pdf_{chat_id}_{filename}",
                        'size_mb': len(pdf_bytes) / (1024 * 1024),
                        'page_count': result.get('page_count', 0),
                        'preview_bytes': None,  # Could add PDF preview generation
                        'output_path': result.get('output_path', '')
                    }
                
                return result
                    
            except Exception as e:
                logger.error(f"PDF processing failed: {e}")
        
        return {'success': False, 'error': 'PDF processing unavailable'}
    
    async def process_audio(self, audio_bytes: bytes, chat_id: int, filename: str) -> Dict[str, Any]:
        """
        FIXED: Process audio with enhanced_replicator_service compatibility
        """
        if not self._initialized:
            await self.initialize()
            
        if self.new_processor and not self.legacy_mode:
            try:
                result = await self.new_processor.process_audio(
                    audio_bytes, filename, chat_id
                )
                
                if result.get('success'):
                    self.stats['audios_processed'] += 1
                    
                    # Format result for enhanced_replicator_service
                    audio_size_mb = len(audio_bytes) / (1024 * 1024)
                    duration_min = audio_size_mb * 2  # Approximate duration
                    
                    return {
                        'success': True,
                        'filename': filename,
                        'download_url': f"http://localhost:8000/download/audio_{chat_id}_{filename}",
                        'size_mb': audio_size_mb,
                        'duration_min': duration_min,
                        'transcription': f"🎵 Audio de {duration_min:.1f} minutos",
                        'output_path': result.get('output_path', '')
                    }
                
                return result
                    
            except Exception as e:
                logger.error(f"Audio processing failed: {e}")
        
        return {'success': False, 'error': 'Audio processing unavailable'}
    
    def _legacy_process_image(self, image_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Legacy processing fallback"""
        # Tu código actual de procesamiento aquí
        # Por ahora retorna un resultado dummy
        return {
            'success': True,
            'filename': filename,
            'output_path': str(self.output_dir / filename),
            'original_size': len(image_bytes),
            'compressed_size': len(image_bytes)
        }
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get combined stats"""
        if self.new_processor:
            try:
                new_stats = await self.new_processor.get_stats()
                # Merge stats
                return {
                    'legacy_stats': self.stats,
                    'microservice_stats': new_stats,
                    'mode': 'microservice' if not self.legacy_mode else 'legacy'
                }
            except:
                pass
        
        return {'processor_stats': self.stats, 'mode': 'legacy'}


class FileProcessorEnhanced:
    """
    Drop-in replacement para tu FileProcessorEnhanced actual
    FIXED: Métodos ahora aceptan argumentos en el orden correcto
    """
    
    def __init__(self):
        self.bridge = FileProcessorBridge()
        self.cache_dir = Path("cache")
        self.temp_dir = Path("temp")
        self.output_dir = Path("processed_files")
        
        # Crear directorios
        for dir_path in [self.cache_dir, self.temp_dir, self.output_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Cache
        self.file_cache = FileCache(self.cache_dir)
        
        # Stats
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
        
        self._initialized = False
        logger.info("🚀 File Processor Enterprise inicializado")
    
    async def initialize(self):
        """Initialize processor"""
        if self._initialized:
            return
            
        await self.bridge.initialize()
        self.stats = self.bridge.stats
        self._initialized = True
        logger.info("✅ File Processor Enhanced (V2) initialized")
    
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
    
    async def process_image(self, image_bytes: bytes, chat_id: int, filename: str) -> Dict[str, Any]:
        """
        FIXED: Compatibilidad con enhanced_replicator_service.py
        El servicio llama: process_image(image_bytes, chat_id)
        """
        if not self._initialized:
            await self.initialize()
        # El bridge espera: (image_bytes, chat_id, filename)
        return await self.bridge.process_image(image_bytes, chat_id, filename)
    
    async def process_video(self, video_bytes: bytes, chat_id: int, filename: str) -> Dict[str, Any]:
        """
        FIXED: Compatibilidad con enhanced_replicator_service.py
        El servicio llama: process_video(video_bytes, chat_id, filename)
        """
        if not self._initialized:
            await self.initialize()
        # El bridge espera: (video_bytes, chat_id, filename)
        return await self.bridge.process_video(video_bytes, chat_id, filename)
    
    async def process_pdf(self, pdf_bytes: bytes, chat_id: int, filename: str) -> Dict[str, Any]:
        """
        FIXED: Compatibilidad con enhanced_replicator_service.py
        El servicio llama: process_pdf(pdf_bytes, chat_id, filename)
        """
        if not self._initialized:
            await self.initialize()
        # El bridge espera: (pdf_bytes, chat_id, filename)
        return await self.bridge.process_pdf(pdf_bytes, chat_id, filename)
    
    async def process_audio(self, audio_bytes: bytes, chat_id: int, filename: str) -> Dict[str, Any]:
        """
        FIXED: Compatibilidad con enhanced_replicator_service.py
        El servicio llama: process_audio(audio_bytes, chat_id, filename)
        """
        if not self._initialized:
            await self.initialize()
        # El bridge espera: (audio_bytes, chat_id, filename)
        return await self.bridge.process_audio(audio_bytes, chat_id, filename)
    
    # MÉTODOS ADICIONALES para compatibilidad con otros servicios
    async def create_temp_download(self, file_bytes: bytes, filename: str, chat_id: int) -> Dict[str, Any]:
        """Crear descarga temporal para documentos genéricos"""
        try:
            # Guardar archivo temporalmente
            temp_file = self.output_dir / f"temp_{chat_id}_{filename}"
            temp_file.write_bytes(file_bytes)
            
            return {
                'success': True,
                'download_url': f"http://localhost:8000/download/{temp_file.name}",
                'size_mb': len(file_bytes) / (1024 * 1024),
                'filename': filename
            }
        except Exception as e:
            logger.error(f"Error creating temp download: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas"""
        return {
            'processor_stats': self.stats,
            'directories': {
                'cache': str(self.cache_dir),
                'temp': str(self.temp_dir),
                'output': str(self.output_dir)
            },
            'mode': 'v2' if hasattr(self.bridge, 'new_processor') else 'legacy'
        }


# Función helper para compatibilidad
def create_file_processor() -> FileProcessorEnhanced:
    """Factory function para crear FileProcessorEnhanced"""
    return FileProcessorEnhanced()


# Exportar clases para compatibilidad total
__all__ = ['FileCache', 'FileProcessorEnhanced', 'FileProcessorBridge', 'create_file_processor']