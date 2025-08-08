"""
App Utils Logger
===============
Configuración de logging para el sistema
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """Configurar logger para el sistema"""
    
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # Crear directorio de logs si no existe
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # Handler para consola
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        # Handler para archivo
        file_handler = logging.FileHandler(
            logs_dir / f"replicator_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        
        # Añadir handlers
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
        # Configurar nivel
        logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    return logger