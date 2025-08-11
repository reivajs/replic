#!/usr/bin/env python3
"""
🚀 DISCOVERY SERVICE LAUNCHER v2.0
==================================
Script de inicialización completo para Discovery Service
"""

import subprocess
import sys
import time
import os
import signal
import threading
from pathlib import Path
from typing import List, Dict, Optional

def check_dependencies():
    """Verificar dependencias necesarias"""
    required_packages = [
        'fastapi',
        'uvicorn',
        'telethon',
        'httpx',
        'aiosqlite'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ Dependencias faltantes: {', '.join(missing)}")
        print("💡 Instala con: pip install -r requirements.txt")
        return False
    
    return True

def setup_directories():
    """Crear directorios necesarios"""
    directories = [
        "data",
        "sessions", 
        "logs",
        "services/discovery",
        "frontend/templates",
        "frontend/static"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Directorios configurados")

def setup_environment():
    """Configurar variables de entorno"""
    env_file = Path(".env.discovery")
    
    if not env_file.exists():
        print("⚠️ Archivo .env.discovery no encontrado")
        return False
    
    # Load environment variables
    try:
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
        
        print("✅ Variables de entorno cargadas")
        return True
    except Exception as e:
        print(f"❌ Error cargando .env: {e}")
        return False

def check_telegram_session():
    """Verificar sesión de Telegram"""
    session_path = Path("sessions/discovery_session.session")
    
    if not session_path.exists():
        print("⚠️ Sesión de Telegram no encontrada")
        print("💡 El servicio creará una nueva sesión automáticamente")
        return True
    
    print("✅ Sesión de Telegram encontrada")
    return True

def check_ports():
    """Verificar puertos disponibles"""
    import socket
    
    ports_to_check = [8002]  # Discovery Service port
    
    for port in ports_to_check:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            result = sock.connect_ex(('localhost', port))
            if result == 0:
                print(f"❌ Puerto {port} ya está en uso")
                return False
    
    print("✅ Puertos disponibles")
    return True

def start_discovery_service():
    """Iniciar Discovery Service"""
    try:
        print("🚀 Iniciando Discovery Service...")
        
        # Ensure we're in the right directory
        discovery_main = Path("services/discovery/main.py")
        
        if not discovery_main.exists():
            print(f"❌ {discovery_main} no encontrado")
            return None
        
        # Start the service
        process = subprocess.Popen([
            sys.executable, str(discovery_main)
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Wait a moment to check if it started successfully
        time.sleep(3)
        
        if process.poll() is None:
            print("✅ Discovery Service iniciado correctamente")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Error al iniciar Discovery Service:")
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Error iniciando Discovery Service: {e}")
        return None

def monitor_service(process):
    """Monitor service health"""
    import requests
    import time
    
    def check_health():
        while True:
            try:
                if process.poll() is not None:
                    print("❌ Discovery Service se detuvo inesperadamente")
                    break
                
                # Check health endpoint
                response = requests.get("http://localhost:8002/health", timeout=5)
                if response.status_code == 200:
                    status = "✅ Healthy"
                else:
                    status = f"⚠️ HTTP {response.status_code}"
                
                print(f"\r{status} | PID: {process.pid} | Uptime: {int(time.time() - start_time)}s", end="", flush=True)
                
            except requests.RequestException:
                print(f"\r❌ Service unreachable | PID: {process.pid}", end="", flush=True)
            except KeyboardInterrupt:
                break
            
            time.sleep(10)
    
    start_time = time.time()
    health_thread = threading.Thread(target=check_health, daemon=True)
    health_thread.start()
    
    return health_thread

def test_discovery_endpoints():
    """Test key Discovery Service endpoints"""
    import requests
    import time
    
    print("\n🧪 Testing Discovery Service endpoints...")
    
    # Wait for service to be fully ready
    time.sleep(2)
    
    endpoints = [
        ("Health Check", "GET", "/health"),
        ("Status", "GET", "/status"),
        ("Chat List", "GET", "/api/discovery/chats?limit=5"),
    ]
    
    base_url = "http://localhost:8002"
    
    for name, method, endpoint in endpoints:
        try:
            response = requests.request(method, f"{base_url}{endpoint}", timeout=10)
            if response.status_code == 200:
                print(f"   ✅ {name}: OK")
            else:
                print(f"   ⚠️ {name}: HTTP {response.status_code}")
        except Exception as e:
            print(f"   ❌ {name}: {e}")

def setup_integration_with_orchestrator():
    """Setup integration with main orchestrator"""
    import requests
    import time
    
    print("\n🔗 Setting up integration with Orchestrator...")
    
    # Wait a bit for both services to be ready
    time.sleep(3)
    
    try:
        # Check if orchestrator is running
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Orchestrator is running")
            
            # Test discovery integration
            response = requests.get("http://localhost:8000/api/discovery/status", timeout=10)
            if response.status_code == 200:
                print("   ✅ Discovery integration working")
            else:
                print(f"   ⚠️ Discovery integration: HTTP {response.status_code}")
        else:
            print("   ⚠️ Orchestrator not responding properly")
            
    except requests.RequestException as e:
        print(f"   ❌ Cannot connect to Orchestrator: {e}")
        print("   💡 Start the orchestrator with: python main.py")

def show_service_info():
    """Show service information and URLs"""
    print("\n" + "="*70)
    print("🔍 DISCOVERY SERVICE v2.0 - READY")
    print("="*70)
    print("🌐 Service URLs:")
    print("   📊 Status:           http://localhost:8002/status")
    print("   🔍 Scan Chats:       http://localhost:8002/api/discovery/scan")
    print("   📋 List Chats:       http://localhost:8002/api/discovery/chats")
    print("   🏥 Health Check:     http://localhost:8002/health")
    print("   📚 API Docs:         http://localhost:8002/docs")
    print("\n🎯 Integration URLs:")
    print("   🎭 Main Dashboard:   http://localhost:8000/dashboard")
    print("   🔍 Discovery UI:     http://localhost:8000/discovery")
    print("\n💡 Quick Actions:")
    print("   • Trigger scan:      POST /api/discovery/scan")
    print("   • Get chats:         GET /api/discovery/chats")
    print("   • Configure chat:    POST /api/discovery/configure")
    print("="*70)

def handle_shutdown(signum, frame, processes):
    """Handle graceful shutdown"""
    print("\n\n🛑 Shutting down Discovery Service...")
    
    for process in processes:
        if process and process.poll() is None:
            print(f"   Terminating PID {process.pid}...")
            process.terminate()
            
            try:
                process.wait(timeout=5)
                print(f"   ✅ Process {process.pid} terminated gracefully")
            except subprocess.TimeoutExpired:
                print(f"   ⚠️ Force killing process {process.pid}...")
                process.kill()
                process.wait()
    
    print("👋 Discovery Service stopped")
    sys.exit(0)

def main():
    """Main launcher function"""
    print("🚀 Discovery Service Launcher v2.0")
    print("=" * 50)
    
    # Pre-flight checks
    print("🔍 Running pre-flight checks...")
    
    if not check_dependencies():
        sys.exit(1)
    
    setup_directories()
    
    if not setup_environment():
        sys.exit(1)
    
    if not check_telegram_session():
        sys.exit(1)
    
    if not check_ports():
        print("💡 Try stopping other services or change port in .env.discovery")
        sys.exit(1)
    
    print("✅ All pre-flight checks passed")
    
    # Start services
    processes = []
    
    try:
        # Start Discovery Service
        discovery_process = start_discovery_service()
        if not discovery_process:
            print("❌ Failed to start Discovery Service")
            sys.exit(1)
        
        processes.append(discovery_process)
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, lambda s, f: handle_shutdown(s, f, processes))
        signal.signal(signal.SIGTERM, lambda s, f: handle_shutdown(s, f, processes))
        
        # Test endpoints
        test_discovery_endpoints()
        
        # Setup integration
        setup_integration_with_orchestrator()
        
        # Show service info
        show_service_info()
        
        # Start monitoring
        monitor_thread = monitor_service(discovery_process)
        
        print("\n🎯 Discovery Service is running!")
        print("Press Ctrl+C to stop...")
        
        # Wait for processes
        try:
            discovery_process.wait()
        except KeyboardInterrupt:
            pass
            
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        handle_shutdown(None, None, processes)

if __name__ == "__main__":
    main()