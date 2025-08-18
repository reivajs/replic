#!/usr/bin/env python3
"""
🚨 EMERGENCY FIX - SYNTAX ERROR MAIN.PY
=======================================
Este script repara automáticamente el error de sintaxis en main.py
"""

import os
import re
import shutil
from datetime import datetime
from pathlib import Path

def fix_main_py_syntax():
    """Reparar error de sintaxis en main.py"""
    
    print("🚨 EMERGENCY FIX - Reparando main.py")
    print("=" * 40)
    
    main_file = Path("main.py")
    
    if not main_file.exists():
        print("❌ main.py no encontrado")
        return False
    
    # Crear backup
    backup_file = f"main.py.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(main_file, backup_file)
    print(f"✅ Backup creado: {backup_file}")
    
    # Leer contenido
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"📄 Archivo leído: {len(content)} caracteres")
    
    # Mostrar líneas alrededor del error (línea 83)
    lines = content.split('\n')
    print("\n🔍 CONTENIDO ALREDEDOR DE LA LÍNEA 83:")
    print("-" * 40)
    
    start_line = max(0, 80)
    end_line = min(len(lines), 87)
    
    for i in range(start_line, end_line):
        if i < len(lines):
            marker = ">>> " if i == 82 else "    "  # línea 83 es index 82
            print(f"{marker}{i+1:3d}: {lines[i]}")
    
    print("-" * 40)
    
    # Patrones de problemas comunes
    fixes_applied = []
    
    # Fix 1: Líneas rotas con imports
    if '#!/usr/bin/env python3' in content and 'templates = Jinja2Templates' in content:
        # Buscar la línea problemática
        problem_pattern = r'(templates = Jinja2Templates\(directory="frontend/templates"\))\s*(#!/usr/bin/env python3)'
        if re.search(problem_pattern, content, re.MULTILINE):
            content = re.sub(problem_pattern, r'\1\n\n# \2', content)
            fixes_applied.append("Separar templates de shebang")
    
    # Fix 2: Comas faltantes en definiciones
    patterns_to_fix = [
        # Problema: falta coma después de statement
        (r'(\w+\s*=\s*[^,\n]+)(\s*[A-Z])', r'\1,\n\2'),
        
        # Problema: templates = ... directamente después de otra línea
        (r'([^,\n])(\s*templates\s*=\s*Jinja2Templates)', r'\1\n\n\2'),
        
        # Problema: falta separación entre statements
        (r'(\))(\s*templates\s*=)', r'\1\n\n\2'),
        
        # Fix específico para el error mostrado
        (r'(directory="frontend/templates"\))\s*(#!/usr/bin/env python3)', r'\1\n\n# \2'),
    ]
    
    for pattern, replacement in patterns_to_fix:
        old_content = content
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        if content != old_content:
            fixes_applied.append(f"Pattern fix: {pattern[:30]}...")
    
    # Fix 3: Remover shebang duplicado o mal colocado
    if content.count('#!/usr/bin/env python3') > 1:
        # Mantener solo el primero
        parts = content.split('#!/usr/bin/env python3')
        content = '#!/usr/bin/env python3' + ''.join(parts[1:])
        fixes_applied.append("Remover shebang duplicado")
    
    # Fix 4: Asegurar que templates esté en lugar correcto
    if 'templates = Jinja2Templates' in content:
        # Mover templates después de app = FastAPI
        content_lines = content.split('\n')
        new_lines = []
        templates_line = None
        
        for line in content_lines:
            if 'templates = Jinja2Templates' in line:
                templates_line = line
            elif 'app = FastAPI' in line:
                new_lines.append(line)
                if templates_line:
                    new_lines.append('')
                    new_lines.append('# Templates configuration')
                    new_lines.append(templates_line)
                    new_lines.append('')
                    templates_line = None
            else:
                new_lines.append(line)
        
        if templates_line:  # Si no se encontró app = FastAPI, añadir al principio
            new_lines.insert(1, '')
            new_lines.insert(2, '# Templates configuration')
            new_lines.insert(3, templates_line)
            new_lines.insert(4, '')
        
        content = '\n'.join(new_lines)
        fixes_applied.append("Reposicionar templates")
    
    # Fix 5: Limpiar líneas vacías excesivas
    content = re.sub(r'\n{3,}', '\n\n', content)
    fixes_applied.append("Limpiar líneas vacías")
    
    # Fix 6: Asegurar imports necesarios
    required_imports = [
        "from fastapi import FastAPI, Request, HTTPException",
        "from fastapi.responses import HTMLResponse",
        "from fastapi.templating import Jinja2Templates"
    ]
    
    for import_line in required_imports:
        module_name = import_line.split()[-1]
        if module_name not in content:
            # Añadir import después de la línea de shebang
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('from ') or line.startswith('import '):
                    lines.insert(i, import_line)
                    break
            content = '\n'.join(lines)
            fixes_applied.append(f"Añadir import: {module_name}")
    
    # Escribir archivo reparado
    with open(main_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n✅ FIXES APLICADOS ({len(fixes_applied)}):")
    for fix in fixes_applied:
        print(f"   - {fix}")
    
    print(f"\n📄 Archivo reparado: {len(content)} caracteres")
    
    # Verificar sintaxis
    try:
        compile(content, 'main.py', 'exec')
        print("✅ SINTAXIS VERIFICADA: OK")
        return True
    except SyntaxError as e:
        print(f"❌ SINTAXIS TODAVÍA TIENE ERRORES:")
        print(f"   Línea {e.lineno}: {e.text}")
        print(f"   Error: {e.msg}")
        
        # Mostrar contenido alrededor del nuevo error
        lines = content.split('\n')
        start = max(0, e.lineno - 3)
        end = min(len(lines), e.lineno + 2)
        
        print("\n🔍 CONTENIDO ALREDEDOR DEL ERROR:")
        for i in range(start, end):
            if i < len(lines):
                marker = ">>> " if i == e.lineno - 1 else "    "
                print(f"{marker}{i+1:3d}: {lines[i]}")
        
        return False

def create_clean_main_py():
    """Crear un main.py limpio y funcional"""
    
    print("\n🔧 Creando main.py limpio...")
    
    clean_main = '''#!/usr/bin/env python3
"""
🎭 ZERO COST PROJECT - MAIN ORCHESTRATOR
=======================================
Orchestrator principal con panel de watermarks integrado
"""

import asyncio
import logging
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear app FastAPI
app = FastAPI(
    title="Zero Cost Orchestrator",
    description="Sistema de replicación de mensajes con watermarks",
    version="2.0.0"
)

# Templates configuration
templates = Jinja2Templates(directory="frontend/templates")

# Static files (si existe el directorio)
if Path("frontend/static").exists():
    app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# ============ HEALTH CHECK ============

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "zero_cost_orchestrator",
        "version": "2.0.0"
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Zero Cost Orchestrator", "status": "running"}

# ============ DASHBOARD ============

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Dashboard principal"""
    try:
        return templates.TemplateResponse("dashboard.html", {"request": request})
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        return HTMLResponse(f"<h1>Dashboard</h1><p>Error: {e}</p>")

# ============ WATERMARK ADMIN PANEL ============

@app.get("/admin/watermarks", response_class=HTMLResponse)
async def watermark_admin_panel(request: Request):
    """Panel de administración de watermarks"""
    try:
        return templates.TemplateResponse("admin/watermarks.html", {"request": request})
    except Exception as e:
        logger.error(f"Error loading watermark panel: {e}")
        return HTMLResponse(f"""
        <h1>🎨 Panel de Watermarks</h1>
        <p>Error: {e}</p>
        <p>Asegúrate de que el archivo watermarks.html esté en frontend/templates/admin/</p>
        <a href="/dashboard">← Volver al Dashboard</a>
        """)

@app.get("/api/watermark/groups")
async def get_watermark_groups():
    """API para obtener grupos configurados"""
    try:
        import json
        from pathlib import Path
        
        config_dir = Path("config")
        groups = []
        
        if config_dir.exists():
            for config_file in config_dir.glob("group_*.json"):
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    groups.append(data)
                except Exception as e:
                    logger.error(f"Error loading {config_file}: {e}")
        
        return {"groups": groups, "status": "success"}
    except Exception as e:
        logger.error(f"Error getting groups: {e}")
        return {"error": str(e), "status": "error"}

@app.post("/api/watermark/groups/{group_id}/config")
async def save_group_config(group_id: int, config: dict):
    """Guardar configuración de grupo"""
    try:
        import json
        from pathlib import Path
        
        config_dir = Path("config")
        config_dir.mkdir(exist_ok=True)
        
        config_file = config_dir / f"group_{group_id}.json"
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        return {"status": "success", "message": "Configuración guardada"}
    except Exception as e:
        logger.error(f"Error saving config: {e}")
        return {"error": str(e), "status": "error"}

# ============ STARTUP ============

@app.on_event("startup")
async def startup_event():
    """Inicialización del sistema"""
    logger.info("🚀 Zero Cost Orchestrator iniciando...")
    
    # Crear directorios necesarios
    directories = ["config", "logs", "watermarks", "temp", "frontend/templates/admin"]
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    logger.info("✅ Zero Cost Orchestrator iniciado correctamente")

# ============ MAIN ============

if __name__ == "__main__":
    import uvicorn
    
    logger.info("🎭 Iniciando Zero Cost Orchestrator...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
'''
    
    # Escribir archivo limpio
    with open("main.py", 'w', encoding='utf-8') as f:
        f.write(clean_main)
    
    print("✅ main.py limpio creado")
    
    # Verificar sintaxis
    try:
        compile(clean_main, 'main.py', 'exec')
        print("✅ SINTAXIS VERIFICADA: OK")
        return True
    except SyntaxError as e:
        print(f"❌ Error en main.py limpio: {e}")
        return False

def main():
    """Función principal"""
    
    print("🚨 ZERO COST EMERGENCY FIX")
    print("=" * 30)
    print("Reparando error de sintaxis en main.py...")
    print()
    
    # Intentar reparar el archivo actual
    if fix_main_py_syntax():
        print("\n🎉 MAIN.PY REPARADO EXITOSAMENTE!")
        print("\n🚀 PRUEBA AHORA:")
        print("   python main.py")
        print("   # o")
        print("   python start_dev.py")
    else:
        print("\n⚠️ No se pudo reparar automáticamente.")
        print("Creando main.py limpio desde cero...")
        
        if create_clean_main_py():
            print("\n🎉 MAIN.PY LIMPIO CREADO!")
            print("\n🚀 PRUEBA AHORA:")
            print("   python main.py")
        else:
            print("\n❌ Error crítico. Contacta al desarrollador.")
            return False
    
    print("\n📋 PRÓXIMOS PASOS:")
    print("1. python main.py")
    print("2. Abrir: http://localhost:8000/admin/watermarks")
    print("3. Verificar: http://localhost:8000/health")
    
    return True

if __name__ == "__main__":
    main()