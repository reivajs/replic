#!/usr/bin/env python3
"""
📡 MESSAGE REPLICATOR MICROSERVICE v4.0
=======================================
Tu EnhancedReplicatorService como microservicio independiente
Mantiene TODA la funcionalidad original + API REST enterprise
"""

import asyncio
import sys
import os
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Añadir paths para importar tu código existente
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

try:
    # Intentar importar tu EnhancedReplicatorService existente
    from app.services.enhanced_replicator_service import EnhancedReplicatorService
    HAS_ENHANCED_REPLICATOR = True
except ImportError as e:
    print(f"⚠️ No se pudo importar EnhancedReplicatorService: {e}")
    print("📡 Funcionando en modo simulado")
    HAS_ENHANCED_REPLICATOR = False

# Logger simple
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Instancia global del servicio
replicator_service = None

class MockReplicatorService:
    """Servicio simulado para cuando no está disponible el Enhanced Replicator"""
    
    def __init__(self):
        self.is_running = True
        self.is_listening = True
        self.stats = {
            'messages_processed': 1234,
            'messages_replicated': 1100,
            'watermarks_applied': 89,
            'errors': 2,
            'start_time': datetime.now(),
            'uptime_hours': 24.5
        }
    
    async def initialize(self):
        logger.info("🎭 Mock Replicator Service inicializado")
    
    async def start_listening(self):
        logger.info("👂 Mock listening iniciado")
        # Simular trabajo
        while True:
            await asyncio.sleep(30)
            self.stats['messages_processed'] += 1
    
    async def stop(self):
        logger.info("🛑 Mock Replicator detenido")
    
    async def get_health(self):
        return {
            "status": "healthy",
            "service": "mock_replicator",
            "is_running": self.is_running,
            "is_listening": self.is_listening,
            "uptime": (datetime.now() - self.stats['start_time']).total_seconds()
        }
    
    async def get_dashboard_stats(self):
        return self.stats

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manejo del ciclo de vida del microservicio"""
    global replicator_service
    
    try:
        logger.info("🚀 Iniciando Message Replicator Microservice...")
        
        if HAS_ENHANCED_REPLICATOR:
            # Usar tu Enhanced Replicator Service real
            replicator_service = EnhancedReplicatorService()
            await replicator_service.initialize()
            
            # Iniciar listening en background
            asyncio.create_task(replicator_service.start_listening())
            logger.info("✅ Enhanced Replicator Service iniciado")
        else:
            # Usar servicio simulado
            replicator_service = MockReplicatorService()
            await replicator_service.initialize()
            
            # Iniciar mock listening en background
            asyncio.create_task(replicator_service.start_listening())
            logger.info("✅ Mock Replicator Service iniciado")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Error en Message Replicator: {e}")
        raise
    finally:
        if replicator_service:
            await replicator_service.stop()
        logger.info("🛑 Message Replicator detenido")

# Crear aplicación FastAPI
app = FastAPI(
    title="📡 Message Replicator Microservice",
    description="Tu Enhanced Replicator Service como microservicio",
    version="4.0.0",
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

@app.get("/")
async def root():
    """Información del microservicio"""
    return {
        "service": "Message Replicator Microservice",
        "version": "4.0.0",
        "description": "Enhanced Replicator Service como microservicio",
        "status": "running" if replicator_service else "initializing",
        "mode": "enhanced" if HAS_ENHANCED_REPLICATOR else "mock"
    }

@app.get("/health")
async def health_check():
    """Health check del servicio"""
    try:
        if not replicator_service:
            return {
                "status": "initializing",
                "timestamp": datetime.now().isoformat()
            }
        
        # Usar el método de health check
        health_data = await replicator_service.get_health()
        
        return {
            "status": "healthy",
            "service": "message_replicator",
            "version": "4.0.0",
            "mode": "enhanced" if HAS_ENHANCED_REPLICATOR else "mock",
            "replicator_health": health_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Health check error: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/stats")
async def get_stats():
    """Obtener estadísticas del replicador"""
    try:
        if not replicator_service:
            return {"error": "Service not initialized"}
        
        # Usar el método de stats
        stats = await replicator_service.get_dashboard_stats()
        
        return {
            "service": "message_replicator",
            "mode": "enhanced" if HAS_ENHANCED_REPLICATOR else "mock",
            "data": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Stats error: {e}")
        return {"error": str(e)}

@app.get("/status")
async def get_status():
    """Estado detallado del servicio"""
    try:
        if not replicator_service:
            return {"status": "not_initialized"}
        
        return {
            "service": "message_replicator",
            "mode": "enhanced" if HAS_ENHANCED_REPLICATOR else "mock",
            "is_running": getattr(replicator_service, 'is_running', True),
            "is_listening": getattr(replicator_service, 'is_listening', True),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    config = {
        "host": "0.0.0.0",
        "port": 8001,
        "reload": False,  # Desactivar reload para evitar problemas
        "log_level": "info"
    }
    
    print("🚀 Starting Message Replicator Microservice...")
    print(f"   📡 Service: Message Replicator")
    print(f"   🌐 URL: http://{config['host']}:{config['port']}")
    print(f"   📚 Docs: http://{config['host']}:{config['port']}/docs")
    print(f"   🏥 Health: http://{config['host']}:{config['port']}/health")
    print(f"   🎭 Mode: {'Enhanced' if HAS_ENHANCED_REPLICATOR else 'Mock'}")
    
    uvicorn.run(app, **config)
