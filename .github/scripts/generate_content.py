#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_content.py
Генерирует заголовок и статью (OpenRouter -> Groq fallback),
сохраняет изображения как JPG/PNG с безопасными именами,
обновляет data/gallery.yaml и data/gallery.json,
удаляет старые .md статьи (оставляет KEEP_POSTS), изображения не трогает.
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

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Папки / константы
POSTS_DIR = "content/posts"
STATIC_IMAGES_DIR = "static/images/posts"
DATA_DIR = "data"
GALLERY_YAML = os.path.join(DATA_DIR, "gallery.yaml")
GALLERY_JSON = os.path.join(DATA_DIR, "gallery.json")
KEEP_POSTS = 10  # сколько последних статей сохранять

# API ключи (передаются в workflow / secrets)
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Ensure dirs exist
os.makedirs(POSTS_DIR, exist_ok=True)
os.makedirs(STATIC_IMAGES_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

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
    prompt = f"Придумай короткий (5-9 слов) заголовок на русском про актуальные тренды ИИ и технологий {year} года."
    logging.info("📝 Генерация заголовка...")
    text = generate_with_openrouter_chat(prompt, max_tokens=70)
    if text:
        return text.strip().strip('"')
    text = generate_with_openrouter_completions(prompt, max_tokens=70)
    if text:
        return text.strip().strip('"')
    text = generate_with_groq_chat(prompt, max_tokens=70)
    if text:
        return text.strip().strip('"')
    return f"Тренды ИИ {year}"

def generate_article_text(title, year):
    prompt = f"Напиши статью на русском по заголовку: «{title}». Объём 400-600 слов, с введением, разделами и заключением."
    logging.info("📝 Генерация текста статьи...")
    text = generate_with_openrouter_chat(prompt, max_tokens=1100)
    if text:
        return text
    text = generate_with_openrouter_completions(prompt, max_tokens=1100)
    if text:
        return text
    text = generate_with_groq_chat(prompt, max_tokens=1100)
    if text:
        return text
    return f"## Введение\n\nИскусственный интеллект в {year} году продолжает развиваться.\n\n## Основные тренды\n\n- Генеративные модели развиваются.\n- Мультимодальные системы интегрируют текст, изображение и звук.\n- Внимание к этике и безопасности растёт.\n\n## Заключение\n\nТехнологии трансформируют отрасли."

# --- Image creation (JPG placeholder) ---
def create_jpg_image(title, slug):
    filename = f"{slug}.jpg"
    img_path = os.path.join(STATIC_IMAGES_DIR, filename)
    width, height = 1200, 630
    image = Image.new("RGB", (width, height), color=(102, 126, 234))
    draw = ImageDraw.Draw(image)
    try:
        font_title = ImageFont.truetype("arial.ttf", 44)
    except:
        font_title = ImageFont.load_default()
    draw.text((width//2, height//2), title, fill=(255,255,255), font=font_title, anchor="mm")
    image.save(img_path)
    logging.info(f"🖼️ JPG image created: {img_path}")
    return f"/images/posts/{filename}"

# --- Save article ---
def save_article(title, text, model_name, slug, image_src):
    fm = {
        "title": safe_yaml_value(title),
        "date": datetime.now().astimezone().isoformat(),
        "draft": False,
        "image": image_src,
        "model": safe_yaml_value(model_name),
        "tags": ["AI", "Tech"],
        "categories": ["Технологии"],
        "author": "AI Generator",
        "description": safe_yaml_value(text[:200]+"..." if len(text)>200 else "")
    }
    filename = os.path.join(POSTS_DIR, f"{slug}.md")
    yaml_block = yaml.safe_dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
    content = f"---\n{yaml_block}---\n\n{text}\n"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    logging.info(f"✅ Article saved: {filename}")

# --- Rebuild gallery ---
def rebuild_gallery_from_static(limit=200):
    patterns = ["*.png", "*.jpg", "*.jpeg", "*.svg"]
    files = []
    for p in patterns:
        files.extend(glob.glob(os.path.join(STATIC_IMAGES_DIR, p)))
    gallery = []
    for f in sorted(files, key=os.path.getmtime, reverse=True)[:limit]:
        base = os.path.basename(f)
        slug = os.path.splitext(base)[0]
        gallery.append({
            "alt": slug.replace("-", " ").capitalize(),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "src": f"/images/posts/{base}",
            "title": slug.replace("-", " ").capitalize()
        })
    # Save YAML
    with open(GALLERY_YAML, "w", encoding="utf-8") as f:
        yaml.safe_dump(gallery, f, allow_unicode=True, default_flow_style=False)
    # Save JSON
    with open(GALLERY_JSON, "w", encoding="utf-8") as f:
        json.dump(gallery, f, ensure_ascii=False, indent=2)
    logging.info(f"🎨 Gallery rebuilt with {len(gallery)} images.")

# --- Clean old posts ---
def clean_old_posts():
    files = sorted(glob.glob(os.path.join(POSTS_DIR, "*.md")), key=os.path.getmtime, reverse=True)
    if len(files) <= KEEP_POSTS:
        return
    to_delete = files[KEEP_POSTS:]
    for f in to_delete:
        os.remove(f)
        logging.info(f"🗑️ Deleted old post: {f}")

# --- Main ---
def main():
    year = datetime.now().year
    clean_old_posts()
    title = generate_title(year)
    slug = slugify(title)
    text = generate_article_text(title, year)
    image_src = create_jpg_image(title, slug)
    save_article(title, text, "AI Generator", slug, image_src)
    rebuild_gallery_from_static()

if __name__ == "__main__":
    main()
