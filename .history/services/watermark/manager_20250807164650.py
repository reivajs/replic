"""
Services - Watermark Manager v3.0 (Simplified)
==============================================
Versión simplificada para quick setup
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, Optional, Tuple, Any, List
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from utils.logger import setup_logger

logger = setup_logger(__name__)

class WatermarkType(Enum):
    NONE = "none"
    TEXT = "text"
    PNG = "png" 
    BOTH = "both"

class Position(Enum):
    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"
    CENTER = "center"
    CUSTOM = "custom"

@dataclass
class WatermarkConfig:
    group_id: int
    watermark_type: WatermarkType = WatermarkType.NONE
    text_content: str = ""
    text_enabled: bool = False
    png_enabled: bool = False
    png_path: Optional[str] = None
    video_enabled: bool = False
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

class WatermarkManager:
    """Watermark Manager simplificado para quick setup"""
    
    def __init__(self, config_dir: Path = Path("config")):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self.configs: Dict[int, WatermarkConfig] = {}
        self.can_process_images = PIL_AVAILABLE
        
        logger.info("🎨 WatermarkManager (simplified) inicializado")
    
    def create_group_config(self, group_id: int, **kwargs) -> WatermarkConfig:
        config = WatermarkConfig(group_id=group_id, **kwargs)
        self.configs[group_id] = config
        return config
    
    def get_group_config(self, group_id: int) -> Optional[WatermarkConfig]:
        return self.configs.get(group_id)
    
    def get_all_configs(self) -> Dict[int, WatermarkConfig]:
        return self.configs.copy()
    
    async def process_text_message(self, text: str, group_id: int) -> Tuple[str, bool]:
        config = self.get_group_config(group_id)
        if not config or not config.text_enabled or not config.text_content:
            return text, False
        
        processed = f"{text}\n\n{config.text_content.strip()}"
        return processed, True
    
    async def process_image(self, image_bytes: bytes, group_id: int) -> Tuple[bytes, bool]:
        # Versión simplificada - retorna imagen original
        return image_bytes, False
    
    async def process_video(self, video_bytes: bytes, group_id: int) -> Tuple[bytes, bool]:
        # Versión simplificada - retorna video original  
        return video_bytes, False
    
    def health_check(self) -> Dict[str, Any]:
        return {
            "status": "healthy",
            "capabilities": {
                "images": self.can_process_images,
                "videos": False  # Simplificado
            }
        }
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "processing": {
                "total_processed": 0,
                "images_processed": 0,
                "videos_processed": 0
            },
            "groups_configured": len(self.configs)
        }

def create_watermark_manager(config_dir: Path = None, **kwargs) -> WatermarkManager:
    return WatermarkManager(config_dir or Path("config"))
