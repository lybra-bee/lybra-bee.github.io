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
            r.encoding = "utf-8"
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
    prompt = f"""
Проанализируй современные направления и достижения в искусственном интеллекте и высоких технологиях. 
Составь короткий (5–9 слов), ёмкий заголовок на русском, который будет интересен для блога. 
Заголовок должен отражать конкретное применение технологий, кейс, новинку, урок или исследование, 
например: «Применение ИИ в медицине», «Как построить генеративную модель», «ИИ в строительстве», 
«Новые модели нейросетей для музыки». Избегай слов «тренды», «новости» и общих фраз. 
Заголовок должен быть разнообразным и уникальным, актуальным для {year} года.
"""
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
    return f"Применение ИИ и технологий {year}"

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
    return (
        f"## Введение\n\nИскусственный интеллект в {year} году продолжает активно развиваться. "
        "Ниже — сводка основных направлений.\n\n"
        "## Основные применения\n\n- Генеративные модели развиваются и становятся доступнее.\n"
        "- Мультимодальные системы интегрируют текст, изображение и звук.\n"
        "- Применение ИИ в различных отраслях расширяется.\n\n"
        "## Заключение\n\nТехнологии продолжают трансформировать отрасли и повседневную жизнь."
    )

# --- Save article (front matter YAML) ---
def save_article(title, text, model_name, slug):
    fm = {
        "title": safe_yaml_value(title),
        "date": datetime.now().astimezone().isoformat(),
        "draft": False,
        "image": "",  # изображения уже есть в static, не создаём svg
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
                logging.warning(f"⚠️ Не удалось удалить {old}: {e}")
    except Exception as e:
        logging.error(f"❌ Cleanup posts failed: {e}")

# --- Main ---
def main():
    year = datetime.now().year
    cleanup_old_posts()
    rebuild_gallery_from_static()
    title = generate_title(year)
    slug = slugify(title)
    article_text = generate_article_text(title, year)
    save_article(title, article_text, model_name="AI Generator", slug=slug)
    logging.info("🎉 Content generation complete.")

if __name__ == "__main__":
    main()
