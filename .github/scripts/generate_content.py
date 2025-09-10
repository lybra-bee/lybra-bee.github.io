#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_content.py
Генерирует заголовок и статью (OpenRouter -> Groq fallback),
создаёт SVG-заглушку при необходимости,
обновляет data/gallery.yaml и data/gallery.json,
удаляет старые .md статьи (оставляет KEEP_POSTS),
не трогает существующие изображения.
"""

import os
import sys
import time
import json
import yaml
import logging
import requests
import glob
from datetime import datetime
from slugify import slugify

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Папки / константы
POSTS_DIR = "content/posts"
STATIC_IMAGES_DIR = "static/images/posts"
DATA_DIR = "data"
GALLERY_YAML = os.path.join(DATA_DIR, "gallery.yaml")
GALLERY_JSON = os.path.join(DATA_DIR, "gallery.json")
PLACEHOLDER = "static/images/placeholder.jpg"
KEEP_POSTS = 10  # сколько последних статей сохранять

# API ключи
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Ensure dirs exist
os.makedirs(POSTS_DIR, exist_ok=True)
os.makedirs(STATIC_IMAGES_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(os.path.dirname(PLACEHOLDER), exist_ok=True)

# --- Helpers ---
def safe_yaml_value(v):
    if v is None:
        return ""
    return str(v).replace("\r", " ").replace("\n", " ").strip()

def try_extract_openrouter_response(data):
    try:
        if isinstance(data, dict):
            if "choices" in data and data["choices"]:
                c = data["choices"][0]
                if isinstance(c, dict):
                    if "message" in c and isinstance(c["message"], dict) and "content" in c["message"]:
                        return c["message"]["content"]
                    if "text" in c:
                        return c["text"]
            if "output" in data and isinstance(data["output"], list) and data["output"]:
                first = data["output"][0]
                if isinstance(first, dict) and "content" in first:
                    return first["content"]
        return None
    except Exception:
        return None

def generate_with_openrouter_chat(prompt, max_tokens=800, model="gpt-4o-mini"):
    if not OPENROUTER_API_KEY:
        logging.debug("OPENROUTER_API_KEY отсутствует")
        return None
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens}
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        text = try_extract_openrouter_response(data)
        if text:
            return text.strip()
    except Exception as e:
        logging.warning(f"⚠️ OpenRouter(chat) failed: {e}")
    return None

def generate_with_openrouter_completions(prompt, max_tokens=1200, model="gpt-4o-mini"):
    if not OPENROUTER_API_KEY:
        return None
    url = "https://openrouter.ai/api/v1/completions"
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": model, "input": prompt, "max_tokens": max_tokens}
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, dict):
            if "output" in data and isinstance(data["output"], list) and data["output"]:
                out = data["output"][0]
                if isinstance(out, dict) and "content" in out:
                    return out["content"]
            if "choices" in data and data["choices"]:
                c = data["choices"][0]
                if isinstance(c, dict) and "text" in c:
                    return c["text"]
        return None
    except Exception as e:
        logging.warning(f"⚠️ OpenRouter(completions) failed: {e}")
    return None

def generate_with_groq_chat(prompt, max_tokens=1200, model="gpt-4o-mini"):
    if not GROQ_API_KEY:
        logging.debug("GROQ_API_KEY отсутствует")
        return None
    endpoints = [
        "https://api.groq.com/openai/v1/chat/completions",
        "https://api.groq.com/v1/chat/completions",
        "https://api.groq.com/v1/predict",
    ]
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    for url in endpoints:
        try:
            payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens}
            r = requests.post(url, headers=headers, json=payload, timeout=60)
            r.raise_for_status()
            data = r.json()
            if isinstance(data, dict):
                if "choices" in data and data["choices"]:
                    c = data["choices"][0]
                    if isinstance(c, dict):
                        if "message" in c and "content" in c["message"]:
                            return c["message"]["content"].strip()
                        if "text" in c:
                            return c["text"].strip()
                if "prediction" in data:
                    return str(data["prediction"]).strip()
                if "output" in data and isinstance(data["output"], list) and data["output"]:
                    first = data["output"][0]
                    if isinstance(first, dict) and "content" in first:
                        return first["content"].strip()
        except Exception as e:
            logging.warning(f"⚠️ Groq endpoint {url} failed: {e}")
            continue
    return None

# --- High level generators ---
def generate_title(year):
    prompt = (
        f"Проанализируй ключевые события и применения искусственного интеллекта "
        f"и высоких технологий за {year} год и придумай короткий, ёмкий заголовок "
        f"на русском языке. Тематика может включать: AI в медицине, строительстве, "
        f"образовании, новые технологии, разновидности моделей генерации, практические "
        f"уроки по нейросетям. Заголовок должен быть разнообразным и уникальным."
    )
    logging.info("📝 Генерация заголовка (OpenRouter -> Groq)...")
    text = generate_with_openrouter_chat(prompt, max_tokens=70)
    if text:
        logging.info("✅ Заголовок через OpenRouter")
        return text.strip().strip('"')
    text = generate_with_openrouter_completions(prompt, max_tokens=70)
    if text:
        logging.info("✅ Заголовок через OpenRouter (completions)")
        return text.strip().strip('"')
    text = generate_with_groq_chat(prompt, max_tokens=70)
    if text:
        logging.info("✅ Заголовок через Groq")
        return text.strip().strip('"')
    logging.warning("⚠️ Не удалось получить заголовок от API — использовать локальный заголовок")
    return f"AI и технологии {year}"

def generate_article_text(title, year):
    prompt = f"Напиши статью на русском языке по заголовку: «{title}». Объём 400-600 слов. Включи введение, несколько разделов с подзаголовками и заключение."
    logging.info("📝 Генерация текста статьи (OpenRouter -> Groq)...")
    text = generate_with_openrouter_chat(prompt, max_tokens=1100)
    if text:
        logging.info("✅ Текст получен через OpenRouter")
        return text
    text = generate_with_openrouter_completions(prompt, max_tokens=1100)
    if text:
        logging.info("✅ Текст получен через OpenRouter (completions)")
        return text
    text = generate_with_groq_chat(prompt, max_tokens=1100)
    if text:
        logging.info("✅ Текст получен через Groq")
        return text
    logging.warning("⚠️ Все генераторы не сработали — использую локальный fallback")
    return (
        f"## Введение\n\nИскусственный интеллект в {year} году активно развивается. "
        "Ниже — сводка основных направлений.\n\n"
        "## Основные направления\n\n- Генеративные модели развиваются.\n"
        "- Мультимодальные системы интегрируют текст, изображение и звук.\n"
        "- Внимание к этике и безопасности растёт.\n\n"
        "## Заключение\n\nAI и технологии продолжают изменять мир."
    )

def save_article(title, text):
    slug = slugify(title)
    filename = os.path.join(POSTS_DIR, f"{slug}.md")
    logging.info(f"💾 Сохраняем статью в {filename}")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"---\ntitle: {title}\ndate: '{datetime.now().strftime('%Y-%m-%d')}'\nslug: {slug}\n---\n\n{text}\n")
    return filename

# --- Gallery generation ---
def collect_gallery_images():
    images = []
    for ext in ("*.jpg", "*.jpeg", "*.png", "*.gif", "*.svg", "*.webp"):
        images.extend(glob.glob(os.path.join(STATIC_IMAGES_DIR, ext)))
    images = sorted(images)
    gallery = []
    for img in images:
        filename = os.path.basename(img)
        gallery.append({
            "src": f"/images/posts/{filename}",
            "alt": os.path.splitext(filename)[0].replace("-", " ").capitalize(),
            "title": os.path.splitext(filename)[0].replace("-", " ").capitalize(),
            "date": datetime.now().strftime("%Y-%m-%d")
        })
    return gallery

def save_gallery(gallery):
    logging.info("💾 Обновляем data/gallery.yaml и data/gallery.json")
    with open(GALLERY_YAML, "w", encoding="utf-8") as f:
        yaml.safe_dump(gallery, f, allow_unicode=True)
    with open(GALLERY_JSON, "w", encoding="utf-8") as f:
        json.dump(gallery, f, ensure_ascii=False, indent=2)

# --- Cleanup old posts ---
def cleanup_old_posts():
    files = sorted(glob.glob(os.path.join(POSTS_DIR, "*.md")), key=os.path.getmtime, reverse=True)
    old = files[KEEP_POSTS:]
    for f in old:
        logging.info(f"🗑️ Удаляем старую статью {f}")
        os.remove(f)

# --- Main ---
def main():
    year = datetime.now().year
    title = generate_title(year)
    text = generate_article_text(title, year)
    save_article(title, text)
    gallery = collect_gallery_images()
    save_gallery(gallery)
    cleanup_old_posts()
    logging.info("✅ Генерация контента завершена.")

if __name__ == "__main__":
    main()
