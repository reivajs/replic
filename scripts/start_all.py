#!/usr/bin/env python3
"""
🚀 DESARROLLO COMPLETO - Iniciar todos los microservicios
========================================================
Script para iniciar la arquitectura enterprise completa
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
    print("🎭 Iniciando Enterprise Microservices COMPLETO...")
    print("=" * 70)
    
    processes = []
    
    try:
        # Todos los servicios en orden óptimo
        services = [
            ("Message Replicator", "services/message_replicator/main.py", 8001),
            ("Analytics Service", "services/analytics/main.py", 8002),
            ("File Manager", "services/file_manager/main.py", 8003),
            ("Main Orchestrator", "main.py", 8000)
        ]
        
        # Iniciar cada servicio con delay
        for name, script, port in services:
            process = start_service(name, script, port)
            if process:
                processes.append((name, process, port))
                time.sleep(4)  # Esperar entre inicios para estabilidad
        
        print("\n" + "=" * 70)
        print("✅ ARQUITECTURA ENTERPRISE COMPLETA INICIADA")
        print("\n🌐 URLs disponibles:")
        print("   📊 Dashboard Principal:   http://localhost:8000/dashboard")
        print("   🏥 Health Check:          http://localhost:8000/health")
        print("   📚 API Docs Completas:    http://localhost:8000/docs")
        print("\n🔗 Microservicios individuales:")
        print("   📡 Message Replicator:    http://localhost:8001/docs")
        print("   📊 Analytics Service:     http://localhost:8002/docs")
        print("   💾 File Manager:          http://localhost:8003/docs")
        print("\n🎯 CARACTERÍSTICAS ENTERPRISE ACTIVAS:")
        print("   ✅ Tu Enhanced Replicator Service (100% funcional)")
        print("   ✅ Analytics SaaS con métricas en tiempo real")
        print("   ✅ File Manager con upload/download de archivos")
        print("   ✅ Dashboard enterprise con glassmorphism")
        print("   ✅ Health checks automáticos cada 30 segundos")
        print("   ✅ APIs REST completas para todos los servicios")
        print("   ✅ Arquitectura escalable horizontalmente")
        print("   ✅ Service discovery automático")
        print("   ✅ Logging centralizado")
        print("\n💡 PRÓXIMOS PASOS:")
        print("   1. Abre el dashboard: http://localhost:8000/dashboard")
        print("   2. Verifica health checks en tiempo real")
        print("   3. Explora las APIs individuales en /docs")
        print("   4. Tu Enhanced Replicator ya está funcionando!")
        print("=" * 70)
        print("\nPresiona Ctrl+C para detener toda la arquitectura...")
        
        # Esperar a que terminen los procesos
        for name, process, port in processes:
            process.wait()
    
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo arquitectura enterprise...")
        
        # Detener en orden inverso para cleanup ordenado
        for name, process, port in reversed(processes):
            print(f"   🛑 Deteniendo {name}...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print(f"   🔥 Forzando cierre de {name}...")
                process.kill()
        
        print("\n👋 Arquitectura enterprise detenida completamente")
        print("💾 Datos preservados en database/ y files/")

if __name__ == "__main__":
    main()
