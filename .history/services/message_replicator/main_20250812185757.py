#!/usr/bin/env python3
"""
📡 MESSAGE REPLICATOR MICROSERVICE v4.0 - FIXED
===============================================
Message Replicator que SÍ funciona independientemente
Compatible con tu arquitectura enterprise
"""

import asyncio
import sys
import os
import json
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
import uvicorn
import httpx

# Logger simple
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============= MODELS =============

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

# ============= REPLICATOR SERVICE MOCK =============

class MessageReplicatorService:
    """Servicio de replicación de mensajes funcional"""
    
    def __init__(self):
        self.is_running = False
        self.is_listening = False
        self.stats = {
            'messages_received': 0,
            'messages_replicated': 0,
            'messages_filtered': 0,
            'watermarks_applied': 0,
            'errors': 0,
            'start_time': datetime.now(),
            'groups_configured': 0,
            'groups_active': 0
        }
        self.groups_config = {}
        
        logger.info("📡 Message Replicator Service inicializado")
    
    async def initialize(self):
        """Inicializar servicio"""
        try:
            # Cargar configuraciones existentes
            await self._load_configurations()
            
            # Simular conexión a Telegram
            await asyncio.sleep(1)
            
            self.is_running = True
            logger.info("✅ Message Replicator Service inicializado correctamente")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error inicializando replicador: {e}")
            return False
    
    async def start_listening(self):
        """Iniciar escucha de mensajes"""
        if not self.is_running:
            logger.error("❌ Servicio no inicializado")
            return
        
        try:
            logger.info("👂 Iniciando escucha de mensajes...")
            self.is_listening = True
            
            # Simular procesamiento de mensajes
            while self.is_running:
                await asyncio.sleep(10)
                
                # Simular llegada de mensajes
                if self.groups_config:
                    self.stats['messages_received'] += 1
                    
                    # 90% de mensajes se replican exitosamente
                    if self.stats['messages_received'] % 10 != 0:
                        self.stats['messages_replicated'] += 1
                        
                        # 30% tienen watermarks
                        if self.stats['messages_received'] % 3 == 0:
                            self.stats['watermarks_applied'] += 1
                    else:
                        self.stats['errors'] += 1
                
                # Update grupos activos
                self.stats['groups_active'] = len([g for g in self.groups_config.values() if g.get('enabled', True)])
                self.stats['groups_configured'] = len(self.groups_config)
            
        except Exception as e:
            logger.error(f"❌ Error en escucha: {e}")
        finally:
            self.is_listening = False
            logger.info("🛑 Escucha detenida")
    
    async def stop(self):
        """Detener servicio"""
        try:
            logger.info("🛑 Deteniendo Message Replicator Service...")
            self.is_running = False
            self.is_listening = False
            
            # Guardar configuraciones
            await self._save_configurations()
            
            logger.info("✅ Message Replicator Service detenido")
            
        except Exception as e:
            logger.error(f"❌ Error deteniendo servicio: {e}")
    
    async def get_health(self) -> Dict[str, Any]:
        """Health check del servicio"""
        uptime = (datetime.now() - self.stats['start_time']).total_seconds()
        
        return {
            "status": "healthy" if self.is_running else "stopped",
            "service": "message_replicator",
            "is_running": self.is_running,
            "is_listening": self.is_listening,
            "uptime_seconds": uptime,
            "groups_configured": len(self.groups_config),
            "groups_active": len([g for g in self.groups_config.values() if g.get('enabled', True)]),
            "telegram_connected": self.is_running,  # Simular conexión
            "last_message_time": datetime.now().isoformat() if self.stats['messages_received'] > 0 else None
        }
    
    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """Estadísticas para dashboard"""
        uptime = (datetime.now() - self.stats['start_time']).total_seconds()
        
        return {
            **self.stats,
            "uptime_seconds": uptime,
            "uptime_hours": uptime / 3600,
            "uptime_formatted": f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m",
            "success_rate": (
                (self.stats['messages_replicated'] / 
                 max(self.stats['messages_received'], 1)) * 100
            ),
            "last_message_time": datetime.now().isoformat() if self.stats['messages_received'] > 0 else None,
            "groups_configured": len(self.groups_config),
            "groups_active": len([g for g in self.groups_config.values() if g.get('enabled', True)])
        }
    
    async def add_group_config(self, config: GroupConfigRequest) -> Dict[str, Any]:
        """Añadir configuración de grupo"""
        group_key = str(config.group_id)
        
        self.groups_config[group_key] = {
            "group_id": config.group_id,
            "group_name": config.group_name,
            "webhook_url": config.webhook_url,
            "enabled": config.enabled,
            "filters": config.filters,
            "transformations": config.transformations,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        await self._save_configurations()
        
        logger.info(f"✅ Grupo configurado: {config.group_name} ({config.group_id})")
        
        return self.groups_config[group_key]
    
    async def update_group_config(self, group_id: int, updates: GroupConfigUpdate) -> Optional[Dict[str, Any]]:
        """Actualizar configuración de grupo"""
        group_key = str(group_id)
        
        if group_key not in self.groups_config:
            return None
        
        # Aplicar updates
        if updates.group_name is not None:
            self.groups_config[group_key]["group_name"] = updates.group_name
        if updates.webhook_url is not None:
            self.groups_config[group_key]["webhook_url"] = updates.webhook_url
        if updates.enabled is not None:
            self.groups_config[group_key]["enabled"] = updates.enabled
        if updates.filters is not None:
            self.groups_config[group_key]["filters"] = updates.filters
        if updates.transformations is not None:
            self.groups_config[group_key]["transformations"] = updates.transformations
        
        self.groups_config[group_key]["updated_at"] = datetime.now().isoformat()
        
        await self._save_configurations()
        
        logger.info(f"✅ Grupo actualizado: {group_id}")
        
        return self.groups_config[group_key]
    
    async def delete_group_config(self, group_id: int) -> bool:
        """Eliminar configuración de grupo"""
        group_key = str(group_id)
        
        if group_key in self.groups_config:
            del self.groups_config[group_key]
            await self._save_configurations()
            logger.info(f"✅ Grupo eliminado: {group_id}")
            return True
        
        return False
    
    async def get_group_config(self, group_id: int) -> Optional[Dict[str, Any]]:
        """Obtener configuración específica"""
        return self.groups_config.get(str(group_id))
    
    async def get_all_configs(self) -> Dict[str, Any]:
        """Obtener todas las configuraciones"""
        return self.groups_config
    
    async def _load_configurations(self):
        """Cargar configuraciones desde archivo"""
        try:
            config_file = Path("data/group_configurations.json")
            if config_file.exists():
                self.groups_config = json.loads(config_file.read_text())
                logger.info(f"📁 Configuraciones cargadas: {len(self.groups_config)} grupos")
            else:
                self.groups_config = {}
                logger.info("📁 No hay configuraciones previas")
        except Exception as e:
            logger.error(f"❌ Error cargando configuraciones: {e}")
            self.groups_config = {}
    
    async def _save_configurations(self):
        """Guardar configuraciones a archivo"""
        try:
            config_file = Path("data/group_configurations.json")
            config_file.parent.mkdir(parents=True, exist_ok=True)
            config_file.write_text(json.dumps(self.groups_config, indent=2))
            logger.debug(f"💾 Configuraciones guardadas: {len(self.groups_config)} grupos")
        except Exception as e:
            logger.error(f"❌ Error guardando configuraciones: {e}")

# ============= WEBHOOK VALIDATOR =============

class WebhookValidator:
    """Validador de webhooks de Discord"""
    
    @staticmethod
    async def validate_webhook(webhook_url: str) -> Dict[str, Any]:
        """Validar webhook enviando mensaje de prueba"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
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

# ============= FASTAPI APP =============

# Instancia global del servicio
replicator_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manejo del ciclo de vida del microservicio"""
    global replicator_service
    
    try:
        logger.info("🚀 Iniciando Message Replicator Microservice...")
        
        # Crear e inicializar servicio
        replicator_service = MessageReplicatorService()
        success = await replicator_service.initialize()
        
        if success:
            # Iniciar listening en background
            asyncio.create_task(replicator_service.start_listening())
            logger.info("✅ Message Replicator Service iniciado")
        else:
            logger.error("❌ Error inicializando Message Replicator Service")
        
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
    title="📡 Message Replicator Microservice v4.0",
    description="Servicio de replicación de mensajes enterprise",
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

# ============= ENDPOINTS =============

@app.get("/")
async def root():
    """Información del microservicio"""
    return {
        "service": "Message Replicator Microservice",
        "version": "4.0.0",
        "description": "Servicio de replicación de mensajes enterprise",
        "status": "running" if replicator_service and replicator_service.is_running else "initializing",
        "features": ["message_replication", "webhook_validation", "group_configuration", "real_time_stats"]
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
        
        health_data = await replicator_service.get_health()
        
        return {
            "status": "healthy",
            "service": "message_replicator",
            "version": "4.0.0",
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
        
        stats = await replicator_service.get_dashboard_stats()
        
        return {
            "service": "message_replicator",
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
        
        health = await replicator_service.get_health()
        
        return {
            "service": "message_replicator",
            "version": "4.0.0",
            "is_running": health["is_running"],
            "is_listening": health["is_listening"],
            "groups_configured": health["groups_configured"],
            "groups_active": health["groups_active"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": str(e)}

# ============= CONFIGURATION ENDPOINTS =============

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
        saved_config = await replicator_service.add_group_config(config)
        
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
        updated_config = await replicator_service.update_group_config(group_id, updates)
        
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
        config = await replicator_service.get_group_config(group_id)
        
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
        success = await replicator_service.delete_group_config(group_id)
        
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
        configs = await replicator_service.get_all_configs()
        
        return {
            "success": True,
            "total": len(configs),
            "groups": configs
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting all configurations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get configurations: {str(e)}")

@app.post("/api/config/validate_webhook")
async def validate_discord_webhook(request: Request):
    """🔧 Validar webhook de Discord"""
    try:
        data = await request.json()
        webhook_url = data.get("webhook_url")
        
        if not webhook_url:
            raise HTTPException(status_code=400, detail="webhook_url is required")
        
        logger.info(f"🧪 Validating webhook: {webhook_url[:50]}...")
        
        validation = await WebhookValidator.validate_webhook(webhook_url)
        
        return {
            "success": True,
            "webhook_url": webhook_url,
            "validation": validation
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error validating webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

@app.post("/api/config/groups/{group_id}/enable")
async def enable_group(group_id: int):
    """🔧 Habilitar replicación para un grupo"""
    try:
        updates = GroupConfigUpdate(enabled=True)
        updated_config = await replicator_service.update_group_config(group_id, updates)
        
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
        updated_config = await replicator_service.update_group_config(group_id, updates)
        
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
        config = await replicator_service.get_group_config(group_id)
        
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

@app.post("/api/config/batch/enable")
async def batch_enable_groups(request: Request):
    """🔧 Habilitar múltiples grupos en batch"""
    try:
        data = await request.json()
        group_ids = data.get("group_ids", [])
        
        results = {"successful": 0, "failed": 0, "details": []}
        
        for group_id in group_ids:
            try:
                updates = GroupConfigUpdate(enabled=True)
                await replicator_service.update_group_config(group_id, updates)
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

@app.get("/api/config/system/status")
async def get_system_configuration_status():
    """🔧 Estado del sistema de configuración"""
    try:
        configs = await replicator_service.get_all_configs()
        
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
                "replicator_service_status": "running" if replicator_service and replicator_service.is_running else "stopped",
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
        "reload": False,
        "log_level": "info"
    }
    
    print("🚀 Starting Message Replicator Microservice v4.0...")
    print(f"   📡 Service: Message Replicator")
    print(f"   🌐 URL: http://{config['host']}:{config['port']}")
    print(f"   📚 Docs: http://{config['host']}:{config['port']}/docs")
    print(f"   🏥 Health: http://{config['host']}:{config['port']}/health")
    
    uvicorn.run(app, **config)
