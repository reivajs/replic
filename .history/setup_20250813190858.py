#!/usr/bin/env python3
"""
🚀 ENTERPRISE SYSTEM STARTER
============================
Inicia todos los microservicios del sistema enterprise
"""

import asyncio
import subprocess
import sys
import time
import signal
import os
from pathlib import Path
from typing import List, Dict

# Color codes for beautiful output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class EnterpriseSystemStarter:
    """Starter para el sistema enterprise completo"""
    
    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.services = {
            "discovery": {
                "name": "🔍 Discovery Service",
                "port": 8002,
                "file": "services/discovery/main.py",
                "required": False,
                "process": None
            },
            "replicator": {
                "name": "📡 Message Replicator",
                "port": 8001,
                "file": "services/message_replicator/main.py",
                "required": True,
                "process": None
            },
            "orchestrator": {
                "name": "🎭 Main Orchestrator",
                "port": 8000,
                "file": "main.py",
                "required": True,
                "process": None
            },
            "watermark": {
                "name": "🎨 Watermark Service",
                "port": 8081,
                "file": "services/watermark/main.py",
                "required": False,
                "process": None
            }
        }
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def print_banner(self):
        """Print enterprise banner"""
        banner = f"""
{Colors.HEADER}{'='*80}
🚀 ENTERPRISE MICROSERVICES SYSTEM STARTER v2.0
{'='*80}{Colors.ENDC}

{Colors.OKBLUE}🎯 Starting enterprise-grade microservices system...{Colors.ENDC}

{Colors.OKCYAN}📋 Services to start:{Colors.ENDC}
"""
        print(banner)
        
        for service_id, service in self.services.items():
            status = f"{Colors.OKGREEN}✅ Required{Colors.ENDC}" if service["required"] else f"{Colors.WARNING}⚠️ Optional{Colors.ENDC}"
            print(f"   {service['name']:<25} Port {service['port']:<6} {status}")
        
        print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}")
    
    def check_dependencies(self) -> bool:
        """Check system dependencies"""
        print(f"\n{Colors.OKBLUE}🔍 Checking dependencies...{Colors.ENDC}")
        
        # Check Python version
        if sys.version_info < (3, 8):
            print(f"{Colors.FAIL}❌ Python 3.8+ required, found {sys.version}{Colors.ENDC}")
            return False
        
        print(f"{Colors.OKGREEN}✅ Python {sys.version.split()[0]}{Colors.ENDC}")
        
        # Check required files
        missing_files = []
        for service_id, service in self.services.items():
            if service["required"] and not Path(service["file"]).exists():
                missing_files.append(service["file"])
        
        if missing_files:
            print(f"{Colors.FAIL}❌ Missing required files:{Colors.ENDC}")
            for file in missing_files:
                print(f"   - {file}")
            return False
        
        print(f"{Colors.OKGREEN}✅ All required files present{Colors.ENDC}")
        
        # Check .env file
        if not Path(".env").exists():
            print(f"{Colors.WARNING}⚠️ .env file not found - some services may use defaults{Colors.ENDC}")
        else:
            print(f"{Colors.OKGREEN}✅ .env configuration file found{Colors.ENDC}")
        
        # Create data directory
        Path("data").mkdir(exist_ok=True)
        Path("logs").mkdir(exist_ok=True)
        print(f"{Colors.OKGREEN}✅ Data directories created{Colors.ENDC}")
        
        return True
    
    def start_service(self, service_id: str, service_config: Dict) -> bool:
        """Start a single service"""
        if not Path(service_config["file"]).exists():
            if service_config["required"]:
                print(f"{Colors.FAIL}❌ {service_config['name']}: File not found - {service_config['file']}{Colors.ENDC}")
                return False
            else:
                print(f"{Colors.WARNING}⚠️ {service_config['name']}: File not found - skipping{Colors.ENDC}")
                return True
        
        try:
            print(f"{Colors.OKBLUE}🚀 Starting {service_config['name']}...{Colors.ENDC}")
            
            # Start the service
            process = subprocess.Popen(
                [sys.executable, service_config["file"]],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            service_config["process"] = process
            self.processes.append(process)
            
            # Give it a moment to start
            time.sleep(2)
            
            # Check if process is still running
            if process.poll() is None:
                print(f"{Colors.OKGREEN}✅ {service_config['name']} started on port {service_config['port']}{Colors.ENDC}")
                return True
            else:
                stdout, stderr = process.communicate()
                print(f"{Colors.FAIL}❌ {service_config['name']} failed to start{Colors.ENDC}")
                if stderr:
                    print(f"{Colors.FAIL}   Error: {stderr[:200]}...{Colors.ENDC}")
                return service_config.get("required", True) == False
                
        except Exception as e:
            print(f"{Colors.FAIL}❌ {service_config['name']}: {str(e)}{Colors.ENDC}")
            return service_config.get("required", True) == False
    
    def wait_for_services(self):
        """Wait for services to be ready"""
        print(f"\n{Colors.OKBLUE}⏳ Waiting for services to be ready...{Colors.ENDC}")
        
        import requests
        import time
        
        for service_id, service in self.services.items():
            if service["process"] and service["process"].poll() is None:
                # Try to connect to service
                for attempt in range(30):  # 30 seconds timeout
                    try:
                        response = requests.get(f"http://localhost:{service['port']}/health", timeout=1)
                        if response.status_code == 200:
                            print(f"{Colors.OKGREEN}✅ {service['name']} is ready{Colors.ENDC}")
                            break
                    except:
                        pass
                    
                    time.sleep(1)
                else:
                    print(f"{Colors.WARNING}⚠️ {service['name']} may not be fully ready{Colors.ENDC}")
    
    def print_access_info(self):
        """Print access information"""
        print(f"\n{Colors.HEADER}🌐 SYSTEM READY - ACCESS INFORMATION{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}")
        
        running_services = [
            (service["name"], service["port"], service["file"])
            for service in self.services.values()
            if service["process"] and service["process"].poll() is None
        ]
        
        if running_services:
            print(f"{Colors.OKGREEN}🎉 Successfully started {len(running_services)} services:{Colors.ENDC}\n")
            
            # Main access points
            main_endpoints = [
                ("🎭 Main Dashboard", "http://localhost:8000/dashboard", "Enterprise control center"),
                ("🎭 Groups Hub", "http://localhost:8000/groups", "Visual groups management"),
                ("🔍 Discovery System", "http://localhost:8000/discovery", "Auto-discovery interface"),
                ("📚 API Documentation", "http://localhost:8000/docs", "Interactive API docs")
            ]
            
            print(f"{Colors.OKCYAN}🎯 MAIN ACCESS POINTS:{Colors.ENDC}")
            for name, url, desc in main_endpoints:
                print(f"   {name:<25} {url:<35} {desc}")
            
            print(f"\n{Colors.OKCYAN}🔧 SERVICE ENDPOINTS:{Colors.ENDC}")
            for name, port, file in running_services:
                health_url = f"http://localhost:{port}/health"
                dashboard_url = f"http://localhost:{port}/" if port != 8000 else f"http://localhost:{port}/dashboard"
                print(f"   {name:<25} {dashboard_url:<35} {health_url}")
            
            print(f"\n{Colors.OKBLUE}💡 QUICK TIPS:{Colors.ENDC}")
            print(f"   • Start with the Groups Hub: {Colors.UNDERLINE}http://localhost:8000/groups{Colors.ENDC}")
            print(f"   • Use Discovery System to find Telegram groups automatically")
            print(f"   • Drag and drop groups to configure them quickly")
            print(f"   • Monitor everything from the main dashboard")
            
            print(f"\n{Colors.WARNING}🛑 TO STOP ALL SERVICES:{Colors.ENDC}")
            print(f"   Press {Colors.BOLD}Ctrl+C{Colors.ENDC} in this terminal")
            
        else:
            print(f"{Colors.FAIL}❌ No services are running{Colors.ENDC}")
    
    def monitor_services(self):
        """Monitor running services"""
        print(f"\n{Colors.OKBLUE}👁️ Monitoring services... (Press Ctrl+C to stop all){Colors.ENDC}")
        
        try:
            while True:
                time.sleep(10)
                
                # Check if any process died
                dead_services = []
                for service_id, service in self.services.items():
                    if service["process"] and service["process"].poll() is not None:
                        dead_services.append(service["name"])
                
                if dead_services:
                    print(f"{Colors.FAIL}💀 Dead services detected: {', '.join(dead_services)}{Colors.ENDC}")
                    if any(self.services[sid]["required"] for sid, s in self.services.items() if s["name"] in dead_services):
                        print(f"{Colors.FAIL}🚨 Critical service died - stopping system{Colors.ENDC}")
                        break
                
        except KeyboardInterrupt:
            print(f"\n{Colors.WARNING}🛑 Shutdown signal received{Colors.ENDC}")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n{Colors.WARNING}🛑 Received signal {signum} - shutting down gracefully...{Colors.ENDC}")
        self.shutdown()
    
    def shutdown(self):
        """Graceful shutdown of all services"""
        print(f"{Colors.WARNING}🔄 Stopping all services...{Colors.ENDC}")
        
        for service_id, service in self.services.items():
            if service["process"] and service["process"].poll() is None:
                print(f"   🛑 Stopping {service['name']}...")
                try:
                    service["process"].terminate()
                    service["process"].wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print(f"   💀 Force killing {service['name']}...")
                    service["process"].kill()
                except Exception as e:
                    print(f"   ❌ Error stopping {service['name']}: {e}")
        
        print(f"{Colors.OKGREEN}✅ All services stopped{Colors.ENDC}")
        print(f"{Colors.HEADER}👋 Enterprise system shutdown complete{Colors.ENDC}")
        sys.exit(0)
    
    def start_system(self):
        """Start the complete enterprise system"""
        self.print_banner()
        
        # Check dependencies
        if not self.check_dependencies():
            print(f"{Colors.FAIL}❌ Dependency check failed - aborting{Colors.ENDC}")
            return False
        
        # Start services in order
        success_count = 0
        required_count = sum(1 for s in self.services.values() if s["required"])
        
        print(f"\n{Colors.OKBLUE}🚀 Starting services...{Colors.ENDC}")
        
        # Start in specific order for dependencies
        start_order = ["replicator", "discovery", "watermark", "orchestrator"]
        
        for service_id in start_order:
            if service_id in self.services:
                if self.start_service(service_id, self.services[service_id]):
                    if self.services[service_id]["required"]:
                        success_count += 1
        
        # Check if we have minimum required services
        if success_count < required_count:
            print(f"{Colors.FAIL}❌ Failed to start required services - shutting down{Colors.ENDC}")
            self.shutdown()
            return False
        
        # Wait for services to be ready
        self.wait_for_services()
        
        # Print access information
        self.print_access_info()
        
        # Start monitoring
        self.monitor_services()
        
        return True

def main():
    """Main entry point"""
    starter = EnterpriseSystemStarter()
    
    try:
        starter.start_system()
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}🛑 Interrupted by user{Colors.ENDC}")
        starter.shutdown()
    except Exception as e:
        print(f"\n{Colors.FAIL}💥 Unexpected error: {e}{Colors.ENDC}")
        starter.shutdown()

if __name__ == "__main__":
    main()