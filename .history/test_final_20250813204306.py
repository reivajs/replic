#!/usr/bin/env python3
"""
🔧 ENVIRONMENT VARIABLES DIAGNOSTICS
===================================
Verifica que las variables de entorno se están cargando correctamente
"""

import os
from pathlib import Path

def check_env_file():
    """Verificar archivo .env"""
    print("📋 CHECKING .ENV FILE")
    print("-" * 50)
    
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found!")
        return False
    
    print(f"✅ .env file exists: {env_file.absolute()}")
    
    # Read content
    content = env_file.read_text()
    lines = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]
    
    print(f"✅ .env file has {len(lines)} non-empty lines")
    
    # Show variables (masked)
    for line in lines:
        if '=' in line:
            key, value = line.split('=', 1)
            if 'HASH' in key:
                display_value = value[:8] + "..." if len(value) > 8 else "***"
            elif 'PHONE' in key:
                display_value = value[:3] + "***" + value[-3:] if len(value) > 6 else "***"
            elif 'WEBHOOK' in key:
                display_value = value[:50] + "..." if len(value) > 50 else value
            else:
                display_value = value
            print(f"   {key}={display_value}")
    
    return True

def check_environment_variables():
    """Verificar variables en el entorno actual"""
    print("\n🔍 CHECKING LOADED ENVIRONMENT VARIABLES")
    print("-" * 50)
    
    required_vars = [
        "TELEGRAM_API_ID",
        "TELEGRAM_API_HASH", 
        "TELEGRAM_PHONE"
    ]
    
    loaded_vars = []
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            loaded_vars.append(var)
            if 'HASH' in var:
                display_value = value[:8] + "..." if len(value) > 8 else "***"
            elif 'PHONE' in var:
                display_value = value[:3] + "***" + value[-3:] if len(value) > 6 else "***"
            else:
                display_value = value
            print(f"✅ {var}={display_value}")
        else:
            missing_vars.append(var)
            print(f"❌ {var}=<NOT LOADED>")
    
    # Check webhook variables
    webhook_vars = []
    for key, value in os.environ.items():
        if key.startswith('WEBHOOK_'):
            webhook_vars.append(key)
            display_value = value[:50] + "..." if len(value) > 50 else value
            print(f"✅ {key}={display_value}")
    
    print(f"\n📊 Summary:")
    print(f"   Required variables loaded: {len(loaded_vars)}/{len(required_vars)}")
    print(f"   Webhook variables found: {len(webhook_vars)}")
    
    return len(missing_vars) == 0

def load_dotenv_manually():
    """Cargar .env manualmente"""
    print("\n🔧 MANUALLY LOADING .ENV FILE")
    print("-" * 50)
    
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ Cannot load .env - file not found")
        return False
    
    try:
        content = env_file.read_text()
        vars_loaded = 0
        
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                os.environ[key] = value
                vars_loaded += 1
                
                # Display loaded variable (masked)
                if 'HASH' in key:
                    display_value = value[:8] + "..." if len(value) > 8 else "***"
                elif 'PHONE' in key:
                    display_value = value[:3] + "***" + value[-3:] if len(value) > 6 else "***"
                elif 'WEBHOOK' in key:
                    display_value = value[:50] + "..." if len(value) > 50 else value
                else:
                    display_value = value
                print(f"✅ Loaded: {key}={display_value}")
        
        print(f"\n✅ Manually loaded {vars_loaded} variables")
        return True
        
    except Exception as e:
        print(f"❌ Error loading .env manually: {e}")
        return False

def test_telegram_connection():
    """Test conexión a Telegram"""
    print("\n📱 TESTING TELEGRAM CONNECTION")
    print("-" * 50)
    
    # Check if variables are loaded
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    phone = os.getenv('TELEGRAM_PHONE')
    
    if not all([api_id, api_hash, phone]):
        print("❌ Missing Telegram credentials")
        return False
    
    try:
        # Try to import telethon
        from telethon import TelegramClient
        print("✅ Telethon library available")
        
        # Create client (don't connect yet)
        client = TelegramClient('test_session', int(api_id), api_hash)
        print("✅ TelegramClient created successfully")
        print(f"✅ API ID: {api_id}")
        print(f"✅ Phone: {phone}")
        
        return True
        
    except ImportError:
        print("❌ Telethon not installed: pip install telethon")
        return False
    except ValueError as e:
        print(f"❌ Invalid API ID: {e}")
        return False
    except Exception as e:
        print(f"❌ Error creating Telegram client: {e}")
        return False

def check_webhook_configuration():
    """Verificar configuración de webhooks"""
    print("\n🔗 CHECKING WEBHOOK CONFIGURATION")
    print("-" * 50)
    
    webhook_vars = {}
    for key, value in os.environ.items():
        if key.startswith('WEBHOOK_'):
            group_id = key.replace('WEBHOOK_', '')
            webhook_vars[group_id] = value
    
    if not webhook_vars:
        print("❌ No webhook variables found")
        return False
    
    print(f"✅ Found {len(webhook_vars)} webhook configurations:")
    for group_id, webhook_url in webhook_vars.items():
        print(f"   Group {group_id}: {webhook_url[:50]}...")
    
    return True

def generate_fix_recommendations():
    """Generar recomendaciones de solución"""
    print("\n🔧 RECOMMENDED FIXES")
    print("-" * 50)
    
    # Check current state
    env_exists = Path(".env").exists()
    vars_loaded = all(os.getenv(var) for var in ["TELEGRAM_API_ID", "TELEGRAM_API_HASH", "TELEGRAM_PHONE"])
    
    if not env_exists:
        print("1. ❌ Create .env file with your Telegram credentials")
        print("2. 🔧 Add these lines to .env:")
        print("   TELEGRAM_API_ID=your_api_id")
        print("   TELEGRAM_API_HASH=your_api_hash")
        print("   TELEGRAM_PHONE=your_phone")
        print("   WEBHOOK_-4989347027=your_discord_webhook")
    elif not vars_loaded:
        print("1. 🔧 Install python-dotenv: pip install python-dotenv")
        print("2. 🔧 Add this to the top of your main.py files:")
        print("   from dotenv import load_dotenv")
        print("   load_dotenv()")
        print("3. 🔧 Or restart your terminal/IDE to reload environment")
    else:
        print("✅ Environment variables are loaded correctly!")
        print("🚀 The issue might be elsewhere - check service logs")

def main():
    """Función principal"""
    print("🔧 ENVIRONMENT VARIABLES DIAGNOSTICS")
    print("=" * 70)
    
    # Step 1: Check .env file
    env_file_ok = check_env_file()
    
    # Step 2: Check loaded variables
    vars_loaded_ok = check_environment_variables()
    
    # Step 3: Try manual loading if needed
    if not vars_loaded_ok and env_file_ok:
        manual_load_ok = load_dotenv_manually()
        if manual_load_ok:
            # Re-check after manual loading
            vars_loaded_ok = check_environment_variables()
    
    # Step 4: Test Telegram connection
    if vars_loaded_ok:
        telegram_ok = test_telegram_connection()
        webhook_ok = check_webhook_configuration()
    
    # Step 5: Generate recommendations
    generate_fix_recommendations()
    
    # Final summary
    print("\n" + "=" * 70)
    print("📊 DIAGNOSTICS SUMMARY")
    print("=" * 70)
    print(f"📋 .env file exists: {'✅' if env_file_ok else '❌'}")
    print(f"🔍 Variables loaded: {'✅' if vars_loaded_ok else '❌'}")
    
    if vars_loaded_ok:
        print("✅ ENVIRONMENT: Ready for Telegram connection")
        print("🚀 Next: Restart your services to pick up the variables")
    else:
        print("❌ ENVIRONMENT: Variables not loaded")
        print("🔧 Follow the recommended fixes above")
    
    print("=" * 70)

if __name__ == "__main__":
    main()