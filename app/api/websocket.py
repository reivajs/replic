"""
App API WebSocket
================
Gestor de WebSocket para comunicación en tiempo real
"""

import json
import asyncio
from typing import List, Dict, Any
from fastapi import WebSocket

class WebSocketManager:
    """Gestor de conexiones WebSocket"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Conectar nuevo cliente"""
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Desconectar cliente"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Enviar mensaje a cliente específico"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception:
            self.disconnect(websocket)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Enviar mensaje a todos los clientes conectados"""
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                disconnected.append(connection)
        
        # Remover conexiones desconectadas
        for connection in disconnected:
            self.disconnect(connection)
    
    def get_client_count(self) -> int:
        """Obtener número de clientes conectados"""
        return len(self.active_connections)