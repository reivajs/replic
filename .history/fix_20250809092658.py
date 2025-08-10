#!/usr/bin/env python3
"""
🚀 SCRIPT DE APLICACIÓN DEL FIX DE CACHE
=========================================
Aplica la solución al error de cache JSON de manera segura
Ejecutar con: python apply_cache_fix.py
"""

import os
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CacheFixer:
    """Aplicador del fix de cache con backup y rollback"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.backup_dir = self.project_root / "backups" / datetime.now().strftime("%Y%m%d_%H%M%S")
        self.file_processor_path = self.project_root / "app" / "services" / "file_processor.py"
        self.cache_dirs = [
            self.project_root / "cache",
            self.project_root / "temp",
            self.project_root / "processed_files",
            self.project_root / "watermark_data" / "cache"
        ]
        
    def run(self):
        """Ejecutar el proceso completo de fix"""
        print("=" * 60)
        print("🚀 INICIANDO FIX DEL ERROR DE CACHE JSON")
        print("=" * 60)
        print()
        
        try:
            # Paso 1: Verificar estado actual
            print("📋 Paso 1: Verificando estado actual...")
            if not self.verify_current_state():
                return False
            
            # Paso 2: Crear backups
            print("\n💾 Paso 2: Creando backups de seguridad...")
            if not self.create_backups():
                return False
            
            # Paso 3: Limpiar archivos cache corruptos
            print("\n🧹 Paso 3: Limpiando archivos cache corruptos...")
            self.clean_corrupted_caches()
            
            # Paso 4: Aplicar el fix al código
            print("\n🔧 Paso 4: Aplicando fix al código...")
            if not self.apply_code_fix():
                return False
            
            # Paso 5: Crear estructura de directorios
            print("\n📁 Paso 5: Creando estructura de directorios...")
            self.create_directory_structure()
            
            # Paso 6: Verificar la aplicación
            print("\n✅ Paso 6: Verificando aplicación del fix...")
            if not self.verify_fix():
                print("\n❌ La verificación falló. Revirtiendo cambios...")
                self.rollback()
                return False
            
            print("\n" + "=" * 60)
            print("✅ FIX APLICADO EXITOSAMENTE")
            print("=" * 60)
            print("\n📌 Próximos pasos:")
            print("   1. Reiniciar el servicio: python main.py")
            print("   2. Verificar logs: tail -f logs/replicator_*.log")
            print("   3. Monitorear el servicio por unos minutos")
            print(f"\n💾 Backups guardados en: {self.backup_dir}")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Error crítico: {e}")
            print("Intentando rollback...")
            self.rollback()
            return False
    
    def verify_current_state(self) -> bool:
        """Verificar el estado actual del sistema"""
        issues = []
        
        # Verificar que existe el archivo file_processor.py
        if not self.file_processor_path.exists():
            issues.append(f"   ❌ No se encuentra: {self.file_processor_path}")
        else:
            print(f"   ✅ Archivo encontrado: {self.file_processor_path}")
        
        # Verificar archivos cache corruptos
        corrupted_files = []
        for cache_dir in self.cache_dirs:
            if cache_dir.exists():
                for json_file in cache_dir.rglob("*.json"):
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            json.load(f)
                    except json.JSONDecodeError:
                        corrupted_files.append(json_file)
        
        if corrupted_files:
            print(f"   ⚠️ Encontrados {len(corrupted_files)} archivos JSON corruptos")
            for f in corrupted_files[:5]:  # Mostrar máximo 5
                print(f"      - {f.relative_to(self.project_root)}")
        else:
            print("   ✅ No se encontraron archivos JSON corruptos")
        
        if issues:
            print("\n❌ Problemas encontrados:")
            for issue in issues:
                print(issue)
            return False
        
        return True
    
    def create_backups(self) -> bool:
        """Crear backups de todos los archivos relevantes"""
        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Backup del código
            if self.file_processor_path.exists():
                code_backup = self.backup_dir / "code"
                code_backup.mkdir(exist_ok=True)
                
                shutil.copy2(
                    self.file_processor_path,
                    code_backup / "file_processor.py.bak"
                )
                print(f"   ✅ Backup del código creado")
            
            # Backup de archivos cache
            cache_backup = self.backup_dir / "cache"
            cache_backup.mkdir(exist_ok=True)
            
            backed_up = 0
            for cache_dir in self.cache_dirs:
                if cache_dir.exists():
                    for json_file in cache_dir.rglob("*.json"):
                        try:
                            rel_path = json_file.relative_to(self.project_root)
                            backup_path = cache_backup / rel_path
                            backup_path.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(json_file, backup_path)
                            backed_up += 1
                        except Exception as e:
                            logger.warning(f"No se pudo respaldar {json_file}: {e}")
            
            print(f"   ✅ {backed_up} archivos cache respaldados")
            
            # Guardar información del backup
            info = {
                "timestamp": datetime.now().isoformat(),
                "files_backed_up": backed_up,
                "original_path": str(self.project_root)
            }
            
            with open(self.backup_dir / "backup_info.json", 'w') as f:
                json.dump(info, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"   ❌ Error creando backups: {e}")
            return False
    
    def clean_corrupted_caches(self):
        """Limpiar archivos cache corruptos"""
        cleaned = 0
        
        for cache_dir in self.cache_dirs:
            if not cache_dir.exists():
                continue
            
            for json_file in cache_dir.rglob("*.json"):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if not content.strip():
                            # Archivo vacío
                            json_file.unlink()
                            cleaned += 1
                            continue
                        
                        # Intentar parsear
                        json.loads(content)
                        
                except json.JSONDecodeError:
                    # Archivo corrupto - crear versión limpia
                    try:
                        if "cache_index" in json_file.name:
                            # Cache index - crear estructura nueva
                            new_content = {
                                "version": "2.0",
                                "created": datetime.now().isoformat(),
                                "entries": {},
                                "metadata": {
                                    "cleaned": True,
                                    "cleaned_at": datetime.now().isoformat()
                                }
                            }
                        else:
                            # Otro archivo JSON - crear estructura genérica
                            new_content = {}
                        
                        with open(json_file, 'w', encoding='utf-8') as f:
                            json.dump(new_content, f, indent=2, ensure_ascii=False)
                        
                        cleaned += 1
                        print(f"   🔧 Limpiado: {json_file.relative_to(self.project_root)}")
                        
                    except Exception as e:
                        logger.error(f"Error limpiando {json_file}: {e}")
                
                except Exception as e:
                    logger.error(f"Error procesando {json_file}: {e}")
        
        print(f"   ✅ {cleaned} archivos limpiados")
    
    def apply_code_fix(self) -> bool:
        """Aplicar el fix al código de file_processor.py"""
        try:
            if not self.file_processor_path.exists():
                print(f"   ❌ No existe el archivo: {self.file_processor_path}")
                return False
            
            # Leer el archivo original
            with open(self.file_processor_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Buscar la clase FileCache
            import_section_end = original_content.find("class FileCache:")
            if import_section_end == -1:
                print("   ❌ No se encontró la clase FileCache en el archivo")
                return False
            
            # Buscar el final de la clase FileCache
            class_end = original_content.find("\nclass FileProcessorEnhanced:")
            if class_end == -1:
                # Buscar alternativa
                class_end = original_content.find("\nclass ", import_section_end + 1)
                if class_end == -1:
                    class_end = len(original_content)
            
            # Extraer las importaciones y el resto del código
            imports_and_before = original_content[:import_section_end]
            after_filecache = original_content[class_end:]
            
            # Leer el código del fix (desde el artifact anterior)
            fixed_filecache_code = self.get_fixed_filecache_code()
            
            # Construir el nuevo contenido
            new_content = imports_and_before + fixed_filecache_code + after_filecache
            
            # Escribir el archivo actualizado
            with open(self.file_processor_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"   ✅ Código actualizado en: {self.file_processor_path}")
            return True
            
        except Exception as e:
            print(f"   ❌ Error aplicando fix al código: {e}")
            return False
    
    def get_fixed_filecache_code(self) -> str:
        """Obtener el código corregido de FileCache"""
        # Este es el código de la clase FileCache mejorada del artifact anterior
        return '''class FileCache:
    """
    Cache inteligente para archivos procesados con manejo robusto de errores
    Soluciona el problema de caracteres Unicode y JSON corrupto
    """
    
    def __init__(self, cache_dir: Path, max_cache_size_gb: float = 2.0):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_cache_size = max_cache_size_gb * 1024 * 1024 * 1024  # GB to bytes
        self.cache_index_file = cache_dir / "cache_index.json"
        self.backup_dir = cache_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        self.cache_index = self._load_cache_index()
    
    def _load_cache_index(self) -> Dict[str, Any]:
        """Cargar índice de cache con recuperación automática"""
        if not self.cache_index_file.exists():
            logger.info("📂 No existe cache_index.json, creando nuevo...")
            return self._create_empty_cache()
        
        try:
            with open(self.cache_index_file, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                
                if not content.strip():
                    logger.warning("⚠️ Cache index vacío, inicializando nuevo cache")
                    return self._create_empty_cache()
                
                try:
                    data = json.loads(content)
                    logger.info("✅ Cache index cargado correctamente")
                    return self._sanitize_cache_data(data)
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"❌ Error decodificando JSON: {e}")
                    return self._recover_corrupted_cache(content, e)
                    
        except Exception as e:
            logger.error(f"❌ Error crítico cargando cache: {e}")
            return self._handle_critical_error()
    
    def _create_empty_cache(self) -> Dict[str, Any]:
        """Crear estructura de cache vacía"""
        return {
            "version": "2.0",
            "created": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat(),
            "entries": {},
            "metadata": {
                "total_files": 0,
                "total_size_bytes": 0,
                "recovery_count": 0
            }
        }
    
    def _sanitize_cache_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitizar datos del cache para asegurar compatibilidad"""
        if "version" not in data:
            logger.info("📦 Migrando cache de formato antiguo a nuevo...")
            new_cache = self._create_empty_cache()
            new_cache["entries"] = data
            new_cache["metadata"]["migrated_from_v1"] = datetime.now().isoformat()
            return new_cache
        
        if "entries" not in data:
            data["entries"] = {}
        if "metadata" not in data:
            data["metadata"] = {}
            
        return data
    
    def _recover_corrupted_cache(self, content: str, error: json.JSONDecodeError) -> Dict[str, Any]:
        """Intentar recuperar datos de un cache corrupto"""
        logger.info("🔧 Intentando recuperar datos del cache corrupto...")
        
        self._backup_corrupted_file(content)
        
        try:
            error_pos = error.pos if hasattr(error, 'pos') else len(content)
            
            for i in range(error_pos - 1, max(0, error_pos - 1000), -1):
                partial_content = content[:i]
                
                if partial_content.rstrip().endswith('}'):
                    try:
                        recovered_data = json.loads(partial_content)
                        logger.info(f"✅ Recuperados {len(recovered_data)} entries del cache")
                        
                        sanitized = self._sanitize_cache_data(recovered_data)
                        sanitized["metadata"]["recovered_at"] = datetime.now().isoformat()
                        sanitized["metadata"]["recovery_count"] = \
                            sanitized["metadata"].get("recovery_count", 0) + 1
                        
                        return sanitized
                        
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.error(f"❌ Error en recuperación parcial: {e}")
        
        logger.warning("⚠️ No se pudo recuperar el cache, creando uno nuevo")
        new_cache = self._create_empty_cache()
        new_cache["metadata"]["corruption_detected"] = datetime.now().isoformat()
        return new_cache
    
    def _backup_corrupted_file(self, content: str):
        """Crear backup del archivo corrupto"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"cache_index_corrupted_{timestamp}.json.bak"
            
            with open(backup_file, 'w', encoding='utf-8', errors='replace') as f:
                f.write(content)
            
            logger.info(f"💾 Backup del cache corrupto guardado en: {backup_file}")
            
        except Exception as e:
            logger.error(f"❌ Error creando backup: {e}")
    
    def _handle_critical_error(self) -> Dict[str, Any]:
        """Manejar errores críticos creando un cache limpio"""
        logger.error("🆘 Error crítico, creando cache de emergencia")
        
        try:
            if self.cache_index_file.exists():
                emergency_backup = self.cache_index_file.with_suffix('.emergency.bak')
                shutil.move(str(self.cache_index_file), str(emergency_backup))
                logger.info(f"📦 Archivo problemático movido a: {emergency_backup}")
        except:
            pass
        
        return self._create_empty_cache()
    
    def _save_cache_index(self):
        """Guardar índice de cache con manejo robusto de Unicode"""
        try:
            if "metadata" not in self.cache_index:
                self.cache_index["metadata"] = {}
            
            self.cache_index["metadata"]["last_modified"] = datetime.now().isoformat()
            self.cache_index["metadata"]["total_entries"] = len(
                self.cache_index.get("entries", {})
            )
            
            temp_file = self.cache_index_file.with_suffix('.tmp')
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(
                    self.cache_index, 
                    f, 
                    ensure_ascii=False,
                    indent=2,
                    separators=(',', ': '),
                    default=str
                )
            
            with open(temp_file, 'r', encoding='utf-8') as f:
                json.load(f)
            
            temp_file.replace(self.cache_index_file)
            
            logger.debug("✅ Cache index guardado correctamente")
            
        except Exception as e:
            logger.error(f"❌ Error guardando cache index: {e}")
            
            try:
                self._save_emergency_cache()
            except:
                pass
    
    def _save_emergency_cache(self):
        """Guardar versión simplificada del cache en caso de emergencia"""
        try:
            emergency_cache = {
                "version": "2.0",
                "emergency_save": datetime.now().isoformat(),
                "entries": {},
                "metadata": {"emergency": True}
            }
            
            if "entries" in self.cache_index:
                for key, value in list(self.cache_index["entries"].items())[:100]:
                    try:
                        json.dumps(value)
                        emergency_cache["entries"][key] = value
                    except:
                        continue
            
            with open(self.cache_index_file, 'w', encoding='utf-8') as f:
                json.dump(emergency_cache, f, ensure_ascii=True)
                
            logger.warning("⚠️ Cache de emergencia guardado")
            
        except Exception as e:
            logger.error(f"❌ Fallo crítico guardando cache de emergencia: {e}")
    
    def get_file_hash(self, file_bytes: bytes) -> str:
        """Generar hash único para archivo"""
        return hashlib.sha256(file_bytes).hexdigest()[:16]
    
    def get_cached_result(self, file_hash: str, operation: str) -> Optional[Dict[str, Any]]:
        """Obtener resultado cacheado con manejo seguro"""
        cache_key = f"{file_hash}_{operation}"
        entries = self.cache_index.get("entries", {})
        
        if cache_key in entries:
            cache_info = entries[cache_key]
            
            if "filename" in cache_info:
                cache_file = self.cache_dir / cache_info['filename']
                
                if cache_file.exists():
                    cache_info['last_accessed'] = datetime.now().isoformat()
                    self._save_cache_index()
                    return cache_info
                else:
                    logger.warning(f"⚠️ Archivo cache no encontrado: {cache_file}")
                    del entries[cache_key]
                    self._save_cache_index()
        
        return None
    
    def cache_result(self, file_hash: str, operation: str, result: Dict[str, Any], 
                    output_bytes: Optional[bytes] = None) -> str:
        """Cachear resultado con validación"""
        cache_key = f"{file_hash}_{operation}"
        cache_filename = f"{cache_key}_{datetime.now().timestamp()}"
        
        try:
            json.dumps(result)
        except (TypeError, ValueError) as e:
            logger.warning(f"⚠️ Resultado no serializable, limpiando: {e}")
            result = self._make_serializable(result)
        
        cache_info = {
            'filename': cache_filename,
            'operation': operation,
            'result': result,
            'created': datetime.now().isoformat(),
            'last_accessed': datetime.now().isoformat(),
            'size_bytes': len(output_bytes) if output_bytes else 0
        }
        
        if output_bytes:
            try:
                cache_file = self.cache_dir / cache_filename
                cache_file.write_bytes(output_bytes)
            except Exception as e:
                logger.error(f"❌ Error guardando archivo cache: {e}")
        
        if "entries" not in self.cache_index:
            self.cache_index["entries"] = {}
        
        self.cache_index["entries"][cache_key] = cache_info
        self._save_cache_index()
        
        self._cleanup_cache_if_needed()
        
        return cache_filename
    
    def _make_serializable(self, obj: Any) -> Any:
        """Convertir objeto a formato serializable"""
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._make_serializable(v) for v in obj]
        elif isinstance(obj, bytes):
            return obj.decode('utf-8', errors='replace')
        elif hasattr(obj, '__dict__'):
            return str(obj)
        else:
            try:
                json.dumps(obj)
                return obj
            except:
                return str(obj)
    
    def _cleanup_cache_if_needed(self):
        """Limpiar cache si excede el tamaño máximo"""
        entries = self.cache_index.get("entries", {})
        total_size = sum(
            info.get('size_bytes', 0) 
            for info in entries.values()
        )
        
        if total_size > self.max_cache_size:
            logger.info("🧹 Iniciando limpieza de cache...")
            
            sorted_entries = sorted(
                entries.items(),
                key=lambda x: x[1].get('last_accessed', '1970-01-01')
            )
            
            removed_size = 0
            removed_count = 0
            target_remove = total_size - (self.max_cache_size * 0.8)
            
            for cache_key, cache_info in sorted_entries:
                if removed_size >= target_remove:
                    break
                
                if "filename" in cache_info:
                    cache_file = self.cache_dir / cache_info['filename']
                    try:
                        if cache_file.exists():
                            cache_file.unlink()
                    except Exception as e:
                        logger.error(f"❌ Error eliminando archivo: {e}")
                
                removed_size += cache_info.get('size_bytes', 0)
                removed_count += 1
                del entries[cache_key]
            
            self._save_cache_index()
            logger.info(
                f"✅ Cache limpiado: {removed_count} entries, "
                f"{removed_size / (1024*1024):.1f}MB liberados"
            )

'''
    
    def create_directory_structure(self):
        """Crear estructura de directorios necesaria"""
        directories = [
            "cache",
            "cache/backups",
            "temp",
            "processed_files",
            "watermark_data/cache",
            "watermark_data/cache/backups",
            "logs",
            "backups"
        ]
        
        for dir_path in directories:
            full_path = self.project_root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            
            # Crear .gitkeep
            gitkeep = full_path / ".gitkeep"
            gitkeep.touch(exist_ok=True)
        
        print(f"   ✅ Estructura de directorios creada")
    
    def verify_fix(self) -> bool:
        """Verificar que el fix se aplicó correctamente"""
        try:
            # Verificar que el código se actualizó
            with open(self.file_processor_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if "ensure_ascii=False" not in content:
                print("   ❌ El fix no se aplicó correctamente al código")
                return False
            
            print("   ✅ Código actualizado correctamente")
            
            # Verificar que los archivos JSON son válidos
            invalid_files = []
            for cache_dir in self.cache_dirs:
                if cache_dir.exists():
                    for json_file in cache_dir.rglob("*.json"):
                        try:
                            with open(json_file, 'r', encoding='utf-8') as f:
                                json.load(f)
                        except json.JSONDecodeError:
                            invalid_files.append(json_file)
            
            if invalid_files:
                print(f"   ❌ Todavía hay {len(invalid_files)} archivos JSON inválidos")
                return False
            
            print("   ✅ Todos los archivos JSON son válidos")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Error verificando fix: {e}")
            return False
    
    def rollback(self):
        """Revertir los cambios en caso de error"""
        try:
            print("\n🔄 Ejecutando rollback...")
            
            # Restaurar código original
            code_backup = self.backup_dir / "code" / "file_processor.py.bak"
            if code_backup.exists():
                shutil.copy2(code_backup, self.file_processor_path)
                print("   ✅ Código restaurado")
            
            # Restaurar archivos cache
            cache_backup = self.backup_dir / "cache"
            if cache_backup.exists():
                for backup_file in cache_backup.rglob("*.json"):
                    try:
                        rel_path = backup_file.relative_to(cache_backup)
                        original_path = self.project_root / rel_path
                        original_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(backup_file, original_path)
                    except Exception as e:
                        logger.error(f"Error restaurando {backup_file}: {e}")
                
                print("   ✅ Archivos cache restaurados")
            
            print("✅ Rollback completado")
            
        except Exception as e:
            print(f"❌ Error durante rollback: {e}")
            print("⚠️ Puede ser necesario restaurar manualmente desde:")
            print(f"   {self.backup_dir}")


def main():
    """Función principal"""
    print("\n🔧 FIX DE CACHE JSON PARA TELEGRAM-DISCORD BOT")
    print("=" * 60)
    print()
    
    # Confirmación del usuario
    print("⚠️ IMPORTANTE: Este script va a:")
    print("   1. Hacer backup de todos los archivos relevantes")
    print("   2. Limpiar archivos cache corruptos")
    print("   3. Actualizar el código de file_processor.py")
    print("   4. Crear estructura de directorios necesaria")
    print()
    
    response = input("¿Deseas continuar? (s/n): ").strip().lower()
    if response != 's':
        print("❌ Operación cancelada")
        return
    
    print()
    
    # Ejecutar el fix
    fixer = CacheFixer()
    success = fixer.run()
    
    if not success:
        print("\n❌ El fix no se completó exitosamente")
        sys.exit(1)
    
    print("\n✅ Proceso completado exitosamente")
    sys.exit(0)


if __name__ == "__main__":
    main()