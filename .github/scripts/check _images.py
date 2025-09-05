#!/usr/bin/env python3
import glob
from pathlib import Path

def check_images():
    """Простая проверка соответствия"""
    posts = {Path(p).stem for p in glob.glob("content/posts/*.md")}
    images = {Path(p).stem for p in glob.glob("assets/images/posts/*.png")}
    
    print("📊 Статистика:")
    print(f"Статей: {len(posts)}")
    print(f"Изображений: {len(images)}")
    print(f"Соответствий: {len(posts & images)}")
    
    # Несоответствия
    no_image = posts - images
    no_post = images - posts
    
    if no_image:
        print("\n❌ Статьи без изображений:")
        for name in sorted(no_image):
            print(f"  - {name}")
    
    if no_post:
        print("\n⚠️ Изображения без статей:")
        for name in sorted(no_post):
            print(f"  - {name}")

if __name__ == "__main__":
    check_images()
