"""
Message Replicator Microservice
================================
Servicio independiente para replicación de mensajes
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.utils.logger import setup_logger

logger = setup_logger(__name__)

app = FastAPI(
    title="Message Replicator Service",
    version="1.0.0"
)

@app.get("/")
async def root():
    return JSONResponse({
        "service": "Message Replicator",
        "status": "running",
        "version": "1.0.0"
    })

@app.get("/health")
async def health():
    return JSONResponse({
        "status": "healthy",
        "service": "message_replicator"
    })

if __name__ == "__main__":
    logger.info("Starting Message Replicator Service on port 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001)
