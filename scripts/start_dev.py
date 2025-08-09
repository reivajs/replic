#!/usr/bin/env python3
"""
🚀 DESARROLLO - Iniciar microservicio principal
=============================================
Script simplificado para desarrollo
"""

import subprocess
import sys
import time
import os
from pathlib import Path

def start_service(service_name: str, script_path: str, port: int):
    """Iniciar un microservicio"""
    print(f"🚀 Iniciando {service_name} en puerto {port}...")
    
    if not Path(script_path).exists():
        print(f"⚠️ {script_path} no encontrado")
        return None
    
    return subprocess.Popen([
        sys.executable, script_path
    ])

def main():
    """Función principal"""
    print("🎭 Iniciando Enterprise Microservices...")
    print("=" * 60)
    
    processes = []
    
    try:
        # Servicios principales
        services = [
            ("Message Replicator", "services/message_replicator/main.py", 8001),
            ("Main Orchestrator", "main.py", 8000)
        ]
        
        # Iniciar cada servicio
        for name, script, port in services:
            process = start_service(name, script, port)
            if process:
                processes.append((name, process, port))
                time.sleep(3)  # Esperar entre inicios
        
        print("\n" + "=" * 60)
        print("✅ Servicios principales iniciados")
        print("\n🌐 URLs disponibles:")
        print("   📊 Dashboard:         http://localhost:8000/dashboard")
        print("   🏥 Health Check:      http://localhost:8000/health")
        print("   📚 API Docs:          http://localhost:8000/docs")
        print("\n🔗 Microservicios:")
        print("   📡 Message Replicator: http://localhost:8001")
        print("\n🎯 Tu Enhanced Replicator está corriendo como microservicio!")
        print("=" * 60)
        print("\nPresiona Ctrl+C para detener...")
        
        # Esperar a que terminen
        for name, process, port in processes:
            process.wait()
    
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo servicios...")
        
        for name, process, port in processes:
            print(f"   Deteniendo {name}...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        
        print("👋 Servicios detenidos")

if __name__ == "__main__":
    main()
