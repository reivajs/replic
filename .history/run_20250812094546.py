#!/usr/bin/env python3
"""
Run Script - Ejecutar solo main.py
=================================
"""

import subprocess
import sys

def main():
    print("🚀 Ejecutando main.py...")
    print("🌐 Dashboard estará en: http://localhost:8000/dashboard")
    print("📚 API Docs en: http://localhost:8000/docs")
    print("\nPresiona Ctrl+C para detener...")
    
    try:
        subprocess.run([sys.executable, "main.py"])
    except KeyboardInterrupt:
        print("\n👋 Aplicación detenida")

if __name__ == "__main__":
    main()
