"""
🔧 FILE CACHE MEJORADO - SOLUCIÓN ENTERPRISE
============================================
Reemplazo directo para la clase FileCache en app/services/file_processor.py
Soluciona el error de JSON con manejo robusto de Unicode y recuperación automática
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import hashlib
import shutil

logger = logging.getLogger(__name__)

class FileCache:
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
        
        # Cargar cache con manejo robusto de errores
        self.cache_index = self._load_cache_index()
    
    def _load_cache_index(self) -> Dict[str, Any]:
        """
        Cargar índice de cache con recuperación automática de errores
        """
        if not self.cache_index_file.exists():
            logger.info("📂 No existe cache_index.json, creando nuevo...")
            return self._create_empty_cache()
        
        try:
            # Intentar cargar el archivo con encoding UTF-8 explícito
            with open(self.cache_index_file, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                
                # Si el archivo está vacío, crear cache nuevo
                if not content.strip():
                    logger.warning("⚠️ Cache index vacío, inicializando nuevo cache")
                    return self._create_empty_cache()
                
                # Intentar parsear JSON
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
        """
        Sanitizar datos del cache para asegurar compatibilidad
        Convierte el formato antiguo al nuevo si es necesario
        """
        # Si es formato antiguo (sin estructura), convertir
        if "version" not in data:
            logger.info("📦 Migrando cache de formato antiguo a nuevo...")
            new_cache = self._create_empty_cache()
            new_cache["entries"] = data
            new_cache["metadata"]["migrated_from_v1"] = datetime.now().isoformat()
            return new_cache
        
        # Asegurar que todas las claves necesarias existen
        if "entries" not in data:
            data["entries"] = {}
        if "metadata" not in data:
            data["metadata"] = {}
            
        return data
    
    def _recover_corrupted_cache(self, content: str, error: json.JSONDecodeError) -> Dict[str, Any]:
        """
        Intentar recuperar datos de un cache corrupto
        """
        logger.info("🔧 Intentando recuperar datos del cache corrupto...")
        
        # Crear backup del archivo corrupto
        self._backup_corrupted_file(content)
        
        # Estrategia 1: Intentar recuperar hasta el punto del error
        try:
            # Obtener posición del error
            error_pos = error.pos if hasattr(error, 'pos') else len(content)
            
            # Intentar parsear hasta antes del error
            for i in range(error_pos - 1, max(0, error_pos - 1000), -1):
                partial_content = content[:i]
                
                # Buscar el último cierre de objeto válido
                if partial_content.rstrip().endswith('}'):
                    try:
                        recovered_data = json.loads(partial_content)
                        logger.info(f"✅ Recuperados {len(recovered_data)} entries del cache")
                        
                        # Sanitizar y retornar datos recuperados
                        sanitized = self._sanitize_cache_data(recovered_data)
                        sanitized["metadata"]["recovered_at"] = datetime.now().isoformat()
                        sanitized["metadata"]["recovery_count"] = \
                            sanitized["metadata"].get("recovery_count", 0) + 1
                        
                        return sanitized
                        
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.error(f"❌ Error en recuperación parcial: {e}")
        
        # Estrategia 2: Intentar extraer entries individuales con regex
        try:
            import re
            entries_recovered = {}
            
            # Buscar patrones de entries válidos
            entry_pattern = r'"([a-f0-9_]+)":\s*\{[^}]+\}'
            matches = re.finditer(entry_pattern, content)
            
            for match in matches:
                try:
                    entry_json = "{" + match.group(0) + "}"
                    entry_data = json.loads(entry_json)
                    key = list(entry_data.keys())[0]
                    entries_recovered[key] = entry_data[key]
                except:
                    continue
            
            if entries_recovered:
                logger.info(f"✅ Recuperados {len(entries_recovered)} entries mediante regex")
                new_cache = self._create_empty_cache()
                new_cache["entries"] = entries_recovered
                new_cache["metadata"]["recovery_method"] = "regex"
                return new_cache
                
        except Exception as e:
            logger.error(f"❌ Error en recuperación por regex: {e}")
        
        # Si todo falla, crear cache nuevo
        logger.warning("⚠️ No se pudo recuperar el cache, creando uno nuevo")
        new_cache = self._create_empty_cache()
        new_cache["metadata"]["corruption_detected"] = datetime.now().isoformat()
        return new_cache
    
    def _backup_corrupted_file(self, content: str):
        """Crear backup del archivo corrupto para análisis posterior"""
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
        
        # Intentar renombrar el archivo problemático
        try:
            if self.cache_index_file.exists():
                emergency_backup = self.cache_index_file.with_suffix('.emergency.bak')
                shutil.move(str(self.cache_index_file), str(emergency_backup))
                logger.info(f"📦 Archivo problemático movido a: {emergency_backup}")
        except:
            pass
        
        return self._create_empty_cache()
    
    def _save_cache_index(self):
        """
        Guardar índice de cache con manejo robusto de Unicode
        """
        try:
            # Actualizar metadata
            if "metadata" not in self.cache_index:
                self.cache_index["metadata"] = {}
            
            self.cache_index["metadata"]["last_modified"] = datetime.now().isoformat()
            self.cache_index["metadata"]["total_entries"] = len(
                self.cache_index.get("entries", {})
            )
            
            # Crear archivo temporal primero (atomic write)
            temp_file = self.cache_index_file.with_suffix('.tmp')
            
            # Guardar con configuración robusta
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(
                    self.cache_index, 
                    f, 
                    ensure_ascii=False,  # Permitir caracteres Unicode
                    indent=2,            # Formato legible
                    separators=(',', ': '),  # Separadores estándar
                    default=str          # Convertir objetos no serializables a string
                )
            
            # Verificar que el archivo se escribió correctamente
            with open(temp_file, 'r', encoding='utf-8') as f:
                json.load(f)  # Verificar que es JSON válido
            
            # Reemplazar archivo original (operación atómica)
            temp_file.replace(self.cache_index_file)
            
            logger.debug("✅ Cache index guardado correctamente")
            
        except Exception as e:
            logger.error(f"❌ Error guardando cache index: {e}")
            
            # Si falla, intentar guardar versión simplificada
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
            
            # Intentar preservar algunas entries
            if "entries" in self.cache_index:
                for key, value in list(self.cache_index["entries"].items())[:100]:
                    try:
                        # Verificar que el entry es serializable
                        json.dumps(value)
                        emergency_cache["entries"][key] = value
                    except:
                        continue
            
            with open(self.cache_index_file, 'w', encoding='utf-8') as f:
                json.dump(emergency_cache, f, ensure_ascii=True)  # ASCII seguro
                
            logger.warning("⚠️ Cache de emergencia guardado")
            
        except Exception as e:
            logger.error(f"❌ Fallo crítico guardando cache de emergencia: {e}")
    
    def get_file_hash(self, file_bytes: bytes) -> str:
        """Generar hash único para archivo"""
        return hashlib.sha256(file_bytes).hexdigest()[:16]
    
    def get_cached_result(self, file_hash: str, operation: str) -> Optional[Dict[str, Any]]:
        """Obtener resultado cacheado con manejo seguro"""
        cache_key = f"{file_hash}_{operation}"
        
        # Asegurar estructura correcta
        entries = self.cache_index.get("entries", {})
        
        if cache_key in entries:
            cache_info = entries[cache_key]
            
            # Verificar que el archivo físico existe si es necesario
            if "filename" in cache_info:
                cache_file = self.cache_dir / cache_info['filename']
                
                if cache_file.exists():
                    # Actualizar último acceso
                    cache_info['last_accessed'] = datetime.now().isoformat()
                    self._save_cache_index()
                    return cache_info
                else:
                    # El archivo no existe, limpiar entrada
                    logger.warning(f"⚠️ Archivo cache no encontrado: {cache_file}")
                    del entries[cache_key]
                    self._save_cache_index()
        
        return None
    
    def cache_result(self, file_hash: str, operation: str, result: Dict[str, Any], 
                    output_bytes: Optional[bytes] = None) -> str:
        """Cachear resultado con validación"""
        cache_key = f"{file_hash}_{operation}"
        cache_filename = f"{cache_key}_{datetime.now().timestamp()}"
        
        # Asegurar que result es serializable
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
        
        # Guardar archivo si hay bytes
        if output_bytes:
            try:
                cache_file = self.cache_dir / cache_filename
                cache_file.write_bytes(output_bytes)
            except Exception as e:
                logger.error(f"❌ Error guardando archivo cache: {e}")
                # Continuar sin el archivo físico
        
        # Asegurar estructura correcta
        if "entries" not in self.cache_index:
            self.cache_index["entries"] = {}
        
        self.cache_index["entries"][cache_key] = cache_info
        self._save_cache_index()
        
        # Limpieza de cache si es necesario
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
            
            # Ordenar por último acceso
            sorted_entries = sorted(
                entries.items(),
                key=lambda x: x[1].get('last_accessed', '1970-01-01')
            )
            
            # Eliminar entradas más antiguas
            removed_size = 0
            removed_count = 0
            target_remove = total_size - (self.max_cache_size * 0.8)  # Liberar 20% extra
            
            for cache_key, cache_info in sorted_entries:
                if removed_size >= target_remove:
                    break
                
                # Eliminar archivo físico si existe
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
    
    def clear_cache(self):
        """Limpiar todo el cache manualmente"""
        try:
            # Backup antes de limpiar
            if self.cache_index_file.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = self.backup_dir / f"cache_index_before_clear_{timestamp}.json"
                shutil.copy2(self.cache_index_file, backup_file)
            
            # Eliminar todos los archivos cache
            entries = self.cache_index.get("entries", {})
            for cache_info in entries.values():
                if "filename" in cache_info:
                    cache_file = self.cache_dir / cache_info['filename']
                    try:
                        if cache_file.exists():
                            cache_file.unlink()
                    except:
                        pass
            
            # Crear cache nuevo
            self.cache_index = self._create_empty_cache()
            self.cache_index["metadata"]["cleared_at"] = datetime.now().isoformat()
            self._save_cache_index()
            
            logger.info("✅ Cache limpiado completamente")
            
        except Exception as e:
            logger.error(f"❌ Error limpiando cache: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del cache"""
        entries = self.cache_index.get("entries", {})
        
        total_size = sum(
            info.get('size_bytes', 0) 
            for info in entries.values()
        )
        
        return {
            "total_entries": len(entries),
            "total_size_mb": total_size / (1024 * 1024),
            "max_size_mb": self.max_cache_size / (1024 * 1024),
            "usage_percent": (total_size / self.max_cache_size * 100) if self.max_cache_size > 0 else 0,
            "version": self.cache_index.get("version", "unknown"),
            "created": self.cache_index.get("created", "unknown"),
            "last_modified": self.cache_index.get("metadata", {}).get("last_modified", "unknown"),
            "recovery_count": self.cache_index.get("metadata", {}).get("recovery_count", 0)
        }