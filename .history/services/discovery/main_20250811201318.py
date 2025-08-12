#!/usr/bin/env python3
"""
🔍 DISCOVERY SERVICE v2.0 - Enterprise Microservice FIXED
===========================================================
Auto-discovery de chats de Telegram con arquitectura enterprise
FIXES:
- ✅ JSON serialization de datetime objects
- ✅ Dataclass conversion de ScanStatus
- ✅ Modular datetime serialization utility
"""

import asyncio
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from contextlib import asynccontextmanager
from dataclasses import dataclass, asdict

# FastAPI & Core
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Telegram
from telethon import TelegramClient, events
from telethon.tl.types import Channel, Chat, User, Dialog
from telethon.errors import SessionPasswordNeededError, FloodWaitError

# Cache & Storage  
import sqlite3
from pathlib import Path
import aiofiles
import httpx

# ============= UTILITY FUNCTIONS =============

def datetime_serializer(obj: Any) -> Any:
    """
    🔧 FIX: Custom datetime serializer for JSON compatibility
    Convierte objetos datetime a ISO format string
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: datetime_serializer(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [datetime_serializer(item) for item in obj]
    elif hasattr(obj, '__dict__'):
        # Para dataclasses y objetos custom
        return datetime_serializer(obj.__dict__)
    return obj

def safe_asdict(dataclass_instance: Any) -> Dict[str, Any]:
    """
    🔧 FIX: Safe dataclass to dict conversion with datetime serialization
    """
    if hasattr(dataclass_instance, '__dataclass_fields__'):
        # Es un dataclass real
        result = asdict(dataclass_instance)
        return datetime_serializer(result)
    elif hasattr(dataclass_instance, 'dict'):
        # Es un Pydantic model
        result = dataclass_instance.dict()
        return datetime_serializer(result)
    elif hasattr(dataclass_instance, '__dict__'):
        # Objeto con __dict__
        result = dataclass_instance.__dict__
        return datetime_serializer(result)
    else:
        # Fallback: convertir a dict si es posible
        try:
            result = dict(dataclass_instance)
            return datetime_serializer(result)
        except:
            return {"error": "Cannot serialize object"}

def safe_json_dumps(obj: Any) -> str:
    """
    🔧 FIX: Safe JSON dumps with datetime support
    """
    return json.dumps(datetime_serializer(obj), default=str, ensure_ascii=False)

# ============= CONFIGURATION =============
import os
from dotenv import load_dotenv

load_dotenv()  # Añadir esta línea

@dataclass  
class DiscoveryConfig:
    """Configuración del Discovery Service"""
    # Telegram - Leer desde variables de entorno
    api_id: int = int(os.getenv('TELEGRAM_API_ID', 18425773))
    api_hash: str = os.getenv('TELEGRAM_API_HASH', '1a94c8576994cbb3e60383c94562c91b')
    phone: str = os.getenv('TELEGRAM_PHONE', '+56985667015')
    session_name: str = "discovery_session"
    
    # Service
    port: int = 8002
    scan_interval: int = 1800  # 30 minutos
    rate_limit_delay: float = 1.0  # 1 segundo entre requests
    max_concurrent_scans: int = 5
    
    # Database
    db_path: str = "data/discovery.db"
    cache_duration: int = 3600  # 1 hora
    
    # External Services
    orchestrator_url: str = "http://localhost:8000"
    replicator_url: str = "http://localhost:8001"

# ============= DATA MODELS =============

@dataclass
class ChatInfo:
    """Información completa de un chat"""
    id: int
    title: str
    type: str  # 'channel', 'group', 'supergroup', 'user'
    username: Optional[str] = None
    description: Optional[str] = None
    participants_count: Optional[int] = None
    is_broadcast: bool = False
    is_megagroup: bool = False
    is_private: bool = False
    date_created: Optional[datetime] = None
    last_message_date: Optional[datetime] = None
    has_geo: bool = False
    is_scam: bool = False
    is_verified: bool = False
    restriction_reason: Optional[str] = None
    
    # Discovery metadata
    discovered_at: Optional[datetime] = None
    scan_count: int = 0
    is_active: bool = True
    last_activity: Optional[datetime] = None
    
    def __post_init__(self):
        if self.discovered_at is None:
            self.discovered_at = datetime.now()

@dataclass
class ScanStatus:
    """
    🔧 FIX: Changed from BaseModel to dataclass for consistency
    Estado del escaneo como dataclass para usar con asdict()
    """
    is_scanning: bool = False
    progress_percent: float = 0.0
    current_chat: Optional[str] = None
    total_chats: int = 0
    processed_chats: int = 0
    new_chats_found: int = 0
    errors: int = 0
    start_time: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None

class ScanRequest(BaseModel):
    """Request para iniciar escaneo"""
    force_refresh: bool = False
    target_chat_ids: Optional[List[int]] = None

class ChatFilter(BaseModel):
    """Filtros para búsqueda de chats"""
    chat_type: Optional[str] = None  # 'channel', 'group', 'supergroup'
    min_participants: Optional[int] = None
    max_participants: Optional[int] = None
    has_username: Optional[bool] = None
    is_broadcast: Optional[bool] = None
    is_megagroup: Optional[bool] = None
    search_term: Optional[str] = None
    is_active: Optional[bool] = None
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None

# ============= DATABASE LAYER =============

class DiscoveryDatabase:
    """Database abstraction layer con datetime serialization fix"""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Inicializar base de datos"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS chats (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    type TEXT NOT NULL,
                    username TEXT,
                    description TEXT,
                    participants_count INTEGER,
                    is_broadcast BOOLEAN DEFAULT FALSE,
                    is_megagroup BOOLEAN DEFAULT FALSE,
                    is_private BOOLEAN DEFAULT FALSE,
                    date_created TIMESTAMP,
                    last_message_date TIMESTAMP,
                    has_geo BOOLEAN DEFAULT FALSE,
                    is_scam BOOLEAN DEFAULT FALSE,
                    is_verified BOOLEAN DEFAULT FALSE,
                    restriction_reason TEXT,
                    discovered_at TIMESTAMP NOT NULL,
                    scan_count INTEGER DEFAULT 1,
                    is_active BOOLEAN DEFAULT TRUE,
                    last_activity TIMESTAMP,
                    raw_data TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS scan_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_id TEXT UNIQUE NOT NULL,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    total_chats INTEGER DEFAULT 0,
                    new_chats INTEGER DEFAULT 0,
                    updated_chats INTEGER DEFAULT 0,
                    errors INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'running'
                )
            ''')
            
            # Índices para performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_chats_type ON chats(type)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_chats_username ON chats(username)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_chats_active ON chats(is_active)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_chats_discovered ON chats(discovered_at)')
    
    def _datetime_to_str(self, dt: Optional[datetime]) -> Optional[str]:
        """🔧 FIX: Convert datetime to ISO string for SQLite"""
        return dt.isoformat() if dt else None
    
    def _str_to_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """🔧 FIX: Convert ISO string to datetime from SQLite"""
        try:
            return datetime.fromisoformat(dt_str) if dt_str else None
        except (ValueError, TypeError):
            return None
    
    async def save_chat(self, chat_info: ChatInfo) -> bool:
        """🔧 FIX: Guardar información de chat con datetime serialization"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Verificar si existe
                existing = conn.execute(
                    'SELECT scan_count FROM chats WHERE id = ?', 
                    (chat_info.id,)
                ).fetchone()
                
                # 🔧 FIX: Convertir datetimes a strings para SQLite
                date_created_str = self._datetime_to_str(chat_info.date_created)
                last_message_date_str = self._datetime_to_str(chat_info.last_message_date)
                discovered_at_str = self._datetime_to_str(chat_info.discovered_at)
                last_activity_str = self._datetime_to_str(chat_info.last_activity)
                
                # 🔧 FIX: Serializar ChatInfo sin datetimes problemáticos
                chat_dict = safe_asdict(chat_info)
                raw_data_json = safe_json_dumps(chat_dict)
                
                if existing:
                    # Actualizar
                    chat_info.scan_count = existing[0] + 1
                    conn.execute('''
                        UPDATE chats SET 
                        title=?, type=?, username=?, description=?, participants_count=?,
                        is_broadcast=?, is_megagroup=?, is_private=?, date_created=?, 
                        last_message_date=?, has_geo=?, is_scam=?, is_verified=?, 
                        restriction_reason=?, scan_count=?, is_active=?, last_activity=?,
                        raw_data=?
                        WHERE id=?
                    ''', (
                        chat_info.title, chat_info.type, chat_info.username, 
                        chat_info.description, chat_info.participants_count,
                        chat_info.is_broadcast, chat_info.is_megagroup, chat_info.is_private,
                        date_created_str, last_message_date_str, chat_info.has_geo,
                        chat_info.is_scam, chat_info.is_verified, chat_info.restriction_reason,
                        chat_info.scan_count, chat_info.is_active, last_activity_str,
                        raw_data_json, chat_info.id
                    ))
                else:
                    # Insertar
                    conn.execute('''
                        INSERT INTO chats VALUES (
                            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                        )
                    ''', (
                        chat_info.id, chat_info.title, chat_info.type, chat_info.username,
                        chat_info.description, chat_info.participants_count, chat_info.is_broadcast,
                        chat_info.is_megagroup, chat_info.is_private, date_created_str,
                        last_message_date_str, chat_info.has_geo, chat_info.is_scam,
                        chat_info.is_verified, chat_info.restriction_reason, discovered_at_str,
                        chat_info.scan_count, chat_info.is_active, last_activity_str,
                        raw_data_json
                    ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logging.error(f"🔧 FIX: Error saving chat {chat_info.id}: {e}")
            return False
    
    async def get_chats(self, filters: ChatFilter = None, limit: int = 1000, offset: int = 0) -> List[ChatInfo]:
        """🔧 FIX: Obtener chats con datetime deserialization"""
        try:
            query = "SELECT * FROM chats WHERE 1=1"
            params = []
            
            if filters:
                if filters.chat_type:
                    query += " AND type = ?"
                    params.append(filters.chat_type)
                
                if filters.min_participants is not None:
                    query += " AND participants_count >= ?"
                    params.append(filters.min_participants)
                
                if filters.max_participants is not None:
                    query += " AND participants_count <= ?"
                    params.append(filters.max_participants)
                
                if filters.has_username is not None:
                    if filters.has_username:
                        query += " AND username IS NOT NULL"
                    else:
                        query += " AND username IS NULL"
                
                if filters.is_broadcast is not None:
                    query += " AND is_broadcast = ?"
                    params.append(filters.is_broadcast)
                
                if filters.is_megagroup is not None:
                    query += " AND is_megagroup = ?"
                    params.append(filters.is_megagroup)
                
                if filters.search_term:
                    query += " AND (title LIKE ? OR description LIKE ? OR username LIKE ?)"
                    search_pattern = f"%{filters.search_term}%"
                    params.extend([search_pattern, search_pattern, search_pattern])
                
                if filters.is_active is not None:
                    query += " AND is_active = ?"
                    params.append(filters.is_active)
            
            query += " ORDER BY discovered_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(query, params).fetchall()
                
                chats = []
                for row in rows:
                    chat_data = dict(row)
                    
                    # 🔧 FIX: Convertir timestamp strings a datetime objects
                    for field in ['date_created', 'last_message_date', 'discovered_at', 'last_activity']:
                        if chat_data[field]:
                            chat_data[field] = self._str_to_datetime(chat_data[field])
                    
                    # Remover raw_data del constructor
                    chat_constructor_data = {k: v for k, v in chat_data.items() if k != 'raw_data'}
                    chats.append(ChatInfo(**chat_constructor_data))
                
                return chats
                
        except Exception as e:
            logging.error(f"🔧 FIX: Error getting chats: {e}")
            return []
    
    async def get_chat_by_id(self, chat_id: int) -> Optional[ChatInfo]:
        """Obtener chat específico"""
        chats = await self.get_chats(ChatFilter(), limit=1)
        for chat in chats:
            if chat.id == chat_id:
                return chat
        return None

# ============= TELEGRAM SCANNER =============

class TelegramScanner:
    """Scanner inteligente de chats de Telegram con datetime fixes"""
    
    def __init__(self, config: DiscoveryConfig, database: DiscoveryDatabase):
        self.config = config
        self.database = database
        self.client: Optional[TelegramClient] = None
        self.is_scanning = False
        
        # 🔧 FIX: Inicializar ScanStatus como dataclass
        self.scan_status = ScanStatus(
            is_scanning=False, 
            progress_percent=0.0
        )
        
        self.scan_stats = {
            'total_scans': 0,
            'successful_scans': 0,
            'failed_scans': 0,
            'chats_discovered': 0,
            'last_scan': None
        }
    
    async def initialize(self):
        """Inicializar cliente de Telegram"""
        try:
            session_path = Path(f"sessions/{self.config.session_name}.session")
            session_path.parent.mkdir(parents=True, exist_ok=True)
            
            self.client = TelegramClient(
                str(session_path),
                self.config.api_id, 
                self.config.api_hash
            )
            
            await self.client.start(phone=self.config.phone)
            
            if not await self.client.is_user_authorized():
                raise Exception("Telegram authorization required")
            
            logging.info("✅ Telegram client initialized successfully")
            return True
            
        except Exception as e:
            logging.error(f"Failed to initialize Telegram client: {e}")
            return False
    
    async def scan_all_chats(self, force_refresh: bool = False) -> ScanStatus:
        """🔧 FIX: Escanear todos los chats con datetime handling"""
        if self.is_scanning:
            return self.scan_status
        
        self.is_scanning = True
        
        # 🔧 FIX: Recrear ScanStatus como dataclass con datetime actual
        self.scan_status = ScanStatus(
            is_scanning=True,
            progress_percent=0.0,
            start_time=datetime.now(),
            total_chats=0,
            processed_chats=0,
            new_chats_found=0,
            errors=0,
            current_chat=None,
            estimated_completion=None
        )
        
        try:
            if not self.client:
                await self.initialize()
            
            # Obtener todos los diálogos
            logging.info("🔍 Starting chat discovery scan...")
            dialogs = []
            
            async for dialog in self.client.iter_dialogs():
                dialogs.append(dialog)
            
            self.scan_status.total_chats = len(dialogs)
            logging.info(f"Found {len(dialogs)} total dialogs")
            
            new_chats = 0
            processed = 0
            errors = 0
            
            for i, dialog in enumerate(dialogs):
                try:
                    # Rate limiting
                    await asyncio.sleep(self.config.rate_limit_delay)
                    
                    # Actualizar progreso
                    self.scan_status.processed_chats = processed
                    self.scan_status.progress_percent = (processed / len(dialogs)) * 100 if dialogs else 0
                    self.scan_status.current_chat = dialog.title or "Unknown"
                    
                    # Extraer información del chat
                    chat_info = await self._extract_chat_info(dialog)
                    
                    if chat_info:
                        # Verificar si es nuevo
                        existing = await self.database.get_chat_by_id(chat_info.id)
                        is_new = existing is None
                        
                        # Guardar en database
                        if await self.database.save_chat(chat_info):
                            if is_new:
                                new_chats += 1
                            logging.debug(f"{'New' if is_new else 'Updated'} chat: {chat_info.title}")
                    
                    processed += 1
                    
                except Exception as e:
                    errors += 1
                    logging.error(f"Error processing dialog {i}: {e}")
                    continue
            
            # 🔧 FIX: Finalizar escaneo con datetime update
            self.scan_status.new_chats_found = new_chats
            self.scan_status.errors = errors
            self.scan_status.progress_percent = 100.0
            self.scan_status.is_scanning = False
            self.scan_status.estimated_completion = datetime.now()
            
            # Actualizar estadísticas
            self.scan_stats['total_scans'] += 1
            self.scan_stats['successful_scans'] += 1
            self.scan_stats['chats_discovered'] += new_chats
            self.scan_stats['last_scan'] = datetime.now()
            
            logging.info(f"✅ Scan completed: {processed} processed, {new_chats} new, {errors} errors")
            
        except Exception as e:
            self.scan_status.errors += 1
            self.scan_status.is_scanning = False
            self.scan_stats['failed_scans'] += 1
            logging.error(f"Scan failed: {e}")
        
        finally:
            self.is_scanning = False
        
        return self.scan_status
    
    async def _extract_chat_info(self, dialog: Dialog) -> Optional[ChatInfo]:
        """🔧 FIX: Extraer información con list serialization y NULL title handling"""
        try:
            entity = dialog.entity
            
            # Determinar tipo de chat
            chat_type = "unknown"
            if isinstance(entity, Channel):
                if entity.broadcast:
                    chat_type = "channel"
                elif entity.megagroup:
                    chat_type = "supergroup"
                else:
                    chat_type = "group"
            elif isinstance(entity, Chat):
                chat_type = "group"
            elif isinstance(entity, User):
                chat_type = "user"
            
            # 🔧 FIX: Manejo seguro de título - NUNCA puede ser NULL
            title = None
            if hasattr(entity, 'title') and entity.title:
                title = str(entity.title)
            elif hasattr(entity, 'first_name') and entity.first_name:
                # Para usuarios, usar first_name + last_name
                last_name = getattr(entity, 'last_name', '') or ''
                title = f"{entity.first_name} {last_name}".strip()
            elif hasattr(entity, 'username') and entity.username:
                title = f"@{entity.username}"
            else:
                # Fallback: usar ID del chat
                title = f"Chat {entity.id}"
            
            # 🔧 FIX: Garantizar que title nunca sea None, vacío o solo espacios
            if not title or not title.strip():
                title = f"Chat {entity.id}"
            
            # 🔧 FIX: Manejo seguro de datetime fields
            date_created = None
            if hasattr(entity, 'date') and entity.date:
                date_created = entity.date
            
            last_message_date = None
            if hasattr(dialog, 'date') and dialog.date:
                last_message_date = dialog.date
            
            # 🔧 FIX: Manejo de restriction_reason como lista
            restriction_reason = getattr(entity, 'restriction_reason', None)
            if isinstance(restriction_reason, list):
                # Convertir lista a string JSON o texto plano
                if restriction_reason:
                    try:
                        restriction_reason = json.dumps([str(r) for r in restriction_reason])
                    except:
                        restriction_reason = str(restriction_reason)
                else:
                    restriction_reason = None
            elif restriction_reason:
                restriction_reason = str(restriction_reason)
            
            # 🔧 FIX: Manejo seguro de username
            username = getattr(entity, 'username', None)
            if username:
                username = str(username)
            
            # 🔧 FIX: Manejo seguro de description
            description = getattr(entity, 'about', None)
            if description:
                description = str(description)
            
            # Información básica con todos los fixes aplicados
            chat_info = ChatInfo(
                id=entity.id,
                title=title,  # 🔧 FIX: Garantizado non-null
                type=chat_type,
                username=username,
                description=description,
                participants_count=getattr(entity, 'participants_count', None),
                is_broadcast=getattr(entity, 'broadcast', False),
                is_megagroup=getattr(entity, 'megagroup', False),
                is_private=not getattr(entity, 'username', None),
                date_created=date_created,
                last_message_date=last_message_date,
                has_geo=getattr(entity, 'has_geo', False),
                is_scam=getattr(entity, 'scam', False),
                is_verified=getattr(entity, 'verified', False),
                restriction_reason=restriction_reason,  # 🔧 FIX: Serialized properly
                discovered_at=datetime.now(),  # 🔧 FIX: Set current time
                scan_count=1,
                is_active=True,
                last_activity=last_message_date
            )
            
            return chat_info
            
        except Exception as e:
            logging.error(f"Error extracting chat info: {e}")
            return None

# ============= WEBSOCKET MANAGER =============

class WebSocketManager:
    """Gestor de conexiones WebSocket"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def broadcast(self, data: Dict[str, Any]):
        """🔧 FIX: Broadcast con safe JSON serialization"""
        if self.active_connections:
            message = safe_json_dumps(data)
            
            disconnected = []
            for connection in self.active_connections:
                try:
                    await connection.send_text(message)
                except:
                    disconnected.append(connection)
            
            # Limpiar conexiones muertas
            for conn in disconnected:
                self.disconnect(conn)

# ============= DISCOVERY SERVICE =============

class DiscoveryService:
    """🔧 FIX: Servicio principal con datetime handling"""
    
    def __init__(self):
        self.config = DiscoveryConfig()
        self.database = DiscoveryDatabase(self.config.db_path)
        self.scanner = TelegramScanner(self.config, self.database)
        self.ws_manager = WebSocketManager()
        self.http_client = httpx.AsyncClient()
        
        # Background task para escaneo automático
        self.auto_scan_task: Optional[asyncio.Task] = None
    
    async def initialize(self):
        """Inicializar servicio"""
        await self.scanner.initialize()
        self.auto_scan_task = asyncio.create_task(self._auto_scan_loop())
        logging.info("✅ Discovery Service initialized")
    
    async def shutdown(self):
        """Apagar servicio"""
        if self.auto_scan_task:
            self.auto_scan_task.cancel()
        
        if self.scanner.client:
            await self.scanner.client.disconnect()
        
        await self.http_client.aclose()
        logging.info("🛑 Discovery Service shutdown")
    
    async def _auto_scan_loop(self):
        """Loop automático de escaneo"""
        while True:
            try:
                await asyncio.sleep(self.config.scan_interval)
                
                if not self.scanner.is_scanning:
                    logging.info("🔄 Starting automatic scan...")
                    status = await self.scanner.scan_all_chats()
                    
                    # 🔧 FIX: Broadcast con safe serialization
                    await self.ws_manager.broadcast({
                        'type': 'scan_completed',
                        'status': safe_asdict(status),
                        'timestamp': datetime.now().isoformat()
                    })
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Auto scan error: {e}")
    
    async def get_chats_filtered(self, filters: ChatFilter, limit: int = 100, offset: int = 0) -> List[ChatInfo]:
        """Obtener chats con filtros aplicados"""
        return await self.database.get_chats(filters, limit, offset)
    
    async def trigger_manual_scan(self, force_refresh: bool = False) -> ScanStatus:
        """🔧 FIX: Trigger manual con safe serialization"""
        status = await self.scanner.scan_all_chats(force_refresh)
        
        # 🔧 FIX: Notificar via WebSocket con safe serialization
        await self.ws_manager.broadcast({
            'type': 'scan_status',
            'status': safe_asdict(status),
            'timestamp': datetime.now().isoformat()
        })
        
        return status
    
    async def get_service_stats(self) -> Dict[str, Any]:
        """🔧 FIX: Obtener estadísticas con Path object correction"""
        total_chats = len(await self.database.get_chats(limit=10000))
        
        # 🔧 FIX: Convertir db_path string a Path object para .stat()
        db_path_obj = Path(self.config.db_path)
        
        return {
            'service': 'discovery',
            'status': 'healthy',
            'uptime': time.time(),
            'scanner_stats': datetime_serializer(self.scanner.scan_stats),
            'current_scan': safe_asdict(self.scanner.scan_status),  # 🔧 FIX: Safe conversion
            'database_stats': {
                'total_chats': total_chats,
                'db_path': str(self.config.db_path),
                'db_size_mb': db_path_obj.stat().st_size / 1024 / 1024 if db_path_obj.exists() else 0  # 🔧 FIX
            },
            'config': {
                'scan_interval': self.config.scan_interval,
                'rate_limit_delay': self.config.rate_limit_delay,
                'cache_duration': self.config.cache_duration
            }
        }

# ============= FASTAPI APPLICATION =============

# Instancia global del servicio
discovery_service: Optional[DiscoveryService] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management"""
    global discovery_service
    
    try:
        logging.info("🚀 Starting Discovery Service...")
        discovery_service = DiscoveryService()
        await discovery_service.initialize()
        
        print("\n" + "="*60)
        print("🔍 DISCOVERY SERVICE v2.0 - FIXED")
        print("="*60)
        print("🌐 Endpoints:")
        print("   📊 Status:           http://localhost:8002/status")
        print("   🔍 Scan Chats:       http://localhost:8002/api/discovery/scan")
        print("   📋 List Chats:       http://localhost:8002/api/discovery/chats") 
        print("   🏥 Health:           http://localhost:8002/health")
        print("   📚 API Docs:         http://localhost:8002/docs")
        print("="*60)
        
        yield
        
    finally:
        if discovery_service:
            await discovery_service.shutdown()

# Crear aplicación FastAPI
app = FastAPI(
    title="🔍 Discovery Service",
    description="Auto-discovery de chats de Telegram con arquitectura enterprise",
    version="2.0.0",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============= API ENDPOINTS =============

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "discovery",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }

@app.get("/status")
async def get_status():
    """🔧 FIX: Estado completo del servicio con safe serialization"""
    if not discovery_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        stats = await discovery_service.get_service_stats()
        return stats
    except Exception as e:
        logging.error(f"🔧 FIX: Error getting status: {e}")
        return {
            "status": "error",
            "error": str(e),
            "service": "discovery",
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/discovery/scan")
async def start_scan(request: ScanRequest = ScanRequest()):
    """🔧 FIX: Iniciar escaneo con safe response"""
    if not discovery_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        status = await discovery_service.trigger_manual_scan(request.force_refresh)
        return {
            "message": "Scan started",
            "status": safe_asdict(status)  # 🔧 FIX: Safe serialization
        }
    except Exception as e:
        logging.error(f"🔧 FIX: Error starting scan: {e}")
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")

@app.get("/api/discovery/scan/status")
async def get_scan_status():
    """🔧 FIX: Obtener estado del escaneo con safe serialization"""
    if not discovery_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        return safe_asdict(discovery_service.scanner.scan_status)  # 🔧 FIX: Safe conversion
    except Exception as e:
        logging.error(f"🔧 FIX: Error getting scan status: {e}")
        return {
            "error": str(e),
            "is_scanning": False,
            "progress_percent": 0.0
        }

@app.get("/api/discovery/chats")
async def get_chats(
    chat_type: Optional[str] = None,
    min_participants: Optional[int] = None,
    max_participants: Optional[int] = None,
    has_username: Optional[bool] = None,
    is_broadcast: Optional[bool] = None,
    is_megagroup: Optional[bool] = None,
    search_term: Optional[str] = None,
    is_active: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0
):
    """🔧 FIX: Obtener lista de chats con safe serialization"""
    if not discovery_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        filters = ChatFilter(
            chat_type=chat_type,
            min_participants=min_participants,
            max_participants=max_participants,
            has_username=has_username,
            is_broadcast=is_broadcast,
            is_megagroup=is_megagroup,
            search_term=search_term,
            is_active=is_active
        )
        
        chats = await discovery_service.get_chats_filtered(filters, limit, offset)
        
        # 🔧 FIX: Serializar chats de forma segura
        chats_data = [safe_asdict(chat) for chat in chats]
        
        return {
            "chats": chats_data,
            "total": len(chats_data),
            "filters_applied": filters.model_dump(exclude_none=True),  # 🔧 FIX: .dict() -> .model_dump()
            "pagination": {
                "limit": limit,
                "offset": offset
            }
        }
        
    except Exception as e:
        logging.error(f"🔧 FIX: Error getting chats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get chats: {str(e)}")

@app.get("/api/discovery/chats/{chat_id}")
async def get_chat_detail(chat_id: int):
    """🔧 FIX: Obtener detalle de un chat específico"""
    if not discovery_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        chat = await discovery_service.database.get_chat_by_id(chat_id)
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        
        return {
            "chat": safe_asdict(chat),  # 🔧 FIX: Safe serialization
            "found": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"🔧 FIX: Error getting chat {chat_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get chat: {str(e)}")

# ============= WEBSOCKET ENDPOINT =============

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """🔧 FIX: WebSocket endpoint con manejo de errores"""
    if not discovery_service:
        await websocket.close(code=1011, reason="Service not initialized")
        return
    
    try:
        await discovery_service.ws_manager.connect(websocket)
        
        # Enviar estado inicial
        initial_status = {
            "type": "connection_established",
            "scan_status": safe_asdict(discovery_service.scanner.scan_status),
            "timestamp": datetime.now().isoformat()
        }
        
        await websocket.send_text(safe_json_dumps(initial_status))
        
        # Mantener conexión
        while True:
            try:
                # Recibir mensajes del cliente (opcional)
                data = await websocket.receive_text()
                
                # Procesar comandos del cliente si es necesario
                try:
                    message = json.loads(data)
                    if message.get("type") == "ping":
                        pong_response = {
                            "type": "pong", 
                            "timestamp": datetime.now().isoformat()
                        }
                        await websocket.send_text(safe_json_dumps(pong_response))
                        
                except json.JSONDecodeError:
                    # Ignorar mensajes mal formados
                    pass
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logging.error(f"🔧 FIX: WebSocket error: {e}")
                break
                
    except Exception as e:
        logging.error(f"🔧 FIX: WebSocket connection error: {e}")
    finally:
        if discovery_service:
            discovery_service.ws_manager.disconnect(websocket)

# ============= STARTUP CONFIGURATION =============

if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Crear directorios necesarios
    Path("data").mkdir(exist_ok=True)
    Path("sessions").mkdir(exist_ok=True)
    
    print("\n🔍 DISCOVERY SERVICE v2.0 - DATETIME FIXED")
    print("="*50)
    print("🔧 FIXES APPLIED:")
    print("   ✅ JSON datetime serialization")
    print("   ✅ Dataclass ScanStatus conversion")
    print("   ✅ Safe database datetime handling")
    print("   ✅ WebSocket safe broadcasting")
    print("   ✅ Error handling improvements")
    print("="*50)
    
    # Ejecutar servidor
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,
        log_level="info",
        reload=False
    )