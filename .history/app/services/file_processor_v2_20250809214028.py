"""
FILE PROCESSOR MICROSERVICE v2.0 - ZERO COST ARCHITECTURE
=========================================================
Archivo: app/services/file_processor_v2.py

Refactor completo con arquitectura de microservicios local
Optimizado para laptop personal con zero infrastructure cost
"""

import asyncio
import hashlib
import json
import sqlite3
import subprocess
import tempfile
from collections import deque
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union
from concurrent.futures import ThreadPoolExecutor
import pickle
import lz4.frame

try:
    import aiofiles
    AIOFILES_AVAILABLE = True
except ImportError:
    AIOFILES_AVAILABLE = False

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

from app.utils.logger import setup_logger
from app.config.settings import get_settings

logger = setup_logger(__name__)
settings = get_settings()


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
    priority: int = 0  # 0 = normal, 1 = high, -1 = low
    retry_count: int = 0
    max_retries: int = 3

@dataclass
class CacheEntry:
    """Entry para cache distribuido local"""
    key: str
    value: Any
    size_bytes: int
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    ttl_seconds: int = 3600  # 1 hora default


# ============== CACHE DISTRIBUIDO LOCAL ==============

class LocalDistributedCache:
    """
    Cache distribuido usando SQLite + LZ4 compression
    Zero cost alternative to Redis
    """
    
    def __init__(self, db_path: Path, max_size_gb: float = 2.0):
        self.db_path = db_path
        self.max_size_bytes = max_size_gb * 1024 * 1024 * 1024
        self.conn = None
        self._init_db()
        
        # LRU in-memory cache para hot data
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.max_memory_items = 100
        
    def _init_db(self):
        """Inicializar base de datos SQLite"""
        self.conn = sqlite3.connect(
            str(self.db_path),
            check_same_thread=False,
            isolation_level=None  # Auto-commit
        )
        
        # Optimizaciones para velocidad
        self.conn.execute("PRAGMA journal_mode = WAL")
        self.conn.execute("PRAGMA synchronous = NORMAL")
        self.conn.execute("PRAGMA cache_size = -64000")  # 64MB cache
        self.conn.execute("PRAGMA temp_store = MEMORY")
        
        # Crear tabla de cache
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value BLOB,
                size_bytes INTEGER,
                created_at REAL,
                last_accessed REAL,
                access_count INTEGER DEFAULT 0,
                ttl_seconds INTEGER
            )
        """)
        
        # Índices para búsquedas rápidas
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_last_accessed 
            ON cache(last_accessed)
        """)
        
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_size 
            ON cache(size_bytes)
        """)
    
    async def get(self, key: str) -> Optional[Any]:
        """Obtener valor del cache"""
        # Check memory cache first
        if key in self.memory_cache:
            entry = self.memory_cache[key]
            entry.last_accessed = datetime.now()
            entry.access_count += 1
            return entry.value
        
        # Check disk cache
        cursor = self.conn.execute(
            "SELECT value, ttl_seconds, created_at FROM cache WHERE key = ?",
            (key,)
        )
        row = cursor.fetchone()
        
        if row:
            value_compressed, ttl, created_at = row
            
            # Check TTL
            if ttl > 0:
                age = datetime.now().timestamp() - created_at
                if age > ttl:
                    await self.delete(key)
                    return None
            
            # Decompress value
            try:
                value_bytes = lz4.frame.decompress(value_compressed)
                value = pickle.loads(value_bytes)
                
                # Update access time
                self.conn.execute("""
                    UPDATE cache 
                    SET last_accessed = ?, access_count = access_count + 1
                    WHERE key = ?
                """, (datetime.now().timestamp(), key))
                
                # Add to memory cache if hot
                if len(self.memory_cache) < self.max_memory_items:
                    self.memory_cache[key] = CacheEntry(
                        key=key,
                        value=value,
                        size_bytes=len(value_bytes),
                        created_at=datetime.fromtimestamp(created_at),
                        last_accessed=datetime.now(),
                        access_count=1
                    )
                
                return value
                
            except Exception as e:
                logger.error(f"Error deserializing cache value: {e}")
                await self.delete(key)
                return None
        
        return None
    
    async def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> bool:
        """Guardar valor en cache"""
        try:
            # Serialize and compress
            value_bytes = pickle.dumps(value)
            value_compressed = lz4.frame.compress(value_bytes)
            size_bytes = len(value_compressed)
            
            # Check space and cleanup if needed
            await self._cleanup_if_needed(size_bytes)
            
            # Save to disk
            now = datetime.now().timestamp()
            self.conn.execute("""
                INSERT OR REPLACE INTO cache 
                (key, value, size_bytes, created_at, last_accessed, ttl_seconds)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (key, value_compressed, size_bytes, now, now, ttl_seconds))
            
            # Add to memory cache if small enough
            if size_bytes < 1024 * 1024 and len(self.memory_cache) < self.max_memory_items:
                self.memory_cache[key] = CacheEntry(
                    key=key,
                    value=value,
                    size_bytes=size_bytes,
                    created_at=datetime.now(),
                    last_accessed=datetime.now(),
                    ttl_seconds=ttl_seconds
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting cache value: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Eliminar del cache"""
        self.memory_cache.pop(key, None)
        self.conn.execute("DELETE FROM cache WHERE key = ?", (key,))
        return True
    
    async def _cleanup_if_needed(self, required_bytes: int):
        """Limpiar cache si es necesario"""
        cursor = self.conn.execute("SELECT SUM(size_bytes) FROM cache")
        total_size = cursor.fetchone()[0] or 0
        
        if total_size + required_bytes > self.max_size_bytes:
            # Delete oldest entries (LRU)
            target_free = (self.max_size_bytes * 0.2)  # Free 20%
            
            self.conn.execute("""
                DELETE FROM cache 
                WHERE key IN (
                    SELECT key FROM cache 
                    ORDER BY last_accessed ASC 
                    LIMIT (
                        SELECT COUNT(*) FROM cache WHERE
                        (SELECT SUM(size_bytes) FROM cache) > ?
                    )
                )
            """, (self.max_size_bytes - target_free,))
            
            # Clear memory cache of deleted items
            self.memory_cache.clear()
    
    async def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del cache"""
        cursor = self.conn.execute("""
            SELECT 
                COUNT(*) as total_entries,
                SUM(size_bytes) as total_size,
                AVG(access_count) as avg_access_count,
                MAX(last_accessed) as last_activity
            FROM cache
        """)
        
        stats = cursor.fetchone()
        
        return {
            'total_entries': stats[0] or 0,
            'total_size_mb': (stats[1] or 0) / (1024 * 1024),
            'avg_access_count': stats[2] or 0,
            'last_activity': datetime.fromtimestamp(stats[3]) if stats[3] else None,
            'memory_cache_entries': len(self.memory_cache),
            'max_size_gb': self.max_size_bytes / (1024 * 1024 * 1024)
        }


# ============== QUEUE MANAGER LOCAL ==============

class LocalQueueManager:
    """
    Queue manager usando SQLite como backend
    Zero cost alternative to RabbitMQ/Kafka
    """
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = None
        self._init_db()
        
        # In-memory queues para velocidad
        self.pending_queue: deque = deque()
        self.processing_queue: Dict[str, ProcessingJob] = {}
        self.failed_queue: deque = deque()
        
    def _init_db(self):
        """Inicializar base de datos de colas"""
        self.conn = sqlite3.connect(
            str(self.db_path),
            check_same_thread=False
        )
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS job_queue (
                job_id TEXT PRIMARY KEY,
                file_type TEXT,
                file_hash TEXT,
                original_size INTEGER,
                chat_id INTEGER,
                filename TEXT,
                status TEXT,
                created_at REAL,
                started_at REAL,
                completed_at REAL,
                result TEXT,
                error TEXT,
                priority INTEGER DEFAULT 0,
                retry_count INTEGER DEFAULT 0
            )
        """)
        
        # Índices para queries rápidas
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_status 
            ON job_queue(status)
        """)
        
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_priority_created 
            ON job_queue(priority DESC, created_at ASC)
        """)
    
    async def enqueue(self, job: ProcessingJob) -> str:
        """Encolar job de procesamiento"""
        # Save to DB
        self.conn.execute("""
            INSERT INTO job_queue 
            (job_id, file_type, file_hash, original_size, chat_id, 
             filename, status, created_at, priority)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job.job_id, job.file_type.value, job.file_hash,
            job.original_size, job.chat_id, job.filename,
            job.status.value, job.created_at.timestamp(), job.priority
        ))
        self.conn.commit()
        
        # Add to memory queue
        self.pending_queue.append(job)
        
        logger.debug(f"📥 Job {job.job_id} enqueued")
        return job.job_id
    
    async def dequeue(self) -> Optional[ProcessingJob]:
        """Obtener siguiente job para procesar"""
        # Try memory queue first
        if self.pending_queue:
            job = self.pending_queue.popleft()
            job.status = ProcessingStatus.PROCESSING
            job.started_at = datetime.now()
            
            # Update DB
            self.conn.execute("""
                UPDATE job_queue 
                SET status = ?, started_at = ?
                WHERE job_id = ?
            """, (job.status.value, job.started_at.timestamp(), job.job_id))
            self.conn.commit()
            
            self.processing_queue[job.job_id] = job
            return job
        
        # Load from DB if memory queue empty
        cursor = self.conn.execute("""
            SELECT * FROM job_queue 
            WHERE status = ?
            ORDER BY priority DESC, created_at ASC
            LIMIT 10
        """, (ProcessingStatus.PENDING.value,))
        
        rows = cursor.fetchall()
        for row in rows:
            job = self._row_to_job(row)
            self.pending_queue.append(job)
        
        # Try again with loaded jobs
        if self.pending_queue:
            return await self.dequeue()
        
        return None
    
    def _calculate_progress(self, job: ProcessingJob) -> int:
        """Calcular progreso del job"""
        if job.status == ProcessingStatus.PENDING:
            return 0
        elif job.status == ProcessingStatus.PROCESSING:
            return 50
        elif job.status == ProcessingStatus.COMPLETED:
            return 100
        else:
            return -1
    
    def _detect_file_type(self, filename: str, file_bytes: bytes) -> FileType:
        """Detectar tipo de archivo"""
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        
        # Check by extension
        if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp']:
            return FileType.IMAGE
        elif ext in ['mp4', 'avi', 'mov', 'mkv', 'webm']:
            return FileType.VIDEO
        elif ext in ['mp3', 'wav', 'ogg', 'flac', 'm4a']:
            return FileType.AUDIO
        elif ext == 'pdf':
            return FileType.PDF
        elif ext in ['doc', 'docx', 'txt', 'odt']:
            return FileType.DOCUMENT
        
        # Check by magic bytes
        if file_bytes[:4] == b'\xff\xd8\xff':
            return FileType.IMAGE  # JPEG
        elif file_bytes[:8] == b'\x89PNG\r\n\x1a\n':
            return FileType.IMAGE  # PNG
        elif file_bytes[:4] == b'%PDF':
            return FileType.PDF
        
        return FileType.UNKNOWN
    
    async def _processing_loop(self):
        """Loop principal de procesamiento"""
        logger.info("🔄 Processing loop started")
        
        while self.is_running:
            try:
                # Get next job
                job = await self.queue_manager.dequeue()
                
                if not job:
                    await asyncio.sleep(0.1)  # No jobs, wait a bit
                    continue
                
                # Load file data
                file_path = self.data_dir / "temp" / f"{job.job_id}.bin"
                if not file_path.exists():
                    await self.queue_manager.fail_job(job.job_id, "File not found")
                    continue
                
                file_bytes = file_path.read_bytes()
                
                # Select worker (round-robin)
                worker_idx = hash(job.job_id) % len(self.workers)
                worker = self.workers[worker_idx]
                
                # Process based on file type
                start_time = datetime.now()
                
                if job.file_type == FileType.IMAGE:
                    result = await worker.process_image(file_bytes, job)
                elif job.file_type == FileType.VIDEO:
                    result = await worker.process_video(file_bytes, job)
                elif job.file_type == FileType.PDF:
                    result = await worker.process_pdf(file_bytes, job)
                elif job.file_type == FileType.AUDIO:
                    result = await worker.process_audio(file_bytes, job)
                else:
                    result = {'success': False, 'error': f'Unsupported type: {job.file_type}'}
                
                processing_time = (datetime.now() - start_time).total_seconds()
                
                # Handle result
                if result.get('success'):
                    # Save processed file
                    if 'data' in result:
                        output_path = self.data_dir / "processed" / f"{job.job_id}_processed.bin"
                        output_path.parent.mkdir(exist_ok=True)
                        output_path.write_bytes(result['data'])
                        result['output_path'] = str(output_path)
                        del result['data']  # Don't save binary data in DB
                    
                    result['processing_time'] = processing_time
                    await self.queue_manager.complete_job(job.job_id, result)
                    
                    # Update stats
                    self.stats['total_processed'] += 1
                    self._update_avg_processing_time(processing_time)
                    
                    # Cleanup temp file
                    file_path.unlink()
                    
                    logger.info(f"✅ Processed {job.filename} in {processing_time:.2f}s")
                else:
                    await self.queue_manager.fail_job(job.job_id, result.get('error', 'Unknown error'))
                    self.stats['total_failed'] += 1
                    
            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
                await asyncio.sleep(1)
    
    def _update_avg_processing_time(self, new_time: float):
        """Actualizar tiempo promedio de procesamiento"""
        total = self.stats['total_processed']
        if total == 1:
            self.stats['avg_processing_time'] = new_time
        else:
            current_avg = self.stats['avg_processing_time']
            self.stats['avg_processing_time'] = ((current_avg * (total - 1)) + new_time) / total
    
    async def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del servicio"""
        cache_stats = await self.cache.get_stats()
        queue_stats = await self.queue_manager.get_stats()
        
        uptime = (datetime.now() - self.stats['start_time']).total_seconds()
        
        return {
            'service': {
                'uptime_hours': uptime / 3600,
                'total_processed': self.stats['total_processed'],
                'total_failed': self.stats['total_failed'],
                'avg_processing_time': self.stats['avg_processing_time'],
                'workers': self.num_workers,
                'success_rate': (self.stats['total_processed'] / 
                               max(self.stats['total_processed'] + self.stats['total_failed'], 1)) * 100
            },
            'cache': cache_stats,
            'queue': queue_stats
        }
    
    async def cleanup_old_files(self, days: int = 7):
        """Limpiar archivos viejos"""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        # Clean processed files
        processed_dir = self.data_dir / "processed"
        if processed_dir.exists():
            for file in processed_dir.iterdir():
                if file.stat().st_mtime < cutoff_time.timestamp():
                    file.unlink()
                    logger.debug(f"🗑️ Deleted old file: {file.name}")
        
        # Clean temp files
        temp_dir = self.data_dir / "temp"
        if temp_dir.exists():
            for file in temp_dir.iterdir():
                if file.stat().st_mtime < cutoff_time.timestamp():
                    file.unlink()
                    logger.debug(f"🗑️ Deleted temp file: {file.name}")
    
    async def shutdown(self):
        """Apagar servicio gracefully"""
        logger.info("🛑 Shutting down File Processor Microservice...")
        
        self.is_running = False
        
        # Wait for current jobs to complete
        await asyncio.sleep(2)
        
        # Close worker thread pools
        for worker in self.workers:
            worker.thread_pool.shutdown(wait=False)
        
        logger.info("✅ File Processor Microservice stopped")


# ============== API INTERFACE ==============

class FileProcessorAPI:
    """
    API REST para el microservicio
    Compatible con tu Enhanced Replicator actual
    """
    
    def __init__(self, processor: FileProcessorMicroservice):
        self.processor = processor
    
    async def process_image(self, image_bytes: bytes, filename: str, 
                           chat_id: int = 0) -> Dict[str, Any]:
        """API compatible con tu código actual"""
        job_id = await self.processor.process_file(
            image_bytes, filename, chat_id, priority=0
        )
        
        # Wait for completion (con timeout)
        max_wait = 30  # seconds
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < max_wait:
            status = await self.processor.get_job_status(job_id)
            
            if status['status'] == 'completed':
                return status['result']
            elif status['status'] == 'failed':
                return {'success': False, 'error': status.get('error')}
            
            await asyncio.sleep(0.1)
        
        return {'success': False, 'error': 'Processing timeout'}
    
    async def process_video(self, video_bytes: bytes, filename: str,
                          chat_id: int = 0) -> Dict[str, Any]:
        """API compatible para video"""
        job_id = await self.processor.process_file(
            video_bytes, filename, chat_id, priority=0
        )
        
        # For videos, return job_id immediately (async processing)
        return {
            'success': True,
            'job_id': job_id,
            'message': 'Video processing started'
        }
    
    async def process_pdf(self, pdf_bytes: bytes, filename: str,
                        chat_id: int = 0) -> Dict[str, Any]:
        """API compatible para PDF"""
        job_id = await self.processor.process_file(
            pdf_bytes, filename, chat_id, priority=1  # Higher priority
        )
        
        # Wait for PDF processing
        max_wait = 10
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < max_wait:
            status = await self.processor.get_job_status(job_id)
            
            if status['status'] == 'completed':
                return status['result']
            elif status['status'] == 'failed':
                return {'success': False, 'error': status.get('error')}
            
            await asyncio.sleep(0.1)
        
        return {'success': False, 'error': 'Processing timeout'}
    
    async def process_audio(self, audio_bytes: bytes, filename: str,
                          chat_id: int = 0) -> Dict[str, Any]:
        """API compatible para audio"""
        job_id = await self.processor.process_file(
            audio_bytes, filename, chat_id, priority=0
        )
        
        # Return job_id for async tracking
        return {
            'success': True,
            'job_id': job_id,
            'message': 'Audio processing started'
        }
    
    async def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas"""
        return await self.processor.get_stats()


# ============== FACTORY FUNCTION ==============

_processor_instance = None

async def get_file_processor() -> FileProcessorAPI:
    """
    Factory function para obtener instancia del procesador
    Singleton pattern para zero cost
    """
    global _processor_instance
    
    if _processor_instance is None:
        microservice = FileProcessorMicroservice()
        await microservice.initialize()
        _processor_instance = FileProcessorAPI(microservice)
        
        # Start cleanup task
        async def cleanup_task():
            while True:
                await asyncio.sleep(3600)  # Every hour
                await microservice.cleanup_old_files()
        
        asyncio.create_task(cleanup_task())
    
    return _processor_instance


# ============== TESTING ==============

async def test_processor():
    """Test del procesador"""
    processor = await get_file_processor()
    
    # Test image
    test_image = b'\x89PNG\r\n\x1a\n' + b'0' * 1000  # Fake PNG
    result = await processor.process_image(test_image, "test.png", 123)
    print(f"Image test: {result}")
    
    # Get stats
    stats = await processor.get_stats()
    print(f"Stats: {json.dumps(stats, indent=2)}")


if __name__ == "__main__":
    # Run test
    asyncio.run(test_processor()) self.pending_queue.popleft()
            job.status = ProcessingStatus.PROCESSING
            job.started_at = datetime.now()
            
            # Update DB
            self.conn.execute("""
                UPDATE job_queue 
                SET status = ?, started_at = ?
                WHERE job_id = ?
            """, (job.status.value, job.started_at.timestamp(), job.job_id))
            self.conn.commit()
            
            self.processing_queue[job.job_id] = job
            return job
        
        # Load from DB if memory queue empty
        cursor = self.conn.execute("""
            SELECT * FROM job_queue 
            WHERE status = ?
            ORDER BY priority DESC, created_at ASC
            LIMIT 10
        """, (ProcessingStatus.PENDING.value,))
        
        rows = cursor.fetchall()
        for row in rows:
            job = self._row_to_job(row)
            self.pending_queue.append(job)
        
        # Try again with loaded jobs
        if self.pending_queue:
            return await self.dequeue()
        
        return None
    
    async def complete_job(self, job_id: str, result: Dict[str, Any]):
        """Marcar job como completado"""
        if job_id in self.processing_queue:
            job = self.processing_queue.pop(job_id)
            job.status = ProcessingStatus.COMPLETED
            job.completed_at = datetime.now()
            job.result = result
            
            # Update DB
            self.conn.execute("""
                UPDATE job_queue 
                SET status = ?, completed_at = ?, result = ?
                WHERE job_id = ?
            """, (
                job.status.value, 
                job.completed_at.timestamp(),
                json.dumps(result),
                job_id
            ))
            self.conn.commit()
    
    async def fail_job(self, job_id: str, error: str):
        """Marcar job como fallido"""
        if job_id in self.processing_queue:
            job = self.processing_queue.pop(job_id)
            job.status = ProcessingStatus.FAILED
            job.error = error
            job.retry_count += 1
            
            # Retry logic
            if job.retry_count < job.max_retries:
                job.status = ProcessingStatus.PENDING
                await self.enqueue(job)
                logger.info(f"🔄 Retrying job {job_id} (attempt {job.retry_count})")
            else:
                self.failed_queue.append(job)
                
                # Update DB
                self.conn.execute("""
                    UPDATE job_queue 
                    SET status = ?, error = ?, retry_count = ?
                    WHERE job_id = ?
                """, (job.status.value, error, job.retry_count, job_id))
                self.conn.commit()
    
    def _row_to_job(self, row: tuple) -> ProcessingJob:
        """Convertir row de DB a ProcessingJob"""
        return ProcessingJob(
            job_id=row[0],
            file_type=FileType(row[1]),
            file_hash=row[2],
            original_size=row[3],
            chat_id=row[4],
            filename=row[5],
            status=ProcessingStatus(row[6]),
            created_at=datetime.fromtimestamp(row[7]),
            priority=row[11] if len(row) > 11 else 0,
            retry_count=row[12] if len(row) > 12 else 0
        )
    
    async def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de colas"""
        cursor = self.conn.execute("""
            SELECT 
                status, 
                COUNT(*) as count,
                AVG(CASE 
                    WHEN completed_at IS NOT NULL AND started_at IS NOT NULL 
                    THEN completed_at - started_at 
                    ELSE NULL 
                END) as avg_processing_time
            FROM job_queue
            GROUP BY status
        """)
        
        stats = {}
        for row in cursor:
            stats[row[0]] = {
                'count': row[1],
                'avg_processing_time': row[2]
            }
        
        return {
            'queue_stats': stats,
            'memory_pending': len(self.pending_queue),
            'memory_processing': len(self.processing_queue),
            'memory_failed': len(self.failed_queue)
        }


# ============== FILE PROCESSOR WORKERS ==============

class FileProcessorWorker:
    """Worker individual para procesamiento de archivos"""
    
    def __init__(self, worker_id: int, cache: LocalDistributedCache):
        self.worker_id = worker_id
        self.cache = cache
        self.is_running = False
        
        # Thread pool para operaciones CPU-intensive
        self.thread_pool = ThreadPoolExecutor(max_workers=2)
        
    async def process_image(self, image_bytes: bytes, job: ProcessingJob) -> Dict[str, Any]:
        """Procesar imagen con compresión inteligente"""
        if not PIL_AVAILABLE:
            return {'success': False, 'error': 'PIL not available'}
        
        try:
            # Check cache first
            cache_key = f"img_{job.file_hash}"
            cached_result = await self.cache.get(cache_key)
            if cached_result:
                logger.debug(f"✅ Cache hit for image {job.filename}")
                return cached_result
            
            from io import BytesIO
            
            # Process in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.thread_pool,
                self._process_image_sync,
                image_bytes,
                job.filename
            )
            
            # Cache result
            await self.cache.set(cache_key, result, ttl_seconds=7200)  # 2 hours
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return {'success': False, 'error': str(e)}
    
    def _process_image_sync(self, image_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Sync image processing (runs in thread)"""
        from io import BytesIO
        
        img = Image.open(BytesIO(image_bytes))
        original_size = len(image_bytes)
        
        # Smart compression based on size
        if original_size > 2 * 1024 * 1024:  # >2MB
            max_size = (1280, 720)
            quality = 75
        elif original_size > 1024 * 1024:  # >1MB
            max_size = (1920, 1080)
            quality = 80
        else:
            max_size = img.size
            quality = 85
        
        # Resize if needed
        if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Save compressed
        output = BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        compressed_bytes = output.getvalue()
        
        return {
            'success': True,
            'filename': filename,
            'original_size': original_size,
            'compressed_size': len(compressed_bytes),
            'compression_ratio': len(compressed_bytes) / original_size,
            'dimensions': img.size,
            'data': compressed_bytes
        }
    
    async def process_video(self, video_bytes: bytes, job: ProcessingJob) -> Dict[str, Any]:
        """Procesar video con ffmpeg"""
        try:
            # Check cache
            cache_key = f"vid_{job.file_hash}"
            cached_result = await self.cache.get(cache_key)
            if cached_result:
                return cached_result
            
            # Create temp files
            temp_dir = Path(tempfile.gettempdir())
            temp_input = temp_dir / f"input_{job.job_id}.mp4"
            temp_output = temp_dir / f"output_{job.job_id}.mp4"
            
            # Write input
            temp_input.write_bytes(video_bytes)
            
            # FFmpeg command with smart compression
            size_mb = len(video_bytes) / (1024 * 1024)
            if size_mb > 50:
                crf = 28  # High compression
                scale = "scale=1280:720"
            elif size_mb > 20:
                crf = 25  # Medium compression
                scale = "scale=1920:1080"
            else:
                crf = 23  # Low compression
                scale = ""
            
            cmd = [
                'ffmpeg', '-i', str(temp_input),
                '-c:v', 'libx264',
                '-crf', str(crf),
                '-preset', 'faster',  # Faster encoding on laptop
                '-c:a', 'aac',
                '-b:a', '128k'
            ]
            
            if scale:
                cmd.extend(['-vf', scale])
            
            cmd.extend([str(temp_output), '-y'])
            
            # Run ffmpeg
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode == 0:
                compressed_bytes = temp_output.read_bytes()
                
                result = {
                    'success': True,
                    'filename': job.filename,
                    'original_size': len(video_bytes),
                    'compressed_size': len(compressed_bytes),
                    'compression_ratio': len(compressed_bytes) / len(video_bytes),
                    'data': compressed_bytes
                }
                
                # Cache for 4 hours
                await self.cache.set(cache_key, result, ttl_seconds=14400)
                
                # Cleanup
                temp_input.unlink()
                temp_output.unlink()
                
                return result
            else:
                return {'success': False, 'error': stderr.decode()}
                
        except Exception as e:
            logger.error(f"Error processing video: {e}")
            return {'success': False, 'error': str(e)}
    
    async def process_pdf(self, pdf_bytes: bytes, job: ProcessingJob) -> Dict[str, Any]:
        """Procesar PDF"""
        if not PYMUPDF_AVAILABLE:
            return {'success': False, 'error': 'PyMuPDF not available'}
        
        try:
            # Check cache
            cache_key = f"pdf_{job.file_hash}"
            cached_result = await self.cache.get(cache_key)
            if cached_result:
                return cached_result
            
            pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
            page_count = len(pdf_document)
            
            # Extract text from first page for preview
            first_page_text = ""
            if page_count > 0:
                first_page_text = pdf_document[0].get_text()[:500]
            
            pdf_document.close()
            
            result = {
                'success': True,
                'filename': job.filename,
                'page_count': page_count,
                'file_size': len(pdf_bytes),
                'preview_text': first_page_text,
                'data': pdf_bytes
            }
            
            # Cache for 24 hours
            await self.cache.set(cache_key, result, ttl_seconds=86400)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            return {'success': False, 'error': str(e)}
    
    async def process_audio(self, audio_bytes: bytes, job: ProcessingJob) -> Dict[str, Any]:
        """Procesar audio"""
        try:
            # Check cache
            cache_key = f"aud_{job.file_hash}"
            cached_result = await self.cache.get(cache_key)
            if cached_result:
                return cached_result
            
            temp_dir = Path(tempfile.gettempdir())
            temp_input = temp_dir / f"input_{job.job_id}.mp3"
            temp_output = temp_dir / f"output_{job.job_id}.mp3"
            
            temp_input.write_bytes(audio_bytes)
            
            # Convert to optimized MP3
            cmd = [
                'ffmpeg', '-i', str(temp_input),
                '-c:a', 'libmp3lame',
                '-b:a', '128k',
                '-ar', '44100',
                str(temp_output),
                '-y'
            ]
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await proc.communicate()
            
            if proc.returncode == 0:
                processed_bytes = temp_output.read_bytes()
                
                result = {
                    'success': True,
                    'filename': job.filename,
                    'original_size': len(audio_bytes),
                    'processed_size': len(processed_bytes),
                    'format': 'mp3',
                    'bitrate': '128k',
                    'data': processed_bytes
                }
                
                # Cache for 12 hours
                await self.cache.set(cache_key, result, ttl_seconds=43200)
                
                # Cleanup
                temp_input.unlink()
                temp_output.unlink()
                
                return result
            else:
                return {'success': False, 'error': 'FFmpeg processing failed'}
                
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            return {'success': False, 'error': str(e)}


# ============== MAIN PROCESSOR ORCHESTRATOR ==============

class FileProcessorMicroservice:
    """
    Orchestrator principal del microservicio
    Maneja workers, cache y queue
    """
    
    def __init__(self):
        # Paths
        self.data_dir = Path("processor_data")
        self.data_dir.mkdir(exist_ok=True)
        
        # Core components
        self.cache = LocalDistributedCache(
            self.data_dir / "cache.db",
            max_size_gb=2.0  # Ajustable según tu laptop
        )
        
        self.queue_manager = LocalQueueManager(
            self.data_dir / "queue.db"
        )
        
        # Worker pool
        self.workers: List[FileProcessorWorker] = []
        self.num_workers = 4  # Ajustable según CPU de tu laptop
        
        # Stats
        self.stats = {
            'total_processed': 0,
            'total_failed': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'avg_processing_time': 0,
            'start_time': datetime.now()
        }
        
        self.is_running = False
        
    async def initialize(self):
        """Inicializar microservicio"""
        try:
            # Create workers
            for i in range(self.num_workers):
                worker = FileProcessorWorker(i, self.cache)
                self.workers.append(worker)
            
            # Start processing loop
            self.is_running = True
            asyncio.create_task(self._processing_loop())
            
            logger.info(f"✅ File Processor Microservice initialized")
            logger.info(f"   Workers: {self.num_workers}")
            logger.info(f"   Cache: {self.data_dir / 'cache.db'}")
            logger.info(f"   Queue: {self.data_dir / 'queue.db'}")
            
        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            raise
    
    async def process_file(self, file_bytes: bytes, filename: str, 
                          chat_id: int, priority: int = 0) -> str:
        """
        API principal para procesar archivos
        Retorna job_id para tracking asíncrono
        """
        # Detect file type
        file_type = self._detect_file_type(filename, file_bytes)
        
        # Generate hash for deduplication
        file_hash = hashlib.sha256(file_bytes).hexdigest()[:16]
        
        # Create job
        job = ProcessingJob(
            job_id=f"{file_hash}_{datetime.now().timestamp()}",
            file_type=file_type,
            file_hash=file_hash,
            original_size=len(file_bytes),
            chat_id=chat_id,
            filename=filename,
            priority=priority
        )
        
        # Store file data temporarily
        file_path = self.data_dir / "temp" / f"{job.job_id}.bin"
        file_path.parent.mkdir(exist_ok=True)
        file_path.write_bytes(file_bytes)
        
        # Enqueue job
        await self.queue_manager.enqueue(job)
        
        return job.job_id
    
    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Obtener estado de un job"""
        conn = self.queue_manager.conn
        cursor = conn.execute(
            "SELECT * FROM job_queue WHERE job_id = ?",
            (job_id,)
        )
        row = cursor.fetchone()
        
        if not row:
            return {'status': 'not_found'}
        
        job = self.queue_manager._row_to_job(row)
        
        response = {
            'job_id': job.job_id,
            'status': job.status.value,
            'filename': job.filename,
            'file_type': job.file_type.value,
            'created_at': job.created_at.isoformat(),
            'progress': self._calculate_progress(job)
        }
        
        if job.status == ProcessingStatus.COMPLETED and job.result:
            response['result'] = json.loads(job.result) if isinstance(job.result, str) else job.result
        elif job.status == ProcessingStatus.FAILED and job.error:
            response['error'] = job.error
            
        return response
    
    def _calculate_progress(self, job: ProcessingJob) -> int:
        """Calcular progreso del job"""
        if job.status == ProcessingStatus.PENDING:
            return 0
        elif job.status == ProcessingStatus.PROCESSING:
            return 50
        elif job.status == ProcessingStatus.COMPLETED:
            return 100
        else:
            return -1
    
    def _detect_file_type(self, filename: str, file_bytes: bytes) -> FileType:
        """Detectar tipo de archivo"""
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        
        # Check by extension
        if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp']:
            return FileType.IMAGE
        elif ext in ['mp4', 'avi', 'mov', 'mkv', 'webm']:
            return FileType.VIDEO
        elif ext in ['mp3', 'wav', 'ogg', 'flac', 'm4a']:
            return FileType.AUDIO
        elif ext == 'pdf':
            return FileType.PDF
        elif ext in ['doc', 'docx', 'txt', 'odt']:
            return FileType.DOCUMENT
        
        # Check by magic bytes
        if file_bytes[:4] == b'\xff\xd8\xff':
            return FileType.IMAGE  # JPEG
        elif file_bytes[:8] == b'\x89PNG\r\n\x1a\n':
            return FileType.IMAGE  # PNG
        elif file_bytes[:4] == b'%PDF':
            return FileType.PDF
        
        return FileType.UNKNOWN
    
    async def _processing_loop(self):
        """Loop principal de procesamiento"""
        logger.info("🔄 Processing loop started")
        
        while self.is_running:
            try:
                # Get next job
                job = await self.queue_manager.dequeue()
                
                if not job:
                    await asyncio.sleep(0.1)  # No jobs, wait a bit
                    continue
                
                # Load file data
                file_path = self.data_dir / "temp" / f"{job.job_id}.bin"
                if not file_path.exists():
                    await self.queue_manager.fail_job(job.job_id, "File not found")
                    continue
                
                file_bytes = file_path.read_bytes()
                
                # Select worker (round-robin)
                worker_idx = hash(job.job_id) % len(self.workers)
                worker = self.workers[worker_idx]
                
                # Process based on file type
                start_time = datetime.now()
                
                if job.file_type == FileType.IMAGE:
                    result = await worker.process_image(file_bytes, job)
                elif job.file_type == FileType.VIDEO:
                    result = await worker.process_video(file_bytes, job)
                elif job.file_type == FileType.PDF:
                    result = await worker.process_pdf(file_bytes, job)
                elif job.file_type == FileType.AUDIO:
                    result = await worker.process_audio(file_bytes, job)
                else:
                    result = {'success': False, 'error': f'Unsupported type: {job.file_type}'}
                
                processing_time = (datetime.now() - start_time).total_seconds()
                
                # Handle result
                if result.get('success'):
                    # Save processed file
                    if 'data' in result:
                        output_path = self.data_dir / "processed" / f"{job.job_id}_processed.bin"
                        output_path.parent.mkdir(exist_ok=True)
                        output_path.write_bytes(result['data'])
                        result['output_path'] = str(output_path)
                        del result['data']  # Don't save binary data in DB
                    
                    result['processing_time'] = processing_time
                    await self.queue_manager.complete_job(job.job_id, result)
                    
                    # Update stats
                    self.stats['total_processed'] += 1
                    self._update_avg_processing_time(processing_time)
                    
                    # Cleanup temp file
                    file_path.unlink()
                    
                    logger.info(f"✅ Processed {job.filename} in {processing_time:.2f}s")
                else:
                    await self.queue_manager.fail_job(job.job_id, result.get('error', 'Unknown error'))
                    self.stats['total_failed'] += 1
                    
            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
                await asyncio.sleep(1)
    
    def _update_avg_processing_time(self, new_time: float):
        """Actualizar tiempo promedio de procesamiento"""
        total = self.stats['total_processed']
        if total == 1:
            self.stats['avg_processing_time'] = new_time
        else:
            current_avg = self.stats['avg_processing_time']
            self.stats['avg_processing_time'] = ((current_avg * (total - 1)) + new_time) / total
    
    async def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del servicio"""
        cache_stats = await self.cache.get_stats()
        queue_stats = await self.queue_manager.get_stats()
        
        uptime = (datetime.now() - self.stats['start_time']).total_seconds()
        
        return {
            'service': {
                'uptime_hours': uptime / 3600,
                'total_processed': self.stats['total_processed'],
                'total_failed': self.stats['total_failed'],
                'avg_processing_time': self.stats['avg_processing_time'],
                'workers': self.num_workers,
                'success_rate': (self.stats['total_processed'] / 
                               max(self.stats['total_processed'] + self.stats['total_failed'], 1)) * 100
            },
            'cache': cache_stats,
            'queue': queue_stats
        }
    
    async def cleanup_old_files(self, days: int = 7):
        """Limpiar archivos viejos"""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        # Clean processed files
        processed_dir = self.data_dir / "processed"
        if processed_dir.exists():
            for file in processed_dir.iterdir():
                if file.stat().st_mtime < cutoff_time.timestamp():
                    file.unlink()
                    logger.debug(f"🗑️ Deleted old file: {file.name}")
        
        # Clean temp files
        temp_dir = self.data_dir / "temp"
        if temp_dir.exists():
            for file in temp_dir.iterdir():
                if file.stat().st_mtime < cutoff_time.timestamp():
                    file.unlink()
                    logger.debug(f"🗑️ Deleted temp file: {file.name}")
    
    async def shutdown(self):
        """Apagar servicio gracefully"""
        logger.info("🛑 Shutting down File Processor Microservice...")
        
        self.is_running = False
        
        # Wait for current jobs to complete
        await asyncio.sleep(2)
        
        # Close worker thread pools
        for worker in self.workers:
            worker.thread_pool.shutdown(wait=False)
        
        logger.info("✅ File Processor Microservice stopped")


# ============== API INTERFACE ==============

class FileProcessorAPI:
    """
    API REST para el microservicio
    Compatible con tu Enhanced Replicator actual
    """
    
    def __init__(self, processor: FileProcessorMicroservice):
        self.processor = processor
    
    async def process_image(self, image_bytes: bytes, filename: str, 
                           chat_id: int = 0) -> Dict[str, Any]:
        """API compatible con tu código actual"""
        job_id = await self.processor.process_file(
            image_bytes, filename, chat_id, priority=0
        )
        
        # Wait for completion (con timeout)
        max_wait = 30  # seconds
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < max_wait:
            status = await self.processor.get_job_status(job_id)
            
            if status['status'] == 'completed':
                return status['result']
            elif status['status'] == 'failed':
                return {'success': False, 'error': status.get('error')}
            
            await asyncio.sleep(0.1)
        
        return {'success': False, 'error': 'Processing timeout'}
    
    async def process_video(self, video_bytes: bytes, filename: str,
                          chat_id: int = 0) -> Dict[str, Any]:
        """API compatible para video"""
        job_id = await self.processor.process_file(
            video_bytes, filename, chat_id, priority=0
        )
        
        # For videos, return job_id immediately (async processing)
        return {
            'success': True,
            'job_id': job_id,
            'message': 'Video processing started'
        }
    
    async def process_pdf(self, pdf_bytes: bytes, filename: str,
                        chat_id: int = 0) -> Dict[str, Any]:
        """API compatible para PDF"""
        job_id = await self.processor.process_file(
            pdf_bytes, filename, chat_id, priority=1  # Higher priority
        )
        
        # Wait for PDF processing
        max_wait = 10
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < max_wait:
            status = await self.processor.get_job_status(job_id)
            
            if status['status'] == 'completed':
                return status['result']
            elif status['status'] == 'failed':
                return {'success': False, 'error': status.get('error')}
            
            await asyncio.sleep(0.1)
        
        return {'success': False, 'error': 'Processing timeout'}
    
    async def process_audio(self, audio_bytes: bytes, filename: str,
                          chat_id: int = 0) -> Dict[str, Any]:
        """API compatible para audio"""
        job_id = await self.processor.process_file(
            audio_bytes, filename, chat_id, priority=0
        )
        
        # Return job_id for async tracking
        return {
            'success': True,
            'job_id': job_id,
            'message': 'Audio processing started'
        }
    
    async def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas"""
        return await self.processor.get_stats()


# ============== FACTORY FUNCTION ==============

_processor_instance = None

async def get_file_processor() -> FileProcessorAPI:
    """
    Factory function para obtener instancia del procesador
    Singleton pattern para zero cost
    """
    global _processor_instance
    
    if _processor_instance is None:
        microservice = FileProcessorMicroservice()
        await microservice.initialize()
        _processor_instance = FileProcessorAPI(microservice)
        
        # Start cleanup task
        async def cleanup_task():
            while True:
                await asyncio.sleep(3600)  # Every hour
                await microservice.cleanup_old_files()
        
        asyncio.create_task(cleanup_task())
    
    return _processor_instance


# ============== TESTING ==============

async def test_processor():
    """Test del procesador"""
    processor = await get_file_processor()
    
    # Test image
    test_image = b'\x89PNG\r\n\x1a\n' + b'0' * 1000  # Fake PNG
    result = await processor.process_image(test_image, "test.png", 123)
    print(f"Image test: {result}")
    
    # Get stats
    stats = await processor.get_stats()
    print(f"Stats: {json.dumps(stats, indent=2)}")


if __name__ == "__main__":
    # Run test
    asyncio.run(test_processor())