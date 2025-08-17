"""Custom JSON Encoder"""
import json
from datetime import datetime, date, time, timedelta
from decimal import Decimal
from typing import Any

class CustomJSONEncoder(json.JSONEncoder):
    """Encoder para tipos no serializables"""
    
    def default(self, obj: Any) -> Any:
        if isinstance(obj, (datetime, date, time)):
            return obj.isoformat()
        elif isinstance(obj, timedelta):
            return str(obj)
        elif isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, set):
            return list(obj)
        elif isinstance(obj, bytes):
            return obj.decode('utf-8', errors='ignore')
        elif hasattr(obj, 'to_dict'):
            return obj.to_dict()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        return super().default(obj)

def safe_json_response(data: Any) -> dict:
    """Convertir a JSON seguro"""
    try:
        json.dumps(data, cls=CustomJSONEncoder)
        return data
    except Exception as e:
        return {
            "error": "Serialization error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }
