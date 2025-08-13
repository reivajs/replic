#!/usr/bin/env python3
"""
📡 MESSAGE REPLICATOR REAL v5.0 - CÓDIGO COMPLETO
=================================================
Replicador REAL que SÍ conecta a Telegram y Discord
Funciona con tu .env existente - CÓDIGO COMPLETO
"""

import asyncio
import sys
import os
import json
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any, List, Optional

# Telegram imports
try:
    from telethon import TelegramClient, events
    from telethon.tl.types import User, Chat, Channel, MessageMediaPhoto, MessageMediaDocument
    from telethon.tl.functions.messages import GetDialogsRequest
    from telethon.tl.types import InputPeerEmpty
    TELETHON_AVAILABLE = True
except ImportError:
    print("⚠️ Telethon no disponible. Instalando...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "telethon", "cryptg"])
    try:
        from telethon import TelegramClient, events
        from telethon.tl.types import User, Chat, Channel, MessageMediaPhoto, MessageMediaDocument
        from telethon.tl.functions.messages import GetDialogsRequest
        from telethon.tl.types import InputPeerEmpty
        TELETHON_AVAILABLE = True
    except:
        TELETHON_AVAILABLE = False

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
import uvicorn
import httpx
import aiohttp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Logger
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============= CONFIGURATION =============

class Config:
    """Configuración desde .env"""
    
    def __init__(self):
        # Telegram config
        self.TELEGRAM_API_ID = int(os.getenv('TELEGRAM_API_ID', 0))
        self.TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH', '')
        self.TELEGRAM_PHONE = os.getenv('TELEGRAM_PHONE', '')
        self.TELEGRAM_SESSION = os.getenv('TELEGRAM_SESSION', 'replicator_session')
        
        # Load webhooks from .env
        self.WEBHOOKS = {}
        for key, value in os.environ.items():
            if key.startswith('WEBHOOK_'):
                try:
                    group_id = int(key.replace('WEBHOOK_', ''))
                    self.WEBHOOKS[group_id] = value
                except ValueError:
                    continue
        
        logger.info(f"🔧 Config loaded: {len(self.WEBHOOKS)} webhooks, Telegram ID: {self.TELEGRAM_API_ID}")
    
    def is_telegram_configured(self) -> bool:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/stats")
async def get_stats():
    """Obtener estadísticas REALES del replicador"""
    try:
        if not replicator_service:
            return {"error": "Service not initialized"}
        
        stats = await replicator_service.get_dashboard_stats()
        
        return {
            "service": "real_message_replicator",
            "data": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Stats error: {e}")
        return {"error": str(e)}

@app.get("/status")
async def get_status():
    """Estado detallado del servicio REAL"""
    try:
        if not replicator_service:
            return {"status": "not_initialized"}
        
        health = await replicator_service.get_health()
        
        return {
            "service": "real_message_replicator",
            "version": "5.0.0",
            "is_running": health["is_running"],
            "is_listening": health["is_listening"],
            "is_connected": health["is_connected"],
            "telegram_configured": health["telegram_configured"],
            "groups_configured": health["groups_configured"],
            "groups_from_env": health["groups_from_env"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": str(e)}

# ============= GROUPS ENDPOINT PARA GROUPS.HTML =============

@app.get("/api/groups")
async def get_monitored_groups():
    """Obtener grupos monitoreados (para groups.html)"""
    try:
        if not replicator_service or not replicator_service.is_connected:
            return {
                "success": False,
                "error": "Telegram not connected",
                "groups": []
            }
        
        groups = await replicator_service.get_monitored_groups()
        
        return {
            "success": True,
            "groups": groups,
            "total": len(groups)
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting groups: {e}")
        return {
            "success": False,
            "error": str(e),
            "groups": []
        }

# ============= CONFIGURATION ENDPOINTS =============

@app.post("/api/config/add_group")
async def add_group_configuration(config_req: GroupConfigRequest):
    """🔧 Añadir nueva configuración de grupo"""
    try:
        logger.info(f"📝 Adding group configuration: {config_req.group_id} - {config_req.group_name}")
        
        # Validar webhook primero
        validation = await WebhookValidator.validate_webhook(config_req.webhook_url)
        if not validation["valid"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid webhook: {validation['message']}"
            )
        
        # Guardar configuración
        saved_config = await replicator_service.add_group_config(config_req)
        
        return {
            "success": True,
            "message": "Group configured successfully",
            "group_id": config_req.group_id,
            "group_name": config_req.group_name,
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
        config_data = await replicator_service.get_group_config(group_id)
        
        if not config_data:
            raise HTTPException(status_code=404, detail="Group configuration not found")
        
        return {
            "success": True,
            "group_id": group_id,
            "config": config_data
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
        config_data = await replicator_service.get_group_config(group_id)
        
        if not config_data:
            raise HTTPException(status_code=404, detail="Group configuration not found")
        
        # Simular procesamiento del mensaje
        processed_message = sample_message
        
        # Aplicar transformaciones si existen
        transformations = config_data.get("transformations", {})
        if transformations.get("add_prefix"):
            processed_message = f"{transformations['add_prefix']}{processed_message}"
        if transformations.get("add_suffix"):
            processed_message = f"{processed_message}{transformations['add_suffix']}"
        
        # Simular estructura del mensaje de Discord
        discord_preview = {
            "content": processed_message,
            "username": f"Telegram → {config_data['group_name']}",
            "embeds": [{
                "title": f"📱 {config_data['group_name']}",
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
            "config": config_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error generating preview: {e}")
        raise HTTPException(status_code=500, detail=f"Preview failed: {str(e)}")

@app.get("/api/config/system/status")
async def get_system_configuration_status():
    """🔧 Estado del sistema de configuración"""
    try:
        configs = await replicator_service.get_all_configs()
        groups = await replicator_service.get_monitored_groups()
        
        total_groups = len(groups)
        enabled_groups = sum(1 for group in groups if group.get("enabled", True))
        disabled_groups = total_groups - enabled_groups
        
        # Estadísticas por webhook
        webhook_stats = {}
        for group in groups:
            webhook_url = group.get("webhook_url", "unknown")
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
                "telegram_connected": replicator_service.is_connected if replicator_service else False,
                "last_updated": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=f"System status failed: {str(e)}")

# ============= TELEGRAM INTEGRATION ENDPOINTS =============

@app.get("/api/telegram/chats")
async def get_telegram_chats():
    """🔧 Obtener chats de Telegram para Discovery integration"""
    try:
        if not replicator_service or not replicator_service.is_connected:
            raise HTTPException(status_code=503, detail="Telegram not connected")
        
        # Obtener diálogos de Telegram
        dialogs = []
        if replicator_service.client:
            try:
                # Obtener los últimos 100 diálogos
                async for dialog in replicator_service.client.iter_dialogs(limit=100):
                    entity = dialog.entity
                    
                    chat_data = {
                        "id": entity.id,
                        "title": getattr(entity, 'title', None) or getattr(entity, 'first_name', f'Chat {entity.id}'),
                        "type": "private" if hasattr(entity, 'first_name') else ("channel" if getattr(entity, 'broadcast', False) else "group"),
                        "username": getattr(entity, 'username', None),
                        "participants_count": getattr(entity, 'participants_count', None),
                        "is_verified": getattr(entity, 'verified', False),
                        "is_scam": getattr(entity, 'scam', False),
                        "has_photo": getattr(entity, 'photo', None) is not None,
                        "discovered_at": datetime.now().isoformat()
                    }
                    
                    dialogs.append(chat_data)
                    
            except Exception as e:
                logger.error(f"❌ Error getting Telegram chats: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to get chats: {str(e)}")
        
        return {
            "success": True,
            "chats": dialogs,
            "total": len(dialogs)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in get_telegram_chats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get Telegram chats: {str(e)}")

@app.get("/api/telegram/status")
async def get_telegram_status():
    """🔧 Estado de conexión a Telegram"""
    try:
        if not replicator_service:
            return {
                "connected": False,
                "error": "Service not initialized"
            }
        
        health = await replicator_service.get_health()
        
        return {
            "connected": health["is_connected"],
            "configured": health["telegram_configured"],
            "listening": health["is_listening"],
            "uptime_seconds": health["uptime_seconds"],
            "client_info": {
                "session_file": f"sessions/{config.TELEGRAM_SESSION}.session",
                "api_id": config.TELEGRAM_API_ID,
                "phone": config.TELEGRAM_PHONE[:3] + "***" + config.TELEGRAM_PHONE[-3:] if config.TELEGRAM_PHONE else None
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting Telegram status: {e}")
        return {
            "connected": False,
            "error": str(e)
        }

# ============= WEBHOOK MANAGEMENT =============

@app.get("/api/webhooks")
async def get_configured_webhooks():
    """🔧 Obtener webhooks configurados"""
    try:
        webhooks = []
        
        # Webhooks desde .env
        for group_id, webhook_url in config.WEBHOOKS.items():
            webhooks.append({
                "group_id": group_id,
                "webhook_url": webhook_url,
                "source": "env",
                "enabled": True
            })
        
        # Webhooks desde configuraciones dinámicas
        configs = await replicator_service.get_all_configs()
        for group_id, group_config in configs.items():
            webhooks.append({
                "group_id": int(group_id),
                "webhook_url": group_config["webhook_url"],
                "source": "api",
                "enabled": group_config.get("enabled", True),
                "group_name": group_config.get("group_name"),
                "created_at": group_config.get("created_at"),
                "updated_at": group_config.get("updated_at")
            })
        
        return {
            "success": True,
            "webhooks": webhooks,
            "total": len(webhooks)
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting webhooks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get webhooks: {str(e)}")

@app.post("/api/webhooks/test")
async def test_webhook(request: Request):
    """🔧 Test webhook específico"""
    try:
        data = await request.json()
        webhook_url = data.get("webhook_url")
        
        if not webhook_url:
            raise HTTPException(status_code=400, detail="webhook_url is required")
        
        validation = await WebhookValidator.validate_webhook(webhook_url)
        
        return {
            "success": validation["valid"],
            "validation": validation
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error testing webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Webhook test failed: {str(e)}")

if __name__ == "__main__":
    # Crear directorio de sesiones
    Path("sessions").mkdir(exist_ok=True)
    
    config_info = {
        "host": "0.0.0.0",
        "port": 8001,
        "reload": False,
        "log_level": "info"
    }
    
    print("🚀 Starting REAL Message Replicator Microservice v5.0...")
    print(f"   📡 Service: REAL Message Replicator")
    print(f"   🌐 URL: http://{config_info['host']}:{config_info['port']}")
    print(f"   📚 Docs: http://{config_info['host']}:{config_info['port']}/docs")
    print(f"   🏥 Health: http://{config_info['host']}:{config_info['port']}/health")
    print(f"   📱 Telegram configured: {config.is_telegram_configured()}")
    print(f"   🔗 Webhooks loaded: {len(config.WEBHOOKS)}")
    
    uvicorn.run(app, **config_info) self.TELEGRAM_API_ID and self.TELEGRAM_API_HASH and self.TELEGRAM_PHONE

config = Config()

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

# ============= WEBHOOK VALIDATOR =============

class WebhookValidator:
    """Validador REAL de webhooks de Discord"""
    
    @staticmethod
    async def validate_webhook(webhook_url: str) -> Dict[str, Any]:
        """Validar webhook enviando mensaje de prueba REAL"""
        try:
            test_payload = {
                "content": "🧪 **Test de configuración** - Este webhook está funcionando correctamente!",
                "username": "Replicator Test",
                "embeds": [{
                    "title": "✅ Webhook Validation",
                    "description": "Este webhook ha sido configurado exitosamente",
                    "color": 0x00ff00,
                    "timestamp": datetime.now().isoformat(),
                    "footer": {
                        "text": "Real Message Replicator Service"
                    }
                }]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=test_payload) as response:
                    if response.status == 204:
                        return {
                            "valid": True,
                            "message": "Webhook válido y funcionando",
                            "test_sent": True,
                            "response_status": response.status
                        }
                    else:
                        return {
                            "valid": False,
                            "message": f"Webhook respondió con código {response.status}",
                            "test_sent": False,
                            "response_status": response.status
                        }
                        
        except Exception as e:
            return {
                "valid": False,
                "message": f"Error validando webhook: {str(e)}",
                "test_sent": False,
                "error": str(e)
            }

# ============= REAL TELEGRAM SERVICE =============

class RealTelegramReplicator:
    """Replicador REAL de Telegram que SÍ funciona"""
    
    def __init__(self):
        self.client = None
        self.is_running = False
        self.is_listening = False
        self.is_connected = False
        
        self.stats = {
            'messages_received': 0,
            'messages_replicated': 0,
            'messages_filtered': 0,
            'images_processed': 0,
            'videos_processed': 0,
            'errors': 0,
            'start_time': datetime.now(),
            'groups_configured': 0,
            'groups_active': 0
        }
        
        self.groups_config = {}
        self.active_webhooks = config.WEBHOOKS.copy()
        
        logger.info("📡 Real Telegram Replicator inicializado")
    
    async def initialize(self) -> bool:
        """Inicializar conexión REAL a Telegram"""
        try:
            if not TELETHON_AVAILABLE:
                logger.error("❌ Telethon no disponible")
                return False
            
            if not config.is_telegram_configured():
                logger.error("❌ Configuración de Telegram incompleta en .env")
                logger.error(f"   API_ID: {config.TELEGRAM_API_ID}")
                logger.error(f"   API_HASH: {'***' if config.TELEGRAM_API_HASH else 'MISSING'}")
                logger.error(f"   PHONE: {'***' if config.TELEGRAM_PHONE else 'MISSING'}")
                return False
            
            # Crear cliente de Telegram REAL
            logger.info("📱 Conectando a Telegram...")
            
            self.client = TelegramClient(
                f"sessions/{config.TELEGRAM_SESSION}",
                config.TELEGRAM_API_ID,
                config.TELEGRAM_API_HASH
            )
            
            # Conectar
            await self.client.start(phone=config.TELEGRAM_PHONE)
            me = await self.client.get_me()
            
            self.is_connected = True
            self.is_running = True
            
            logger.info(f"✅ Conectado a Telegram como: {me.first_name} (@{me.username or 'sin_username'})")
            
            # Cargar configuraciones
            await self._load_configurations()
            
            # Setup event handlers
            self._setup_event_handlers()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error conectando a Telegram: {e}")
            self.is_connected = False
            return False
    
    def _setup_event_handlers(self):
        """Configurar handlers de eventos REALES"""
        if not self.client:
            return
        
        @self.client.on(events.NewMessage)
        async def handle_new_message(event):
            await self._handle_telegram_message(event)
        
        logger.info("📡 Event handlers configurados")
    
    async def _handle_telegram_message(self, event):
        """Handler REAL para mensajes de Telegram"""
        try:
            chat_id = event.chat_id
            message = event.message
            
            # Actualizar stats
            self.stats['messages_received'] += 1
            
            # Verificar si hay webhook configurado
            webhook_url = None
            
            # Buscar en configuraciones dinámicas
            group_config = self.groups_config.get(str(chat_id))
            if group_config and group_config.get('enabled', True):
                webhook_url = group_config['webhook_url']
            # Buscar en webhooks estáticos (.env)
            elif chat_id in self.active_webhooks:
                webhook_url = self.active_webhooks[chat_id]
            
            if not webhook_url:
                logger.debug(f"📋 No webhook configurado para grupo {chat_id}")
                return
            
            # Obtener info del chat
            chat_info = await self._get_chat_info(chat_id)
            
            # Procesar según tipo de mensaje
            success = False
            
            if message.text and not message.media:
                success = await self._send_text_to_discord(webhook_url, message.text, chat_info)
            elif message.photo:
                success = await self._send_photo_to_discord(webhook_url, message, chat_info)
            elif message.video:
                success = await self._send_video_to_discord(webhook_url, message, chat_info)
            elif message.document:
                success = await self._send_document_to_discord(webhook_url, message, chat_info)
            else:
                # Otros tipos de mensajes
                text = message.text or "[Mensaje multimedia]"
                success = await self._send_text_to_discord(webhook_url, text, chat_info)
            
            # Actualizar estadísticas
            if success:
                self.stats['messages_replicated'] += 1
                logger.info(f"✅ Mensaje replicado: {chat_info['name']} → Discord")
            else:
                self.stats['errors'] += 1
                logger.warning(f"❌ Error replicando mensaje de {chat_info['name']}")
                
        except Exception as e:
            logger.error(f"❌ Error procesando mensaje: {e}")
            self.stats['errors'] += 1
    
    async def _send_text_to_discord(self, webhook_url: str, text: str, chat_info: Dict) -> bool:
        """Enviar mensaje de texto a Discord"""
        try:
            payload = {
                "content": text[:2000],  # Discord limit
                "username": f"📱 {chat_info['name']}"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    return response.status == 204
                    
        except Exception as e:
            logger.error(f"❌ Error enviando texto a Discord: {e}")
            return False
    
    async def _send_photo_to_discord(self, webhook_url: str, message, chat_info: Dict) -> bool:
        """Enviar foto a Discord"""
        try:
            # Descargar imagen
            photo_bytes = await message.download_media(bytes)
            if not photo_bytes:
                return False
            
            # Preparar caption
            caption = message.text or ""
            full_caption = f"📷 Imagen de **{chat_info['name']}**"
            if caption:
                full_caption += f"\n\n{caption}"
            
            # Enviar como archivo
            data = aiohttp.FormData()
            data.add_field('content', full_caption[:2000])  # Discord limit
            data.add_field('file', photo_bytes, filename='image.jpg', content_type='image/jpeg')
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, data=data) as response:
                    if response.status == 200:
                        self.stats['images_processed'] += 1
                        return True
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error enviando foto a Discord: {e}")
            return False
    
    async def _send_video_to_discord(self, webhook_url: str, message, chat_info: Dict) -> bool:
        """Enviar video a Discord"""
        try:
            # Verificar tamaño
            if message.video and message.video.size:
                size_mb = message.video.size / (1024 * 1024)
                if size_mb > 8:  # Discord limit
                    # Enviar solo caption si es muy grande
                    caption = message.text or ""
                    text = f"🎬 Video de **{chat_info['name']}** (demasiado grande para Discord: {size_mb:.1f}MB)\n\n{caption}"
                    return await self._send_text_to_discord(webhook_url, text, chat_info)
            
            # Descargar video
            video_bytes = await message.download_media(bytes)
            if not video_bytes:
                return False
            
            # Preparar caption
            caption = message.text or ""
            full_caption = f"🎬 Video de **{chat_info['name']}**"
            if caption:
                full_caption += f"\n\n{caption}"
            
            # Enviar como archivo
            data = aiohttp.FormData()
            data.add_field('content', full_caption[:2000])  # Discord limit
            data.add_field('file', video_bytes, filename='video.mp4', content_type='video/mp4')
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, data=data) as response:
                    if response.status == 200:
                        self.stats['videos_processed'] += 1
                        return True
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error enviando video a Discord: {e}")
            return False
    
    async def _send_document_to_discord(self, webhook_url: str, message, chat_info: Dict) -> bool:
        """Enviar documento a Discord"""
        try:
            # Para documentos, enviar solo descripción por ahora
            caption = message.text or ""
            doc_name = getattr(message.document, 'file_name', 'Documento')
            size_mb = getattr(message.document, 'size', 0) / (1024 * 1024)
            
            text = f"📎 **{chat_info['name']}** compartió: {doc_name} ({size_mb:.1f}MB)\n\n{caption}"
            return await self._send_text_to_discord(webhook_url, text, chat_info)
            
        except Exception as e:
            logger.error(f"❌ Error enviando documento a Discord: {e}")
            return False
    
    async def _get_chat_info(self, chat_id: int) -> Dict[str, Any]:
        """Obtener información REAL del chat"""
        try:
            entity = await self.client.get_entity(chat_id)
            
            if isinstance(entity, User):
                name = f"{entity.first_name or ''} {entity.last_name or ''}".strip()
                if not name:
                    name = entity.username or f"User {entity.id}"
            elif isinstance(entity, (Chat, Channel)):
                name = entity.title or f"Chat {entity.id}"
            else:
                name = f"Chat {chat_id}"
            
            return {
                'name': name,
                'type': type(entity).__name__,
                'id': chat_id
            }
            
        except Exception as e:
            logger.warning(f"⚠️ No se pudo obtener info de {chat_id}: {e}")
            return {
                'name': f"Chat {chat_id}",
                'type': 'Unknown',
                'id': chat_id
            }
    
    async def start_listening(self):
        """Iniciar escucha REAL de mensajes"""
        if not self.is_connected or not self.client:
            logger.error("❌ Cliente de Telegram no conectado")
            return
        
        try:
            logger.info("👂 Iniciando escucha REAL de mensajes de Telegram...")
            self.is_listening = True
            
            # Mostrar grupos monitoreados
            total_webhooks = len(self.active_webhooks) + len([g for g in self.groups_config.values() if g.get('enabled')])
            logger.info(f"📊 Monitoreando {total_webhooks} grupos/canales")
            
            for group_id in self.active_webhooks.keys():
                try:
                    chat_info = await self._get_chat_info(group_id)
                    logger.info(f"   👥 {chat_info['name']} ({group_id})")
                except:
                    logger.info(f"   👥 Grupo {group_id}")
            
            # Ejecutar cliente de Telegram
            await self.client.run_until_disconnected()
            
        except Exception as e:
            logger.error(f"❌ Error en escucha: {e}")
        finally:
            self.is_listening = False
            logger.info("🛑 Escucha detenida")
    
    async def stop(self):
        """Detener servicio"""
        try:
            logger.info("🛑 Deteniendo Real Telegram Replicator...")
            self.is_running = False
            self.is_listening = False
            
            if self.client and self.client.is_connected():
                await self.client.disconnect()
                self.is_connected = False
                logger.info("📱 Cliente de Telegram desconectado")
            
            await self._save_configurations()
            logger.info("✅ Real Telegram Replicator detenido")
            
        except Exception as e:
            logger.error(f"❌ Error deteniendo servicio: {e}")
    
    async def get_health(self) -> Dict[str, Any]:
        """Health check REAL"""
        return {
            "status": "healthy" if self.is_running else "stopped",
            "service": "real_telegram_replicator",
            "is_running": self.is_running,
            "is_listening": self.is_listening,
            "is_connected": self.is_connected,
            "telegram_configured": config.is_telegram_configured(),
            "groups_configured": len(self.groups_config),
            "groups_from_env": len(self.active_webhooks),
            "uptime_seconds": (datetime.now() - self.stats['start_time']).total_seconds()
        }
    
    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """Estadísticas REALES"""
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
            "groups_configured": len(self.groups_config),
            "groups_from_env": len(self.active_webhooks),
            "total_groups": len(self.groups_config) + len(self.active_webhooks),
            "is_connected": self.is_connected,
            "telegram_configured": config.is_telegram_configured()
        }
    
    async def get_monitored_groups(self) -> List[Dict[str, Any]]:
        """Obtener lista de grupos monitoreados"""
        groups = []
        
        # Grupos de .env
        for group_id, webhook_url in self.active_webhooks.items():
            try:
                chat_info = await self._get_chat_info(group_id)
                groups.append({
                    "id": group_id,
                    "title": chat_info['name'],
                    "type": chat_info.get('type', 'Unknown'),
                    "webhook_url": webhook_url,
                    "enabled": True,
                    "source": "env",
                    "is_active": True,
                    "messages_count": 0,  # TODO: implementar contador
                    "last_activity": datetime.now().isoformat()
                })
            except Exception as e:
                groups.append({
                    "id": group_id,
                    "title": f"Grupo {group_id}",
                    "type": "Unknown",
                    "webhook_url": webhook_url,
                    "enabled": True,
                    "source": "env",
                    "is_active": False,
                    "error": str(e)
                })
        
        # Grupos configurados dinámicamente
        for group_id, group_config in self.groups_config.items():
            if int(group_id) not in self.active_webhooks:  # Evitar duplicados
                groups.append({
                    "id": int(group_id),
                    "title": group_config['group_name'],
                    "type": "Configured",
                    "webhook_url": group_config['webhook_url'],
                    "enabled": group_config.get('enabled', True),
                    "source": "api",
                    "is_active": group_config.get('enabled', True),
                    "filters": group_config.get('filters', {}),
                    "transformations": group_config.get('transformations', {}),
                    "created_at": group_config.get('created_at'),
                    "updated_at": group_config.get('updated_at')
                })
        
        return groups
    
    # Métodos de configuración
    async def add_group_config(self, config_req: GroupConfigRequest) -> Dict[str, Any]:
        """Añadir configuración de grupo"""
        group_key = str(config_req.group_id)
        
        self.groups_config[group_key] = {
            "group_id": config_req.group_id,
            "group_name": config_req.group_name,
            "webhook_url": config_req.webhook_url,
            "enabled": config_req.enabled,
            "filters": config_req.filters,
            "transformations": config_req.transformations,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        await self._save_configurations()
        logger.info(f"✅ Grupo configurado: {config_req.group_name} ({config_req.group_id})")
        
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
        except Exception as e:
            logger.error(f"❌ Error guardando configuraciones: {e}")

# ============= FASTAPI APP =============

# Instancia global del servicio REAL
replicator_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manejo del ciclo de vida del microservicio REAL"""
    global replicator_service
    
    try:
        logger.info("🚀 Iniciando REAL Message Replicator Microservice...")
        
        # Crear e inicializar servicio REAL
        replicator_service = RealTelegramReplicator()
        success = await replicator_service.initialize()
        
        if success:
            # Iniciar listening en background
            asyncio.create_task(replicator_service.start_listening())
            logger.info("✅ REAL Message Replicator Service iniciado")
        else:
            logger.error("❌ Error inicializando REAL Message Replicator Service")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Error en REAL Message Replicator: {e}")
    finally:
        if replicator_service:
            await replicator_service.stop()
        logger.info("🛑 REAL Message Replicator detenido")

# Crear aplicación FastAPI
app = FastAPI(
    title="📡 REAL Message Replicator Microservice v5.0",
    description="Replicador REAL que conecta a Telegram y Discord",
    version="5.0.0",
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
    """Información del microservicio REAL"""
    return {
        "service": "REAL Message Replicator Microservice",
        "version": "5.0.0",
        "description": "Replicador REAL que conecta a Telegram y Discord",
        "status": "running" if replicator_service and replicator_service.is_running else "initializing",
        "features": ["real_telegram_connection", "real_discord_webhooks", "group_configuration", "real_time_stats"],
        "telegram_configured": config.is_telegram_configured(),
        "webhooks_loaded": len(config.WEBHOOKS)
    }

@app.get("/health")
async def health_check():
    """Health check del servicio REAL"""
    try:
        if not replicator_service:
            return {
                "status": "initializing",
                "timestamp": datetime.now().isoformat()
            }
        
        health_data = await replicator_service.get_health()
        
        return {
            "status": "healthy" if health_data["is_connected"] else "degraded",
            "service": "real_message_replicator",
            "version": "5.0.0",
            "replicator_health": health_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Health check error: {e}")
        return