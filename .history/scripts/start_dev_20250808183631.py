import subprocess
import sys
import time
import signal
import os
from pathlib import Path

processes = {}

def start_service(name, script, port):
    print("Starting {0} on port {1}...".format(name, port))
    try:
        process = subprocess.Popen([sys.executable, script])
        processes[name] = process
        return process
    except Exception as e:
        print("Error starting {0}: {1}".format(name, e))
        return None

def stop_all():
    print("\nStopping all services...")
    for name, process in processes.items():
        try:
            process.terminate()
            process.wait(timeout=5)
            print("   {0} stopped".format(name))
        except:
            process.kill()
            print("   {0} killed".format(name))

def signal_handler(signum, frame):
    stop_all()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def main():
    print("Starting Enterprise SaaS Development Mode")
    print("=" * 50)
    
    # Create logs directory
    if not os.path.exists("logs"):
        os.makedirs("logs")
    
    services = [
        ("Main Orchestrator", "main.py", 8000),
        ("Message Replicator", "services/message_replicator/main.py", 8001),
        ("Analytics", "services/analytics/main.py", 8002)
    ]
    
    for name, script, port in services:
        if os.path.exists(script):
            start_service(name, script, port)
            time.sleep(2)
        else:
            print("Warning: {0} not found".format(script))
    
    print("=" * 50)
    print("All services started!")
    print("Dashboard: http://localhost:8000/dashboard")
    print("Health: http://localhost:8000/health")
    print("Message Replicator: http://localhost:8001")
    print("Analytics: http://localhost:8002")
    print("\nPress Ctrl+C to stop all services")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_all()

if __name__ == "__main__":
    main()
