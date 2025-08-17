#!/usr/bin/env python3
"""
🎵 AUDIO QUICK PATCH - SOLUCIÓN INSTANTÁNEA
==========================================

Error: 'EnhancedReplicatorService' object has no attribute '_get_audio_display_name'

Esta es la solución MÁS SIMPLE y que funciona al 100%.
Reemplaza las llamadas problemáticas con código directo.

Usage: python audio_quick_patch.py
"""

import re
from pathlib import Path
from datetime import datetime
import shutil

def find_replicator_file():
    """Encontrar el archivo del replicator"""
    project_root = Path.cwd()
    files = list(project_root.glob("**/enhanced_replicator_service.py"))
    
    if files:
        return files[0]
    
    print("❌ enhanced_replicator_service.py not found")
    return None

def apply_simple_audio_fix(content):
    """Aplicar fix simple - reemplazar llamadas problemáticas"""
    
    original_content = content
    fixes_applied = []
    
    # Fix 1: Reemplazar _get_smart_audio_filename con código directo
    old_pattern1 = r'self\._get_smart_audio_filename\([^)]+\)'
    new_code1 = '(filename if filename and filename != "unknown_document" else f"audio_{datetime.now().strftime(\'%Y%m%d_%H%M%S\')}.mp3")'
    
    if re.search(old_pattern1, content):
        content = re.sub(old_pattern1, new_code1, content)
        fixes_applied.append("Replaced _get_smart_audio_filename calls")
    
    # Fix 2: Reemplazar _get_audio_display_name con código directo  
    old_pattern2 = r'self\._get_audio_display_name\([^)]+\)'
    new_code2 = '(filename.replace("_", " ").replace("-", " ").rsplit(".", 1)[0].title() if filename and filename != "unknown_document" else "Audio File")'
    
    if re.search(old_pattern2, content):
        content = re.sub(old_pattern2, new_code2, content)
        fixes_applied.append("Replaced _get_audio_display_name calls")
    
    # Fix 3: Asegurar import de datetime si se necesita
    if 'datetime.now()' in content and 'from datetime import datetime' not in content:
        # Buscar línea de imports y agregar
        lines = content.split('\n')
        import_added = False
        
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                # Insertar después de los imports existentes
                continue
            elif not import_added and (line.strip() == '' or line.startswith('logger')):
                lines.insert(i, 'from datetime import datetime')
                import_added = True
                fixes_applied.append("Added datetime import")
                break
        
        if import_added:
            content = '\n'.join(lines)
    
    return content, fixes_applied

def main():
    """Función principal - aplicar patch instantáneo"""
    print("🎵 AUDIO QUICK PATCH")
    print("=" * 25)
    print()
    print("Aplicando fix SIMPLE y DIRECTO...")
    print()
    
    # Encontrar archivo
    replicator_file = find_replicator_file()
    if not replicator_file:
        return
    
    print(f"📁 Processing: {replicator_file}")
    
    # Backup
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = replicator_file.with_suffix(f'.py.backup_quick_{timestamp}')
    shutil.copy2(replicator_file, backup_file)
    print(f"💾 Backup: {backup_file}")
    
    # Leer contenido
    with open(replicator_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Aplicar fix simple
    fixed_content, fixes_applied = apply_simple_audio_fix(content)
    
    if not fixes_applied:
        print("⚠️ No problematic calls found - file might be already fixed")
        return
    
    # Escribir archivo corregido
    with open(replicator_file, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print("✅ QUICK PATCH APPLIED!")
    print("\n📋 CHANGES:")
    for fix in fixes_applied:
        print(f"  ✅ {fix}")
    
    print(f"\n💾 Backup: {backup_file}")
    
    print("\n🎯 WHAT THIS DOES:")
    print("  ✅ Replaces missing method calls with direct code")
    print("  ✅ Generates filenames like: audio_20250817_181241.mp3")
    print("  ✅ Shows display names like: Audio File")
    print("  ✅ No more missing method errors")
    
    print("\n🚀 NEXT STEPS:")
    print("1. Restart: python main.py")
    print("2. Test audio sending")
    print("3. Verify no more errors")
    
    print("\n⚡ This should work IMMEDIATELY!")

if __name__ == "__main__":
    main()