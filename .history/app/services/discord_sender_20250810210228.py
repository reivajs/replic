"""
DISCORD SENDER ENTERPRISE - VERSIÓN CORREGIDA PARA ENVÍO DIRECTO
================================================================
Archivo: app/services/discord_sender.py

🚀 SOLUCIÓN COMPLETA PARA ENVÍO DIRECTO
✅ Archivos se envían directamente, no como links
✅ Arquitectura modular y sin parches  
✅ Compatible con enhanced_replicator_service.py
✅ Manejo robusto de errores y limits
"""

import asyncio
import aiohttp
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path
from io import BytesIO

# Setup logger
try:
    from app.utils.logger import setup_logger
    logger = setup_logger(__name__)
except:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

@dataclass
class SendResult:
    """Resultado de envío con detalles completos"""
    success: bool
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    processing_time: float = 0.0
    response_data: Optional[Dict] = None

@dataclass
class RateLimitData:
    """Datos de rate limiting por webhook"""
    remaining: int = 5
    reset_time: datetime = field(default_factory=datetime.now)
    retry_after: float = 0.0
    last_request: datetime = field(default_factory=datetime.now)

class CircuitBreaker:
    """Circuit breaker enterprise para webhooks"""
    
    def __init__(self, failure_threshold: int = 5, reset_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failure_counts: Dict[str, int] = {}
        self.last_failure_times: Dict[str, datetime] = {}
        self.states: Dict[str, str] = {}  # 'closed', 'open', 'half-open'
    
    def can_execute(self, webhook_url: str) -> bool:
        """Verificar si se puede ejecutar la operación"""
        state = self.states.get(webhook_url, 'closed')
        
        if state == 'closed':
            return True
        elif state == 'open':
            # Verificar si debe cambiar a half-open
            last_failure = self.last_failure_times.get(webhook_url)
            if last_failure and (datetime.now() - last_failure).seconds > self.reset_timeout:
                self.states[webhook_url] = 'half-open'
                return True
            return False
        elif state == 'half-open':
            return True
        
        return False
    
    def record_success(self, webhook_url: str):
        """Registrar éxito"""
        self.failure_counts[webhook_url] = 0
        self.states[webhook_url] = 'closed'
    
    def record_failure(self, webhook_url: str):
        """Registrar fallo"""
        self.failure_counts[webhook_url] = self.failure_counts.get(webhook_url, 0) + 1
        self.last_failure_times[webhook_url] = datetime.now()
        
        if self.failure_counts[webhook_url] >= self.failure_threshold:
            self.states[webhook_url] = 'open'

class RateLimiter:
    """Rate limiter per-webhook"""
    
    def __init__(self):
        self.rate_limits: Dict[str, RateLimitData] = {}
    
    async def wait_if_needed(self, webhook_url: str):
        """Esperar si es necesario por rate limits"""
        rate_data = self.rate_limits.get(webhook_url, RateLimitData())
        
        if rate_data.remaining <= 0:
            sleep_time = (rate_data.reset_time - datetime.now()).total_seconds()
            if sleep_time > 0:
                logger.warning(f"⏰ Rate limit alcanzado, esperando {sleep_time:.1f}s")
                await asyncio.sleep(sleep_time)
        
        # Esperar después de retry_after si existe
        if rate_data.retry_after > 0:
            time_since_last = (datetime.now() - rate_data.last_request).total_seconds()
            if time_since_last < rate_data.retry_after:
                wait_time = rate_data.retry_after - time_since_last
                logger.warning(f"⏰ Retry-after activo, esperando {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
    
    def update_limits(self, webhook_url: str, headers: Dict[str, str]):
        """Actualizar límites basado en headers de respuesta"""
        rate_data = self.rate_limits.get(webhook_url, RateLimitData())
        
        # Actualizar desde headers
        if 'x-ratelimit-remaining' in headers:
            rate_data.remaining = int(headers['x-ratelimit-remaining'])
        
        if 'x-ratelimit-reset' in headers:
            reset_timestamp = float(headers['x-ratelimit-reset'])
            rate_data.reset_time = datetime.fromtimestamp(reset_timestamp)
        
        if 'retry-after' in headers:
            rate_data.retry_after = float(headers['retry-after'])
        
        rate_data.last_request = datetime.now()
        self.rate_limits[webhook_url] = rate_data

class DiscordSenderEnhanced:
    """
    🚀 DISCORD SENDER ENTERPRISE PARA ENVÍO DIRECTO
    ===============================================
    
    ✅ CARACTERÍSTICA PRINCIPAL: ENVÍO DIRECTO
    - Imágenes se envían directamente como archivo adjunto
    - Videos se envían directamente como archivo adjunto  
    - Audios se envían directamente como archivo adjunto
    - NO usa links de descarga, todo es directo
    
    ✅ ARQUITECTURA ENTERPRISE:
    - Circuit breaker per-webhook
    - Rate limiting inteligente
    - Retry logic exponential backoff
    - Health monitoring
    - Compression automática para archivos grandes
    """
    
    def __init__(self):
        # Configuración enterprise
        self.config = {
            'max_retries': 3,
            'retry_delay_base': 1.0,
            'retry_delay_max': 30.0,
            'max_file_size_mb': 25,  # Discord limit
            'timeout_seconds': 60,
            'circuit_breaker_threshold': 5,
            'rate_limit_buffer': 2
        }
        
        # Componentes enterprise
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=self.config['circuit_breaker_threshold']
        )
        self.rate_limiter = RateLimiter()
        
        # Session HTTP reutilizable
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Estadísticas detalladas
        self.stats = {
            'messages_sent': 0,
            'files_sent_direct': 0,  # Contador de archivos enviados directamente
            'images_sent_direct': 0,
            'videos_sent_direct': 0,
            'audios_sent_direct': 0,
            'total_failures': 0,
            'rate_limit_hits': 0,
            'circuit_breaker_trips': 0,
            'total_bytes_sent': 0,
            'compression_saves_mb': 0.0,
            'avg_response_time': 0.0,
            'total_response_time': 0.0,
            'start_time': datetime.now()
        }
        
        logger.info("🚀 Discord Sender Enterprise initialized - MODO ENVÍO DIRECTO")
    
    async def initialize(self):
        """Inicializar servicios enterprise"""
        try:
            # Crear session HTTP optimizada
            connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=10,
                keepalive_timeout=30,
                enable_cleanup_closed=True
            )
            
            timeout = aiohttp.ClientTimeout(
                total=self.config['timeout_seconds'],
                connect=10,
                sock_read=30
            )
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    'User-Agent': 'DiscordBot (Enterprise-Replicator, 3.0)'
                }
            )
            
            logger.info("✅ Discord Sender Enterprise inicializado")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando Discord Sender: {e}")
            raise
    
    # ============== MÉTODOS PRINCIPALES - ENVÍO DIRECTO ==============
    
    async def send_message(self, webhook_url: str, content: str, 
                          username: Optional[str] = None) -> bool:
        """
        Enviar mensaje de texto simple
        Compatible con enhanced_replicator_service.py
        """
        if not self.session:
            await self.initialize()
        
        payload = {'content': content}
        if username:
            payload['username'] = username
        
        result = await self._send_with_retry(webhook_url, payload)
        
        if result.success:
            self.stats['messages_sent'] += 1
        
        return result.success
    
    async def send_message_with_file(self, webhook_url: str, content: str, 
                                   file_bytes: bytes, filename: str) -> bool:
        """
        🎯 MÉTODO PRINCIPAL PARA ENVÍO DIRECTO DE ARCHIVOS
        =================================================
        
        Este método envía archivos DIRECTAMENTE a Discord como adjuntos,
        NO como links de descarga. Compatible con enhanced_replicator_service.py
        
        Args:
            webhook_url: URL del webhook de Discord
            content: Texto que acompaña al archivo
            file_bytes: Bytes del archivo
            filename: Nombre del archivo
            
        Returns:
            bool: True si se envió exitosamente
        """
        if not self.session:
            await self.initialize()
        
        # Verificar tamaño y comprimir si es necesario
        file_size_mb = len(file_bytes) / (1024 * 1024)
        
        if file_size_mb > self.config['max_file_size_mb']:
            logger.warning(f"📎 Archivo muy grande ({file_size_mb:.1f}MB)")
            
            # Intentar comprimir si es imagen o video
            compressed_bytes = await self._try_compress_file(file_bytes, filename)
            if compressed_bytes and len(compressed_bytes) < len(file_bytes):
                original_size = len(file_bytes) / (1024 * 1024)
                new_size = len(compressed_bytes) / (1024 * 1024)
                savings = original_size - new_size
                
                self.stats['compression_saves_mb'] += savings
                file_bytes = compressed_bytes
                
                logger.info(f"⚡ Archivo comprimido: {original_size:.1f}MB → {new_size:.1f}MB")
            else:
                # Si no se puede comprimir, enviar mensaje de error
                error_message = f"{content}\n\n❌ **Archivo muy grande:** {filename} ({file_size_mb:.1f}MB)\nDiscord limite: {self.config['max_file_size_mb']}MB"
                return await self.send_message(webhook_url, error_message)
        
        # Verificar circuit breaker
        if not self.circuit_breaker.can_execute(webhook_url):
            logger.warning("⚡ Circuit breaker OPEN - saltando envío")
            return False
        
        # Aplicar rate limiting
        await self.rate_limiter.wait_if_needed(webhook_url)
        
        # ENVÍO DIRECTO del archivo
        result = await self._send_file_direct(webhook_url, content, file_bytes, filename)
        
        if result.success:
            self.stats['files_sent_direct'] += 1
            self.stats['total_bytes_sent'] += len(file_bytes)
            
            # Contadores específicos por tipo
            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                self.stats['images_sent_direct'] += 1
            elif filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                self.stats['videos_sent_direct'] += 1
            elif filename.lower().endswith(('.mp3', '.wav', '.ogg', '.m4a')):
                self.stats['audios_sent_direct'] += 1
            
            logger.info(f"✅ Archivo enviado DIRECTAMENTE: {filename} ({file_size_mb:.1f}MB)")
        
        return result.success
    
    async def _send_file_direct(self, webhook_url: str, content: str, 
                              file_bytes: bytes, filename: str) -> SendResult:
        """
        🎯 ENVÍO DIRECTO DE ARCHIVO - IMPLEMENTACIÓN CORE
        ================================================
        
        Esta función hace el envío real y directo del archivo a Discord
        """
        last_exception = None
        
        for attempt in range(self.config['max_retries'] + 1):
            try:
                start_time = time.time()
                
                # Preparar FormData para envío directo
                data = aiohttp.FormData()
                
                # Añadir contenido de texto
                if content:
                    data.add_field('content', content)
                
                # Determinar content type
                content_type = self._get_content_type(filename)
                
                # 🎯 PUNTO CLAVE: Añadir archivo como FormData
                data.add_field(
                    'file',
                    BytesIO(file_bytes),
                    filename=filename,
                    content_type=content_type
                )
                
                # Enviar con FormData (NO JSON)
                async with self.session.post(webhook_url, data=data) as response:
                    response_time = time.time() - start_time
                    
                    # Actualizar rate limits
                    self.rate_limiter.update_limits(webhook_url, dict(response.headers))
                    
                    if response.status in [200, 204]:  # Success
                        self._record_success(webhook_url, response_time)
                        self.circuit_breaker.record_success(webhook_url)
                        
                        return SendResult(
                            success=True,
                            status_code=response.status,
                            processing_time=response_time
                        )
                    
                    elif response.status == 429:  # Rate limit
                        self._record_rate_limit(webhook_url)
                        retry_after = float(response.headers.get('retry-after', 1.0))
                        
                        logger.warning(f"⏰ Rate limit hit, esperando {retry_after}s")
                        await asyncio.sleep(retry_after)
                        continue
                    
                    else:  # Other error
                        error_text = await response.text()
                        logger.warning(f"⚠️ Error enviando archivo {response.status}: {error_text}")
                        
                        # Si es error de cliente (4xx), no retry
                        if 400 <= response.status < 500:
                            return SendResult(
                                success=False,
                                status_code=response.status,
                                error_message=error_text
                            )
                        
                        # Error de servidor, continuar con retry
                        last_exception = Exception(f"HTTP {response.status}: {error_text}")
                        
            except Exception as e:
                last_exception = e
                logger.warning(f"⚠️ Intento {attempt + 1} falló: {e}")
            
            # Exponential backoff para retry
            if attempt < self.config['max_retries']:
                delay = min(
                    self.config['retry_delay_base'] * (2 ** attempt),
                    self.config['retry_delay_max']
                )
                await asyncio.sleep(delay)
        
        # Todos los intentos fallaron
        self.circuit_breaker.record_failure(webhook_url)
        self.stats['total_failures'] += 1
        
        return SendResult(
            success=False,
            error_message=str(last_exception) if last_exception else "Unknown error",
            retry_count=self.config['max_retries']
        )
    
    async def _send_with_retry(self, webhook_url: str, payload: Dict[str, Any]) -> SendResult:
        """Envío de JSON con retry logic para mensajes de texto"""
        last_exception = None
        
        for attempt in range(self.config['max_retries'] + 1):
            try:
                start_time = time.time()
                
                async with self.session.post(webhook_url, json=payload) as response:
                    response_time = time.time() - start_time
                    
                    # Actualizar rate limits
                    self.rate_limiter.update_limits(webhook_url, dict(response.headers))
                    
                    if response.status == 204:  # Success
                        self._record_success(webhook_url, response_time)
                        self.circuit_breaker.record_success(webhook_url)
                        
                        return SendResult(
                            success=True,
                            status_code=response.status,
                            processing_time=response_time
                        )
                    
                    elif response.status == 429:  # Rate limit
                        self._record_rate_limit(webhook_url)
                        retry_after = float(response.headers.get('retry-after', 1.0))
                        await asyncio.sleep(retry_after)
                        continue
                    
                    else:  # Other error
                        error_text = await response.text()
                        logger.warning(f"⚠️ Error enviando mensaje {response.status}: {error_text}")
                        
                        if 400 <= response.status < 500:
                            return SendResult(
                                success=False,
                                status_code=response.status,
                                error_message=error_text
                            )
                        
                        last_exception = Exception(f"HTTP {response.status}: {error_text}")
                        
            except Exception as e:
                last_exception = e
            
            # Exponential backoff
            if attempt < self.config['max_retries']:
                delay = min(
                    self.config['retry_delay_base'] * (2 ** attempt),
                    self.config['retry_delay_max']
                )
                await asyncio.sleep(delay)
        
        # Falló completamente
        self.circuit_breaker.record_failure(webhook_url)
        self.stats['total_failures'] += 1
        
        return SendResult(
            success=False,
            error_message=str(last_exception) if last_exception else "Unknown error",
            retry_count=self.config['max_retries']
        )
    
    # ============== MÉTODOS DE UTILIDAD ==============
    
    def _get_content_type(self, filename: str) -> str:
        """Determinar content type por extensión"""
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        
        content_types = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg', 
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp',
            'mp4': 'video/mp4',
            'avi': 'video/avi',
            'mov': 'video/quicktime',
            'mkv': 'video/x-matroska',
            'mp3': 'audio/mpeg',
            'wav': 'audio/wav',
            'ogg': 'audio/ogg',
            'm4a': 'audio/mp4',
            'pdf': 'application/pdf'
        }
        
        return content_types.get(ext, 'application/octet-stream')
    
    async def _try_compress_file(self, file_bytes: bytes, filename: str) -> Optional[bytes]:
        """Intentar comprimir archivo si es posible"""
        try:
            ext = filename.lower().split('.')[-1] if '.' in filename else ''
            
            if ext in ['jpg', 'jpeg', 'png', 'webp']:
                return await self._compress_image(file_bytes)
            elif ext in ['mp4', 'avi', 'mov']:
                # Para videos, solo reducir calidad en casos extremos
                # En este caso básico, no comprimimos videos
                return None
            
            return None
            
        except Exception as e:
            logger.warning(f"⚠️ Error comprimiendo archivo: {e}")
            return None
    
    async def _compress_image(self, image_bytes: bytes) -> Optional[bytes]:
        """Comprimir imagen usando PIL"""
        try:
            from PIL import Image
            from io import BytesIO
            
            # Cargar imagen
            img = Image.open(BytesIO(image_bytes))
            
            # Reducir tamaño si es muy grande
            max_size = (1920, 1080)
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Comprimir
            output = BytesIO()
            
            # Convertir a RGB si tiene transparencia
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            img.save(output, format='JPEG', quality=75, optimize=True)
            
            compressed = output.getvalue()
            return compressed if len(compressed) < len(image_bytes) else None
            
        except ImportError:
            logger.warning("⚠️ PIL no disponible para compresión")
            return None
        except Exception as e:
            logger.warning(f"⚠️ Error comprimiendo imagen: {e}")
            return None
    
    def _record_success(self, webhook_url: str, response_time: float):
        """Registrar éxito y actualizar métricas"""
        # Actualizar tiempo de respuesta promedio
        total_requests = self.stats['messages_sent'] + self.stats['files_sent_direct'] + 1
        self.stats['total_response_time'] += response_time
        self.stats['avg_response_time'] = self.stats['total_response_time'] / total_requests
    
    def _record_rate_limit(self, webhook_url: str):
        """Registrar hit de rate limit"""
        self.stats['rate_limit_hits'] += 1
    
    # ============== MÉTODOS DE GESTIÓN ==============
    
    async def get_health(self) -> Dict[str, Any]:
        """Health check enterprise"""
        try:
            uptime_seconds = (datetime.now() - self.stats['start_time']).total_seconds()
            
            # Calcular tasas
            total_operations = self.stats['messages_sent'] + self.stats['files_sent_direct']
            success_rate = ((total_operations - self.stats['total_failures']) / max(total_operations, 1)) * 100
            
            return {
                "status": "healthy" if self.session and not self.session.closed else "unhealthy",
                "session_active": self.session is not None and not (self.session.closed if self.session else True),
                "uptime_seconds": uptime_seconds,
                "performance": {
                    "total_operations": total_operations,
                    "success_rate": success_rate,
                    "avg_response_time": self.stats['avg_response_time'],
                    "operations_per_minute": (total_operations / max(uptime_seconds / 60, 1))
                },
                "files_direct": {
                    "total_files_sent": self.stats['files_sent_direct'],
                    "images_sent": self.stats['images_sent_direct'],
                    "videos_sent": self.stats['videos_sent_direct'],
                    "audios_sent": self.stats['audios_sent_direct'],
                    "total_mb_sent": self.stats['total_bytes_sent'] / (1024 * 1024)
                },
                "circuit_breaker": {
                    "trips": self.stats['circuit_breaker_trips'],
                    "active_breaks": len([url for url, state in self.circuit_breaker.states.items() if state == 'open'])
                }
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas completas"""
        return {
            "discord_sender_stats": self.stats.copy(),
            "rate_limiter": {
                "active_limits": len(self.rate_limiter.rate_limits),
                "rate_limit_hits": self.stats['rate_limit_hits']
            },
            "circuit_breaker": {
                "webhooks_monitored": len(self.circuit_breaker.states),
                "failure_counts": self.circuit_breaker.failure_counts,
                "current_states": self.circuit_breaker.states
            }
        }
    
    async def close(self):
        """Cerrar conexiones"""
        try:
            if self.session and not self.session.closed:
                await self.session.close()
            
            logger.info("✅ Discord Sender cerrado correctamente")
            
        except Exception as e:
            logger.error(f"❌ Error cerrando Discord Sender: {e}")

# ============== FACTORY PARA COMPATIBILIDAD ==============

def create_discord_sender() -> DiscordSenderEnhanced:
    """Factory function para crear DiscordSenderEnhanced"""
    return DiscordSenderEnhanced()

# Alias para compatibilidad
DiscordSender = DiscordSenderEnhanced