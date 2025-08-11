#!/usr/bin/env python3
"""
🚀 STARTUP SCRIPT PARA TU SISTEMA COMPLETO
==========================================
Inicia todos los servicios en el orden correcto
"""

import subprocess
import sys
import time
import os
from pathlib import Path

def start_discovery_service():
    """Iniciar Discovery Service"""
    print("🔍 Iniciando Discovery Service...")
    
    discovery_path = Path("services/discovery/main.py")
    if discovery_path.exists():
        return subprocess.Popen([
            sys.executable, str(discovery_path)
        ], cwd=".", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        print("❌ services/discovery/main.py no encontrado")
        print("💡 Copia paste.txt a services/discovery/main.py")
        return None

def start_main_orchestrator():
    """Iniciar Main Orchestrator"""
    print("🎭 Iniciando Main Orchestrator...")
    
    return subprocess.Popen([
        sys.executable, "main.py"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def check_service_health(port):
    """Verificar si un servicio está funcionando"""
    try:
        import requests
        response = requests.get(f"http://localhost:{port}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    """Función principal"""
    print("🚀 Iniciando Sistema Completo Enterprise")
    print("=" * 50)
    
    # Crear directorios necesarios
    Path("services/discovery").mkdir(parents=True, exist_ok=True)
    Path("frontend/templates").mkdir(parents=True, exist_ok=True)
    Path("data").mkdir(exist_ok=True)
    Path("sessions").mkdir(exist_ok=True)
    
    processes = []
    
    try:
        # 1. Iniciar Discovery Service (puerto 8002)
        discovery_process = start_discovery_service()
        if discovery_process:
            processes.append(("Discovery Service", discovery_process, 8002))
            print("⏳ Esperando que Discovery Service arranque...")
            time.sleep(5)
            
            if check_service_health(8002):
                print("✅ Discovery Service funcionando en puerto 8002")
            else:
                print("⚠️ Discovery Service puede no estar funcionando correctamente")
        
        # 2. Iniciar Main Orchestrator (puerto 8000)
        main_process = start_main_orchestrator()
        processes.append(("Main Orchestrator", main_process, 8000))
        
        print("⏳ Esperando que Main Orchestrator arranque...")
        time.sleep(3)
        
        if check_service_health(8000):
            print("✅ Main Orchestrator funcionando en puerto 8000")
        else:
            print("⚠️ Main Orchestrator puede no estar funcionando correctamente")
        
        print("\n" + "=" * 50)
        print("🎉 SISTEMA ENTERPRISE INICIADO")
        print("=" * 50)
        print("🌐 URLs disponibles:")
        print("   📊 Dashboard Principal: http://localhost:8000/dashboard")
        print("   🔍 Discovery System:    http://localhost:8000/discovery")
        print("   🏥 Health Check:        http://localhost:8000/health")
        print("   📚 API Docs:            http://localhost:8000/docs")
        print("   🔧 Discovery API:       http://localhost:8002/status")
        print("\n🎯 FUNCIONALIDADES DISPONIBLES:")
        print("   ✅ Auto-Discovery de chats de Telegram")
        print("   ✅ Configuración visual sin código")
        print("   ✅ Replicación en tiempo real")
        print("   ✅ WebSocket real-time updates")
        print("   ✅ Dashboard enterprise moderno")
        print("\nPresiona Ctrl+C para detener el sistema...")
        
        # Mantener procesos ejecutándose
        while True:
            time.sleep(1)
            
            # Verificar que los procesos siguen ejecutándose
            for name, process, port in processes:
                if process.poll() is not None:
                    print(f"⚠️ {name} se ha detenido inesperadamente")
    
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo sistema...")
        
        for name, process, port in processes:
            print(f"   Deteniendo {name}...")
            process.terminate()
            try:
                process.wait(timeout=5)
                print(f"   ✅ {name} detenido correctamente")
            except subprocess.TimeoutExpired:
                print(f"   🔥 Forzando cierre de {name}...")
                process.kill()
        
        print("👋 Sistema completamente detenido")

if __name__ == "__main__":
    main()