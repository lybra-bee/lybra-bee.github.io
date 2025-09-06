#!/usr/bin/env python3
import os
import requests
import json
import logging
from datetime import datetime
import yaml
from slugify import slugify

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
FUSIONBRAIN_API_KEY = os.environ.get("FUSIONBRAIN_API_KEY")

CONTENT_DIR = "content/posts"
IMAGE_DIR = "assets/images/posts"
GALLERY_FILE = "data/gallery.yaml"

PROMPT = "проанализируй последние тренды в искусственном интеллекте и высоких технологиях и напиши статью на 400-600 слов."

# -----------------------------
# Генерация статьи через OpenRouter/Groq
# -----------------------------
def generate_article():
    logging.info("📝 Генерация статьи...")
    # OpenRouter
    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openai/gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "Ты — эксперт по искусственному интеллекту и высоким технологиям."},
                    {"role": "user", "content": PROMPT}
                ]
            }
        )
        r.raise_for_status()
        text = r.json()["choices"][0]["message"]["content"].strip()
        logging.info("✅ Статья получена через OpenRouter")
        return text, "OpenRouter"
    except Exception as e:
        logging.warning(f"⚠️ OpenRouter не сработал: {e}")

    # fallback на Groq
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.1-70b-versatile",
                "messages": [
                    {"role": "system", "content": "Ты — эксперт по искусственному интеллекту и высоким технологиям."},
                    {"role": "user", "content": PROMPT}
                ]
            }
        )
        r.raise_for_status()
        text = r.json()["choices"][0]["message"]["content"].strip()
        logging.info("✅ Статья получена через Groq")
        return text, "Groq"
    except Exception as e:
        logging.error(f"❌ Не удалось сгенерировать статью: {e}")
        return None, None

# -----------------------------
# Генерация изображения через FusionBrain
# -----------------------------
def generate_image(title, slug):
    logging.info("🎨 Генерация изображения через FusionBrain...")
    try:
        r = requests.post(
            "https://api.fusionbrain.ai/v1/text2image",
            headers={
                "Authorization": f"Bearer {FUSIONBRAIN_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "prompt": title,
                "width": 1024,
                "height": 1024,
                "num_images": 1
            }
        )
        r.raise_for_status()
        img_data = r.json()["images"][0]
        img_bytes = bytes(img_data, encoding='utf-8')
        os.makedirs(IMAGE_DIR, exist_ok=True)
        img_path = os.path.join(IMAGE_DIR, f"{slug}.png")
        with open(img_path, "wb") as f:
            f.write(base64.b64decode(img_data))
        logging.info(f"✅ Изображение сохранено: {img_path}")
        return img_path
    except Exception as e:
        logging.error(f"❌ Ошибка генерации изображения: {e}")
        placeholder = os.path.join(IMAGE_DIR, "placeholder.jpg")
        os.makedirs(IMAGE_DIR, exist_ok=True)
        if not os.path.exists(placeholder):
            with open(placeholder, "wb") as f:
                f.write(b"placeholder")
        return placeholder

# -----------------------------
# Сохраняем статью в content/posts
# -----------------------------
def save_article(title, text, model, img_path):
    slug = slugify(title)
    os.makedirs(CONTENT_DIR, exist_ok=True)
    filename = os.path.join(CONTENT_DIR, f"{slug}.md")
    image_relative = os.path.relpath(img_path, "static") if img_path else "/images/placeholder.jpg"
    content = f"""---
title: "{title}"
date: {datetime.utcnow().isoformat()}Z
model: "{model}"
image: "/images/posts/{os.path.basename(img_path)}"
---

{text}
"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    logging.info(f"✅ Статья сохранена: {filename}")
    return slug

# -----------------------------
# Обновляем галерею
# -----------------------------
def update_gallery(slug, title, img_path):
    os.makedirs(os.path.dirname(GALLERY_FILE), exist_ok=True)
    gallery = []
    if os.path.exists(GALLERY_FILE):
        with open(GALLERY_FILE, "r", encoding="utf-8") as f:
            gallery = yaml.safe_load(f) or []

    gallery.insert(0, {
        "src": f"/images/posts/{os.path.basename(img_path)}",
        "alt": title,
        "title": title
    })
    with open(GALLERY_FILE, "w", encoding="utf-8") as f:
        yaml.dump(gallery, f, allow_unicode=True)
    logging.info(f"✅ Галерея обновлена: {GALLERY_FILE}")

# -----------------------------
# Main
# -----------------------------
def main():
    text, model = generate_article()
    if not text:
        logging.error("Статья не сгенерирована. Прерывание.")
        return

    title = text.split("\n")[0][:60]  # первая строка как заголовок
    slug = slugify(title)
    img_path = generate_image(title, slug)
    save_article(title, text, model, img_path)
    update_gallery(slug, title, img_path)

if __name__ == "__main__":
    import base64
    main()
