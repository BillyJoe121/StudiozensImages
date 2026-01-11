"""
Script para optimizar imágenes y videos de Servicios a ServiciosOptimized.
VERSION AGRESIVA: Máxima compresión manteniendo calidad aceptable para web.

Requisitos:
    pip install Pillow

Para videos se requiere FFmpeg instalado en el sistema.
"""

import os
import shutil
import subprocess
from pathlib import Path
from PIL import Image

# Configuración
SOURCE_DIR = Path(__file__).parent / "Servicios"
OUTPUT_DIR = Path(__file__).parent / "ServiciosOptimized"

# ============ CONFIGURACIÓN AGRESIVA ============
# Imágenes: WebP con calidad 75%, max 1920px
IMAGE_QUALITY = 75
IMAGE_MAX_WIDTH = 1920
IMAGE_MAX_HEIGHT = 1080
CONVERT_TO_WEBP = True  # Convertir a WebP para mejor compresión

# Videos: CRF 28, max 720p
VIDEO_CRF = 28  # Mayor = menor calidad pero más compresión (18-28 rango útil)
VIDEO_MAX_HEIGHT = 720  # Escalar a 720p max
VIDEO_AUDIO_BITRATE = "96k"  # Reducir bitrate de audio
# ================================================

# Extensiones soportadas
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.JPG', '.JPEG', '.PNG', '.WEBP'}
VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.MP4', '.MOV', '.AVI', '.MKV'}


def get_file_size_mb(file_path: Path) -> float:
    """Retorna el tamaño del archivo en MB."""
    return file_path.stat().st_size / (1024 * 1024)


def optimize_image(source_path: Path, output_path: Path) -> dict:
    """
    Optimiza una imagen con compresión agresiva.
    Convierte a WebP y redimensiona si es necesario.
    """
    result = {
        'source': source_path,
        'output': output_path,
        'original_size_mb': get_file_size_mb(source_path),
        'success': False,
        'error': None
    }
    
    try:
        # Crear directorio de salida si no existe
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Abrir imagen
        with Image.open(source_path) as img:
            # Convertir a RGB (WebP no soporta todos los modos)
            if img.mode in ('RGBA', 'P'):
                # Crear fondo blanco para imágenes con transparencia
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Redimensionar si es más grande que el límite
            original_size = img.size
            if img.width > IMAGE_MAX_WIDTH or img.height > IMAGE_MAX_HEIGHT:
                # Calcular nuevo tamaño manteniendo proporción
                ratio = min(IMAGE_MAX_WIDTH / img.width, IMAGE_MAX_HEIGHT / img.height)
                new_size = (int(img.width * ratio), int(img.height * ratio))
                img = img.resize(new_size, Image.LANCZOS)
            
            # Determinar formato de salida
            if CONVERT_TO_WEBP:
                # Cambiar extensión a .webp
                final_output = output_path.with_suffix('.webp')
                img.save(final_output, 'WEBP', quality=IMAGE_QUALITY, method=6)
            else:
                final_output = output_path
                img.save(final_output, quality=IMAGE_QUALITY, optimize=True)
        
        result['output'] = final_output
        result['optimized_size_mb'] = get_file_size_mb(final_output)
        result['reduction_percent'] = (1 - result['optimized_size_mb'] / result['original_size_mb']) * 100
        result['success'] = True
        result['resized'] = original_size != img.size if 'img' in dir() else False
        
    except Exception as e:
        result['error'] = str(e)
        # Si falla, copiar el archivo original
        shutil.copy2(source_path, output_path)
        result['optimized_size_mb'] = get_file_size_mb(output_path)
        result['reduction_percent'] = 0
    
    return result


def optimize_video(source_path: Path, output_path: Path) -> dict:
    """
    Optimiza un video con compresión agresiva.
    Escala a 720p y usa CRF alto.
    """
    result = {
        'source': source_path,
        'output': output_path,
        'original_size_mb': get_file_size_mb(source_path),
        'success': False,
        'error': None
    }
    
    try:
        # Crear directorio de salida si no existe
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Comando FFmpeg con compresión agresiva
        # -vf scale: escala a 720p manteniendo proporción
        # -crf 28: compresión alta
        # -preset slow: mejor compresión
        cmd = [
            'ffmpeg',
            '-i', str(source_path),
            '-c:v', 'libx264',
            '-crf', str(VIDEO_CRF),
            '-preset', 'slow',
            '-vf', f'scale=-2:{VIDEO_MAX_HEIGHT}:flags=lanczos',  # Escalar a 720p
            '-c:a', 'aac',
            '-b:a', VIDEO_AUDIO_BITRATE,
            '-movflags', '+faststart',
            '-y',
            str(output_path)
        ]
        
        # Ejecutar FFmpeg
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600
        )
        
        if process.returncode != 0:
            raise Exception(f"FFmpeg error: {process.stderr[-500:]}")
        
        result['optimized_size_mb'] = get_file_size_mb(output_path)
        result['reduction_percent'] = (1 - result['optimized_size_mb'] / result['original_size_mb']) * 100
        result['success'] = True
        
    except FileNotFoundError:
        result['error'] = "FFmpeg no encontrado"
        shutil.copy2(source_path, output_path)
        result['optimized_size_mb'] = get_file_size_mb(output_path)
        result['reduction_percent'] = 0
        
    except Exception as e:
        result['error'] = str(e)
        shutil.copy2(source_path, output_path)
        result['optimized_size_mb'] = get_file_size_mb(output_path)
        result['reduction_percent'] = 0
    
    return result


def main():
    """Función principal que procesa todos los archivos."""
    print("=" * 60)
    print("🚀 OPTIMIZADOR AGRESIVO - Servicios → ServiciosOptimized")
    print("=" * 60)
    print(f"\n📂 Origen: {SOURCE_DIR}")
    print(f"📂 Destino: {OUTPUT_DIR}")
    print(f"\n⚙️  Configuración AGRESIVA:")
    print(f"   🖼️  Imágenes:")
    print(f"      - Formato: {'WebP' if CONVERT_TO_WEBP else 'Original'}")
    print(f"      - Calidad: {IMAGE_QUALITY}%")
    print(f"      - Max resolución: {IMAGE_MAX_WIDTH}x{IMAGE_MAX_HEIGHT}")
    print(f"   🎬 Videos:")
    print(f"      - CRF: {VIDEO_CRF}")
    print(f"      - Max altura: {VIDEO_MAX_HEIGHT}p")
    print(f"      - Audio: {VIDEO_AUDIO_BITRATE}")
    print("\n" + "-" * 60)
    
    if not SOURCE_DIR.exists():
        print(f"❌ Error: No se encontró el directorio '{SOURCE_DIR}'")
        return
    
    # Crear directorio de salida
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Estadísticas
    stats = {
        'images': {'processed': 0, 'original_size': 0, 'optimized_size': 0, 'errors': 0},
        'videos': {'processed': 0, 'original_size': 0, 'optimized_size': 0, 'errors': 0}
    }
    
    # Recorrer todos los archivos
    all_files = list(SOURCE_DIR.rglob('*'))
    files_to_process = [f for f in all_files if f.is_file()]
    
    print(f"\n📋 Encontrados {len(files_to_process)} archivos para procesar\n")
    
    for i, source_file in enumerate(files_to_process, 1):
        # Calcular ruta de salida (misma estructura)
        relative_path = source_file.relative_to(SOURCE_DIR)
        output_file = OUTPUT_DIR / relative_path
        
        print(f"[{i}/{len(files_to_process)}] Procesando: {relative_path}")
        
        if source_file.suffix in IMAGE_EXTENSIONS:
            result = optimize_image(source_file, output_file)
            category = 'images'
        elif source_file.suffix in VIDEO_EXTENSIONS:
            result = optimize_video(source_file, output_file)
            category = 'videos'
        else:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_file, output_file)
            print(f"   ⏭️  Copiado sin cambios")
            continue
        
        # Actualizar estadísticas
        stats[category]['processed'] += 1
        stats[category]['original_size'] += result['original_size_mb']
        stats[category]['optimized_size'] += result['optimized_size_mb']
        
        if result['success']:
            print(f"   ✅ {result['original_size_mb']:.2f} MB → {result['optimized_size_mb']:.2f} MB "
                  f"({result['reduction_percent']:.1f}% reducción)")
        else:
            stats[category]['errors'] += 1
            print(f"   ⚠️  Error: {result['error']}")
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📊 RESUMEN FINAL")
    print("=" * 60)
    
    for category, data in stats.items():
        if data['processed'] > 0:
            emoji = "🖼️ " if category == 'images' else "🎬"
            print(f"\n{emoji} {category.upper()}:")
            print(f"   Procesados: {data['processed']}")
            print(f"   Tamaño original: {data['original_size']:.2f} MB")
            print(f"   Tamaño optimizado: {data['optimized_size']:.2f} MB")
            if data['original_size'] > 0:
                reduction = (1 - data['optimized_size'] / data['original_size']) * 100
                print(f"   Reducción: {reduction:.1f}%")
            if data['errors'] > 0:
                print(f"   ⚠️  Errores: {data['errors']}")
    
    total_original = sum(d['original_size'] for d in stats.values())
    total_optimized = sum(d['optimized_size'] for d in stats.values())
    
    print(f"\n📦 TOTAL:")
    print(f"   Original: {total_original:.2f} MB")
    print(f"   Optimizado: {total_optimized:.2f} MB")
    if total_original > 0:
        print(f"   🎯 Ahorro: {total_original - total_optimized:.2f} MB ({(1 - total_optimized/total_original)*100:.1f}%)")
    
    print(f"\n✨ Archivos guardados en: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
