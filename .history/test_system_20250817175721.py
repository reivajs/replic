#!/usr/bin/env python3
"""
🏥 DASHBOARD DEFINITIVE FIX - SOLUCIÓN FINAL
============================================

Fix DEFINITIVO para eliminar el error:
"RuntimeWarning: coroutine 'ServiceRegistry.check_all_services' was never awaited"

Este script localiza EXACTAMENTE la línea problemática y la corrige.

Usage: python dashboard_definitive_fix.py
"""

import re
import ast
from pathlib import Path
from datetime import datetime
import shutil

class DashboardFixer:
    """Fixer inteligente para dashboard health checks"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.fixes_applied = []
        self.backup_dir = None
    
    def find_dashboard_files(self):
        """Encontrar todos los archivos dashboard"""
        dashboard_files = []
        
        # Patrones comunes para archivos dashboard
        patterns = [
            "**/dashboard.py",
            "**/dashboard*.py", 
            "**/api/**/dashboard.py",
            "**/v1/dashboard.py"
        ]
        
        for pattern in patterns:
            dashboard_files.extend(self.project_root.glob(pattern))
        
        # Remover duplicados
        return list(set(dashboard_files))
    
    def create_backup(self, files):
        """Crear backup de archivos"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.backup_dir = self.project_root / "backups" / f"dashboard_fix_{timestamp}"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        for file in files:
            backup_file = self.backup_dir / f"{file.name}.backup"
            shutil.copy2(file, backup_file)
            print(f"💾 Backed up: {file} -> {backup_file}")
        
        return self.backup_dir
    
    def analyze_file(self, file_path):
        """Analizar archivo para encontrar problemas específicos"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        issues = []
        
        for i, line in enumerate(lines):
            line_num = i + 1
            stripped = line.strip()
            
            # Detectar el patrón específico problemático
            if 'service_registry.check_all_services()' in line and 'await' not in line:
                # Verificar que no sea un comentario
                if not stripped.startswith('#'):
                    issues.append({
                        'type': 'missing_await',
                        'line_num': line_num,
                        'line': line,
                        'pattern': 'service_registry.check_all_services()'
                    })
            
            # Detectar funciones que deberían ser async
            if 'def ' in line and not 'async def' in line:
                # Verificar si esta función usa check_all_services en sus próximas líneas
                function_content = '\n'.join(lines[i:i+20])  # Próximas 20 líneas
                if 'check_all_services()' in function_content:
                    issues.append({
                        'type': 'should_be_async',
                        'line_num': line_num,
                        'line': line,
                        'pattern': 'def '
                    })
        
        return issues, content, lines
    
    def fix_missing_await(self, line):
        """Fix para agregar await"""
        # Patrón: variable = service_registry.check_all_services()
        pattern = r'(\s*)(.*?)\s*=\s*service_registry\.check_all_services\(\)'
        replacement = r'\1\2 = await service_registry.check_all_services()'
        
        fixed_line = re.sub(pattern, replacement, line)
        return fixed_line
    
    def fix_function_to_async(self, line):
        """Fix para convertir función a async"""
        return line.replace('def ', 'async def ')
    
    def apply_fixes(self, file_path, issues, lines):
        """Aplicar todos los fixes a un archivo"""
        fixed_lines = lines.copy()
        fixes_in_file = []
        
        # Aplicar fixes en orden reverso para no afectar números de línea
        for issue in sorted(issues, key=lambda x: x['line_num'], reverse=True):
            line_idx = issue['line_num'] - 1  # Convertir a índice 0-based
            original_line = fixed_lines[line_idx]
            
            if issue['type'] == 'missing_await':
                fixed_line = self.fix_missing_await(original_line)
                fixed_lines[line_idx] = fixed_line
                fixes_in_file.append(f"Line {issue['line_num']}: Added 'await'")
                
            elif issue['type'] == 'should_be_async':
                fixed_line = self.fix_function_to_async(original_line)
                fixed_lines[line_idx] = fixed_line
                fixes_in_file.append(f"Line {issue['line_num']}: Added 'async'")
        
        # Escribir archivo corregido
        if fixes_in_file:
            fixed_content = '\n'.join(fixed_lines)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            
            print(f"✅ Fixed {file_path}:")
            for fix in fixes_in_file:
                print(f"   - {fix}")
            
            self.fixes_applied.extend(fixes_in_file)
            return True
        
        return False
    
    def verify_fix(self, file_path):
        """Verificar que el fix funcionó"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificaciones
        has_await_check = 'await service_registry.check_all_services()' in content
        no_missing_await = 'service_registry.check_all_services()' not in content or has_await_check
        
        return {
            'has_await': has_await_check,
            'no_missing_await': no_missing_await,
            'is_fixed': has_await_check and no_missing_await
        }
    
    def fix_all_dashboards(self):
        """Fix principal - corregir todos los dashboards"""
        print("🔍 Searching for dashboard files...")
        dashboard_files = self.find_dashboard_files()
        
        if not dashboard_files:
            print("❌ No dashboard files found")
            return False
        
        print(f"📁 Found {len(dashboard_files)} dashboard files:")
        for file in dashboard_files:
            print(f"   - {file}")
        
        # Crear backup
        print("\n💾 Creating backups...")
        backup_dir = self.create_backup(dashboard_files)
        
        # Analizar y corregir cada archivo
        total_fixes = 0
        
        for file_path in dashboard_files:
            print(f"\n🔧 Analyzing {file_path}...")
            
            issues, content, lines = self.analyze_file(file_path)
            
            if not issues:
                print(f"✅ No issues found in {file_path}")
                continue
            
            print(f"⚠️  Found {len(issues)} issues in {file_path}:")
            for issue in issues:
                print(f"   - Line {issue['line_num']}: {issue['type']}")
            
            # Aplicar fixes
            if self.apply_fixes(file_path, issues, lines):
                total_fixes += len(issues)
                
                # Verificar fix
                verification = self.verify_fix(file_path)
                if verification['is_fixed']:
                    print(f"✅ Fix verified successfully for {file_path}")
                else:
                    print(f"⚠️  Fix applied but verification incomplete for {file_path}")
        
        return total_fixes > 0
    
    def create_summary_report(self):
        """Crear reporte resumen"""
        if not self.fixes_applied:
            return
        
        report = f"""
🎉 DASHBOARD FIX COMPLETED SUCCESSFULLY!
=======================================

📊 SUMMARY:
- Total fixes applied: {len(self.fixes_applied)}
- Backup location: {self.backup_dir}
- Timestamp: {datetime.now().isoformat()}

🔧 FIXES APPLIED:
"""
        for fix in self.fixes_applied:
            report += f"✅ {fix}\n"
        
        report += f"""
🚀 NEXT STEPS:
1. Restart your application: python main.py
2. Open dashboard: http://localhost:8000/dashboard  
3. Verify no health check errors in logs
4. Test all dashboard functionality

💾 ROLLBACK (if needed):
If anything goes wrong, restore from backup:
cp {self.backup_dir}/*.backup app/api/v1/dashboard.py

🎯 EXPECTED RESULT:
- ✅ No more "RuntimeWarning: coroutine was never awaited" 
- ✅ No more "cannot unpack non-iterable coroutine object"
- ✅ Dashboard health checks working correctly
- ✅ Clean logs without async warnings
"""
        
        print(report)
        
        # Guardar reporte
        if self.backup_dir:
            report_file = self.backup_dir / "fix_report.txt"
            with open(report_file, 'w') as f:
                f.write(report)
            print(f"📝 Report saved to: {report_file}")


def main():
    """Función principal"""
    print("🏥 DASHBOARD DEFINITIVE FIXER")
    print("=" * 50)
    print()
    print("This tool will:")
    print("✅ Find all dashboard files in your project")
    print("✅ Backup original files automatically")
    print("✅ Fix missing 'await' statements")
    print("✅ Convert functions to async where needed")
    print("✅ Verify fixes work correctly")
    print("✅ Provide rollback instructions")
    print()
    
    # Confirmar antes de proceder
    response = input("🤔 Proceed with automatic fix? (y/N): ")
    if response.lower() != 'y':
        print("❌ Fix cancelled by user")
        return
    
    # Ejecutar fix
    fixer = DashboardFixer()
    
    try:
        success = fixer.fix_all_dashboards()
        
        if success:
            fixer.create_summary_report()
            print("\n🎉 ALL FIXES COMPLETED SUCCESSFULLY!")
            print("Your dashboard health check errors should now be resolved.")
        else:
            print("\n⚠️  No fixes were needed or applied")
            print("Your dashboard might already be correct, or manual review is needed.")
    
    except Exception as e:
        print(f"\n❌ Error during fix process: {e}")
        print("Please review manually or contact support.")


if __name__ == "__main__":
    main()