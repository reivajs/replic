"""
Servicios Enterprise Unificados
===============================
Archivo: app/services/__init__.py

Exporta todos los servicios enterprise para facilitar imports
"""

# Importar servicios enterprise
from .discord_sender import DiscordSenderEnhanced
from .file_processor import FileProcessorEnhanced
from .watermark_service import WatermarkServiceIntegrated

# Mantener compatibilidad con nombre original
FileProcessorService = FileProcessorEnhanced

# Alias para facilitar imports
__all__ = [
    'DiscordSenderEnhanced',
    'FileProcessorEnhanced', 
    'FileProcessorService',  # Compatibilidad
    'WatermarkServiceIntegrated'
]