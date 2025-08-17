from enum import Enum
from typing import Optional
from pydantic import BaseSettings, validator

class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Enterprise Orchestrator"
    VERSION: str = "6.0.0"
    DESCRIPTION: str = "Modular SaaS Orchestrator"
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    RELOAD: bool = False
    
    # URLs
    BASE_URL: str = "http://localhost:8000"
    
    # Database
    DATABASE_URL: str = "postgresql://user:pass@localhost/db"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 40
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    CACHE_TTL: int = 300
    
    # Services
    SERVICES_CONFIG: str = "config/services.yaml"
    ENABLE_SERVICE_DISCOVERY: bool = True
    CONSUL_HOST: str = "localhost"
    CONSUL_PORT: int = 8500
    
    # Security
    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Features
    ENABLE_BETA_FEATURES: bool = False
    ENABLE_METRICS: bool = True
    PROMETHEUS_ENABLED: bool = True
    
    # Performance
    MAX_WORKERS: int = 10
    REQUEST_TIMEOUT: int = 30
    FAIL_FAST: bool = False
    
    # Logging
    LOG_LEVEL: str = "INFO"
    ACCESS_LOG: bool = True
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 100
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()