import subprocess
import sys
import time
import signal
from pathlib import Path

processes = {}

def start_service(name, script, port):
    print(f"🚀 Starting {name} on port {port}...")
    try:
        process = subprocess.Popen([sys.executable, script])
        processes[name] = process
        return process
    except Exception as e:
        print(f"❌ Error starting {name}: {e}")
        return None

def stop_all():
    print("\n🛑 Stopping all services...")
    for name, process in processes.items():
        try:
            process.terminate()
            process.wait(timeout=5)
            print(f"   ✅ {name} stopped")
        except:
            process.kill()
            print(f"   🔪 {name} killed")

def signal_handler(signum, frame):
    stop_all()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def main():
    print("🔧 Starting Enterprise SaaS Development Mode")
    print("="*50)
    
    # Create directories
    Path("logs").mkdir(exist_ok=True)
    
    services = [
        ("Main Orchestrator", "main.py", 8000),
        ("Message Replicator", "services/message_replicator/main.py", 8001),
        ("Analytics", "services/analytics/main.py", 8002)
    ]
    
    for name, script, port in services:
        if Path(script).exists():
            start_service(name, script, port)
            time.sleep(2)
    
    print("="*50)
    print("✅ All services started!")
    print("📊 Dashboard: http://localhost:8000/dashboard")
    print("🏥 Health: http://localhost:8000/health")
    print("📡 Message Replicator: http://localhost:8001")
    print("📈 Analytics: http://localhost:8002")
    print("\nPress Ctrl+C to stop all services")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_all()

if __name__ == "__main__":
    main()