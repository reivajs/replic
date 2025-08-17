"""
Custom Exceptions Module
========================
"""

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

class ServiceUnavailableError(Exception):
    """Service unavailable error"""
    pass

class ConfigurationError(Exception):
    """Configuration error"""
    pass

class AuthenticationError(Exception):
    """Authentication error"""
    pass

def setup_exception_handlers(app):
    """Setup global exception handlers"""
    
    @app.exception_handler(ServiceUnavailableError)
    async def service_unavailable_handler(request: Request, exc: ServiceUnavailableError):
        logger.error(f"Service unavailable: {exc}")
        return JSONResponse(
            status_code=503,
            content={"detail": str(exc)}
        )
    
    @app.exception_handler(ConfigurationError)
    async def configuration_error_handler(request: Request, exc: ConfigurationError):
        logger.error(f"Configuration error: {exc}")
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc)}
        )
    
    @app.exception_handler(AuthenticationError)
    async def auth_error_handler(request: Request, exc: AuthenticationError):
        return JSONResponse(
            status_code=401,
            content={"detail": str(exc)}
        )
