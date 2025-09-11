#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_content.py
Генерация заголовка и статьи (Groq -> OpenRouter -> fallback),
сохраняет статьи, обновляет галерею с ВСЕМИ изображениями,
удаляет старые .md статьи, оставляя 10 последних.
"""

import os
import json
import yaml
import logging
import requests
import glob
from datetime import datetime
from slugify import slugify

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Папки / константы
POSTS_DIR = "content/posts"
STATIC_DIR = "static/images/posts"
GALLERY_FILE = "data/gallery.yaml"
KEEP_POSTS = 10
PLACEHOLDER = os.path.join(STATIC_DIR, "placeholder.svg")

os.makedirs(POSTS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(os.path.dirname(GALLERY_FILE), exist_ok=True)

# API ключи
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# ---------------- Helpers ----------------
def safe_yaml_value(value):
    if not value:
        return ""
    return str(value).replace('"', "'").replace('\n', ' ').strip()

# --- Генерация через API ---
def generate_with_openrouter(prompt, max_tokens=1200):
    if not OPENROUTER_API_KEY:
        return None
    try:
        logging.info("🌐 Пробуем OpenRouter...")
        headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
        payload = {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens}
        r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        if "choices" in data and data["choices"]:
            return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logging.warning(f"⚠️ OpenRouter failed: {e}")
    return None

def generate_with_groq(prompt, max_tokens=1200):
    if not GROQ_API_KEY:
        return None
    try:
        logging.info("🌐 Пробуем Groq...")
        endpoints = [
            "https://api.groq.com/openai/v1/chat/completions",
            "https://api.groq.com/v1/chat/completions",
        ]
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        for url in endpoints:
            try:
                payload = {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens}
                r = requests.post(url, headers=headers, json=payload, timeout=60)
                r.raise_for_status()
                data = r.json()
                if "choices" in data and data["choices"]:
                    c = data["choices"][0]
                    if "message" in c and "content" in c["message"]:
                        return c["message"]["content"].strip()
            except Exception as e:
                logging.warning(f"⚠️ Groq endpoint {url} failed: {e}")
                continue
    except Exception as e:
        logging.warning(f"⚠️ Groq failed: {e}")
    return None

# ---------------- High level generators ----------------
def generate_title(year):
    prompt = f"""Проанализируй современные направления и достижения в искусственном интеллекте и высоких технологиях. 
Составь короткий (5–9 слов), ёмкий заголовок на русском, интересный для блога. Актуально для {year} года."""
    text = generate_with_groq(prompt, max_tokens=70)
    if text:
        logging.info("✅ Заголовок через Groq")
        return text
    text = generate_with_openrouter(prompt, max_tokens=70)
    if text:
        logging.info("✅ Заголовок через OpenRouter")
        return text
    logging.warning("⚠️ Не удалось получить заголовок от API — fallback")
    return f"Применение ИИ и технологий {year}"

def generate_article_text(title, year):
    prompt = f"Напиши статью на русском языке по заголовку: «{title}». Объём 400-600 слов. Введи разделы с подзаголовками и заключение."
    text = generate_with_groq(prompt, max_tokens=1100)
    if text:
        logging.info(f"✅ Статья через Groq (первые 120 символов): {text[:120]}...")
        return text
    text = generate_with_openrouter(prompt, max_tokens=1100)
    if text:
        logging.info(f"✅ Статья через OpenRouter (первые 120 символов): {text[:120]}...")
        return text
    logging.warning("⚠️ Все генераторы не сработали — fallback")
    return f"## Введение\nИскусственный интеллект в {year} году продолжает активно развиваться.\n\n## Основные направления\n- Генеративные модели\n- Мультимодальные системы\n- Применение ИИ в разных отраслях\n\n## Заключение\nТехнологии продолжают трансформировать отрасли."

# ---------------- Image ----------------
def generate_image(title, slug):
    try:
        img_path = os.path.join(STATIC_DIR, f"{slug}.svg")
        svg_content = f'''<svg width="1200" height="630" xmlns="http://www.w3.org/2000/svg">
<rect width="100%" height="100%" fill="#667eea"/>
<text x="600" y="300" font-size="48" fill="white" text-anchor="middle">{title}</text>
</svg>'''
        with open(img_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)
        return f"/images/posts/{slug}.svg"
    except Exception as e:
        logging.error(f"❌ Ошибка создания изображения: {e}")
        return PLACEHOLDER

# ---------------- Gallery ----------------
def rebuild_gallery():
    try:
        files = glob.glob(os.path.join(STATIC_DIR, "*"))
        files = sorted(files, key=os.path.getmtime)
        gallery = []
        for fpath in files:
            fname = os.path.basename(fpath)
            gallery.append({
                "src": f"/images/posts/{fname}",
                "alt": fname,
                "title": fname,
                "date": datetime.fromtimestamp(os.path.getmtime(fpath)).strftime("%Y-%m-%d")
            })
        with open(GALLERY_FILE, 'w', encoding='utf-8') as f:
            yaml.safe_dump(gallery, f, allow_unicode=True, default_flow_style=False)
        logging.info(f"✅ Галерея обновлена ({len(gallery)} изображений)")
    except Exception as e:
        logging.error(f"❌ Ошибка обновления галереи: {e}")

# ---------------- Save article ----------------
def save_article(title, text, model_name, slug, image_path):
    try:
        filename = os.path.join(POSTS_DIR, f"{slug}.md")
        fm = {
            "title": safe_yaml_value(title),
            "date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+03:00"),
            "draft": False,
            "image": image_path,
            "tags": ["AI","Tech"],
            "categories": ["Технологии"],
            "author": model_name,
            "description": safe_yaml_value(text[:200]+"..." if len(text)>200 else text)
        }
        yaml_block = yaml.safe_dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
        content = f"---\n{yaml_block}---\n\n{text}\n"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        logging.info(f"✅ Статья сохранена: {filename}")
    except Exception as e:
        logging.error(f"❌ Ошибка сохранения статьи: {e}")

# ---------------- Cleanup ----------------
def cleanup_old_posts():
    posts = sorted(glob.glob(os.path.join(POSTS_DIR, "*.md")), key=os.path.getmtime, reverse=True)
    for old in posts[KEEP_POSTS:]:
        try:
            os.remove(old)
            logging.info(f"🗑️ Удалён старый пост: {old}")
        except Exception as e:
            logging.warning(f"⚠️ Не удалось удалить {old}: {e}")

# ---------------- Main ----------------
def main():
    year = datetime.now().year
    title = generate_title(year)
    slug = slugify(title)
    text = generate_article_text(title, year)
    image_path = generate_image(title, slug)
    save_article(title, text, "AI Generator", slug, image_path)
    rebuild_gallery()
    cleanup_old_posts()
    logging.info("🎉 Генерация контента завершена!")

if __name__ == "__main__":
    main()
