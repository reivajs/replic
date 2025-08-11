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
from pydantic import BaseModel, Field, validator
import httpx
import json
from pathlib import Path

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

class GroupConfigRequest(BaseModel):
    """Request para configurar un grupo"""
    group_id: int = Field(..., description="ID del grupo de Telegram")
    group_name: str = Field(..., min_length=1, max_length=255, description="Nombre del grupo")
    webhook_url: str = Field(..., description="URL del webhook de Discord")
    enabled: bool = Field(default=True, description="Si la replicación está habilitada")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Filtros de mensajes")
    transformations: Dict[str, Any] = Field(default_factory=dict, description="Transformaciones")
    
    @validator('webhook_url')
    def validate_webhook_url(cls, v):
        if not v.startswith('https://discord.com/api/webhooks/'):
            raise ValueError('URL de webhook de Discord inválida')
        return v
    
    @validator('group_id')
    def validate_group_id(cls, v):
        if v >= 0:
            raise ValueError('Group ID debe ser negativo (formato Telegram)')
        return v

class GroupConfigUpdate(BaseModel):
    """Request para actualizar configuración de grupo"""
    group_name: Optional[str] = Field(None, min_length=1, max_length=255)
    webhook_url: Optional[str] = None
    enabled: Optional[bool] = None
    filters: Optional[Dict[str, Any]] = None
    transformations: Optional[Dict[str, Any]] = None
    
    @validator('webhook_url')
    def validate_webhook_url(cls, v):
        if v and not v.startswith('https://discord.com/api/webhooks/'):
            raise ValueError('URL de webhook de Discord inválida')
        return v

class WebhookValidationRequest(BaseModel):
    """Request para validar webhook"""
    webhook_url: str = Field(..., description="URL del webhook a validar")
    
    @validator('webhook_url')
    def validate_webhook_url(cls, v):
        if not v.startswith('https://discord.com/api/webhooks/'):
            raise ValueError('URL de webhook de Discord inválida')
        return v

class GroupPreviewRequest(BaseModel):
    """Request para preview de configuración"""
    group_id: int
    sample_message: str = Field(default="Este es un mensaje de ejemplo")
    filters: Dict[str, Any] = Field(default_factory=dict)
    transformations: Dict[str, Any] = Field(default_factory=dict)

# ============= CONFIGURATION MANAGER =============

class ConfigurationManager:
    """Gestor dinámico de configuraciones de grupos"""
    
    def __init__(self):
        self.config_file = Path("data/group_configurations.json")
        self.config_file.parent.mkdir(exist_ok=True)
        self._ensure_config_file()
    
    def _ensure_config_file(self):
        """Asegurar que existe el archivo de configuración"""
        if not self.config_file.exists():
            self.config_file.write_text(json.dumps({}, indent=2))
    
    async def load_configurations(self) -> Dict[str, Any]:
        """Cargar configuraciones desde archivo"""
        try:
            if self.config_file.exists():
                return json.loads(self.config_file.read_text())
            return {}
        except Exception as e:
            logger.error(f"Error loading configurations: {e}")
            return {}
    
    async def save_configurations(self, configs: Dict[str, Any]) -> bool:
        """Guardar configuraciones a archivo"""
        try:
            self.config_file.write_text(json.dumps(configs, indent=2))
            return True
        except Exception as e:
            logger.error(f"Error saving configurations: {e}")
            return False
    
    async def add_group_config(self, config: GroupConfigRequest) -> Dict[str, Any]:
        """Añadir nueva configuración de grupo"""
        configs = await self.load_configurations()
        group_key = str(config.group_id)
        
        configs[group_key] = {
            "group_id": config.group_id,
            "group_name": config.group_name,
            "webhook_url": config.webhook_url,
            "enabled": config.enabled,
            "filters": config.filters,
            "transformations": config.transformations,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        await self.save_configurations(configs)
        
        # Actualizar replicator service si está disponible
        await self._update_replicator_service(config.group_id, config.webhook_url, config.enabled)
        
        return configs[group_key]
    
    async def update_group_config(self, group_id: int, updates: GroupConfigUpdate) -> Optional[Dict[str, Any]]:
        """Actualizar configuración existente"""
        configs = await self.load_configurations()
        group_key = str(group_id)
        
        if group_key not in configs:
            return None
        
        # Aplicar updates
        if updates.group_name is not None:
            configs[group_key]["group_name"] = updates.group_name
        if updates.webhook_url is not None:
            configs[group_key]["webhook_url"] = updates.webhook_url
        if updates.enabled is not None:
            configs[group_key]["enabled"] = updates.enabled
        if updates.filters is not None:
            configs[group_key]["filters"] = updates.filters
        if updates.transformations is not None:
            configs[group_key]["transformations"] = updates.transformations
        
        configs[group_key]["updated_at"] = datetime.now().isoformat()
        
        await self.save_configurations(configs)
        
        # Actualizar replicator service
        await self._update_replicator_service(
            group_id, 
            configs[group_key]["webhook_url"], 
            configs[group_key]["enabled"]
        )
        
        return configs[group_key]
    
    async def delete_group_config(self, group_id: int) -> bool:
        """Eliminar configuración de grupo"""
        configs = await self.load_configurations()
        group_key = str(group_id)
        
        if group_key in configs:
            del configs[group_key]
            await self.save_configurations(configs)
            
            # Remover del replicator service
            await self._update_replicator_service(group_id, None, False)
            return True
        
        return False
    
    async def get_group_config(self, group_id: int) -> Optional[Dict[str, Any]]:
        """Obtener configuración específica"""
        configs = await self.load_configurations()
        return configs.get(str(group_id))
    
    async def get_all_configs(self) -> Dict[str, Any]:
        """Obtener todas las configuraciones"""
        return await self.load_configurations()
    
    async def _update_replicator_service(self, group_id: int, webhook_url: Optional[str], enabled: bool):
        """Actualizar el replicator service dinámicamente"""
        try:
            if replicator_service and hasattr(replicator_service, 'update_group_webhook'):
                # Si el enhanced replicator service tiene método de update dinámico
                await replicator_service.update_group_webhook(group_id, webhook_url, enabled)
            else:
                # Fallback: actualizar variables de entorno para próximo restart
                await self._update_env_webhooks()
        except Exception as e:
            logger.error(f"Error updating replicator service: {e}")
    
    async def _update_env_webhooks(self):
        """Actualizar webhooks en variables de entorno"""
        try:
            configs = await self.load_configurations()
            
            # Construir nuevos webhooks
            webhook_vars = []
            for config in configs.values():
                if config.get("enabled", True) and config.get("webhook_url"):
                    group_id = config["group_id"]
                    webhook_url = config["webhook_url"]
                    webhook_vars.append(f"WEBHOOK_{group_id}={webhook_url}")
            
            # Actualizar archivo .env (opcional, para persistencia)
            env_file = Path(".env")
            if env_file.exists():
                lines = env_file.read_text().split('\n')
                # Filtrar líneas de webhooks existentes
                new_lines = [line for line in lines if not line.startswith('WEBHOOK_')]
                # Añadir nuevos webhooks
                new_lines.extend(webhook_vars)
                env_file.write_text('\n'.join(new_lines))
            
        except Exception as e:
            logger.error(f"Error updating env webhooks: {e}")

# Instancia global del gestor de configuración
config_manager = ConfigurationManager()

# ============= WEBHOOK VALIDATION SERVICE =============

class WebhookValidator:
    """Validador de webhooks de Discord"""
    
    @staticmethod
    async def validate_webhook(webhook_url: str) -> Dict[str, Any]:
        """Validar webhook enviando mensaje de prueba"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Enviar mensaje de prueba
                test_payload = {
                    "content": "🧪 **Test de configuración** - Este webhook está funcionando correctamente!",
                    "username": "Replicator Test",
                    "embeds": [{
                        "title": "✅ Webhook Validation",
                        "description": "Este webhook ha sido configurado exitosamente",
                        "color": 0x00ff00,
                        "timestamp": datetime.now().isoformat(),
                        "footer": {
                            "text": "Message Replicator Service"
                        }
                    }]
                }
                
                response = await client.post(webhook_url, json=test_payload)
                
                if response.status_code == 204:
                    return {
                        "valid": True,
                        "message": "Webhook válido y funcionando",
                        "test_sent": True,
                        "response_time_ms": int(response.elapsed.total_seconds() * 1000)
                    }
                else:
                    return {
                        "valid": False,
                        "message": f"Webhook respondió con código {response.status_code}",
                        "test_sent": False,
                        "error": response.text
                    }
                    
        except httpx.TimeoutException:
            return {
                "valid": False,
                "message": "Timeout al conectar con Discord",
                "test_sent": False,
                "error": "Connection timeout"
            }
        except Exception as e:
            return {
                "valid": False,
                "message": f"Error validando webhook: {str(e)}",
                "test_sent": False,
                "error": str(e)
            }

# ============= CONFIGURATION API ENDPOINTS =============

@app.post("/api/config/add_group")
async def add_group_configuration(config: GroupConfigRequest):
    """🔧 Añadir nueva configuración de grupo"""
    try:
        logger.info(f"📝 Adding group configuration: {config.group_id} - {config.group_name}")
        
        # Validar webhook primero
        validation = await WebhookValidator.validate_webhook(config.webhook_url)
        if not validation["valid"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid webhook: {validation['message']}"
            )
        
        # Guardar configuración
        saved_config = await config_manager.add_group_config(config)
        
        return {
            "success": True,
            "message": "Group configured successfully",
            "group_id": config.group_id,
            "group_name": config.group_name,
            "webhook_validation": validation,
            "config": saved_config
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error adding group configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Configuration failed: {str(e)}")

@app.put("/api/config/groups/{group_id}")
async def update_group_configuration(group_id: int, updates: GroupConfigUpdate):
    """🔧 Actualizar configuración de grupo existente"""
    try:
        logger.info(f"📝 Updating group configuration: {group_id}")
        
        # Validar webhook si se está actualizando
        if updates.webhook_url:
            validation = await WebhookValidator.validate_webhook(updates.webhook_url)
            if not validation["valid"]:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid webhook: {validation['message']}"
                )
        
        # Actualizar configuración
        updated_config = await config_manager.update_group_config(group_id, updates)
        
        if not updated_config:
            raise HTTPException(status_code=404, detail="Group configuration not found")
        
        return {
            "success": True,
            "message": "Group configuration updated successfully",
            "group_id": group_id,
            "config": updated_config
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating group configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")

@app.get("/api/config/groups/{group_id}")
async def get_group_configuration(group_id: int):
    """🔧 Obtener configuración de grupo específico"""
    try:
        config = await config_manager.get_group_config(group_id)
        
        if not config:
            raise HTTPException(status_code=404, detail="Group configuration not found")
        
        return {
            "success": True,
            "group_id": group_id,
            "config": config
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting group configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get configuration: {str(e)}")

@app.delete("/api/config/groups/{group_id}")
async def delete_group_configuration(group_id: int):
    """🔧 Eliminar configuración de grupo"""
    try:
        success = await config_manager.delete_group_config(group_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Group configuration not found")
        
        return {
            "success": True,
            "message": "Group configuration deleted successfully",
            "group_id": group_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting group configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

@app.get("/api/config/groups")
async def get_all_group_configurations():
    """🔧 Obtener todas las configuraciones de grupos"""
    try:
        configs = await config_manager.get_all_configs()
        
        return {
            "success": True,
            "total": len(configs),
            "groups": configs
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting all configurations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get configurations: {str(e)}")

@app.post("/api/config/validate_webhook")
async def validate_discord_webhook(request: WebhookValidationRequest):
    """🔧 Validar webhook de Discord"""
    try:
        logger.info(f"🧪 Validating webhook: {request.webhook_url[:50]}...")
        
        validation = await WebhookValidator.validate_webhook(request.webhook_url)
        
        return {
            "success": True,
            "webhook_url": request.webhook_url,
            "validation": validation
        }
        
    except Exception as e:
        logger.error(f"❌ Error validating webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

@app.post("/api/config/groups/{group_id}/enable")
async def enable_group(group_id: int):
    """🔧 Habilitar replicación para un grupo"""
    try:
        updates = GroupConfigUpdate(enabled=True)
        updated_config = await config_manager.update_group_config(group_id, updates)
        
        if not updated_config:
            raise HTTPException(status_code=404, detail="Group configuration not found")
        
        return {
            "success": True,
            "message": f"Group {group_id} enabled successfully",
            "group_id": group_id,
            "enabled": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error enabling group: {e}")
        raise HTTPException(status_code=500, detail=f"Enable failed: {str(e)}")

@app.post("/api/config/groups/{group_id}/disable")
async def disable_group(group_id: int):
    """🔧 Deshabilitar replicación para un grupo"""
    try:
        updates = GroupConfigUpdate(enabled=False)
        updated_config = await config_manager.update_group_config(group_id, updates)
        
        if not updated_config:
            raise HTTPException(status_code=404, detail="Group configuration not found")
        
        return {
            "success": True,
            "message": f"Group {group_id} disabled successfully",
            "group_id": group_id,
            "enabled": False
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error disabling group: {e}")
        raise HTTPException(status_code=500, detail=f"Disable failed: {str(e)}")

@app.get("/api/config/preview/{group_id}")
async def preview_group_configuration(group_id: int, sample_message: str = "Este es un mensaje de ejemplo"):
    """🔧 Preview de cómo se verá la configuración"""
    try:
        config = await config_manager.get_group_config(group_id)
        
        if not config:
            raise HTTPException(status_code=404, detail="Group configuration not found")
        
        # Simular procesamiento del mensaje
        processed_message = sample_message
        
        # Aplicar transformaciones si existen
        transformations = config.get("transformations", {})
        if transformations.get("add_prefix"):
            processed_message = f"{transformations['add_prefix']}{processed_message}"
        if transformations.get("add_suffix"):
            processed_message = f"{processed_message}{transformations['add_suffix']}"
        
        # Simular estructura del mensaje de Discord
        discord_preview = {
            "content": processed_message,
            "username": f"Telegram → {config['group_name']}",
            "embeds": [{
                "title": f"📱 {config['group_name']}",
                "description": processed_message,
                "color": 0x0099ff,
                "timestamp": datetime.now().isoformat(),
                "footer": {
                    "text": "Message Replicator"
                }
            }] if transformations.get("use_embeds", False) else None
        }
        
        return {
            "success": True,
            "group_id": group_id,
            "original_message": sample_message,
            "processed_message": processed_message,
            "discord_preview": discord_preview,
            "applied_transformations": transformations,
            "config": config
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error generating preview: {e}")
        raise HTTPException(status_code=500, detail=f"Preview failed: {str(e)}")

# ============= BATCH OPERATIONS =============

@app.post("/api/config/batch/enable")
async def batch_enable_groups(group_ids: List[int]):
    """🔧 Habilitar múltiples grupos en batch"""
    try:
        results = {"successful": 0, "failed": 0, "details": []}
        
        for group_id in group_ids:
            try:
                updates = GroupConfigUpdate(enabled=True)
                await config_manager.update_group_config(group_id, updates)
                results["successful"] += 1
                results["details"].append({"group_id": group_id, "status": "enabled"})
            except Exception as e:
                results["failed"] += 1
                results["details"].append({"group_id": group_id, "status": "failed", "error": str(e)})
        
        return {
            "success": True,
            "message": f"Batch operation completed: {results['successful']} enabled, {results['failed']} failed",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"❌ Error in batch enable: {e}")
        raise HTTPException(status_code=500, detail=f"Batch operation failed: {str(e)}")

@app.post("/api/config/batch/disable")
async def batch_disable_groups(group_ids: List[int]):
    """🔧 Deshabilitar múltiples grupos en batch"""
    try:
        results = {"successful": 0, "failed": 0, "details": []}
        
        for group_id in group_ids:
            try:
                updates = GroupConfigUpdate(enabled=False)
                await config_manager.update_group_config(group_id, updates)
                results["successful"] += 1
                results["details"].append({"group_id": group_id, "status": "disabled"})
            except Exception as e:
                results["failed"] += 1
                results["details"].append({"group_id": group_id, "status": "failed", "error": str(e)})
        
        return {
            "success": True,
            "message": f"Batch operation completed: {results['successful']} disabled, {results['failed']} failed",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"❌ Error in batch disable: {e}")
        raise HTTPException(status_code=500, detail=f"Batch operation failed: {str(e)}")

# ============= SYSTEM STATUS =============

@app.get("/api/config/system/status")
async def get_system_configuration_status():
    """🔧 Estado del sistema de configuración"""
    try:
        configs = await config_manager.get_all_configs()
        
        total_groups = len(configs)
        enabled_groups = sum(1 for config in configs.values() if config.get("enabled", True))
        disabled_groups = total_groups - enabled_groups
        
        # Estadísticas por webhook
        webhook_stats = {}
        for config in configs.values():
            webhook_url = config.get("webhook_url", "unknown")
            webhook_domain = webhook_url.split("/")[2] if "/" in webhook_url else "unknown"
            webhook_stats[webhook_domain] = webhook_stats.get(webhook_domain, 0) + 1
        
        return {
            "success": True,
            "system_status": {
                "total_groups": total_groups,
                "enabled_groups": enabled_groups,
                "disabled_groups": disabled_groups,
                "webhook_distribution": webhook_stats,
                "replicator_service_status": "running" if replicator_service else "stopped",
                "configuration_file": str(config_manager.config_file),
                "last_updated": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=f"System status failed: {str(e)}")

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
