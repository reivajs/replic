"""WebSocket Module"""
try:
    from .enhanced_manager import websocket_manager
except ImportError:
    websocket_manager = None

__all__ = ['websocket_manager']
