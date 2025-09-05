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
    
    # Получаем все существующие изображения
    existing_images = {}
    for img_path in glob.glob(f"{images_dir}/*.png"):
        img_name = Path(img_path).stem
        existing_images[img_name] = img_path
        print(f"📁 Найдено изображение: {img_name}")
    
    # Обрабатываем каждую статью
    for post_file in glob.glob(f"{posts_dir}/*.md"):
        try:
            with open(post_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Извлекаем заголовок статьи
            title_match = re.search(r'title:\s*["\'](.*?)["\']', content)
            if not title_match:
                print(f"⚠️ Не найден заголовок в {post_file}")
                continue
                
            title = title_match.group(1)
            post_slug = generate_slug(title)
            post_name = Path(post_file).stem
            
            print(f"📄 Обработка статьи: {post_name} -> '{title}'")
            
            # Ищем соответствующее изображение
            matching_image = None
            possible_names = [post_slug, post_name, post_name.replace('-', ' ')]
            
            for name in possible_names:
                if name in existing_images:
                    matching_image = existing_images[name]
                    break
            
            if matching_image:
                image_path = f"/assets/images/posts/{Path(matching_image).name}"
                print(f"🖼️ Найдено изображение: {image_path}")
                
                # Обновляем frontmatter
                if 'image:' in content:
                    # Заменяем существующее изображение
                    new_content = re.sub(
                        r'image:\s*["\'].*?["\']', 
                        f'image: "{image_path}"', 
                        content
                    )
                else:
                    # Добавляем новое поле image
                    new_content = content.replace('title:', f'image: "{image_path}"\ntitle:')
                
                # Сохраняем изменения
                if new_content != content:
                    with open(post_file, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"✅ Исправлено: {post_file}")
                else:
                    print(f"✅ Уже правильно: {post_file}")
                    
            else:
                print(f"⚠️ Не найдено изображение для: {post_name}")
                
        except Exception as e:
            print(f"❌ Ошибка обработки {post_file}: {e}")

if __name__ == "__main__":
    fix_image_references()
