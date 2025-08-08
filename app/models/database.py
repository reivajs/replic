"""
App Models Database
==================
Configuración de base de datos simplificada
"""

import asyncio
from typing import AsyncGenerator
import sqlite3
from pathlib import Path

# Base de datos SQLite simple
DATABASE_PATH = Path("replicator.db")

class DatabaseManager:
    """Gestor de base de datos simplificado"""
    
    def __init__(self):
        self.db_path = DATABASE_PATH
        self._ensure_database()
    
    def _ensure_database(self):
        """Crear base de datos si no existe"""
        if not self.db_path.exists():
            conn = sqlite3.connect(self.db_path)
            
            # Crear tablas básicas
            conn.execute("""
                CREATE TABLE IF NOT EXISTS replication_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    group_id INTEGER,
                    message_type TEXT,
                    status TEXT,
                    processing_time REAL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS configurations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id INTEGER UNIQUE,
                    config_json TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            conn.close()
    
    def get_connection(self):
        """Obtener conexión a la base de datos"""
        return sqlite3.connect(self.db_path)

# Instancia global
db_manager = DatabaseManager()

async def get_db() -> AsyncGenerator:
    """Obtener conexión a base de datos (async)"""
    conn = db_manager.get_connection()
    try:
        yield conn
    finally:
        conn.close()

async def init_database():
    """Inicializar base de datos"""
    try:
        db_manager._ensure_database()
        print("✅ Base de datos inicializada")
        return True
    except Exception as e:
        print(f"❌ Error inicializando base de datos: {e}")
        return False