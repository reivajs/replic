#!/usr/bin/env python3
"""
🛠️ Reparación Instantánea del Sistema
Soluciona los problemas identificados en el diagnóstico
"""

import os
import sys
import subprocess
import asyncio
from pathlib import Path

class InstantFix:
    """Reparación instantánea"""
    
    def __init__(self):
        self.fixes_applied = []
        
    def fix_dependencies(self):
        """Solucionar dependencias faltantes"""
        print("📦 Instalando dependencias faltantes...")
        
        try:
            # Instalar python-dotenv específicamente
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "python-dotenv", "aiofiles"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("  ✅ python-dotenv instalado correctamente")
                self.fixes_applied.append("✅ Dependencias instaladas")
                return True
            else:
                print(f"  ❌ Error instalando: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False
    
    def create_missing_directories(self):
        """Crear directorios faltantes"""
        print("📁 Creando directorios faltantes...")
        
        required_dirs = ['media', 'temp', 'data', 'sessions']
        
        for dir_name in required_dirs:
            dir_path = Path(dir_name)
            if not dir_path.exists():
                try:
                    dir_path.mkdir(exist_ok=True)
                    print(f"  ✅ {dir_name}/ creado")
                except Exception as e:
                    print(f"  ❌ Error creando {dir_name}: {e}")
        
        self.fixes_applied.append("✅ Directorios creados")
        return True
    
    def fix_discord_webhooks_guide(self):
        """Guía para arreglar webhooks Discord"""
        print("💬 Guía para reparar webhooks Discord...")
        
        print("""
🔧 TUS WEBHOOKS DISCORD ESTÁN RETORNANDO 404 (ELIMINADOS O DESHABILITADOS)

📋 PASOS PARA SOLUCIONARLO:

1️⃣ Ve a tu servidor Discord
2️⃣ Configuración del servidor → Integraciones → Webhooks
3️⃣ Elimina los webhooks antiguos (si existen)
4️⃣ Crear nuevos webhooks:
   • Canal donde quieres recibir mensajes
   • Botón derecho → Editar canal → Integraciones → Webhooks
   • "Crear webhook" 
   • Copiar URL del webhook

5️⃣ Actualizar .env con las nuevas URLs:
   WEBHOOK_-4989347027=https://discord.com/api/webhooks/NUEVA_URL_1
   WEBHOOK_-1001697798998=https://discord.com/api/webhooks/NUEVA_URL_2

⚠️ IMPORTANTE: Los webhooks expiran o se eliminan automáticamente si:
   - No se usan por mucho tiempo
   - Se regenera el token del bot
   - Se elimina el canal asociado
        """)
        
        self.fixes_applied.append("⚠️ Guía webhooks Discord proporcionada")
        return True
    
    def create_test_runner(self):
        """Crear script de test mejorado"""
        print("🧪 Creando script de test mejorado...")
        
        test_content = '''#!/usr/bin/env python3
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
    print("\\n💬 Testeando configuración Discord...")
    
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
    print("\\n🔄 Test del flujo completo...")
    
    # Test 1: Telegram
    telegram_ok = await test_telegram_connection()
    
    # Test 2: Discord  
    discord_ok = await test_discord_webhook_creation()
    
    print(f"\\n" + "="*50)
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
'''
        
        Path('test_final.py').write_text(test_content)
        print("  ✅ test_final.py creado")
        self.fixes_applied.append("✅ Script de test final creado")
        return True
    
    def create_webhook_helper(self):
        """Crear helper para webhooks Discord"""
        print("🔗 Creando helper para webhooks Discord...")
        
        webhook_helper = '''#!/usr/bin/env python3
"""
🔗 Discord Webhook Helper
Ayuda a crear y testear webhooks Discord
"""

import asyncio
import aiohttp

class WebhookHelper:
    """Helper para webhooks Discord"""
    
    async def test_webhook(self, webhook_url: str, group_name: str = "Test"):
        """Testear un webhook específico"""
        try:
            test_payload = {
                "content": f"🔧 **Webhook Test** - {group_name} configurado correctamente!",
                "username": "Webhook Helper"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=test_payload, timeout=10) as response:
                    if response.status == 204:
                        print(f"✅ Webhook {group_name}: FUNCIONANDO")
                        return True
                    else:
                        print(f"❌ Webhook {group_name}: Error HTTP {response.status}")
                        return False
                        
        except Exception as e:
            print(f"❌ Webhook {group_name}: Error - {str(e)}")
            return False
    
    def generate_env_template(self, group_ids: list, webhook_urls: list):
        """Generar template .env con nuevos webhooks"""
        if len(group_ids) != len(webhook_urls):
            print("❌ Número de grupos y webhooks no coincide")
            return
        
        print("\\n📝 NUEVO CONTENIDO PARA .env:")
        print("# Copiar estas líneas a tu archivo .env")
        print("-" * 50)
        
        for group_id, webhook_url in zip(group_ids, webhook_urls):
            print(f"WEBHOOK_{group_id}={webhook_url}")
        
        print("-" * 50)
        print("💾 Copia estas líneas y reemplaza las antiguas en tu .env")

async def interactive_webhook_setup():
    """Setup interactivo de webhooks"""
    print("🔗 Discord Webhook Setup Interactivo")
    print("=" * 50)
    
    helper = WebhookHelper()
    
    # Grupos que necesitas configurar
    required_groups = ["-4989347027", "-1001697798998"]
    
    print("📋 Necesitas configurar webhooks para estos grupos:")
    for group in required_groups:
        print(f"  • Grupo {group}")
    
    print("\\n📖 PASOS:")
    print("1. Ve a Discord → Tu servidor → Configuración")
    print("2. Integraciones → Webhooks → Crear webhook")
    print("3. Elige el canal donde quieres recibir mensajes")
    print("4. Copia la URL del webhook")
    print("5. Pega la URL aquí")
    
    new_webhooks = {}
    
    for group_id in required_groups:
        print(f"\\n🔧 Configurando webhook para grupo {group_id}:")
        webhook_url = input(f"Pega la URL del webhook para grupo {group_id}: ").strip()
        
        if webhook_url and webhook_url.startswith('https://discord.com/api/webhooks/'):
            print(f"🔄 Testeando webhook...")
            success = await helper.test_webhook(webhook_url, f"Grupo_{group_id}")
            
            if success:
                new_webhooks[group_id] = webhook_url
                print(f"✅ Webhook grupo {group_id} configurado correctamente")
            else:
                print(f"❌ Webhook grupo {group_id} no funciona, verifica la URL")
        else:
            print(f"❌ URL inválida para grupo {group_id}")
    
    if new_webhooks:
        print(f"\\n🎉 {len(new_webhooks)} webhooks configurados exitosamente!")
        
        # Generar template para .env
        group_ids = list(new_webhooks.keys())
        webhook_urls = list(new_webhooks.values())
        helper.generate_env_template(group_ids, webhook_urls)
        
        print(f"\\n▶️ Después de actualizar .env, ejecuta: python test_final.py")
    else:
        print("\\n❌ No se configuraron webhooks válidos")

if __name__ == "__main__":
    asyncio.run(interactive_webhook_setup())
'''
        
        Path('webhook_helper.py').write_text(webhook_helper)
        print("  ✅ webhook_helper.py creado")
        self.fixes_applied.append("✅ Helper webhooks creado")
        return True
    
    async def run_instant_fix(self):
        """Ejecutar todas las reparaciones"""
        print("🛠️ Reparación Instantánea del Sistema")
        print("=" * 50)
        
        # Fix 1: Dependencias
        deps_ok = self.fix_dependencies()
        
        # Fix 2: Directorios
        dirs_ok = self.create_missing_directories()
        
        # Fix 3: Guía webhooks
        webhook_guide_ok = self.fix_discord_webhooks_guide()
        
        # Fix 4: Scripts de ayuda
        test_ok = self.create_test_runner()
        helper_ok = self.create_webhook_helper()
        
        print("\n" + "=" * 50)
        print("📊 RESUMEN DE REPARACIONES")
        print("=" * 50)
        
        for fix in self.fixes_applied:
            print(f"  {fix}")
        
        print("\n🎯 PRÓXIMOS PASOS:")
        print("1️⃣ Crear nuevos webhooks Discord:")
        print("   python webhook_helper.py")
        print("\n2️⃣ Test completo del sistema:")
        print("   python test_final.py")
        print("\n3️⃣ Si todo funciona, ejecutar:")
        print("   python main.py")
        
        return True

async def main():
    """Función principal"""
    fix_system = InstantFix()
    await fix_system.run_instant_fix()
    
    print(f"\n🎉 ¡REPARACIÓN COMPLETADA!")
    print(f"📋 Siguiente paso: python webhook_helper.py")

if __name__ == "__main__":
    asyncio.run(main())
