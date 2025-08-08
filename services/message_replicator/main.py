import asyncio
import sys
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from app.services.enhanced_replicator_service import EnhancedReplicatorService
    from app.config.settings import get_settings
    ORIGINAL_AVAILABLE = True
except ImportError:
    from shared.config.settings import get_settings
    ORIGINAL_AVAILABLE = False

from shared.utils.logger import setup_logger

logger = setup_logger(__name__, "message-replicator")
settings = get_settings()
replicator_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global replicator_service
    logger.info("🚀 Iniciando Message Replicator Microservice...")
    
    try:
        if ORIGINAL_AVAILABLE:
            replicator_service = EnhancedReplicatorService()
            success = await replicator_service.initialize()
            if success:
                asyncio.create_task(replicator_service.start_listening())
                logger.info("✅ Enhanced Replicator inicializado")
        yield
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        if replicator_service:
            await replicator_service.stop()

app = FastAPI(title="Message Replicator Microservice", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/")
async def root():
    return {"service": "Message Replicator", "version": "3.0.0", "original_available": ORIGINAL_AVAILABLE}

@app.get("/health")
async def health():
    try:
        if not replicator_service:
            return {"status": "unhealthy", "reason": "Service not initialized"}
        
        if hasattr(replicator_service, 'get_health'):
            health_data = await replicator_service.get_health()
        else:
            health_data = {"status": "healthy"}
        
        health_data["microservice"] = "message-replicator"
        return health_data
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

if __name__ == "__main__":
    print("🚀 Starting Message Replicator on port 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)