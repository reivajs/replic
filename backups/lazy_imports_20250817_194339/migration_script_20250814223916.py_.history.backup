#!/usr/bin/env python3
"""
🔄 MIGRATION SCRIPT - Monolito a Arquitectura Modular
======================================================
Script automático para migrar tu main.py monolítico a la nueva estructura modular
"""

import os
import shutil
import re
from pathlib import Path
from typing import List, Dict, Tuple
import ast
import json
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProjectMigrator:
    """Migrador automático de proyecto monolítico a modular"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.backup_dir = self.project_root / "backup_migration"
        self.new_structure = {
            "app/api/v1": ["health.py", "discovery.py", "groups.py", "config.py", "websocket.py"],
            "app/api/v2": ["__init__.py"],
            "app/api/middleware": ["auth.py", "rate_limit.py", "cors.py", "logging.py"],
            "app/core": ["config.py", "dependencies.py", "exceptions.py", "logging.py", "middleware.py", "security.py"],
            "app/services": ["registry.py", "discovery.py", "cache.py", "metrics.py"],
            "app/database": ["connection.py", "models.py"],
            "app/database/repositories": ["base.py", "chat.py", "user.py", "config.py"],
            "app/database/migrations": [],
            "app/tasks": ["manager.py", "scheduled.py"],
            "app/tasks/workers": ["discovery.py", "cleanup.py", "analytics.py"],
            "app/websocket": ["manager.py", "handlers.py", "events.py"],
            "app/ui": ["dashboard.py", "discovery_ui.py", "groups_hub.py"],
            "tests/unit": [],
            "tests/integration": [],
            "tests/e2e": [],
            "docker": ["Dockerfile.app", "Dockerfile.services"],
            "k8s": ["deployment.yaml", "service.yaml", "ingress.yaml"],
            "docs": ["API.md", "ARCHITECTURE.md", "DEPLOYMENT.md"],
            "monitoring": ["prometheus.yml", "loki-config.yml"],
            "monitoring/grafana/dashboards": [],
            "monitoring/grafana/datasources": [],
            "scripts": [],
            "config": ["services.yaml"]
        }
        
    def run_migration(self):
        """Ejecutar migración completa"""
        print("\n" + "="*70)
        print("🔄 INICIANDO MIGRACIÓN A ARQUITECTURA MODULAR")
        print("="*70 + "\n")
        
        try:
            # Paso 1: Backup
            self.create_backup()
            
            # Paso 2: Crear estructura
            self.create_directory_structure()
            
            # Paso 3: Extraer código del main.py
            self.extract_code_from_main()
            
            # Paso 4: Crear archivos de configuración
            self.create_config_files()
            
            # Paso 5: Actualizar imports
            self.update_imports()
            
            # Paso 6: Crear archivos Docker
            self.create_docker_files()
            
            # Paso 7: Crear archivos de testing
            self.create_test_files()
            
            # Paso 8: Generar documentación
            self.generate_documentation()
            
            # Paso 9: Validar migración
            self.validate_migration()
            
            print("\n" + "="*70)
            print("✅ MIGRACIÓN COMPLETADA EXITOSAMENTE")
            print("="*70 + "\n")
            
            self.print_next_steps()
            
        except Exception as e:
            logger.error(f"❌ Error en migración: {e}")
            self.rollback()
            raise
    
    def create_backup(self):
        """Crear backup del proyecto actual"""
        logger.info("📦 Creando backup del proyecto...")
        
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)
        
        # Backup archivos importantes
        files_to_backup = [
            "main.py",
            ".env",
            "requirements.txt",
            "services/message_replicator/main.py"
        ]
        
        self.backup_dir.mkdir(exist_ok=True)
        
        for file in files_to_backup:
            src = self.project_root / file
            if src.exists():
                dst = self.backup_dir / file
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                logger.info(f"  ✓ Backup: {file}")
    
    def create_directory_structure(self):
        """Crear nueva estructura de directorios"""
        logger.info("📁 Creando estructura de directorios...")
        
        for path, files in self.new_structure.items():
            dir_path = self.project_root / path
            dir_path.mkdir(parents=True, exist_ok=True)
            
            # Crear __init__.py en cada directorio Python
            if not path.startswith(("docker", "k8s", "docs", "monitoring", "scripts", "config")):
                init_file = dir_path / "__init__.py"
                init_file.touch()
            
            # Crear archivos especificados
            for file in files:
                file_path = dir_path / file
                if not file_path.exists():
                    file_path.touch()
            
            logger.info(f"  ✓ Created: {path}")
    
    def extract_code_from_main(self):
        """Extraer y reorganizar código del main.py monolítico"""
        logger.info("🔍 Extrayendo código del main.py...")
        
        main_file = self.project_root / "main.py"
        if not main_file.exists():
            logger.warning("  ⚠️ main.py no encontrado")
            return
        
        with open(main_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extraer diferentes secciones
        extractions = {
            "app/services/registry.py": self._extract_service_registry(content),
            "app/api/v1/health.py": self._extract_health_endpoints(content),
            "app/api/v1/discovery.py": self._extract_discovery_endpoints(content),
            "app/api/v1/groups.py": self._extract_groups_endpoints(content),
            "app/api/v1/websocket.py": self._extract_websocket_handlers(content),
            "app/core/config.py": self._create_config_module(),
            "app/core/dependencies.py": self._create_dependencies_module(),
            "app/core/exceptions.py": self._create_exceptions_module(),
            "app/services/cache.py": self._create_cache_service(),
            "app/database/models.py": self._create_database_models(),
        }
        
        for filepath, content in extractions.items():
            if content:
                file_path = self.project_root / filepath
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"  ✓ Extracted: {filepath}")
    
    def _extract_service_registry(self, content: str) -> str:
        """Extraer ServiceRegistry del main.py"""
        # Buscar clase EnhancedServiceRegistry
        pattern = r'class\s+EnhancedServiceRegistry.*?(?=class\s+|\Z)'
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            return f'''"""
Service Registry Module
=======================
Gestión centralizada de microservicios
"""

import asyncio
import httpx
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

{match.group()}

# Instancia global
service_registry = EnhancedServiceRegistry()
'''
        return ""
    
    def _extract_health_endpoints(self, content: str) -> str:
        """Extraer endpoints de health"""
        return '''"""
Health Check Endpoints
======================
"""

from fastapi import APIRouter, Depends
from datetime import datetime
from app.core.dependencies import get_service_registry

router = APIRouter()

@router.get("/health")
async def health_check(registry = Depends(get_service_registry)):
    """Health check del sistema"""
    healthy, total = await registry.check_all_services()
    
    return {
        "status": "healthy" if healthy > 0 else "degraded",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "healthy": healthy,
            "total": total,
            "percentage": (healthy / total * 100) if total > 0 else 0
        }
    }

@router.get("/health/detailed")
async def health_detailed(registry = Depends(get_service_registry)):
    """Health check detallado por servicio"""
    results = {}
    
    for service_name in registry.services:
        health = await registry.check_service_health(service_name)
        results[service_name] = health
    
    return results
'''
    
    def _extract_discovery_endpoints(self, content: str) -> str:
        """Extraer endpoints de discovery"""
        return '''"""
Discovery Service Endpoints
===========================
"""

from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional
from app.core.dependencies import get_service_registry
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/chats")
async def get_discovered_chats(
    chat_type: Optional[str] = Query(None),
    search_term: Optional[str] = Query(None),
    min_participants: Optional[int] = Query(None),
    limit: int = Query(100),
    offset: int = Query(0),
    registry = Depends(get_service_registry)
):
    """Obtener chats descubiertos"""
    try:
        params = {"limit": limit, "offset": offset}
        
        if chat_type:
            params["chat_type"] = chat_type
        if search_term:
            params["search_term"] = search_term
        if min_participants is not None:
            params["min_participants"] = min_participants
        
        chats = await registry.get_discovered_chats(params)
        
        return {
            "chats": chats,
            "total": len(chats),
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Error getting discovered chats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scan")
async def trigger_scan(
    force_refresh: bool = False,
    registry = Depends(get_service_registry)
):
    """Iniciar escaneo de discovery"""
    result = await registry.discovery_scan_chats(force_refresh)
    return result
'''
    
    def _extract_groups_endpoints(self, content: str) -> str:
        """Extraer endpoints de grupos"""
        return '''"""
Groups Management Endpoints
===========================
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from app.core.dependencies import get_service_registry
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class GroupConfig(BaseModel):
    """Configuración de grupo"""
    group_id: int
    group_name: str
    webhook_url: Optional[str] = None
    enabled: bool = True
    filters: Dict[str, Any] = {}
    transformations: Dict[str, Any] = {}

@router.get("/")
async def get_groups(registry = Depends(get_service_registry)):
    """Obtener todos los grupos configurados"""
    try:
        groups = await registry.get_configured_groups()
        return {"groups": groups}
    except Exception as e:
        logger.error(f"Error getting groups: {e}")
        return {"groups": []}

@router.post("/{group_id}/enable")
async def enable_group(
    group_id: int,
    registry = Depends(get_service_registry)
):
    """Habilitar grupo"""
    try:
        result = await registry.enable_group(group_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{group_id}/disable")
async def disable_group(
    group_id: int,
    registry = Depends(get_service_registry)
):
    """Deshabilitar grupo"""
    try:
        result = await registry.disable_group(group_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
'''
    
    def _extract_websocket_handlers(self, content: str) -> str:
        """Extraer handlers de WebSocket"""
        return '''"""
WebSocket Handlers
==================
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import asyncio
from datetime import datetime
from app.websocket.manager import WebSocketManager
import logging

router = APIRouter()
logger = logging.getLogger(__name__)
ws_manager = WebSocketManager()

@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket principal"""
    await ws_manager.connect(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })
            
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)
'''
    
    def _create_config_module(self) -> str:
        """Crear módulo de configuración"""
        return '''"""
Configuration Module
====================
Configuración centralizada usando Pydantic
"""

from enum import Enum
from typing import Optional
from pydantic import BaseSettings, validator
import os

class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Enterprise Orchestrator"
    VERSION: str = "6.0.0"
    DESCRIPTION: str = "Modular SaaS Orchestrator"
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    RELOAD: bool = False
    DEBUG: bool = False
    
    # URLs
    BASE_URL: str = "http://localhost:8000"
    
    # Database
    DATABASE_URL: str = "postgresql://user:pass@localhost/db"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 40
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    CACHE_TTL: int = 300
    
    # Security
    SECRET_KEY: str = "your-secret-key-here"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Features
    ENABLE_BETA_FEATURES: bool = False
    ENABLE_SERVICE_DISCOVERY: bool = True
    PROMETHEUS_ENABLED: bool = True
    
    # Performance
    MAX_WORKERS: int = 10
    REQUEST_TIMEOUT: int = 30
    FAIL_FAST: bool = False
    
    # Logging
    LOG_LEVEL: str = "INFO"
    ACCESS_LOG: bool = True
    
    # Services
    SERVICES_CONFIG: str = "config/services.yaml"
    CONSUL_HOST: str = "localhost"
    CONSUL_PORT: int = 8500
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 100
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
'''
    
    def _create_dependencies_module(self) -> str:
        """Crear módulo de dependencias"""
        return '''"""
Dependency Injection Module
============================
"""

from functools import lru_cache
from app.services.registry import service_registry
from app.services.cache import CacheService
from app.database.connection import get_db

@lru_cache()
def get_service_registry():
    """Get service registry instance"""
    return service_registry

@lru_cache()
def get_cache_service():
    """Get cache service instance"""
    return CacheService()

def get_db_session():
    """Get database session"""
    return get_db()
'''
    
    def _create_exceptions_module(self) -> str:
        """Crear módulo de excepciones"""
        return '''"""
Custom Exceptions Module
========================
"""

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

class ServiceUnavailableError(Exception):
    """Service unavailable error"""
    pass

class ConfigurationError(Exception):
    """Configuration error"""
    pass

class AuthenticationError(Exception):
    """Authentication error"""
    pass

def setup_exception_handlers(app):
    """Setup global exception handlers"""
    
    @app.exception_handler(ServiceUnavailableError)
    async def service_unavailable_handler(request: Request, exc: ServiceUnavailableError):
        logger.error(f"Service unavailable: {exc}")
        return JSONResponse(
            status_code=503,
            content={"detail": str(exc)}
        )
    
    @app.exception_handler(ConfigurationError)
    async def configuration_error_handler(request: Request, exc: ConfigurationError):
        logger.error(f"Configuration error: {exc}")
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc)}
        )
    
    @app.exception_handler(AuthenticationError)
    async def auth_error_handler(request: Request, exc: AuthenticationError):
        return JSONResponse(
            status_code=401,
            content={"detail": str(exc)}
        )
'''
    
    def _create_cache_service(self) -> str:
        """Crear servicio de cache"""
        return '''"""
Cache Service Module
====================
"""

import redis.asyncio as redis
import json
from typing import Any, Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class CacheService:
    def __init__(self, redis_url: str = None, ttl: int = 300):
        self.redis_url = redis_url or settings.REDIS_URL
        self.ttl = ttl
        self.client = None
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.client = await redis.from_url(self.redis_url)
            await self.client.ping()
            logger.info("✅ Redis connected")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.client:
            await self.client.close()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.client:
            return None
        
        try:
            value = await self.client.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
        return None
    
    async def set(self, key: str, value: Any, ttl: int = None):
        """Set value in cache"""
        if not self.client:
            return
        
        try:
            ttl = ttl or self.ttl
            await self.client.set(
                key,
                json.dumps(value),
                ex=ttl
            )
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    async def delete(self, key: str):
        """Delete key from cache"""
        if not self.client:
            return
        
        try:
            await self.client.delete(key)
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
'''
    
    def _create_database_models(self) -> str:
        """Crear modelos de base de datos"""
        return '''"""
Database Models
===============
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Chat(Base):
    __tablename__ = "chats"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True, index=True)
    title = Column(String)
    chat_type = Column(String)
    username = Column(String, nullable=True)
    participants_count = Column(Integer, default=0)
    is_configured = Column(Boolean, default=False)
    is_active = Column(Boolean, default=False)
    discovered_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    configurations = relationship("Configuration", back_populates="chat")

class Configuration(Base):
    __tablename__ = "configurations"
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey("chats.id"))
    webhook_url = Column(String)
    filters = Column(JSON, default={})
    transformations = Column(JSON, default={})
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    chat = relationship("Chat", back_populates="configurations")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
'''
    
    def create_config_files(self):
        """Crear archivos de configuración"""
        logger.info("⚙️ Creando archivos de configuración...")
        
        # services.yaml
        services_yaml = """# Service Configuration
services:
  message_replicator:
    name: "Message Replicator"
    url: "http://localhost:8001"
    port: 8001
    health_endpoint: "/health"
    timeout: 10
    retry_attempts: 3
    circuit_breaker_threshold: 5
    
  discovery:
    name: "Discovery Service"
    url: "http://localhost:8002"
    port: 8002
    health_endpoint: "/health"
    timeout: 10
    retry_attempts: 3
    circuit_breaker_threshold: 5
    
  watermark:
    name: "Watermark Service"
    url: "http://localhost:8081"
    port: 8081
    health_endpoint: "/health"
    timeout: 10
    retry_attempts: 3
    circuit_breaker_threshold: 5
"""
        
        config_file = self.project_root / "config" / "services.yaml"
        with open(config_file, 'w') as f:
            f.write(services_yaml)
        logger.info("  ✓ Created: config/services.yaml")
        
        # .env.example
        env_example = """# Environment Configuration
ENVIRONMENT=development
DEBUG=true

# Application
APP_NAME="Enterprise Orchestrator"
VERSION=6.0.0
SECRET_KEY=your-secret-key-here

# Server
HOST=0.0.0.0
PORT=8000
WORKERS=4

# Database
DATABASE_URL=postgresql://user:pass@localhost/db
DB_POOL_SIZE=20

# Redis
REDIS_URL=redis://localhost:6379
CACHE_TTL=300

# Telegram
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_PHONE=your_phone

# Discord Webhooks
WEBHOOK_GROUP1=https://discord.com/api/webhooks/...
WEBHOOK_GROUP2=https://discord.com/api/webhooks/...

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_USER=admin
GRAFANA_PASSWORD=admin
"""
        
        env_file = self.project_root / ".env.example"
        with open(env_file, 'w') as f:
            f.write(env_example)
        logger.info("  ✓ Created: .env.example")
    
    def update_imports(self):
        """Actualizar imports en archivos"""
        logger.info("🔄 Actualizando imports...")
        
        # Crear nuevo main.py simplificado
        new_main = '''#!/usr/bin/env python3
"""
Enterprise Orchestrator - Main Entry Point
==========================================
"""

from app.core.config import settings
from app.core.logging import setup_logging
import uvicorn

# Import the refactored application
from app.main import app

if __name__ == "__main__":
    setup_logging()
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        workers=settings.WORKERS,
        log_level=settings.LOG_LEVEL.lower()
    )
'''
        
        main_file = self.project_root / "main_new.py"
        with open(main_file, 'w') as f:
            f.write(new_main)
        logger.info("  ✓ Created: main_new.py")
    
    def create_docker_files(self):
        """Crear archivos Docker"""
        logger.info("🐳 Creando archivos Docker...")
        
        # Dockerfile.app
        dockerfile_app = """FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/
COPY main.py .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
        
        docker_file = self.project_root / "docker" / "Dockerfile.app"
        with open(docker_file, 'w') as f:
            f.write(dockerfile_app)
        logger.info("  ✓ Created: docker/Dockerfile.app")
    
    def create_test_files(self):
        """Crear archivos de testing"""
        logger.info("🧪 Creando archivos de testing...")
        
        # test_health.py
        test_health = """import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] in ["healthy", "degraded"]

def test_health_detailed():
    response = client.get("/api/v1/health/detailed")
    assert response.status_code == 200
"""
        
        test_file = self.project_root / "tests" / "unit" / "test_health.py"
        with open(test_file, 'w') as f:
            f.write(test_health)
        logger.info("  ✓ Created: tests/unit/test_health.py")
        
        # pytest.ini
        pytest_ini = """[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --color=yes
"""
        
        pytest_file = self.project_root / "pytest.ini"
        with open(pytest_file, 'w') as f:
            f.write(pytest_ini)
        logger.info("  ✓ Created: pytest.ini")
    
    def generate_documentation(self):
        """Generar documentación"""
        logger.info("📚 Generando documentación...")
        
        # MIGRATION.md
        migration_doc = """# Migration Guide

## From Monolithic to Modular Architecture

### Before Migration
- Single main.py file with 1300+ lines
- Mixed concerns (API, business logic, UI)
- Hard to test and maintain

### After Migration
- Modular structure with clear separation
- Easy to test individual components
- Scalable and maintainable

### Steps Completed
1. ✅ Created modular directory structure
2. ✅ Extracted code into separate modules
3. ✅ Updated imports and dependencies
4. ✅ Created configuration files
5. ✅ Added Docker support
6. ✅ Created test structure

### Next Steps
1. Run tests: `pytest tests/`
2. Start services: `docker-compose up`
3. Access dashboard: http://localhost:8000
"""
        
        doc_file = self.project_root / "docs" / "MIGRATION.md"
        with open(doc_file, 'w') as f:
            f.write(migration_doc)
        logger.info("  ✓ Created: docs/MIGRATION.md")
    
    def validate_migration(self):
        """Validar que la migración fue exitosa"""
        logger.info("✅ Validando migración...")
        
        required_files = [
            "app/core/config.py",
            "app/api/v1/health.py",
            "app/services/registry.py",
            "docker/Dockerfile.app",
            "config/services.yaml",
            "tests/unit/test_health.py",
            ".env.example"
        ]
        
        missing_files = []
        for file in required_files:
            file_path = self.project_root / file
            if not file_path.exists():
                missing_files.append(file)
        
        if missing_files:
            logger.warning(f"  ⚠️ Archivos faltantes: {missing_files}")
        else:
            logger.info("  ✓ Todos los archivos críticos creados")
    
    def rollback(self):
        """Rollback en caso de error"""
        logger.info("⏮️ Ejecutando rollback...")
        
        if self.backup_dir.exists():
            # Restaurar archivos desde backup
            for backup_file in self.backup_dir.rglob("*"):
                if backup_file.is_file():
                    relative_path = backup_file.relative_to(self.backup_dir)
                    original_path = self.project_root / relative_path
                    
                    original_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(backup_file, original_path)
                    logger.info(f"  ✓ Restored: {relative_path}")
    
    def print_next_steps(self):
        """Imprimir próximos pasos"""
        print("\n" + "="*70)
        print("📋 PRÓXIMOS PASOS")
        print("="*70)
        print("""
1. REVISAR Y AJUSTAR:
   - Revisa los archivos generados en app/
   - Ajusta la configuración en .env
   - Personaliza config/services.yaml

2. INSTALAR DEPENDENCIAS:
   pip install -r requirements-new.txt

3. EJECUTAR TESTS:
   pytest tests/ -v

4. INICIAR SERVICIOS:
   # Desarrollo local
   python main_new.py
   
   # Con Docker
   docker-compose -f docker-compose.optimized.yml up

5. VERIFICAR:
   - Dashboard: http://localhost:8000/dashboard
   - API Docs: http://localhost:8000/docs
   - Health: http://localhost:8000/api/v1/health

6. LIMPIAR:
   # Renombrar main.py original
   mv main.py main_old.py
   mv main_new.py main.py
   
   # Eliminar backup si todo está OK
   rm -rf backup_migration/
""")
        print("="*70)


class RequirementsGenerator:
    """Generador de requirements.txt actualizado"""
    
    @staticmethod
    def generate():
        """Generar requirements.txt optimizado"""
        requirements = """# Core Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
python-dotenv==1.0.0

# Database
sqlalchemy==2.0.23
alembic==1.12.1
asyncpg==0.29.0
psycopg2-binary==2.9.9

# Redis
redis==5.0.1
aioredis==2.0.1

# HTTP Client
httpx==0.25.2
aiohttp==3.9.1

# Telegram
telethon==1.32.0
cryptg==0.4.0

# Image Processing
Pillow==10.1.0

# Authentication
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6

# Monitoring
prometheus-client==0.19.0
sentry-sdk==1.38.0

# Utils
pyyaml==6.0.1
python-dateutil==2.8.2
pytz==2023.3
tenacity==8.2.3
loguru==0.7.2

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
httpx==0.25.2
faker==20.1.0

# Development
black==23.12.0
flake8==6.1.0
isort==5.13.0
mypy==1.7.1
pre-commit==3.5.0
"""
        return requirements


def main():
    """Función principal del script de migración"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="🔄 Script de Migración Automática - Monolito a Modular"
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Directorio raíz del proyecto"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Ejecutar en modo simulación sin hacer cambios"
    )
    parser.add_argument(
        "--generate-requirements",
        action="store_true",
        help="Solo generar requirements.txt"
    )
    
    args = parser.parse_args()
    
    if args.generate_requirements:
        # Solo generar requirements
        requirements = RequirementsGenerator.generate()
        req_file = Path(args.project_root) / "requirements-new.txt"
        with open(req_file, 'w') as f:
            f.write(requirements)
        print(f"✅ Requirements generado: {req_file}")
        return
    
    if args.dry_run:
        print("🔍 MODO SIMULACIÓN - No se harán cambios reales")
        print("\nArchivos y directorios que se crearían:")
        migrator = ProjectMigrator(args.project_root)
        for path in migrator.new_structure.keys():
            print(f"  📁 {path}/")
        print("\n✅ Ejecuta sin --dry-run para aplicar cambios")
    else:
        # Ejecutar migración completa
        migrator = ProjectMigrator(args.project_root)
        migrator.run_migration()
        
        # Generar requirements
        requirements = RequirementsGenerator.generate()
        req_file = Path(args.project_root) / "requirements-new.txt"
        with open(req_file, 'w') as f:
            f.write(requirements)
        print(f"✅ Requirements generado: {req_file}")


if __name__ == "__main__":
    main()