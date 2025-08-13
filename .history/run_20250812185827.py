#!/usr/bin/env python3
"""
🚀 FIXED STARTUP SCRIPT
======================
Script corregido que maneja archivos correctamente
"""

import subprocess
import sys
import time
import os
import requests
from pathlib import Path
import shutil

def check_service_health(port, service_name):
    """Check if a service is running"""
    try:
        response = requests.get(f"http://localhost:{port}/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ {service_name} (port {port}) - Healthy")
            return True
        else:
            print(f"❌ {service_name} (port {port}) - Unhealthy (HTTP {response.status_code})")
            return False
    except requests.exceptions.RequestException:
        print(f"❌ {service_name} (port {port}) - Not responding")
        return False

def create_directories():
    """Crear directorios necesarios"""
    dirs = [
        "services/discovery",
        "services/message_replicator", 
        "services/tenant",
        "data",
        "sessions",
        "frontend/templates",
        "logs"
    ]
    
    for directory in dirs:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("📁 Directorios creados")

def setup_message_replicator():
    """Configurar Message Replicator desde el artifact"""
    target_file = Path("services/message_replicator/main.py")
    
    if target_file.exists():
        print("✅ Message Replicator ya existe")
        return True
    
    print("📝 Copiando Message Replicator desde paste.txt...")
    
    # Si existe paste.txt, lo copiamos
    paste_file = Path("paste.txt")
    if paste_file.exists():
        try:
            shutil.copy(paste_file, target_file)
            print(f"✅ Copiado {paste_file} → {target_file}")
            return True
        except Exception as e:
            print(f"❌ Error copiando: {e}")
    
    print("⚠️ paste.txt no encontrado")
    print("💡 Copia el código del Message Replicator artifact a services/message_replicator/main.py")
    return False

def setup_main_orchestrator():
    """Configurar Main Orchestrator"""
    target_file = Path("main.py")
    
    if target_file.exists():
        print("✅ main.py ya existe")
        return True
    
    print("📝 Configurando Main Orchestrator...")
    
    # Si existe paste-2.txt, lo copiamos
    paste_file = Path("paste-2.txt")
    if paste_file.exists():
        try:
            shutil.copy(paste_file, target_file)
            print(f"✅ Copiado {paste_file} → {target_file}")
            return True
        except Exception as e:
            print(f"❌ Error copiando: {e}")
    
    print("⚠️ paste-2.txt no encontrado")
    print("💡 Copia el código del Main Orchestrator a main.py")
    return False

def setup_discovery_service():
    """Configurar Discovery Service"""
    target_file = Path("services/discovery/main.py")
    
    if target_file.exists():
        print("✅ Discovery Service ya existe")
        return True
    
    print("💡 Copia el código del Discovery Service artifact a services/discovery/main.py")
    return False

def start_service(name, script_path, port):
    """Start a microservice"""
    if not Path(script_path).exists():
        print(f"❌ {script_path} not found")
        return None
    
    print(f"🚀 Starting {name}...")
    return subprocess.Popen([
        sys.executable, script_path
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def wait_for_service(port, service_name, max_wait=30):
    """Wait for service to be ready"""
    print(f"⏳ Waiting for {service_name} to be ready...")
    
    for i in range(max_wait):
        if check_service_health(port, service_name):
            return True
        time.sleep(1)
        if i % 5 == 0:
            print(f"   Waiting... ({i}/{max_wait}s)")
    
    print(f"❌ {service_name} failed to start within {max_wait} seconds")
    return False

def main():
    """Main startup function"""
    print("🚀 STARTING ENTERPRISE SYSTEM")
    print("="*50)
    
    # 1. Create directories
    create_directories()
    
    # 2. Setup services
    print("\n📋 SETTING UP SERVICES...")
    print("-"*30)
    
    discovery_ready = setup_discovery_service()
    replicator_ready = setup_message_replicator()
    orchestrator_ready = setup_main_orchestrator()
    
    if not any([discovery_ready, replicator_ready, orchestrator_ready]):
        print("❌ No services configured. Please copy the artifacts first.")
        print("\n📝 INSTRUCTIONS:")
        print("1. Copy Discovery Service code to: services/discovery/main.py")
        print("2. Copy Message Replicator code to: services/message_replicator/main.py") 
        print("3. Copy Main Orchestrator code to: main.py")
        print("4. Run this script again")
        return
    
    # 3. Start services
    print("\n🚀 STARTING SERVICES...")
    print("-"*30)
    
    processes = []
    
    try:
        # Start Discovery Service (puerto 8002)
        if discovery_ready:
            discovery_proc = start_service("Discovery Service", "services/discovery/main.py", 8002)
            if discovery_proc:
                processes.append(("Discovery Service", discovery_proc, 8002))
                if wait_for_service(8002, "Discovery Service", 20):
                    print("✅ Discovery Service ready")
                else:
                    print("⚠️ Discovery Service may not be ready")
        
        time.sleep(2)
        
        # Start Message Replicator (puerto 8001)
        if replicator_ready:
            replicator_proc = start_service("Message Replicator", "services/message_replicator/main.py", 8001)
            if replicator_proc:
                processes.append(("Message Replicator", replicator_proc, 8001))
                if wait_for_service(8001, "Message Replicator", 20):
                    print("✅ Message Replicator ready")
                else:
                    print("⚠️ Message Replicator may not be ready")
        
        time.sleep(2)
        
        # Start Main Orchestrator (puerto 8000)
        if orchestrator_ready:
            orchestrator_proc = start_service("Main Orchestrator", "main.py", 8000)
            if orchestrator_proc:
                processes.append(("Main Orchestrator", orchestrator_proc, 8000))
                if wait_for_service(8000, "Main Orchestrator", 20):
                    print("✅ Main Orchestrator ready")
                else:
                    print("⚠️ Main Orchestrator may not be ready")
        
        time.sleep(3)
        
        # 4. Final health check
        print("\n🏥 FINAL HEALTH CHECK")
        print("-"*30)
        
        services_status = []
        if discovery_ready:
            services_status.append((8002, "Discovery Service"))
        if replicator_ready:
            services_status.append((8001, "Message Replicator"))
        if orchestrator_ready:
            services_status.append((8000, "Main Orchestrator"))
        
        healthy_services = 0
        for port, name in services_status:
            if check_service_health(port, name):
                healthy_services += 1
        
        print(f"\n📊 SYSTEM STATUS: {healthy_services}/{len(services_status)} services healthy")
        
        if healthy_services > 0:
            print("\n🌐 ACCESS URLS:")
            print("="*50)
            if orchestrator_ready:
                print("🎭 Main Dashboard:      http://localhost:8000/dashboard")
                print("🔍 Discovery System:    http://localhost:8000/discovery")  
                print("👥 Groups Hub:          http://localhost:8000/groups")
                print("📚 API Documentation:   http://localhost:8000/docs")
                print("🏥 Health Check:        http://localhost:8000/health")
            
            print("\n🔗 DIRECT SERVICE ACCESS:")
            if discovery_ready:
                print("🔍 Discovery Service:   http://localhost:8002/")
            if replicator_ready:
                print("📡 Message Replicator:  http://localhost:8001/")
            print("="*50)
            print("\n✨ ENTERPRISE SYSTEM IS READY!")
            print("Press Ctrl+C to stop all services...")
            
            # Wait for keyboard interrupt
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
        else:
            print("❌ No services started successfully")
            
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"❌ Startup error: {e}")
    finally:
        print("\n🛑 STOPPING ALL SERVICES...")
        print("-"*30)
        
        for name, proc, port in processes:
            try:
                print(f"🛑 Stopping {name}...")
                proc.terminate()
                proc.wait(timeout=5)
                print(f"✅ {name} stopped")
            except subprocess.TimeoutExpired:
                print(f"⚠️ Force killing {name}...")
                proc.kill()
                proc.wait()
            except Exception as e:
                print(f"❌ Error stopping {name}: {e}")
        
        print("\n👋 ENTERPRISE SYSTEM STOPPED")
        print("="*50)

if __name__ == "__main__":
    main()