"""Adaptador para compatibilidad con código existente"""
from app.services.registry.service_registry import ServiceRegistry, get_registry

# Export para compatibilidad
__all__ = ['ServiceRegistry', 'get_registry']
