#!/usr/bin/env python3
import os
import json
import requests
import random
from datetime import datetime
import shutil
import yaml
import logging
from slugify import slugify

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Пути
POSTS_DIR = "content/posts"
IMAGES_DIR = "static/images/posts"
GALLERY_YAML = "data/gallery.yaml"
GALLERY_JSON = "data/gallery.json"

# Количество последних статей, которые оставляем
KEEP_LAST_N = 5

# Примеры тегов
TAGS = ["ai", "tech", "нейросети"]

# Заглушка для изображений
PLACEHOLDER_IMAGE = "static/images/placeholder.jpg"

# ------------------------
# Утилиты
# ------------------------

def save_article(title, text):
    slug = slugify(title)
    filename = os.path.join(POSTS_DIR, f"{slug}.md")
    logging.info(f"💾 Сохраняем статью в {filename}")
    
    # Экранируем кавычки и убираем переносы строк
    safe_title = title.replace('"', '\\"').replace('\n', ' ').strip()
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(
            f"---\n"
            f"title: \"{safe_title}\"\n"
            f"date: '{datetime.now().strftime('%Y-%m-%d')}'\n"
            f"slug: {slug}\n"
            f"tags: {json.dumps(TAGS)}\n"
            f"---\n\n"
            f"{text}\n"
        )
    return filename

def update_gallery():
    """Создаём галерею на основе всех изображений в static/images/posts"""
    gallery_items = []
    for filename in sorted(os.listdir(IMAGES_DIR)):
        if not filename.lower().endswith((".jpg", ".jpeg", ".png", ".svg")):
            continue
        title = os.path.splitext(filename)[0].replace("-", " ").capitalize()
        gallery_items.append({
            "src": f"/images/posts/{filename}",
            "title": title,
            "alt": title,
            "date": datetime.now().strftime("%Y-%m-%d")
        })
    
    # Сохраняем YAML
    with open(GALLERY_YAML, "w", encoding="utf-8") as f:
        yaml.safe_dump(gallery_items, f, allow_unicode=True)
    
    # Сохраняем JSON
    with open(GALLERY_JSON, "w", encoding="utf-8") as f:
        json.dump(gallery_items, f, ensure_ascii=False, indent=2)

    logging.info(f"🖼 Галерея обновлена: {len(gallery_items)} элементов")

def cleanup_old_articles():
    """Удаляем старые статьи, оставляем только последние KEEP_LAST_N"""
    posts = sorted(
        [f for f in os.listdir(POSTS_DIR) if f.endswith(".md")],
        key=lambda x: os.path.getmtime(os.path.join(POSTS_DIR, x)),
        reverse=True
    )
    to_delete = posts[KEEP_LAST_N:]
    for f in to_delete:
        os.remove(os.path.join(POSTS_DIR, f))
        logging.info(f"🗑 Удалена старая статья: {f}")

# ------------------------
# Генерация статьи
# ------------------------

def generate_article():
    """
    Заглушка генерации текста.
    Здесь можно интегрировать OpenRouter, Groq или любую модель ИИ.
    """
    # Пример заголовка — разнообразный, с применением ИИ в разных сферах
    examples = [
        "Применение искусственного интеллекта в медицине: как ИИ помогает врачам",
        "Создание чат-бота на основе нейросети: пошаговое руководство",
        "Нейросети в строительстве: автоматизация проектирования зданий",
        "Генерация изображений для образовательных материалов с помощью ИИ",
        "Обучение модели машинного обучения на реальных данных",
        "ИИ в финансах: прогнозирование рынка и оценка рисков"
    ]
    title = random.choice(examples)
    text = f"Это статья с заголовком «{title}». Здесь будет содержаться полный текст статьи, с описанием применения технологий и примерами."
    
    return title, text

def main():
    os.makedirs(POSTS_DIR, exist_ok=True)
    os.makedirs(IMAGES_DIR, exist_ok=True)
    
    # 1. Очистка старых статей
    cleanup_old_articles()
    
    # 2. Генерация новой статьи
    title, text = generate_article()
    save_article(title, text)
    
    # 3. Обновление галереи
    update_gallery()

if __name__ == "__main__":
    main()
