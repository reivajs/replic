#!/usr/bin/env python3
"""
🚀 COMPLETE SYSTEM LAUNCHER v5.0 - DISCOVERY INTEGRATION
========================================================
Script maestro para iniciar todo el sistema con Discovery Service
"""

import subprocess
import sys
import time
import os
import signal
import threading
import requests
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

class ServiceManager:
    """Gestor completo de microservicios"""
    
    def __init__(self):
        self.services = {
            "discovery": {
                "name": "Discovery Service",
                "script": "services/discovery/main.py",
                "port": 8002,
                "health_endpoint": "/health",
                "required": True,
                "startup_delay": 3,
                "process": None
            },
            "message_replicator": {
                "name": "Message Replicator",
                "script": "services/message_replicator/main.py", 
                "port": 8001,
                "health_endpoint": "/health",
                "required": True,
                "startup_delay": 2,
                "process": None
            },
            "watermark": {
                "name": "Watermark Service",
                "script": "watermark_service.py",
                "port": 8081,
                "health_endpoint": "/health",
                "required": False,
                "startup_delay": 2,
                "process": None
            },
            "orchestrator": {
                "name": "Main Orchestrator",
                "script": "main.py",
                "port": 8000,
                "health_endpoint": "/health",
                "required": True,
                "startup_delay": 4,  # Start last
                "process": None
            }
        }
        
        self.startup_order = ["discovery", "message_replicator", "watermark", "orchestrator"]
        self.running = False
        self.monitor_thread = None

    def check_system_requirements(self) -> bool:
        """Verificar requisitos del sistema"""
        print("🔍 Checking system requirements...")
        
        # Check Python version
        if sys.version_info < (3, 8):
            print("❌ Python 3.8+ required")
            return False
        
        # Check required packages
        required_packages = [
            'fastapi', 'uvicorn', 'telethon', 'httpx', 
            'aiosqlite', 'jinja2', 'python-multipart'
        ]
        
        missing = []
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing.append(package)
        
        if missing:
            print(f"❌ Missing packages: {', '.join(missing)}")
            print("💡 Install with: pip install -r requirements.txt")
            return False
        
        print("✅ System requirements OK")
        return True

    def setup_environment(self) -> bool:
        """Configurar entorno"""
        print("⚙️ Setting up environment...")
        
        # Create necessary directories
        directories = [
            "data", "sessions", "logs", "temp", "watermarks",
            "watermark_data/config", "watermark_data/assets", 
            "watermark_data/temp", "services/discovery",
            "frontend/templates", "frontend/static"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
        
        # Load environment variables
        env_files = [".env", ".env.discovery", ".env.microservices"]
        
        for env_file in env_files:
            if Path(env_file).exists():
                try:
                    with open(env_file) as f:
                        for line in f:
                            if line.strip() and not line.startswith('#') and '=' in line:
                                key, value = line.strip().split('=', 1)
                                os.environ[key] = value
                except Exception as e:
                    print(f"⚠️ Error loading {env_file}: {e}")
        
        print("✅ Environment configured")
        return True

    def check_ports(self) -> bool:
        """Verificar disponibilidad de puertos"""
        print("🔌 Checking port availability...")
        
        import socket
        
        for service_name, config in self.services.items():
            port = config["port"]
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                result = sock.connect_ex(('localhost', port))
                if result == 0:
                    print(f"❌ Port {port} ({service_name}) already in use")
                    return False
        
        print("✅ All ports available")
        return True

    def start_service(self, service_name: str) -> bool:
        """Iniciar un servicio específico"""
        config = self.services[service_name]
        script_path = Path(config["script"])
        
        if not script_path.exists():
            print(f"⚠️ {script_path} not found")
            if not config["required"]:
                print(f"   Skipping optional service: {config['name']}")
                return True
            return False
        
        print(f"🚀 Starting {config['name']}...")
        
        try:
            process = subprocess.Popen([
                sys.executable, str(script_path)
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            config["process"] = process
            
            # Wait for startup
            time.sleep(config["startup_delay"])
            
            # Check if process is still running
            if process.poll() is None:
                print(f"✅ {config['name']} started (PID: {process.pid})")
                return True
            else:
                stdout, stderr = process.communicate()
                print(f"❌ {config['name']} failed to start:")
                print(f"STDOUT: {stdout[:200]}...")
                print(f"STDERR: {stderr[:200]}...")
                return False
                
        except Exception as e:
            print(f"❌ Error starting {config['name']}: {e}")
            return False

    def check_service_health(self, service_name: str) -> bool:
        """Verificar salud de un servicio"""
        config = self.services[service_name]
        
        if not config["process"] or config["process"].poll() is not None:
            return False
        
        try:
            url = f"http://localhost:{config['port']}{config['health_endpoint']}"
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except:
            return False

    def start_all_services(self) -> bool:
        """Iniciar todos los servicios en orden"""
        print("🎭 Starting all microservices...")
        
        failed_services = []
        
        for service_name in self.startup_order:
            if not self.start_service(service_name):
                config = self.services[service_name]
                if config["required"]:
                    failed_services.append(service_name)
                    print(f"❌ Required service {service_name} failed to start")
                else:
                    print(f"⚠️ Optional service {service_name} skipped")
        
        if failed_services:
            print(f"❌ Failed to start required services: {failed_services}")
            return False
        
        return True

    def wait_for_services_ready(self) -> bool:
        """Esperar a que todos los servicios estén listos"""
        print("⏳ Waiting for services to be ready...")
        
        max_attempts = 30
        attempt = 0
        
        while attempt < max_attempts:
            all_healthy = True
            
            for service_name, config in self.services.items():
                if config["process"] and config["process"].poll() is None:
                    if not self.check_service_health(service_name):
                        all_healthy = False
                        break
            
            if all_healthy:
                print("✅ All services are ready!")
                return True
            
            attempt += 1
            print(f"   Attempt {attempt}/{max_attempts}...")
            time.sleep(2)
        
        print("❌ Timeout waiting for services to be ready")
        return False

    def test_integration(self) -> bool:
        """Probar integración entre servicios"""
        print("🧪 Testing service integration...")
        
        tests = [
            {
                "name": "Orchestrator Health",
                "url": "http://localhost:8000/health",
                "expected": 200
            },
            {
                "name": "Discovery Status", 
                "url": "http://localhost:8002/status",
                "expected": 200
            },
            {
                "name": "Discovery Integration",
                "url": "http://localhost:8000/api/discovery/status",
                "expected": 200
            },
            {
                "name": "Message Replicator Stats",
                "url": "http://localhost:8001/stats",
                "expected": 200
            }
        ]
        
        all_passed = True
        
        for test in tests:
            try:
                response = requests.get(test["url"], timeout=10)
                if response.status_code == test["expected"]:
                    print(f"   ✅ {test['name']}: OK")
                else:
                    print(f"   ❌ {test['name']}: HTTP {response.status_code}")
                    all_passed = False
            except Exception as e:
                print(f"   ❌ {test['name']}: {str(e)[:50]}...")
                all_passed = False
        
        return all_passed

    def show_system_status(self):
        """Mostrar estado del sistema"""
        print("\n" + "="*80)
        print("🎭 ENTERPRISE MICROSERVICES SYSTEM v5.0 - READY")
        print("="*80)
        print("🌐 Main URLs:")
        print("   📊 Enterprise Dashboard: http://localhost:8000/dashboard")
        print("   🔍 Discovery System:     http://localhost:8000/discovery")
        print("   🏥 System Health:        http://localhost:8000/health")
        print("   📚 API Documentation:    http://localhost:8000/docs")
        
        print("\n🔗 Individual Services:")
        for service_name, config in self.services.items():
            if config["process"] and config["process"].poll() is None:
                status = "✅" if self.check_service_health(service_name) else "⚠️"
                print(f"   {status} {config['name']:20} http://localhost:{config['port']}")
        
        print("\n🎯 Key Features Available:")
        print("   • Auto-discovery of Telegram chats")
        print("   • Visual chat configuration")
        print("   • Real-time monitoring")
        print("   • Message replication")
        print("   • Watermark processing")
        print("   • Bulk operations")
        
        print("\n💡 Quick Actions:")
        print("   • Trigger chat scan:     POST http://localhost:8002/api/discovery/scan")
        print("   • View discovered chats: GET http://localhost:8002/api/discovery/chats")
        print("   • Configure replication: POST http://localhost:8000/api/discovery/configure")
        print("="*80)

    def monitor_services(self):
        """Monitor de servicios en tiempo real"""
        while self.running:
            try:
                status_line = f"\r⏰ {datetime.now().strftime('%H:%M:%S')} | "
                
                for service_name, config in self.services.items():
                    if config["process"]:
                        if config["process"].poll() is None:
                            if self.check_service_health(service_name):
                                status_line += f"✅{service_name[:3]} "
                            else:
                                status_line += f"⚠️{service_name[:3]} "
                        else:
                            status_line += f"❌{service_name[:3]} "
                    else:
                        status_line += f"⚫{service_name[:3]} "
                
                print(status_line, end="", flush=True)
                time.sleep(5)
                
            except KeyboardInterrupt:
                break

    def stop_all_services(self):
        """Detener todos los servicios"""
        print("\n\n🛑 Stopping all services...")
        self.running = False
        
        # Stop in reverse order
        for service_name in reversed(self.startup_order):
            config = self.services[service_name]
            if config["process"] and config["process"].poll() is None:
                print(f"   Stopping {config['name']}...")
                config["process"].terminate()
                
                try:
                    config["process"].wait(timeout=5)
                    print(f"   ✅ {config['name']} stopped gracefully")
                except subprocess.TimeoutExpired:
                    print(f"   ⚠️ Force killing {config['name']}...")
                    config["process"].kill()
                    config["process"].wait()
        
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
        print("🚀 Enterprise Microservices System Launcher v5.0")
        print("=" * 60)
        
        # Pre-flight checks
        if not manager.check_system_requirements():
            sys.exit(1)
        
        if not manager.setup_environment():
            sys.exit(1)
        
        if not manager.check_ports():
            print("💡 Stop conflicting services or change ports in .env files")
            sys.exit(1)
        
        # Start services
        if not manager.start_all_services():
            print("❌ Failed to start required services")
            sys.exit(1)
        
        # Wait for readiness
        if not manager.wait_for_services_ready():
            print("❌ Services not ready in time")
            sys.exit(1)
        
        # Test integration
        if not manager.test_integration():
            print("⚠️ Some integration tests failed, but system is running")
        
        # Show status
        manager.show_system_status()
        
        # Start monitoring
        manager.running = True
        manager.monitor_thread = threading.Thread(target=manager.monitor_services, daemon=True)
        manager.monitor_thread.start()
        
        print("\n🎯 System is fully operational!")
        print("Press Ctrl+C to stop all services...")
        
        # Keep main thread alive
        while manager.running:
            time.sleep(1)
    
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        manager.stop_all_services()

if __name__ == "__main__":
    main()