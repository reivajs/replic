#!/usr/bin/env python3
"""
🔧 SYSTEM DIAGNOSTICS SCRIPT
============================
Diagnóstica y repara problemas del sistema enterprise
"""

import os
import sys
import asyncio
import aiohttp
import json
from pathlib import Path
from datetime import datetime

class SystemDiagnostics:
    """Diagnostico completo del sistema"""
    
    def __init__(self):
        self.services = {
            "orchestrator": {"port": 8000, "name": "Main Orchestrator"},
            "replicator": {"port": 8001, "name": "Message Replicator"},
            "discovery": {"port": 8002, "name": "Discovery Service"}
        }
        self.results = {}
    
    def print_header(self):
        print("\n" + "="*70)
        print("🔧 ENTERPRISE SYSTEM DIAGNOSTICS")
        print("="*70)
        print(f"🕐 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("🎯 Checking system health and configuration...")
        print("="*70)
    
    def check_env_config(self):
        """Verificar configuración .env"""
        print("\n📋 CHECKING .ENV CONFIGURATION")
        print("-" * 50)
        
        env_file = Path(".env")
        if not env_file.exists():
            print("❌ .env file not found!")
            return False
        
        required_vars = [
            "TELEGRAM_API_ID",
            "TELEGRAM_API_HASH", 
            "TELEGRAM_PHONE"
        ]
        
        missing_vars = []
        env_content = env_file.read_text()
        
        for var in required_vars:
            if f"{var}=" not in env_content:
                missing_vars.append(var)
        
        if missing_vars:
            print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
            return False
        
        # Check if values are set (not empty)
        for line in env_content.split('\n'):
            if '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                if key in required_vars:
                    if not value.strip():
                        print(f"❌ {key} is empty")
                        return False
                    else:
                        # Mask sensitive data
                        if 'HASH' in key:
                            display_value = value[:8] + "..." if len(value) > 8 else "***"
                        elif 'PHONE' in key:
                            display_value = value[:3] + "***" + value[-3:] if len(value) > 6 else "***"
                        else:
                            display_value = value
                        print(f"✅ {key}: {display_value}")
        
        print("✅ .env configuration looks good")
        return True
    
    def check_file_structure(self):
        """Verificar estructura de archivos"""
        print("\n📁 CHECKING FILE STRUCTURE")
        print("-" * 50)
        
        required_files = [
            "main.py",
            "services/discovery/main.py",
            "services/message_replicator/main.py",
            "frontend/templates/groups_hub.html"
        ]
        
        missing_files = []
        for file_path in required_files:
            if not Path(file_path).exists():
                missing_files.append(file_path)
            else:
                print(f"✅ {file_path}")
        
        if missing_files:
            print(f"❌ Missing files: {', '.join(missing_files)}")
            return False
        
        # Create data directories
        for directory in ["data", "logs"]:
            Path(directory).mkdir(exist_ok=True)
            print(f"✅ {directory}/ directory ready")
        
        return True
    
    async def check_service_health(self, session, service_name, config):
        """Verificar salud de un servicio específico"""
        port = config["port"]
        name = config["name"]
        
        try:
            async with session.get(f"http://localhost:{port}/health", timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ {name} (:{port}) - HEALTHY")
                    self.results[service_name] = {"status": "healthy", "data": data}
                    return True
                else:
                    print(f"❌ {name} (:{port}) - HTTP {response.status}")
                    self.results[service_name] = {"status": "unhealthy", "error": f"HTTP {response.status}"}
                    return False
        except asyncio.TimeoutError:
            print(f"❌ {name} (:{port}) - TIMEOUT")
            self.results[service_name] = {"status": "timeout", "error": "Connection timeout"}
            return False
        except Exception as e:
            print(f"❌ {name} (:{port}) - ERROR: {str(e)}")
            self.results[service_name] = {"status": "error", "error": str(e)}
            return False
    
    async def check_all_services(self):
        """Verificar todos los servicios"""
        print("\n🏥 CHECKING SERVICE HEALTH")
        print("-" * 50)
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for service_name, config in self.services.items():
                task = self.check_service_health(session, service_name, config)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            healthy_count = sum(1 for result in results if result is True)
            
            print(f"\n📊 Service Health Summary: {healthy_count}/{len(self.services)} healthy")
            return healthy_count, len(self.services)
    
    async def test_discovery_service(self):
        """Test específico del Discovery Service"""
        print("\n🔍 TESTING DISCOVERY SERVICE")
        print("-" * 50)
        
        if "discovery" not in self.results or self.results["discovery"]["status"] != "healthy":
            print("❌ Discovery Service not healthy, skipping tests")
            return False
        
        async with aiohttp.ClientSession() as session:
            try:
                # Test chats endpoint
                async with session.get("http://localhost:8002/api/discovery/chats?limit=5") as response:
                    if response.status == 200:
                        data = await response.json()
                        chat_count = len(data.get("chats", []))
                        print(f"✅ Discovery chats endpoint working - {chat_count} chats found")
                        
                        if chat_count == 0:
                            print("⚠️  No chats discovered - checking Telegram connection...")
                            
                            # Check status endpoint for more details
                            async with session.get("http://localhost:8002/status") as status_response:
                                if status_response.status == 200:
                                    status_data = await status_response.json()
                                    scanner_status = status_data.get("scanner_status", {})
                                    config_valid = scanner_status.get("config_valid", False)
                                    config_errors = scanner_status.get("config_errors", [])
                                    
                                    if not config_valid:
                                        print("❌ Telegram configuration invalid:")
                                        for error in config_errors:
                                            print(f"   - {error}")
                                        return False
                                    else:
                                        print("✅ Telegram configuration valid")
                                        
                                        # Try to trigger a scan
                                        print("🔄 Triggering discovery scan...")
                                        async with session.post("http://localhost:8002/api/discovery/scan", 
                                                               json={"force_refresh": True, "max_chats": 50}) as scan_response:
                                            if scan_response.status == 200:
                                                print("✅ Discovery scan started successfully")
                                                return True
                                            else:
                                                print(f"❌ Failed to start scan: HTTP {scan_response.status}")
                                                return False
                        else:
                            return True
                    else:
                        print(f"❌ Discovery chats endpoint failed: HTTP {response.status}")
                        return False
            except Exception as e:
                print(f"❌ Discovery Service test failed: {e}")
                return False
    
    async def test_replicator_service(self):
        """Test específico del Message Replicator"""
        print("\n📡 TESTING MESSAGE REPLICATOR")
        print("-" * 50)
        
        if "replicator" not in self.results or self.results["replicator"]["status"] != "healthy":
            print("❌ Message Replicator not healthy, skipping tests")
            return False
        
        async with aiohttp.ClientSession() as session:
            try:
                # Test groups endpoint
                async with session.get("http://localhost:8001/api/config/groups") as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("success"):
                            group_count = len(data.get("groups", {}))
                            print(f"✅ Replicator groups endpoint working - {group_count} groups configured")
                            return True
                        else:
                            print("❌ Replicator returned unsuccessful response")
                            return False
                    else:
                        print(f"❌ Replicator groups endpoint failed: HTTP {response.status}")
                        return False
            except Exception as e:
                print(f"❌ Message Replicator test failed: {e}")
                return False
    
    def check_groups_hub_file(self):
        """Verificar archivo Groups Hub por duplicados"""
        print("\n🎭 CHECKING GROUPS HUB FILE")
        print("-" * 50)
        
        groups_hub_file = Path("frontend/templates/groups_hub.html")
        if not groups_hub_file.exists():
            print("❌ groups_hub.html file not found")
            return False
        
        content = groups_hub_file.read_text()
        
        # Check for duplicate class declarations
        class_declarations = content.count("class EnterpriseGroupsHub")
        if class_declarations > 1:
            print(f"❌ Found {class_declarations} EnterpriseGroupsHub class declarations (should be 1)")
            print("🔧 Need to remove duplicate class declaration")
            return False
        elif class_declarations == 1:
            print("✅ EnterpriseGroupsHub class declared once (correct)")
        else:
            print("❌ EnterpriseGroupsHub class not found")
            return False
        
        # Check file size
        file_size = len(content)
        print(f"✅ Groups Hub file size: {file_size:,} characters")
        
        return True
    
    def generate_fix_commands(self):
        """Generar comandos para solucionar problemas"""
        print("\n🔧 RECOMMENDED FIXES")
        print("-" * 50)
        
        issues_found = []
        
        # Check results
        if "discovery" in self.results and self.results["discovery"]["status"] != "healthy":
            issues_found.append("discovery_service")
        
        if "replicator" in self.results and self.results["replicator"]["status"] != "healthy":
            issues_found.append("replicator_service")
        
        if issues_found:
            print("To fix the issues, run these commands:")
            print()
            print("1. 🛑 Stop all services:")
            print("   Ctrl+C (if running)")
            print()
            print("2. 🔧 Start individual services for testing:")
            
            if "discovery_service" in issues_found:
                print("   python services/discovery/main.py")
                print("   (Test in browser: http://localhost:8002/dashboard)")
            
            if "replicator_service" in issues_found:
                print("   python services/message_replicator/main.py")
                print("   (Test in browser: http://localhost:8001/dashboard)")
            
            print()
            print("3. 🚀 Start complete system:")
            print("   python start_complete_system.py")
            print()
            print("4. 🌐 Access Groups Hub:")
            print("   http://localhost:8000/groups")
        else:
            print("✅ No critical issues found!")
            print("🌐 Access your Groups Hub at: http://localhost:8000/groups")
    
    async def run_full_diagnostics(self):
        """Ejecutar diagnósticos completos"""
        self.print_header()
        
        # Step 1: Check environment
        env_ok = self.check_env_config()
        
        # Step 2: Check file structure
        files_ok = self.check_file_structure()
        
        # Step 3: Check Groups Hub file
        groups_hub_ok = self.check_groups_hub_file()
        
        # Step 4: Check services
        healthy_count, total_count = await self.check_all_services()
        
        # Step 5: Test specific services
        if healthy_count > 0:
            await self.test_discovery_service()
            await self.test_replicator_service()
        
        # Step 6: Generate fixes
        self.generate_fix_commands()
        
        # Final summary
        print("\n" + "="*70)
        print("📊 DIAGNOSTIC SUMMARY")
        print("="*70)
        print(f"📋 Environment Config: {'✅ OK' if env_ok else '❌ ISSUES'}")
        print(f"📁 File Structure: {'✅ OK' if files_ok else '❌ ISSUES'}")
        print(f"🎭 Groups Hub File: {'✅ OK' if groups_hub_ok else '❌ ISSUES'}")
        print(f"🏥 Services Health: {healthy_count}/{total_count} healthy")
        
        if env_ok and files_ok and groups_hub_ok and healthy_count == total_count:
            print("\n🎉 SYSTEM STATUS: ALL GOOD!")
            print("🌐 Ready to use: http://localhost:8000/groups")
        else:
            print("\n⚠️ SYSTEM STATUS: NEEDS ATTENTION")
            print("🔧 Follow the recommended fixes above")
        
        print("="*70)

async def main():
    """Función principal"""
    diagnostics = SystemDiagnostics()
    await diagnostics.run_full_diagnostics()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n🛑 Diagnostics interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Diagnostics failed: {e}")
