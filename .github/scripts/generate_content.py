#!/usr/bin/env python3
import os
import json
import requests
import random
from datetime import datetime
import base64
import time
import logging
from PIL import Image, ImageDraw, ImageFont
import re
import shutil
import yaml

# ===== ЛОГИРОВАНИЕ =====
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ===== УТИЛИТЫ =====
def generate_slug(title):
    slug = title.lower()
    slug = slug.replace(' ', '-')
    slug = ''.join(c for c in slug if c.isalnum() or c=='-')
    return slug

def save_image_bytes(image_data, title):
    os.makedirs("assets/images/posts", exist_ok=True)
    slug = generate_slug(title)
    filename = f"assets/images/posts/{slug}.png"
    with open(filename, "wb") as f:
        f.write(image_data)
    logger.info(f"Изображение сохранено в assets: {filename}")
    return f"/images/posts/{slug}.png"

def generate_placeholder_image(title):
    os.makedirs("assets/images/posts", exist_ok=True)
    slug = generate_slug(title)
    filename = f"assets/images/posts/{slug}.png"
    
    img = Image.new('RGB', (800, 400), color='#0f172a')
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 30)
    except:
        font = ImageFont.load_default()
    
    bbox = draw.textbbox((0, 0), title, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (800 - text_width) / 2
    y = (400 - text_height) / 2
    draw.text((x, y), title, fill='white', font=font)
    img.save(filename)
    logger.info(f"Placeholder создан: {filename}")
    return f"/images/posts/{slug}.png"

def sanitize_title(title):
    return re.sub(r'[^\w\s\-]', '', title)

def generate_frontmatter(title, content, model, image_path):
    sanitized_title = sanitize_title(title)
    frontmatter = {
        'title': sanitized_title,
        'date': datetime.now().isoformat(),
        'draft': False,
        'image': image_path,
        'model': model,
        'categories': ['AI'],
        'tags': ['автоматическая генерация', 'искусственный интеллект']
    }
    return f"---\n{yaml.dump(frontmatter, allow_unicode=True)}---\n\n{content}"

# ===== Генерация статьи (заглушка для примера) =====
def generate_article_prompt():
    trends = ["машинное обучение", "нейросети", "генеративный AI", "компьютерное зрение", "глубокое обучение"]
    domains = ["веб-разработка", "мобильные приложения", "облачные вычисления", "анализ данных", "кибербезопасность"]
    trend = random.choice(trends)
    domain = random.choice(domains)
    prompt = f"Напиши развернутую статью на русском языке на тему '{trend} в {domain}'."
    return prompt, f"{trend} в {domain}"

def generate_fallback_content(prompt):
    return f"# {prompt}\n\nСтатья сгенерирована автоматически."

def generate_article_content(prompt):
    # Здесь можно подключить реальные нейросети
    return generate_fallback_content(prompt), "fallback"

# ===== Генерация изображения (заглушка) =====
def generate_article_image(title):
    return generate_placeholder_image(title)

# ===== Копирование изображений в static =====
def copy_images_to_static():
    os.makedirs("static/images/posts", exist_ok=True)
    assets_dir = "assets/images/posts"
    if not os.path.exists(assets_dir):
        return False
    for f_name in os.listdir(assets_dir):
        src = os.path.join(assets_dir, f_name)
        dst = os.path.join("static/images/posts", f_name)
        shutil.copy2(src, dst)
    return True

# ===== Обновление данных галереи =====
def update_hugo_data():
    gallery_images = []
    target_dir = "static/images/posts"
    if os.path.exists(target_dir):
        image_files = [f for f in os.listdir(target_dir) if f.lower().endswith(('.png','.jpg','.jpeg'))]
        for img_file in image_files:
            name = os.path.splitext(img_file)[0].replace('-', ' ').title()
            gallery_images.append({
                'src': f"/images/posts/{img_file}",
                'alt': f"AI generated image: {name}",
                'title': name,
                'filename': img_file
            })
    if not gallery_images:
        gallery_images.append({
            'src': '/images/placeholder.jpg',
            'alt': 'AI generated images will appear here soon',
            'title': 'Gallery Placeholder',
            'filename': 'placeholder.jpg'
        })
    os.makedirs("data", exist_ok=True)
    with open("data/gallery.yaml", "w", encoding="utf-8") as f:
        yaml.dump(gallery_images, f, allow_unicode=True, default_flow_style=False)
    with open("data/gallery.json", "w", encoding="utf-8") as f:
        json.dump(gallery_images, f, ensure_ascii=False, indent=2)
    logger.info(f"✅ Данные галереи обновлены: {len(gallery_images)} изображений")

# ===== Генерация контента =====
def generate_content():
    logger.info("=== НАЧАЛО ГЕНЕРАЦИИ КОНТЕНТА ===")
    os.makedirs("content/posts", exist_ok=True)
    
    # Генерация новой статьи
    prompt, topic = generate_article_prompt()
    content, model = generate_article_content(prompt)
    title = topic
    image_path = generate_article_image(title)
    
    slug = title.lower().replace(' ','-')
    filename = f"content/posts/{datetime.now().strftime('%Y-%m-%d')}-{slug}.md"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(generate_frontmatter(title, content, model, image_path))
    
    # Копируем изображения и обновляем галерею
    copy_images_to_static()
    update_hugo_data()
    
    logger.info(f"✅ Статья создана: {filename}")
    return filename

if __name__ == "__main__":
    generate_content()
