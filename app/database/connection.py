"""Database Connection Module"""
from typing import AsyncGenerator
import logging

logger = logging.getLogger(__name__)

# For now, using in-memory storage
# In production, use SQLAlchemy + PostgreSQL

class Database:
    """Simple in-memory database for development"""
    
    def __init__(self):
        self.data = {}
        
    async def connect(self):
        logger.info("Database connected (in-memory)")
        
    async def disconnect(self):
        logger.info("Database disconnected")

# Global instance
db = Database()

async def init_database(app):
    """Initialize database"""
    await db.connect()

async def close_db_connections():
    """Close database connections"""
    await db.disconnect()

async def get_db():
    """Get database session"""
    yield db
