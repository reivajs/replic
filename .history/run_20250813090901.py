#!/usr/bin/env python3
"""
🚀 QUICK START SCRIPT
====================
Script simplificado para iniciar tu sistema enterprise
"""

import subprocess
import sys
import time
import os
from pathlib import Path
import shutil

def setup_files():
    """Setup inicial de archivos"""
    print("📁 Setting up files...")
    
    # Crear directorios
    dirs = ["services/message_replicator", "services/discovery", "data", "sessions", "logs"]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
        print(f"   ✅ {d}")
    
    # Verificar archivos críticos
    files_to_check = [
        ("paste.txt", "services/message_replicator/main.py"),
        ("paste-2.txt", "main.py"),
        ("services/discovery/main.py", None)  # Ya debe existir del artifact anterior
    ]
    
    missing_files = []
    for source, target in files_to_check:
        if target and Path(source).exists() and not Path(target).exists():
            try:
                shutil.copy(source, target)
                print(f"   ✅ Copied {source} → {target}")
            except Exception as e:
                print(f"   ❌ Failed to copy {source}: {e}")
                missing_files.append(source)
        elif target and not Path(target).exists():
            missing_files.append(target)
        elif not target and not Path(source).exists():
            missing_files.append(source)
    
    if missing_files:
        print(f"\n❌ Missing files: {missing_files}")
        print("\n💡 ACTION NEEDED:")
        print("1. Make sure paste.txt exists (your Message Replicator)")
        print("2. Make sure paste-2.txt exists (your Main Orchestrator)")
        print("3. Create services/discovery/main.py from the Discovery Service artifact")
        return False
    
    print("✅ All files ready!")
    return True

def start_service(name, script_path, port):
    """Start a service"""
    if not Path(script_path).exists():
        print(f"❌ {script_path} not found")
        return None
    
    print(f"🚀 Starting {name} on port {port}...")
    try:
        proc = subprocess.Popen([
            sys.executable, script_path
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return proc
    except Exception as e:
        print(f"❌ Failed to start {name}: {e}")
        return None

def check_service(port, name, timeout=10):
    """Check if service is responding"""
    import requests
    
    for i in range(timeout):
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=2)
            if response.status_code == 200:
                print(f"✅ {name} (port {port}) - Ready!")
                return True
        except:
            pass
        time.sleep(1)
        if i % 3 == 0:
            print(f"   ⏳ Waiting for {name}... ({i+1}/{timeout})")
    
    print(f"❌ {name} (port {port}) - Not responding")
    return False

def main():
    """Main function"""
    print("🚀 QUICK START - ENTERPRISE SYSTEM")
    print("="*50)
    
    # 1. Setup files
    if not setup_files():
        print("\n❌ Setup failed. Please fix missing files and try again.")
        return
    
    print("\n🎯 STARTING SERVICES...")
    print("-"*30)
    
    processes = []
    
    try:
        # Start services in order
        services = [
            ("Discovery Service", "services/discovery/main.py", 8002),
            ("Message Replicator", "services/message_replicator/main.py", 8001),
            ("Main Orchestrator", "main.py", 8000)
        ]
        
        for name, script, port in services:
            proc = start_service(name, script, port)
            if proc:
                processes.append((name, proc, port))
                time.sleep(3)  # Give service time to start
                
                # Check if it's responding
                check_service(port, name)
            else:
                print(f"⚠️ Skipping {name}")
        
        # Final status
        print(f"\n📊 SERVICES STARTED: {len(processes)}")
        
        if len(processes) >= 2:  # At least 2 services running
            print("\n🌐 ACCESS YOUR SYSTEM:")
            print("="*40)
            print("🎭 Main Dashboard:      http://localhost:8000/dashboard")
            print("🔍 Discovery System:    http://localhost:8000/discovery")
            print("👥 Groups Hub:          http://localhost:8000/groups")
            print("📚 API Docs:            http://localhost:8000/docs")
            print()
            print("🔗 DIRECT ACCESS:")
            print("🔍 Discovery Service:   http://localhost:8002/")
            print("📡 Message Replicator:  http://localhost:8001/")
            print("="*40)
            print("\n✨ SYSTEM READY! Press Ctrl+C to stop...")
            
            # Keep running
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
        else:
            print("❌ Not enough services started")
    
    except KeyboardInterrupt:
        pass
    finally:
        print("\n🛑 STOPPING SERVICES...")
        for name, proc, port in processes:
            try:
                print(f"   Stopping {name}...")
                proc.terminate()
                proc.wait(timeout=5)
            except:
                proc.kill()
        print("👋 System stopped")

if __name__ == "__main__":
    main()