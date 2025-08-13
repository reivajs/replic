#!/usr/bin/env python3
"""
🔍 DISCOVERY SERVICE v3.0 - COMPLETE IMPLEMENTATION
================================================
Servicio completo de auto-discovery que conecta con tu UI existente
Compatible con tu arquitectura enterprise actual
"""

import asyncio
import json
import os
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Telegram imports
try:
    from telethon import TelegramClient
    from telethon.tl.types import User, Chat, Channel
    from telethon.tl.functions.contacts import ResolveUsernameRequest
    from telethon.tl.functions.messages import GetDialogsRequest
    from telethon.tl.types import InputPeerEmpty
    TELETHON_AVAILABLE = True
except ImportError:
    TELETHON_AVAILABLE = False

# Logger
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============= MODELS =============

class ScanRequest(BaseModel):
    """Request para iniciar scan"""
    force_refresh: bool = Field(default=False, description="Force full rescan")
    max_chats: int = Field(default=1000, description="Max chats to scan")
    include_private: bool = Field(default=False, description="Include private chats")

class ChatFilter(BaseModel):
    """Filtros para búsqueda de chats"""
    chat_type: Optional[str] = Field(None, description="channel, group, supergroup, private")
    search_term: Optional[str] = Field(None, description="Search in title/description")
    min_participants: Optional[int] = Field(None, description="Minimum participants")
    max_participants: Optional[int] = Field(None, description="Maximum participants")
    is_active: Optional[bool] = Field(None, description="Only active chats")
    has_username: Optional[bool] = Field(None, description="Has public username")

class DiscoveredChat(BaseModel):
    """Modelo para chat discovered"""
    id: int
    title: str
    type: str
    username: Optional[str] = None
    description: Optional[str] = None
    participants_count: Optional[int] = None
    is_broadcast: bool = False
    is_verified: bool = False
    is_scam: bool = False
    is_fake: bool = False
    discovered_at: datetime
    last_activity: Optional[datetime] = None
    has_photo: bool = False
    is_public: bool = False

# ============= DATABASE MANAGER =============

class DiscoveryDatabase:
    """Gestor de base de datos para chats discovered"""
    
    def __init__(self, db_path: str = "data/discovery.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Inicializar base de datos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS discovered_chats (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                type TEXT NOT NULL,
                username TEXT,
                description TEXT,
                participants_count INTEGER,
                is_broadcast BOOLEAN DEFAULT 0,
                is_verified BOOLEAN DEFAULT 0,
                is_scam BOOLEAN DEFAULT 0,
                is_fake BOOLEAN DEFAULT 0,
                discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP,
                has_photo BOOLEAN DEFAULT 0,
                is_public BOOLEAN DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_chat_type ON discovered_chats(type)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_chat_title ON discovered_chats(title)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_participants ON discovered_chats(participants_count)
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Discovery database initialized: {self.db_path}")
    
    def save_chat(self, chat_data: Dict[str, Any]) -> bool:
        """Guardar chat discovered"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO discovered_chats 
                (id, title, type, username, description, participants_count,
                 is_broadcast, is_verified, is_scam, is_fake, discovered_at,
                 last_activity, has_photo, is_public, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                chat_data['id'], chat_data['title'], chat_data['type'],
                chat_data.get('username'), chat_data.get('description'),
                chat_data.get('participants_count'), chat_data.get('is_broadcast', False),
                chat_data.get('is_verified', False), chat_data.get('is_scam', False),
                chat_data.get('is_fake', False), chat_data.get('discovered_at'),
                chat_data.get('last_activity'), chat_data.get('has_photo', False),
                chat_data.get('is_public', False), datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving chat {chat_data.get('id')}: {e}")
            return False
    
    def get_chats(self, filters: Dict[str, Any] = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Obtener chats con filtros"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM discovered_chats WHERE 1=1"
            params = []
            
            if filters:
                if filters.get('chat_type'):
                    query += " AND type = ?"
                    params.append(filters['chat_type'])
                
                if filters.get('search_term'):
                    search_term = f"%{filters['search_term']}%"
                    query += " AND (title LIKE ? OR description LIKE ? OR username LIKE ?)"
                    params.extend([search_term, search_term, search_term])
                
                if filters.get('min_participants') is not None:
                    query += " AND participants_count >= ?"
                    params.append(filters['min_participants'])
                
                if filters.get('max_participants') is not None:
                    query += " AND participants_count <= ?"
                    params.append(filters['max_participants'])
                
                if filters.get('has_username') is not None:
                    if filters['has_username']:
                        query += " AND username IS NOT NULL"
                    else:
                        query += " AND username IS NULL"
                
                if filters.get('is_verified') is not None:
                    query += " AND is_verified = ?"
                    params.append(1 if filters['is_verified'] else 0)
            
            query += " ORDER BY last_updated DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            chats = []
            for row in rows:
                chat = dict(row)
                # Convert boolean fields
                for bool_field in ['is_broadcast', 'is_verified', 'is_scam', 'is_fake', 'has_photo', 'is_public']:
                    chat[bool_field] = bool(chat[bool_field])
                chats.append(chat)
            
            conn.close()
            return chats
            
        except Exception as e:
            logger.error(f"❌ Error getting chats: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de la base de datos"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Stats básicas
            cursor.execute("SELECT COUNT(*) FROM discovered_chats")
            total_chats = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM discovered_chats WHERE type = 'channel'")
            channels = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM discovered_chats WHERE type IN ('group', 'supergroup')")
            groups = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM discovered_chats WHERE username IS NOT NULL")
            public_chats = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM discovered_chats WHERE is_verified = 1")
            verified_chats = cursor.fetchone()[0]
            
            cursor.execute("SELECT AVG(participants_count) FROM discovered_chats WHERE participants_count > 0")
            avg_participants = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return {
                "total_chats": total_chats,
                "channels": channels,
                "groups": groups,
                "public_chats": public_chats,
                "verified_chats": verified_chats,
                "avg_participants": round(avg_participants, 1)
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting stats: {e}")
            return {}

# ============= TELEGRAM SCANNER =============

class TelegramScanner:
    """Scanner de chats de Telegram"""
    
    def __init__(self):
        self.client = None
        self.is_scanning = False
        self.scan_progress = {"current": 0, "total": 0, "status": "idle"}
        self.stats = {
            "total_scanned": 0,
            "new_discovered": 0,
            "updated": 0,
            "errors": 0,
            "last_scan": None,
            "scan_duration": 0
        }
    
    async def initialize(self) -> bool:
        """Inicializar cliente de Telegram"""
        if not TELETHON_AVAILABLE:
            logger.error("❌ Telethon no disponible")
            return False
        
        try:
            # Usar configuración desde variables de entorno
            api_id = int(os.getenv('TELEGRAM_API_ID', 0))
            api_hash = os.getenv('TELEGRAM_API_HASH', '')
            phone = os.getenv('TELEGRAM_PHONE', '')
            
            if not api_id or not api_hash or not phone:
                logger.error("❌ Configuración de Telegram incompleta")
                return False
            
            self.client = TelegramClient('discovery_session', api_id, api_hash)
            await self.client.start(phone=phone)
            
            me = await self.client.get_me()
            logger.info(f"✅ Scanner conectado como: {me.first_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error inicializando scanner: {e}")
            return False
    
    async def scan_chats(self, database: DiscoveryDatabase, 
                        max_chats: int = 1000, 
                        include_private: bool = False) -> Dict[str, Any]:
        """Escanear chats de Telegram"""
        if not self.client:
            return {"error": "Scanner not initialized"}
        
        if self.is_scanning:
            return {"error": "Scan already in progress"}
        
        self.is_scanning = True
        scan_start = datetime.now()
        
        try:
            logger.info(f"🔍 Starting chat scan (max: {max_chats})")
            
            # Reset stats
            self.stats.update({
                "total_scanned": 0,
                "new_discovered": 0,
                "updated": 0,
                "errors": 0
            })
            
            # Obtener diálogos
            dialogs = []
            offset_date = None
            offset_id = 0
            offset_peer = InputPeerEmpty()
            
            while len(dialogs) < max_chats:
                try:
                    result = await self.client(GetDialogsRequest(
                        offset_date=offset_date,
                        offset_id=offset_id,
                        offset_peer=offset_peer,
                        limit=100,
                        hash=0
                    ))
                    
                    if not result.dialogs:
                        break
                    
                    dialogs.extend(result.dialogs)
                    
                    # Update pagination
                    if result.dialogs:
                        last_dialog = result.dialogs[-1]
                        offset_date = last_dialog.top_message
                        offset_id = last_dialog.top_message
                        offset_peer = last_dialog.peer
                    
                    # Update progress
                    self.scan_progress = {
                        "current": len(dialogs),
                        "total": max_chats,
                        "status": "scanning"
                    }
                    
                    logger.info(f"📊 Scanned {len(dialogs)} dialogs...")
                    
                except Exception as e:
                    logger.error(f"❌ Error getting dialogs: {e}")
                    break
            
            # Procesar cada diálogo
            for i, dialog in enumerate(dialogs[:max_chats]):
                try:
                    entity = dialog.entity
                    
                    # Skip private chats if not requested
                    if isinstance(entity, User) and not include_private:
                        continue
                    
                    chat_data = await self._extract_chat_data(entity)
                    if chat_data:
                        # Guardar en base de datos
                        if database.save_chat(chat_data):
                            self.stats["new_discovered"] += 1
                        else:
                            self.stats["updated"] += 1
                    
                    self.stats["total_scanned"] += 1
                    
                    # Update progress
                    self.scan_progress["current"] = i + 1
                    
                    # Rate limiting
                    if i % 50 == 0:
                        await asyncio.sleep(1)
                        
                except Exception as e:
                    logger.error(f"❌ Error processing dialog {i}: {e}")
                    self.stats["errors"] += 1
            
            # Finalizar scan
            scan_duration = (datetime.now() - scan_start).total_seconds()
            self.stats["last_scan"] = datetime.now().isoformat()
            self.stats["scan_duration"] = scan_duration
            
            self.scan_progress = {
                "current": len(dialogs),
                "total": max_chats,
                "status": "completed"
            }
            
            logger.info(f"✅ Scan completed: {self.stats['total_scanned']} chats, {self.stats['new_discovered']} new")
            
            return {
                "success": True,
                "stats": self.stats,
                "scan_duration": scan_duration
            }
            
        except Exception as e:
            logger.error(f"❌ Scan error: {e}")
            return {"error": str(e)}
        finally:
            self.is_scanning = False
    
    async def _extract_chat_data(self, entity) -> Optional[Dict[str, Any]]:
        """Extraer datos de un chat entity"""
        try:
            chat_data = {
                "id": entity.id,
                "discovered_at": datetime.now().isoformat(),
                "last_activity": datetime.now().isoformat()
            }
            
            if isinstance(entity, User):
                chat_data.update({
                    "title": f"{entity.first_name or ''} {entity.last_name or ''}".strip() or "Unknown User",
                    "type": "private",
                    "username": entity.username,
                    "is_verified": getattr(entity, 'verified', False),
                    "is_scam": getattr(entity, 'scam', False),
                    "is_fake": getattr(entity, 'fake', False),
                    "has_photo": getattr(entity, 'photo', None) is not None,
                    "is_public": entity.username is not None
                })
                
            elif isinstance(entity, Chat):
                chat_data.update({
                    "title": entity.title,
                    "type": "group",
                    "participants_count": getattr(entity, 'participants_count', None),
                    "has_photo": getattr(entity, 'photo', None) is not None,
                    "is_public": False
                })
                
            elif isinstance(entity, Channel):
                chat_data.update({
                    "title": entity.title,
                    "type": "supergroup" if entity.megagroup else "channel",
                    "username": entity.username,
                    "description": getattr(entity, 'about', None),
                    "participants_count": getattr(entity, 'participants_count', None),
                    "is_broadcast": entity.broadcast,
                    "is_verified": getattr(entity, 'verified', False),
                    "is_scam": getattr(entity, 'scam', False),
                    "is_fake": getattr(entity, 'fake', False),
                    "has_photo": getattr(entity, 'photo', None) is not None,
                    "is_public": entity.username is not None
                })
            
            return chat_data
            
        except Exception as e:
            logger.error(f"❌ Error extracting chat data: {e}")
            return None
    
    def get_scan_status(self) -> Dict[str, Any]:
        """Obtener estado del scan"""
        return {
            "is_scanning": self.is_scanning,
            "progress": self.scan_progress,
            "stats": self.stats
        }

# ============= DISCOVERY SERVICE =============

# Global instances
database = DiscoveryDatabase()
scanner = TelegramScanner()
websocket_connections: List[WebSocket] = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle del servicio"""
    try:
        logger.info("🔍 Starting Discovery Service v3.0...")
        
        # Initialize scanner
        scanner_ready = await scanner.initialize()
        if scanner_ready:
            logger.info("✅ Telegram scanner initialized")
        else:
            logger.warning("⚠️ Telegram scanner not available")
        
        # Info
        print("\n" + "="*50)
        print("🔍 DISCOVERY SERVICE v3.0")
        print("="*50)
        print("🌐 Endpoints:")
        print("   📊 Dashboard:     http://localhost:8002/")
        print("   🔍 Scan:          POST /api/discovery/scan")
        print("   📋 Chats:         GET /api/discovery/chats")
        print("   🏥 Health:        GET /health")
        print("   📚 Docs:          GET /docs")
        print("   🔌 WebSocket:     ws://localhost:8002/ws")
        print("="*50)
        
        yield
        
    finally:
        if scanner.client:
            await scanner.client.disconnect()
        logger.info("🛑 Discovery Service stopped")

# FastAPI app
app = FastAPI(
    title="🔍 Discovery Service v3.0",
    description="Auto-discovery completo de chats Telegram",
    version="3.0.0",
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

# ============= ENDPOINTS =============

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "discovery",
        "version": "3.0.0",
        "status": "running",
        "scanner_ready": scanner.client is not None,
        "description": "Auto-discovery service for Telegram chats"
    }

@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "service": "discovery",
        "timestamp": datetime.now().isoformat(),
        "scanner_connected": scanner.client is not None,
        "database_ready": database.db_path is not None,
        "is_scanning": scanner.is_scanning
    }

@app.get("/status")
async def get_status():
    """Estado detallado del servicio"""
    scan_status = scanner.get_scan_status()
    db_stats = database.get_stats()
    
    return {
        "service": "discovery",
        "version": "3.0.0",
        "scanner_status": scan_status,
        "database_stats": db_stats,
        "current_scan": scan_status["progress"],
        "scanner_stats": scan_status["stats"],
        "websocket_connections": len(websocket_connections)
    }

@app.post("/api/discovery/scan")
async def trigger_scan(request: ScanRequest):
    """Trigger discovery scan"""
    if not scanner.client:
        raise HTTPException(status_code=503, detail="Telegram scanner not available")
    
    if scanner.is_scanning:
        raise HTTPException(status_code=409, detail="Scan already in progress")
    
    # Start scan in background
    asyncio.create_task(scanner.scan_chats(
        database, 
        max_chats=request.max_chats,
        include_private=request.include_private
    ))
    
    return {
        "success": True,
        "message": "Discovery scan started",
        "max_chats": request.max_chats,
        "include_private": request.include_private
    }

@app.get("/api/discovery/chats")
async def get_discovered_chats(
    chat_type: Optional[str] = Query(None, description="Filter by type"),
    search_term: Optional[str] = Query(None, description="Search term"),
    min_participants: Optional[int] = Query(None, description="Min participants"),
    max_participants: Optional[int] = Query(None, description="Max participants"),
    has_username: Optional[bool] = Query(None, description="Has username"),
    is_verified: Optional[bool] = Query(None, description="Is verified"),
    limit: int = Query(100, description="Limit results"),
    offset: int = Query(0, description="Offset results")
):
    """Obtener chats discovered con filtros"""
    filters = {}
    
    if chat_type:
        filters["chat_type"] = chat_type
    if search_term:
        filters["search_term"] = search_term
    if min_participants is not None:
        filters["min_participants"] = min_participants
    if max_participants is not None:
        filters["max_participants"] = max_participants
    if has_username is not None:
        filters["has_username"] = has_username
    if is_verified is not None:
        filters["is_verified"] = is_verified
    
    chats = database.get_chats(filters, limit, offset)
    total = database.get_stats().get("total_chats", 0)
    
    return {
        "chats": chats,
        "total": total,
        "limit": limit,
        "offset": offset,
        "filters_applied": filters
    }

@app.get("/api/discovery/stats")
async def get_discovery_stats():
    """Estadísticas del discovery"""
    db_stats = database.get_stats()
    scan_status = scanner.get_scan_status()
    
    return {
        "database": db_stats,
        "scanner": scan_status["stats"],
        "current_scan": scan_status["progress"],
        "is_scanning": scan_status["is_scanning"]
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket para updates en tiempo real"""
    await websocket.accept()
    websocket_connections.append(websocket)
    
    try:
        # Send initial data
        initial_data = {
            "type": "initial_connection",
            "status": await get_status(),
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send_text(json.dumps(initial_data))
        
        # Keep connection alive
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }))
                elif message.get("type") == "request_status":
                    status = await get_status()
                    await websocket.send_text(json.dumps({
                        "type": "status_update",
                        "data": status,
                        "timestamp": datetime.now().isoformat()
                    }))
                    
            except asyncio.TimeoutError:
                await websocket.send_text(json.dumps({"type": "ping"}))
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
    finally:
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)

# ============= BACKGROUND TASKS =============

async def broadcast_scan_updates():
    """Broadcast scan updates to WebSocket clients"""
    while True:
        try:
            if scanner.is_scanning and websocket_connections:
                status = scanner.get_scan_status()
                message = {
                    "type": "scan_update",
                    "data": status,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Send to all connected clients
                for websocket in websocket_connections.copy():
                    try:
                        await websocket.send_text(json.dumps(message))
                    except:
                        websocket_connections.remove(websocket)
            
            await asyncio.sleep(2)  # Update every 2 seconds
            
        except Exception as e:
            logger.error(f"❌ Broadcast error: {e}")
            await asyncio.sleep(5)

@app.on_event("startup")
async def startup_background_tasks():
    """Start background tasks"""
    asyncio.create_task(broadcast_scan_updates())

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0", 
        port=8002,
        reload=False,
        log_level="info"
    )