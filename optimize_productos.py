"""
Script para optimizar imágenes de Productos a ProductosOptimized.
VERSION AGRESIVA: Máxima compresión manteniendo calidad aceptable para web.
"""

import os
import shutil
from pathlib import Path
from PIL import Image

# Configuración
SOURCE_DIR = Path(__file__).parent / "Productos"
OUTPUT_DIR = Path(__file__).parent / "ProductosOptimized"

# ============ CONFIGURACIÓN AGRESIVA ============
IMAGE_QUALITY = 75
IMAGE_MAX_WIDTH = 1920
IMAGE_MAX_HEIGHT = 1080
CONVERT_TO_WEBP = True
# ================================================

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.JPG', '.JPEG', '.PNG', '.WEBP'}


def get_file_size_mb(file_path: Path) -> float:
    return file_path.stat().st_size / (1024 * 1024)


def optimize_image(source_path: Path, output_path: Path) -> dict:
    result = {
        'source': source_path,
        'output': output_path,
        'original_size_mb': get_file_size_mb(source_path),
        'success': False,
        'error': None
    }
    
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with Image.open(source_path) as img:
            if img.mode in ('RGBA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            original_size = img.size
            if img.width > IMAGE_MAX_WIDTH or img.height > IMAGE_MAX_HEIGHT:
                ratio = min(IMAGE_MAX_WIDTH / img.width, IMAGE_MAX_HEIGHT / img.height)
                new_size = (int(img.width * ratio), int(img.height * ratio))
                img = img.resize(new_size, Image.LANCZOS)
            
            if CONVERT_TO_WEBP:
                final_output = output_path.with_suffix('.webp')
                img.save(final_output, 'WEBP', quality=IMAGE_QUALITY, method=6)
            else:
                final_output = output_path
                img.save(final_output, quality=IMAGE_QUALITY, optimize=True)
        
        result['output'] = final_output
        result['optimized_size_mb'] = get_file_size_mb(final_output)
        result['reduction_percent'] = (1 - result['optimized_size_mb'] / result['original_size_mb']) * 100
        result['success'] = True
        
    except Exception as e:
        result['error'] = str(e)
        shutil.copy2(source_path, output_path)
        result['optimized_size_mb'] = get_file_size_mb(output_path)
        result['reduction_percent'] = 0
    
    return result


def main():
    print("=" * 60)
    print("🚀 OPTIMIZADOR - Productos → ProductosOptimized")
    print("=" * 60)
    print(f"\n📂 Origen: {SOURCE_DIR}")
    print(f"📂 Destino: {OUTPUT_DIR}")
    print(f"\n⚙️  Configuración:")
    print(f"   - Formato: {'WebP' if CONVERT_TO_WEBP else 'Original'}")
    print(f"   - Calidad: {IMAGE_QUALITY}%")
    print(f"   - Max resolución: {IMAGE_MAX_WIDTH}x{IMAGE_MAX_HEIGHT}")
    print("\n" + "-" * 60)
    
    if not SOURCE_DIR.exists():
        print(f"❌ Error: No se encontró el directorio '{SOURCE_DIR}'")
        return
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    stats = {'processed': 0, 'original_size': 0, 'optimized_size': 0, 'errors': 0}
    
    all_files = list(SOURCE_DIR.rglob('*'))
    files_to_process = [f for f in all_files if f.is_file() and f.suffix in IMAGE_EXTENSIONS]
    
    print(f"\n📋 Encontradas {len(files_to_process)} imágenes para procesar\n")
    
    for i, source_file in enumerate(files_to_process, 1):
        relative_path = source_file.relative_to(SOURCE_DIR)
        output_file = OUTPUT_DIR / relative_path
        
        print(f"[{i}/{len(files_to_process)}] {relative_path}")
        
        result = optimize_image(source_file, output_file)
        
        stats['processed'] += 1
        stats['original_size'] += result['original_size_mb']
        stats['optimized_size'] += result['optimized_size_mb']
        
        if result['success']:
            print(f"   ✅ {result['original_size_mb']:.2f} MB → {result['optimized_size_mb']:.2f} MB "
                  f"({result['reduction_percent']:.1f}% reducción)")
        else:
            stats['errors'] += 1
            print(f"   ⚠️  Error: {result['error']}")
    
    print("\n" + "=" * 60)
    print("📊 RESUMEN FINAL")
    print("=" * 60)
    print(f"\n🖼️  IMÁGENES:")
    print(f"   Procesadas: {stats['processed']}")
    print(f"   Tamaño original: {stats['original_size']:.2f} MB")
    print(f"   Tamaño optimizado: {stats['optimized_size']:.2f} MB")
    if stats['original_size'] > 0:
        reduction = (1 - stats['optimized_size'] / stats['original_size']) * 100
        print(f"   🎯 Reducción: {reduction:.1f}%")
    if stats['errors'] > 0:
        print(f"   ⚠️  Errores: {stats['errors']}")
    
    print(f"\n✨ Archivos guardados en: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
