"""
Enterprise File Processor Service
=================================
Servicio enterprise para procesamiento de archivos multimedia

Archivo: app/services/file_processor.py
"""

import asyncio
import subprocess
import tempfile
import shutil
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import hashlib
import mimetypes

try:
    import fitz  # PyMuPDF para PDFs
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from app.utils.logger import setup_logger
from app.config.settings import get_settings

logger = setup_logger(__name__)
settings = get_settings()

class FileCache:
    """Cache inteligente para archivos procesados"""
    
    def __init__(self, cache_dir: Path, max_cache_size_gb: float = 2.0):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_cache_size = max_cache_size_gb * 1024 * 1024 * 1024  # GB to bytes
        self.cache_index_file = cache_dir / "cache_index.json"
        self.cache_index = self._load_cache_index()
    
    def _load_cache_index(self) -> Dict[str, Any]:
        """Cargar índice de cache"""
        if self.cache_index_file.exists():
            try:
                with open(self.cache_index_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error cargando cache index: {e}")
        return {}
    
    def _save_cache_index(self):
        """Guardar índice de cache"""
        try:
            with open(self.cache_index_file, 'w') as f:
                json.dump(self.cache_index, f)
        except Exception as e:
            logger.error(f"Error guardando cache index: {e}")
    
    def get_file_hash(self, file_bytes: bytes) -> str:
        """Generar hash único para archivo"""
        return hashlib.sha256(file_bytes).hexdigest()[:16]
    
    def get_cached_result(self, file_hash: str, operation: str) -> Optional[Dict[str, Any]]:
        """Obtener resultado cacheado"""
        cache_key = f"{file_hash}_{operation}"
        if cache_key in self.cache_index:
            cache_info = self.cache_index[cache_key]
            cache_file = self.cache_dir / cache_info['filename']
            
            if cache_file.exists():
                # Actualizar último acceso
                cache_info['last_accessed'] = datetime.now().isoformat()
                self._save_cache_index()
                return cache_info
        
        return None
    
    def cache_result(self, file_hash: str, operation: str, result: Dict[str, Any], 
                    output_bytes: Optional[bytes] = None) -> str:
        """Cachear resultado"""
        cache_key = f"{file_hash}_{operation}"
        cache_filename = f"{cache_key}_{datetime.now().timestamp()}"
        
        cache_info = {
            'filename': cache_filename,
            'operation': operation,
            'result': result,
            'created': datetime.now().isoformat(),
            'last_accessed': datetime.now().isoformat(),
            'size_bytes': len(output_bytes) if output_bytes else 0
        }
        
        # Guardar archivo si hay bytes
        if output_bytes:
            cache_file = self.cache_dir / cache_filename
            cache_file.write_bytes(output_bytes)
        
        self.cache_index[cache_key] = cache_info
        self._save_cache_index()
        
        # Limpieza de cache si es necesario
        self._cleanup_cache_if_needed()
        
        return cache_filename
    
    def _cleanup_cache_if_needed(self):
        """Limpiar cache si excede el tamaño máximo"""
        total_size = sum(info.get('size_bytes', 0) for info in self.cache_index.values())
        
        if total_size > self.max_cache_size:
            # Ordenar por último acceso
            sorted_entries = sorted(
                self.cache_index.items(),
                key=lambda x: x[1].get('last_accessed', '1970-01-01')
            )
            
            # Eliminar entradas más antiguas
            removed_size = 0
            target_remove = total_size - (self.max_cache_size * 0.8)  # Liberar 20% extra
            
            for cache_key, cache_info in sorted_entries:
                if removed_size >= target_remove:
                    break
                
                cache_file = self.cache_dir / cache_info['filename']
                if cache_file.exists():
                    cache_file.unlink()
                    removed_size += cache_info.get('size_bytes', 0)
                
                del self.cache_index[cache_key]
            
            self._save_cache_index()
            logger.info(f"🧹 Cache limpiado: {removed_size / (1024*1024):.1f}MB liberados")

class FileProcessorEnhanced:
    """
    🚀 FILE PROCESSOR ENTERPRISE
    ============================
    
    Características Enterprise:
    ✅ Cache inteligente de archivos procesados
    ✅ Procesamiento paralelo de videos
    ✅ Compresión automática con FFmpeg
    ✅ Preview automático de PDFs
    ✅ Transcripción simulada de audios
    ✅ Cleanup automático de archivos temporales
    ✅ Estadísticas detalladas de procesamiento
    ✅ Health monitoring
    ✅ Rate limiting de recursos
    """
    
    def __init__(self):
        self.temp_dir = Path("temp_files")
        self.cache_dir = Path("cache_files")
        self.processed_dir = Path("processed_files")
        
        # Crear directorios
        for directory in [self.temp_dir, self.cache_dir, self.processed_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Cache inteligente
        self.cache = FileCache(self.cache_dir, max_cache_size_gb=2.0)
        
        # Estadísticas enterprise
        self.stats = {
            'pdfs_processed': 0,
            'videos_processed': 0,
            'audios_processed': 0,
            'images_processed': 0,
            'documents_processed': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'total_processing_time': 0.0,
            'avg_processing_time': 0.0,
            'errors': 0,
            'start_time': datetime.now(),
            'temp_files_created': 0,
            'temp_files_cleaned': 0
        }
        
        # Configuración enterprise
        self.config = {
            'max_file_size_mb': 50,
            'video_compression_quality': 23,  # CRF value for FFmpeg
            'max_video_duration': 300,  # 5 minutes
            'cleanup_interval_hours': 6,
            'max_concurrent_processing': 3,
            'ffmpeg_timeout': 180  # 3 minutes
        }
        
        # Semáforo para controlar procesamiento concurrente
        self.processing_semaphore = asyncio.Semaphore(self.config['max_concurrent_processing'])
        
        logger.info("🚀 File Processor Enterprise inicializado")
    
    async def initialize(self):
        """Inicializar servicio enterprise"""
        try:
            # Verificar dependencias
            await self._check_dependencies()
            
            # Iniciar cleanup automático
            asyncio.create_task(self._periodic_cleanup())
            
            logger.info("✅ File Processor Enterprise inicializado correctamente")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando File Processor: {e}")
            raise
    
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
        """Verificar si FFmpeg está disponible"""
        try:
            result = await asyncio.create_subprocess_exec(
                'ffmpeg', '-version',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.wait()
            return result.returncode == 0
        except Exception:
            return False
    
    async def process_pdf(self, pdf_bytes: bytes, chat_id: int, filename: str) -> Dict[str, Any]:
        """✅ Procesar PDF con preview enterprise"""
        async with self.processing_semaphore:
            start_time = datetime.now()
            
            try:
                # Verificar cache
                file_hash = self.cache.get_file_hash(pdf_bytes)
                cached_result = self.cache.get_cached_result(file_hash, 'pdf_process')
                
                if cached_result:
                    self.stats['cache_hits'] += 1
                    logger.info(f"📄 PDF encontrado en cache: {filename}")
                    return cached_result['result']
                
                self.stats['cache_misses'] += 1
                
                # Verificar tamaño
                size_mb = len(pdf_bytes) / (1024 * 1024)
                if size_mb > self.config['max_file_size_mb']:
                    return {
                        "success": False,
                        "error": f"Archivo muy grande ({size_mb:.1f}MB)",
                        "max_size_mb": self.config['max_file_size_mb']
                    }
                
                # Crear archivo temporal
                temp_pdf = self.temp_dir / f"pdf_{chat_id}_{datetime.now().timestamp()}.pdf"
                temp_pdf.write_bytes(pdf_bytes)
                self.stats['temp_files_created'] += 1
                
                preview_bytes = None
                page_count = 0
                
                if PYMUPDF_AVAILABLE:
                    try:
                        # Generar preview de primera página
                        doc = fitz.open(temp_pdf)
                        page_count = len(doc)
                        
                        if page_count > 0:
                            page = doc[0]
                            # Generar imagen de alta calidad
                            matrix = fitz.Matrix(2.0, 2.0)  # 2x scale
                            pix = page.get_pixmap(matrix=matrix)
                            preview_bytes = pix.tobytes("png")
                        
                        doc.close()
                        
                    except Exception as e:
                        logger.warning(f"Error generando preview PDF: {e}")
                
                # Crear archivo procesado
                processed_file = self.processed_dir / f"pdf_{file_hash}_{chat_id}.pdf"
                shutil.copy2(temp_pdf, processed_file)
                
                # URL de descarga
                download_url = f"http://localhost:8000/download/{processed_file.name}"
                
                result = {
                    "success": True,
                    "preview_bytes": preview_bytes,
                    "download_url": download_url,
                    "size_mb": size_mb,
                    "page_count": page_count,
                    "filename": filename,
                    "processing_time": (datetime.now() - start_time).total_seconds()
                }
                
                # Cachear resultado
                self.cache.cache_result(file_hash, 'pdf_process', result, preview_bytes)
                
                # Cleanup
                temp_pdf.unlink()
                self.stats['temp_files_cleaned'] += 1
                
                self.stats['pdfs_processed'] += 1
                self._update_processing_stats(start_time)
                
                logger.info(f"📄 PDF procesado: {filename} ({page_count} páginas)")
                return result
                
            except Exception as e:
                self.stats['errors'] += 1
                logger.error(f"❌ Error procesando PDF {filename}: {e}")
                return {"success": False, "error": str(e)}
    
    async def process_video(self, video_bytes: bytes, chat_id: int, 
                           filename: str = "video.mp4") -> Dict[str, Any]:
        """✅ Procesar video con compresión FFmpeg enterprise"""
        async with self.processing_semaphore:
            start_time = datetime.now()
            
            try:
                # Verificar cache
                file_hash = self.cache.get_file_hash(video_bytes)
                cached_result = self.cache.get_cached_result(file_hash, 'video_process')
                
                if cached_result:
                    self.stats['cache_hits'] += 1
                    logger.info(f"🎬 Video encontrado en cache: {filename}")
                    return cached_result['result']
                
                self.stats['cache_misses'] += 1
                
                # Verificar tamaño inicial
                original_size_mb = len(video_bytes) / (1024 * 1024)
                
                # Crear archivos temporales
                input_video = self.temp_dir / f"input_{chat_id}_{datetime.now().timestamp()}.mp4"
                output_video = self.temp_dir / f"output_{chat_id}_{datetime.now().timestamp()}.mp4"
                
                input_video.write_bytes(video_bytes)
                self.stats['temp_files_created'] += 1
                
                # Verificar duración del video
                duration = await self._get_video_duration(input_video)
                if duration > self.config['max_video_duration']:
                    return {
                        "success": False,
                        "error": f"Video muy largo ({duration:.1f}s)",
                        "max_duration": self.config['max_video_duration']
                    }
                
                # Determinar si necesita compresión
                needs_compression = (
                    original_size_mb > 8 or  # Discord limit
                    duration > 60  # Compress videos longer than 1 minute
                )
                
                if needs_compression:
                    # Comprimir con FFmpeg
                    compressed_bytes = await self._compress_video_ffmpeg(
                        input_video, output_video, chat_id
                    )
                    
                    if compressed_bytes:
                        final_bytes = compressed_bytes
                        final_size_mb = len(compressed_bytes) / (1024 * 1024)
                        was_compressed = True
                    else:
                        # Fallback si falla compresión
                        final_bytes = video_bytes
                        final_size_mb = original_size_mb
                        was_compressed = False
                else:
                    final_bytes = video_bytes
                    final_size_mb = original_size_mb
                    was_compressed = False
                
                # Guardar archivo procesado
                processed_file = self.processed_dir / f"video_{file_hash}_{chat_id}.mp4"
                processed_file.write_bytes(final_bytes)
                
                # URL de descarga
                download_url = f"http://localhost:8000/download/{processed_file.name}"
                
                result = {
                    "success": True,
                    "download_url": download_url,
                    "original_size_mb": original_size_mb,
                    "final_size_mb": final_size_mb,
                    "compression_ratio": final_size_mb / original_size_mb if original_size_mb > 0 else 1.0,
                    "duration_seconds": duration,
                    "was_compressed": was_compressed,
                    "filename": filename,
                    "processing_time": (datetime.now() - start_time).total_seconds()
                }
                
                # Cachear resultado
                self.cache.cache_result(file_hash, 'video_process', result)
                
                # Cleanup
                for temp_file in [input_video, output_video]:
                    if temp_file.exists():
                        temp_file.unlink()
                        self.stats['temp_files_cleaned'] += 1
                
                self.stats['videos_processed'] += 1
                self._update_processing_stats(start_time)
                
                logger.info(f"🎬 Video procesado: {filename} ({original_size_mb:.1f}MB → {final_size_mb:.1f}MB)")
                return result
                
            except Exception as e:
                self.stats['errors'] += 1
                logger.error(f"❌ Error procesando video {filename}: {e}")
                return {"success": False, "error": str(e)}
    
    async def _get_video_duration(self, video_path: Path) -> float:
        """Obtener duración del video con FFprobe"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', str(video_path)
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=30
            )
            
            if process.returncode == 0:
                probe_data = json.loads(stdout.decode())
                return float(probe_data['format']['duration'])
            else:
                logger.warning(f"FFprobe error: {stderr.decode()}")
                return 0.0
                
        except Exception as e:
            logger.warning(f"Error obteniendo duración de video: {e}")
            return 0.0
    
    async def _compress_video_ffmpeg(self, input_path: Path, output_path: Path, 
                                   chat_id: int) -> Optional[bytes]:
        """Comprimir video con FFmpeg"""
        try:
            # Comando FFmpeg optimizado para Discord
            cmd = [
                'ffmpeg', '-i', str(input_path),
                '-c:v', 'libx264',
                '-crf', str(self.config['video_compression_quality']),
                '-preset', 'medium',
                '-c:a', 'aac',
                '-b:a', '128k',
                '-movflags', '+faststart',
                '-y',  # Overwrite output
                str(output_path)
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.config['ffmpeg_timeout']
            )
            
            if process.returncode == 0 and output_path.exists():
                compressed_bytes = output_path.read_bytes()
                logger.info(f"✅ Video comprimido con FFmpeg para grupo {chat_id}")
                return compressed_bytes
            else:
                logger.warning(f"FFmpeg error: {stderr.decode()}")
                return None
                
        except asyncio.TimeoutError:
            logger.error("⏰ Timeout comprimiendo video con FFmpeg")
            return None
        except Exception as e:
            logger.error(f"❌ Error comprimiendo video: {e}")
            return None
    
    async def process_audio(self, audio_bytes: bytes, chat_id: int, 
                           filename: str) -> Dict[str, Any]:
        """✅ Procesar audio con transcripción simulada"""
        start_time = datetime.now()
        
        try:
            # Verificar cache
            file_hash = self.cache.get_file_hash(audio_bytes)
            cached_result = self.cache.get_cached_result(file_hash, 'audio_process')
            
            if cached_result:
                self.stats['cache_hits'] += 1
                return cached_result['result']
            
            self.stats['cache_misses'] += 1
            
            # Crear archivo temporal
            temp_audio = self.temp_dir / f"audio_{chat_id}_{datetime.now().timestamp()}.mp3"
            temp_audio.write_bytes(audio_bytes)
            self.stats['temp_files_created'] += 1
            
            # Obtener duración
            duration = await self._get_audio_duration(temp_audio)
            
            # Transcripción simulada (en producción usarías Whisper API)
            transcription = f"🎵 Audio de {duration:.1f} segundos"
            if duration > 10:
                transcription += " - Transcripción automática disponible próximamente"
            
            # Guardar archivo procesado
            processed_file = self.processed_dir / f"audio_{file_hash}_{chat_id}.mp3"
            shutil.copy2(temp_audio, processed_file)
            
            download_url = f"http://localhost:8000/download/{processed_file.name}"
            
            result = {
                "success": True,
                "download_url": download_url,
                "transcription": transcription,
                "duration_min": duration / 60,
                "size_mb": len(audio_bytes) / (1024*1024),
                "filename": filename,
                "processing_time": (datetime.now() - start_time).total_seconds()
            }
            
            # Cachear resultado
            self.cache.cache_result(file_hash, 'audio_process', result)
            
            # Cleanup
            temp_audio.unlink()
            self.stats['temp_files_cleaned'] += 1
            
            self.stats['audios_processed'] += 1
            self._update_processing_stats(start_time)
            
            return result
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"❌ Error procesando audio: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_audio_duration(self, audio_path: Path) -> float:
        """Obtener duración del audio"""
        try:
            # Simular duración basada en tamaño (estimación)
            size_mb = audio_path.stat().st_size / (1024 * 1024)
            # Estimación: ~1MB por minuto para MP3 128kbps
            estimated_duration = size_mb * 60
            return estimated_duration
        except Exception:
            return 60.0  # Default 1 minute
    
    async def create_temp_download(self, file_bytes: bytes, filename: str, 
                                 chat_id: int) -> Dict[str, Any]:
        """Crear enlace de descarga temporal para documentos"""
        try:
            file_hash = self.cache.get_file_hash(file_bytes)
            
            # Crear archivo en processed_dir
            safe_filename = "".join(c for c in filename if c.isalnum() or c in '.-_')
            processed_file = self.processed_dir / f"doc_{file_hash}_{chat_id}_{safe_filename}"
            processed_file.write_bytes(file_bytes)
            
            download_url = f"http://localhost:8000/download/{processed_file.name}"
            
            self.stats['documents_processed'] += 1
            
            return {
                "success": True,
                "download_url": download_url,
                "size_mb": len(file_bytes) / (1024*1024),
                "filename": filename
            }
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"❌ Error creando enlace temporal: {e}")
            return {"success": False, "error": str(e)}
    
    def _update_processing_stats(self, start_time: datetime):
        """Actualizar estadísticas de procesamiento"""
        processing_time = (datetime.now() - start_time).total_seconds()
        self.stats['total_processing_time'] += processing_time
        
        total_processed = (
            self.stats['pdfs_processed'] + 
            self.stats['videos_processed'] + 
            self.stats['audios_processed'] +
            self.stats['documents_processed']
        )
        
        if total_processed > 0:
            self.stats['avg_processing_time'] = (
                self.stats['total_processing_time'] / total_processed
            )
    
    async def _periodic_cleanup(self):
        """Cleanup periódico de archivos temporales"""
        while True:
            try:
                await asyncio.sleep(self.config['cleanup_interval_hours'] * 3600)
                await self._cleanup_old_files()
            except Exception as e:
                logger.error(f"Error en cleanup periódico: {e}")
    
    async def _cleanup_old_files(self):
        """Limpiar archivos antiguos"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=24)
            cleaned_count = 0
            
            for directory in [self.temp_dir, self.processed_dir]:
                for file_path in directory.iterdir():
                    if file_path.is_file():
                        file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if file_time < cutoff_time:
                            file_path.unlink()
                            cleaned_count += 1
            
            if cleaned_count > 0:
                logger.info(f"🧹 Cleanup: {cleaned_count} archivos eliminados")
                
        except Exception as e:
            logger.error(f"Error en cleanup: {e}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas enterprise"""
        uptime = (datetime.now() - self.stats['start_time']).total_seconds()
        
        return {
            **self.stats,
            'uptime_seconds': uptime,
            'uptime_hours': uptime / 3600,
            'cache_hit_rate': (
                (self.stats['cache_hits'] / 
                 max(self.stats['cache_hits'] + self.stats['cache_misses'], 1)) * 100
            ),
            'total_files_processed': (
                self.stats['pdfs_processed'] + 
                self.stats['videos_processed'] + 
                self.stats['audios_processed'] +
                self.stats['documents_processed']
            ),
            'temp_files_ratio': (
                self.stats['temp_files_cleaned'] / 
                max(self.stats['temp_files_created'], 1)
            )
        }
    
    async def get_health(self) -> Dict[str, Any]:
        """Health check del servicio"""
        return {
            "status": "healthy",
            "dependencies": {
                "ffmpeg": await self._check_ffmpeg(),
                "pymupdf": PYMUPDF_AVAILABLE,
                "pil": PIL_AVAILABLE
            },
            "disk_usage": {
                "temp_dir_files": len(list(self.temp_dir.iterdir())),
                "cache_dir_files": len(list(self.cache_dir.iterdir())),
                "processed_dir_files": len(list(self.processed_dir.iterdir()))
            },
            "processing_queue": self.processing_semaphore._value,
            "stats": await self.get_stats()
        }