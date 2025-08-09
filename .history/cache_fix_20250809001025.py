#!/usr/bin/env python3
"""
🔧 FIX DEL ERROR DE CACHE JSON
=============================
Corregir el error: "Expecting value: line 1 column 3498 (char 3497)"
"""

import os
import json
from pathlib import Path
import shutil

def fix_cache_files():
    """Arreglar archivos de cache corruptos"""
    print("🔧 Arreglando archivos de cache corruptos...")
    
    # Directorios donde pueden estar los archivos de cache
    cache_dirs = [
        "cache",
        "temp",
        "processed_files", 
        "watermark_data/cache",
        ".cache",
        "__pycache__"
    ]
    
    # Patrones de archivos de cache problemáticos
    cache_files = [
        "*.json",
        "cache_index.json",
        "file_cache.json",
        "watermark_cache.json",
        "processed_cache.json"
    ]
    
    fixed_count = 0
    
    for cache_dir in cache_dirs:
        cache_path = Path(cache_dir)
        if not cache_path.exists():
            continue
            
        print(f"   📂 Revisando directorio: {cache_dir}")
        
        # Buscar archivos JSON potencialmente corruptos
        for json_file in cache_path.rglob("*.json"):
            try:
                # Intentar leer el archivo JSON
                with open(json_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    
                    if not content:
                        # Archivo vacío
                        print(f"   🗑️ Eliminando archivo vacío: {json_file}")
                        json_file.unlink()
                        fixed_count += 1
                        continue
                    
                    # Intentar parsear JSON
                    json.loads(content)
                    
            except json.JSONDecodeError as e:
                print(f"   ❌ JSON corrupto encontrado: {json_file}")
                print(f"      Error: {e}")
                
                # Hacer backup del archivo corrupto
                backup_file = json_file.with_suffix('.json.backup')
                shutil.copy2(json_file, backup_file)
                print(f"   💾 Backup creado: {backup_file}")
                
                # Crear nuevo archivo JSON válido
                if "cache_index" in json_file.name:
                    # Cache index específico
                    new_content = {
                        "version": "1.0",
                        "created": "2025-08-08",
                        "files": {},
                        "metadata": {}
                    }
                elif "watermark" in json_file.name:
                    # Watermark cache
                    new_content = {
                        "processed_images": {},
                        "settings": {},
                        "last_updated": "2025-08-08"
                    }
                else:
                    # Cache genérico
                    new_content = {
                        "cache": {},
                        "timestamp": "2025-08-08",
                        "version": "1.0"
                    }
                
                # Escribir nuevo archivo JSON válido
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(new_content, f, indent=2)
                
                print(f"   ✅ Archivo reparado: {json_file}")
                fixed_count += 1
                
            except Exception as e:
                print(f"   ⚠️ Error procesando {json_file}: {e}")
    
    return fixed_count

def create_cache_directories():
    """Crear directorios de cache necesarios"""
    print("📁 Creando directorios de cache...")
    
    cache_dirs = [
        "cache",
        "temp",
        "processed_files",
        "watermark_data/cache",
        "watermark_data/temp",
        "database",
        "files",
        "logs"
    ]
    
    for cache_dir in cache_dirs:
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        
        # Crear archivo .gitkeep para mantener el directorio
        gitkeep = Path(cache_dir) / ".gitkeep"
        gitkeep.touch()
    
    print("   ✅ Directorios de cache creados")

def create_improved_file_processor():
    """Crear versión mejorada del file processor que evita el error"""
    print("🔧 Creando file processor mejorado...")
    
    file_processor_code = '''"""
File Processor Mejorado con Manejo de Cache Robusto
==================================================
Evita errores de JSON corrupto con validación y recuperación automática
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class SafeFileProcessor:
    """File processor con manejo seguro de cache"""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_file = self.cache_dir / "cache_index.json"
        self._cache = {}
        self._load_cache()
    
    def _load_cache(self):
        """Cargar cache de forma segura con recuperación automática"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    
                    if not content:
                        logger.warning("Cache file is empty, initializing new cache")
                        self._init_cache()
                        return
                    
                    # Intentar parsear JSON
                    try:
                        self._cache = json.loads(content)
                        logger.info("Cache loaded successfully")
                    except json.JSONDecodeError as e:
                        logger.warning(f"Cache JSON corrupted: {e}")
                        self._recover_cache(content)
                        
            else:
                logger.info("No cache file found, initializing new cache")
                self._init_cache()
                
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
            self._init_cache()
    
    def _recover_cache(self, corrupted_content: str):
        """Intentar recuperar datos del cache corrupto"""
        try:
            # Crear backup del archivo corrupto
            backup_file = self.cache_file.with_suffix('.json.corrupted')
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(corrupted_content)
            logger.info(f"Corrupted cache backed up to: {backup_file}")
            
            # Intentar extraer datos válidos del JSON corrupto
            # Buscar el último objeto JSON válido
            for i in range(len(corrupted_content) - 1, 0, -1):
                try:
                    partial_content = corrupted_content[:i]
                    if partial_content.endswith('}'):
                        recovered_data = json.loads(partial_content)
                        self._cache = recovered_data
                        logger.info("Successfully recovered partial cache data")
                        self._save_cache()
                        return
                except:
                    continue
            
            # Si no se puede recuperar, inicializar cache nuevo
            logger.warning("Could not recover cache data, initializing fresh cache")
            self._init_cache()
            
        except Exception as e:
            logger.error(f"Cache recovery failed: {e}")
            self._init_cache()
    
    def _init_cache(self):
        """Inicializar cache nuevo"""
        self._cache = {
            "version": "1.0",
            "created": datetime.now().isoformat(),
            "files": {},
            "metadata": {},
            "stats": {
                "total_files": 0,
                "last_updated": datetime.now().isoformat()
            }
        }
        self._save_cache()
        logger.info("New cache initialized")
    
    def _save_cache(self):
        """Guardar cache de forma segura"""
        try:
            # Actualizar timestamp
            self._cache["metadata"]["last_updated"] = datetime.now().isoformat()