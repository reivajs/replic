"""WebSocket Router"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint"""
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Echo back for now
            await websocket.send_json({
                "type": "echo",
                "data": message
            })
            
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
