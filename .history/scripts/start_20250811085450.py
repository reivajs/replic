#!/usr/bin/env python3
"""
🚀 FIXED STARTUP SCRIPT v1.0
============================
Script corregido con mejor detección de dependencias
"""

import subprocess
import sys
import time
import os
import signal
import threading
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

class ServiceManager:
    """Gestor de microservicios simplificado"""
    
    def __init__(self):
        self.services = {
            "discovery": {
                "name": "Discovery Service",
                "script": "services/discovery/main.py",
                "port": 8002,
                "required": False,  # Opcional por ahora
                "process": None
            },
            "message_replicator": {
                "name": "Message Replicator",
                "script": "services/message_replicator/main.py", 
                "port": 8001,
                "required": False,  # Opcional por ahora
                "process": None
            },
            "orchestrator": {
                "name": "Main Orchestrator",
                "script": "main.py",
                "port": 8000,
                "required": True,
                "process": None
            }
        }
        
        self.running = False

    def check_system_requirements(self) -> bool:
        """Verificar requisitos del sistema - VERSION MEJORADA"""
        print("🔍 Checking system requirements...")
        
        # Check Python version
        if sys.version_info < (3, 8):
            print("❌ Python 3.8+ required")
            return False
        print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
        
        # Check required packages con mejor detección
        required_checks = [
            ("fastapi", "FastAPI"),
            ("uvicorn", "Uvicorn"),
            ("telethon", "Telethon"),
            ("jinja2", "Jinja2"),
            ("pydantic", "Pydantic")
        ]
        
        missing = []
        for module_name, display_name in required_checks:
            try:
                __import__(module_name)
                print(f"✅ {display_name}")
            except ImportError:
                missing.append(display_name)
                print(f"❌ {display_name}")
        
        # Check optional packages
        optional_checks = [
            ("httpx", "HTTPX"),
            ("aiosqlite", "AsyncSQLite"),
            ("requests", "Requests")
        ]
        
        for module_name, display_name in optional_checks:
            try:
                __import__(module_name)
                print(f"✅ {display_name} (optional)")
            except ImportError:
                print(f"⚠️ {display_name} (optional) - will install if needed")
        
        if missing:
            print(f"\n❌ Critical packages missing: {', '.join(missing)}")
            print("💡 Install with: pip install fastapi uvicorn telethon jinja2 pydantic")
            return False
        
        print("✅ All critical requirements OK")
        return True

    def setup_environment(self) -> bool:
        """Configurar entorno"""
        print("⚙️ Setting up environment...")
        
        # Create necessary directories
        directories = [
            "data", "sessions", "logs", "temp",
            "frontend/templates", "frontend/static",
            "services/discovery"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
        
        # Check .env file
        if not Path(".env").exists():
            if Path(".env.discovery").exists():
                print("📋 Copying .env.discovery to .env...")
                import shutil
                shutil.copy(".env.discovery", ".env")
            elif Path(".env.microservices").exists():
                print("📋 Copying .env.microservices to .env...")
                import shutil
                shutil.copy(".env.microservices", ".env")
            else:
                print("⚠️ No .env file found - creating basic one...")
                with open(".env", "w") as f:
                    f.write("# Basic configuration\n")
                    f.write("TELEGRAM_API_ID=your_api_id\n")
                    f.write("TELEGRAM_API_HASH=your_api_hash\n")
                    f.write("TELEGRAM_PHONE=your_phone\n")
        
        print("✅ Environment configured")
        return True

    def check_main_file(self) -> bool:
        """Verificar que main.py existe"""
        if not Path("main.py").exists():
            print("❌ main.py not found")
            print("💡 Make sure you're in the project root directory")
            return False
        
        print("✅ main.py found")
        return True

    def start_service(self, service_name: str) -> bool:
        """Iniciar un servicio específico"""
        config = self.services[service_name]
        script_path = Path(config["script"])
        
        if not script_path.exists():
            if config["required"]:
                print(f"❌ Required service script not found: {script_path}")
                return False
            else:
                print(f"⚠️ Optional service script not found: {script_path} - skipping")
                return True
        
        print(f"🚀 Starting {config['name']}...")
        
        try:
            process = subprocess.Popen([
                sys.executable, str(script_path)
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            config["process"] = process
            
            # Quick check if process started
            time.sleep(1)
            
            if process.poll() is None:
                print(f"✅ {config['name']} started (PID: {process.pid})")
                return True
            else:
                stdout, stderr = process.communicate()
                print(f"❌ {config['name']} failed to start")
                if stderr:
                    print(f"Error: {stderr[:200]}...")
                return config["required"] == False  # If optional, don't fail
                
        except Exception as e:
            print(f"❌ Error starting {config['name']}: {e}")
            return config["required"] == False

    def start_main_orchestrator(self) -> bool:
        """Start main orchestrator only"""
        print("🎭 Starting Main Orchestrator...")
        
        try:
            process = subprocess.Popen([
                sys.executable, "main.py"
            ])
            
            self.services["orchestrator"]["process"] = process
            
            # Wait a moment and check
            time.sleep(2)
            
            if process.poll() is None:
                print("✅ Main Orchestrator started successfully")
                return True
            else:
                print("❌ Main Orchestrator failed to start")
                return False
                
        except Exception as e:
            print(f"❌ Error starting Main Orchestrator: {e}")
            return False

    def show_system_status(self):
        """Mostrar estado del sistema"""
        print("\n" + "="*70)
        print("🎭 ENTERPRISE MICROSERVICES SYSTEM - READY")
        print("="*70)
        print("🌐 Available URLs:")
        print("   📊 Dashboard:    http://localhost:8000/dashboard")
        print("   🏥 Health:       http://localhost:8000/health")
        print("   📚 API Docs:     http://localhost:8000/docs")
        
        # Check what services are running
        running_services = []
        for name, config in self.services.items():
            if config["process"] and config["process"].poll() is None:
                running_services.append(config["name"])
        
        if running_services:
            print(f"\n🔗 Running Services: {', '.join(running_services)}")
        
        print("\n💡 Next Steps:")
        print("   1. Open http://localhost:8000/dashboard in your browser")
        print("   2. Configure your Telegram credentials in .env if needed")
        print("   3. Start using the Discovery System!")
        print("="*70)

    def stop_all_services(self):
        """Detener todos los servicios"""
        print("\n🛑 Stopping all services...")
        self.running = False
        
        for service_name, config in self.services.items():
            if config["process"] and config["process"].poll() is None:
                print(f"   Stopping {config['name']}...")
                config["process"].terminate()
                
                try:
                    config["process"].wait(timeout=5)
                    print(f"   ✅ {config['name']} stopped")
                except subprocess.TimeoutExpired:
                    print(f"   ⚠️ Force killing {config['name']}...")
                    config["process"].kill()
        
        print("👋 All services stopped")

def main():
    """Función principal"""
    manager = ServiceManager()
    
    # Setup signal handlers
    def signal_handler(signum, frame):
        manager.stop_all_services()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        print("🚀 Enterprise Microservices Launcher - FIXED VERSION")
        print("=" * 60)
        
        # Pre-flight checks
        if not manager.check_system_requirements():
            print("\n💡 To install missing packages:")
            print("   pip install fastapi uvicorn telethon jinja2 pydantic")
            sys.exit(1)
        
        if not manager.setup_environment():
            sys.exit(1)
        
        if not manager.check_main_file():
            sys.exit(1)
        
        # Start main orchestrator (minimum viable system)
        if not manager.start_main_orchestrator():
            print("❌ Failed to start main system")
            sys.exit(1)
        
        # Show status
        manager.show_system_status()
        
        # Keep running
        manager.running = True
        print("\n🎯 System is running! Press Ctrl+C to stop...")
        
        try:
            # Wait for the main process
            manager.services["orchestrator"]["process"].wait()
        except KeyboardInterrupt:
            pass
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        manager.stop_all_services()

if __name__ == "__main__":
    main()