#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_content.py
Генерирует заголовок и статью (OpenRouter -> Groq fallback),
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
        r.encoding = "utf-8"
        data = r.json()
        return try_extract_openrouter_response(data)
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
        if isinstance(data, dict):
            if "output" in data and isinstance(data["output"], list) and data["output"]:
                return data["output"][0].get("content")
            if "choices" in data and data["choices"]:
                return data["choices"][0].get("text")
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
            r.encoding = "utf-8"
            data = r.json()
            if "choices" in data and data["choices"]:
                c = data["choices"][0]
                if "message" in c and "content" in c["message"]:
                    return c["message"]["content"].strip()
                if "text" in c:
                    return c["text"].strip()
            if "prediction" in data:
                return str(data["prediction"]).strip()
        except Exception as e:
            logging.warning(f"⚠️ Groq endpoint {url} failed: {e}")
    return None

# --- High level generators ---
def generate_title(year):
    prompt = f"""
Составь короткий (5–9 слов) заголовок на русском языке для статьи о применении ИИ и технологий в {year} году.
Он должен быть конкретным (пример: «ИИ в диагностике заболеваний», «Нейросети в строительстве»).
Избегай слов «новости», «тренды» и общих фраз. Сделай так, чтобы заголовок выглядел как статья в блоге, а не рекламный слоган.
"""
    logging.info("📝 Генерация заголовка (OpenRouter -> Groq)...")
    text = generate_with_openrouter_chat(prompt, max_tokens=70)
    if text:
        return text.strip().strip('"')
    text = generate_with_openrouter_completions(prompt, max_tokens=70)
    if text:
        return text.strip().strip('"')
    text = generate_with_groq_chat(prompt, max_tokens=70)
    if text:
        return text.strip().strip('"')
    logging.warning("⚠️ Не удалось получить заголовок от API — fallback")
    return f"ИИ и технологии {year}"

def generate_article_text(title, year):
    prompt = f"""
Напиши информативную статью на русском языке по заголовку: «{title}». 
Объём: 400–600 слов.  
Структура: Введение → 2–3 раздела с подзаголовками → Заключение.  
Сделай связный текст, без пунктов-списков, чтобы это выглядело как полноценный пост в блоге.
"""
    logging.info("📝 Генерация текста статьи (OpenRouter -> Groq)...")
    text = generate_with_openrouter_chat(prompt, max_tokens=1100)
    if text:
        return text
    text = generate_with_openrouter_completions(prompt, max_tokens=1100)
    if text:
        return text
    text = generate_with_groq_chat(prompt, max_tokens=1100)
    if text:
        return text
    logging.warning("⚠️ Все генераторы не сработали — fallback")
    return (
        f"## Введение\n\nИскусственный интеллект в {year} году активно внедряется в разные сферы.\n\n"
        "## Основные применения\n\nИИ помогает в медицине, образовании, промышленности и творчестве. "
        "Мультимодальные модели объединяют текст, изображение и звук.\n\n"
        "## Заключение\n\nРазвитие технологий продолжает менять повседневную жизнь."
    )

# --- Save article ---
def save_article(title, text, model_name, slug):
    fm = {
        "title": safe_yaml_value(title),
        "date": datetime.now().astimezone().isoformat(),
        "draft": False,
        "image": "",
        "model": safe_yaml_value(model_name),
        "tags": ["AI", "Tech"],
        "categories": ["Технологии"],
        "author": "AI Generator",
        "description": safe_yaml_value(text[:200] + ("..." if len(text) > 200 else "")),
    }
    filename = os.path.join(POSTS_DIR, f"{slug}.md")
    # если файл уже есть — добавим timestamp к slug
    if os.path.exists(filename):
        slug = f"{slug}-{int(time.time())}"
        filename = os.path.join(POSTS_DIR, f"{slug}.md")
    yaml_block = yaml.safe_dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
    content = f"---\n{yaml_block}---\n\n{text}\n"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    logging.info(f"✅ Article saved: {filename}")
    return filename

# --- Gallery ---
def rebuild_gallery_from_static(limit=200):
    logging.info("🗂️ Rebuilding gallery ...")
    patterns = ["*.png", "*.jpg", "*.jpeg", "*.svg", "*.webp", "*.gif"]
    files = []
    for p in patterns:
        files.extend(glob.glob(os.path.join(STATIC_IMAGES_DIR, p)))
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
    with open(GALLERY_YAML, "w", encoding="utf-8") as yf:
        yaml.safe_dump(images, yf, allow_unicode=True, default_flow_style=False)
    with open(GALLERY_JSON, "w", encoding="utf-8") as jf:
        json.dump(images, jf, ensure_ascii=False, indent=2)
    logging.info(f"✅ Gallery rebuilt: {len(images)} items")

# --- Cleanup old posts ---
def cleanup_old_posts(keep=KEEP_POSTS):
    md_files = sorted(glob.glob(os.path.join(POSTS_DIR, "*.md")), key=os.path.getmtime, reverse=True)
    for old in md_files[keep:]:
        try:
            os.remove(old)
            logging.info(f"🗑️ Removed old article: {old}")
        except Exception as e:
            logging.warning(f"⚠️ Не удалось удалить {old}: {e}")

# --- Main ---
def main():
    year = datetime.now().year
    cleanup_old_posts()
    rebuild_gallery_from_static()
    title = generate_title(year)
    slug = slugify(title)
    article_text = generate_article_text(title, year)
    save_article(title, article_text, model_name="openrouter:gpt-4o-mini", slug=slug)
    logging.info("🎉 Content generation complete.")

if __name__ == "__main__":
    main()
