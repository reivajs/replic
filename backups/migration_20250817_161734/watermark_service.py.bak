"""
Watermark Service - FIXED
=========================
"""

import logging
from typing import Dict, Any, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
import io

logger = logging.getLogger(__name__)

class WatermarkServiceIntegrated:
    """Watermark service integrado y corregido"""
    
    def __init__(self):
        self.enabled = True
        self.default_text = "Replicated"
        self.opacity = 0.3
        self.position = "bottom-right"
        logger.info("🎨 Watermark Service initialized")
    
    async def initialize(self):
        """Initialize service"""
        logger.info("✅ Watermark Service initialized successfully")
        return True
    
    async def process_text(self, text: str, config: Optional[Dict[str, Any]] = None) -> str:
        """Process text with optional transformations"""
        try:
            # Si config es un entero (group_id), crear config por defecto
            if isinstance(config, int):
                config = {"group_id": config}
            
            if not config:
                config = {}
            
            # Aplicar transformaciones si están configuradas
            if config.get("add_prefix"):
                text = f"{config['add_prefix']} {text}"
            
            if config.get("add_suffix"):
                text = f"{text} {config['add_suffix']}"
            
            return text
            
        except Exception as e:
            logger.error(f"Error processing text: {e}")
            return text  # Retornar texto original si hay error
    
    async def add_watermark_to_image(
        self, 
        image_bytes: bytes, 
        watermark_text: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """Add watermark to image"""
        try:
            # Si config es un entero, crear config por defecto
            if isinstance(config, int):
                config = {"group_id": config}
            
            if not self.enabled:
                return image_bytes
            
            # Open image
            img = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGBA if needed
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Create watermark layer
            watermark = Image.new('RGBA', img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(watermark)
            
            # Watermark text
            text = watermark_text or self.default_text
            
            # Try to use a font, fallback to default
            try:
                font_size = min(img.width, img.height) // 20
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
            except:
                font = ImageFont.load_default()
            
            # Get text bbox
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Calculate position
            margin = 10
            if self.position == "bottom-right":
                x = img.width - text_width - margin
                y = img.height - text_height - margin
            elif self.position == "bottom-left":
                x = margin
                y = img.height - text_height - margin
            elif self.position == "top-right":
                x = img.width - text_width - margin
                y = margin
            else:  # top-left
                x = margin
                y = margin
            
            # Draw text
            draw.text((x, y), text, fill=(255, 255, 255, int(255 * self.opacity)), font=font)
            
            # Composite
            watermarked = Image.alpha_composite(img, watermark)
            
            # Save to bytes
            output = io.BytesIO()
            watermarked.save(output, format='PNG')
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error adding watermark: {e}")
            return image_bytes  # Return original if error
    
    async def process_with_config(self, data: Any, config: Dict[str, Any]) -> Any:
        """Process with configuration"""
        # Compatibility method
        return data
