"""
Logging Configuration Module - FIXED
====================================
"""

import logging
import sys
from pathlib import Path

# Global flag to track if logging is configured
_logging_configured = False

def get_logger(name: str) -> logging.Logger:
    """Get logger instance"""
    return logging.getLogger(name)

def setup_logging(level: str = "INFO"):
    """Setup logging configuration - prevents duplicates"""
    global _logging_configured
    
    if _logging_configured:
        return
    
    _logging_configured = True
    
    # Clear any existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    # Configure root logger
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Single handler to avoid duplicates
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(log_format))
    
    root_logger.setLevel(getattr(logging, level.upper()))
    root_logger.addHandler(handler)
    
    # Reduce noise from libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("telethon").setLevel(logging.INFO)
    
    # Prevent propagation to avoid duplicates
    for logger_name in ["app.services.enhanced_replicator_service", 
                        "app.services.discord_sender",
                        "app.services.file_processor",
                        "app.services.watermark_service"]:
        logger = logging.getLogger(logger_name)
        logger.propagate = False
        logger.addHandler(handler)
