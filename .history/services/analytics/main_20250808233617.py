#!/usr/bin/env python3
"""
📊 ANALYTICS MICROSERVICE v4.0
==============================
Servicio de analytics enterprise para tu SaaS
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import logging

# Logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AnalyticsDB:
    """Base de datos de analytics optimizada"""
    
    def __init__(self, db_path: str = "database/analytics.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Inicializar base de datos"""
        Path("database").mkdir(exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        
        # Tabla de métricas
        conn.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                service_name TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                group_id INTEGER,
                metadata TEXT
            )
        """)
        
        # Tabla de eventos
        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT NOT NULL,
                service_name TEXT NOT NULL,
                group_id INTEGER,
                data TEXT
            )
        """)
        
        # Índices para performance
        conn.execute('CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_metrics_service ON metrics(service_name)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)')
        
        conn.commit()
        conn.close()
        
        # Insertar datos iniciales de muestra
        self._insert_sample_data()
    
    def _insert_sample_data(self):
        """Insertar datos de muestra para dashboard"""
        conn = sqlite3.connect(self.db_path)
        
        # Métricas de ejemplo
        sample_metrics = [
            ('message_replicator', 'messages_processed', 12278, None, '{"source": "telegram"}'),
            ('message_replicator', 'messages_replicated', 11856, None, '{"target": "discord"}'),
            ('message_replicator', 'errors', 34, None, '{"type": "connection"}'),
            ('analytics', 'queries_processed', 5674, None, '{"endpoint": "dashboard"}'),
            ('file_manager', 'files_stored', 1234, None, '{"type": "media"}'),
        ]
        
        for service, metric, value, group_id, metadata in sample_metrics:
            conn.execute("""
                INSERT OR IGNORE INTO metrics (service_name, metric_name, metric_value, group_id, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (service, metric, value, group_id, metadata))
        
        conn.commit()
        conn.close()
    
    def add_metric(self, service_name: str, metric_name: str, value: float, group_id: int = None, metadata: str = None):
        """Añadir métrica"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO metrics (service_name, metric_name, metric_value, group_id, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (service_name, metric_name, value, group_id, metadata))
        conn.commit()
        conn.close()
    
    def get_saas_dashboard_data(self) -> Dict[str, Any]:
        """Obtener datos para dashboard SaaS"""
        
        # Datos simulados pero realistas para SaaS
        dashboard_data = {
            "revenue": {
                "total": 12278.35,
                "change": "+5%",
                "period": "This month"
            },
            "new_orders": {
                "total": 4673,
                "change": "-2%", 
                "period": "This month"
            },
            "completed_orders": {
                "total": 5342,
                "change": "+18%",
                "period": "This month"
            },
            "spending": {
                "total": 10365.32,
                "change": "-17%",
                "period": "This month"
            },
            "customers": {
                "total": 651,
                "segments": {
                    "freelancer": 45,
                    "upwork": 30,
                    "behance": 25
                }
            },
            "regions": {
                "israel": 266,
                "usa": 148,
                "canada": 88,
                "australia": 122
            },
            "progress": {
                "overall_performance": 90,
                "order_fulfillment": 85
            },
            "attendance": {
                "youtube": "15K",
                "instagram": "132K", 
                "facebook": "176K"
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return dashboard_data

# Instancia global
analytics_db = AnalyticsDB()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida del servicio"""
    try:
        logger.info("🚀 Iniciando Analytics Service...")
        logger.info("✅ Analytics Service iniciado")
        yield
    finally:
        logger.info("🛑 Analytics Service detenido")

# Crear aplicación FastAPI
app = FastAPI(
    title="📊 Analytics Microservice",
    description="Servicio de analytics enterprise",
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

class MetricCreate(BaseModel):
    service_name: str
    metric_name: str
    value: float
    group_id: int = None
    metadata: str = None

@app.get("/")
async def root():
    """Información del servicio"""
    return {
        "service": "Analytics Microservice",
        "version": "4.0.0",
        "description": "Servicio de analytics enterprise para SaaS"
    }

@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "service": "analytics",
        "version": "4.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/metrics")
async def add_metric(metric: MetricCreate):
    """Añadir nueva métrica"""
    try:
        analytics_db.add_metric(
            metric.service_name,
            metric.metric_name,
            metric.value,
            metric.group_id,
            metric.metadata
        )
        
        return {
            "message": "Metric added successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    """Obtener estadísticas"""
    try:
        return {
            "service": "analytics",
            "metrics_count": 1000,
            "events_count": 500,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/dashboard-data")
async def get_dashboard_data():
    """Datos para dashboard SaaS"""
    try:
        return analytics_db.get_saas_dashboard_data()
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    config = {
        "host": "0.0.0.0",
        "port": 8002,
        "reload": False,
        "log_level": "info"
    }
    
    print("🚀 Starting Analytics Microservice...")
    print(f"   📊 Service: Analytics")
    print(f"   🌐 URL: http://{config['host']}:{config['port']}")
    print(f"   📚 Docs: http://{config['host']}:{config['port']}/docs")
    print(f"   🏥 Health: http://{config['host']}:{config['port']}/health")
    
    uvicorn.run(app, **config)