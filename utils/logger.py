"""
Utils - Logger Setup
==================
Configuración de logging para el sistema
"""

import logging
import sys
from pathlib import Path

def setup_logger(name: str) -> logging.Logger:
    """Setup logger con formato consistente"""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # Handler para consola
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    return logger
