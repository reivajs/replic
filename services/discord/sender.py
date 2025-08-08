"""
Services Discord Sender - Implementación básica
==============================================
"""

import aiohttp
import asyncio
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class DiscordMessage:
    content: Optional[str] = None
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = {}
        if self.content:
            data['content'] = self.content
        if self.username:
            data['username'] = self.username
        if self.avatar_url:
            data['avatar_url'] = self.avatar_url
        return data

@dataclass
class SendResult:
    success: bool
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    processing_time: float = 0.0

class DiscordSenderService:
    """Servicio básico de envío a Discord"""
    
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def send_text_message(self, webhook_url: str, message: DiscordMessage) -> SendResult:
        """Enviar mensaje de texto"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            payload = message.to_dict()
            
            async with self.session.post(webhook_url, json=payload) as response:
                return SendResult(
                    success=response.status == 204,
                    status_code=response.status
                )
        except Exception as e:
            return SendResult(success=False, error_message=str(e))
    
    async def send_image_message(self, webhook_url: str, image_bytes: bytes, 
                               caption: str = "", filename: str = "image.jpg") -> SendResult:
        """Enviar imagen"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            data = aiohttp.FormData()
            if caption:
                data.add_field('content', caption)
            data.add_field('file', image_bytes, filename=filename, content_type='image/jpeg')
            
            async with self.session.post(webhook_url, data=data) as response:
                return SendResult(
                    success=response.status == 200,
                    status_code=response.status
                )
        except Exception as e:
            return SendResult(success=False, error_message=str(e))
    
    async def send_video_message(self, webhook_url: str, video_bytes: bytes,
                               caption: str = "", filename: str = "video.mp4") -> SendResult:
        """Enviar video"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            data = aiohttp.FormData()
            if caption:
                data.add_field('content', caption)
            data.add_field('file', video_bytes, filename=filename, content_type='video/mp4')
            
            async with self.session.post(webhook_url, data=data) as response:
                return SendResult(
                    success=response.status == 200,
                    status_code=response.status
                )
        except Exception as e:
            return SendResult(success=False, error_message=str(e))
