#!/usr/bin/env python3
"""Script de desarrollo con hot reload"""

import subprocess
import sys

def main():
    print("🔧 Starting in development mode...")
    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
    ])

if __name__ == "__main__":
    main()
