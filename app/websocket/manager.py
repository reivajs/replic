"""WebSocket Manager"""
from typing import Dict, Set
from fastapi import WebSocket
import json
import logging

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        
    async def connect(self, websocket: WebSocket, client_id: str = None):
        """Connect a client"""
        await websocket.accept()
        if client_id is None:
            client_id = str(id(websocket))
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected")
        
    def disconnect(self, websocket: WebSocket):
        """Disconnect a client"""
        for cid, ws in list(self.active_connections.items()):
            if ws == websocket:
                del self.active_connections[cid]
                logger.info(f"Client {cid} disconnected")
                break
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send message to specific client"""
        await websocket.send_text(message)
    
    async def broadcast(self, message: str):
        """Broadcast to all clients"""
        for connection in self.active_connections.values():
            await connection.send_text(message)
    
    async def disconnect_all(self):
        """Disconnect all clients"""
        for websocket in self.active_connections.values():
            await websocket.close()
        self.active_connections.clear()
