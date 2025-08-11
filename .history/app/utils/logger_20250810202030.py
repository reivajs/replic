"""
🔧 LOGGER ENTERPRISE - FALTANTE CRÍTICO
=======================================
Archivo: app/utils/logger.py

Este archivo es necesario para que funcionen los otros artefacts
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    Configurar logger enterprise con formato consistente
    """
    # Crear directorio de logs si no existe
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configurar logger
    logger = logging.getLogger(name)
    
    # Evitar duplicar handlers
    if logger.handlers:
        return logger
    
    # Configurar nivel
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Formato enterprise
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Handler para archivo (opcional)
    try:
        log_file = log_dir / f"replicator_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        # Si falla el archivo, continuar solo con consola
        logger.warning(f"No se pudo configurar log de archivo: {e}")
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """Obtener logger existente o crear uno nuevo"""
    return setup_logger(name)