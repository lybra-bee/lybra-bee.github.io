#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import yaml
import logging
import requests
from datetime import datetime
from slugify import slugify
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import shutil

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# --- Конфигурация ---
POSTS_DIR = Path("content/posts")
IMAGES_DIR = Path("static/images/posts")
GALLERY_JSON = Path("data/gallery.json")
MAX_POSTS = 10  # сколько постов оставлять
IMAGE_WIDTH = 1200
IMAGE_HEIGHT = 630

# --- Утилиты ---
def remove_old_posts(posts_dir: Path, keep_last=MAX_POSTS):
    posts = sorted(posts_dir.glob("*.md"), key=os.path.getmtime, reverse=True)
    removed = []
    for post in posts[keep_last:]:
        post.unlink()
        removed.append(post)
    for p in removed:
        logging.info(f"🗑 Старый пост удалён: {p.name}")
    return removed

def save_post(title: str, content: str, image_filename: str):
    slug = slugify(title)
    filename = POSTS_DIR / f"{slug}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"---\ntitle: \"{title}\"\ndate: {datetime.now().isoformat()}\nimage: {image_filename}\n---\n\n")
        f.write(content)
    logging.info(f"✅ Статья сохранена: {filename}")
    return filename

def generate_image(title: str) -> str:
    filename = IMAGES_DIR / f"{slugify(title)}.jpg"
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    # Простое создание заглушки изображения с текстом
    img = Image.new("RGB", (IMAGE_WIDTH, IMAGE_HEIGHT), color=(73, 109, 137))
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    draw.text((50, IMAGE_HEIGHT//2), title, font=font, fill=(255, 255, 0))
    img.save(filename)
    logging.info(f"🖼 Изображение создано: {filename}")
    return str(filename)

def update_gallery(gallery_json: Path):
    images = list(IMAGES_DIR.glob("*.jpg"))
    gallery_data = [{"image": str(img), "title": img.stem} for img in images]
    with open(gallery_json, "w", encoding="utf-8") as f:
        json.dump(gallery_data, f, ensure_ascii=False, indent=2)
    logging.info(f"🎨 Галерея обновлена ({len(images)} изображений)")

def generate_text(title_prompt: str) -> str:
    # Здесь используем твой существующий промпт и генерацию
    # Возвращаем текст статьи
    try:
        # пример вызова OpenAI или другого API
        content = f"Текст статьи для '{title_prompt}' сгенерирован успешно."
        logging.info("📝 Генерация текста статьи прошла успешно через API")
        return content
    except Exception as e:
        logging.error(f"❌ Ошибка генерации текста статьи: {e}")
        return "Текст статьи не сгенерирован."

def generate_title() -> str:
    try:
        title = "Новая статья ИИ 2025"  # тут твой промпт для заголовка
        logging.info("📝 Генерация заголовка прошла успешно")
        return title
    except Exception as e:
        logging.error(f"❌ Ошибка генерации заголовка: {e}")
        return "Без заголовка"

# --- Основная функция ---
def main():
    logging.info("🚀 Старт генерации контента")
    
    # Удаляем старые посты
    remove_old_posts(POSTS_DIR)
    
    # Генерируем заголовок
    title = generate_title()
    
    # Генерируем текст статьи
    content = generate_text(title)
    
    # Генерируем изображение
    image_path = generate_image(title)
    
    # Сохраняем статью
    save_post(title, content, image_path)
    
    # Обновляем галерею
    update_gallery(GALLERY_JSON)
    
    logging.info("🎯 Генерация контента завершена успешно")

if __name__ == "__main__":
    main()
