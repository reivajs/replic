#!/usr/bin/env python3
"""
ZERO COST DEPLOYMENT SCRIPT
===========================
Deploy completo del sistema en tu laptop
Ejecuta todo con recursos mínimos
"""

import os
import sys
import asyncio
import signal
import subprocess
from pathlib import Path
from datetime import datetime
import json

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class ZeroCostDeployment:
    """
    Deployment manager para tu laptop
    Gestiona todos los servicios con recursos mínimos
    """
    
    def __init__(self):
        self.services = {}
        self.is_running = False
        
        # Resource limits for laptop
        self.config = {
            'max_memory_mb': 2048,  # 2GB max
            'max_cpu_percent': 70,   # 70% CPU max
            'enable_dashboard': True,
            'enable_monitoring': True,
            'auto_cleanup_hours': 24,
            'backup_enabled': True
        }
    
    async def start_services(self):
        """Start all services"""
        logger.info("🚀 Starting Zero Cost Architecture...")
        
        # 1. Start File Processor Microservice
        logger.info("📦 Starting File Processor Microservice...")
        from app.services.file_processor_v2 import get_file_processor
        processor = await get_file_processor()
        self.services['processor'] = processor
        
        # 2. Start Enhanced Replicator with Bridge
        logger.info("🔄 Starting Enhanced Replicator Service...")
        from app.services.integration_bridge import EnhancedReplicatorServiceV2
        replicator = EnhancedReplicatorServiceV2()
        await replicator.initialize()
        self.services['replicator'] = replicator
        
        # 3. Start Discord Sender
        logger.info("📤 Starting Discord Sender...")
        from app.services.discord_sender import DiscordSenderEnhanced
        discord = DiscordSenderEnhanced()
        await discord.initialize()
        self.services['discord'] = discord
        
        # 4. Start Watermark Service
        logger.info("🎨 Starting Watermark Service...")
        from app.services.watermark_service import WatermarkServiceIntegrated
        watermark = WatermarkServiceIntegrated()
        await watermark.initialize()
        self.services['watermark'] = watermark
        
        # 5. Start Web Dashboard
        if self.config['enable_dashboard']:
            logger.info("📊 Starting Web Dashboard...")
            await self.start_dashboard()
        
        # 6. Start monitoring tasks
        if self.config['enable_monitoring']:
            asyncio.create_task(self.monitoring_loop())
        
        # 7. Start cleanup task
        asyncio.create_task(self.cleanup_loop())
        
        self.is_running = True
        logger.info("✅ All services started successfully!")
        
        # Print access info
        self.print_access_info()
    
    async def start_dashboard(self):
        """Start web dashboard"""
        from fastapi import FastAPI, WebSocket
        from fastapi.responses import HTMLResponse
        from fastapi.staticfiles import StaticFiles
        import uvicorn
        
        app = FastAPI(title="File Processor Dashboard")
        
        # Serve dashboard HTML
        @app.get("/")
        async def get_dashboard():
            dashboard_path = Path("monitoring_dashboard.html")
            if dashboard_path.exists():
                return HTMLResponse(dashboard_path.read_text())
            return HTMLResponse("<h1>Dashboard not found</h1>")
        
        # API endpoints
        @app.get("/api/stats")
        async def get_stats():
            stats = {}
            
            # Get processor stats
            if 'processor' in self.services:
                processor_stats = await self.services['processor'].get_stats()
                stats['processor'] = processor_stats
            
            # Get replicator stats
            if 'replicator' in self.services:
                stats['replicator'] = {
                    'is_running': self.services['replicator'].is_running,
                    'is_listening': self.services['replicator'].is_listening
                }
            
            # Get discord stats
            if 'discord' in self.services:
                discord_stats = await self.services['discord'].get_stats()
                stats['discord'] = discord_stats
            
            # Get watermark stats
            if 'watermark' in self.services:
                watermark_stats = await self.services['watermark'].get_stats()
                stats['watermark'] = watermark_stats
            
            return stats
        
        # WebSocket for real-time updates
        @app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            
            try:
                while True:
                    # Send stats every 2 seconds
                    stats = await get_stats()
                    await websocket.send_json(stats)
                    await asyncio.sleep(2)
                    
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
            finally:
                await websocket.close()
        
        # Health check
        @app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "services": list(self.services.keys()),
                "uptime": datetime.now().isoformat()
            }
        
        # Start server in background
        config = uvicorn.Config(
            app=app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )
        server = uvicorn.Server(config)
        asyncio.create_task(server.serve())
    
    async def monitoring_loop(self):
        """Monitor system resources"""
        import psutil
        
        while self.is_running:
            try:
                # Get system stats
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                # Check limits
                if cpu_percent > self.config['max_cpu_percent']:
                    logger.warning(f"⚠️ High CPU usage: {cpu_percent}%")
                
                if memory.percent > 80:
                    logger.warning(f"⚠️ High memory usage: {memory.percent}%")
                
                if disk.percent > 90:
                    logger.warning(f"⚠️ Low disk space: {disk.percent}% used")
                
                # Log stats every 5 minutes
                if datetime.now().minute % 5 == 0:
                    logger.info(f"📊 System: CPU {cpu_percent}% | RAM {memory.percent}% | Disk {disk.percent}%")
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def cleanup_loop(self):
        """Cleanup old files periodically"""
        while self.is_running:
            try:
                # Cleanup every N hours
                await asyncio.sleep(self.config['auto_cleanup_hours'] * 3600)
                
                logger.info("🧹 Running cleanup...")
                
                # Cleanup processor files
                if 'processor' in self.services:
                    from app.services.integration_bridge import FileProcessorEnhanced
                    if isinstance(self.services['processor'], FileProcessorMicroservice):
                        await self.services['processor'].cleanup_old_files(days=7)
                
                # Cleanup logs
                logs_dir = Path("logs")
                if logs_dir.exists():
                    for log_file in logs_dir.glob("*.log"):
                        if log_file.stat().st_mtime < (datetime.now().timestamp() - 7 * 86400):
                            log_file.unlink()
                            logger.debug(f"Deleted old log: {log_file}")
                
                logger.info("✅ Cleanup completed")
                
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
    
    def print_access_info(self):
        """Print access information"""
        print("\n" + "="*60)
        print("🎉 ZERO COST ARCHITECTURE RUNNING!")
        print("="*60)
        print("\n📊 Dashboard: http://localhost:8000")
        print("📡 API Docs: http://localhost:8000/docs")
        print("❤️ Health: http://localhost:8000/health")
        print("\n💡 Tips:")
        print("  - Dashboard updates in real-time")
        print("  - All data stored locally (zero cloud cost)")
        print("  - Auto-cleanup every 24 hours")
        print("  - Press Ctrl+C to stop")
        print("\n" + "="*60 + "\n")
    
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("🛑 Shutting down services...")
        
        self.is_running = False
        
        # Stop replicator
        if 'replicator' in self.services:
            await self.services['replicator'].stop()
        
        # Close discord
        if 'discord' in self.services:
            await self.services['discord'].close()
        
        # Stop processor
        if 'processor' in self.services:
            from app.services.integration_bridge import FileProcessorEnhanced
            processor = self.services['processor']
            if hasattr(processor, 'processor') and isinstance(processor.processor, FileProcessorMicroservice):
                await processor.processor.shutdown()
        
        logger.info("✅ All services stopped")


async def main():
    """Main entry point"""
    deployment = ZeroCostDeployment()
    
    # Handle shutdown signals
    def signal_handler(sig, frame):
        logger.info("Received shutdown signal")
        asyncio.create_task(deployment.shutdown())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start services
        await deployment.start_services()
        
        # Keep running
        while deployment.is_running:
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        await deployment.shutdown()
        sys.exit(1)


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║     🚀 ZERO COST FILE PROCESSOR MICROSERVICES 🚀        ║
    ║                                                          ║
    ║     Arquitectura Enterprise en tu Laptop                ║
    ║     Sin costos de infraestructura                      ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # Check dependencies
    try:
        import aiofiles
        import lz4
        import psutil
        import fastapi
        import uvicorn
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("\n📦 Install with:")
        print("pip install aiofiles lz4-python psutil fastapi uvicorn[standard]")
        sys.exit(1)
    
    # Run
    asyncio.run(main())