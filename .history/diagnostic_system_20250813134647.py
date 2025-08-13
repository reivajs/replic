#!/usr/bin/env python3
"""
🔧 Diagnóstico Rápido y Robusto
Versión simplificada sin dependencias complejas
"""

import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime

class QuickDiagnostic:
    """Diagnóstico rápido del sistema"""
    
    def __init__(self):
        self.results = {}
        self.errors = []
        self.warnings = []
        
    def check_python_environment(self):
        """Verificar entorno Python"""
        print("🐍 Verificando entorno Python...")
        
        result = {
            "python_version": sys.version,
            "platform": sys.platform,
            "working_directory": os.getcwd()
        }
        
        # Verificar dependencias
        required_deps = ['telethon', 'fastapi', 'uvicorn', 'aiohttp', 'dotenv']
        missing_deps = []
        
        for dep in required_deps:
            try:
                if dep == 'dotenv':
                    __import__('python_dotenv')
                else:
                    __import__(dep)
                print(f"  ✅ {dep}: Disponible")
            except ImportError:
                print(f"  ❌ {dep}: FALTANTE")
                missing_deps.append(dep)
        
        result["missing_dependencies"] = missing_deps
        
        if missing_deps:
            self.errors.append(f"Dependencias faltantes: {', '.join(missing_deps)}")
            print("\n📦 Para instalar dependencias faltantes:")
            print("pip install fastapi uvicorn telethon aiohttp python-dotenv aiofiles")
        
        self.results["python_env"] = result
        return len(missing_deps) == 0
    
    def check_env_configuration(self):
        """Verificar configuración .env"""
        print("\n📄 Verificando configuración .env...")
        
        env_path = Path('.env')
        if not env_path.exists():
            print("  ❌ Archivo .env NO ENCONTRADO")
            self.errors.append("Archivo .env no encontrado")
            
            print("\n📝 Crea un archivo .env con esta estructura:")
            print("""
# Telegram Configuration
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=tu_hash_de_32_caracteres
TELEGRAM_PHONE=+1234567890

# Discord Webhooks
WEBHOOK_-1001234567890=https://discord.com/api/webhooks/tu_webhook_url
""")
            return False
        
        print("  ✅ Archivo .env encontrado")
        
        # Leer configuración
        config = {}
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip().strip('"\'')
        
        # Verificar campos obligatorios
        required_fields = ['TELEGRAM_API_ID', 'TELEGRAM_API_HASH', 'TELEGRAM_PHONE']
        missing_fields = []
        
        for field in required_fields:
            if field not in config or not config[field]:
                missing_fields.append(field)
                print(f"  ❌ {field}: FALTANTE")
            else:
                # Validaciones específicas
                if field == 'TELEGRAM_API_ID':
                    if config[field].isdigit():
                        print(f"  ✅ {field}: {config[field]}")
                    else:
                        print(f"  ⚠️  {field}: No es numérico")
                        self.warnings.append("TELEGRAM_API_ID debe ser numérico")
                elif field == 'TELEGRAM_API_HASH':
                    if len(config[field]) == 32:
                        print(f"  ✅ {field}: Configurado (32 chars)")
                    else:
                        print(f"  ⚠️  {field}: Longitud incorrecta ({len(config[field])} chars)")
                        self.warnings.append("TELEGRAM_API_HASH debe tener 32 caracteres")
                elif field == 'TELEGRAM_PHONE':
                    if config[field].startswith('+'):
                        print(f"  ✅ {field}: {config[field]}")
                    else:
                        print(f"  ⚠️  {field}: Debe empezar con +")
                        self.warnings.append("TELEGRAM_PHONE debe incluir código de país (+)")
        
        # Verificar webhooks Discord
        webhooks = {k: v for k, v in config.items() if k.startswith('WEBHOOK_')}
        if webhooks:
            print(f"\n💬 Webhooks Discord encontrados: {len(webhooks)}")
            for webhook_key, webhook_url in webhooks.items():
                group_id = webhook_key.replace('WEBHOOK_', '')
                if webhook_url.startswith('https://discord.com/api/webhooks/'):
                    print(f"  ✅ Grupo {group_id}: Webhook válido")
                else:
                    print(f"  ❌ Grupo {group_id}: URL inválida")
                    self.errors.append(f"Webhook {group_id} tiene URL inválida")
        else:
            print("  ❌ No se encontraron webhooks Discord")
            self.errors.append("No hay webhooks Discord configurados")
        
        if missing_fields:
            self.errors.extend([f"{field} no configurado" for field in missing_fields])
        
        self.results["env_config"] = {
            "file_exists": True,
            "missing_fields": missing_fields,
            "webhooks_count": len(webhooks),
            "config": config
        }
        
        return len(missing_fields) == 0 and len(webhooks) > 0
    
    async def test_discord_webhooks(self):
        """Test básico de webhooks Discord"""
        print("\n🔗 Testeando webhooks Discord...")
        
        if "env_config" not in self.results:
            print("  ❌ No hay configuración .env para testear")
            return False
        
        config = self.results["env_config"]["config"]
        webhooks = {k: v for k, v in config.items() if k.startswith('WEBHOOK_')}
        
        if not webhooks:
            print("  ❌ No hay webhooks para testear")
            return False
        
        # Intentar importar aiohttp
        try:
            import aiohttp
        except ImportError:
            print("  ❌ aiohttp no disponible, saltando test de webhooks")
            return False
        
        success_count = 0
        
        for webhook_key, webhook_url in webhooks.items():
            group_id = webhook_key.replace('WEBHOOK_', '')
            
            try:
                test_payload = {
                    "content": f"🔧 **Test de Diagnóstico** - Grupo {group_id} funcionando correctamente",
                    "username": "Sistema Diagnóstico"
                }
                
                print(f"  🔄 Testeando webhook grupo {group_id}...")
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(webhook_url, json=test_payload, timeout=10) as response:
                        if response.status == 204:
                            print(f"  ✅ Grupo {group_id}: Test exitoso")
                            success_count += 1
                        else:
                            print(f"  ❌ Grupo {group_id}: Error HTTP {response.status}")
                            self.errors.append(f"Webhook {group_id}: HTTP {response.status}")
                            
            except Exception as e:
                print(f"  ❌ Grupo {group_id}: Error - {str(e)}")
                self.errors.append(f"Webhook {group_id}: {str(e)}")
        
        print(f"\n📊 Resultado: {success_count}/{len(webhooks)} webhooks funcionando")
        
        self.results["discord_test"] = {
            "total_webhooks": len(webhooks),
            "working_webhooks": success_count
        }
        
        return success_count > 0
    
    def check_file_structure(self):
        """Verificar estructura de archivos"""
        print("\n📁 Verificando estructura de archivos...")
        
        # Archivos importantes
        important_files = {
            'main.py': "Archivo principal del sistema",
            'requirements.txt': "Lista de dependencias",
            '.env': "Configuración del sistema"
        }
        
        # Directorios importantes
        important_dirs = {
            'logs': "Directorio de logs",
            'media': "Directorio de archivos temporales",
            'app': "Directorio de aplicación",
            'app/services': "Servicios de la aplicación"
        }
        
        files_ok = 0
        dirs_ok = 0
        
        for file_name, description in important_files.items():
            if Path(file_name).exists():
                print(f"  ✅ {file_name}: Existe")
                files_ok += 1
            else:
                print(f"  ❌ {file_name}: Faltante ({description})")
        
        for dir_name, description in important_dirs.items():
            if Path(dir_name).exists():
                print(f"  ✅ {dir_name}/: Existe")
                dirs_ok += 1
            else:
                print(f"  ⚠️  {dir_name}/: Faltante ({description})")
        
        self.results["file_structure"] = {
            "files_found": files_ok,
            "files_total": len(important_files),
            "dirs_found": dirs_ok,
            "dirs_total": len(important_dirs)
        }
        
        return files_ok >= 2  # Al menos .env y requirements.txt
    
    async def run_full_diagnostic(self):
        """Ejecutar diagnóstico completo"""
        print("🔧 Sistema de Diagnóstico Rápido v2.0")
        print("=" * 60)
        
        # Test 1: Entorno Python
        python_ok = self.check_python_environment()
        
        # Test 2: Configuración .env
        env_ok = self.check_env_configuration()
        
        # Test 3: Estructura de archivos
        files_ok = self.check_file_structure()
        
        # Test 4: Webhooks Discord (solo si env está OK)
        discord_ok = False
        if env_ok:
            discord_ok = await self.test_discord_webhooks()
        
        return {
            "python_environment": python_ok,
            "env_configuration": env_ok,
            "file_structure": files_ok,
            "discord_webhooks": discord_ok
        }
    
    def print_summary(self, test_results):
        """Mostrar resumen final"""
        print("\n" + "=" * 60)
        print("📊 RESUMEN DEL DIAGNÓSTICO")
        print("=" * 60)
        
        # Calcular score
        total_tests = len(test_results)
        passed_tests = sum(1 for result in test_results.values() if result)
        score = (passed_tests / total_tests) * 100
        
        print(f"\n🎯 SCORE GENERAL: {score:.1f}% ({passed_tests}/{total_tests} tests pasados)")
        
        # Estado por test
        test_names = {
            "python_environment": "🐍 Entorno Python",
            "env_configuration": "📄 Configuración .env",
            "file_structure": "📁 Estructura de archivos",
            "discord_webhooks": "💬 Webhooks Discord"
        }
        
        print(f"\n📋 DETALLE POR TEST:")
        for test_key, passed in test_results.items():
            icon = "✅" if passed else "❌"
            name = test_names.get(test_key, test_key)
            print(f"  {icon} {name}: {'PASÓ' if passed else 'FALLÓ'}")
        
        # Mostrar errores
        if self.errors:
            print(f"\n❌ ERRORES ENCONTRADOS ({len(self.errors)}):")
            for error in self.errors:
                print(f"  • {error}")
        
        # Mostrar warnings
        if self.warnings:
            print(f"\n⚠️ ADVERTENCIAS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        # Recomendaciones
        print(f"\n💡 PRÓXIMOS PASOS:")
        
        if not test_results["python_environment"]:
            print(f"  1. Instalar dependencias: pip install -r requirements.txt")
        
        if not test_results["env_configuration"]:
            print(f"  2. Configurar .env con credenciales de Telegram y webhooks Discord")
        
        if not test_results["file_structure"]:
            print(f"  3. Ejecutar auto-reparación: python auto_repair_system.py")
        
        if not test_results["discord_webhooks"] and test_results["env_configuration"]:
            print(f"  4. Verificar URLs de webhooks Discord en el servidor")
        
        if score >= 75:
            print(f"\n🎉 ¡SISTEMA EN BUEN ESTADO!")
            print(f"▶️  Puedes ejecutar: python run.py")
        else:
            print(f"\n⚠️ SISTEMA NECESITA REPARACIONES")
            print(f"🔧 Ejecuta: python auto_repair_system.py")
        
        print("\n" + "=" * 60)

async def main():
    """Función principal"""
    diagnostic = QuickDiagnostic()
    test_results = await diagnostic.run_full_diagnostic()
    diagnostic.print_summary(test_results)
    
    # Guardar resultados
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    with open(f'diagnostic_quick_{timestamp}.txt', 'w') as f:
        f.write(f"Diagnóstico rápido - {datetime.now()}\n")
        f.write(f"Score: {sum(test_results.values())}/{len(test_results)}\n")
        f.write(f"Errores: {len(diagnostic.errors)}\n")
        f.write(f"Warnings: {len(diagnostic.warnings)}\n")
        for test, result in test_results.items():
            f.write(f"{test}: {'PASS' if result else 'FAIL'}\n")
    
    return test_results

if __name__ == "__main__":
    asyncio.run(main())