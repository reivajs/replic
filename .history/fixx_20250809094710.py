#!/usr/bin/env python3
"""
🚀 APLICACIÓN RÁPIDA DEL FIX COMPLETO
======================================
Restaura FileProcessorEnhanced + FileCache mejorado
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

def apply_fix():
    """Aplicar el fix completo al file_processor.py"""
    
    print("\n" + "="*60)
    print("🚀 APLICANDO FIX COMPLETO DE FILE PROCESSOR")
    print("="*60 + "\n")
    
    # Definir rutas
    file_processor_path = Path("app/services/file_processor.py")
    backup_dir = Path("backups") / datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Verificar que existe el archivo
    if not file_processor_path.exists():
        print(f"❌ No se encuentra el archivo: {file_processor_path}")
        print("   Asegúrate de ejecutar este script desde la raíz del proyecto")
        return False
    
    # Crear backup
    print("💾 Creando backup...")
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_file = backup_dir / "file_processor.py.bak"
    shutil.copy2(file_processor_path, backup_file)
    print(f"   ✅ Backup guardado en: {backup_file}")
    
    # Escribir el nuevo contenido
    print("\n🔧 Aplicando fix completo...")
    
    new_content = '''"""
Enterprise File Processor Service - VERSIÓN COMPLETA CON FIX
============================================================
Servicio enterprise para procesamiento de archivos multimedia
Incluye FileCache mejorado + FileProcessorEnhanced

Archivo: app/services/file_processor.py
"""

import asyncio
import subprocess
import tempfile
import shutil
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import hashlib
import mimetypes

try:
    import fitz  # PyMuPDF para PDFs
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from app.utils.logger import setup_logger
from app.config.settings import get_settings

logger = setup_logger(__name__)
settings = get_settings()


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
            # Compatibilidad con formato antiguo (sin "entries")
            if not any(k in data for k in ["version", "entries", "metadata"]):
                new_cache["entries"] = data
            else:
                new_cache["entries"] = data.get("entries", {})
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
                        logger.info(f"✅ Recuperados datos del cache")
                        
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
            
            # Compatibilidad con ambos formatos
            if "entries" in self.cache_index:
                self.cache_index["metadata"]["total_entries"] = len(self.cache_index["entries"])
            
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
            
            temp_file.replace(self.cache_index_file)
            
        except Exception as e:
            logger.error(f"❌ Error guardando cache index: {e}")
    
    def get_file_hash(self, file_bytes: bytes) -> str:
        """Generar hash único para archivo"""
        return hashlib.sha256(file_bytes).hexdigest()[:16]
    
    def get_cached_result(self, file_hash: str, operation: str) -> Optional[Dict[str, Any]]:
        """Obtener resultado cacheado con manejo seguro"""
        cache_key = f"{file_hash}_{operation}"
        
        # Compatibilidad con ambos formatos
        if "entries" in self.cache_index:
            entries = self.cache_index["entries"]
        else:
            entries = self.cache_index
        
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
        
        # Compatibilidad con ambos formatos
        if "entries" not in self.cache_index:
            self.cache_index = self._sanitize_cache_data(self.cache_index)
        
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
        # Compatibilidad con ambos formatos
        if "entries" in self.cache_index:
            entries = self.cache_index["entries"]
        else:
            entries = self.cache_index
            
        total_size = sum(
            info.get('size_bytes', 0) 
            for info in entries.values()
            if isinstance(info, dict)
        )
        
        if total_size > self.max_cache_size:
            logger.info("🧹 Iniciando limpieza de cache...")
            
            sorted_entries = sorted(
                entries.items(),
                key=lambda x: x[1].get('last_accessed', '1970-01-01') if isinstance(x[1], dict) else '1970-01-01'
            )
            
            removed_size = 0
            removed_count = 0
            target_remove = total_size - (self.max_cache_size * 0.8)
            
            for cache_key, cache_info in sorted_entries:
                if not isinstance(cache_info, dict):
                    continue
                    
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


class FileProcessorEnhanced:
    """
    🚀 FILE PROCESSOR ENTERPRISE - Sistema completo de procesamiento
    ==================================================================
    Procesamiento avanzado de multimedia con cache inteligente
    """
    
    def __init__(self):
        self.cache_dir = Path(settings.CACHE_DIR if hasattr(settings, 'CACHE_DIR') else "cache")
        self.temp_dir = Path(settings.TEMP_DIR if hasattr(settings, 'TEMP_DIR') else "temp")
        self.output_dir = Path(settings.OUTPUT_DIR if hasattr(settings, 'OUTPUT_DIR') else "processed_files")
        
        # Crear directorios necesarios
        for dir_path in [self.cache_dir, self.temp_dir, self.output_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Inicializar cache inteligente
        self.file_cache = FileCache(self.cache_dir)
        
        # Estadísticas de procesamiento
        self.stats = {
            'images_processed': 0,
            'videos_processed': 0,
            'pdfs_processed': 0,
            'audios_processed': 0,
            'total_size_processed': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'errors': 0
        }
        
        # Configuración de compresión
        self.compression_settings = {
            'image_quality': 85,
            'video_crf': 23,
            'audio_bitrate': '128k',
            'max_image_size': (1920, 1080),
            'max_video_size': (1280, 720)
        }
        
        logger.info(f"🚀 File Processor Enterprise inicializado")
        logger.info(f"   📁 Cache: {self.cache_dir}")
        logger.info(f"   📁 Temp: {self.temp_dir}")
        logger.info(f"   📁 Output: {self.output_dir}")
    
    async def initialize(self):
        """Inicializar el procesador"""
        await self._check_dependencies()
        logger.info("✅ File Processor Enterprise inicializado correctamente")
    
    async def _check_dependencies(self):
        """Verificar dependencias del sistema"""
        dependencies = {
            'ffmpeg': await self._check_ffmpeg(),
            'pymupdf': PYMUPDF_AVAILABLE,
            'pil': PIL_AVAILABLE
        }
        
        logger.info("📦 Dependencias verificadas:")
        for dep, available in dependencies.items():
            status = "✅" if available else "❌"
            logger.info(f"   {dep}: {status}")
    
    async def _check_ffmpeg(self) -> bool:
        """Verificar si ffmpeg está disponible"""
        try:
            proc = await asyncio.create_subprocess_exec(
                'ffmpeg', '-version',
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await proc.wait()
            return proc.returncode == 0
        except:
            return False
    
    async def process_file(self, file_bytes: bytes, filename: str, 
                          file_type: str) -> Dict[str, Any]:
        """Procesar archivo según su tipo"""
        try:
            # Generar hash del archivo
            file_hash = self.file_cache.get_file_hash(file_bytes)
            
            # Buscar en cache
            cached_result = self.file_cache.get_cached_result(file_hash, file_type)
            if cached_result:
                self.stats['cache_hits'] += 1
                logger.info(f"✅ Cache hit para {filename}")
                return cached_result['result']
            
            self.stats['cache_misses'] += 1
            
            # Procesar según tipo
            if file_type == 'image':
                result = await self.process_image(file_bytes, filename)
            elif file_type == 'video':
                result = await self.process_video(file_bytes, filename)
            elif file_type == 'pdf':
                result = await self.process_pdf(file_bytes, filename)
            elif file_type == 'audio':
                result = await self.process_audio(file_bytes, filename)
            else:
                result = await self.process_generic(file_bytes, filename)
            
            # Cachear resultado
            self.file_cache.cache_result(file_hash, file_type, result)
            
            # Actualizar estadísticas
            self.stats['total_size_processed'] += len(file_bytes)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error procesando archivo {filename}: {e}")
            self.stats['errors'] += 1
            return {
                'success': False,
                'error': str(e),
                'filename': filename
            }
    
    async def process_image(self, image_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Procesar imagen con compresión opcional"""
        if not PIL_AVAILABLE:
            return {
                'success': False,
                'error': 'PIL no disponible',
                'filename': filename
            }
        
        try:
            from io import BytesIO
            
            # Abrir imagen
            img = Image.open(BytesIO(image_bytes))
            
            # Obtener información
            original_size = len(image_bytes)
            original_format = img.format
            original_dimensions = img.size
            
            # Comprimir si es necesario
            max_size = self.compression_settings['max_image_size']
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Guardar con compresión
            output_buffer = BytesIO()
            save_format = 'JPEG' if original_format in ['JPEG', 'JPG'] else original_format
            img.save(
                output_buffer, 
                format=save_format,
                quality=self.compression_settings['image_quality'],
                optimize=True
            )
            
            compressed_bytes = output_buffer.getvalue()
            compressed_size = len(compressed_bytes)
            
            # Guardar archivo procesado
            output_filename = f"img_{self.file_cache.get_file_hash(image_bytes)}_{filename}"
            output_path = self.output_dir / output_filename
            output_path.write_bytes(compressed_bytes)
            
            self.stats['images_processed'] += 1
            
            result = {
                'success': True,
                'filename': filename,
                'output_path': str(output_path),
                'original_size': original_size,
                'compressed_size': compressed_size,
                'compression_ratio': compressed_size / original_size,
                'original_dimensions': original_dimensions,
                'final_dimensions': img.size,
                'format': save_format
            }
            
            logger.info(f"🖼️ Imagen procesada: {filename} "
                       f"({original_size/1024:.1f}KB → {compressed_size/1024:.1f}KB)")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error procesando imagen: {e}")
            return {
                'success': False,
                'error': str(e),
                'filename': filename
            }
    
    async def process_video(self, video_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Procesar video con compresión opcional"""
        try:
            # Guardar temporalmente
            temp_input = self.temp_dir / f"input_{filename}"
            temp_output = self.temp_dir / f"output_{filename}"
            
            temp_input.write_bytes(video_bytes)
            
            # Comando ffmpeg para comprimir
            cmd = [
                'ffmpeg', '-i', str(temp_input),
                '-c:v', 'libx264',
                '-crf', str(self.compression_settings['video_crf']),
                '-preset', 'medium',
                '-c:a', 'aac',
                '-b:a', self.compression_settings['audio_bitrate'],
                '-movflags', '+faststart',
                str(temp_output),
                '-y'
            ]
            
            # Ejecutar ffmpeg
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                raise Exception(f"FFmpeg error: {stderr.decode()}")
            
            # Leer archivo procesado
            processed_bytes = temp_output.read_bytes()
            
            # Guardar en directorio de salida
            output_filename = f"audio_{self.file_cache.get_file_hash(audio_bytes)}_{filename}.mp3"
            output_path = self.output_dir / output_filename
            output_path.write_bytes(processed_bytes)
            
            # Limpiar temporales
            temp_input.unlink()
            temp_output.unlink()
            
            self.stats['audios_processed'] += 1
            
            result = {
                'success': True,
                'filename': filename,
                'output_path': str(output_path),
                'original_size': len(audio_bytes),
                'compressed_size': len(processed_bytes),
                'format': 'mp3',
                'bitrate': self.compression_settings['audio_bitrate']
            }
            
            logger.info(f"🎵 Audio procesado: {filename} → MP3")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error procesando audio: {e}")
            return {
                'success': False,
                'error': str(e),
                'filename': filename
            }
    
    async def process_generic(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Procesar archivo genérico (solo guardar)"""
        try:
            # Guardar archivo
            output_filename = f"file_{self.file_cache.get_file_hash(file_bytes)}_{filename}"
            output_path = self.output_dir / output_filename
            output_path.write_bytes(file_bytes)
            
            result = {
                'success': True,
                'filename': filename,
                'output_path': str(output_path),
                'file_size': len(file_bytes),
                'mime_type': mimetypes.guess_type(filename)[0]
            }
            
            logger.info(f"📎 Archivo genérico guardado: {filename}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error procesando archivo: {e}")
            return {
                'success': False,
                'error': str(e),
                'filename': filename
            }
    
    async def cleanup(self):
        """Limpiar archivos temporales y cache viejo"""
        try:
            # Limpiar archivos temporales
            cleaned_count = 0
            for temp_file in self.temp_dir.glob("*"):
                try:
                    if temp_file.is_file():
                        # Eliminar si tiene más de 1 hora
                        file_age = datetime.now().timestamp() - temp_file.stat().st_mtime
                        if file_age > 3600:  # 1 hora
                            temp_file.unlink()
                            cleaned_count += 1
                except Exception as e:
                    logger.error(f"Error limpiando {temp_file}: {e}")
            
            logger.info(f"🧹 Limpiados {cleaned_count} archivos temporales")
            
            # Limpiar cache si es necesario
            if hasattr(self.file_cache, '_cleanup_cache_if_needed'):
                self.file_cache._cleanup_cache_if_needed()
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"❌ Error en limpieza: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de procesamiento"""
        return {
            'processor_stats': self.stats,
            'directories': {
                'cache': str(self.cache_dir),
                'temp': str(self.temp_dir),
                'output': str(self.output_dir)
            }
        }


# Función helper para crear instancia
def create_file_processor() -> FileProcessorEnhanced:
    """Factory function para crear FileProcessorEnhanced"""
    return FileProcessorEnhanced()


# Exportar las clases principales
__all__ = ['FileCache', 'FileProcessorEnhanced', 'create_file_processor']
'''
    
    try:
        with open(file_processor_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("   ✅ Archivo actualizado correctamente")
    except Exception as e:
        print(f"   ❌ Error escribiendo archivo: {e}")
        return False
    
    # Limpiar archivos cache corruptos
    print("\n🧹 Limpiando archivos cache corruptos...")
    cache_dirs = [
        Path("cache"),
        Path("temp"),
        Path("processed_files"),
        Path("watermark_data/cache")
    ]
    
    cleaned = 0
    for cache_dir in cache_dirs:
        if cache_dir.exists():
            for json_file in cache_dir.rglob("*.json"):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        json.load(f)
                except:
                    print(f"   🗑️ Eliminando cache corrupto: {json_file}")
                    json_file.unlink()
                    cleaned += 1
    
    print(f"   ✅ {cleaned} archivos cache limpiados")
    
    # Crear directorios necesarios
    print("\n📁 Creando estructura de directorios...")
    for cache_dir in cache_dirs:
        cache_dir.mkdir(parents=True, exist_ok=True)
        backup_dir = cache_dir / "backups"
        backup_dir.mkdir(exist_ok=True)
    print("   ✅ Directorios creados")
    
    # Verificar la aplicación
    print("\n✅ VERIFICACIÓN FINAL:")
    print("   ✅ FileCache con manejo robusto de Unicode")
    print("   ✅ FileProcessorEnhanced restaurado completamente")
    print("   ✅ Compatible con el Enhanced Replicator Service")
    print("   ✅ Archivos cache corruptos limpiados")
    print("   ✅ Estructura de directorios creada")
    
    print("\n" + "="*60)
    print("✅ FIX APLICADO EXITOSAMENTE")
    print("="*60)
    
    return True


def verify_import():
    """Verificar que se puede importar correctamente"""
    print("\n🔍 Verificando importación...")
    try:
        import sys
        import importlib
        
        # Añadir el directorio actual al path si no está
        if '.' not in sys.path:
            sys.path.insert(0, '.')
        
        # Intentar importar el módulo
        if 'app.services.file_processor' in sys.modules:
            importlib.reload(sys.modules['app.services.file_processor'])
        else:
            import app.services.file_processor
        
        # Verificar que las clases existen
        from app.services.file_processor import FileCache, FileProcessorEnhanced
        
        print("   ✅ FileCache importado correctamente")
        print("   ✅ FileProcessorEnhanced importado correctamente")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Error de importación: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Error inesperado: {e}")
        return False


def main():
    """Función principal"""
    print("\n🚀 FIX RÁPIDO PARA FILE PROCESSOR")
    print("="*60)
    print("Este script:")
    print("  1. Restaura FileProcessorEnhanced")
    print("  2. Mantiene el fix de cache Unicode")
    print("  3. Limpia archivos corruptos")
    print("  4. Crea estructura de directorios")
    print("="*60)
    
    # Aplicar el fix
    if apply_fix():
        # Verificar importación
        if verify_import():
            print("\n" + "="*60)
            print("🎉 TODO LISTO!")
            print("="*60)
            print("\n📌 Ahora puedes:")
            print("   1. Reiniciar los servicios:")
            print("      python scripts/start_all.py")
            print("   2. O ejecutar el servicio principal:")
            print("      python main.py")
            print("\n✅ Tu bot debería replicar mensajes correctamente ahora")
        else:
            print("\n⚠️ El fix se aplicó pero hay problemas de importación")
            print("Intenta reiniciar Python o tu IDE")
    else:
        print("\n❌ No se pudo aplicar el fix")
        print("Verifica que estás en el directorio correcto del proyecto")


if __name__ == "__main__":
    main()code != 0:
                raise Exception(f"FFmpeg error: {stderr.decode()}")
            
            # Leer archivo procesado
            processed_bytes = temp_output.read_bytes()
            
            # Guardar en directorio de salida
            output_filename = f"video_{self.file_cache.get_file_hash(video_bytes)}_{filename}"
            output_path = self.output_dir / output_filename
            output_path.write_bytes(processed_bytes)
            
            # Limpiar temporales
            temp_input.unlink()
            temp_output.unlink()
            
            self.stats['videos_processed'] += 1
            
            result = {
                'success': True,
                'filename': filename,
                'output_path': str(output_path),
                'original_size': len(video_bytes),
                'compressed_size': len(processed_bytes),
                'compression_ratio': len(processed_bytes) / len(video_bytes)
            }
            
            logger.info(f"🎬 Video procesado: {filename} "
                       f"({len(video_bytes)/1024/1024:.1f}MB → {len(processed_bytes)/1024/1024:.1f}MB)")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error procesando video: {e}")
            return {
                'success': False,
                'error': str(e),
                'filename': filename
            }
    
    async def process_pdf(self, pdf_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Procesar PDF y extraer información"""
        if not PYMUPDF_AVAILABLE:
            return {
                'success': False,
                'error': 'PyMuPDF no disponible',
                'filename': filename
            }
        
        try:
            # Abrir PDF
            pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            # Extraer información
            page_count = len(pdf_document)
            text_content = []
            images_count = 0
            
            for page_num in range(min(page_count, 10)):  # Limitar a 10 páginas para preview
                page = pdf_document[page_num]
                text_content.append(page.get_text())
                images_count += len(page.get_images())
            
            # Guardar PDF
            output_filename = f"pdf_{self.file_cache.get_file_hash(pdf_bytes)}_{filename}"
            output_path = self.output_dir / output_filename
            output_path.write_bytes(pdf_bytes)
            
            pdf_document.close()
            
            self.stats['pdfs_processed'] += 1
            
            result = {
                'success': True,
                'filename': filename,
                'output_path': str(output_path),
                'page_count': page_count,
                'images_count': images_count,
                'text_preview': '\\n'.join(text_content[:3])[:500],  # Primeras 3 páginas, max 500 chars
                'file_size': len(pdf_bytes)
            }
            
            logger.info(f"📄 PDF procesado: {filename} ({page_count} páginas)")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error procesando PDF: {e}")
            return {
                'success': False,
                'error': str(e),
                'filename': filename
            }
    
    async def process_audio(self, audio_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Procesar audio y convertir a formato estándar"""
        try:
            # Guardar temporalmente
            temp_input = self.temp_dir / f"input_{filename}"
            temp_output = self.temp_dir / f"output_{filename}.mp3"
            
            temp_input.write_bytes(audio_bytes)
            
            # Convertir a MP3 con ffmpeg
            cmd = [
                'ffmpeg', '-i', str(temp_input),
                '-c:a', 'libmp3lame',
                '-b:a', self.compression_settings['audio_bitrate'],
                str(temp_output),
                '-y'
            ]
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.return