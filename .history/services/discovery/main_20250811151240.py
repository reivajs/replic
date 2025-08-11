# 🔍 Discovery Service Enterprise - services/discovery/main.py

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, asdict
import sqlite3
import json
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from telethon import TelegramClient
from telethon.tl.types import Chat, Channel, User
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError

# ============= CONFIGURACIÓN =============

@dataclass
class ChatInfo:
    """Información de chat descubierto"""
    id: int
    title: str
    username: Optional[str] = None
    type: str = "unknown"
    participants_count: int = 0
    description: Optional[str] = None
    is_broadcast: bool = False
    is_megagroup: bool = False
    is_group: bool = False
    is_channel: bool = False
    access_hash: Optional[int] = None
    discovered_at: datetime = None
    last_activity: Optional[datetime] = None
    is_active: bool = True
    
    def __post_init__(self):
        if self.discovered_at is None:
            self.discovered_at = datetime.now()

class TelegramDiscoveryService:
    """🔍 Servicio de descubrimiento de chats de Telegram"""
    
    def __init__(self, api_id: str, api_hash: str, phone: str):
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = phone
        self.client = None
        self.db_path = "data/discovery.db"
        self.discovered_chats: Dict[int, ChatInfo] = {}
        self.websocket_connections: Set[WebSocket] = set()
        self.is_scanning = False
        self.last_scan_time = None
        
        # Crear directorio de datos
        Path("data").mkdir(exist_ok=True)
        self._init_database()
        
    def _init_database(self):
        """Inicializar base de datos SQLite"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS discovered_chats (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                username TEXT,
                type TEXT,
                participants_count INTEGER DEFAULT 0,
                description TEXT,
                is_broadcast BOOLEAN DEFAULT FALSE,
                is_megagroup BOOLEAN DEFAULT FALSE,
                is_group BOOLEAN DEFAULT FALSE,
                is_channel BOOLEAN DEFAULT FALSE,
                access_hash INTEGER,
                discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                metadata TEXT
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_chat_id ON discovered_chats(id);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_chat_type ON discovered_chats(type);
        """)
        
        conn.commit()
        conn.close()
        
    async def initialize_telegram(self):
        """Inicializar cliente de Telegram"""
        try:
            self.client = TelegramClient('discovery_session', self.api_id, self.api_hash)
            await self.client.start(phone=self.phone)
            
            if not await self.client.is_user_authorized():
                raise Exception("Usuario no autorizado en Telegram")
                
            logging.info("🔍 Telegram Discovery Service inicializado")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error inicializando Telegram: {e}")
            return False
    
    async def discover_chats(self, force_refresh: bool = False) -> List[ChatInfo]:
        """🔍 Descubrir todos los chats disponibles"""
        if self.is_scanning and not force_refresh:
            logging.info("⏳ Escaneo ya en progreso...")
            return list(self.discovered_chats.values())
            
        self.is_scanning = True
        discovered_count = 0
        
        try:
            logging.info("🔍 Iniciando discovery de chats...")
            
            # Obtener todos los diálogos
            async for dialog in self.client.iter_dialogs():
                try:
                    chat_info = await self._process_dialog(dialog)
                    if chat_info:
                        self.discovered_chats[chat_info.id] = chat_info
                        await self._save_chat_to_db(chat_info)
                        discovered_count += 1
                        
                        # Notificar via WebSocket
                        await self._broadcast_chat_discovered(chat_info)
                        
                        # Rate limiting
                        await asyncio.sleep(0.1)
                        
                except Exception as e:
                    logging.error(f"❌ Error procesando dialog: {e}")
                    continue
            
            self.last_scan_time = datetime.now()
            logging.info(f"✅ Discovery completado: {discovered_count} chats encontrados")
            
            # Notificar completion
            await self._broadcast_discovery_complete(discovered_count)
            
        except Exception as e:
            logging.error(f"❌ Error en discovery: {e}")
            await self._broadcast_discovery_error(str(e))
            
        finally:
            self.is_scanning = False
            
        return list(self.discovered_chats.values())
    
    async def _process_dialog(self, dialog) -> Optional[ChatInfo]:
        """Procesar un diálogo individual"""
        try:
            entity = dialog.entity
            chat_info = None
            
            if isinstance(entity, Chat):
                # Grupo normal
                chat_info = ChatInfo(
                    id=entity.id,
                    title=entity.title,
                    type="group",
                    participants_count=getattr(entity, 'participants_count', 0),
                    is_group=True,
                    access_hash=getattr(entity, 'access_hash', None)
                )
                
            elif isinstance(entity, Channel):
                # Canal o supergrupo
                chat_info = ChatInfo(
                    id=entity.id,
                    title=entity.title,
                    username=getattr(entity, 'username', None),
                    type="channel" if entity.broadcast else "supergroup",
                    participants_count=getattr(entity, 'participants_count', 0),
                    is_broadcast=entity.broadcast,
                    is_megagroup=entity.megagroup,
                    is_channel=entity.broadcast,
                    access_hash=entity.access_hash
                )
                
            elif isinstance(entity, User):
                # Chat privado (opcional)
                if not entity.bot:  # Excluir bots
                    chat_info = ChatInfo(
                        id=entity.id,
                        title=f"{entity.first_name or ''} {entity.last_name or ''}".strip(),
                        username=getattr(entity, 'username', None),
                        type="private",
                        participants_count=2,
                        access_hash=getattr(entity, 'access_hash', None)
                    )
            
            return chat_info
            
        except Exception as e:
            logging.error(f"❌ Error procesando entity: {e}")
            return None
    
    async def _save_chat_to_db(self, chat_info: ChatInfo):
        """Guardar chat en base de datos"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO discovered_chats 
                (id, title, username, type, participants_count, description,
                 is_broadcast, is_megagroup, is_group, is_channel, access_hash,
                 discovered_at, last_activity, is_active, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                chat_info.id,
                chat_info.title,
                chat_info.username,
                chat_info.type,
                chat_info.participants_count,
                chat_info.description,
                chat_info.is_broadcast,
                chat_info.is_megagroup,
                chat_info.is_group,
                chat_info.is_channel,
                chat_info.access_hash,
                chat_info.discovered_at.isoformat(),
                chat_info.last_activity.isoformat() if chat_info.last_activity else None,
                chat_info.is_active,
                json.dumps(asdict(chat_info))
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logging.error(f"❌ Error guardando chat en DB: {e}")
    
    async def get_chat_preview(self, chat_id: int) -> Dict:
        """🔍 Obtener preview de un chat específico"""
        try:
            if not self.client:
                raise Exception("Cliente Telegram no inicializado")
                
            # Obtener información del chat
            entity = await self.client.get_entity(chat_id)
            
            # Obtener mensajes recientes
            messages = []
            async for message in self.client.iter_messages(entity, limit=3):
                if message.text:
                    messages.append({
                        "text": message.text[:100] + "..." if len(message.text) > 100 else message.text,
                        "date": message.date.isoformat(),
                        "sender": getattr(message.sender, 'first_name', 'Unknown') if message.sender else 'Unknown'
                    })
            
            return {
                "chat_id": chat_id,
                "title": entity.title if hasattr(entity, 'title') else str(entity.id),
                "recent_messages": messages,
                "members_count": getattr(entity, 'participants_count', 0),
                "type": entity.__class__.__name__.lower()
            }
            
        except Exception as e:
            logging.error(f"❌ Error getting chat preview: {e}")
            return {"error": str(e)}
    
    async def _broadcast_chat_discovered(self, chat_info: ChatInfo):
        """Broadcast nuevo chat descubierto via WebSocket"""
        message = {
            "type": "chat_discovered",
            "data": asdict(chat_info)
        }
        await self._broadcast_websocket(message)
    
    async def _broadcast_discovery_complete(self, count: int):
        """Broadcast discovery completado"""
        message = {
            "type": "discovery_complete",
            "data": {
                "total_discovered": count,
                "timestamp": datetime.now().isoformat()
            }
        }
        await self._broadcast_websocket(message)
    
    async def _broadcast_discovery_error(self, error: str):
        """Broadcast error en discovery"""
        message = {
            "type": "discovery_error",
            "data": {"error": error}
        }
        await self._broadcast_websocket(message)
    
    async def _broadcast_websocket(self, message: Dict):
        """Enviar mensaje a todos los WebSockets conectados"""
        if not self.websocket_connections:
            return
            
        disconnected = set()
        for websocket in self.websocket_connections:
            try:
                await websocket.send_text(json.dumps(message))
            except:
                disconnected.add(websocket)
        
        # Limpiar conexiones desconectadas
        self.websocket_connections -= disconnected

# ============= FASTAPI APP =============

app = FastAPI(title="🔍 Discovery Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global service instance
discovery_service: Optional[TelegramDiscoveryService] = None

@app.on_event("startup")
async def startup_event():
    """Inicializar el servicio al arrancar"""
    global discovery_service
    
    # Obtener configuración (ajustar según tu estructura)
    import os
    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")
    phone = os.getenv("TELEGRAM_PHONE")
    
    if not all([api_id, api_hash, phone]):
        logging.error("❌ Faltan credenciales de Telegram")
        return
    
    discovery_service = TelegramDiscoveryService(api_id, api_hash, phone)
    await discovery_service.initialize_telegram()

# ============= API ENDPOINTS =============

@app.get("/health")
async def health_check():
    """Health check del servicio"""
    return {
        "status": "healthy",
        "service": "discovery",
        "timestamp": datetime.now().isoformat(),
        "telegram_connected": discovery_service.client is not None if discovery_service else False
    }

@app.post("/api/discovery/scan")
async def start_discovery(force_refresh: bool = False):
    """🔍 Iniciar discovery de chats"""
    if not discovery_service:
        raise HTTPException(status_code=503, detail="Servicio no inicializado")
    
    chats = await discovery_service.discover_chats(force_refresh)
    
    return {
        "status": "success",
        "message": "Discovery iniciado",
        "total_chats": len(chats),
        "is_scanning": discovery_service.is_scanning
    }

@app.get("/api/discovery/chats")
async def get_discovered_chats(
    limit: int = 50,
    offset: int = 0,
    chat_type: Optional[str] = None
):
    """📋 Obtener chats descubiertos"""
    if not discovery_service:
        raise HTTPException(status_code=503, detail="Servicio no inicializado")
    
    chats = list(discovery_service.discovered_chats.values())
    
    # Filtrar por tipo si se especifica
    if chat_type:
        chats = [c for c in chats if c.type == chat_type]
    
    # Paginación
    total = len(chats)
    chats = chats[offset:offset+limit]
    
    return {
        "chats": [asdict(chat) for chat in chats],
        "total": total,
        "limit": limit,
        "offset": offset
    }

@app.get("/api/discovery/chats/{chat_id}/preview")
async def get_chat_preview(chat_id: int):
    """🔍 Obtener preview de un chat específico"""
    if not discovery_service:
        raise HTTPException(status_code=503, detail="Servicio no inicializado")
    
    preview = await discovery_service.get_chat_preview(chat_id)
    return preview

@app.get("/api/discovery/status")
async def get_discovery_status():
    """📊 Obtener estado del discovery"""
    if not discovery_service:
        return {
            "available": False,
            "error": "Servicio no inicializado"
        }
    
    return {
        "available": True,
        "is_scanning": discovery_service.is_scanning,
        "last_scan": discovery_service.last_scan_time.isoformat() if discovery_service.last_scan_time else None,
        "total_discovered": len(discovery_service.discovered_chats),
        "telegram_connected": discovery_service.client is not None
    }

# ============= WEBSOCKET =============

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """🔗 WebSocket para updates en tiempo real"""
    if not discovery_service:
        await websocket.close(code=1011, reason="Servicio no disponible")
        return
    
    await websocket.accept()
    discovery_service.websocket_connections.add(websocket)
    
    try:
        # Enviar estado inicial
        initial_data = {
            "type": "initial_connection",
            "data": {
                "total_chats": len(discovery_service.discovered_chats),
                "is_scanning": discovery_service.is_scanning,
                "last_scan": discovery_service.last_scan_time.isoformat() if discovery_service.last_scan_time else None
            }
        }
        await websocket.send_text(json.dumps(initial_data))
        
        # Mantener conexión activa
        while True:
            await websocket.receive_text()
            
    except WebSocketDisconnect:
        discovery_service.websocket_connections.discard(websocket)
    except Exception as e:
        logging.error(f"❌ WebSocket error: {e}")
        discovery_service.websocket_connections.discard(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)