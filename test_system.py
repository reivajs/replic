#!/usr/bin/env python3
"""
Test Script - Probar sistema rápidamente
======================================
"""

import asyncio
import sys
from pathlib import Path

# Añadir paths
sys.path.append(".")
sys.path.append("services")

async def test_configuration():
    """Test básico de configuración"""
    try:
        print("🧪 Probando configuración...")
        
        # Test app.config.settings
        from app.config.settings import get_settings
        settings = get_settings()
        print(f"✅ Settings cargados: Telegram configurado: {settings.telegram.api_id > 0}")
        
        # Test watermark client
        try:
            from watermark_client import WatermarkClient
            client = WatermarkClient()
            available = await client.is_service_available()
            print(f"🎨 Watermark service: {'✅ Disponible' if available else '❌ No disponible'}")
        except Exception as e:
            print(f"⚠️ Watermark client: {e}")
        
        # Test Discord sender
        try:
            from discord.sender import DiscordSenderService
            print("📤 Discord sender: ✅ Disponible")
        except Exception as e:
            print(f"⚠️ Discord sender: {e}")
        
        print("\n🎯 Para iniciar el sistema:")
        print("   python main.py")
        print("   (o python start_system.py para iniciar todo)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        return False

def main():
    """Test principal"""
    print("🧪 Ejecutando tests de configuración...")
    success = asyncio.run(test_configuration())
    
    if success:
        print("\n✅ Configuración OK - El sistema debería funcionar")
    else:
        print("\n❌ Hay problemas en la configuración")

if __name__ == "__main__":
    main()
