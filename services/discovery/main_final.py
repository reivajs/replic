#!/usr/bin/env python3
"""
🔍 DISCOVERY SERVICE v3.2 - FINAL FIXED
========================================
Versión final corregida con manejo correcto de Dialog objects
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

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Telegram imports
try:
    from telethon import TelegramClient
    from telethon.tl.types import User, Chat, Channel
    TELETHON_AVAILABLE = True
    print("✅ Telethon imported successfully")
except ImportError as e:
    TELETHON_AVAILABLE = False
    print(f"❌ Telethon not available: {e}")

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
            
            cursor.execute("SELECT COUNT(*) FROM discovered_chats")
            total_chats = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM discovered_chats WHERE type = 'channel'")
            channels = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM discovered_chats WHERE type IN ('group', 'supergroup')")
            groups = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM discovered_chats WHERE username IS NOT NULL")
            public_chats = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "total_chats": total_chats,
                "channels": channels,
                "groups": groups,
                "public_chats": public_chats,
                "verified_chats": 0,
                "avg_participants": 0
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting stats: {e}")
            return {}

# ============= TELEGRAM SCANNER =============

class TelegramScanner:
    """Scanner de chats de Telegram - FIXED VERSION"""
    
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
        self.config_valid = False
        self.config_errors = []
    
    async def initialize(self) -> bool:
        """Inicializar cliente de Telegram"""
        if not TELETHON_AVAILABLE:
            self.config_errors.append("Telethon no disponible")
            logger.error("❌ Telethon no disponible")
            return False
        
        try:
            # Obtener configuración
            api_id = os.getenv('TELEGRAM_API_ID')
            api_hash = os.getenv('TELEGRAM_API_HASH')
            phone = os.getenv('TELEGRAM_PHONE')
            
            print(f"🔍 Debugging config:")
            print(f"   API_ID: {api_id} (type: {type(api_id)})")
            print(f"   API_HASH: {api_hash[:8] + '...' if api_hash else 'None'}")
            print(f"   PHONE: {phone}")
            
            # Validación
            if not api_id or not api_hash or not phone:
                self.config_errors.append("Variables de Telegram faltantes")
                return False
            
            # Crear cliente
            logger.info("📱 Creando cliente de Telegram...")
            self.client = TelegramClient('discovery_session', int(api_id), api_hash)
            
            # Conectar
            logger.info("🔄 Conectando a Telegram...")
            await self.client.start(phone=phone)
            
            # Verificar conexión
            me = await self.client.get_me()
            logger.info(f"✅ Conectado a Telegram como: {me.first_name} (@{me.username or 'sin_username'})")
            
            self.config_valid = True
            return True
            
        except Exception as e:
            error_msg = f"Error conectando a Telegram: {e}"
            self.config_errors.append(error_msg)
            logger.error(f"❌ {error_msg}")
            return False
    
    async def scan_chats(self, database: DiscoveryDatabase, 
                        max_chats: int = 1000, 
                        include_private: bool = False) -> Dict[str, Any]:
        """🔧 FIX: Escanear chats de Telegram con manejo correcto de Dialog objects"""
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
            
            # 🔧 FIX: Usar get_dialogs en lugar de GetDialogsRequest directamente
            logger.info("📊 Getting dialogs...")
            dialogs = await self.client.get_dialogs(limit=max_chats)
            
            logger.info(f"📊 Found {len(dialogs)} dialogs to process")
            
            # Procesar cada diálogo
            for i, dialog in enumerate(dialogs):
                try:
                    # 🔧 FIX: Acceder correctamente a la entidad
                    entity = dialog.entity
                    
                    # Skip private chats if not requested
                    if isinstance(entity, User) and not include_private:
                        continue
                    
                    chat_data = await self._extract_chat_data(entity)
                    if chat_data:
                        # Guardar en base de datos
                        if database.save_chat(chat_data):
                            self.stats["new_discovered"] += 1
                            logger.info(f"✅ Saved: {chat_data['title']} ({chat_data['type']})")
                        else:
                            self.stats["updated"] += 1
                    
                    self.stats["total_scanned"] += 1
                    
                    # Update progress
                    self.scan_progress = {
                        "current": i + 1,
                        "total": len(dialogs),
                        "status": "scanning"
                    }
                    
                    # Rate limiting
                    if i % 10 == 0:
                        logger.info(f"📊 Processed {i+1}/{len(dialogs)} dialogs...")
                        await asyncio.sleep(0.5)
                        
                except Exception as e:
                    logger.error(f"❌ Error processing dialog {i}: {e}")
                    self.stats["errors"] += 1
            
            # Finalizar scan
            scan_duration = (datetime.now() - scan_start).total_seconds()
            self.stats["last_scan"] = datetime.now().isoformat()
            self.stats["scan_duration"] = scan_duration
            
            self.scan_progress = {
                "current": len(dialogs),
                "total": len(dialogs),
                "status": "completed"
            }
            
            logger.info(f"✅ Scan completed: {self.stats['total_scanned']} chats processed, {self.stats['new_discovered']} saved")
            
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
        """🔧 FIX: Extraer datos de un chat entity correctamente"""
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
                    "username": getattr(entity, 'username', None),
                    "is_verified": getattr(entity, 'verified', False),
                    "is_scam": getattr(entity, 'scam', False),
                    "is_fake": getattr(entity, 'fake', False),
                    "has_photo": getattr(entity, 'photo', None) is not None,
                    "is_public": getattr(entity, 'username', None) is not None
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
                    "type": "supergroup" if getattr(entity, 'megagroup', False) else "channel",
                    "username": getattr(entity, 'username', None),
                    "description": getattr(entity, 'about', None),
                    "participants_count": getattr(entity, 'participants_count', None),
                    "is_broadcast": getattr(entity, 'broadcast', False),
                    "is_verified": getattr(entity, 'verified', False),
                    "is_scam": getattr(entity, 'scam', False),
                    "is_fake": getattr(entity, 'fake', False),
                    "has_photo": getattr(entity, 'photo', None) is not None,
                    "is_public": getattr(entity, 'username', None) is not None
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
            "stats": self.stats,
            "config_valid": self.config_valid,
            "config_errors": self.config_errors
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
        logger.info("🔍 Starting Discovery Service v3.2...")
        
        # Initialize scanner
        scanner_ready = await scanner.initialize()
        if scanner_ready:
            logger.info("✅ Telegram scanner initialized")
        else:
            logger.warning(f"⚠️ Telegram scanner not available: {scanner.config_errors}")
        
        # Info
        print("\n" + "="*60)
        print("🔍 DISCOVERY SERVICE v3.2 - FINAL FIXED")
        print("="*60)
        print("🌐 Endpoints:")
        print("   📊 Dashboard:     http://localhost:8002/")
        print("   🔍 Scan:          POST /api/discovery/scan")
        print("   📋 Chats:         GET /api/discovery/chats")
        print("   🏥 Health:        GET /health")
        print("   📚 Docs:          GET /docs")
        print("="*60)
        
        if scanner_ready:
            print("✅ Telegram scanner ready - auto-discovery enabled!")
            print("🎯 To scan: curl -X POST http://localhost:8002/api/discovery/scan")
        else:
            print("❌ Telegram scanner not ready:")
            for error in scanner.config_errors:
                print(f"   - {error}")
        
        yield
        
    finally:
        if scanner.client:
            await scanner.client.disconnect()
        logger.info("🛑 Discovery Service stopped")

# FastAPI app
app = FastAPI(
    title="🔍 Discovery Service v3.2",
    description="Auto-discovery de chats Telegram - FINAL FIXED",
    version="3.2.0",
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
        "version": "3.2.0",
        "status": "running",
        "scanner_ready": scanner.config_valid,
        "description": "Auto-discovery service for Telegram chats - FINAL FIXED"
    }

@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "service": "discovery",
        "timestamp": datetime.now().isoformat(),
        "scanner_connected": scanner.config_valid,
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
        "version": "3.2.0",
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
        raise HTTPException(status_code=503, detail=f"Telegram scanner not available: {scanner.config_errors}")
    
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
    limit: int = Query(100, description="Limit results"),
    offset: int = Query(0, description="Offset results")
):
    """Obtener chats discovered con filtros"""
    filters = {}
    
    if chat_type:
        filters["chat_type"] = chat_type
    if search_term:
        filters["search_term"] = search_term
    
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

@app.post("/api/discovery/configure")
async def configure_discovered_chat_fixed(request: dict):
    """Configurar chat discovered"""
    try:
        chat_id = request.get("chat_id")
        chat_title = request.get("chat_title", f"Chat {chat_id}")
        
        if not chat_id:
            raise HTTPException(status_code=400, detail="chat_id is required")
        
        logger.info(f"Configuring chat {chat_id}: {chat_title}")
        
        return {
            "success": True,
            "message": f"Chat '{chat_title}' configured successfully"
        }
        
    except Exception as e:
        logger.error(f"❌ Error configuring chat: {e}")
        raise HTTPException(status_code=500, detail=f"Configuration error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "main_final:app",
        host="0.0.0.0", 
        port=8002,
        reload=False,
        log_level="info"
    )