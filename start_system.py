#!/usr/bin/env python3
"""
Startup Script - Iniciar sistema completo
========================================
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def start_watermark_service():
    """Iniciar microservicio de watermarks"""
    if Path("watermark_service.py").exists():
        print("🎨 Iniciando Watermark Microservice...")
        return subprocess.Popen([sys.executable, "watermark_service.py"])
    else:
        print("⚠️ watermark_service.py no encontrado")
        return None

def start_main_application():
    """Iniciar aplicación principal"""
    print("🚀 Iniciando aplicación principal...")
    return subprocess.Popen([sys.executable, "main.py"])

def main():
    """Función principal"""
    print("🔧 Iniciando sistema completo...")
    
    processes = []
    
    try:
        # Iniciar microservicio de watermarks
        watermark_process = start_watermark_service()
        if watermark_process:
            processes.append(("Watermark Service", watermark_process))
            time.sleep(3)
        
        # Iniciar aplicación principal
        main_process = start_main_application()
        processes.append(("Main Application", main_process))
        
        print("✅ Sistema iniciado completamente")
        print("🌐 Dashboard principal: http://localhost:8000/dashboard")
        print("🎨 Watermark dashboard: http://localhost:8081/dashboard")
        print("\nPresiona Ctrl+C para detener...")
        
        # Esperar
        for name, process in processes:
            process.wait()
    
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo sistema...")
        for name, process in processes:
            print(f"   Deteniendo {name}...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        print("👋 Sistema detenido")

if __name__ == "__main__":
    main()
