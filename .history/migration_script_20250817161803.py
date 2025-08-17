#!/usr/bin/env python3
"""
🏥 HEALTH CHECK FIX - DASHBOARD COMPATIBILITY
============================================

Soluciona el error de health check dashboard:
"Health check error: cannot unpack non-iterable coroutine object"

Este error ocurre cuando el dashboard intenta hacer unpack de una coroutine
sin await. Lo solucionamos asegurando compatibilidad async/await.

Author: Senior Enterprise Developer  
Date: 2025-08-17
"""

import os
import sys
import asyncio
from pathlib import Path
from typing import Dict, Any, Tuple
import json
import logging

logger = logging.getLogger(__name__)

def fix_dashboard_health_check():
    """
    Solucionar el error de health check en dashboard
    
    El error: "cannot unpack non-iterable coroutine object" 
    Indica que el código está intentando hacer unpack de una coroutine sin await
    """
    
    # Buscar archivos de dashboard
    project_root = Path.cwd()
    dashboard_files = []
    
    # Buscar posibles archivos de dashboard
    for pattern in ["*dashboard*.py", "*health*.py", "api/*dashboard*.py", "app/api/*dashboard*.py"]:
        dashboard_files.extend(project_root.glob(pattern))
    
    print(f"🔍 Found {len(dashboard_files)} dashboard files to check:")
    for file in dashboard_files:
        print(f"  - {file}")
    
    # Patrones problemáticos a buscar y corregir
    problematic_patterns = [
        # Patrón 1: Unpack sin await
        {
            'pattern': r'(\w+),\s*(\w+)\s*=\s*([^(]+\([^)]*\))\s*(?!await)',
            'description': 'Variable unpacking without await',
            'fix': lambda match: f'{match.group(1)}, {match.group(2)} = await {match.group(3)}'
        },
        
        # Patrón 2: Return sin await  
        {
            'pattern': r'return\s+([^(]+\([^)]*\))\s*(?!await)',
            'description': 'Return without await',
            'fix': lambda match: f'return await {match.group(1)}'
        }
    ]
    
    fixed_files = []
    
    for dashboard_file in dashboard_files:
        try:
            with open(dashboard_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            fixes_applied = []
            
            # Buscar y corregir patrones problemáticos
            lines = content.split('\n')
            fixed_lines = []
            
            for i, line in enumerate(lines):
                fixed_line = line
                
                # Buscar patrones específicos conocidos que causan este error
                if 'health_check' in line.lower() and '=' in line and 'await' not in line:
                    if ',' in line and '(' in line and ')' in line:
                        # Posible unpack sin await
                        if not line.strip().startswith('#') and not line.strip().startswith('"""'):
                            # Agregar await si falta
                            if '=' in line and 'await' not in line:
                                parts = line.split('=', 1)
                                if len(parts) == 2:
                                    left = parts[0].strip()
                                    right = parts[1].strip()
                                    if '(' in right and ')' in right:
                                        fixed_line = f"{left} = await {right}"
                                        fixes_applied.append(f"Line {i+1}: Added await to assignment")
                
                fixed_lines.append(fixed_line)
            
            # Si se aplicaron correcciones
            if fixes_applied:
                fixed_content = '\n'.join(fixed_lines)
                
                # Crear backup
                backup_file = dashboard_file.with_suffix('.py.health_backup')
                with open(backup_file, 'w', encoding='utf-8') as f:
                    f.write(original_content)
                
                # Escribir archivo corregido
                with open(dashboard_file, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                
                fixed_files.append({
                    'file': dashboard_file,
                    'fixes': fixes_applied,
                    'backup': backup_file
                })
                
                print(f"✅ Fixed {dashboard_file}")
                for fix in fixes_applied:
                    print(f"   - {fix}")
            
        except Exception as e:
            print(f"❌ Error processing {dashboard_file}: {e}")
    
    return fixed_files

def create_corrected_dashboard_health_endpoint():
    """
    Crear endpoint de health check correcto para dashboard
    """
    
    health_check_code = '''"""
🏥 HEALTH CHECK ENDPOINT - CORRECTED VERSION
==========================================

Endpoint de health check compatible con dashboard
Soluciona: "cannot unpack non-iterable coroutine object"
"""

import asyncio
from typing import Dict, Any, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class HealthCheckManager:
    """Gestor de health checks compatible con dashboard"""
    
    def __init__(self):
        self.services = {}
        self.last_check = None
        self.check_interval = 30  # seconds
    
    async def check_service_health(self, service_name: str, service_instance) -> Tuple[bool, Dict[str, Any]]:
        """
        Verificar salud de un servicio individual
        
        Returns:
            (is_healthy, health_data)
        """
        try:
            health_data = {
                'service': service_name,
                'status': 'unknown',
                'timestamp': datetime.now().isoformat(),
                'details': {}
            }
            
            if hasattr(service_instance, 'get_health'):
                # Si el servicio tiene método get_health
                if asyncio.iscoroutinefunction(service_instance.get_health):
                    service_health = await service_instance.get_health()
                else:
                    service_health = service_instance.get_health()
                
                health_data.update(service_health)
                is_healthy = health_data.get('status') == 'healthy'
                
            elif hasattr(service_instance, 'is_running'):
                # Verificar si está corriendo
                is_running = service_instance.is_running if not callable(service_instance.is_running) else service_instance.is_running()
                is_healthy = bool(is_running)
                health_data['status'] = 'healthy' if is_healthy else 'unhealthy'
                health_data['details']['running'] = is_running
                
            else:
                # Verificar básico - si existe la instancia
                is_healthy = service_instance is not None
                health_data['status'] = 'healthy' if is_healthy else 'unhealthy'
                health_data['details']['exists'] = is_healthy
            
            return is_healthy, health_data
            
        except Exception as e:
            logger.error(f"❌ Error checking health for {service_name}: {e}")
            return False, {
                'service': service_name,
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    async def check_all_services(self, services: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Verificar salud de todos los servicios
        
        Returns:
            (overall_healthy, detailed_report)
        """
        try:
            overall_healthy = True
            service_reports = {}
            
            for service_name, service_instance in services.items():
                is_healthy, health_data = await self.check_service_health(service_name, service_instance)
                service_reports[service_name] = health_data
                
                if not is_healthy:
                    overall_healthy = False
            
            # Compilar reporte general
            report = {
                'overall_status': 'healthy' if overall_healthy else 'unhealthy',
                'timestamp': datetime.now().isoformat(),
                'services': service_reports,
                'summary': {
                    'total_services': len(services),
                    'healthy_services': sum(1 for r in service_reports.values() if r.get('status') == 'healthy'),
                    'unhealthy_services': sum(1 for r in service_reports.values() if r.get('status') != 'healthy')
                }
            }
            
            self.last_check = datetime.now()
            return overall_healthy, report
            
        except Exception as e:
            logger.error(f"❌ Error in comprehensive health check: {e}")
            return False, {
                'overall_status': 'error',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    async def quick_health_check(self) -> Tuple[bool, str]:
        """
        Health check rápido para endpoints simples
        
        Returns:
            (is_healthy, status_message)
        """
        try:
            # Check básico del sistema
            import psutil
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            
            is_healthy = cpu_percent < 90 and memory.percent < 90
            
            if is_healthy:
                return True, "System healthy"
            else:
                return False, f"System stressed: CPU {cpu_percent}%, RAM {memory.percent}%"
                
        except ImportError:
            # Si psutil no está disponible, asumir saludable
            return True, "Basic health check passed"
        except Exception as e:
            return False, f"Health check error: {str(e)}"

# Instance global para reuso
health_manager = HealthCheckManager()

# ============ FUNCIONES DE UTILIDAD PARA DASHBOARD ============

async def get_system_health() -> Dict[str, Any]:
    """Obtener salud del sistema para dashboard"""
    try:
        is_healthy, status = await health_manager.quick_health_check()
        
        return {
            'status': 'healthy' if is_healthy else 'unhealthy',
            'message': status,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f"Health check failed: {e}",
            'timestamp': datetime.now().isoformat()
        }

async def get_services_health(services: Dict[str, Any]) -> Dict[str, Any]:
    """Obtener salud de servicios para dashboard"""
    try:
        overall_healthy, report = await health_manager.check_all_services(services)
        return report
    except Exception as e:
        return {
            'overall_status': 'error',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }

# ============ ENDPOINT PATTERNS CORREGIDOS ============

async def dashboard_health_endpoint(services=None):
    """
    Endpoint de health para dashboard - VERSIÓN CORREGIDA
    
    USO CORRECTO en dashboard:
    
    # ❌ INCORRECTO (causa el error):
    # healthy, data = dashboard_health_endpoint()
    
    # ✅ CORRECTO:
    # healthy, data = await dashboard_health_endpoint()
    """
    try:
        if services:
            # Health check completo con servicios
            overall_healthy, report = await health_manager.check_all_services(services)
            return overall_healthy, report
        else:
            # Health check básico del sistema
            is_healthy, message = await health_manager.quick_health_check()
            return is_healthy, {
                'status': 'healthy' if is_healthy else 'unhealthy',
                'message': message,
                'timestamp': datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"❌ Dashboard health endpoint error: {e}")
        return False, {
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }

# ============ EJEMPLOS DE USO CORRECTO ============

async def example_dashboard_usage():
    """Ejemplos de cómo usar correctamente en dashboard"""
    
    # Ejemplo 1: Health check básico
    is_healthy, health_data = await dashboard_health_endpoint()
    print(f"System healthy: {is_healthy}")
    
    # Ejemplo 2: Health check con servicios
    services = {
        'watermark': None,  # Tu servicio de watermark
        'replicator': None,  # Tu servicio replicator
    }
    
    overall_healthy, detailed_report = await dashboard_health_endpoint(services)
    print(f"Overall healthy: {overall_healthy}")
    
    # Ejemplo 3: Health check de sistema solamente
    system_health = await get_system_health()
    print(f"System status: {system_health['status']}")

if __name__ == "__main__":
    # Test del health check
    asyncio.run(example_dashboard_usage())
'''
    
    # Escribir el archivo de health check corregido
    health_file = Path("app/utils/health_check_fixed.py")
    health_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(health_file, 'w', encoding='utf-8') as f:
        f.write(health_check_code)
    
    print(f"✅ Created corrected health check file: {health_file}")
    return health_file

def main():
    """Función principal"""
    print("🏥 FIXING DASHBOARD HEALTH CHECK ERRORS")
    print("=" * 50)
    
    # 1. Corregir archivos de dashboard existentes
    print("\n1. Scanning and fixing existing dashboard files...")
    fixed_files = fix_dashboard_health_check()
    
    if fixed_files:
        print(f"\n✅ Fixed {len(fixed_files)} files:")
        for fix_info in fixed_files:
            print(f"  - {fix_info['file']}")
            print(f"    Backup: {fix_info['backup']}")
    else:
        print("\n⚠️  No automatic fixes applied")
        print("    Manual review may be required")
    
    # 2. Crear health check corregido
    print("\n2. Creating corrected health check module...")
    health_file = create_corrected_dashboard_health_endpoint()
    
    # 3. Instrucciones
    print("\n" + "="*50)
    print("🔧 MANUAL FIX INSTRUCTIONS")
    print("="*50)
    
    print("""
    The error "cannot unpack non-iterable coroutine object" occurs when:
    
    ❌ WRONG:
    healthy, data = some_async_function()
    
    ✅ CORRECT:  
    healthy, data = await some_async_function()
    
    STEPS TO FIX MANUALLY:
    
    1. Find the dashboard file with health check code
    2. Look for lines like: "healthy, data = ..." 
    3. Add "await" before the function call
    4. Ensure the calling function is marked as "async"
    
    EXAMPLE FIX:
    
    # Before (❌):
    def dashboard_health():
        healthy, data = check_health()
        return healthy, data
    
    # After (✅):
    async def dashboard_health():
        healthy, data = await check_health()
        return healthy, data
    """)
    
    print(f"\n📁 New health check module created: {health_file}")
    print("   You can import and use this in your dashboard")
    
    print("\n🚀 NEXT STEPS:")
    print("1. Review any files that were automatically fixed")
    print("2. Apply manual fixes where needed")
    print("3. Test your dashboard health endpoint")
    print("4. Restart your application")

if __name__ == "__main__":
    main()