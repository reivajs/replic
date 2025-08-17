import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass
import httpx
import yaml
from tenacity import retry, stop_after_attempt, wait_exponential

@dataclass
class ServiceInfo:
    name: str
    url: str
    port: int
    health_endpoint: str = "/health"
    timeout: int = 10
    retry_attempts: int = 3
    circuit_breaker_threshold: int = 5

class ServiceRegistry:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.services: Dict[str, ServiceInfo] = {}
        self.health_status: Dict[str, bool] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def initialize(self):
        """Load services from config file"""
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        for name, details in config['services'].items():
            service = ServiceInfo(**details)
            self.services[name] = service
            self.circuit_breakers[name] = CircuitBreaker(
                threshold=service.circuit_breaker_threshold
            )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def call_service(
        self,
        service_name: str,
        endpoint: str,
        method: str = "GET",
        **kwargs
    ):
        """Call a service with circuit breaker and retry logic"""
        service = self.services.get(service_name)
        if not service:
            raise ValueError(f"Service {service_name} not found")
        
        # Check circuit breaker
        breaker = self.circuit_breakers[service_name]
        if breaker.is_open():
            raise ServiceUnavailableError(f"{service_name} circuit breaker is open")
        
        try:
            url = f"{service.url}{endpoint}"
            response = await self.http_client.request(method, url, **kwargs)
            response.raise_for_status()
            breaker.record_success()
            return response.json()
        except Exception as e:
            breaker.record_failure()
            raise