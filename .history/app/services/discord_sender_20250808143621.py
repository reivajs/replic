"""
Enterprise Discord Sender Service
=================================
Servicio enterprise con patrones de resilencia y escalabilidad

Archivo: app/services/discord_sender.py
"""

import asyncio
import aiohttp
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from pathlib import Path

from app.utils.logger import setup_logger
from app.config.settings import get_settings

logger = setup_logger(__name__)
settings = get_settings()

@dataclass
class WebhookStats:
    """Estadísticas por webhook"""
    total_sent: int = 0
    total_failed: int = 0
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    consecutive_failures: int = 0
    avg_response_time: float = 0.0
    rate_limit_resets: int = 0

@dataclass
class CircuitBreakerState:
    """Estado del Circuit Breaker"""
    state: str = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    next_attempt_time: Optional[datetime] = None

class DiscordWebhookCircuitBreaker:
    """Circuit Breaker pattern para webhooks de Discord"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.states: Dict[str, CircuitBreakerState] = {}
    
    def get_state(self, webhook_url: str) -> CircuitBreakerState:
        """Obtener estado del circuit breaker para un webhook"""
        if webhook_url not in self.states:
            self.states[webhook_url] = CircuitBreakerState()
        return self.states[webhook_url]
    
    def can_execute(self, webhook_url: str) -> bool:
        """Verificar si se puede ejecutar la petición"""
        state = self.get_state(webhook_url)
        
        if state.state == "CLOSED":
            return True
        elif state.state == "OPEN":
            # Verificar si es hora de intentar recovery
            if (state.next_attempt_time and 
                datetime.now() >= state.next_attempt_time):
                state.state = "HALF_OPEN"
                return True
            return False
        elif state.state == "HALF_OPEN":
            return True
        
        return False
    
    def record_success(self, webhook_url: str):
        """Registrar éxito"""
        state = self.get_state(webhook_url)
        state.failure_count = 0
        state.state = "CLOSED"
        state.last_failure_time = None
        state.next_attempt_time = None
    
    def record_failure(self, webhook_url: str):
        """Registrar fallo"""
        state = self.get_state(webhook_url)
        state.failure_count += 1
        state.last_failure_time = datetime.now()
        
        if state.failure_count >= self.failure_threshold:
            state.state = "OPEN"
            state.next_attempt_time = (
                datetime.now() + timedelta(seconds=self.recovery_timeout)
            )

class DiscordRateLimiter:
    """Rate limiter para Discord API"""
    
    def __init__(self):
        self.webhook_limits: Dict[str, Dict[str, Any]] = {}
    
    async def wait_if_needed(self, webhook_url: str):
        """Esperar si hay rate limit activo"""
        if webhook_url in self.webhook_limits:
            limit_info = self.webhook_limits[webhook_url]
            reset_time = limit_info.get('reset_time')
            
            if reset_time and datetime.now() < reset_time:
                wait_time = (reset_time - datetime.now()).total_seconds()
                if wait_time > 0:
                    logger.warning(f"⏳ Rate limit activo, esperando {wait_time:.1f}s")
                    await asyncio.sleep(wait_time)
    
    def update_limits(self, webhook_url: str, headers: Dict[str, str]):
        """Actualizar límites basado en headers de respuesta"""
        if 'x-ratelimit-remaining' in headers:
            remaining = int(headers.get('x-ratelimit-remaining', 0))
            reset_after = float(headers.get('x-ratelimit-reset-after', 0))
            
            if remaining == 0 and reset_after > 0:
                reset_time = datetime.now() + timedelta(seconds=reset_after)
                self.webhook_limits[webhook_url] = {
                    'reset_time': reset_time,
                    'remaining': remaining
                }

class DiscordSenderEnhanced:
    """
    🚀 DISCORD SENDER ENTERPRISE
    ============================
    
    Características Enterprise:
    ✅ Circuit Breaker pattern
    ✅ Rate limiting inteligente  
    ✅ Retry logic con exponential backoff
    ✅ Estadísticas detalladas por webhook
    ✅ Health monitoring
    ✅ Configuración flexible
    ✅ Logging estructurado
    ✅ Failover automático
    """
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.circuit_breaker = DiscordWebhookCircuitBreaker()
        self.rate_limiter = DiscordRateLimiter()
        
        # Estadísticas enterprise
        self.webhook_stats: Dict[str, WebhookStats] = {}
        self.global_stats = {
            'total_messages': 0,
            'total_successes': 0,
            'total_failures': 0,
            'total_retries': 0,
            'total_rate_limits': 0,
            'avg_response_time': 0.0,
            'start_time': datetime.now()
        }
        
        # Configuración enterprise
        self.config = {
            'max_retries': 3,
            'base_delay': 1.0,
            'max_delay': 30.0,
            'timeout': 30.0,
            'max_file_size_mb': 8,
            'chunk_size': 1024 * 1024  # 1MB chunks
        }
        
        logger.info("🚀 Discord Sender Enterprise inicializado")
    
    async def initialize(self):
        """Inicializar servicio enterprise"""
        try:
            # Configurar sesión HTTP optimizada
            connector = aiohttp.TCPConnector(
                limit=100,  # Pool de conexiones
                limit_per_host=10,
                keepalive_timeout=30,
                enable_cleanup_closed=True
            )
            
            timeout = aiohttp.ClientTimeout(total=self.config['timeout'])
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    'User-Agent': 'ReplicBot Enterprise/3.0',
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                }
            )
            
            logger.info("✅ Discord Sender Enterprise inicializado correctamente")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando Discord Sender: {e}")
            raise
    
    async def send_message(self, webhook_url: str, content: str, 
                          embeds: Optional[List[Dict]] = None) -> bool:
        """
        Enviar mensaje con resilencia enterprise
        """
        if not webhook_url or not content.strip():
            return False
        
        # Verificar circuit breaker
        if not self.circuit_breaker.can_execute(webhook_url):
            logger.warning("⚡ Circuit breaker OPEN, saltando envío")
            return False
        
        # Aplicar rate limiting
        await self.rate_limiter.wait_if_needed(webhook_url)
        
        # Preparar payload
        payload = {
            'content': content[:2000],  # Límite Discord
            'username': 'ReplicBot Enterprise'
        }
        
        if embeds:
            payload['embeds'] = embeds
        
        return await self._send_with_retry(webhook_url, payload)
    
    async def send_message_with_file(self, webhook_url: str, content: str, 
                                   file_bytes: bytes, filename: str) -> bool:
        """
        Enviar mensaje con archivo adjunto
        """
        if not webhook_url:
            return False
        
        # Verificar tamaño de archivo
        file_size_mb = len(file_bytes) / (1024 * 1024)
        if file_size_mb > self.config['max_file_size_mb']:
            logger.warning(f"📎 Archivo muy grande ({file_size_mb:.1f}MB), usando enlace")
            return await self.send_message(
                webhook_url, 
                f"{content}\n\n📎 **Archivo:** {filename} ({file_size_mb:.1f}MB)\n"
                "⚠️ Archivo muy grande para Discord, usar enlace de descarga"
            )
        
        # Verificar circuit breaker
        if not self.circuit_breaker.can_execute(webhook_url):
            logger.warning("⚡ Circuit breaker OPEN, saltando envío")
            return False
        
        # Aplicar rate limiting
        await self.rate_limiter.wait_if_needed(webhook_url)
        
        return await self._send_file_with_retry(webhook_url, content, file_bytes, filename)
    
    async def _send_with_retry(self, webhook_url: str, payload: Dict[str, Any]) -> bool:
        """Envío con retry logic exponential backoff"""
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
                        return True
                    
                    elif response.status == 429:  # Rate limit
                        self._record_rate_limit(webhook_url)
                        retry_after = float(response.headers.get('retry-after', 1))
                        logger.warning(f"⏳ Rate limit, esperando {retry_after}s")
                        await asyncio.sleep(retry_after)
                        continue
                    
                    else:  # Other error
                        error_text = await response.text()
                        logger.warning(f"⚠️ Discord error {response.status}: {error_text}")
                        self._record_failure(webhook_url)
                
            except Exception as e:
                last_exception = e
                logger.warning(f"⚠️ Intento {attempt + 1} falló: {e}")
                self._record_failure(webhook_url)
            
            # Exponential backoff si no es el último intento
            if attempt < self.config['max_retries']:
                delay = min(
                    self.config['base_delay'] * (2 ** attempt),
                    self.config['max_delay']
                )
                logger.info(f"🔄 Retry en {delay:.1f}s...")
                await asyncio.sleep(delay)
                self.global_stats['total_retries'] += 1
        
        # Todos los intentos fallaron
        self.circuit_breaker.record_failure(webhook_url)
        logger.error(f"❌ Falló envío después de {self.config['max_retries']} intentos")
        return False
    
    async def _send_file_with_retry(self, webhook_url: str, content: str, 
                                  file_bytes: bytes, filename: str) -> bool:
        """Envío de archivo con retry logic - CORREGIDO PARA DISCORD"""
        
        for attempt in range(self.config['max_retries'] + 1):
            try:
                # ✅ SOLUCIÓN: Usar aiohttp.FormData correctamente para Discord
                data = aiohttp.FormData()
                
                # Agregar el archivo
                data.add_field(
                    'file',
                    file_bytes,
                    filename=filename,
                    content_type=self._get_content_type(filename)
                )
                
                # ✅ SOLUCIÓN: Agregar contenido como form field separado (NO JSON)
                if content and content.strip():
                    data.add_field('content', content[:2000])
                
                # ✅ SOLUCIÓN: Agregar username como form field
                data.add_field('username', 'ReplicBot Enterprise')
                
                start_time = time.time()
                
                # ✅ SOLUCIÓN: Enviar con headers correctos (sin Content-Type manual)
                async with self.session.post(webhook_url, data=data) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        self._record_success(webhook_url, response_time)
                        self.circuit_breaker.record_success(webhook_url)
                        logger.debug(f"✅ Archivo enviado exitosamente: {filename}")
                        return True
                    
                    elif response.status == 429:
                        self._record_rate_limit(webhook_url)
                        retry_after = float(response.headers.get('retry-after', 1))
                        logger.warning(f"⏳ Rate limit, esperando {retry_after}s")
                        await asyncio.sleep(retry_after)
                        continue
                    
                    else:
                        error_text = await response.text()
                        logger.warning(f"⚠️ Error enviando archivo {response.status}: {error_text}")
                        self._record_failure(webhook_url)
                
            except Exception as e:
                logger.warning(f"⚠️ Error enviando archivo intento {attempt + 1}: {e}")
                self._record_failure(webhook_url)
            
            # Exponential backoff
            if attempt < self.config['max_retries']:
                delay = min(
                    self.config['base_delay'] * (2 ** attempt),
                    self.config['max_delay']
                )
                await asyncio.sleep(delay)
                self.global_stats['total_retries'] += 1
        
        self.circuit_breaker.record_failure(webhook_url)
        return False
    
    def _get_content_type(self, filename: str) -> str:
        """Obtener content type basado en extensión de archivo"""
        import mimetypes
        content_type, _ = mimetypes.guess_type(filename)
        
        if content_type:
            return content_type
        
        # Fallbacks comunes
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        
        fallbacks = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp',
            'mp4': 'video/mp4',
            'avi': 'video/avi',
            'mov': 'video/quicktime',
            'mp3': 'audio/mpeg',
            'wav': 'audio/wav',
            'ogg': 'audio/ogg',
            'pdf': 'application/pdf',
            'txt': 'text/plain',
            'json': 'application/json'
        }
        
        return fallbacks.get(ext, 'application/octet-stream')
    
    async def send_message_with_file(self, webhook_url: str, content: str, 
                                   file_bytes: bytes, filename: str) -> bool:
        """
        Enviar mensaje con archivo adjunto - VERSIÓN CORREGIDA
        """
        if not webhook_url:
            return False
        
        # Verificar tamaño de archivo
        file_size_mb = len(file_bytes) / (1024 * 1024)
        if file_size_mb > self.config['max_file_size_mb']:
            logger.warning(f"📎 Archivo muy grande ({file_size_mb:.1f}MB), enviando como enlace")
            
            # ✅ SOLUCIÓN: Enviar mensaje indicando archivo grande
            large_file_message = f"{content}\n\n📎 **Archivo:** {filename} ({file_size_mb:.1f}MB)\n⚠️ Archivo muy grande para Discord (máx. {self.config['max_file_size_mb']}MB)"
            return await self.send_message(webhook_url, large_file_message)
        
        # Verificar circuit breaker
        if not self.circuit_breaker.can_execute(webhook_url):
            logger.warning("⚡ Circuit breaker OPEN, saltando envío")
            return False
        
        # Aplicar rate limiting
        await self.rate_limiter.wait_if_needed(webhook_url)
        
        # ✅ SOLUCIÓN: Usar método corregido
        return await self._send_file_with_retry(webhook_url, content, file_bytes, filename)
    
    def _record_success(self, webhook_url: str, response_time: float):
        """Registrar éxito en estadísticas"""
        # Estadísticas por webhook
        if webhook_url not in self.webhook_stats:
            self.webhook_stats[webhook_url] = WebhookStats()
        
        stats = self.webhook_stats[webhook_url]
        stats.total_sent += 1
        stats.last_success = datetime.now()
        stats.consecutive_failures = 0
        
        # Actualizar promedio de tiempo de respuesta
        if stats.avg_response_time == 0:
            stats.avg_response_time = response_time
        else:
            stats.avg_response_time = (stats.avg_response_time + response_time) / 2
        
        # Estadísticas globales
        self.global_stats['total_messages'] += 1
        self.global_stats['total_successes'] += 1
        
        # Actualizar promedio global
        total_responses = self.global_stats['total_successes']
        if self.global_stats['avg_response_time'] == 0:
            self.global_stats['avg_response_time'] = response_time
        else:
            current_avg = self.global_stats['avg_response_time']
            self.global_stats['avg_response_time'] = (
                (current_avg * (total_responses - 1) + response_time) / total_responses
            )
    
    def _record_failure(self, webhook_url: str):
        """Registrar fallo en estadísticas"""
        if webhook_url not in self.webhook_stats:
            self.webhook_stats[webhook_url] = WebhookStats()
        
        stats = self.webhook_stats[webhook_url]
        stats.total_failed += 1
        stats.last_failure = datetime.now()
        stats.consecutive_failures += 1
        
        self.global_stats['total_messages'] += 1
        self.global_stats['total_failures'] += 1
    
    def _record_rate_limit(self, webhook_url: str):
        """Registrar rate limit"""
        if webhook_url not in self.webhook_stats:
            self.webhook_stats[webhook_url] = WebhookStats()
        
        self.webhook_stats[webhook_url].rate_limit_resets += 1
        self.global_stats['total_rate_limits'] += 1
    
    async def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas enterprise"""
        uptime = (datetime.now() - self.global_stats['start_time']).total_seconds()
        
        return {
            **self.global_stats,
            'uptime_seconds': uptime,
            'uptime_hours': uptime / 3600,
            'success_rate': (
                (self.global_stats['total_successes'] / 
                 max(self.global_stats['total_messages'], 1)) * 100
            ),
            'webhooks_configured': len(settings.discord.webhooks),
            'active_webhooks': len(self.webhook_stats),
            'circuit_breaker_open_count': sum(
                1 for state in self.circuit_breaker.states.values() 
                if state.state == 'OPEN'
            )
        }
    
    async def get_webhook_health(self) -> Dict[str, Any]:
        """Health check detallado por webhook"""
        health_report = {}
        
        for webhook_url, stats in self.webhook_stats.items():
            # Determinar estado de salud
            if stats.consecutive_failures >= 5:
                health_status = "critical"
            elif stats.consecutive_failures >= 3:
                health_status = "warning"
            elif stats.total_sent > 0:
                health_status = "healthy"
            else:
                health_status = "unknown"
            
            health_report[webhook_url] = {
                'status': health_status,
                'success_rate': (
                    (stats.total_sent / max(stats.total_sent + stats.total_failed, 1)) * 100
                ),
                'total_sent': stats.total_sent,
                'total_failed': stats.total_failed,
                'consecutive_failures': stats.consecutive_failures,
                'avg_response_time': stats.avg_response_time,
                'last_success': stats.last_success.isoformat() if stats.last_success else None,
                'last_failure': stats.last_failure.isoformat() if stats.last_failure else None,
                'circuit_breaker_state': self.circuit_breaker.get_state(webhook_url).state
            }
        
        return health_report
    
    async def close(self):
        """Cerrar recursos"""
        try:
            if self.session:
                await self.session.close()
                logger.info("✅ Discord Sender cerrado correctamente")
        except Exception as e:
            logger.error(f"❌ Error cerrando Discord Sender: {e}")
    
    def __del__(self):
        """Destructor"""
        if self.session and not self.session.closed:
            logger.warning("⚠️ Discord Sender no cerrado correctamente")