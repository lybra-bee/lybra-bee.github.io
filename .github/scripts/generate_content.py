#!/usr/bin/env python3
import os
import json
import requests
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

BASE_DIR = Path(__file__).parent.parent
CONTENT_DIR = BASE_DIR / "content/posts"
GALLERY_DIR = BASE_DIR / "static/images/gallery"

# Проверка и создание директорий
if GALLERY_DIR.exists() and not GALLERY_DIR.is_dir():
    logging.warning(f"{GALLERY_DIR} существует, но это не директория. Удаляем и создаём папку.")
    GALLERY_DIR.unlink()
GALLERY_DIR.mkdir(parents=True, exist_ok=True)
CONTENT_DIR.mkdir(parents=True, exist_ok=True)

# Генерация статьи через фолбек API
def generate_article():
    logging.info("📝 Генерация статьи через публичный фолбек API")
    try:
        # Используем публичный API для генерации текста
        response = requests.get("https://api.quotable.io/random")
        data = response.json()
        content = f"{data.get('content', 'Это пример статьи о нейросетях и высоких технологиях.')}"
        title = content.split('.')[0][:50]  # берем первые 50 символов как заголовок
        return title, content
    except Exception as e:
        logging.error(f"Ошибка генерации статьи: {e}")
        title = "Пример статьи"
        content = "Это пример статьи о нейросетях и высоких технологиях."
        return title, content

# Сохранение статьи
def save_article(title, content):
    filename = f"{title.replace(' ', '-').lower()[:50]}.md"
    filepath = CONTENT_DIR / filename
    md_content = f"""---
title: "{title}"
date: {datetime.now().isoformat()}
---

{content}
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(md_content)
    logging.info(f"📄 Статья сохранена: {filepath.name}")

# Удаляем старые статьи, оставляем последние 5
def cleanup_articles():
    files = sorted(CONTENT_DIR.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True)
    for f in files[5:]:
        f.unlink()
        logging.info(f"🧹 Удалена старая статья: {f.name}")

def main():
    title, content = generate_article()
    save_article(title, content)
    cleanup_articles()

if __name__ == "__main__":
    main()
