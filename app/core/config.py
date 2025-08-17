"""
Configuration Module
====================
Configuración centralizada usando Pydantic v2
"""

from enum import Enum
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
import os

class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class Settings(BaseSettings):
    # Application
    APP_NAME: str = Field(default="Enterprise Orchestrator")
    VERSION: str = Field(default="6.0.0")
    DESCRIPTION: str = Field(default="Modular SaaS Orchestrator")
    ENVIRONMENT: Environment = Field(default=Environment.DEVELOPMENT)
    
    # Server
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
    WORKERS: int = Field(default=4)
    RELOAD: bool = Field(default=False)
    DEBUG: bool = Field(default=False)
    
    # URLs
    BASE_URL: str = Field(default="http://localhost:8000")
    
    # Database
    DATABASE_URL: str = Field(default="postgresql://user:pass@localhost/db")
    DB_POOL_SIZE: int = Field(default=20)
    DB_MAX_OVERFLOW: int = Field(default=40)
    
    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379")
    CACHE_TTL: int = Field(default=300)
    
    # Security
    SECRET_KEY: str = Field(default="your-secret-key-here")
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    
    # Features
    ENABLE_BETA_FEATURES: bool = Field(default=False)
    ENABLE_SERVICE_DISCOVERY: bool = Field(default=True)
    PROMETHEUS_ENABLED: bool = Field(default=True)
    
    # Performance
    MAX_WORKERS: int = Field(default=10)
    REQUEST_TIMEOUT: int = Field(default=30)
    FAIL_FAST: bool = Field(default=False)
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO")
    ACCESS_LOG: bool = Field(default=True)
    
    # Services
    SERVICES_CONFIG: str = Field(default="config/services.yaml")
    CONSUL_HOST: str = Field(default="localhost")
    CONSUL_PORT: int = Field(default=8500)
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True)
    RATE_LIMIT_PER_MINUTE: int = Field(default=100)
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore"
    }

settings = Settings()
