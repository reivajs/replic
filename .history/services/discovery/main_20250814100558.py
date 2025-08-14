#!/usr/bin/env python3
"""
🔍 DISCOVERY SERVICE v4.0 - ENTERPRISE FINAL
==============================================
Auto-discovery system para Telegram chats con UI integration
"""
from dotenv import load_dotenv
load_dotenv()  # Cargar variables .env ANTES de todo
import asyncio
import json
import logging
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============= TELEGRAM INTEGRATION =============

TELETHON_AVAILABLE = False
try:
    from telethon import TelegramClient
    from telethon.tl.types import Channel, Chat, User
    TELETHON_AVAILABLE = True
    logger.info("✅ Telethon disponible")
except ImportError:
    logger.warning("⚠️ Telethon no disponible - simulando datos")

# ============= MODELS =============

class ScanRequest(BaseModel):
    """Request para iniciar scan"""
    force_refresh: bool = False
    max_chats: int = 1000
    include_private: bool = False

class ChatInfo(BaseModel):
    """Información de chat discovered"""
    id: int
    title: str
    type: str
    username: Optional[str] = None
    description: Optional[str] = None
    participants_count: Optional[int] = None
    is_public: bool = False
    is_verified: bool = False
    discovered_at: str

# ============= DATABASE =============

class DiscoveryDatabase:
    """Database para chats discovered"""
    
    def __init__(self):
        self.db_path = Path("data/discovery.db")
        self.db_path.parent.mkdir(exist_ok=True)
        self._setup_database()
    
    def _setup_database(self):
        """Setup inicial de la database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS discovered_chats (
                        id INTEGER PRIMARY KEY,
                        title TEXT NOT NULL,
                        type TEXT NOT NULL,
                        username TEXT,
                        description TEXT,
                        participants_count INTEGER,
                        is_public BOOLEAN DEFAULT FALSE,
                        is_verified BOOLEAN DEFAULT FALSE,
                        discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_chat_type ON discovered_chats(type);
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_public_chats ON discovered_chats(is_public);
                """)
                
                logger.info("✅ Discovery database initialized")
                
        except Exception as e:
            logger.error(f"❌ Database setup error: {e}")
    
    async def save_chat(self, chat_data: Dict[str, Any]) -> bool:
        """Guardar chat discovered"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO discovered_chats 
                    (id, title, type, username, description, participants_count, 
                     is_public, is_verified, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    chat_data["id"],
                    chat_data["title"],
                    chat_data["type"],
                    chat_data.get("username"),
                    chat_data.get("description"),
                    chat_data.get("participants_count"),
                    chat_data.get("is_public", False),
                    chat_data.get("is_verified", False)
                ))
                return True
        except Exception as e:
            logger.error(f"❌ Error saving chat {chat_data.get('id')}: {e}")
            return False
    
    async def get_chats(self, 
                       chat_type: Optional[str] = None,
                       search_term: Optional[str] = None,
                       min_participants: Optional[int] = None,
                       limit: int = 100,
                       offset: int = 0,
                       is_private: Optional[bool] = None) -> List[Dict[str, Any]]:
        """Obtener chats con filtros"""
        try:
            query = "SELECT * FROM discovered_chats WHERE 1=1"
            params = []
            
            # ✅ ENTERPRISE FIX: Filtros inteligentes
            if chat_type and chat_type not in ["", "all"]:
                if "," in chat_type:
                    # Multiple types
                    types = [t.strip() for t in chat_type.split(",")]
                    placeholders = ",".join("?" * len(types))
                    query += f" AND type IN ({placeholders})"
                    params.extend(types)
                else:
                    query += " AND type = ?"
                    params.append(chat_type)
            
            if search_term:
                query += " AND (title LIKE ? OR username LIKE ? OR description LIKE ?)"
                search_pattern = f"%{search_term}%"
                params.extend([search_pattern, search_pattern, search_pattern])
            
            if min_participants is not None and min_participants > 0:
                query += " AND participants_count >= ?"
                params.append(min_participants)
            
            # ✅ CRITICAL FIX: Excluir chats privados por defecto
            if is_private is False:
                query += " AND (type != 'private' OR type IS NULL)"
            
            query += " ORDER BY participants_count DESC NULLS LAST, title ASC"
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                
                chats = []
                for row in rows:
                    chat = dict(row)
                    # ✅ ENTERPRISE ENHANCEMENT: Add metadata
                    chat["discovered_at"] = chat.get("discovered_at") or chat.get("updated_at")
                    chat["_relevance_score"] = self._calculate_relevance(chat)
                    chats.append(chat)
                
                logger.info(f"✅ Retrieved {len(chats)} chats (query: {len(params)} filters)")
                return chats
                
        except Exception as e:
            logger.error(f"❌ Error retrieving chats: {e}")
            return []
    
    def _calculate_relevance(self, chat: Dict[str, Any]) -> int:
        """Calculate chat relevance score"""
        score = 0
        
        # Participant count scoring
        participants = chat.get("participants_count", 0) or 0
        if participants > 1000:
            score += 5
        elif participants > 100:
            score += 3
        elif participants > 10:
            score += 1
        
        # Public chat bonus
        if chat.get("is_public"):
            score += 2
        
        # Verified bonus
        if chat.get("is_verified"):
            score += 3
        
        # Type priority
        type_scores = {"channel": 3, "supergroup": 2, "group": 1}
        score += type_scores.get(chat.get("type", ""), 0)
        
        return score
    
    async def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de la database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM discovered_chats")
                total_chats = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT type, COUNT(*) FROM discovered_chats GROUP BY type")
                type_counts = dict(cursor.fetchall())
                
                cursor = conn.execute("SELECT AVG(participants_count) FROM discovered_chats WHERE participants_count > 0")
                avg_participants = cursor.fetchone()[0] or 0
                
                return {
                    "total_chats": total_chats,
                    "type_distribution": type_counts,
                    "avg_participants": round(avg_participants, 2),
                    "db_size_mb": round(self.db_path.stat().st_size / (1024 * 1024), 2)
                }
        except Exception as e:
            logger.error(f"❌ Error getting stats: {e}")
            return {"total_chats": 0, "type_distribution": {}, "avg_participants": 0}

# ============= TELEGRAM SCANNER =============

class TelegramScanner:
    """Enhanced Telegram chat scanner"""
    
    def __init__(self):
        self.client = None
        self.is_scanning = False
        self.scan_progress = {"percent": 0, "current": 0, "total": 0}
        self.stats = {
            "total_scans": 0,
            "successful_scans": 0,
            "chats_discovered": 0,
            "last_scan": None,
            "scan_duration": 0
        }
        self.config_valid = False
        self.config_errors = []
    
    async def initialize(self) -> bool:
        """Inicializar cliente de Telegram"""
        if not TELETHON_AVAILABLE:
            self.config_errors.append("Telethon not available - using simulated data")
            logger.warning("⚠️ Telethon not available - using simulated data")
            return True  # ✅ DEVELOPMENT MODE: Allow simulated data
        
        try:
            # Get configuration
            api_id = os.getenv('TELEGRAM_API_ID')
            api_hash = os.getenv('TELEGRAM_API_HASH')
            phone = os.getenv('TELEGRAM_PHONE')
            
            if not api_id or not api_hash or not phone:
                self.config_errors.append("Missing Telegram configuration")
                logger.warning("⚠️ Telegram config missing - using simulated data")
                return True  # ✅ DEVELOPMENT MODE
            
            # Create client
            logger.info("📱 Creating Telegram client...")
            self.client = TelegramClient('discovery_session', int(api_id), api_hash)
            
            # Connect
            logger.info("🔄 Connecting to Telegram...")
            await self.client.start(phone=phone)
            
            # Verify connection
            me = await self.client.get_me()
            logger.info(f"✅ Connected to Telegram as: {me.first_name} (@{me.username or 'no_username'})")
            
            self.config_valid = True
            return True
            
        except Exception as e:
            error_msg = f"Error connecting to Telegram: {e}"
            self.config_errors.append(error_msg)
            logger.error(f"❌ {error_msg}")
            return True  # ✅ DEVELOPMENT MODE: Continue with simulated data
    
    async def scan_chats(self, database: DiscoveryDatabase, 
                        max_chats: int = 1000, 
                        include_private: bool = False) -> Dict[str, Any]:
        """Scan Telegram chats - with simulation fallback"""
        if self.is_scanning:
            return {"error": "Scan already in progress"}
        
        self.is_scanning = True
        scan_start = datetime.now()
        discovered_count = 0
        
        try:
            self.stats["total_scans"] += 1
            logger.info(f"🔍 Starting chat scan (max: {max_chats}, include_private: {include_private})")
            
            if self.client and TELETHON_AVAILABLE:
                # ✅ REAL TELEGRAM SCAN
                discovered_count = await self._scan_real_telegram(database, max_chats, include_private)
            else:
                # ✅ SIMULATED DATA FOR DEVELOPMENT
                discovered_count = await self._scan_simulated_data(database, max_chats)
            
            # Update stats
            scan_duration = (datetime.now() - scan_start).total_seconds()
            self.stats.update({
                "successful_scans": self.stats["successful_scans"] + 1,
                "chats_discovered": self.stats["chats_discovered"] + discovered_count,
                "last_scan": datetime.now().isoformat(),
                "scan_duration": scan_duration
            })
            
            logger.info(f"✅ Scan completed: {discovered_count} chats discovered in {scan_duration:.2f}s")
            
            return {
                "success": True,
                "chats_discovered": discovered_count,
                "scan_duration": scan_duration,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Scan error: {e}")
            return {"error": str(e)}
        finally:
            self.is_scanning = False
            self.scan_progress = {"percent": 100, "current": 0, "total": 0}
    
    async def _scan_real_telegram(self, database: DiscoveryDatabase, max_chats: int, include_private: bool) -> int:
        """Real Telegram scanning logic"""
        discovered_count = 0
        
        try:
            # Get dialogs
            dialogs = await self.client.get_dialogs(limit=max_chats)
            logger.info(f"📡 Retrieved {len(dialogs)} dialogs from Telegram")
            
            total_dialogs = len(dialogs)
            
            for i, dialog in enumerate(dialogs):
                # Update progress
                self.scan_progress = {
                    "percent": (i / total_dialogs) * 100,
                    "current": i + 1,
                    "total": total_dialogs
                }
                
                try:
                    entity = dialog.entity
                    chat_data = self._extract_chat_data(entity)
                    
                    if chat_data:
                        # Filter logic
                        if not include_private and chat_data.get("type") == "private":
                            continue
                        
                        # ✅ ENTERPRISE FILTER: Only relevant chats
                        if self._is_relevant_chat(chat_data):
                            saved = await database.save_chat(chat_data)
                            if saved:
                                discovered_count += 1
                                logger.debug(f"💾 Saved: {chat_data['title']} ({chat_data['type']})")
                    
                    # Rate limiting
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.warning(f"⚠️ Error processing dialog {i}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"❌ Real scan error: {e}")
            raise
        
        return discovered_count
    
    async def _scan_simulated_data(self, database: DiscoveryDatabase, max_chats: int) -> int:
        """✅ DEVELOPMENT MODE: Generate simulated chat data"""
        logger.info("🎭 Using simulated chat data for development")
        
        simulated_chats = [
            {
                "id": -1001234567890,
                "title": "Tech News Channel",
                "type": "channel",
                "username": "technews",
                "description": "Latest technology news and updates",
                "participants_count": 15420,
                "is_public": True,
                "is_verified": True
            },
            {
                "id": -1001234567891,
                "title": "Development Community",
                "type": "supergroup",
                "username": "devcomm",
                "description": "Community for developers",
                "participants_count": 8750,
                "is_public": True,
                "is_verified": False
            },
            {
                "id": -1001234567892,
                "title": "Crypto Signals",
                "type": "channel",
                "username": "cryptosignals",
                "description": "Cryptocurrency trading signals",
                "participants_count": 25680,
                "is_public": True,
                "is_verified": True
            },
            {
                "id": -1001234567893,
                "title": "Local Group Chat",
                "type": "group",
                "username": None,
                "description": "Local community group",
                "participants_count": 127,
                "is_public": False,
                "is_verified": False
            },
            {
                "id": -1001234567894,
                "title": "Gaming Megagroup",
                "type": "supergroup",
                "username": "gaming_mega",
                "description": "Gaming community and discussions",
                "participants_count": 45230,
                "is_public": True,
                "is_verified": False
            },
            {
                "id": -1001234567895,
                "title": "News & Updates",
                "type": "channel",
                "username": "newsupdates",
                "description": "Daily news and current events",
                "participants_count": 67890,
                "is_public": True,
                "is_verified": True
            }
        ]
        
        discovered_count = 0
        total_chats = min(len(simulated_chats), max_chats)
        
        for i, chat_data in enumerate(simulated_chats[:max_chats]):
            # Update progress
            self.scan_progress = {
                "percent": ((i + 1) / total_chats) * 100,
                "current": i + 1,
                "total": total_chats
            }
            
            # Add timestamp
            chat_data["discovered_at"] = datetime.now().isoformat()
            
            # Save to database
            saved = await database.save_chat(chat_data)
            if saved:
                discovered_count += 1
            
            # Simulate processing delay
            await asyncio.sleep(0.05)
        
        return discovered_count
    
    def _extract_chat_data(self, entity) -> Optional[Dict[str, Any]]:
        """Extract chat data from Telegram entity"""
        try:
            chat_data = {
                "id": entity.id,
                "discovered_at": datetime.now().isoformat()
            }
            
            if isinstance(entity, User):
                chat_data.update({
                    "title": f"{entity.first_name or ''} {entity.last_name or ''}".strip() or "Unknown User",
                    "type": "private",
                    "username": entity.username,
                    "description": None,
                    "participants_count": None,
                    "is_public": False,
                    "is_verified": getattr(entity, 'verified', False)
                })
                
            elif isinstance(entity, Chat):
                chat_data.update({
                    "title": entity.title,
                    "type": "group",
                    "username": None,
                    "description": None,
                    "participants_count": getattr(entity, 'participants_count', None),
                    "is_public": False,
                    "is_verified": False
                })
                
            elif isinstance(entity, Channel):
                chat_data.update({
                    "title": entity.title,
                    "type": "supergroup" if entity.megagroup else "channel",
                    "username": entity.username,
                    "description": getattr(entity, 'about', None),
                    "participants_count": getattr(entity, 'participants_count', None),
                    "is_public": entity.username is not None,
                    "is_verified": getattr(entity, 'verified', False)
                })
            
            return chat_data
            
        except Exception as e:
            logger.error(f"❌ Error extracting chat data: {e}")
            return None
    
    def _is_relevant_chat(self, chat_data: Dict[str, Any]) -> bool:
        """Determine if chat is relevant for discovery"""
        # Skip private chats by default
        if chat_data.get("type") == "private":
            return False
        
        # Skip very small groups
        participants = chat_data.get("participants_count", 0) or 0
        if participants <= 1:
            return False
        
        # Skip suspicious titles
        title = chat_data.get("title", "").lower()
        if any(suspicious in title for suspicious in ["spam", "fake", "bot", "test123"]):
            return False
        
        return True
    
    def get_scan_status(self) -> Dict[str, Any]:
        """Get current scan status"""
        return {
            "is_scanning": self.is_scanning,
            "progress": self.scan_progress,
            "stats": self.stats,
            "config_valid": self.config_valid,
            "config_errors": self.config_errors
        }

# ============= FASTAPI APPLICATION =============

# Global instances
database = DiscoveryDatabase()
scanner = TelegramScanner()
websocket_connections: List[WebSocket] = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle"""
    try:
        logger.info("🔍 Starting Discovery Service v4.0...")
        
        # Initialize scanner
        scanner_ready = await scanner.initialize()
        
        # Auto-scan on startup if possible
        if scanner_ready and scanner.config_valid:
            logger.info("🚀 Running initial discovery scan...")
            asyncio.create_task(scanner.scan_chats(database, max_chats=100))
        
        # Info
        print("\n" + "="*70)
        print("🔍 DISCOVERY SERVICE v4.0 - ENTERPRISE READY")
        print("="*70)
        print("🌐 Endpoints:")
        print("   📊 Dashboard:     http://localhost:8002/")
        print("   🔍 Scan:          POST /api/discovery/scan")
        print("   📋 Chats:         GET /api/discovery/chats")
        print("   🏥 Health:        GET /health")
        print("   📚 API Docs:      GET /docs")
        print("   🔌 WebSocket:     ws://localhost:8002/ws")
        print(f"\n📊 Scanner Status:")
        print(f"   Config Valid:     {'✅' if scanner.config_valid else '❌'}")
        print(f"   Telethon:         {'✅' if TELETHON_AVAILABLE else '❌ (simulated data)'}")
        print(f"   Database:         ✅ SQLite ready")
        if scanner.config_errors:
            print("⚠️ Config Issues:")
            for error in scanner.config_errors:
                print(f"   - {error}")
        print("="*70)
        
        yield
        
    finally:
        if scanner.client:
            await scanner.client.disconnect()
        logger.info("🛑 Discovery Service stopped")

# Create FastAPI app
app = FastAPI(
    title="🔍 Discovery Service v4.0",
    description="Enterprise Telegram Chat Discovery System",
    version="4.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============= API ENDPOINTS =============

@app.get("/")
async def root():
    """Service information"""
    return {
        "service": "discovery",
        "version": "4.0.0",
        "status": "running",
        "scanner_ready": scanner.config_valid,
        "telethon_available": TELETHON_AVAILABLE,
        "endpoints": {
            "health": "/health",
            "scan": "/api/discovery/scan",
            "chats": "/api/discovery/chats",
            "status": "/status",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_stats = await database.get_stats()
    
    return {
        "status": "healthy",
        "service": "discovery",
        "version": "4.0.0",
        "timestamp": datetime.now().isoformat(),
        "scanner": {
            "ready": scanner.config_valid,
            "scanning": scanner.is_scanning,
            "telethon_available": TELETHON_AVAILABLE
        },
        "database": {
            "total_chats": db_stats.get("total_chats", 0),
            "size_mb": db_stats.get("db_size_mb", 0)
        }
    }

@app.get("/status")
async def get_full_status():
    """Complete service status"""
    scan_status = scanner.get_scan_status()
    db_stats = await database.get_stats()
    
    return {
        "service": "discovery",
        "version": "4.0.0",
        "scanner_status": scan_status,
        "database_stats": db_stats,
        "current_scan": scan_status["progress"],
        "scanner_stats": scan_status["stats"],
        "websocket_connections": len(websocket_connections)
    }

@app.post("/api/discovery/scan")
async def trigger_scan(request: ScanRequest):
    """Trigger discovery scan"""
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
    chat_type: Optional[str] = Query(None, description="Filter by type (group,supergroup,channel)"),
    search_term: Optional[str] = Query(None, description="Search term"),
    min_participants: Optional[int] = Query(None, description="Minimum participants"),
    limit: int = Query(100, description="Limit results"),
    offset: int = Query(0, description="Offset results"),
    is_private: Optional[bool] = Query(False, description="Include private chats")
):
    """✅ FIXED: Get discovered chats with intelligent filtering"""
    try:
        chats = await database.get_chats(
            chat_type=chat_type,
            search_term=search_term,
            min_participants=min_participants,
            limit=limit,
            offset=offset,
            is_private=is_private
        )
        
        return {
            "chats": chats,
            "total": len(chats),
            "limit": limit,
            "offset": offset,
            "filters": {
                "chat_type": chat_type,
                "search_term": search_term,
                "min_participants": min_participants,
                "is_private": is_private
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting chats: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving chats: {str(e)}")

@app.get("/api/discovery/chats/{chat_id}")
async def get_chat_details(chat_id: int):
    """Get detailed information about a specific chat"""
    try:
        chats = await database.get_chats(limit=1, offset=0)
        chat = next((c for c in chats if c["id"] == chat_id), None)
        
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        
        return {"chat": chat}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting chat {chat_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving chat: {str(e)}")

@app.get("/api/discovery/stats")
async def get_discovery_stats():
    """Get discovery statistics"""
    try:
        db_stats = await database.get_stats()
        scan_stats = scanner.get_scan_status()
        
        return {
            "database": db_stats,
            "scanner": scan_stats,
            "service_info": {
                "version": "4.0.0",
                "telethon_available": TELETHON_AVAILABLE,
                "config_valid": scanner.config_valid
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving stats: {str(e)}")

# ============= WEBSOCKET ENDPOINTS =============

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await websocket.accept()
    websocket_connections.append(websocket)
    
    try:
        # Send initial status
        status = await get_full_status()
        await websocket.send_json({
            "type": "initial_status",
            "data": status
        })
        
        # Keep connection alive and send updates
        while True:
            try:
                # Wait for client messages or send periodic updates
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                elif message.get("type") == "request_status":
                    status = await get_full_status()
                    await websocket.send_json({
                        "type": "status_update",
                        "data": status
                    })
                    
            except asyncio.TimeoutError:
                # Send periodic status update
                if scanner.is_scanning:
                    scan_status = scanner.get_scan_status()
                    await websocket.send_json({
                        "type": "scan_progress",
                        "data": scan_status["progress"]
                    })
                else:
                    await websocket.send_json({"type": "heartbeat"})
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
    finally:
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)

# ============= BROADCAST FUNCTIONS =============

async def broadcast_scan_update(scan_data: Dict[str, Any]):
    """Broadcast scan updates to all connected clients"""
    if not websocket_connections:
        return
    
    message = {
        "type": "scan_update",
        "data": scan_data,
        "timestamp": datetime.now().isoformat()
    }
    
    disconnected = []
    for websocket in websocket_connections:
        try:
            await websocket.send_json(message)
        except Exception:
            disconnected.append(websocket)
    
    # Remove disconnected clients
    for ws in disconnected:
        websocket_connections.remove(ws)

async def broadcast_new_chat(chat_data: Dict[str, Any]):
    """Broadcast new chat discovery to all clients"""
    if not websocket_connections:
        return
    
    message = {
        "type": "new_chat_discovered",
        "data": chat_data,
        "timestamp": datetime.now().isoformat()
    }
    
    disconnected = []
    for websocket in websocket_connections:
        try:
            await websocket.send_json(message)
        except Exception:
            disconnected.append(websocket)
    
    # Remove disconnected clients
    for ws in disconnected:
        websocket_connections.remove(ws)

# ============= DASHBOARD UI =============

@app.get("/dashboard", response_class=HTMLResponse)
async def discovery_dashboard():
    """Simple discovery dashboard"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>🔍 Discovery Service Dashboard</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                margin: 0;
                padding: 20px;
                min-height: 100vh;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            .header {
                text-align: center;
                margin-bottom: 40px;
            }
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 40px;
            }
            .stat-card {
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border-radius: 15px;
                padding: 20px;
                text-align: center;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            .stat-value {
                font-size: 2.5rem;
                font-weight: bold;
                margin-bottom: 10px;
            }
            .stat-label {
                font-size: 1rem;
                opacity: 0.8;
            }
            .actions {
                display: flex;
                gap: 15px;
                justify-content: center;
                margin-bottom: 30px;
                flex-wrap: wrap;
            }
            .btn {
                background: rgba(255, 255, 255, 0.2);
                border: none;
                padding: 12px 24px;
                border-radius: 10px;
                color: white;
                cursor: pointer;
                font-size: 1rem;
                transition: all 0.3s;
                backdrop-filter: blur(5px);
            }
            .btn:hover {
                background: rgba(255, 255, 255, 0.3);
                transform: translateY(-2px);
            }
            .btn.primary {
                background: rgba(16, 185, 129, 0.8);
            }
            .chats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                gap: 20px;
            }
            .chat-card {
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border-radius: 12px;
                padding: 15px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            .chat-title {
                font-weight: bold;
                margin-bottom: 8px;
                font-size: 1.1rem;
            }
            .chat-meta {
                font-size: 0.9rem;
                opacity: 0.8;
                display: flex;
                justify-content: space-between;
                margin-bottom: 10px;
            }
            .chat-type {
                background: rgba(59, 130, 246, 0.8);
                padding: 2px 8px;
                border-radius: 12px;
                font-size: 0.8rem;
            }
            .loading {
                text-align: center;
                padding: 40px;
            }
            .spinner {
                border: 3px solid rgba(255, 255, 255, 0.3);
                border-top: 3px solid white;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto 20px;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            .status {
                background: rgba(0, 0, 0, 0.2);
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 20px;
                font-family: monospace;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔍 Discovery Service Dashboard</h1>
                <p>Enterprise Telegram Chat Discovery System v4.0</p>
            </div>
            
            <div class="status" id="status">
                📡 Connecting to Discovery Service...
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value" id="total-chats">0</div>
                    <div class="stat-label">Total Chats</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="scan-count">0</div>
                    <div class="stat-label">Scans Completed</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="last-scan">Never</div>
                    <div class="stat-label">Last Scan</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="scanner-status">🔄</div>
                    <div class="stat-label">Scanner Status</div>
                </div>
            </div>
            
            <div class="actions">
                <button class="btn primary" onclick="startScan()">🔍 Start Discovery Scan</button>
                <button class="btn" onclick="refreshData()">🔄 Refresh Data</button>
                <button class="btn" onclick="viewAPI()">📚 View API Docs</button>
            </div>
            
            <div id="chats-container">
                <div class="loading">
                    <div class="spinner"></div>
                    <p>Loading discovered chats...</p>
                </div>
            </div>
        </div>
        
        <script>
            let ws = null;
            
            function connectWebSocket() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
                
                ws.onopen = () => {
                    document.getElementById('status').textContent = '✅ Connected to Discovery Service';
                };
                
                ws.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    handleWebSocketMessage(data);
                };
                
                ws.onclose = () => {
                    document.getElementById('status').textContent = '❌ Disconnected - Reconnecting...';
                    setTimeout(connectWebSocket, 5000);
                };
                
                ws.onerror = (error) => {
                    document.getElementById('status').textContent = '❌ Connection Error';
                };
            }
            
            function handleWebSocketMessage(data) {
                switch(data.type) {
                    case 'initial_status':
                    case 'status_update':
                        updateStats(data.data);
                        break;
                    case 'scan_progress':
                        updateScanProgress(data.data);
                        break;
                    case 'new_chat_discovered':
                        addNewChat(data.data);
                        break;
                }
            }
            
            function updateStats(data) {
                const dbStats = data.database_stats || {};
                const scannerStats = data.scanner_status?.stats || {};
                
                document.getElementById('total-chats').textContent = dbStats.total_chats || 0;
                document.getElementById('scan-count').textContent = scannerStats.successful_scans || 0;
                document.getElementById('last-scan').textContent = 
                    scannerStats.last_scan ? new Date(scannerStats.last_scan).toLocaleTimeString() : 'Never';
                
                const scannerStatus = data.scanner_status?.is_scanning ? '🔄 Scanning' : '✅ Ready';
                document.getElementById('scanner-status').textContent = scannerStatus;
            }
            
            function updateScanProgress(progress) {
                const percent = Math.round(progress.percent || 0);
                document.getElementById('status').textContent = 
                    `🔍 Scanning... ${percent}% (${progress.current || 0}/${progress.total || 0})`;
            }
            
            async function loadChats() {
                try {
                    const response = await fetch('/api/discovery/chats?limit=50');
                    const data = await response.json();
                    
                    const container = document.getElementById('chats-container');
                    
                    if (data.chats && data.chats.length > 0) {
                        container.innerHTML = '<div class="chats-grid">' + 
                            data.chats.map(chat => createChatCard(chat)).join('') + 
                            '</div>';
                    } else {
                        container.innerHTML = '<div class="loading"><p>No chats discovered yet. Try running a scan!</p></div>';
                    }
                } catch (error) {
                    console.error('Error loading chats:', error);
                    document.getElementById('chats-container').innerHTML = 
                        '<div class="loading"><p>❌ Error loading chats</p></div>';
                }
            }
            
            function createChatCard(chat) {
                const typeClass = chat.type === 'channel' ? 'channel' : 'group';
                const participants = chat.participants_count ? 
                    `${chat.participants_count.toLocaleString()} members` : 'Unknown size';
                
                return `
                    <div class="chat-card">
                        <div class="chat-title">${chat.title || 'Unknown'}</div>
                        <div class="chat-meta">
                            <span class="chat-type ${typeClass}">${chat.type}</span>
                            <span>${participants}</span>
                        </div>
                        ${chat.username ? `<div>@${chat.username}</div>` : ''}
                        ${chat.description ? `<div style="opacity: 0.7; font-size: 0.9rem; margin-top: 8px;">${chat.description.substring(0, 100)}...</div>` : ''}
                    </div>
                `;
            }
            
            async function startScan() {
                try {
                    document.getElementById('status').textContent = '🚀 Starting discovery scan...';
                    
                    const response = await fetch('/api/discovery/scan', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ force_refresh: true, max_chats: 500 })
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        document.getElementById('status').textContent = '✅ Scan started successfully';
                    } else {
                        document.getElementById('status').textContent = '❌ Scan failed to start';
                    }
                } catch (error) {
                    console.error('Error starting scan:', error);
                    document.getElementById('status').textContent = '❌ Error starting scan';
                }
            }
            
            async function refreshData() {
                document.getElementById('status').textContent = '🔄 Refreshing data...';
                await loadChats();
                
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({ type: 'request_status' }));
                }
                
                document.getElementById('status').textContent = '✅ Data refreshed';
            }
            
            function viewAPI() {
                window.open('/docs', '_blank');
            }
            
            // Initialize
            document.addEventListener('DOMContentLoaded', () => {
                connectWebSocket();
                loadChats();
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# ============= MAIN EXECUTION =============

if __name__ == "__main__":
    # Ensure data directory exists
    Path("data").mkdir(exist_ok=True)
    
    # Run the service
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=False,
        log_level="info"
    )