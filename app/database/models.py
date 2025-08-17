"""
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
