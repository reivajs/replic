#!/usr/bin/env python3
"""
🚀 SCRIPT DE REPARACIÓN COMPLETA - FILE PROCESSOR
==================================================
Restaura FileProcessorEnhanced + FileCache con fix Unicode
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime


def apply_fix():
    """Aplicar el fix completo al proyecto"""
    
    print("\n" + "="*60)
    print("🚀 REPARACIÓN COMPLETA DE FILE PROCESSOR")
    print("="*60 + "\n")
    
    # Verificar que estamos en el directorio correcto
    file_processor_path = Path("app/services/file_processor.py")
    
    if not file_processor_path.parent.exists():
        print("❌ Error: No se encuentra el directorio app/services/")
        print("   Asegúrate de ejecutar este script desde la raíz del proyecto")
        return False
    
    # Crear backup
    print("💾 Creando backup...")
    backup_dir = Path("backups") / datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    if file_processor_path.exists():
        backup_file = backup_dir / "file_processor.py.bak"
        shutil.copy2(file_processor_path, backup_file)
        print(f"   ✅ Backup guardado en: {backup_file}")
    
    # Limpiar archivos cache corruptos ANTES de escribir el nuevo código
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
                    print(f"   🗑️ Eliminando: {json_file.name}")
                    try:
                        json_file.unlink()
                        cleaned += 1
                    except:
                        pass
    
    print(f"   ✅ {cleaned} archivos corruptos eliminados")
    
    # Crear directorios necesarios
    print("\n📁 Creando estructura de directorios...")
    for cache_dir in cache_dirs:
        cache_dir.mkdir(parents=True, exist_ok=True)
        backup_dir = cache_dir / "backups"
        backup_dir.mkdir(exist_ok=True)
    print("   ✅ Directorios creados")
    
    # Escribir el nuevo código
    print("\n🔧 Aplicando el código reparado...")
    
    # Leer el template del código desde un archivo externo o generarlo aquí
    new_code = generate_fixed_code()
    
    try:
        # Asegurar que el directorio existe
        file_processor_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Escribir el nuevo código
        with open(file_processor_path, 'w', encoding='utf-8') as f:
            f.write(new_code)
        
        print("   ✅ Código actualizado correctamente")
        
    except Exception as e:
        print(f"   ❌ Error escribiendo archivo: {e}")
        return False
    
    print("\n" + "="*60)
    print("✅ REPARACIÓN COMPLETADA EXITOSAMENTE")
    print("="*60)
    
    return True


def generate_fixed_code():
    """Generar el código completo reparado"""
    
    # Este es el código completo con FileCache mejorado + FileProcessorEnhanced
    code = '''"""
Enterprise File Processor Service
=================================
Servicio enterprise para procesamiento de archivos multimedia
Versión reparada con manejo robusto de Unicode

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
    """Cache inteligente para archivos procesados"""
    
    def __init__(self, cache_dir: Path, max_cache_size_gb: float = 2.0):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_cache_size = max_cache_size_gb * 1024 * 1024 * 1024
        self.cache_index_file = cache_dir / "cache_index.json"
        self.cache_index = self._load_cache_index()
    
    def _load_cache_index(self) -> Dict[str, Any]:
        """Cargar índice de cache con manejo robusto"""
        if self.cache_index_file.exists():
            try:
                with open(self.cache_index_file, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                    if content.strip():
                        return json.loads(content)
            except Exception as e:
                logger.warning(f"Error cargando cache index: {e}")
                # Hacer backup del archivo corrupto
                backup_file = self.cache_index_file.with_suffix('.corrupted')
                try:
                    shutil.copy2(self.cache_index_file, backup_file)
                except:
                    pass
        return {}
    
    def _save_cache_index(self):
        """Guardar índice de cache con manejo robusto de Unicode"""
        try:
            # Crear archivo temporal primero
            temp_file = self.cache_index_file.with_suffix('.tmp')
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(
                    self.cache_index, 
                    f, 
                    ensure_ascii=False,  # Permitir Unicode
                    indent=2,
                    default=str  # Convertir objetos no serializables
                )
            
            # Reemplazar archivo original
            temp_file.replace(self.cache_index_file)
            
        except Exception as e:
            logger.error(f"Error guardando cache index: {e}")
    
    def get_file_hash(self, file_bytes: bytes) -> str:
        """Generar hash único para archivo"""
        return hashlib.sha256(file_bytes).hexdigest()[:16]
    
    def get_cached_result(self, file_hash: str, operation: str) -> Optional[Dict[str, Any]]:
        """Obtener resultado cacheado"""
        cache_key = f"{file_hash}_{operation}"
        if cache_key in self.cache_index:
            cache_info = self.cache_index[cache_key]
            cache_file = self.cache_dir / cache_info['filename']
            
            if cache_file.exists():
                cache_info['last_accessed'] = datetime.now().isoformat()
                self._save_cache_index()
                return cache_info
        
        return None
    
    def cache_result(self, file_hash: str, operation: str, result: Dict[str, Any], 
                    output_bytes: Optional[bytes] = None) -> str:
        """Cachear resultado"""
        cache_key = f"{file_hash}_{operation}"
        cache_filename = f"{cache_key}_{datetime.now().timestamp()}"
        
        # Asegurar que result es serializable
        try:
            json.dumps(result)
        except:
            result = {k: str(v) for k, v in result.items()}
        
        cache_info = {
            'filename': cache_filename,
            'operation': operation,
            'result': result,
            'created': datetime.now().isoformat(),
            'last_accessed': datetime.now().isoformat(),
            'size_bytes': len(output_bytes) if output_bytes else 0
        }
        
        if output_bytes:
            cache_file = self.cache_dir / cache_filename
            cache_file.write_bytes(output_bytes)
        
        self.cache_index[cache_key] = cache_info
        self._save_cache_index()
        
        self._cleanup_cache_if_needed()
        
        return cache_filename
    
    def _cleanup_cache_if_needed(self):
        """Limpiar cache si excede el tamaño máximo"""
        total_size = sum(info.get('size_bytes', 0) for info in self.cache_index.values())
        
        if total_size > self.max_cache_size:
            sorted_entries = sorted(
                self.cache_index.items(),
                key=lambda x: x[1].get('last_accessed', '1970-01-01')
            )
            
            removed_size = 0
            target_remove = total_size - (self.max_cache_size * 0.8)
            
            for cache_key, cache_info in sorted_entries:
                if removed_size >= target_remove:
                    break
                
                cache_file = self.cache_dir / cache_info['filename']
                if cache_file.exists():
                    cache_file.unlink()
                    removed_size += cache_info.get('size_bytes', 0)
                
                del self.cache_index[cache_key]
            
            self._save_cache_index()
            logger.info(f"Cache limpiado: {removed_size / (1024*1024):.1f}MB liberados")


class FileProcessorEnhanced:
    """
    FILE PROCESSOR ENTERPRISE
    Sistema completo de procesamiento de archivos multimedia
    """
    
    def __init__(self):
        self.cache_dir = Path(settings.CACHE_DIR if hasattr(settings, 'CACHE_DIR') else "cache")
        self.temp_dir = Path(settings.TEMP_DIR if hasattr(settings, 'TEMP_DIR') else "temp")
        self.output_dir = Path(settings.OUTPUT_DIR if hasattr(settings, 'OUTPUT_DIR') else "processed_files")
        
        # Crear directorios
        for dir_path in [self.cache_dir, self.temp_dir, self.output_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Inicializar cache
        self.file_cache = FileCache(self.cache_dir)
        
        # Estadísticas
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
        
        # Configuración
        self.compression_settings = {
            'image_quality': 85,
            'video_crf': 23,
            'audio_bitrate': '128k',
            'max_image_size': (1920, 1080),
            'max_video_size': (1280, 720)
        }
        
        logger.info(f"🚀 File Processor Enterprise inicializado")
    
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
    
    async def process_image(self, image_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Procesar imagen"""
        if not PIL_AVAILABLE:
            return {'success': False, 'error': 'PIL no disponible'}
        
        try:
            from io import BytesIO
            
            img = Image.open(BytesIO(image_bytes))
            original_size = len(image_bytes)
            
            # Comprimir si es necesario
            max_size = self.compression_settings['max_image_size']
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Guardar
            output_buffer = BytesIO()
            img.save(
                output_buffer, 
                format='JPEG',
                quality=self.compression_settings['image_quality'],
                optimize=True
            )
            
            compressed_bytes = output_buffer.getvalue()
            
            # Guardar archivo
            output_filename = f"img_{self.file_cache.get_file_hash(image_bytes)}_{filename}"
            output_path = self.output_dir / output_filename
            output_path.write_bytes(compressed_bytes)
            
            self.stats['images_processed'] += 1
            
            logger.info(f"🖼️ Imagen procesada: {filename}")
            
            return {
                'success': True,
                'filename': filename,
                'output_path': str(output_path),
                'original_size': original_size,
                'compressed_size': len(compressed_bytes)
            }
            
        except Exception as e:
            logger.error(f"Error procesando imagen: {e}")
            return {'success': False, 'error': str(e)}
    
    async def process_video(self, video_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Procesar video"""
        try:
            # Guardar temporalmente
            temp_input = self.temp_dir / f"input_{filename}"
            temp_output = self.temp_dir / f"output_{filename}"
            
            temp_input.write_bytes(video_bytes)
            
            # Comando ffmpeg
            cmd = [
                'ffmpeg', '-i', str(temp_input),
                '-c:v', 'libx264',
                '-crf', str(self.compression_settings['video_crf']),
                '-preset', 'medium',
                '-c:a', 'aac',
                '-b:a', self.compression_settings['audio_bitrate'],
                str(temp_output),
                '-y'
            ]
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await proc.communicate()
            
            if proc.returncode == 0:
                processed_bytes = temp_output.read_bytes()
                
                # Guardar
                output_filename = f"video_{self.file_cache.get_file_hash(video_bytes)}_{filename}"
                output_path = self.output_dir / output_filename
                output_path.write_bytes(processed_bytes)
                
                # Limpiar
                temp_input.unlink()
                temp_output.unlink()
                
                self.stats['videos_processed'] += 1
                
                logger.info(f"🎬 Video procesado: {filename}")
                
                return {
                    'success': True,
                    'filename': filename,
                    'output_path': str(output_path),
                    'original_size': len(video_bytes),
                    'compressed_size': len(processed_bytes)
                }
            
            return {'success': False, 'error': 'FFmpeg falló'}
            
        except Exception as e:
            logger.error(f"Error procesando video: {e}")
            return {'success': False, 'error': str(e)}
    
    async def process_pdf(self, pdf_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Procesar PDF"""
        if not PYMUPDF_AVAILABLE:
            return {'success': False, 'error': 'PyMuPDF no disponible'}
        
        try:
            pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
            page_count = len(pdf_document)
            
            # Guardar
            output_filename = f"pdf_{self.file_cache.get_file_hash(pdf_bytes)}_{filename}"
            output_path = self.output_dir / output_filename
            output_path.write_bytes(pdf_bytes)
            
            pdf_document.close()
            
            self.stats['pdfs_processed'] += 1
            
            logger.info(f"📄 PDF procesado: {filename} ({page_count} páginas)")
            
            return {
                'success': True,
                'filename': filename,
                'output_path': str(output_path),
                'page_count': page_count,
                'file_size': len(pdf_bytes)
            }
            
        except Exception as e:
            logger.error(f"Error procesando PDF: {e}")
            return {'success': False, 'error': str(e)}
    
    async def process_audio(self, audio_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Procesar audio"""
        try:
            # Guardar temporalmente
            temp_input = self.temp_dir / f"input_{filename}"
            temp_output = self.temp_dir / f"output_{filename}.mp3"
            
            temp_input.write_bytes(audio_bytes)
            
            # Convertir a MP3
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
            
            await proc.communicate()
            
            if proc.returncode == 0:
                processed_bytes = temp_output.read_bytes()
                
                # Guardar
                output_filename = f"audio_{self.file_cache.get_file_hash(audio_bytes)}_{filename}.mp3"
                output_path = self.output_dir / output_filename
                output_path.write_bytes(processed_bytes)
                
                # Limpiar
                temp_input.unlink()
                temp_output.unlink()
                
                self.stats['audios_processed'] += 1
                
                logger.info(f"🎵 Audio procesado: {filename}")
                
                return {
                    'success': True,
                    'filename': filename,
                    'output_path': str(output_path),
                    'original_size': len(audio_bytes),
                    'format': 'mp3'
                }
            
            return {'success': False, 'error': 'FFmpeg falló'}
            
        except Exception as e:
            logger.error(f"Error procesando audio: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas"""
        return {
            'processor_stats': self.stats,
            'directories': {
                'cache': str(self.cache_dir),
                'temp': str(self.temp_dir),
                'output': str(self.output_dir)
            }
        }


# Función helper
def create_file_processor() -> FileProcessorEnhanced:
    """Factory function para crear FileProcessorEnhanced"""
    return FileProcessorEnhanced()


# Exportar clases
__all__ = ['FileCache', 'FileProcessorEnhanced', 'create_file_processor']
'''
    
    return code


def verify_fix():
    """Verificar que el fix funcionó"""
    print("\n🔍 Verificando la reparación...")
    
    try:
        # Intentar importar
        import sys
        if '.' not in sys.path:
            sys.path.insert(0, '.')
        
        # Forzar recarga del módulo
        if 'app.services.file_processor' in sys.modules:
            del sys.modules['app.services.file_processor']
        
        from app.services.file_processor import FileCache, FileProcessorEnhanced
        
        print("   ✅ FileCache importado correctamente")
        print("   ✅ FileProcessorEnhanced importado correctamente")
        
        # Verificar que se puede crear instancia
        processor = FileProcessorEnhanced()
        print("   ✅ FileProcessorEnhanced instanciado correctamente")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Error de importación: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def main():
    """Función principal"""
    print("\n🔧 REPARADOR DE FILE PROCESSOR")
    print("="*60)
    print("Este script:")
    print("  ✅ Restaura FileProcessorEnhanced")
    print("  ✅ Aplica fix de Unicode al cache")
    print("  ✅ Limpia archivos corruptos")
    print("  ✅ Crea estructura de directorios")
    print("="*60)
    
    # Aplicar el fix
    if apply_fix():
        # Verificar
        if verify_fix():
            print("\n" + "="*60)
            print("🎉 REPARACIÓN EXITOSA!")
            print("="*60)
            print("\n📌 Próximos pasos:")
            print("   1. Reinicia los servicios:")
            print("      python scripts/start_all.py")
            print("\n   2. O ejecuta el servicio principal:")
            print("      python main.py")
            print("\n✅ Tu bot ahora debería replicar mensajes correctamente")
        else:
            print("\n⚠️ El código se actualizó pero hay problemas de importación")
            print("   Intenta reiniciar tu terminal o IDE")
    else:
        print("\n❌ No se pudo aplicar la reparación")


if __name__ == "__main__":
    main()