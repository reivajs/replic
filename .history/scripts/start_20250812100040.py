#!/usr/bin/env python3
"""
🚀 ENTERPRISE MICROSERVICES LAUNCHER - FIXED VERSION
====================================================
Solución definitiva al error "address already in use"
"""

import subprocess
import sys
import time
import socket
import psutil
from pathlib import Path

class EnterpriseSystemLauncher:
    """Launcher inteligente que maneja conflictos de puertos"""
    
    def __init__(self):
        self.ports_needed = [8000, 8001, 8002, 8081]
        self.processes = []
        
    def check_requirements(self) -> bool:
        """Verificar dependencias del sistema"""
        print("🔍 Checking system requirements...")
        
        # Verificar Python
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        print(f"✅ Python {python_version}")
        
        # Verificar dependencias críticas
        required_modules = [
            "fastapi", "uvicorn", "telethon", "jinja2", "pydantic"
        ]
        
        for module in required_modules:
            try:
                __import__(module)
                print(f"✅ {module.title()}")
            except ImportError:
                print(f"❌ {module.title()} not found")
                return False
        
        # Verificar dependencias opcionales
        optional_modules = ["httpx", "aiosqlite", "requests"]
        for module in optional_modules:
            try:
                __import__(module)
                print(f"✅ {module.title()} (optional)")
            except ImportError:
                print(f"⚠️ {module.title()} (optional, recommended)")
        
        print("✅ All critical requirements OK")
        return True
    
    def kill_processes_on_ports(self):
        """Matar procesos que usan los puertos necesarios"""
        print("🔍 Checking for processes using required ports...")
        killed_any = False
        
        for port in self.ports_needed:
            if self.is_port_in_use(port):
                print(f"🔄 Port {port} is in use, attempting to free it...")
                if self.kill_process_on_port(port):
                    print(f"✅ Port {port} freed")
                    killed_any = True
                    time.sleep(1)  # Esperar a que el puerto se libere
                else:
                    print(f"⚠️ Could not free port {port}")
        
        if not killed_any:
            print("✅ All required ports are available")
        
        return True
    
    def is_port_in_use(self, port: int) -> bool:
        """Verificar si un puerto está en uso"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                result = sock.connect_ex(('localhost', port))
                return result == 0
        except Exception:
            return False
    
    def kill_process_on_port(self, port: int) -> bool:
        """Matar el proceso que usa un puerto específico"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'connections']):
                try:
                    connections = proc.info['connections']
                    if connections:
                        for conn in connections:
                            if conn.laddr.port == port:
                                print(f"  Killing process {proc.info['pid']} ({proc.info['name']})")
                                proc.terminate()
                                proc.wait(timeout=3)
                                return True
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            return False
        except Exception as e:
            print(f"  Error killing process on port {port}: {e}")
            return False
    
    def setup_environment(self) -> bool:
        """Configurar el entorno necesario"""
        print("⚙️ Setting up environment...")
        
        # Crear directorios necesarios
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

    def start_service(self, service_name: str, script_path: str, port: int, wait_time: int = 3):
        """Iniciar un servicio específico"""
        print(f"🚀 Starting {service_name} on port {port}...")
        
        if not Path(script_path).exists():
            print(f"⚠️ {script_path} not found - skipping")
            return None
        
        try:
            process = subprocess.Popen([
                sys.executable, script_path
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Esperar un poco para que el servicio inicie
            time.sleep(wait_time)
            
            # Verificar si el proceso sigue corriendo
            if process.poll() is None:
                print(f"✅ {service_name} started successfully")
                self.processes.append((service_name, process, port))
                return process
            else:
                stdout, stderr = process.communicate()
                print(f"❌ {service_name} failed to start")
                if stderr:
                    print(f"   Error: {stderr[:200]}...")
                return None
                
        except Exception as e:
            print(f"❌ Error starting {service_name}: {e}")
            return None

    def start_main_orchestrator(self):
        """Iniciar el Main Orchestrator"""
        print("🎭 Starting Main Orchestrator...")
        return self.start_service("Main Orchestrator", "main.py", 8000, 5)

    def check_service_health(self, port: int, max_retries: int = 5) -> bool:
        """Verificar si un servicio está funcionando"""
        for i in range(max_retries):
            try:
                import requests
                response = requests.get(f"http://localhost:{port}/health", timeout=3)
                if response.status_code == 200:
                    return True
            except Exception:
                if i < max_retries - 1:
                    time.sleep(2)
                    continue
        return False

    def start_system(self):
        """Iniciar el sistema completo"""
        try:
            print("🎭 Enterprise Microservices Launcher - FIXED VERSION")
            print("=" * 60)
            
            # 1. Verificar dependencias
            if not self.check_requirements():
                print("❌ Missing critical dependencies")
                return False
            
            # 2. Liberar puertos ocupados
            self.kill_processes_on_ports()
            
            # 3. Configurar entorno
            if not self.setup_environment():
                print("❌ Environment setup failed")
                return False
            
            # 4. Verificar archivos principales
            if not self.check_main_file():
                print("❌ Critical files missing")
                return False
            
            # 5. Iniciar servicios opcionales primero
            optional_services = [
                ("Message Replicator", "services/message_replicator/main.py", 8001),
                ("Discovery Service", "services/discovery/main.py", 8002),
                ("Watermark Service", "watermark_service.py", 8081)
            ]
            
            services_started = 0
            for name, script, port in optional_services:
                if self.start_service(name, script, port):
                    services_started += 1
            
            # 6. Iniciar Main Orchestrator
            main_process = self.start_main_orchestrator()
            if not main_process:
                print("❌ Main Orchestrator failed to start")
                return False
            
            # 7. Verificar salud del sistema
            print("⏳ Checking system health...")
            time.sleep(3)
            
            main_healthy = self.check_service_health(8000)
            if main_healthy:
                print("✅ Main Orchestrator is healthy")
            else:
                print("⚠️ Main Orchestrator may not be responding correctly")
            
            # 8. Mostrar resumen
            print("\n" + "=" * 70)
            print("🎭 ENTERPRISE MICROSERVICES ORCHESTRATOR v5.0")
            print("=" * 70)
            print("🌐 Main endpoints:")
            print("   📊 Dashboard:         http://localhost:8000/dashboard")
            print("   🔍 Discovery UI:      http://localhost:8000/discovery")
            print("   🎭 Groups Hub:        http://localhost:8000/groups")
            print("   🏥 Health Check:      http://localhost:8000/health")
            print("   📚 API Docs:          http://localhost:8000/docs")
            
            print("🔗 Microservices:")
            replicator_healthy = self.check_service_health(8001)
            discovery_healthy = self.check_service_health(8002)
            watermark_healthy = self.check_service_health(8081)
            
            print(f"   {'✅' if replicator_healthy else '❌'} Message Replicator   http://localhost:8001")
            print(f"   {'✅' if discovery_healthy else '❌'} Discovery Service    http://localhost:8002")
            print(f"   {'✅' if watermark_healthy else '❌'} Watermark Service    http://localhost:8081")
            
            print("🎯 NEW: Auto-Discovery System integrated!")
            print("=" * 70)
            
            # Mantener el sistema corriendo
            print("\nPress Ctrl+C to stop all services...")
            
            while True:
                time.sleep(1)
                # Verificar que main.py sigue corriendo
                if main_process.poll() is not None:
                    print("⚠️ Main Orchestrator stopped unexpectedly")
                    break
            
        except KeyboardInterrupt:
            print("\n🛑 Stopping all services...")
            self.stop_all_services()
            
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            self.stop_all_services()
            return False
            
        return True

    def stop_all_services(self):
        """Detener todos los servicios"""
        print("🛑 Stopping all services...")
        
        for name, process, port in self.processes:
            try:
                print(f"   Stopping {name}...")
                process.terminate()
                process.wait(timeout=5)
                print(f"   ✅ {name} stopped")
            except subprocess.TimeoutExpired:
                print(f"   🔥 Force killing {name}...")
                process.kill()
            except Exception as e:
                print(f"   ⚠️ Error stopping {name}: {e}")
        
        print("👋 All services stopped")

def main():
    """Función principal"""
    launcher = EnterpriseSystemLauncher()
    success = launcher.start_system()
    
    if success:
        print("✅ System started successfully")
    else:
        print("❌ Failed to start main system")

if __name__ == "__main__":
    main()