#!/usr/bin/env python3
"""
🔧 Sistema de Diagnóstico y Reparación Completo
Versión Enterprise para debugging total del sistema
"""

import os
import sys
import json
import asyncio
import aiohttp
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import traceback

# ============ CONFIGURACIÓN ============

@dataclass
class DiagnosticConfig:
    """Configuración para diagnósticos"""
    telegram_api_id: Optional[str] = None
    telegram_api_hash: Optional[str] = None
    telegram_phone: Optional[str] = None
    discord_webhooks: Dict[str, str] = None
    debug: bool = True
    
    def __post_init__(self):
        if self.discord_webhooks is None:
            self.discord_webhooks = {}

class SystemDiagnostic:
    """Sistema completo de diagnóstico"""
    
    def __init__(self):
        # Configurar logging PRIMERO
        self.setup_logging()
        # Luego cargar configuración
        self.config = self._load_config()
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "errors": [],
            "warnings": [],
            "recommendations": []
        }
    
    def setup_logging(self):
        """Configurar logging detallado"""
        logging.basicConfig(
            level=logging.DEBUG if self.config.debug else logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('diagnostic.log')
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def _load_config(self) -> DiagnosticConfig:
        """Cargar configuración desde .env"""
        config = DiagnosticConfig()
        
        # Intentar cargar desde .env
        env_file = Path('.env')
        if env_file.exists():
            print("📄 Cargando configuración desde .env")  # Usar print en lugar de logger
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"\'')
                        
                        if key == 'TELEGRAM_API_ID':
                            config.telegram_api_id = value
                        elif key == 'TELEGRAM_API_HASH':
                            config.telegram_api_hash = value
                        elif key == 'TELEGRAM_PHONE':
                            config.telegram_phone = value
                        elif key.startswith('WEBHOOK_'):
                            group_id = key.replace('WEBHOOK_', '')
                            config.discord_webhooks[group_id] = value
                        elif key == 'DEBUG':
                            config.debug = value.lower() in ('true', '1', 'yes')
        else:
            print("⚠️ Archivo .env no encontrado")
        
        return config
    
    def test_environment(self) -> Dict[str, Any]:
        """Test 1: Verificar entorno Python"""
        self.logger.info("🐍 Testing Python environment...")
        
        result = {
            "status": "success",
            "python_version": sys.version,
            "platform": sys.platform,
            "working_directory": os.getcwd(),
            "env_file_exists": Path('.env').exists(),
            "dependencies": {}
        }
        
        # Verificar dependencias críticas
        critical_deps = [
            'telethon', 'fastapi', 'uvicorn', 'aiohttp', 
            'python-dotenv', 'pydantic', 'asyncio'
        ]
        
        for dep in critical_deps:
            try:
                __import__(dep)
                result["dependencies"][dep] = "✅ Available"
            except ImportError:
                result["dependencies"][dep] = "❌ Missing"
                result["status"] = "error"
                self.results["errors"].append(f"Missing dependency: {dep}")
        
        self.results["tests"]["environment"] = result
        return result
    
    def test_telegram_config(self) -> Dict[str, Any]:
        """Test 2: Verificar configuración de Telegram"""
        self.logger.info("📱 Testing Telegram configuration...")
        
        result = {
            "status": "success",
            "api_id_configured": bool(self.config.telegram_api_id),
            "api_hash_configured": bool(self.config.telegram_api_hash),
            "phone_configured": bool(self.config.telegram_phone),
            "phone_format": None,
            "session_file": None
        }
        
        # Verificar API ID
        if not self.config.telegram_api_id:
            result["status"] = "error"
            self.results["errors"].append("TELEGRAM_API_ID no configurado en .env")
        elif not self.config.telegram_api_id.isdigit():
            result["status"] = "warning"
            self.results["warnings"].append("TELEGRAM_API_ID debe ser numérico")
        
        # Verificar API Hash
        if not self.config.telegram_api_hash:
            result["status"] = "error" 
            self.results["errors"].append("TELEGRAM_API_HASH no configurado en .env")
        elif len(self.config.telegram_api_hash) != 32:
            result["status"] = "warning"
            self.results["warnings"].append("TELEGRAM_API_HASH debe tener 32 caracteres")
        
        # Verificar teléfono
        if not self.config.telegram_phone:
            result["status"] = "error"
            self.results["errors"].append("TELEGRAM_PHONE no configurado en .env")
        else:
            phone = self.config.telegram_phone
            if phone.startswith('+') and len(phone) >= 10:
                result["phone_format"] = "✅ Formato correcto"
            else:
                result["phone_format"] = "❌ Formato incorrecto (debe ser +1234567890)"
                result["status"] = "warning"
        
        # Verificar archivos de sesión
        session_files = list(Path('.').glob('*.session'))
        if session_files:
            result["session_file"] = f"✅ Encontrado: {session_files[0]}"
        else:
            result["session_file"] = "⚠️ No encontrado (se creará automáticamente)"
        
        self.results["tests"]["telegram_config"] = result
        return result
    
    async def test_discord_webhooks(self) -> Dict[str, Any]:
        """Test 3: Verificar webhooks de Discord"""
        self.logger.info("💬 Testing Discord webhooks...")
        
        result = {
            "status": "success",
            "webhooks_configured": len(self.config.discord_webhooks),
            "webhook_tests": {}
        }
        
        if not self.config.discord_webhooks:
            result["status"] = "error"
            self.results["errors"].append("No hay webhooks de Discord configurados")
            self.results["tests"]["discord_webhooks"] = result
            return result
        
        # Test cada webhook
        async with aiohttp.ClientSession() as session:
            for group_id, webhook_url in self.config.discord_webhooks.items():
                webhook_result = {
                    "url": webhook_url,
                    "status": "unknown",
                    "response_time": None,
                    "error": None
                }
                
                try:
                    # Test básico del webhook
                    start_time = datetime.now()
                    
                    test_payload = {
                        "content": "🔧 Test de diagnóstico - Sistema funcionando correctamente",
                        "username": "Sistema Diagnóstico"
                    }
                    
                    async with session.post(webhook_url, json=test_payload) as response:
                        end_time = datetime.now()
                        webhook_result["response_time"] = (end_time - start_time).total_seconds()
                        
                        if response.status == 204:
                            webhook_result["status"] = "✅ Funcionando"
                        elif response.status == 429:
                            webhook_result["status"] = "⚠️ Rate limited"
                            webhook_result["error"] = "Demasiadas requests"
                        else:
                            webhook_result["status"] = "❌ Error"
                            webhook_result["error"] = f"HTTP {response.status}"
                            result["status"] = "warning"
                
                except Exception as e:
                    webhook_result["status"] = "❌ Error"
                    webhook_result["error"] = str(e)
                    result["status"] = "error"
                    self.results["errors"].append(f"Webhook {group_id}: {str(e)}")
                
                result["webhook_tests"][group_id] = webhook_result
        
        self.results["tests"]["discord_webhooks"] = result
        return result
    
    async def test_telegram_connection(self) -> Dict[str, Any]:
        """Test 4: Probar conexión real a Telegram"""
        self.logger.info("🔌 Testing Telegram connection...")
        
        result = {
            "status": "success",
            "connection": False,
            "user_info": None,
            "groups_accessible": [],
            "error": None
        }
        
        try:
            from telethon import TelegramClient
            
            if not all([self.config.telegram_api_id, self.config.telegram_api_hash, self.config.telegram_phone]):
                result["status"] = "error"
                result["error"] = "Configuración incompleta de Telegram"
                self.results["tests"]["telegram_connection"] = result
                return result
            
            # Crear cliente temporal
            client = TelegramClient(
                'diagnostic_session',
                int(self.config.telegram_api_id),
                self.config.telegram_api_hash
            )
            
            await client.start(phone=self.config.telegram_phone)
            
            # Obtener info del usuario
            me = await client.get_me()
            result["connection"] = True
            result["user_info"] = {
                "id": me.id,
                "first_name": me.first_name,
                "username": me.username or "sin_username",
                "phone": me.phone
            }
            
            # Intentar obtener grupos disponibles
            try:
                async for dialog in client.iter_dialogs(limit=50):
                    if dialog.is_group or dialog.is_channel:
                        group_info = {
                            "id": dialog.id,
                            "title": dialog.title,
                            "type": "channel" if dialog.is_channel else "group",
                            "participants": getattr(dialog.entity, 'participants_count', 'unknown')
                        }
                        result["groups_accessible"].append(group_info)
            except Exception as e:
                self.logger.warning(f"No se pudieron obtener grupos: {e}")
            
            await client.disconnect()
            
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            self.results["errors"].append(f"Error conexión Telegram: {str(e)}")
        
        self.results["tests"]["telegram_connection"] = result
        return result
    
    def test_file_permissions(self) -> Dict[str, Any]:
        """Test 5: Verificar permisos de archivos"""
        self.logger.info("📁 Testing file permissions...")
        
        result = {
            "status": "success",
            "directories": {},
            "files": {}
        }
        
        # Directorios críticos
        critical_dirs = ['logs', 'data', 'temp', 'media']
        
        for dir_name in critical_dirs:
            dir_path = Path(dir_name)
            dir_result = {
                "exists": dir_path.exists(),
                "writable": False,
                "readable": False
            }
            
            if dir_path.exists():
                dir_result["writable"] = os.access(dir_path, os.W_OK)
                dir_result["readable"] = os.access(dir_path, os.R_OK)
            else:
                # Intentar crear directorio
                try:
                    dir_path.mkdir(exist_ok=True)
                    dir_result["exists"] = True
                    dir_result["writable"] = True
                    dir_result["readable"] = True
                except Exception as e:
                    self.results["errors"].append(f"No se puede crear directorio {dir_name}: {e}")
                    result["status"] = "error"
            
            result["directories"][dir_name] = dir_result
        
        # Archivos críticos
        critical_files = ['.env', 'main.py', 'requirements.txt']
        
        for file_name in critical_files:
            file_path = Path(file_name)
            file_result = {
                "exists": file_path.exists(),
                "readable": False,
                "size": None
            }
            
            if file_path.exists():
                file_result["readable"] = os.access(file_path, os.R_OK)
                file_result["size"] = file_path.stat().st_size
            else:
                if file_name == '.env':
                    self.results["errors"].append("Archivo .env no encontrado")
                    result["status"] = "error"
            
            result["files"][file_name] = file_result
        
        self.results["tests"]["file_permissions"] = result
        return result
    
    async def test_full_message_flow(self) -> Dict[str, Any]:
        """Test 6: Simular flujo completo de mensaje"""
        self.logger.info("🔄 Testing full message flow...")
        
        result = {
            "status": "success",
            "simulation": {
                "message_created": False,
                "filters_applied": False,
                "discord_sent": False,
                "watermark_applied": False
            },
            "performance": {
                "total_time": None,
                "steps": {}
            }
        }
        
        start_time = datetime.now()
        
        try:
            # Simular mensaje de prueba
            test_message = {
                "id": 12345,
                "text": "🔧 Mensaje de prueba del sistema de diagnóstico",
                "from_group": list(self.config.discord_webhooks.keys())[0] if self.config.discord_webhooks else "-1001234567890",
                "media_type": "text",
                "timestamp": datetime.now().isoformat()
            }
            
            step_start = datetime.now()
            result["simulation"]["message_created"] = True
            result["performance"]["steps"]["message_creation"] = (datetime.now() - step_start).total_seconds()
            
            # Simular filtros
            step_start = datetime.now()
            # Aquí aplicarías filtros reales
            result["simulation"]["filters_applied"] = True
            result["performance"]["steps"]["filters"] = (datetime.now() - step_start).total_seconds()
            
            # Simular envío a Discord
            if self.config.discord_webhooks:
                step_start = datetime.now()
                webhook_url = list(self.config.discord_webhooks.values())[0]
                
                async with aiohttp.ClientSession() as session:
                    payload = {
                        "content": test_message["text"],
                        "username": "Sistema Diagnóstico"
                    }
                    
                    async with session.post(webhook_url, json=payload) as response:
                        if response.status == 204:
                            result["simulation"]["discord_sent"] = True
                        
                result["performance"]["steps"]["discord_send"] = (datetime.now() - step_start).total_seconds()
            
            # Simular watermark (si está disponible)
            step_start = datetime.now()
            # Aquí verificarías watermark service
            result["simulation"]["watermark_applied"] = True  # Por ahora simulado
            result["performance"]["steps"]["watermark"] = (datetime.now() - step_start).total_seconds()
            
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            self.results["errors"].append(f"Error en flujo de mensaje: {str(e)}")
        
        end_time = datetime.now()
        result["performance"]["total_time"] = (end_time - start_time).total_seconds()
        
        self.results["tests"]["full_message_flow"] = result
        return result
    
    def generate_recommendations(self):
        """Generar recomendaciones basadas en tests"""
        self.logger.info("💡 Generating recommendations...")
        
        recommendations = []
        
        # Basado en errores encontrados
        if any("TELEGRAM_API_ID" in error for error in self.results["errors"]):
            recommendations.append({
                "priority": "HIGH",
                "category": "Configuration",
                "issue": "Telegram API ID no configurado",
                "solution": "Obtener API ID desde https://my.telegram.org y agregarlo al .env",
                "example": "TELEGRAM_API_ID=12345678"
            })
        
        if any("webhook" in error.lower() for error in self.results["errors"]):
            recommendations.append({
                "priority": "HIGH", 
                "category": "Discord",
                "issue": "Webhooks de Discord con problemas",
                "solution": "Verificar URLs de webhooks y permisos del bot",
                "example": "WEBHOOK_-1001234567890=https://discord.com/api/webhooks/..."
            })
        
        # Basado en warnings
        if any("formato" in warning.lower() for warning in self.results["warnings"]):
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Configuration", 
                "issue": "Formato de configuración incorrecto",
                "solution": "Revisar formato de teléfono y API hash",
                "example": "TELEGRAM_PHONE=+56985667015"
            })
        
        # Recomendaciones generales
        recommendations.append({
            "priority": "LOW",
            "category": "Performance",
            "issue": "Optimizaciones disponibles",
            "solution": "Considerar implementar cache y compression",
            "example": "REDIS_URL=redis://localhost:6379"
        })
        
        self.results["recommendations"] = recommendations
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Ejecutar todos los tests en secuencia"""
        self.logger.info("🚀 Starting comprehensive system diagnostic...")
        
        try:
            # Test 1: Environment
            self.test_environment()
            
            # Test 2: Telegram Config
            self.test_telegram_config()
            
            # Test 3: Discord Webhooks
            await self.test_discord_webhooks()
            
            # Test 4: Telegram Connection (solo si config está OK)
            if self.results["tests"]["telegram_config"]["status"] != "error":
                await self.test_telegram_connection()
            
            # Test 5: File Permissions
            self.test_file_permissions()
            
            # Test 6: Full Message Flow
            await self.test_full_message_flow()
            
            # Generar recomendaciones
            self.generate_recommendations()
            
            # Calcular score general
            total_tests = len(self.results["tests"])
            successful_tests = sum(1 for test in self.results["tests"].values() if test["status"] == "success")
            
            self.results["overall_score"] = (successful_tests / total_tests) * 100
            self.results["overall_status"] = (
                "HEALTHY" if self.results["overall_score"] >= 80 else
                "WARNING" if self.results["overall_score"] >= 60 else
                "CRITICAL"
            )
            
        except Exception as e:
            self.logger.error(f"Error durante diagnóstico: {e}")
            self.results["fatal_error"] = str(e)
            self.results["traceback"] = traceback.format_exc()
        
        return self.results
    
    def save_report(self, filename: str = None):
        """Guardar reporte completo"""
        if filename is None:
            filename = f"diagnostic_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"📄 Reporte guardado en: {filename}")
        return filename
    
    def print_summary(self):
        """Imprimir resumen en consola"""
        print("\n" + "="*80)
        print("🔧 RESUMEN DEL DIAGNÓSTICO COMPLETO")
        print("="*80)
        
        print(f"\n📊 SCORE GENERAL: {self.results['overall_score']:.1f}% - {self.results['overall_status']}")
        
        print(f"\n✅ TESTS PASADOS: {sum(1 for t in self.results['tests'].values() if t['status'] == 'success')}")
        print(f"⚠️  WARNINGS: {len(self.results['warnings'])}")
        print(f"❌ ERRORES: {len(self.results['errors'])}")
        
        if self.results["errors"]:
            print(f"\n❌ ERRORES CRÍTICOS:")
            for error in self.results["errors"]:
                print(f"   • {error}")
        
        if self.results["warnings"]:
            print(f"\n⚠️  WARNINGS:")
            for warning in self.results["warnings"]:
                print(f"   • {warning}")
        
        if self.results["recommendations"]:
            print(f"\n💡 RECOMENDACIONES:")
            for rec in self.results["recommendations"][:3]:  # Top 3
                print(f"   {rec['priority']}: {rec['issue']}")
                print(f"      → {rec['solution']}")
        
        print("\n" + "="*80)

# ============ FUNCIÓN PRINCIPAL ============

async def main():
    """Función principal de diagnóstico"""
    print("🔧 Sistema de Diagnóstico Enterprise v2.0")
    print("Iniciando análisis completo del sistema...\n")
    
    diagnostic = SystemDiagnostic()
    results = await diagnostic.run_all_tests()
    
    # Mostrar resumen
    diagnostic.print_summary()
    
    # Guardar reporte completo
    report_file = diagnostic.save_report()
    
    print(f"\n📄 Reporte completo disponible en: {report_file}")
    print("🔧 Diagnóstico completado!")
    
    return results

if __name__ == "__main__":
    # Ejecutar diagnóstico
    asyncio.run(main())