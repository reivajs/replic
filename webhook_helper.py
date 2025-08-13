#!/usr/bin/env python3
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
        
        print("\n📝 NUEVO CONTENIDO PARA .env:")
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
    
    print("\n📖 PASOS:")
    print("1. Ve a Discord → Tu servidor → Configuración")
    print("2. Integraciones → Webhooks → Crear webhook")
    print("3. Elige el canal donde quieres recibir mensajes")
    print("4. Copia la URL del webhook")
    print("5. Pega la URL aquí")
    
    new_webhooks = {}
    
    for group_id in required_groups:
        print(f"\n🔧 Configurando webhook para grupo {group_id}:")
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
        print(f"\n🎉 {len(new_webhooks)} webhooks configurados exitosamente!")
        
        # Generar template para .env
        group_ids = list(new_webhooks.keys())
        webhook_urls = list(new_webhooks.values())
        helper.generate_env_template(group_ids, webhook_urls)
        
        print(f"\n▶️ Después de actualizar .env, ejecuta: python test_final.py")
    else:
        print("\n❌ No se configuraron webhooks válidos")

if __name__ == "__main__":
    asyncio.run(interactive_webhook_setup())
