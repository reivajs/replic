"""WebSocket Manager Enhanced"""
import asyncio
from typing import Dict, Optional
from fastapi import WebSocket
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class EnhancedWebSocketManager:
    """WebSocket manager mejorado"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.connections = {}
        self.max_connections = 100
        self.connection_count = 0
        self._initialized = True
        
        logger.info("WebSocket Manager initialized")
    
    async def connect(self, websocket: WebSocket, client_id: Optional[str] = None):
        """Conectar cliente"""
        if self.connection_count >= self.max_connections:
            await websocket.close(code=1008, reason="Max connections")
            return None
        
        await websocket.accept()
        
        if client_id is None:
            client_id = f"client_{id(websocket)}"
        
        self.connections[client_id] = websocket
        self.connection_count += 1
        
        logger.info(f"Client {client_id} connected (total: {self.connection_count})")
        return client_id
    
    async def disconnect(self, client_id: str):
        """Desconectar cliente"""
        if client_id in self.connections:
            del self.connections[client_id]
            self.connection_count -= 1
            logger.info(f"Client {client_id} disconnected (remaining: {self.connection_count})")
    
    async def send_to_client(self, client_id: str, data: dict):
        """Enviar a cliente"""
        if client_id not in self.connections:
            return False
        
        try:
            from app.utils.json_encoder import CustomJSONEncoder
            message = json.dumps(data, cls=CustomJSONEncoder)
            await self.connections[client_id].send_text(message)
            return True
        except Exception as e:
            logger.error(f"Send error: {e}")
            await self.disconnect(client_id)
            return False

websocket_manager = EnhancedWebSocketManager()
