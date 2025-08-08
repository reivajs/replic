"""
Services - Watermark Client
==========================
Cliente para conectar con el microservicio de watermarks
"""

import aiohttp
import asyncio
from typing import Tuple, Optional

class WatermarkClient:
    """Cliente para el microservicio de watermarks"""
    
    def __init__(self, base_url: str = "http://localhost:8081"):
        self.base_url = base_url
        self.session = None
        self._last_check = None
        self._service_available = False
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def is_service_available(self) -> bool:
        """Verificar si el microservicio está disponible (con cache)"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            async with self.session.get(
                f"{self.base_url}/health", 
                timeout=aiohttp.ClientTimeout(total=3)
            ) as response:
                self._service_available = response.status == 200
                return self._service_available
        except:
            self._service_available = False
            return False
    
    async def process_text(self, group_id: int, text: str) -> Tuple[str, bool]:
        """Procesar texto con watermarks"""
        try:
            if not await self.is_service_available():
                return text, False
            
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            data = aiohttp.FormData()
            data.add_field('group_id', str(group_id))
            data.add_field('text', text)
            
            async with self.session.post(
                f"{self.base_url}/process/text", 
                data=data,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    processed_text = result[1]["processed_text"]
                    was_modified = result[0]["processed"]
                    return processed_text, was_modified
                else:
                    return text, False
        except Exception as e:
            print(f"Error processing text: {e}")
            return text, False
    
    async def process_image(self, group_id: int, image_bytes: bytes) -> Tuple[bytes, bool]:
        """Procesar imagen con watermarks"""
        try:
            if not await self.is_service_available():
                return image_bytes, False
            
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            data = aiohttp.FormData()
            data.add_field('group_id', str(group_id))
            data.add_field('file', image_bytes, filename='image.jpg', content_type='image/jpeg')
            
            async with self.session.post(
                f"{self.base_url}/process/image", 
                data=data,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    processed_bytes = await response.read()
                    was_processed = response.headers.get('X-Processed') == 'True'
                    return processed_bytes, was_processed
                else:
                    return image_bytes, False
        except Exception as e:
            print(f"Error processing image: {e}")
            return image_bytes, False
    
    async def process_video(self, group_id: int, video_bytes: bytes) -> Tuple[bytes, bool]:
        """Procesar video con watermarks"""
        try:
            if not await self.is_service_available():
                return video_bytes, False
            
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            data = aiohttp.FormData()
            data.add_field('group_id', str(group_id))
            data.add_field('file', video_bytes, filename='video.mp4', content_type='video/mp4')
            
            async with self.session.post(
                f"{self.base_url}/process/video", 
                data=data,
                timeout=aiohttp.ClientTimeout(total=120)  # 2 minutos para videos
            ) as response:
                if response.status == 200:
                    processed_bytes = await response.read()
                    was_processed = response.headers.get('X-Processed') == 'True'
                    return processed_bytes, was_processed
                else:
                    return video_bytes, False
        except Exception as e:
            print(f"Error processing video: {e}")
            return video_bytes, False

# Cliente global para uso fácil
watermark_client = WatermarkClient()