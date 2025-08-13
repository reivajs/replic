import importlib

packages = [
    'fastapi', 
    'uvicorn', 
    'telethon', 
    'cryptg', 
    'aiohttp', 
    'python_dotenv'
]

for package in packages:
    try:
        importlib.import_module(package)
        print(f"El paquete '{package}' está instalado correctamente.")
    except ImportError:
        print(f"El paquete '{package}' NO está instalado.")
