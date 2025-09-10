#!/usr/bin/env python3
import os
import json
import requests
import logging
import shutil
from datetime import datetime
from pathlib import Path
import yaml

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

STATIC_POSTS_DIR = Path("static/images/posts")
ASSETS_GALLERY_DIR = Path("assets/gallery")
CONTENT_POSTS_DIR = Path("content/posts")
GALLERY_YAML = Path("data/gallery.yaml")
GALLERY_JSON = Path("data/gallery.json")

# === Генерация заголовка ===
def generate_article_title():
    prompt = "Придумай ёмкий заголовок статьи про ИИ и высокие технологии на русском языке"
    try:
        response = requests.post(
            "https://api.openrouter.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"},
            json={"model": "gpt-4.1-mini", "messages":[{"role":"user","content": prompt}]}
        )
        response.raise_for_status()
        title = response.json()["choices"][0]["message"]["content"].strip()
        logging.info("Заголовок сгенерирован через OpenRouter")
        return title
    except Exception as e:
        logging.warning(f"OpenRouter не сработал: {e}, пробуем GROQ...")
    try:
        response = requests.post(
            "https://api.groq.ai/generate",
            headers={"Authorization": f"Bearer {os.environ['GROQ_API_KEY']}"},
            json={"prompt": prompt}
        )
        response.raise_for_status()
        title = response.json()["text"].strip()
        logging.info("Заголовок сгенерирован через GROQ")
        return title
    except Exception as e:
        logging.error(f"GROQ тоже не сработал: {e}")
        return "Автоматически сгенерированная статья"

# === Генерация статьи ===
def generate_article_body(title):
    prompt = f"Напиши структурированную статью по заголовку: '{title}' на русском языке с подзаголовками"
    try:
        response = requests.post(
            "https://api.openrouter.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"},
            json={"model": "gpt-4.1-mini", "messages":[{"role":"user","content": prompt}]}
        )
        response.raise_for_status()
        body = response.json()["choices"][0]["message"]["content"].strip()
        logging.info("Статья сгенерирована через OpenRouter")
        return body
    except Exception as e:
        logging.warning(f"OpenRouter не сработал для статьи: {e}, пробуем GROQ...")
    try:
        response = requests.post(
            "https://api.groq.ai/generate",
            headers={"Authorization": f"Bearer {os.environ['GROQ_API_KEY']}"},
            json={"prompt": prompt}
        )
        response.raise_for_status()
        body = response.json()["text"].strip()
        logging.info("Статья сгенерирована через GROQ")
        return body
    except Exception as e:
        logging.error(f"GROQ тоже не сработал для статьи: {e}")
        return "Контент временно недоступен."

# === Сохраняем статью ===
def save_article(title, body):
    safe_title = "".join(c if c.isalnum() or c in "-_" else "-" for c in title.lower())
    filename = CONTENT_POSTS_DIR / f"{safe_title}.md"
    front_matter = f"""---
title: "{title}"
date: '{datetime.now().strftime('%Y-%m-%d')}'
draft: false
---

{body}
"""
    CONTENT_POSTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(front_matter)
    logging.info(f"Статья сохранена: {filename}")
    return filename

# === Копируем новые изображения из static → assets/gallery, только если их нет ===
def update_gallery_assets():
    ASSETS_GALLERY_DIR.mkdir(parents=True, exist_ok=True)
    for img in STATIC_POSTS_DIR.glob("*.*"):
        dest = ASSETS_GALLERY_DIR / img.name
        if not dest.exists():
            shutil.copy2(img, dest)
            logging.info(f"Скопировано изображение в assets: {img.name}")

# === Обновляем data/gallery.yaml и .json ===
def update_gallery_data():
    gallery = []
    for img in ASSETS_GALLERY_DIR.glob("*.*"):
        gallery.append({
            "alt": img.stem,
            "date": datetime.now().strftime('%Y-%m-%d'),
            "src": f"/assets/gallery/{img.name}",
            "title": img.stem
        })
    with open(GALLERY_YAML, "w", encoding="utf-8") as f:
        yaml.dump(gallery, f, allow_unicode=True)
    with open(GALLERY_JSON, "w", encoding="utf-8") as f:
        json.dump(gallery, f, ensure_ascii=False, indent=2)
    logging.info(f"Галерея обновлена: {len(gallery)} элементов")

# === Основной запуск ===
def main():
    logging.info("🚀 Запуск генерации статьи...")
    title = generate_article_title()
    body = generate_article_body(title)
    save_article(title, body)
    update_gallery_assets()
    update_gallery_data()

if __name__ == "__main__":
    main()
