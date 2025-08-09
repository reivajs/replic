#!/usr/bin/env python3
"""
💾 FILE MANAGER MICROSERVICE v4.0
=================================
Servicio de gestión de archivos y multimedia
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn
import logging

# Logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FileManager:
    """Gestor de archivos optimizado"""
    
    def __init__(self):
        self.base_dir = Path("files")
        self.temp_dir = Path("temp")
        self.processed_dir = Path("processed")
        
        # Crear directorios
        for directory in [self.base_dir, self.temp_dir, self.processed_dir]:
            directory.mkdir(exist_ok=True)
        
        # Crear subdirectorios por categoría
        categories = ["images", "videos", "documents", "audio", "general"]
        for category in categories:
            (self.base_dir / category).mkdir(exist_ok=True)
    
    def save_file(self, file_content: bytes, filename: str, category: str = "general") -> str:
        """Guardar archivo"""
        category_dir = self.base_dir / category
        category_dir.mkdir(exist_ok=True)
        
        # Añadir timestamp al nombre para evitar colisiones
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name, ext = os.path.splitext(filename)
        safe_filename = f"{name}_{timestamp}{ext}"
        
        file_path = category_dir / safe_filename
        
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        logger.info(f"📁 Archivo guardado: {file_path}")
        return str(file_path)
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Obtener información del archivo"""
        path = Path(file_path)
        
        if not path.exists():
            return {"error": "File not found"}
        
        stat = path.stat()
        
        return {
            "name": path.name,
            "size": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "extension": path.suffix,
            "category": path.parent.name,
            "full_path": str(path),
            "exists": True
        }
    
    def list_files(self, category: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Listar archivos"""
        files = []
        
        if category:
            search_dir = self.base_dir / category
            if not search_dir.exists():
                return []
            search_dirs = [search_dir]
        else:
            search_dirs = [self.base_dir]
        
        for search_dir in search_dirs:
            for file_path in search_dir.rglob("*"):
                if file_path.is_file() and len(files) < limit:
                    files.append(self.get_file_info(str(file_path)))
        
        # Ordenar por fecha de modificación (más recientes primero)
        files.sort(key=lambda x: x.get('modified', ''), reverse=True)
        
        return files[:limit]
    
    def cleanup_old_files(self, hours: int = 24) -> int:
        """Limpiar archivos antiguos de directorios temporales"""
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        cleaned = 0
        
        for directory in [self.temp_dir, self.processed_dir]:
            for file_path in directory.rglob("*"):
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    try:
                        file_path.unlink()
                        cleaned += 1
                    except Exception as e:
                        logger.error(f"Error limpiando {file_path}: {e}")
        
        logger.info(f"🧹 Archivos limpiados: {cleaned}")
        return cleaned
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de almacenamiento"""
        stats = {
            "categories": {},
            "total_files": 0,
            "total_size_bytes": 0,
            "total_size_mb": 0,
            "directories": {
                "base": str(self.base_dir),
                "temp": str(self.temp_dir),
                "processed": str(self.processed_dir)
            }
        }
        
        # Estadísticas por categoría
        for category_dir in self.base_dir.iterdir():
            if category_dir.is_dir():
                category_stats = {
                    "files": 0,
                    "size_bytes": 0,
                    "size_mb": 0
                }
                
                for file_path in category_dir.rglob("*"):
                    if file_path.is_file():
                        size = file_path.stat().st_size
                        category_stats["files"] += 1
                        category_stats["size_bytes"] += size
                        
                        stats["total_files"] += 1
                        stats["total_size_bytes"] += size
                
                category_stats["size_mb"] = round(category_stats["size_bytes"] / (1024 * 1024), 2)
                stats["categories"][category_dir.name] = category_stats
        
        stats["total_size_mb"] = round(stats["total_size_bytes"] / (1024 * 1024), 2)
        
        return stats

# Instancia global
file_manager = FileManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida del servicio"""
    try:
        logger.info("🚀 Iniciando File Manager Service...")
        
        # Cleanup inicial
        cleaned = file_manager.cleanup_old_files()
        logger.info(f"🧹 Archivos temporales limpiados: {cleaned}")
        
        logger.info("✅ File Manager Service iniciado")
        yield
    finally:
        logger.info("🛑 File Manager Service detenido")

# Crear aplicación FastAPI
app = FastAPI(
    title="💾 File Manager Microservice",
    description="Servicio de gestión de archivos y multimedia",
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
    """Información del servicio"""
    return {
        "service": "File Manager Microservice",
        "version": "4.0.0",
        "description": "Gestión de archivos y multimedia enterprise"
    }

@app.get("/health")
async def health_check():
    """Health check"""
    storage_stats = file_manager.get_storage_stats()
    
    return {
        "status": "healthy",
        "service": "file_manager",
        "version": "4.0.0",
        "storage": storage_stats,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/stats")
async def get_stats():
    """Obtener estadísticas"""
    return {
        "service": "file_manager",
        "storage": file_manager.get_storage_stats(),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), category: str = "general"):
    """Subir archivo"""
    try:
        content = await file.read()
        file_path = file_manager.save_file(content, file.filename, category)
        
        return {
            "message": "File uploaded successfully",
            "file_path": file_path,
            "file_info": file_manager.get_file_info(file_path),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files")
async def list_files(category: str = None, limit: int = 100):
    """Listar archivos"""
    try:
        files = file_manager.list_files(category, limit)
        
        return {
            "files": files,
            "count": len(files),
            "category": category,
            "limit": limit,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files/{category}/{filename}")
async def get_file(category: str, filename: str):
    """Obtener archivo"""
    file_path = file_manager.base_dir / category / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_path)

@app.delete("/cleanup")
async def cleanup_files(hours: int = 24):
    """Limpiar archivos antiguos"""
    try:
        cleaned = file_manager.cleanup_old_files(hours)
        
        return {
            "message": f"Cleaned {cleaned} old files",
            "hours": hours,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/storage")
async def get_storage_info():
    """Información de almacenamiento"""
    return {
        "storage": file_manager.get_storage_stats(),
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    config = {
        "host": "0.0.0.0",
        "port": 8003,
        "reload": False,
        "log_level": "info"
    }
    
    print("🚀 Starting File Manager Microservice...")
    print(f"   💾 Service: File Manager")
    print(f"   🌐 URL: http://{config['host']}:{config['port']}")
    print(f"   📚 Docs: http://{config['host']}:{config['port']}/docs")
    print(f"   🏥 Health: http://{config['host']}:{config['port']}/health")
    
    uvicorn.run(app, **config)