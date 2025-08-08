import logging
import sys
from pathlib import Path

def setup_logger(name: str, service_name: str = None) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if logger.handlers:
        return logger
    
    formatter = logging.Formatter(f'{service_name or name} - %(levelname)s - %(message)s')
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger