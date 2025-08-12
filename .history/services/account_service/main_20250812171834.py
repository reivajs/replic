# =====================================================
# UNIVERSAL REPLICATION CENTER - BACKEND ARCHITECTURE
# =====================================================
# Microservices modulares y escalables para SaaS multi-tenant

# ================== 1. ACCOUNT SERVICE ==================
# services/account_service/main.py

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio
import aiohttp
from telethon import TelegramClient
from telethon.sessions import StringSession
import logging

# Database setup
DATABASE_URL = "sqlite:///./accounts.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ========== MODELS ==========

class TenantAccount(Base):
    """Multi-tenant account model"""
    __tablename__ = "tenant_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, unique=True, index=True)
    company_name = Column(String)
    email = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    subscription_tier = Column(String, default="starter")  # starter, pro, enterprise
    max_telegram_accounts = Column(Integer, default=1)
    max_flows = Column(Integer, default=10)
    
    # Relationships
    telegram_accounts = relationship("TelegramAccount", back_populates="tenant")
    discord_webhooks = relationship("DiscordWebhook", back_populates="tenant")
    flows = relationship("ReplicationFlow", back_populates="tenant")

class TelegramAccount(Base):
    """Telegram account per tenant"""
    __tablename__ = "telegram_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, ForeignKey("tenant_accounts.tenant_id"))
    phone_number = Column(String)
    api_id = Column(String)
    api_hash = Column(String)
    session_string = Column(String)  # Encrypted session
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_scan = Column(DateTime)
    groups_count = Column(Integer, default=0)
    
    tenant = relationship("TenantAccount", back_populates="telegram_accounts")

class DiscordWebhook(Base):
    """Discord webhooks per tenant"""
    __tablename__ = "discord_webhooks"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, ForeignKey("tenant_accounts.tenant_id"))
    name = Column(String)
    webhook_url = Column(String)
    server_name = Column(String)
    channel_name = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    tenant = relationship("TenantAccount", back_populates="discord_webhooks")

class ReplicationFlow(Base):
    """Replication flows configuration"""
    __tablename__ = "replication_flows"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, ForeignKey("tenant_accounts.tenant_id"))
    flow_name = Column(String)
    source_type = Column(String)  # telegram, discord
    source_id = Column(String)
    destination_type = Column(String)  # telegram, discord
    destination_id = Column(String)
    filters = Column(JSON)
    transformations = Column(JSON)
    schedule = Column(JSON)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    messages_processed = Column(Integer, default=0)
    last_message_at = Column(DateTime)
    error_count = Column(Integer, default=0)
    last_error = Column(String)
    
    tenant = relationship("TenantAccount", back_populates="flows")

Base.metadata.create_all(bind=engine)

# ========== API SCHEMAS ==========

class TelegramAccountCreate(BaseModel):
    phone_number: str
    api_id: str
    api_hash: str

class DiscordWebhookCreate(BaseModel):
    name: str
    webhook_url: str
    server_name: str
    channel_name: Optional[str] = None

class FlowCreate(BaseModel):
    flow_name: str
    source_type: str
    source_id: str
    destination_type: str
    destination_id: str
    filters: Dict[str, Any]
    transformations: Dict[str, Any]
    schedule: Optional[Dict[str, Any]] = None

# ========== ACCOUNT SERVICE ==========

app = FastAPI(title="Account Service", version="2.0.0")
logger = logging.getLogger(__name__)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_tenant(tenant_id: str, db: Session = Depends(get_db)):
    """Get current tenant from header or token"""
    tenant = db.query(TenantAccount).filter(TenantAccount.tenant_id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant

@app.post("/api/tenants/register")
async def register_tenant(
    company_name: str,
    email: str,
    subscription_tier: str = "starter",
    db: Session = Depends(get_db)
):
    """Register new tenant (company)"""
    import uuid
    tenant_id = str(uuid.uuid4())
    
    tenant = TenantAccount(
        tenant_id=tenant_id,
        company_name=company_name,
        email=email,
        subscription_tier=subscription_tier,
        max_telegram_accounts={"starter": 1, "pro": 5, "enterprise": 50}[subscription_tier],
        max_flows={"starter": 10, "pro": 50, "enterprise": 1000}[subscription_tier]
    )
    
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    
    return {"tenant_id": tenant_id, "message": "Tenant registered successfully"}

@app.post("/api/telegram/add")
async def add_telegram_account(
    account: TelegramAccountCreate,
    tenant_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Add Telegram account for tenant"""
    tenant = get_current_tenant(tenant_id, db)
    
    # Check limits
    current_accounts = db.query(TelegramAccount).filter(
        TelegramAccount.tenant_id == tenant_id
    ).count()
    
    if current_accounts >= tenant.max_telegram_accounts:
        raise HTTPException(
            status_code=403,
            detail=f"Account limit reached. Upgrade to add more accounts."
        )
    
    # Create session
    session_string = await create_telegram_session(
        account.api_id,
        account.api_hash,
        account.phone_number
    )
    
    tg_account = TelegramAccount(
        tenant_id=tenant_id,
        phone_number=account.phone_number,
        api_id=account.api_id,
        api_hash=account.api_hash,
        session_string=session_string
    )
    
    db.add(tg_account)
    db.commit()
    
    # Trigger discovery scan in background
    background_tasks.add_task(scan_telegram_groups, tg_account.id, tenant_id)
    
    return {"message": "Telegram account added successfully", "account_id": tg_account.id}

@app.post("/api/discord/webhooks")
async def add_discord_webhook(
    webhook: DiscordWebhookCreate,
    tenant_id: str,
    db: Session = Depends(get_db)
):
    """Add Discord webhook for tenant"""
    tenant = get_current_tenant(tenant_id, db)
    
    # Test webhook
    is_valid = await test_discord_webhook(webhook.webhook_url)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid webhook URL")
    
    discord_webhook = DiscordWebhook(
        tenant_id=tenant_id,
        name=webhook.name,
        webhook_url=webhook.webhook_url,
        server_name=webhook.server_name,
        channel_name=webhook.channel_name
    )
    
    db.add(discord_webhook)
    db.commit()
    
    return {"message": "Webhook added successfully", "webhook_id": discord_webhook.id}

@app.post("/api/flows/create")
async def create_flow(
    flow: FlowCreate,
    tenant_id: str,
    db: Session = Depends(get_db)
):
    """Create replication flow"""
    tenant = get_current_tenant(tenant_id, db)
    
    # Check limits
    current_flows = db.query(ReplicationFlow).filter(
        ReplicationFlow.tenant_id == tenant_id
    ).count()
    
    if current_flows >= tenant.max_flows:
        raise HTTPException(
            status_code=403,
            detail=f"Flow limit reached. Upgrade to create more flows."
        )
    
    replication_flow = ReplicationFlow(
        tenant_id=tenant_id,
        **flow.dict()
    )
    
    db.add(replication_flow)
    db.commit()
    
    # Notify replication service
    await notify_replication_service(replication_flow.id)
    
    return {"message": "Flow created successfully", "flow_id": replication_flow.id}

@app.get("/api/flows/{tenant_id}")
async def get_tenant_flows(tenant_id: str, db: Session = Depends(get_db)):
    """Get all flows for a tenant"""
    flows = db.query(ReplicationFlow).filter(
        ReplicationFlow.tenant_id == tenant_id
    ).all()
    
    return {
        "flows": [
            {
                "id": f.id,
                "name": f.flow_name,
                "source": f"{f.source_type}:{f.source_id}",
                "destination": f"{f.destination_type}:{f.destination_id}",
                "status": "active" if f.is_active else "paused",
                "messages": f.messages_processed,
                "errors": f.error_count
            }
            for f in flows
        ]
    }

# ========== HELPER FUNCTIONS ==========

async def create_telegram_session(api_id: str, api_hash: str, phone: str) -> str:
    """Create and return encrypted Telegram session"""
    client = TelegramClient(StringSession(), api_id, api_hash)
    await client.connect()
    
    if not await client.is_user_authorized():
        await client.send_code_request(phone)
        # In production, implement OTP verification flow
        # For now, return placeholder
        return "encrypted_session_string"
    
    session_string = client.session.save()
    await client.disconnect()
    return session_string

async def test_discord_webhook(webhook_url: str) -> bool:
    """Test if Discord webhook is valid"""
    async with aiohttp.ClientSession() as session:
        test_payload = {
            "content": "🔗 Webhook connection test",
            "username": "Replication Bot"
        }
        try:
            async with session.post(webhook_url, json=test_payload) as response:
                return response.status == 204
        except:
            return False

async def scan_telegram_groups(account_id: int, tenant_id: str):
    """Background task to scan Telegram groups"""
    # Connect to Discovery Service
    async with aiohttp.ClientSession() as session:
        payload = {
            "account_id": account_id,
            "tenant_id": tenant_id
        }
        async with session.post(
            "http://localhost:8002/api/discovery/scan",
            json=payload
        ) as response:
            return await response.json()

async def notify_replication_service(flow_id: int):
    """Notify replication service about new flow"""
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"http://localhost:8001/api/flows/activate/{flow_id}"
        ) as response:
            return response.status == 200

# ================== 2. DISCOVERY SERVICE ENHANCED ==================
# services/discovery_service/main.py

from fastapi import FastAPI, HTTPException, BackgroundTasks
from telethon import TelegramClient
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.functions.messages import GetHistoryRequest
import asyncio
from typing import List, Dict, Any
import redis
import json

app = FastAPI(title="Discovery Service", version="2.0.0")

# Redis for caching
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

class DiscoveryEngine:
    """Enhanced discovery engine with multi-tenant support"""
    
    def __init__(self):
        self.active_scanners = {}
        self.scan_results_cache = {}
    
    async def scan_telegram_channels(
        self,
        tenant_id: str,
        session_string: str,
        api_id: str,
        api_hash: str
    ) -> List[Dict]:
        """Scan all available Telegram channels for a tenant"""
        
        # Check cache first
        cache_key = f"discovery:{tenant_id}"
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
        
        client = TelegramClient(StringSession(session_string), api_id, api_hash)
        await client.connect()
        
        channels = []
        async for dialog in client.iter_dialogs():
            if dialog.is_group or dialog.is_channel:
                try:
                    entity = await client.get_entity(dialog.id)
                    
                    # Get detailed info
                    if hasattr(entity, 'megagroup'):
                        full_channel = await client(GetFullChannelRequest(entity))
                        participants_count = full_channel.full_chat.participants_count
                    else:
                        participants_count = 0
                    
                    channel_info = {
                        "id": dialog.id,
                        "name": dialog.name,
                        "type": self._get_chat_type(entity),
                        "members": participants_count,
                        "username": getattr(entity, 'username', None),
                        "is_verified": getattr(entity, 'verified', False),
                        "is_restricted": getattr(entity, 'restricted', False),
                        "is_scam": getattr(entity, 'scam', False),
                        "has_geo": getattr(entity, 'has_geo', False),
                        "access_hash": getattr(entity, 'access_hash', None)
                    }
                    
                    channels.append(channel_info)
                    
                except Exception as e:
                    logger.error(f"Error processing channel {dialog.id}: {e}")
                    continue
                
                # Rate limiting
                await asyncio.sleep(0.5)
        
        await client.disconnect()
        
        # Cache results for 30 minutes
        redis_client.setex(cache_key, 1800, json.dumps(channels))
        
        return channels
    
    def _get_chat_type(self, entity) -> str:
        """Determine chat type"""
        if hasattr(entity, 'broadcast') and entity.broadcast:
            return 'channel'
        elif hasattr(entity, 'megagroup') and entity.megagroup:
            return 'megagroup'
        elif hasattr(entity, 'gigagroup') and entity.gigagroup:
            return 'gigagroup'
        else:
            return 'group'
    
    async def get_channel_preview(
        self,
        tenant_id: str,
        channel_id: int,
        session_string: str,
        api_id: str,
        api_hash: str
    ) -> Dict:
        """Get preview of recent messages from a channel"""
        
        client = TelegramClient(StringSession(session_string), api_id, api_hash)
        await client.connect()
        
        messages = []
        entity = await client.get_entity(channel_id)
        
        # Get last 10 messages
        history = await client(GetHistoryRequest(
            peer=entity,
            offset_id=0,
            offset_date=None,
            add_offset=0,
            limit=10,
            max_id=0,
            min_id=0,
            hash=0
        ))
        
        for message in history.messages:
            if message.message:  # Text message
                messages.append({
                    "id": message.id,
                    "text": message.message[:200],  # First 200 chars
                    "date": message.date.isoformat(),
                    "views": getattr(message, 'views', 0),
                    "forwards": getattr(message, 'forwards', 0)
                })
        
        await client.disconnect()
        
        return {
            "channel_id": channel_id,
            "messages": messages,
            "preview_generated": datetime.utcnow().isoformat()
        }

discovery_engine = DiscoveryEngine()

@app.post("/api/discovery/scan")
async def trigger_scan(
    tenant_id: str,
    account_id: int,
    background_tasks: BackgroundTasks
):
    """Trigger channel discovery scan"""
    
    # Get account details from Account Service
    account = await get_telegram_account(tenant_id, account_id)
    
    # Start scan in background
    background_tasks.add_task(
        discovery_engine.scan_telegram_channels,
        tenant_id,
        account['session_string'],
        account['api_id'],
        account['api_hash']
    )
    
    return {"status": "scanning", "message": "Discovery scan started"}

@app.get("/api/discovery/channels/{tenant_id}")
async def get_discovered_channels(tenant_id: str):
    """Get discovered channels for tenant"""
    
    cache_key = f"discovery:{tenant_id}"
    cached = redis_client.get(cache_key)
    
    if not cached:
        return {"channels": [], "message": "No channels found. Please run a scan first."}
    
    channels = json.loads(cached)
    return {"channels": channels, "total": len(channels)}

@app.get("/api/discovery/preview/{channel_id}")
async def get_channel_preview(
    tenant_id: str,
    channel_id: int,
    account_id: int
):
    """Get preview of channel messages"""
    
    account = await get_telegram_account(tenant_id, account_id)
    
    preview = await discovery_engine.get_channel_preview(
        tenant_id,
        channel_id,
        account['session_string'],
        account['api_id'],
        account['api_hash']
    )
    
    return preview

# ================== 3. REPLICATION ENGINE SERVICE ==================
# services/replication_engine/main.py

from fastapi import FastAPI, HTTPException
import asyncio
from typing import Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
import aiohttp
from telethon import TelegramClient, events

app = FastAPI(title="Replication Engine", version="2.0.0")

@dataclass
class ReplicationWorker:
    """Worker for handling message replication"""
    flow_id: int
    tenant_id: str
    source_type: str
    source_id: str
    destination_type: str
    destination_id: str
    filters: Dict[str, Any]
    transformations: Dict[str, Any]
    is_active: bool = True
    
    async def start(self):
        """Start replication worker"""
        if self.source_type == "telegram" and self.destination_type == "discord":
            await self.replicate_telegram_to_discord()
        elif self.source_type == "discord" and self.destination_type == "telegram":
            await self.replicate_discord_to_telegram()
        elif self.source_type == "telegram" and self.destination_type == "telegram":
            await self.replicate_telegram_to_telegram()
        elif self.source_type == "discord" and self.destination_type == "discord":
            await self.replicate_discord_to_discord()
    
    async def replicate_telegram_to_discord(self):
        """Replicate from Telegram to Discord"""
        # Get account details
        account = await get_account_for_flow(self.flow_id)
        
        client = TelegramClient(
            StringSession(account['session_string']),
            account['api_id'],
            account['api_hash']
        )
        
        await client.connect()
        
        @client.on(events.NewMessage(chats=int(self.source_id)))
        async def handler(event):
            if not self.is_active:
                return
            
            # Apply filters
            if not self.apply_filters(event.message):
                return
            
            # Apply transformations
            transformed = await self.apply_transformations(event.message)
            
            # Send to Discord
            await self.send_to_discord(transformed)
            
            # Update stats
            await self.update_stats()
        
        await client.run_until_disconnected()
    
    def apply_filters(self, message) -> bool:
        """Apply message filters"""
        if not self.filters.get('enabled', True):
            return True
        
        text = message.message if hasattr(message, 'message') else str(message)
        
        # Min length filter
        min_length = self.filters.get('min_length', 0)
        if len(text) < min_length:
            return False
        
        # Blocked keywords
        blocked = self.filters.get('blocked_keywords', [])
        if any(word.lower() in text.lower() for word in blocked):
            return False
        
        # Required keywords
        required = self.filters.get('required_keywords', [])
        if required and not any(word.lower() in text.lower() for word in required):
            return False
        
        return True
    
    async def apply_transformations(self, message) -> Dict:
        """Apply message transformations"""
        transformed = {
            "text": message.message if hasattr(message, 'message') else str(message),
            "media": None,
            "metadata": {}
        }
        
        # Add watermark to images
        if self.transformations.get('watermark', False) and message.photo:
            transformed['media'] = await self.add_watermark(message.photo)
        
        # Format message
        if self.transformations.get('format', False):
            transformed['text'] = self.format_message(transformed['text'])
        
        # Add delay
        delay = self.transformations.get('delay', 0)
        if delay > 0:
            await asyncio.sleep(delay)
        
        return transformed
    
    async def send_to_discord(self, message: Dict):
        """Send message to Discord webhook"""
        webhook_url = await get_webhook_for_flow(self.flow_id, self.destination_id)
        
        async with aiohttp.ClientSession() as session:
            payload = {
                "content": message['text'],
                "username": "Replication Bot"
            }
            
            if message.get('media'):
                # Handle media upload
                pass
            
            async with session.post(webhook_url, json=payload) as response:
                if response.status != 204:
                    logger.error(f"Failed to send to Discord: {response.status}")

class ReplicationManager:
    """Manages all replication workers"""
    
    def __init__(self):
        self.workers: Dict[int, ReplicationWorker] = {}
    
    async def create_worker(self, flow_data: Dict) -> ReplicationWorker:
        """Create new replication worker"""
        worker = ReplicationWorker(**flow_data)
        self.workers[flow_data['flow_id']] = worker
        
        # Start worker in background
        asyncio.create_task(worker.start())
        
        return worker
    
    async def stop_worker(self, flow_id: int):
        """Stop replication worker"""
        if flow_id in self.workers:
            self.workers[flow_id].is_active = False
            del self.workers[flow_id]
    
    def get_status(self) -> Dict:
        """Get status of all workers"""
        return {
            "active_workers": len(self.workers),
            "workers": [
                {
                    "flow_id": w.flow_id,
                    "tenant_id": w.tenant_id,
                    "status": "active" if w.is_active else "paused"
                }
                for w in self.workers.values()
            ]
        }

manager = ReplicationManager()

@app.post("/api/flows/activate/{flow_id}")
async def activate_flow(flow_id: int):
    """Activate a replication flow"""
    
    # Get flow details from database
    flow_data = await get_flow_details(flow_id)
    
    if not flow_data:
        raise HTTPException(status_code=404, detail="Flow not found")
    
    # Create and start worker
    worker = await manager.create_worker(flow_data)
    
    return {"status": "activated", "flow_id": flow_id}

@app.post("/api/flows/deactivate/{flow_id}")
async def deactivate_flow(flow_id: int):
    """Deactivate a replication flow"""
    
    await manager.stop_worker(flow_id)
    
    return {"status": "deactivated", "flow_id": flow_id}

@app.get("/api/status")
async def get_status():
    """Get replication engine status"""
    return manager.get_status()

# ================== 4. MONITORING SERVICE ==================
# services/monitoring_service/main.py

from fastapi import FastAPI, WebSocket
import asyncio
from typing import List, Dict
import json
from datetime import datetime, timedelta

app = FastAPI(title="Monitoring Service", version="2.0.0")

class MonitoringHub:
    """Real-time monitoring hub"""
    
    def __init__(self):
        self.connections: List[WebSocket] = []
        self.metrics = {}
        self.alerts = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.connections.remove(websocket)
    
    async def broadcast_metrics(self):
        """Broadcast metrics to all connected clients"""
        while True:
            metrics = await self.collect_metrics()
            
            for connection in self.connections:
                try:
                    await connection.send_json(metrics)
                except:
                    # Remove dead connections
                    self.connections.remove(connection)
            
            await asyncio.sleep(5)  # Update every 5 seconds
    
    async def collect_metrics(self) -> Dict:
        """Collect metrics from all services"""
        
        # Get metrics from Account Service
        account_metrics = await self.get_service_metrics("http://localhost:8000/api/metrics")
        
        # Get metrics from Discovery Service
        discovery_metrics = await self.get_service_metrics("http://localhost:8002/api/metrics")
        
        # Get metrics from Replication Engine
        replication_metrics = await self.get_service_metrics("http://localhost:8001/api/metrics")
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "account": account_metrics,
                "discovery": discovery_metrics,
                "replication": replication_metrics
            },
            "alerts": self.get_active_alerts()
        }
    
    async def get_service_metrics(self, url: str) -> Dict:
        """Get metrics from a service"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    return await response.json()
        except:
            return {"status": "offline"}
    
    def get_active_alerts(self) -> List[Dict]:
        """Get active alerts"""
        # Filter alerts from last hour
        cutoff = datetime.utcnow() - timedelta(hours=1)
        return [
            alert for alert in self.alerts 
            if alert['timestamp'] > cutoff
        ]
    
    async def create_alert(self, alert_type: str, message: str, severity: str = "warning"):
        """Create new alert"""
        alert = {
            "id": len(self.alerts) + 1,
            "type": alert_type,
            "message": message,
            "severity": severity,
            "timestamp": datetime.utcnow()
        }
        
        self.alerts.append(alert)
        
        # Broadcast alert immediately
        for connection in self.connections:
            try:
                await connection.send_json({"alert": alert})
            except:
                pass

hub = MonitoringHub()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time monitoring"""
    await hub.connect(websocket)
    try:
        # Start broadcasting metrics
        await hub.broadcast_metrics()
    except:
        hub.disconnect(websocket)

@app.post("/api/alerts")
async def create_alert(
    alert_type: str,
    message: str,
    severity: str = "warning"
):
    """Create monitoring alert"""
    await hub.create_alert(alert_type, message, severity)
    return {"status": "alert created"}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "monitoring",
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    
    # Start services based on port
    import sys
    
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
        
        if port == 8000:
            # Account Service
            uvicorn.run("account_service:app", host="0.0.0.0", port=8000, reload=True)
        elif port == 8001:
            # Replication Engine
            uvicorn.run("replication_engine:app", host="0.0.0.0", port=8001, reload=True)
        elif port == 8002:
            # Discovery Service
            uvicorn.run("discovery_service:app", host="0.0.0.0", port=8002, reload=True)
        elif port == 8003:
            # Monitoring Service
            uvicorn.run("monitoring_service:app", host="0.0.0.0", port=8003, reload=True)