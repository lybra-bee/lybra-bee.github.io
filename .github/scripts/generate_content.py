#!/usr/bin/env python3
import os
import json
import yaml
import logging
import requests
import base64
import shutil
from datetime import datetime
from slugify import slugify

# ====== Настройки ======
STATIC_IMAGES_DIR = "static/images/posts"
ASSETS_GALLERY_DIR = "assets/gallery"
GALLERY_YAML = "data/gallery.yaml"
POSTS_DIR = "content/posts"

os.makedirs(STATIC_IMAGES_DIR, exist_ok=True)
os.makedirs(ASSETS_GALLERY_DIR, exist_ok=True)
os.makedirs(POSTS_DIR, exist_ok=True)
os.makedirs(os.path.dirname(GALLERY_YAML), exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ====== Функции ======

def generate_title():
    """Генерация заголовка статьи через OpenRouter API"""
    prompt = "Придумай интересный заголовок для статьи об искусственном интеллекте, нейросетях, высоких технологиях, их применении в медицине, строительстве, обучении, бизнесе и создании нейросетевых проектов."
    response = requests.post(
        "https://api.openrouter.ai/v1/generate",
        headers={"Authorization": f"Bearer {os.environ.get('OPENROUTER_API_KEY')}"},
        json={"prompt": prompt, "max_tokens": 20}
    )
    title = response.json().get("text", "Новая статья").strip()
    logging.info(f"Заголовок: {title}")
    return title

def generate_text(title):
    """Генерация текста статьи через OpenRouter API"""
    prompt = f"Напиши подробную, уникальную статью по заголовку: {title}"
    response = requests.post(
        "https://api.openrouter.ai/v1/generate",
        headers={"Authorization": f"Bearer {os.environ.get('OPENROUTER_API_KEY')}"},
        json={"prompt": prompt, "max_tokens": 800}
    )
    text = response.json().get("text", "Статья пока пуста").strip()
    return text

def generate_image(title):
    """Генерация изображения (пример с заглушкой)"""
    prompt = f"{title}, digital art, high quality"
    # Здесь подставьте вызов реального API генерации изображений
    image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAJYAAACWCAYAAAB34vZJAAA..."  # пример
    filename = slugify(title) + ".png"
    filepath = os.path.join(STATIC_IMAGES_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(base64.b64decode(image_base64))
    logging.info(f"Сгенерировано изображение: {filepath}")
    return filename

def update_gallery_from_assets():
    """Сканируем static/images/posts, копируем новые файлы в assets/gallery и обновляем gallery.yaml"""
    gallery = []
    if os.path.exists(GALLERY_YAML):
        with open(GALLERY_YAML, "r", encoding="utf-8") as f:
            gallery = yaml.safe_load(f) or []

    existing_files = {item['src'] for item in gallery}

    for filename in os.listdir(STATIC_IMAGES_DIR):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.svg', '.gif')):
            src_path = os.path.join(STATIC_IMAGES_DIR, filename)
            dest_path = os.path.join(ASSETS_GALLERY_DIR, filename)
            if not os.path.exists(dest_path):
                shutil.copy2(src_path, dest_path)
                logging.info(f"Копия изображения создана: {dest_path}")

            src_web = f"/images/posts/{filename}"
            if src_web not in existing_files:
                gallery.append({
                    "src": src_web,
                    "title": filename.replace("-", " ").replace(".png", "").replace(".jpg", "").title(),
                    "alt": filename.replace("-", " ").replace(".png", "").replace(".jpg", "").title(),
                    "date": datetime.now().strftime("%Y-%m-%d")
                })

    with open(GALLERY_YAML, "w", encoding="utf-8") as f:
        yaml.dump(gallery, f, allow_unicode=True)
    logging.info(f"Галерея обновлена: {len(gallery)} элементов")

def save_article(title, text, img_filename):
    """Сохраняем статью в content/posts"""
    slug = slugify(title)
    post_file = os.path.join(POSTS_DIR, f"{slug}.md")
    front_matter = f"""---
title: "{title}"
date: "{date
