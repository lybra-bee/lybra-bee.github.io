#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_content.py
Генерация заголовка, статьи, изображений и обновление галереи
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
from PIL import Image, ImageDraw, ImageFont

# --- Настройка ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

POSTS_DIR = "content/posts"
STATIC_IMAGES_DIR = "static/images/posts"
ASSETS_GALLERY_DIR = "assets/gallery"
DATA_DIR = "data"
GALLERY_YAML = os.path.join(DATA_DIR, "gallery.yaml")
GALLERY_JSON = os.path.join(DATA_DIR, "gallery.json")
KEEP_POSTS = 10

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

os.makedirs(POSTS_DIR, exist_ok=True)
os.makedirs(STATIC_IMAGES_DIR, exist_ok=True)
os.makedirs(ASSETS_GALLERY_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# --- Helpers ---
def safe_yaml_value(v):
    if v is None:
        return ""
    return str(v).replace("\r", " ").replace("\n", " ").strip()

# --- API генерация ---
def try_generate(prompt, max_tokens=1000):
    headers_or = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
    headers_groq = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    # OpenRouter Chat
    if OPENROUTER_API_KEY:
        try:
            r = requests.post("https://openrouter.ai/api/v1/chat/completions",
                              headers=headers_or,
                              json={"model":"gpt-4o-mini","messages":[{"role":"user","content":prompt}],
                                    "max_tokens":max_tokens}, timeout=60)
            r.raise_for_status()
            data = r.json()
            return data.get("choices",[{}])[0].get("message",{}).get("content")
        except:
            pass
    # GROQ
    if GROQ_API_KEY:
        try:
            r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                              headers=headers_groq,
                              json={"model":"gpt-4o-mini","messages":[{"role":"user","content":prompt}],
                                    "max_tokens":max_tokens}, timeout=60)
            r.raise_for_status()
            data = r.json()
            return data.get("choices",[{}])[0].get("message",{}).get("content")
        except:
            pass
    return None

# --- Заголовок и статья ---
def generate_title(year):
    logging.info("📝 Генерация заголовка...")
    text = try_generate(f"Придумай короткий заголовок про ИИ и технологии {year} года, 5-9 слов на русском")
    return text.strip().strip('"') if text else f"Тренды ИИ {year}"

def generate_article(title, year):
    logging.info("📝 Генерация текста статьи...")
    text = try_generate(f"Напиши статью на русском по заголовку: «{title}». 400-600 слов, с введением, разделами и заключением")
    return text if text else f"## Введение\nИскусственный интеллект в {year} году развивается.\n## Основные тренды\n- Генеративные модели.\n- Мультимодальные системы.\n- Этические вопросы.\n## Заключение\nТехнологии трансформируют отрасли."

# --- Изображение ---
def create_image(title, slug):
    filename = f"{slug}.jpg"
    path_static = os.path.join(STATIC_IMAGES_DIR, filename)
    path_assets = os.path.join(ASSETS_GALLERY_DIR, filename)
    width, height = 1200, 630
    image = Image.new("RGB", (width, height), color=(102,126,234))
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("arial.ttf", 44)
    except:
        font = ImageFont.load_default()
    draw.text((width//2, height//2), title, fill=(255,255,255), font=font, anchor="mm")
    image.save(path_static)
    # Копируем в assets
    import shutil
    shutil.copy(path_static, path_assets)
    logging.info(f"🖼 Изображение создано: {path_static}")
    return f"/images/posts/{filename}"

# --- Сохранение статьи ---
def save_article(title, text, slug, image_src):
    fm = {
        "title": safe_yaml_value(title),
        "date": datetime.now().isoformat(),
        "draft": False,
        "image": image_src,
        "tags": ["AI","Tech"],
        "categories": ["Технологии"],
        "author": "AI Generator",
        "description": safe_yaml_value(text[:200]+"..." if len(text)>200 else "")
    }
    filename = os.path.join(POSTS_DIR, f"{slug}.md")
    content = f"---\n{yaml.safe_dump(fm, allow_unicode=True, default_flow_style=False)}---\n\n{text}\n"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    logging.info(f"✅ Статья сохранена: {filename}")

# --- Галерея ---
def rebuild_gallery(limit=200):
    patterns = ["*.png","*.jpg","*.jpeg","*.svg"]
    files = []
    for p in patterns:
        files.extend(glob.glob(os.path.join(STATIC_IMAGES_DIR,p)))
    gallery = []
    for f in sorted(files, key=os.path.getmtime, reverse=True)[:limit]:
        base = os.path.basename(f)
        slug = os.path.splitext(base)[0]
        gallery.append({
            "alt": slug.replace("-"," ").capitalize(),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "src": f"/images/posts/{base}",
            "title": slug.replace("-"," ").capitalize()
        })
    # YAML и JSON
    with open(GALLERY_YAML, "w", encoding="utf-8") as f:
        yaml.safe_dump(gallery, f, allow_unicode=True, default_flow_style=False)
    with open(GALLERY_JSON, "w", encoding="utf-8") as f:
        json.dump(gallery, f, ensure_ascii=False, indent=2)
    logging.info(f"🎨 Галерея обновлена ({len(gallery)} изображений)")

# --- Удаление старых статей ---
def clean_old_posts():
    files = sorted(glob.glob(os.path.join(POSTS_DIR,"*.md")), key=os.path.getmtime, reverse=True)
    for f in files[KEEP_POSTS:]:
        os.remove(f)
        logging.info(f"🗑 Старый пост удалён: {f}")

# --- Main ---
def main():
    year = datetime.now().year
    clean_old_posts()
    title = generate_title(year)
    slug = slugify(title)
    text = generate_article(title, year)
    image_src = create_image(title, slug)
    save_article(title, text, slug, image_src)
    rebuild_gallery()

if __name__ == "__main__":
    main()
