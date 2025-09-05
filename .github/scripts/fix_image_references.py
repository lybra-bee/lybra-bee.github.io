#!/usr/bin/env python3
import os
import re
import glob
from pathlib import Path

def generate_slug(text):
    """Генерация slug на основе заголовка"""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = text.replace(' ', '-')
    text = re.sub(r'-+', '-', text)
    return text[:50]

def fix_image_references():
    """Исправляет ссылки на изображения в статьях"""
    posts_dir = "content/posts"
    images_dir = "assets/images/posts"
    
    print("🔍 Поиск статей и изображений...")
    
    # Создаем mapping: имя файла -> путь к изображению
    image_mapping = {}
    for img_path in glob.glob(f"{images_dir}/*.png"):
        stem = Path(img_path).stem
        image_mapping[stem] = f"/assets/images/posts/{Path(img_path).name}"
    
    print(f"📁 Найдено {len(image_mapping)} изображений")
    
    # Обрабатываем статьи
    updated_count = 0
    for post_file in glob.glob(f"{posts_dir}/*.md"):
        try:
            with open(post_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            post_stem = Path(post_file).stem
            
            # Ищем изображение с таким же именем
            if post_stem in image_mapping:
                image_path = image_mapping[post_stem]
                
                # Обновляем или добавляем поле image
                if 'image:' in content:
                    new_content = re.sub(
                        r'image:\s*["\'].*?["\']', 
                        f'image: "{image_path}"', 
                        content
                    )
                else:
                    # Добавляем после первой строки с ---
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if line.strip() == '---':
                            lines.insert(i + 1, f'image: "{image_path}"')
                            break
                    new_content = '\n'.join(lines)
                
                if new_content != content:
                    with open(post_file, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"✅ Исправлено: {post_stem} -> {image_path}")
                    updated_count += 1
                else:
                    print(f"✓ Уже правильно: {post_stem}")
            else:
                print(f"⚠️ Нет изображения для: {post_stem}")
                
        except Exception as e:
            print(f"❌ Ошибка в {post_file}: {e}")
    
    print(f"🎉 Обновлено статей: {updated_count}")

if __name__ == "__main__":
    fix_image_references()
