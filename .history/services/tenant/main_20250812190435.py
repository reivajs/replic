#!/usr/bin/env python3
"""
🏢 MULTI-TENANT SERVICE v2.0
===========================
Gestión completa de tenants para SaaS enterprise
Compatible con tu arquitectura existente
"""

import asyncio
import json
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import hashlib
import secrets

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, EmailStr
import uvicorn
import bcrypt

# Logger
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============= MODELS =============

class TenantCreate(BaseModel):
    """Request para crear tenant"""
    name: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    plan: str = Field(default="starter", description="starter, pro, enterprise")
    max_groups: int = Field(default=10, description="Max groups allowed")
    max_webhooks: int = Field(default=5, description="Max Discord webhooks")

class TenantUpdate(BaseModel):
    """Request para actualizar tenant"""
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    plan: Optional[str] = None
    max_groups: Optional[int] = None
    max_webhooks: Optional[int] = None
    is_active: Optional[bool] = None

class TenantAuth(BaseModel):
    """Autenticación de tenant"""
    tenant_id: str
    api_key: str

class UsageUpdate(BaseModel):
    """Actualización de uso"""
    tenant_id: str
    groups_count: int = 0
    messages_processed: int = 0
    webhooks_count: int = 0

# ============= PLANS CONFIGURATION =============

TENANT_PLANS = {
    "starter": {
        "name": "Starter",
        "price": 29,
        "max_groups": 10,
        "max_webhooks": 3,
        "max_messages_month": 10000,
        "watermarks": True,
        "priority_support": False,
        "custom_branding": False
    },
    "pro": {
        "name": "Pro", 
        "price": 79,
        "max_groups": 50,
        "max_webhooks": 10,
        "max_messages_month": 100000,
        "watermarks": True,
        "priority_support": True,
        "custom_branding": True
    },
    "enterprise": {
        "name": "Enterprise",
        "price": 199,
        "max_groups": 1000,
        "max_webhooks": 50,
        "max_messages_month": 1000000,
        "watermarks": True,
        "priority_support": True,
        "custom_branding": True
    }
}

# ============= DATABASE MANAGER =============

class TenantDatabase:
    """Gestor de base de datos para tenants"""
    
    def __init__(self, db_path: str = "data/tenants.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Inicializar base de datos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla de tenants
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tenants (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                plan TEXT NOT NULL DEFAULT 'starter',
                api_key TEXT UNIQUE NOT NULL,
                max_groups INTEGER DEFAULT 10,
                max_webhooks INTEGER DEFAULT 5,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP,
                telegram_api_id INTEGER,
                telegram_api_hash TEXT,
                telegram_phone TEXT,
                telegram_session_name TEXT
            )
        ''')
        
        # Tabla de usage/metrics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tenant_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                date DATE NOT NULL,
                groups_count INTEGER DEFAULT 0,
                messages_processed INTEGER DEFAULT 0,
                webhooks_count INTEGER DEFAULT 0,
                storage_used_mb INTEGER DEFAULT 0,
                api_calls INTEGER DEFAULT 0,
                FOREIGN KEY (tenant_id) REFERENCES tenants (id),
                UNIQUE(tenant_id, date)
            )
        ''')
        
        # Tabla de configuraciones por tenant
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tenant_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                config_key TEXT NOT NULL,
                config_value TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (tenant_id) REFERENCES tenants (id),
                UNIQUE(tenant_id, config_key)
            )
        ''')
        
        # Índices
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tenant_email ON tenants(email)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tenant_api_key ON tenants(api_key)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_usage_tenant_date ON tenant_usage(tenant_id, date)')
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Tenant database initialized: {self.db_path}")
    
    def create_tenant(self, tenant_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crear nuevo tenant"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Generar ID y API key únicos
            tenant_id = self._generate_tenant_id()
            api_key = self._generate_api_key()
            
            # Obtener límites del plan
            plan_limits = TENANT_PLANS.get(tenant_data.get('plan', 'starter'))
            
            cursor.execute('''
                INSERT INTO tenants 
                (id, name, email, plan, api_key, max_groups, max_webhooks, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                tenant_id, tenant_data['name'], tenant_data['email'],
                tenant_data.get('plan', 'starter'), api_key,
                plan_limits['max_groups'], plan_limits['max_webhooks'],
                datetime.now().isoformat(), datetime.now().isoformat()
            ))
            
            # Crear entrada inicial de usage
            today = datetime.now().date().isoformat()
            cursor.execute('''
                INSERT INTO tenant_usage (tenant_id, date)
                VALUES (?, ?)
            ''', (tenant_id, today))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Tenant created: {tenant_id} ({tenant_data['name']})")
            
            return {
                "tenant_id": tenant_id,
                "api_key": api_key,
                "plan": tenant_data.get('plan', 'starter'),
                "limits": plan_limits
            }
            
        except sqlite3.IntegrityError as e:
            if "email" in str(e):
                raise HTTPException(status_code=400, detail="Email already exists")
            else:
                raise HTTPException(status_code=400, detail="Tenant creation failed")
        except Exception as e:
            logger.error(f"❌ Error creating tenant: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    def get_tenant(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Obtener tenant por ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM tenants WHERE id = ?', (tenant_id,))
            row = cursor.fetchone()
            
            if row:
                tenant = dict(row)
                tenant['is_active'] = bool(tenant['is_active'])
                
                # Obtener usage actual
                today = datetime.now().date().isoformat()
                cursor.execute('''
                    SELECT * FROM tenant_usage 
                    WHERE tenant_id = ? AND date = ?
                ''', (tenant_id, today))
                usage_row = cursor.fetchone()
                
                if usage_row:
                    tenant['current_usage'] = dict(usage_row)
                else:
                    tenant['current_usage'] = {
                        'groups_count': 0,
                        'messages_processed': 0,
                        'webhooks_count': 0,
                        'storage_used_mb': 0,
                        'api_calls': 0
                    }
                
                conn.close()
                return tenant
            
            conn.close()
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting tenant {tenant_id}: {e}")
            return None
    
    def get_tenant_by_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Obtener tenant por API key"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM tenants WHERE api_key = ? AND is_active = 1', (api_key,))
            row = cursor.fetchone()
            
            if row:
                tenant = dict(row)
                tenant['is_active'] = bool(tenant['is_active'])
                conn.close()
                return tenant
            
            conn.close()
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting tenant by API key: {e}")
            return None
    
    def update_tenant(self, tenant_id: str, updates: Dict[str, Any]) -> bool:
        """Actualizar tenant"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Construir query dinámicamente
            set_clauses = []
            params = []
            
            for key, value in updates.items():
                if key in ['name', 'plan', 'max_groups', 'max_webhooks', 'is_active']:
                    set_clauses.append(f"{key} = ?")
                    params.append(value)
            
            if not set_clauses:
                return False
            
            set_clauses.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            params.append(tenant_id)
            
            query = f"UPDATE tenants SET {', '.join(set_clauses)} WHERE id = ?"
            cursor.execute(query, params)
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            if success:
                logger.info(f"✅ Tenant updated: {tenant_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error updating tenant {tenant_id}: {e}")
            return False
    
    def update_usage(self, tenant_id: str, usage_data: Dict[str, Any]) -> bool:
        """Actualizar usage de tenant"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            today = datetime.now().date().isoformat()
            
            # Insert or update usage
            cursor.execute('''
                INSERT OR REPLACE INTO tenant_usage 
                (tenant_id, date, groups_count, messages_processed, webhooks_count, storage_used_mb, api_calls)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                tenant_id, today,
                usage_data.get('groups_count', 0),
                usage_data.get('messages_processed', 0),
                usage_data.get('webhooks_count', 0),
                usage_data.get('storage_used_mb', 0),
                usage_data.get('api_calls', 0)
            ))
            
            # Update last activity
            cursor.execute('''
                UPDATE tenants SET last_activity = ? WHERE id = ?
            ''', (datetime.now().isoformat(), tenant_id))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating usage for {tenant_id}: {e}")
            return False
    
    def get_all_tenants(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Obtener todos los tenants"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM tenants"
            if active_only:
                query += " WHERE is_active = 1"
            query += " ORDER BY created_at DESC"
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            tenants = []
            for row in rows:
                tenant = dict(row)
                tenant['is_active'] = bool(tenant['is_active'])
                tenants.append(tenant)
            
            conn.close()
            return tenants
            
        except Exception as e:
            logger.error(f"❌ Error getting all tenants: {e}")
            return []
    
    def _generate_tenant_id(self) -> str:
        """Generar ID único para tenant"""
        return f"tenant_{secrets.token_urlsafe(12)}"
    
    def _generate_api_key(self) -> str:
        """Generar API key única"""
        return f"tk_{secrets.token_urlsafe(32)}"

# ============= AUTHENTICATION =============

security = HTTPBearer()
database = TenantDatabase()

async def get_current_tenant(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Obtener tenant actual desde API key"""
    api_key = credentials.credentials
    
    tenant = database.get_tenant_by_api_key(api_key)
    if not tenant:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    if not tenant['is_active']:
        raise HTTPException(status_code=403, detail="Tenant account disabled")
    
    return tenant

async def verify_tenant_limits(tenant: Dict[str, Any], usage_check: str) -> bool:
    """Verificar límites del tenant"""
    current_usage = tenant.get('current_usage', {})
    
    if usage_check == "groups":
        return current_usage.get('groups_count', 0) < tenant['max_groups']
    elif usage_check == "webhooks":
        return current_usage.get('webhooks_count', 0) < tenant['max_webhooks']
    elif usage_check == "messages":
        plan_limits = TENANT_PLANS.get(tenant['plan'], {})
        max_messages = plan_limits.get('max_messages_month', 10000)
        return current_usage.get('messages_processed', 0) < max_messages
    
    return True

# ============= FASTAPI APP =============

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle del servicio"""
    logger.info("🏢 Starting Multi-Tenant Service v2.0...")
    
    print("\n" + "="*50)
    print("🏢 MULTI-TENANT SERVICE v2.0")
    print("="*50)
    print("🌐 Endpoints:")
    print("   📊 Dashboard:         http://localhost:8003/")
    print("   🏢 Create Tenant:     POST /api/tenants")
    print("   🔑 Auth Check:        GET /api/tenants/me")
    print("   📈 Usage Update:      POST /api/tenants/usage")
    print("   🏥 Health:            GET /health")
    print("="*50)
    
    yield
    
    logger.info("🛑 Multi-Tenant Service stopped")

app = FastAPI(
    title="🏢 Multi-Tenant Service v2.0",
    description="Gestión completa de tenants para SaaS enterprise",
    version="2.0.0",
    lifespan=lifespan
)

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
    """Root endpoint"""
    return {
        "service": "multi_tenant",
        "version": "2.0.0",
        "status": "running",
        "description": "Multi-tenant management for SaaS enterprise"
    }

@app.get("/health")
async def health_check():
    """Health check"""
    tenants_count = len(database.get_all_tenants())
    
    return {
        "status": "healthy",
        "service": "multi_tenant",
        "timestamp": datetime.now().isoformat(),
        "tenants_count": tenants_count,
        "database_ready": database.db_path is not None
    }

@app.post("/api/tenants")
async def create_tenant(tenant_data: TenantCreate):
    """Crear nuevo tenant"""
    try:
        result = database.create_tenant(tenant_data.dict())
        
        return {
            "success": True,
            "message": "Tenant created successfully",
            "tenant": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating tenant: {e}")
        raise HTTPException(status_code=500, detail="Failed to create tenant")

@app.get("/api/tenants/me")
async def get_current_tenant_info(current_tenant: Dict[str, Any] = Depends(get_current_tenant)):
    """Obtener información del tenant actual"""
    # Remove sensitive data
    safe_tenant = current_tenant.copy()
    safe_tenant.pop('api_key', None)
    safe_tenant.pop('telegram_api_hash', None)
    
    # Add plan details
    plan_details = TENANT_PLANS.get(current_tenant['plan'], {})
    safe_tenant['plan_details'] = plan_details
    
    return {
        "success": True,
        "tenant": safe_tenant
    }

@app.put("/api/tenants/me")
async def update_current_tenant(
    updates: TenantUpdate,
    current_tenant: Dict[str, Any] = Depends(get_current_tenant)
):
    """Actualizar tenant actual"""
    try:
        update_data = {}
        
        # Only allow certain updates
        if updates.name:
            update_data['name'] = updates.name
        if updates.plan and updates.plan in TENANT_PLANS:
            # Update plan and limits
            plan_limits = TENANT_PLANS[updates.plan]
            update_data['plan'] = updates.plan
            update_data['max_groups'] = plan_limits['max_groups']
            update_data['max_webhooks'] = plan_limits['max_webhooks']
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No valid updates provided")
        
        success = database.update_tenant(current_tenant['id'], update_data)
        
        if success:
            return {
                "success": True,
                "message": "Tenant updated successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update tenant")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating tenant: {e}")
        raise HTTPException(status_code=500, detail="Update failed")

@app.post("/api/tenants/usage")
async def update_tenant_usage(
    usage_data: UsageUpdate,
    current_tenant: Dict[str, Any] = Depends(get_current_tenant)
):
    """Actualizar usage del tenant"""
    try:
        # Verify tenant ID matches
        if usage_data.tenant_id != current_tenant['id']:
            raise HTTPException(status_code=403, detail="Tenant ID mismatch")
        
        success = database.update_usage(current_tenant['id'], usage_data.dict())
        
        if success:
            return {
                "success": True,
                "message": "Usage updated successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update usage")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating usage: {e}")
        raise HTTPException(status_code=500, detail="Usage update failed")

@app.get("/api/tenants/limits/check")
async def check_tenant_limits(
    limit_type: str,
    current_tenant: Dict[str, Any] = Depends(get_current_tenant)
):
    """Verificar límites del tenant"""
    try:
        can_proceed = await verify_tenant_limits(current_tenant, limit_type)
        
        current_usage = current_tenant.get('current_usage', {})
        plan_limits = TENANT_PLANS.get(current_tenant['plan'], {})
        
        limits_info = {
            "groups": {
                "current": current_usage.get('groups_count', 0),
                "max": current_tenant['max_groups'],
                "can_add": await verify_tenant_limits(current_tenant, "groups")
            },
            "webhooks": {
                "current": current_usage.get('webhooks_count', 0),
                "max": current_tenant['max_webhooks'],
                "can_add": await verify_tenant_limits(current_tenant, "webhooks")
            },
            "messages": {
                "current": current_usage.get('messages_processed', 0),
                "max": plan_limits.get('max_messages_month', 10000),
                "can_add": await verify_tenant_limits(current_tenant, "messages")
            }
        }
        
        return {
            "success": True,
            "can_proceed": can_proceed,
            "limits": limits_info,
            "plan": current_tenant['plan']
        }
        
    except Exception as e:
        logger.error(f"❌ Error checking limits: {e}")
        raise HTTPException(status_code=500, detail="Limits check failed")

@app.get("/api/tenants/usage/history")
async def get_usage_history(
    days: int = 30,
    current_tenant: Dict[str, Any] = Depends(get_current_tenant)
):
    """Obtener historial de usage"""
    try:
        conn = sqlite3.connect(database.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        cursor.execute('''
            SELECT * FROM tenant_usage 
            WHERE tenant_id = ? AND date BETWEEN ? AND ?
            ORDER BY date DESC
        ''', (current_tenant['id'], start_date.isoformat(), end_date.isoformat()))
        
        rows = cursor.fetchall()
        usage_history = [dict(row) for row in rows]
        
        conn.close()
        
        return {
            "success": True,
            "usage_history": usage_history,
            "period_days": days
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting usage history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get usage history")

@app.get("/api/tenants/config")
async def get_tenant_config(
    current_tenant: Dict[str, Any] = Depends(get_current_tenant)
):
    """Obtener configuración del tenant"""
    try:
        conn = sqlite3.connect(database.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT config_key, config_value FROM tenant_configs
            WHERE tenant_id = ?
        ''', (current_tenant['id'],))
        
        rows = cursor.fetchall()
        config = {row['config_key']: row['config_value'] for row in rows}
        
        conn.close()
        
        return {
            "success": True,
            "config": config
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting config: {e}")
        raise HTTPException(status_code=500, detail="Failed to get config")

@app.post("/api/tenants/config")
async def update_tenant_config(
    config_updates: Dict[str, str],
    current_tenant: Dict[str, Any] = Depends(get_current_tenant)
):
    """Actualizar configuración del tenant"""
    try:
        conn = sqlite3.connect(database.db_path)
        cursor = conn.cursor()
        
        for key, value in config_updates.items():
            cursor.execute('''
                INSERT OR REPLACE INTO tenant_configs 
                (tenant_id, config_key, config_value, created_at)
                VALUES (?, ?, ?, ?)
            ''', (current_tenant['id'], key, value, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": "Configuration updated successfully"
        }
        
    except Exception as e:
        logger.error(f"❌ Error updating config: {e}")
        raise HTTPException(status_code=500, detail="Failed to update config")

# ============= ADMIN ENDPOINTS =============

@app.get("/api/admin/tenants")
async def list_all_tenants(admin_key: str = Header(None)):
    """[ADMIN] Listar todos los tenants"""
    # Simple admin auth - in production use proper admin authentication
    if admin_key != "admin_secret_key_change_me":
        raise HTTPException(status_code=401, detail="Admin access required")
    
    tenants = database.get_all_tenants(active_only=False)
    
    # Remove sensitive data
    safe_tenants = []
    for tenant in tenants:
        safe_tenant = tenant.copy()
        safe_tenant.pop('api_key', None)
        safe_tenant.pop('telegram_api_hash', None)
        safe_tenants.append(safe_tenant)
    
    return {
        "success": True,
        "tenants": safe_tenants,
        "total": len(safe_tenants)
    }

@app.put("/api/admin/tenants/{tenant_id}")
async def admin_update_tenant(
    tenant_id: str,
    updates: TenantUpdate,
    admin_key: str = Header(None)
):
    """[ADMIN] Actualizar cualquier tenant"""
    if admin_key != "admin_secret_key_change_me":
        raise HTTPException(status_code=401, detail="Admin access required")
    
    update_data = updates.dict(exclude_unset=True)
    success = database.update_tenant(tenant_id, update_data)
    
    if success:
        return {
            "success": True,
            "message": f"Tenant {tenant_id} updated successfully"
        }
    else:
        raise HTTPException(status_code=404, detail="Tenant not found")

@app.get("/api/admin/stats")
async def get_admin_stats(admin_key: str = Header(None)):
    """[ADMIN] Estadísticas globales"""
    if admin_key != "admin_secret_key_change_me":
        raise HTTPException(status_code=401, detail="Admin access required")
    
    try:
        conn = sqlite3.connect(database.db_path)
        cursor = conn.cursor()
        
        # Total tenants por plan
        cursor.execute('''
            SELECT plan, COUNT(*) as count FROM tenants
            WHERE is_active = 1
            GROUP BY plan
        ''')
        plan_stats = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Usage total del día
        today = datetime.now().date().isoformat()
        cursor.execute('''
            SELECT 
                SUM(groups_count) as total_groups,
                SUM(messages_processed) as total_messages,
                SUM(webhooks_count) as total_webhooks
            FROM tenant_usage WHERE date = ?
        ''', (today,))
        
        usage_row = cursor.fetchone()
        daily_usage = {
            "total_groups": usage_row[0] or 0,
            "total_messages": usage_row[1] or 0,
            "total_webhooks": usage_row[2] or 0
        }
        
        # Revenue estimado
        revenue = 0
        for plan, count in plan_stats.items():
            plan_price = TENANT_PLANS.get(plan, {}).get('price', 0)
            revenue += plan_price * count
        
        conn.close()
        
        return {
            "success": True,
            "stats": {
                "total_tenants": sum(plan_stats.values()),
                "plan_distribution": plan_stats,
                "daily_usage": daily_usage,
                "estimated_monthly_revenue": revenue
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting admin stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get stats")

# ============= INTEGRATION HELPERS =============

@app.get("/api/integration/tenant/{tenant_id}/telegram")
async def get_tenant_telegram_config(tenant_id: str):
    """Helper para obtener config de Telegram del tenant (para otros servicios)"""
    tenant = database.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    return {
        "telegram_configured": bool(tenant.get('telegram_api_id')),
        "session_name": tenant.get('telegram_session_name', f"session_{tenant_id}"),
        "api_id": tenant.get('telegram_api_id'),
        "api_hash": tenant.get('telegram_api_hash'),
        "phone": tenant.get('telegram_phone')
    }

@app.post("/api/integration/usage/increment")
async def increment_usage(
    tenant_id: str,
    metric: str,  # 'messages', 'api_calls', 'storage'
    amount: int = 1
):
    """Helper para incrementar usage desde otros servicios"""
    try:
        tenant = database.get_tenant(tenant_id)
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        current_usage = tenant.get('current_usage', {})
        
        if metric == 'messages':
            current_usage['messages_processed'] = current_usage.get('messages_processed', 0) + amount
        elif metric == 'api_calls':
            current_usage['api_calls'] = current_usage.get('api_calls', 0) + amount
        elif metric == 'storage':
            current_usage['storage_used_mb'] = current_usage.get('storage_used_mb', 0) + amount
        
        success = database.update_usage(tenant_id, current_usage)
        
        return {
            "success": success,
            "metric": metric,
            "amount": amount,
            "new_value": current_usage.get(f"{metric}_processed" if metric == 'messages' else metric, current_usage.get(metric, 0))
        }
        
    except Exception as e:
        logger.error(f"❌ Error incrementing usage: {e}")
        raise HTTPException(status_code=500, detail="Failed to increment usage")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8003,
        reload=False,
        log_level="info"
    )