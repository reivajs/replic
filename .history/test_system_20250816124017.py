#!/usr/bin/env python3
"""
Test Script - Verificar que todo funciona
==========================================
"""

import asyncio
import httpx

async def test_system():
    """Probar el sistema"""
    print("\n🧪 PROBANDO SISTEMA\n")
    
    async with httpx.AsyncClient() as client:
        # Test health
        print("Testing /health...")
        response = await client.get("http://localhost:8000/api/v1/health")
        print(f"Health: {response.status_code}")
        
        # Test dashboard stats
        print("\nTesting dashboard stats...")
        response = await client.get("http://localhost:8000/api/v1/dashboard/api/stats")
        print(f"Stats: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Messages received: {data.get('messages_received', 0)}")
            print(f"  Uptime: {data.get('uptime_formatted', 'N/A')}")
        
        # Test flows
        print("\nTesting flows...")
        response = await client.get("http://localhost:8000/api/v1/dashboard/api/flows")
        print(f"Flows: {response.status_code}")
        
    print("\n✅ Tests completados")

if __name__ == "__main__":
    print("Asegúrate de que el servidor esté corriendo en http://localhost:8000")
    print("Presiona Enter para continuar...")
    input()
    asyncio.run(test_system())
