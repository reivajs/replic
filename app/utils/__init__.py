"""Utils Module"""
try:
    from .json_encoder import CustomJSONEncoder, safe_json_response
except ImportError:
    CustomJSONEncoder = None
    safe_json_response = None

__all__ = ['CustomJSONEncoder', 'safe_json_response']
