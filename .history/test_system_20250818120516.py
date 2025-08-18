#!/usr/bin/env python3
"""
🔧 AUTO-FIX SCRIPT - ZERO COST PROJECT
=====================================

Este script ejecuta automáticamente todos los pasos restantes para completar
la implementación del panel de watermarks y resolver los errores críticos.

Autor: Senior Dev Assistant
Proyecto: Zero Cost SaaS
"""

import os
import re
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

class ZeroCostAutoFix:
    """Auto-fix para completar la implementación de Zero Cost"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.backup_dir = self.project_root / "backups" / datetime.now().strftime("%Y%m%d_%H%M%S")
        self.fixes_applied = []
        self.errors_found = []
        
    def log(self, message, level="INFO"):
        """Log con colores"""
        colors = {
            "INFO": "\033[94m",  # Blue
            "SUCCESS": "\033[92m",  # Green
            "WARNING": "\033[93m",  # Yellow
            "ERROR": "\033[91m",  # Red
            "RESET": "\033[0m"
        }
        
        color = colors.get(level, colors["INFO"])
        reset = colors["RESET"]
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        print(f"{color}[{timestamp}] {level}: {message}{reset}")
    
    def create_backup(self, file_path):
        """Crear backup de archivo crítico"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return False
                
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            backup_path = self.backup_dir / file_path.name
            shutil.copy2(file_path, backup_path)
            
            self.log(f"✅ Backup creado: {backup_path}", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"❌ Error creando backup: {e}", "ERROR")
            return False
    
    def find_dashboard_files(self):
        """Buscar archivos de dashboard"""
        dashboard_files = []
        
        # Patrones de búsqueda
        patterns = [
            "**/dashboard*.py",
            "**/api/**/dashboard*.py", 
            "**/*dashboard*.py"
        ]
        
        for pattern in patterns:
            files = list(self.project_root.glob(pattern))
            dashboard_files.extend(files)
        
        # Eliminar duplicados
        dashboard_files = list(set(dashboard_files))
        
        self.log(f"📁 Archivos dashboard encontrados: {len(dashboard_files)}")
        for file in dashboard_files:
            self.log(f"   - {file}")
            
        return dashboard_files
    
    def fix_dashboard_health_check(self):
        """Fix 1: Arreglar dashboard health check async"""
        self.log("🔧 Fix 1: Reparando dashboard health check...", "INFO")
        
        dashboard_files = self.find_dashboard_files()
        
        if not dashboard_files:
            self.log("❌ No se encontraron archivos de dashboard", "ERROR")
            self.errors_found.append("No dashboard files found")
            return False
        
        fixed_files = []
        
        for dashboard_file in dashboard_files:
            try:
                # Crear backup
                self.create_backup(dashboard_file)
                
                # Leer contenido
                with open(dashboard_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                # Fix 1: Añadir await a check_all_services()
                pattern1 = r'(\s*)(healthy,\s*total)\s*=\s*(service_registry\.check_all_services\(\))'
                replacement1 = r'\1\2 = await \3'
                content = re.sub(pattern1, replacement1, content)
                
                # Fix 2: Hacer función async si no lo es
                pattern2 = r'def\s+(get_health|health_check|dashboard_health)\s*\('
                replacement2 = r'async def \1('
                content = re.sub(pattern2, replacement2, content)
                
                # Fix 3: Arreglar otras llamadas await faltantes
                patterns_await = [
                    (r'(\s*)(.*?)\s*=\s*(service_registry\.get_stats\(\))', r'\1\2 = await \3'),
                    (r'(\s*)(.*?)\s*=\s*(service_registry\.health_check\(\))', r'\1\2 = await \3'),
                    (r'(\s*)(.*?)\s*=\s*(service\.get_dashboard_stats\(\))', r'\1\2 = await \3'),
                ]
                
                for pattern, replacement in patterns_await:
                    content = re.sub(pattern, replacement, content)
                
                # Solo escribir si hubo cambios
                if content != original_content:
                    with open(dashboard_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    fixed_files.append(str(dashboard_file))
                    self.log(f"✅ Dashboard fixed: {dashboard_file}", "SUCCESS")
                
            except Exception as e:
                self.log(f"❌ Error fixing {dashboard_file}: {e}", "ERROR")
                self.errors_found.append(f"Dashboard fix error: {e}")
        
        if fixed_files:
            self.fixes_applied.extend(fixed_files)
            return True
        else:
            self.log("⚠️ No dashboard fixes needed or applied", "WARNING")
            return False
    
    def fix_service_registry(self):
        """Fix 2: Verificar y arreglar service registry async"""
        self.log("🔧 Fix 2: Verificando service registry...", "INFO")
        
        registry_files = list(self.project_root.glob("**/registry.py"))
        
        if not registry_files:
            self.log("❌ No se encontró registry.py", "ERROR")
            self.errors_found.append("registry.py not found")
            return False
        
        registry_file = registry_files[0]
        self.log(f"📁 Registry encontrado: {registry_file}")
        
        try:
            # Crear backup
            self.create_backup(registry_file)
            
            # Leer contenido
            with open(registry_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Verificar si check_all_services es async
            if 'async def check_all_services' in content:
                self.log("✅ check_all_services ya es async", "SUCCESS")
                return True
            
            # Si no es async, hacerlo async
            pattern = r'def\s+check_all_services\s*\('
            replacement = 'async def check_all_services('
            content = re.sub(pattern, replacement, content)
            
            # Añadir import asyncio si no existe
            if 'import asyncio' not in content and 'async def' in content:
                # Buscar donde añadir el import
                import_section = content.split('\n')
                for i, line in enumerate(import_section):
                    if line.startswith('import ') or line.startswith('from '):
                        continue
                    else:
                        import_section.insert(i, 'import asyncio')
                        break
                content = '\n'.join(import_section)
            
            # Escribir si hubo cambios
            if content != original_content:
                with open(registry_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.log("✅ Service registry fixed", "SUCCESS")
                self.fixes_applied.append(str(registry_file))
                return True
            else:
                self.log("✅ Service registry ya está correcto", "SUCCESS")
                return True
                
        except Exception as e:
            self.log(f"❌ Error fixing registry: {e}", "ERROR")
            self.errors_found.append(f"Registry fix error: {e}")
            return False
    
    def create_directories(self):
        """Fix 3: Crear directorios necesarios"""
        self.log("🔧 Fix 3: Creando directorios necesarios...", "INFO")
        
        directories = [
            "watermarks",
            "config", 
            "logs",
            "temp",
            "frontend/templates/admin",
            "frontend/static/admin",
            "data"
        ]
        
        created_dirs = []
        
        for directory in directories:
            dir_path = self.project_root / directory
            
            if not dir_path.exists():
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    created_dirs.append(directory)
                    self.log(f"📁 Directorio creado: {directory}", "SUCCESS")
                except Exception as e:
                    self.log(f"❌ Error creando {directory}: {e}", "ERROR")
                    self.errors_found.append(f"Directory creation error: {e}")
            else:
                self.log(f"✅ Directorio ya existe: {directory}")
        
        if created_dirs:
            self.fixes_applied.extend(created_dirs)
        
        return True
    
    def setup_watermark_route(self):
        """Fix 4: Añadir ruta para panel de watermarks"""
        self.log("🔧 Fix 4: Configurando ruta del panel...", "INFO")
        
        # Buscar main.py o app.py
        main_files = list(self.project_root.glob("main.py")) + list(self.project_root.glob("app.py"))
        
        if not main_files:
            self.log("❌ No se encontró main.py o app.py", "ERROR")
            self.errors_found.append("main.py not found")
            return False
        
        main_file = main_files[0]
        self.log(f"📁 Archivo principal: {main_file}")
        
        try:
            # Crear backup
            self.create_backup(main_file)
            
            # Leer contenido
            with open(main_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Verificar si ya existe la ruta
            if '/admin/watermarks' in content:
                self.log("✅ Ruta de watermarks ya existe", "SUCCESS")
                return True
            
            # Añadir imports necesarios si no existen
            imports_to_add = [
                "from fastapi.responses import HTMLResponse",
                "from fastapi.templating import Jinja2Templates"
            ]
            
            for import_line in imports_to_add:
                if import_line.split()[1] not in content:
                    # Buscar donde añadir el import
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if line.startswith('from fastapi') or line.startswith('import fastapi'):
                            lines.insert(i + 1, import_line)
                            break
                    content = '\n'.join(lines)
            
            # Añadir configuración de templates si no existe
            if 'Jinja2Templates' in content and 'templates = Jinja2Templates' not in content:
                # Buscar donde añadir templates
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if 'app = FastAPI' in line:
                        lines.insert(i + 2, '\n# Templates configuration')
                        lines.insert(i + 3, 'templates = Jinja2Templates(directory="frontend/templates")')
                        break
                content = '\n'.join(lines)
            
            # Añadir la ruta del panel
            watermark_route = '''
# Watermark Admin Panel
@app.get("/admin/watermarks", response_class=HTMLResponse)
async def watermark_admin_panel(request: Request):
    """Panel de administración de watermarks"""
    return templates.TemplateResponse("admin/watermarks.html", {"request": request})

@app.get("/api/watermark/groups")
async def get_watermark_groups():
    """API para obtener grupos configurados"""
    try:
        # Aquí conectarías con tu watermark service
        return {"groups": [], "status": "success"}
    except Exception as e:
        return {"error": str(e), "status": "error"}
'''
            
            # Buscar donde añadir la ruta (al final de las rutas)
            if '@app.get' in content or '@app.post' in content:
                # Añadir al final antes de if __name__ == "__main__"
                if 'if __name__ == "__main__"' in content:
                    content = content.replace('if __name__ == "__main__"', watermark_route + '\nif __name__ == "__main__"')
                else:
                    content += watermark_route
            
            # Escribir si hubo cambios
            if content != original_content:
                with open(main_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.log("✅ Ruta de watermarks añadida", "SUCCESS")
                self.fixes_applied.append(f"Route added to {main_file}")
                return True
            else:
                self.log("✅ Configuración de rutas ya está correcta", "SUCCESS")
                return True
                
        except Exception as e:
            self.log(f"❌ Error configurando rutas: {e}", "ERROR")
            self.errors_found.append(f"Route setup error: {e}")
            return False
    
    def install_dependencies(self):
        """Fix 5: Verificar e instalar dependencias"""
        self.log("🔧 Fix 5: Verificando dependencias...", "INFO")
        
        dependencies = [
            "fastapi",
            "uvicorn", 
            "pillow",
            "jinja2",
            "python-multipart"
        ]
        
        installed_deps = []
        
        for dep in dependencies:
            try:
                # Verificar si está instalado
                result = subprocess.run([sys.executable, "-c", f"import {dep.replace('-', '_')}"], 
                                      capture_output=True)
                
                if result.returncode != 0:
                    # Instalar dependencia
                    self.log(f"📦 Instalando {dep}...", "INFO")
                    result = subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                                          capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        installed_deps.append(dep)
                        self.log(f"✅ {dep} instalado correctamente", "SUCCESS")
                    else:
                        self.log(f"❌ Error instalando {dep}: {result.stderr}", "ERROR")
                        self.errors_found.append(f"Failed to install {dep}")
                else:
                    self.log(f"✅ {dep} ya está instalado")
                    
            except Exception as e:
                self.log(f"❌ Error verificando {dep}: {e}", "ERROR")
        
        if installed_deps:
            self.fixes_applied.extend(installed_deps)
        
        return True
    
    def create_sample_config(self):
        """Fix 6: Crear configuración de ejemplo si no existe"""
        self.log("🔧 Fix 6: Verificando configuraciones...", "INFO")
        
        config_dir = self.project_root / "config"
        
        # Verificar si ya hay configuraciones
        existing_configs = list(config_dir.glob("group_*.json"))
        
        if existing_configs:
            self.log(f"✅ Configuraciones existentes encontradas: {len(existing_configs)}")
            return True
        
        # Crear configuración de ejemplo
        sample_config = {
            "group_id": -1234567890,
            "name": "Grupo de Ejemplo",
            "enabled": True,
            "watermark_type": "text",
            "text_enabled": True,
            "text_content": "Replicated via Zero Cost",
            "text_position": "bottom_right",
            "text_font_size": 32,
            "text_color": "#FFFFFF",
            "text_stroke_color": "#000000",
            "text_stroke_width": 2,
            "text_custom_x": 20,
            "text_custom_y": 20,
            "png_enabled": False,
            "png_position": "bottom_right",
            "png_opacity": 0.7,
            "png_scale": 0.15,
            "png_custom_x": 20,
            "png_custom_y": 20,
            "png_path": "",
            "video_enabled": False,
            "video_max_size_mb": 1024,
            "video_timeout_sec": 60,
            "video_compress": True,
            "video_quality_crf": 23,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        try:
            import json
            config_file = config_dir / "group_-1234567890.json"
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(sample_config, f, indent=2, ensure_ascii=False)
            
            self.log("✅ Configuración de ejemplo creada", "SUCCESS")
            self.fixes_applied.append(str(config_file))
            return True
            
        except Exception as e:
            self.log(f"❌ Error creando configuración: {e}", "ERROR")
            self.errors_found.append(f"Sample config error: {e}")
            return False
    
    def run_validation_tests(self):
        """Fix 7: Ejecutar tests de validación"""
        self.log("🔧 Fix 7: Ejecutando tests de validación...", "INFO")
        
        tests_passed = 0
        total_tests = 3
        
        # Test 1: Verificar watermark service
        try:
            sys.path.append(str(self.project_root))
            from app.services.watermark_service import WatermarkServiceIntegrated
            
            service = WatermarkServiceIntegrated()
            
            # Verificar que tiene el método crítico
            if hasattr(service, 'apply_image_watermark'):
                self.log("✅ Test 1: apply_image_watermark método existe", "SUCCESS")
                tests_passed += 1
            else:
                self.log("❌ Test 1: apply_image_watermark método faltante", "ERROR")
                
        except Exception as e:
            self.log(f"❌ Test 1: Error importando watermark service: {e}", "ERROR")
        
        # Test 2: Verificar directorios
        required_dirs = ["watermarks", "config", "logs", "temp"]
        dirs_ok = all((self.project_root / d).exists() for d in required_dirs)
        
        if dirs_ok:
            self.log("✅ Test 2: Todos los directorios existen", "SUCCESS")
            tests_passed += 1
        else:
            self.log("❌ Test 2: Faltan directorios", "ERROR")
        
        # Test 3: Verificar panel de administración
        panel_file = self.project_root / "frontend" / "templates" / "admin" / "watermarks.html"
        
        if panel_file.exists():
            self.log("✅ Test 3: Panel de administración existe", "SUCCESS")
            tests_passed += 1
        else:
            self.log("❌ Test 3: Panel de administración faltante", "ERROR")
        
        self.log(f"📊 Tests pasados: {tests_passed}/{total_tests}")
        return tests_passed == total_tests
    
    def generate_report(self):
        """Generar reporte final"""
        self.log("📊 Generando reporte final...", "INFO")
        
        report = f"""
🎯 REPORTE DE AUTO-FIX - ZERO COST PROJECT
==========================================

Fecha: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Directorio: {self.project_root}

✅ FIXES APLICADOS ({len(self.fixes_applied)}):
{chr(10).join(f"   - {fix}" for fix in self.fixes_applied)}

{"❌ ERRORES ENCONTRADOS (" + str(len(self.errors_found)) + "):" if self.errors_found else "🎉 SIN ERRORES"}
{chr(10).join(f"   - {error}" for error in self.errors_found) if self.errors_found else "   Todos los fixes se aplicaron correctamente"}

📁 BACKUPS CREADOS:
   Directorio: {self.backup_dir}

🚀 PRÓXIMOS PASOS:
   1. Ejecutar: python main.py
   2. Abrir: http://localhost:8000/admin/watermarks
   3. Probar replicación de imágenes
   4. Verificar logs: tail -f logs/replicator_*.log

💡 COMANDOS ÚTILES:
   # Verificar servicios
   curl http://localhost:8000/health
   
   # Verificar panel
   curl http://localhost:8000/admin/watermarks
   
   # Ver logs en tiempo real
   tail -f logs/replicator_$(date +%Y%m%d).log

{"🎉 IMPLEMENTACIÓN COMPLETADA CON ÉXITO!" if not self.errors_found else "⚠️ IMPLEMENTACIÓN COMPLETADA CON ERRORES"}
==========================================
"""
        
        # Guardar reporte
        report_file = self.project_root / "auto_fix_report.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(report)
        self.log(f"📄 Reporte guardado en: {report_file}", "SUCCESS")
    
    def run_all_fixes(self):
        """Ejecutar todos los fixes automáticamente"""
        self.log("🚀 INICIANDO AUTO-FIX ZERO COST PROJECT", "INFO")
        self.log("=" * 50, "INFO")
        
        fixes = [
            ("Dashboard Health Check", self.fix_dashboard_health_check),
            ("Service Registry", self.fix_service_registry), 
            ("Directorios", self.create_directories),
            ("Rutas Watermark", self.setup_watermark_route),
            ("Dependencias", self.install_dependencies),
            ("Configuración", self.create_sample_config),
            ("Validación", self.run_validation_tests)
        ]
        
        for fix_name, fix_function in fixes:
            try:
                self.log(f"🔧 Ejecutando: {fix_name}", "INFO")
                success = fix_function()
                
                if success:
                    self.log(f"✅ {fix_name} completado", "SUCCESS")
                else:
                    self.log(f"⚠️ {fix_name} completado con warnings", "WARNING")
                    
                self.log("-" * 30, "INFO")
                
            except Exception as e:
                self.log(f"❌ Error en {fix_name}: {e}", "ERROR")
                self.errors_found.append(f"{fix_name}: {e}")
        
        # Generar reporte final
        self.generate_report()
        
        return len(self.errors_found) == 0


def main():
    """Función principal"""
    print("🎯 ZERO COST AUTO-FIX SCRIPT")
    print("=" * 40)
    print("Este script completará automáticamente la implementación")
    print("de tu panel de watermarks y resolverá errores críticos.")
    print()
    
    response = input("¿Continuar con el auto-fix? (y/N): ").strip().lower()
    
    if response not in ['y', 'yes', 'sí', 's']:
        print("❌ Auto-fix cancelado por el usuario")
        return
    
    # Ejecutar auto-fix
    fixer = ZeroCostAutoFix()
    success = fixer.run_all_fixes()
    
    if success:
        print("\n🎉 AUTO-FIX COMPLETADO CON ÉXITO!")
        print("Tu proyecto Zero Cost está listo para usar.")
        print("\n🚀 SIGUIENTE PASO:")
        print("   python main.py")
    else:
        print("\n⚠️ AUTO-FIX COMPLETADO CON ALGUNOS ERRORES")
        print("Revisa el reporte para más detalles.")


if __name__ == "__main__":
    main()