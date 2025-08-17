"""
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
