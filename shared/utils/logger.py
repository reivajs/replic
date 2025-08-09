"""
📝 SHARED LOGGER v4.0
====================
Sistema de logging centralizado para microservicios
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

def setup_logger(name: str, service_name: str = "system", log_level: str = "INFO") -> logging.Logger:
    """
    Configurar logger para microservicios
    
    Args:
        name: Nombre del logger (generalmente __name__)
        service_name: Nombre del servicio para identificación
        log_level: Nivel de logging
    
    Returns:
        Logger configurado
    """
    
    # Crear directorio de logs
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configurar logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Evitar duplicar handlers
    if logger.handlers:
        return logger
    
    # Formato de logs
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger
