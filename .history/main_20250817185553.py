#!/usr/bin/env python3
"""
SIMPLE STARTUP - Inicio rápido del sistema
==========================================
"""

import asyncio
import uvicorn
from pathlib import Path
import sys

# Añadir proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def start_system():
    """Iniciar sistema simplificado"""
    print("\n" + "="*70)
    print("🚀 INICIANDO SISTEMA MODULAR")
    print("="*70 + "\n")
    
    # Verificar que existe .env
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ ERROR: No se encontró archivo .env")
        print("Copia .env.example a .env y configura tus credenciales")
        return
    
    print("✅ Archivo .env encontrado")
    print("✅ Iniciando servidor...")
    print("\n🌐 El sistema estará disponible en:")
    print("   📊 Dashboard: http://localhost:8000")
    print("   📚 API Docs:  http://localhost:8000/docs")
    print("   🏥 Health:    http://localhost:8000/api/v1/health")
    print("\n[Presiona Ctrl+C para detener]\n")
    
    # Iniciar servidor
    config = uvicorn.Config(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
    
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    try:
        asyncio.run(start_system())
    except KeyboardInterrupt:
        print("\n✅ Sistema detenido por el usuario")
