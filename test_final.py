#!/usr/bin/env python3
"""
🧪 Test Específico para tu Sistema
Prueba tu configuración exacta
"""

import os
import asyncio
import sys
from pathlib import Path

# Cargar variables de entorno
sys.path.append('.')
from dotenv import load_dotenv
load_dotenv()

async def test_telegram_connection():
    """Test conexión Telegram con tus credenciales exactas"""
    print("📱 Testeando conexión Telegram...")
    
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH') 
    phone = os.getenv('TELEGRAM_PHONE')
    
    print(f"  📋 API ID: {api_id}")
    print(f"  📋 Teléfono: {phone}")
    
    try:
        from telethon import TelegramClient
        
        client = TelegramClient('test_session', int(api_id), api_hash)
        await client.start(phone=phone)
        
        me = await client.get_me()
        print(f"  ✅ Conectado como: {me.first_name} (@{me.username or 'sin_username'})")
        
        # Listar algunos grupos disponibles
        print("  📋 Algunos grupos disponibles:")
        count = 0
        async for dialog in client.iter_dialogs(limit=10):
            if dialog.is_group or dialog.is_channel:
                print(f"    • {dialog.title} (ID: {dialog.id})")
                count += 1
        
        if count == 0:
            print("    ⚠️ No se encontraron grupos. Asegúrate de estar en grupos de Telegram.")
        
        await client.disconnect()
        return True
        
    except Exception as e:
        print(f"  ❌ Error conectando Telegram: {e}")
        return False

async def test_discord_webhook_creation():
    """Ayuda para crear nuevos webhooks Discord"""
    print("\n💬 Testeando configuración Discord...")
    
    webhooks = {}
    for key, value in os.environ.items():
        if key.startswith('WEBHOOK_'):
            group_id = key.replace('WEBHOOK_', '')
            webhooks[group_id] = value
    
    print(f"  📋 Webhooks configurados: {len(webhooks)}")
    
    if not webhooks:
        print("  ❌ No hay webhooks configurados")
        return False
    
    try:
        import aiohttp
        
        working_webhooks = []
        
        for group_id, webhook_url in webhooks.items():
            print(f"  🔄 Testeando grupo {group_id}...")
            
            try:
                test_payload = {
                    "content": f"🧪 **Test Final** - Grupo {group_id} - Sistema listo para replicar!",
                    "username": "Sistema Test Final"
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(webhook_url, json=test_payload, timeout=10) as response:
                        if response.status == 204:
                            print(f"    ✅ Grupo {group_id}: ¡FUNCIONANDO!")
                            working_webhooks.append(group_id)
                        else:
                            print(f"    ❌ Grupo {group_id}: Error HTTP {response.status}")
                            print(f"    💡 Necesitas crear nuevo webhook para este grupo")
                            
            except Exception as e:
                print(f"    ❌ Grupo {group_id}: {str(e)}")
                print(f"    💡 Webhook probablemente eliminado, crear uno nuevo")
        
        return len(working_webhooks) > 0
        
    except ImportError:
        print("  ❌ aiohttp no disponible")
        return False

async def test_complete_flow():
    """Test del flujo completo"""
    print("\n🔄 Test del flujo completo...")
    
    # Test 1: Telegram
    telegram_ok = await test_telegram_connection()
    
    # Test 2: Discord  
    discord_ok = await test_discord_webhook_creation()
    
    print(f"\n" + "="*50)
    print("📊 RESULTADO FINAL")
    print("="*50)
    
    if telegram_ok and discord_ok:
        print("🎉 ¡SISTEMA COMPLETAMENTE FUNCIONANDO!")
        print("▶️  Ejecutar: python main.py")
        print("🌐 Dashboard: http://localhost:8000/dashboard")
    elif telegram_ok:
        print("✅ Telegram: OK")  
        print("❌ Discord: Necesita webhooks nuevos")
        print("🔧 Sigue la guía para crear webhooks Discord")
    elif discord_ok:
        print("✅ Discord: OK")
        print("❌ Telegram: Problema de conexión")
        print("🔧 Revisa credenciales de Telegram")
    else:
        print("❌ Ambos servicios necesitan configuración")
        print("🔧 Revisa credenciales y webhooks")
    
    return telegram_ok and discord_ok

if __name__ == "__main__":
    asyncio.run(test_complete_flow())
