"""
FILE PROCESSOR MICROSERVICE v2.0 - ZERO COST ARCHITECTURE
=========================================================
Archivo: app/services/file_processor_v2.py

Versión completa y corregida
Optimizado para laptop personal con zero infrastructure cost
"""

import asyncio
import hashlib
import json
import sqlite3
import subprocess
import tempfile
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List
from concurrent.futures import ThreadPoolExecutor
import pickle

# Importar lz4 si está disponible
try:
    import lz4.frame
    LZ4_AVAILABLE = True
except ImportError:
    LZ4_AVAILABLE = False
    print("⚠️ LZ4 not available, using uncompressed cache")

# Otros imports opcionales
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Import configuración y logger
try:
    from app.utils.logger import setup_logger
    from app.config.settings import get_settings
    logger = setup_logger(__name__)
    settings = get_settings()
except:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    class Settings:
        pass
    settings = Settings()


# ============== ENUMS Y DATACLASSES ==============

class FileType(Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    PDF = "pdf"
    DOCUMENT = "document"
    UNKNOWN = "unknown"

class ProcessingStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CACHED = "cached"

@dataclass
class ProcessingJob:
    """Job de procesamiento con toda la metadata"""
    job_id: str
    file_type: FileType
    file_hash: str
    original_size: int
    chat_id: int
    filename: str
    status: ProcessingStatus = ProcessingStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    priority: int = 0
    retry_count: int = 0
    max_retries: int = 3


# ============== CACHE SIMPLE (Sin LZ4 si no está disponible) ==============

class SimpleCache:
    """Cache simple usando pickle sin compresión"""
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_index = {}
    
    async def get(self, key: str) -> Optional[Any]:
        """Obtener del cache"""
        cache_file = self.cache_dir / f"{key}.pkl"
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
            except:
                return None
        return None
    
    async def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> bool:
        """Guardar en cache"""
        try:
            cache_file = self.cache_dir / f"{key}.pkl"
            with open(cache_file, 'wb') as f:
                pickle.dump(value, f)
            return True
        except:
            return False
    
    async def delete(self, key: str) -> bool:
        """Eliminar del cache"""
        cache_file = self.cache_dir / f"{key}.pkl"
        if cache_file.exists():
            cache_file.unlink()
        return True
    
    async def get_stats(self) -> Dict[str, Any]:
        """Estadísticas del cache"""
        cache_files = list(self.cache_dir.glob("*.pkl"))
        total_size = sum(f.stat().st_size for f in cache_files)
        return {
            'total_entries': len(cache_files),
            'total_size_mb': total_size / (1024 * 1024),
            'cache_dir': str(self.cache_dir)
        }


# ============== QUEUE MANAGER SIMPLE ==============

class SimpleQueueManager:
    """Queue manager simplificado"""
    
    def __init__(self):
        self.pending_queue = deque()
        self.processing_queue = {}
        self.completed_queue = deque(maxlen=100)
        self.failed_queue = deque(maxlen=50)
    
    async def enqueue(self, job: ProcessingJob) -> str:
        """Encolar job"""
        self.pending_queue.append(job)
        logger.debug(f"📥 Job {job.job_id} enqueued")
        return job.job_id
    
    async def dequeue(self) -> Optional[ProcessingJob]:
        """Obtener siguiente job"""
        if self.pending_queue:
            job = self.pending_queue.popleft()
            job.status = ProcessingStatus.PROCESSING
            job.started_at = datetime.now()
            self.processing_queue[job.job_id] = job
            return job
        return None
    
    async def complete_job(self, job_id: str, result: Dict[str, Any]):
        """Marcar job como completado"""
        if job_id in self.processing_queue:
            job = self.processing_queue.pop(job_id)
            job.status = ProcessingStatus.COMPLETED
            job.completed_at = datetime.now()
            job.result = result
            self.completed_queue.append(job)
    
    async def fail_job(self, job_id: str, error: str):
        """Marcar job como fallido"""
        if job_id in self.processing_queue:
            job = self.processing_queue.pop(job_id)
            job.status = ProcessingStatus.FAILED
            job.error = error
            job.retry_count += 1
            
            if job.retry_count < job.max_retries:
                job.status = ProcessingStatus.PENDING
                await self.enqueue(job)
                logger.info(f"🔄 Retrying job {job_id}")
            else:
                self.failed_queue.append(job)
    
    def get_job_by_id(self, job_id: str) -> Optional[ProcessingJob]:
        """Buscar job por ID"""
        # Buscar en processing
        if job_id in self.processing_queue:
            return self.processing_queue[job_id]
        
        # Buscar en completed
        for job in self.completed_queue:
            if job.job_id == job_id:
                return job
        
        # Buscar en failed
        for job in self.failed_queue:
            if job.job_id == job_id:
                return job
        
        # Buscar en pending
        for job in self.pending_queue:
            if job.job_id == job_id:
                return job
        
        return None
    
    async def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas"""
        return {
            'pending': len(self.pending_queue),
            'processing': len(self.processing_queue),
            'completed': len(self.completed_queue),
            'failed': len(self.failed_queue)
        }


# ============== FILE PROCESSOR WORKER ==============

class FileProcessorWorker:
    """Worker para procesamiento"""
    
    def __init__(self, worker_id: int, cache: SimpleCache):
        self.worker_id = worker_id
        self.cache = cache
        self.thread_pool = ThreadPoolExecutor(max_workers=1)
    
    async def process_image(self, image_bytes: bytes, job: ProcessingJob) -> Dict[str, Any]:
        """Procesar imagen"""
        if not PIL_AVAILABLE:
            return {'success': False, 'error': 'PIL not available'}
        
        try:
            cache_key = f"img_{job.file_hash}"
            cached = await self.cache.get(cache_key)
            if cached:
                return cached
            
            from io import BytesIO
            img = Image.open(BytesIO(image_bytes))
            
            # Comprimir
            max_size = (1920, 1080)
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            output = BytesIO()
            img.save(output, format='JPEG', quality=85, optimize=True)
            compressed = output.getvalue()
            
            result = {
                'success': True,
                'filename': job.filename,
                'original_size': len(image_bytes),
                'compressed_size': len(compressed),
                'data': compressed
            }
            
            await self.cache.set(cache_key, result)
            return result
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def process_video(self, video_bytes: bytes, job: ProcessingJob) -> Dict[str, Any]:
        """Procesar video"""
        try:
            temp_dir = Path(tempfile.gettempdir())
            temp_input = temp_dir / f"in_{job.job_id}.mp4"
            temp_output = temp_dir / f"out_{job.job_id}.mp4"
            
            temp_input.write_bytes(video_bytes)
            
            cmd = [
                'ffmpeg', '-i', str(temp_input),
                '-c:v', 'libx264', '-crf', '23',
                '-c:a', 'aac', '-b:a', '128k',
                str(temp_output), '-y'
            ]
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            
            await proc.communicate()
            
            if proc.returncode == 0 and temp_output.exists():
                compressed = temp_output.read_bytes()
                temp_input.unlink()
                temp_output.unlink()
                
                return {
                    'success': True,
                    'filename': job.filename,
                    'original_size': len(video_bytes),
                    'compressed_size': len(compressed),
                    'data': compressed
                }
            
            return {'success': False, 'error': 'FFmpeg failed'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def process_pdf(self, pdf_bytes: bytes, job: ProcessingJob) -> Dict[str, Any]:
        """Procesar PDF"""
        return {
            'success': True,
            'filename': job.filename,
            'file_size': len(pdf_bytes),
            'data': pdf_bytes
        }
    
    async def process_audio(self, audio_bytes: bytes, job: ProcessingJob) -> Dict[str, Any]:
        """Procesar audio"""
        return {
            'success': True,
            'filename': job.filename,
            'file_size': len(audio_bytes),
            'data': audio_bytes
        }


# ============== MAIN PROCESSOR ==============

class FileProcessorMicroservice:
    """Procesador principal"""
    
    def __init__(self):
        self.data_dir = Path("processor_data")
        self.data_dir.mkdir(exist_ok=True)
        
        self.cache = SimpleCache(self.data_dir / "cache")
        self.queue_manager = SimpleQueueManager()
        
        self.workers = []
        self.num_workers = 2  # Reducido para laptop
        
        self.stats = {
            'total_processed': 0,
            'total_failed': 0,
            'start_time': datetime.now()
        }
        
        self.is_running = False
    
    async def initialize(self):
        """Inicializar servicio"""
        try:
            for i in range(self.num_workers):
                worker = FileProcessorWorker(i, self.cache)
                self.workers.append(worker)
            
            self.is_running = True
            asyncio.create_task(self._processing_loop())
            
            logger.info(f"✅ File Processor initialized with {self.num_workers} workers")
            
        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            raise
    
    async def process_file(self, file_bytes: bytes, filename: str, 
                          chat_id: int, priority: int = 0) -> str:
        """Procesar archivo"""
        file_type = self._detect_file_type(filename, file_bytes)
        file_hash = hashlib.sha256(file_bytes).hexdigest()[:16]
        
        job = ProcessingJob(
            job_id=f"{file_hash}_{datetime.now().timestamp()}",
            file_type=file_type,
            file_hash=file_hash,
            original_size=len(file_bytes),
            chat_id=chat_id,
            filename=filename,
            priority=priority
        )
        
        # Guardar archivo temporalmente
        temp_file = self.data_dir / "temp" / f"{job.job_id}.bin"
        temp_file.parent.mkdir(exist_ok=True)
        temp_file.write_bytes(file_bytes)
        
        await self.queue_manager.enqueue(job)
        return job.job_id
    
    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Obtener estado del job"""
        job = self.queue_manager.get_job_by_id(job_id)
        
        if not job:
            return {'status': 'not_found'}
        
        response = {
            'job_id': job.job_id,
            'status': job.status.value,
            'filename': job.filename,
            'file_type': job.file_type.value
        }
        
        if job.status == ProcessingStatus.COMPLETED and job.result:
            response['result'] = job.result
        elif job.status == ProcessingStatus.FAILED and job.error:
            response['error'] = job.error
        
        return response
    
    def _detect_file_type(self, filename: str, file_bytes: bytes) -> FileType:
        """Detectar tipo de archivo"""
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        
        if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
            return FileType.IMAGE
        elif ext in ['mp4', 'avi', 'mov', 'mkv']:
            return FileType.VIDEO
        elif ext in ['mp3', 'wav', 'ogg']:
            return FileType.AUDIO
        elif ext == 'pdf':
            return FileType.PDF
        
        return FileType.UNKNOWN
    
    async def _processing_loop(self):
        """Loop de procesamiento"""
        logger.info("🔄 Processing loop started")
        
        while self.is_running:
            try:
                job = await self.queue_manager.dequeue()
                
                if not job:
                    await asyncio.sleep(0.1)
                    continue
                
                # Cargar archivo
                temp_file = self.data_dir / "temp" / f"{job.job_id}.bin"
                if not temp_file.exists():
                    await self.queue_manager.fail_job(job.job_id, "File not found")
                    continue
                
                file_bytes = temp_file.read_bytes()
                
                # Seleccionar worker
                worker = self.workers[hash(job.job_id) % len(self.workers)]
                
                # Procesar según tipo
                if job.file_type == FileType.IMAGE:
                    result = await worker.process_image(file_bytes, job)
                elif job.file_type == FileType.VIDEO:
                    result = await worker.process_video(file_bytes, job)
                elif job.file_type == FileType.PDF:
                    result = await worker.process_pdf(file_bytes, job)
                elif job.file_type == FileType.AUDIO:
                    result = await worker.process_audio(file_bytes, job)
                else:
                    result = {'success': False, 'error': 'Unsupported type'}
                
                if result.get('success'):
                    # Guardar resultado
                    if 'data' in result:
                        output_file = self.data_dir / "processed" / f"{job.job_id}.out"
                        output_file.parent.mkdir(exist_ok=True)
                        output_file.write_bytes(result['data'])
                        result['output_path'] = str(output_file)
                        del result['data']
                    
                    await self.queue_manager.complete_job(job.job_id, result)
                    self.stats['total_processed'] += 1
                    
                    # Limpiar temporal
                    temp_file.unlink()
                    
                    logger.info(f"✅ Processed {job.filename}")
                else:
                    await self.queue_manager.fail_job(job.job_id, result.get('error'))
                    self.stats['total_failed'] += 1
                    
            except Exception as e:
                logger.error(f"Processing error: {e}")
                await asyncio.sleep(1)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas"""
        cache_stats = await self.cache.get_stats()
        queue_stats = await self.queue_manager.get_stats()
        
        return {
            'service': {
                'total_processed': self.stats['total_processed'],
                'total_failed': self.stats['total_failed'],
                'uptime': (datetime.now() - self.stats['start_time']).total_seconds()
            },
            'cache': cache_stats,
            'queue': queue_stats
        }
    
    async def shutdown(self):
        """Apagar servicio"""
        self.is_running = False
        await asyncio.sleep(1)
        logger.info("✅ Service stopped")


# ============== API INTERFACE ==============

class FileProcessorAPI:
    """API para compatibilidad"""
    
    def __init__(self, processor: FileProcessorMicroservice):
        self.processor = processor
    
    async def process_image(self, image_bytes: bytes, filename: str, 
                           chat_id: int = 0) -> Dict[str, Any]:
        """Procesar imagen"""
        job_id = await self.processor.process_file(
            image_bytes, filename, chat_id
        )
        
        # Esperar resultado
        for _ in range(100):  # 10 segundos max
            status = await self.processor.get_job_status(job_id)
            if status['status'] == 'completed':
                return status.get('result', {'success': True})
            elif status['status'] == 'failed':
                return {'success': False, 'error': status.get('error')}
            await asyncio.sleep(0.1)
        
        return {'success': False, 'error': 'Timeout'}
    
    async def process_video(self, video_bytes: bytes, filename: str,
                          chat_id: int = 0) -> Dict[str, Any]:
        """Procesar video"""
        job_id = await self.processor.process_file(
            video_bytes, filename, chat_id
        )
        return {'success': True, 'job_id': job_id}
    
    async def process_pdf(self, pdf_bytes: bytes, filename: str,
                        chat_id: int = 0) -> Dict[str, Any]:
        """Procesar PDF"""
        job_id = await self.processor.process_file(
            pdf_bytes, filename, chat_id
        )
        return {'success': True, 'job_id': job_id}
    
    async def process_audio(self, audio_bytes: bytes, filename: str,
                          chat_id: int = 0) -> Dict[str, Any]:
        """Procesar audio"""
        job_id = await self.processor.process_file(
            audio_bytes, filename, chat_id
        )
        return {'success': True, 'job_id': job_id}
    
    async def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas"""
        return await self.processor.get_stats()


# ============== FACTORY ==============

_processor_instance = None

async def get_file_processor() -> FileProcessorAPI:
    """Obtener instancia del procesador"""
    global _processor_instance
    
    if _processor_instance is None:
        microservice = FileProcessorMicroservice()
        await microservice.initialize()
        _processor_instance = FileProcessorAPI(microservice)
    
    return _processor_instance


# ============== TEST ==============

async def test_processor():
    """Test básico"""
    processor = await get_file_processor()
    
    # Test image
    test_image = b'\x89PNG\r\n\x1a\n' + b'0' * 1000
    result = await processor.process_image(test_image, "test.png")
    print(f"Test result: {result}")
    
    # Stats
    stats = await processor.get_stats()
    print(f"Stats: {json.dumps(stats, indent=2)}")


if __name__ == "__main__":
    asyncio.run(test_processor())