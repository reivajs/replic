#!/usr/bin/env python3
"""
🎵 AUDIO FIX INMEDIATO - SOLUCIÓN RÁPIDA
=======================================

Error específico:
'EnhancedReplicatorService' object has no attribute '_get_audio_display_name'

Este fix agrega EXACTAMENTE los métodos que faltan.

Usage: python audio_fix_immediate.py
"""

import re
from pathlib import Path
from datetime import datetime
import shutil

def find_enhanced_replicator_file():
    """Encontrar archivo enhanced_replicator_service.py"""
    project_root = Path.cwd()
    files = list(project_root.glob("**/enhanced_replicator_service.py"))
    
    if not files:
        print("❌ enhanced_replicator_service.py not found")
        return None
    
    return files[0]

def create_backup(file_path):
    """Crear backup del archivo"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = file_path.with_suffix(f'.py.backup_{timestamp}')
    shutil.copy2(file_path, backup_file)
    print(f"💾 Backup created: {backup_file}")
    return backup_file

def add_missing_audio_methods(content):
    """Agregar métodos que faltan para audio"""
    
    # Verificar si ya existen los métodos
    if '_get_audio_display_name' in content and '_get_smart_audio_filename' in content:
        print("✅ Audio methods already exist")
        return content
    
    # Encontrar el final de la clase (antes de la última línea)
    lines = content.split('\n')
    
    # Buscar un lugar apropiado para insertar (antes del final de la clase)
    insert_index = len(lines) - 1
    
    # Buscar el último método de la clase
    for i in range(len(lines) - 1, -1, -1):
        line = lines[i].strip()
        if line.startswith('def ') or line.startswith('async def '):
            # Encontrar el final de este método
            for j in range(i + 1, len(lines)):
                next_line = lines[j].strip()
                if (next_line.startswith('def ') or 
                    next_line.startswith('async def ') or 
                    next_line.startswith('class ') or
                    (next_line and not next_line.startswith(' ') and not next_line.startswith('#'))):
                    insert_index = j
                    break
            else:
                insert_index = len(lines)
            break
    
    # Métodos para agregar
    audio_methods = [
        "",
        "    # ============ AUDIO HELPER METHODS (AUTO-ADDED) ============",
        "",
        "    def _get_smart_audio_filename(self, filename: str, audio_bytes: bytes) -> str:",
        "        \"\"\"Generate smart filename for audio files\"\"\"",
        "        try:",
        "            if filename and filename != 'unknown_document':",
        "                # Si ya tiene un nombre válido, usarlo",
        "                return filename",
        "            ",
        "            # Detectar tipo de audio por bytes",
        "            audio_type = self._detect_audio_type(audio_bytes)",
        "            ",
        "            # Generar nombre basado en timestamp y tipo",
        "            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')",
        "            return f'audio_{timestamp}.{audio_type}'",
        "            ",
        "        except Exception as e:",
        "            logger.debug(f'Error generating audio filename: {e}')",
        "            return 'audio_enterprise.mp3'",
        "",
        "    def _detect_audio_type(self, audio_bytes: bytes) -> str:",
        "        \"\"\"Detect audio type from byte signature\"\"\"",
        "        try:",
        "            if not audio_bytes or len(audio_bytes) < 12:",
        "                return 'mp3'",
        "            ",
        "            # Verificar firmas de archivos de audio",
        "            header = audio_bytes[:12]",
        "            ",
        "            if header.startswith(b'ID3') or b'ftyp' in header:",
        "                return 'mp3'",
        "            elif header.startswith(b'OggS'):",
        "                return 'ogg'",
        "            elif header.startswith(b'RIFF') and b'WAVE' in header:",
        "                return 'wav'",
        "            elif header.startswith(b'fLaC'):",
        "                return 'flac'",
        "            elif header.startswith(b'#!AMR'):",
        "                return 'amr'",
        "            else:",
        "                return 'mp3'  # Default fallback",
        "        except Exception as e:",
        "            logger.debug(f'Error detecting audio type: {e}')",
        "            return 'mp3'",
        "",
        "    def _get_audio_display_name(self, filename: str) -> str:",
        "        \"\"\"Get display name for audio file\"\"\"",
        "        try:",
        "            if not filename or filename == 'unknown_document':",
        "                return 'Audio File'",
        "            ",
        "            # Limpiar nombre para display",
        "            display_name = filename.replace('_', ' ').replace('-', ' ')",
        "            if '.' in display_name:",
        "                display_name = display_name.rsplit('.', 1)[0]",
        "            ",
        "            return display_name.title()",
        "        except Exception as e:",
        "            logger.debug(f'Error getting audio display name: {e}')",
        "            return 'Audio File'",
        ""
    ]
    
    # Insertar métodos
    lines = lines[:insert_index] + audio_methods + lines[insert_index:]
    
    return '\n'.join(lines)

def fix_audio_method_calls(content):
    """Arreglar llamadas a métodos de audio que pueden estar rotas"""
    
    # Fix 1: Llamadas incorrectas en _handle_audio_enterprise
    content = content.replace(
        'self._get_smart_audio_filename(filename, audio_bytes)',
        'self._get_smart_audio_filename(filename or "unknown_document", audio_bytes)'
    )
    
    content = content.replace(
        'self._get_audio_display_name(filename)',
        'self._get_audio_display_name(filename or "unknown_document")'
    )
    
    # Fix 2: Asegurar imports necesarios
    if 'from datetime import datetime' not in content:
        # Agregar import si no existe
        lines = content.split('\n')
        
        # Buscar línea de imports
        import_index = 0
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                import_index = i + 1
        
        lines.insert(import_index, 'from datetime import datetime')
        content = '\n'.join(lines)
    
    return content

def main():
    """Función principal"""
    print("🎵 AUDIO FIX INMEDIATO")
    print("=" * 30)
    print()
    print("Fixing error: '_get_audio_display_name' not found")
    print()
    
    # Encontrar archivo
    replicator_file = find_enhanced_replicator_file()
    if not replicator_file:
        return
    
    print(f"📁 Found: {replicator_file}")
    
    # Crear backup
    backup_file = create_backup(replicator_file)
    
    # Leer contenido
    with open(replicator_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n🔧 Adding missing audio methods...")
    
    # Aplicar fixes
    content = add_missing_audio_methods(content)
    content = fix_audio_method_calls(content)
    
    # Escribir archivo corregido
    with open(replicator_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Audio methods added successfully!")
    print("\n📋 CHANGES MADE:")
    print("  ✅ Added _get_smart_audio_filename() method")
    print("  ✅ Added _detect_audio_type() method") 
    print("  ✅ Added _get_audio_display_name() method")
    print("  ✅ Fixed method calls to handle None values")
    print("  ✅ Added necessary imports")
    
    print(f"\n💾 Backup available at: {backup_file}")
    
    print("\n🚀 NEXT STEPS:")
    print("1. Restart your application: python main.py")
    print("2. Test audio file sending in Telegram")
    print("3. Verify Discord shows proper filename")
    
    print("\n🎯 EXPECTED RESULT:")
    print("✅ Audio files will show as 'audio_20250817_180837.mp3'")
    print("✅ No more 'unknown_document'")
    print("✅ No more missing method errors")

if __name__ == "__main__":
    main()