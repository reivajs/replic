"""
FILE PROCESSOR - ARQUITECTURA MODULAR DEFINITIVA
================================================
Archivo: app/services/file_processor.py

Solución completa, escalable y sin parches
Compatible con enhanced_replicator_service.py
"""

import asyncio
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Protocol
import logging

# ============== PROTOCOLS FOR TYPE SAFETY ==============

class FileProcessorProtocol(Protocol):
    """Protocol para definir la interfaz del procesador"""
    async def process_image(self, image_bytes: bytes, filename: str, chat_id: int) -> Dict[str, Any]: ...
    async def process_video(self, video_bytes: bytes, filename: str, chat_id: int) -> Dict[str, Any]: ...
    async def process_pdf(self, pdf_bytes: bytes, filename: str, chat_id: int) -> Dict[str, Any]: ...
    async def process_audio(self, audio_bytes: bytes, filename: str, chat_id: int) -> Dict[str, Any]: ...
    async def get_stats(self) -> Dict[str, Any]: ...


# ============== IMPORTS ==============

# Intentar importar la versión V2 si existe
try:
    from app.services.file_processor_v2 import get_file_processor
    V2_AVAILABLE = True
except ImportError:
    V2_AVAILABLE = False
    get_file_processor = None

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


# ============== FILE CACHE ==============

class FileCache:
    """Cache simple y robusto para archivos procesados"""
    
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
        """Guardar índice de cache de forma segura"""
        try:
            clean_index = {}
            for key, value in self.cache_index.items():
                if isinstance(value, dict):
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
        """Generar hash único de archivo"""
        return hashlib.sha256(file_bytes).hexdigest()[:16]


# ============== V2 ADAPTER ==============

class V2ProcessorAdapter:
    """
    Adapter para el procesador V2
    Traduce las llamadas al formato esperado por V2
    """
    
    def __init__(self):
        self.processor = None
        self.initialized = False
    
    async def initialize(self):
        """Inicializar el procesador V2"""
        if not self.initialized and V2_AVAILABLE:
            try:
                self.processor = await get_file_processor()
                self.initialized = True
                logger.info("✅ V2 Processor Adapter initialized")
            except Exception as e:
                logger.error(f"Failed to initialize V2 processor: {e}")
                self.processor = None
    
    async def process_image(self, image_bytes: bytes, chat_id: int, filename: str) -> Dict[str, Any]:
        """Adaptar llamada para imagen"""
        if not self.processor:
            return {'success': False, 'error': 'V2 processor not available'}
        
        # V2 espera: (image_bytes, filename, chat_id)
        return await self.processor.process_image(image_bytes, filename, chat_id)
    
    async def process_video(self, video_bytes: bytes, chat_id: int, filename: str) -> Dict[str, Any]:
        """Adaptar llamada para video"""
        if not self.processor:
            return {'success': False, 'error': 'V2 processor not available'}
        
        # V2 espera: (video_bytes, filename, chat_id)
        result = await self.processor.process_video(video_bytes, filename, chat_id)
        
        # Enriquecer resultado para enhanced_replicator
        if result.get('success'):
            return {
                'success': True,
                'filename': filename,
                'download_url': f"http://localhost:8000/download/video_{chat_id}_{filename}",
                'original_size_mb': len(video_bytes) / (1024 * 1024),
                'final_size_mb': result.get('compressed_size', len(video_bytes)) / (1024 * 1024),
                'compression_ratio': result.get('compression_ratio', 1.0),
                'duration_seconds': result.get('duration_seconds', 0),
                'was_compressed': result.get('job_id') is not None
            }
        return result
    
    async def process_pdf(self, pdf_bytes: bytes, chat_id: int, filename: str) -> Dict[str, Any]:
        """Adaptar llamada para PDF"""
        if not self.processor:
            return {'success': False, 'error': 'V2 processor not available'}
        
        # V2 espera: (pdf_bytes, filename, chat_id)
        result = await self.processor.process_pdf(pdf_bytes, filename, chat_id)
        
        # Enriquecer resultado
        if result.get('success'):
            return {
                'success': True,
                'filename': filename,
                'download_url': f"http://localhost:8000/download/pdf_{chat_id}_{filename}",
                'size_mb': len(pdf_bytes) / (1024 * 1024),
                'page_count': result.get('page_count', 0),
                'preview_bytes': None,
                'job_id': result.get('job_id')
            }
        return result
    
    async def process_audio(self, audio_bytes: bytes, chat_id: int, filename: str) -> Dict[str, Any]:
        """Adaptar llamada para audio"""
        if not self.processor:
            return {'success': False, 'error': 'V2 processor not available'}
        
        # V2 espera: (audio_bytes, filename, chat_id)
        result = await self.processor.process_audio(audio_bytes, filename, chat_id)
        
        # Enriquecer resultado
        if result.get('success'):
            size_mb = len(audio_bytes) / (1024 * 1024)
            return {
                'success': True,
                'filename': filename,
                'download_url': f"http://localhost:8000/download/audio_{chat_id}_{filename}",
                'size_mb': size_mb,
                'duration_min': size_mb * 2,  # Estimación
                'transcription': f"🎵 Audio de {size_mb*2:.1f} minutos",
                'job_id': result.get('job_id')
            }
        return result
    
    async def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del procesador V2"""
        if self.processor:
            return await self.processor.get_stats()
        return {}


# ============== LEGACY PROCESSOR ==============

class LegacyProcessor:
    """
    Procesador legacy para cuando V2 no está disponible
    Implementación mínima pero funcional
    """
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.stats = {
            'images_processed': 0,
            'videos_processed': 0,
            'pdfs_processed': 0,
            'audios_processed': 0
        }
    
    async def process_image(self, image_bytes: bytes, chat_id: int, filename: str) -> Dict[str, Any]:
        """Procesamiento básico de imagen"""
        if not PIL_AVAILABLE:
            return {'success': False, 'error': 'PIL not available'}
        
        try:
            from io import BytesIO
            img = Image.open(BytesIO(image_bytes))
            
            # Compresión básica
            output = BytesIO()
            img.save(output, format='JPEG', quality=85, optimize=True)
            compressed = output.getvalue()
            
            # Guardar
            output_path = self.output_dir / f"img_{chat_id}_{filename}"
            output_path.write_bytes(compressed)
            
            self.stats['images_processed'] += 1
            
            return {
                'success': True,
                'filename': filename,
                'output_path': str(output_path),
                'original_size': len(image_bytes),
                'compressed_size': len(compressed)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def process_video(self, video_bytes: bytes, chat_id: int, filename: str) -> Dict[str, Any]:
        """Procesamiento básico de video"""
        # Sin procesamiento real en legacy
        output_path = self.output_dir / f"video_{chat_id}_{filename}"
        output_path.write_bytes(video_bytes)
        
        self.stats['videos_processed'] += 1
        
        return {
            'success': True,
            'filename': filename,
            'download_url': f"http://localhost:8000/download/{output_path.name}",
            'original_size_mb': len(video_bytes) / (1024 * 1024),
            'final_size_mb': len(video_bytes) / (1024 * 1024),
            'compression_ratio': 1.0,
            'duration_seconds': 0,
            'was_compressed': False
        }
    
    async def process_pdf(self, pdf_bytes: bytes, chat_id: int, filename: str) -> Dict[str, Any]:
        """Procesamiento básico de PDF"""
        output_path = self.output_dir / f"pdf_{chat_id}_{filename}"
        output_path.write_bytes(pdf_bytes)
        
        page_count = 0
        if PYMUPDF_AVAILABLE:
            try:
                pdf = fitz.open(stream=pdf_bytes, filetype="pdf")
                page_count = len(pdf)
                pdf.close()
            except:
                pass
        
        self.stats['pdfs_processed'] += 1
        
        return {
            'success': True,
            'filename': filename,
            'download_url': f"http://localhost:8000/download/{output_path.name}",
            'size_mb': len(pdf_bytes) / (1024 * 1024),
            'page_count': page_count,
            'preview_bytes': None
        }
    
    async def process_audio(self, audio_bytes: bytes, chat_id: int, filename: str) -> Dict[str, Any]:
        """Procesamiento básico de audio"""
        output_path = self.output_dir / f"audio_{chat_id}_{filename}"
        output_path.write_bytes(audio_bytes)
        
        size_mb = len(audio_bytes) / (1024 * 1024)
        self.stats['audios_processed'] += 1
        
        return {
            'success': True,
            'filename': filename,
            'download_url': f"http://localhost:8000/download/{output_path.name}",
            'size_mb': size_mb,
            'duration_min': size_mb * 2,
            'transcription': f"🎵 Audio de {size_mb*2:.1f} minutos"
        }


# ============== MAIN FILE PROCESSOR ==============

class FileProcessorEnterprise:
    """
    Procesador principal con arquitectura modular
    Compatible con enhanced_replicator_service.py
    
    FIRMA DE MÉTODOS:
    - Todos reciben: (bytes, chat_id, filename)
    - enhanced_replicator llama con estos 3 parámetros exactamente
    """
    
    def __init__(self):
        # Directorios
        self.cache_dir = Path(getattr(settings, 'CACHE_DIR', 'cache'))
        self.temp_dir = Path(getattr(settings, 'TEMP_DIR', 'temp'))
        self.output_dir = Path(getattr(settings, 'OUTPUT_DIR', 'processed_files'))
        
        # Crear directorios
        for dir_path in [self.cache_dir, self.temp_dir, self.output_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Componentes
        self.file_cache = FileCache(self.cache_dir)
        self.v2_adapter = V2ProcessorAdapter() if V2_AVAILABLE else None
        self.legacy_processor = LegacyProcessor(self.output_dir)
        
        # Estado
        self._initialized = False
        self._use_v2 = False
        
        # Estadísticas unificadas
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
        
        logger.info("🚀 FileProcessorEnhanced initialized")
    
    async def initialize(self):
        """Inicializar el procesador con la mejor estrategia disponible"""
        if self._initialized:
            return
        
        # Intentar usar V2 si está disponible
        if self.v2_adapter:
            try:
                await self.v2_adapter.initialize()
                self._use_v2 = True
                logger.info("✅ Using V2 processor (microservices architecture)")
            except Exception as e:
                logger.warning(f"⚠️ V2 initialization failed: {e}")
                self._use_v2 = False
        
        if not self._use_v2:
            logger.info("📌 Using legacy processor")
        
        await self._check_dependencies()
        self._initialized = True
        logger.info("✅ FileProcessorEnhanced ready")
    
    async def _check_dependencies(self):
        """Verificar dependencias del sistema"""
        dependencies = {
            'ffmpeg': await self._check_ffmpeg(),
            'pymupdf': PYMUPDF_AVAILABLE,
            'pil': PIL_AVAILABLE
        }
        
        logger.info("📦 Dependencies:")
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
    
    # ============== MÉTODOS PÚBLICOS CON FIRMA CORRECTA ==============
    
    async def process_image(self, image_bytes: bytes, chat_id: int, filename: str) -> Dict[str, Any]:
        """
        Procesar imagen
        Firma: (bytes, chat_id, filename) - Como lo llama enhanced_replicator
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            if self._use_v2:
                result = await self.v2_adapter.process_image(image_bytes, chat_id, filename)
            else:
                result = await self.legacy_processor.process_image(image_bytes, chat_id, filename)
            
            if result.get('success'):
                self.stats['images_processed'] += 1
                self.stats['total_size_processed'] += len(image_bytes)
            else:
                self.stats['errors'] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            self.stats['errors'] += 1
            return {'success': False, 'error': str(e)}
    
    async def process_video(self, video_bytes: bytes, chat_id: int, filename: str) -> Dict[str, Any]:
        """
        Procesar video
        Firma: (bytes, chat_id, filename) - Como lo llama enhanced_replicator
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            if self._use_v2:
                result = await self.v2_adapter.process_video(video_bytes, chat_id, filename)
            else:
                result = await self.legacy_processor.process_video(video_bytes, chat_id, filename)
            
            if result.get('success'):
                self.stats['videos_processed'] += 1
                self.stats['total_size_processed'] += len(video_bytes)
            else:
                self.stats['errors'] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing video: {e}")
            self.stats['errors'] += 1
            return {'success': False, 'error': str(e)}
    
    async def process_pdf(self, pdf_bytes: bytes, chat_id: int, filename: str) -> Dict[str, Any]:
        """
        Procesar PDF
        Firma: (bytes, chat_id, filename) - Como lo llama enhanced_replicator
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            if self._use_v2:
                result = await self.v2_adapter.process_pdf(pdf_bytes, chat_id, filename)
            else:
                result = await self.legacy_processor.process_pdf(pdf_bytes, chat_id, filename)
            
            if result.get('success'):
                self.stats['pdfs_processed'] += 1
                self.stats['total_size_processed'] += len(pdf_bytes)
            else:
                self.stats['errors'] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            self.stats['errors'] += 1
            return {'success': False, 'error': str(e)}
    
    async def process_audio(self, audio_bytes: bytes, chat_id: int, filename: str) -> Dict[str, Any]:
        """
        Procesar audio
        Firma: (bytes, chat_id, filename) - Como lo llama enhanced_replicator
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            if self._use_v2:
                result = await self.v2_adapter.process_audio(audio_bytes, chat_id, filename)
            else:
                result = await self.legacy_processor.process_audio(audio_bytes, chat_id, filename)
            
            if result.get('success'):
                self.stats['audios_processed'] += 1
                self.stats['total_size_processed'] += len(audio_bytes)
            else:
                self.stats['errors'] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            self.stats['errors'] += 1
            return {'success': False, 'error': str(e)}
    
    async def create_temp_download(self, file_bytes: bytes, filename: str, chat_id: int) -> Dict[str, Any]:
        """
        Crear descarga temporal para documentos genéricos
        Compatible con enhanced_replicator para documentos
        """
        try:
            output_path = self.output_dir / f"doc_{chat_id}_{filename}"
            output_path.write_bytes(file_bytes)
            
            return {
                'success': True,
                'download_url': f"http://localhost:8000/download/{output_path.name}",
                'size_mb': len(file_bytes) / (1024 * 1024),
                'filename': filename
            }
        except Exception as e:
            logger.error(f"Error creating temp download: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas unificadas"""
        stats = {
            'processor_stats': self.stats,
            'mode': 'v2' if self._use_v2 else 'legacy',
            'directories': {
                'cache': str(self.cache_dir),
                'temp': str(self.temp_dir),
                'output': str(self.output_dir)
            }
        }
        
        # Agregar stats de componentes si están disponibles
        if self._use_v2 and self.v2_adapter:
            asyncio.create_task(self._async_get_v2_stats(stats))
        elif self.legacy_processor:
            stats['legacy_stats'] = self.legacy_processor.stats
        
        return stats
    
    async def _async_get_v2_stats(self, stats_dict: Dict[str, Any]):
        """Helper para obtener stats de V2 de forma asíncrona"""
        try:
            v2_stats = await self.v2_adapter.get_stats()
            stats_dict['v2_stats'] = v2_stats
        except:
            pass
    
    async def get_health(self) -> Dict[str, Any]:
        """Health check del procesador"""
        return {
            'status': 'healthy' if self._initialized else 'not_initialized',
            'mode': 'v2' if self._use_v2 else 'legacy',
            'dependencies': {
                'pil': PIL_AVAILABLE,
                'pymupdf': PYMUPDF_AVAILABLE,
                'v2_available': V2_AVAILABLE
            }
        }


# ============== FACTORY Y EXPORTS ==============

def create_file_processor() -> FileProcessorEnhanced:
    """Factory function para crear FileProcessorEnhanced"""
    return FileProcessorEnhanced()


# NO exportar FileProcessorBridge para evitar confusión
__all__ = ['FileCache', 'FileProcessorEnhanced', 'create_file_processor']