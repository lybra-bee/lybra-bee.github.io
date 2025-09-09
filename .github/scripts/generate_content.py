#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_content.py
Генерирует заголовок и статью (OpenRouter -> Groq fallback),
создаёт SVG-заглушку в static/images/posts/,
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

# API ключи (передаются в workflow / secrets)
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
    # Try common shapes
    try:
        if isinstance(data, dict):
            if "choices" in data and data["choices"]:
                c = data["choices"][0]
                # chat style: message.content
                if isinstance(c, dict):
                    if "message" in c and isinstance(c["message"], dict) and "content" in c["message"]:
                        return c["message"]["content"]
                    if "text" in c:
                        return c["text"]
            if "output" in data and isinstance(data["output"], list) and data["output"]:
                first = data["output"][0]
                if isinstance(first, dict):
                    # openrouter completions: output[0].content
                    if "content" in first:
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
        r.encoding = "utf-8"
        data = r.json()
        text = try_extract_openrouter_response(data)
        if text:
            return text.strip()
        # fallback: maybe simpler response
        if isinstance(data, dict) and "message" in data:
            return str(data["message"])
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
        r.encoding = "utf-8"
        data = r.json()
        # Try expected shapes
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
    # Try a few endpoints Groq historically used
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
            r.encoding = "utf-8"
            data = r.json()
            # parse common shapes
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
            # If no usable content, continue to next endpoint
        except Exception as e:
            logging.warning(f"⚠️ Groq endpoint {url} failed: {e}")
            continue
    return None

# --- High level generators ---
def generate_title(year):
    prompt = f"Придумай короткий (5-9 слов), ёмкий заголовок на русском про актуальные тренды в искусственном интеллекте и высоких технологиях. Не указывай прошлые годы, заголовок должен быть актуален для {year} года и не содержать дат."
    logging.info("📝 Генерация заголовка (OpenRouter -> Groq)...")
    # Try OpenRouter chat
    text = generate_with_openrouter_chat(prompt, max_tokens=70)
    if text:
        logging.info("✅ Заголовок через OpenRouter")
        return text.strip().strip('"')
    # Try OpenRouter completions
    text = generate_with_openrouter_completions(prompt, max_tokens=70)
    if text:
        logging.info("✅ Заголовок через OpenRouter (completions)")
        return text.strip().strip('"')
    # Groq fallback
    text = generate_with_groq_chat(prompt, max_tokens=70)
    if text:
        logging.info("✅ Заголовок через Groq")
        return text.strip().strip('"')
    # Final fallback
    logging.warning("⚠️ Не удалось получить заголовок от API — использовать локальный заголовок")
    return f"Тренды искусственного интеллекта {year}"

def generate_article_text(title, year):
    prompt = f"Напиши статью на русском языке по заголовку: «{title}». Объём 400-600 слов. Сделай информативно и связно, раздели текст на введение, несколько разделов с подзаголовками и заключение."
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
    # simple fallback text
    return (
        f"## Введение\n\nИскусственный интеллект в {year} году продолжает активно развиваться. "
        "Ниже — сводка основных трендов и направлений.\n\n"
        "## Основные тренды\n\n- Генеративные модели развиваются и становятся доступнее.\n"
        "- Мультимодальные системы интегрируют текст, изображение и звук.\n"
        "- Внимание к этике и безопасности растёт.\n\n"
        "## Заключение\n\nТехнологии продолжают трансформировать отрасли и повседневную жизнь."
    )

# --- Image creation (SVG placeholder) ---
def create_svg_image(title, slug):
    safe_title = title.replace('"', '').replace("'", "")
    filename = f"{slug}.svg"
    img_path = os.path.join(STATIC_IMAGES_DIR, filename)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#667eea"/>
      <stop offset="1" stop-color="#764ba2"/>
    </linearGradient>
  </defs>
  <rect width="100%" height="100%" fill="url(#g)"/>
  <text x="600" y="310" font-family="Arial, Helvetica, sans-serif" font-size="44" fill="#fff" text-anchor="middle" dominant-baseline="middle">{safe_title}</text>
  <text x="600" y="360" font-family="Arial, Helvetica, sans-serif" font-size="20" fill="rgba(255,255,255,0.85)" text-anchor="middle">AI generated placeholder</text>
</svg>'''
    try:
        with open(img_path, "w", encoding="utf-8") as f:
            f.write(svg)
        logging.info(f"🖼️ SVG image created: {img_path}")
        return f"/images/posts/{filename}"
    except Exception as e:
        logging.error(f"❌ Error writing SVG image: {e}")
        return f"/{PLACEHOLDER.lstrip('/')}"


# --- Save article (front matter YAML) ---
def save_article(title, text, model_name, slug):
    fm = {
        "title": safe_yaml_value(title),
        "date": datetime.now().astimezone().isoformat(),
        "draft": False,
        "image": f"/images/posts/{slug}.svg",
        "model": safe_yaml_value(model_name),
        "tags": ["AI", "Tech"],
        "categories": ["Технологии"],
        "author": "AI Generator",
        "description": safe_yaml_value(text[:200] + ("..." if len(text) > 200 else "")),
    }
    filename = os.path.join(POSTS_DIR, f"{slug}.md")
    yaml_block = yaml.safe_dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
    content = f"---\n{yaml_block}---\n\n{text}\n"
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        logging.info(f"✅ Article saved: {filename}")
        return filename
    except Exception as e:
        logging.error(f"❌ Error saving article: {e}")
        raise

# --- Gallery generation from static/images/posts/ ---
def rebuild_gallery_from_static(limit=200):
    logging.info("🗂️ Rebuilding gallery from static/images/posts/ ...")
    # find images
    patterns = ["*.png", "*.jpg", "*.jpeg", "*.svg", "*.webp", "*.gif"]
    files = []
    for p in patterns:
        files.extend(glob.glob(os.path.join(STATIC_IMAGES_DIR, p)))
    # sort by mtime desc
    files = sorted(files, key=os.path.getmtime, reverse=True)
    images = []
    for fpath in files[:limit]:
        fname = os.path.basename(fpath)
        title = os.path.splitext(fname)[0].replace("-", " ").replace("_", " ").title()
        item = {
            "src": f"/images/posts/{fname}",
            "alt": title,
            "title": title,
            "date": datetime.fromtimestamp(os.path.getmtime(fpath)).strftime("%Y-%m-%d")
        }
        images.append(item)
    # write YAML (list) and JSON
    try:
        with open(GALLERY_YAML, "w", encoding="utf-8") as yf:
            yaml.safe_dump(images, yf, allow_unicode=True, default_flow_style=False)
        with open(GALLERY_JSON, "w", encoding="utf-8") as jf:
            json.dump(images, jf, ensure_ascii=False, indent=2)
        logging.info(f"✅ Gallery rebuilt: {len(images)} items ({GALLERY_YAML}, {GALLERY_JSON})")
    except Exception as e:
        logging.error(f"❌ Error writing gallery files: {e}")


# --- Cleanup old posts (keep only KEEP_POSTS newest) ---
def cleanup_old_posts(keep=KEEP_POSTS):
    try:
        md_files = glob.glob(os.path.join(POSTS_DIR, "*.md"))
        md_files = sorted(md_files, key=os.path.getmtime, reverse=True)
        if len(md_files) <= keep:
            logging.info("🧾 Нет старых статей для удаления")
            return
        for old in md_files[keep:]:
            try:
                os.remove(old)
                logging.info(f"🗑️ Removed old article: {old}")
            except Exception as e:
                logging.warning(f"⚠️ Could not remove {old}: {e}")
    except Exception as e:
        logging.error(f"❌ Error during cleanup_old_posts: {e}")


# === Main ===
def main():
    try:
        year = datetime.now().year
        title = generate_title(year)
        text = generate_article_text(title, year)
        model_name = "OpenRouter/Groq"
        slug = slugify(title) or slugify(f"article-{int(time.time())}")
        # create image
        image_path = create_svg_image(title, slug)
        # save article
        save_article(title, text, model_name, slug)
        # cleanup old posts (only md files)
        cleanup_old_posts(keep=KEEP_POSTS)
        # rebuild gallery by scanning static folder
        rebuild_gallery_from_static(limit=200)
        logging.info("🎉 Generation completed successfully")
    except Exception as e:
        logging.exception(f"🔥 Critical failure in main: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
