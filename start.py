#!/usr/bin/env python3
"""Script de inicio para Zero Cost SaaS"""

import subprocess
import sys
import time

def main():
    print("🚀 Iniciando Zero Cost SaaS...")
    print("=" * 50)
    
    try:
        # Iniciar orchestrator principal
        print("Starting main orchestrator on port 8000...")
        subprocess.run([sys.executable, "main.py"])
        
    except KeyboardInterrupt:
        print("\n🛑 Shutdown requested")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
