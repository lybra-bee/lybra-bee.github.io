#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import requests
import logging
import time
from datetime import datetime
from slugify import slugify
import base64

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Настройки директорий ---
POSTS_DIR = "content/posts"
IMAGES_DIR = "static/images/posts"
GALLERY_FILE = "data/gallery.yaml"

os.makedirs(POSTS_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(os.path.dirname(GALLERY_FILE), exist_ok=True)

# --- API ключи из env ---
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
FUSIONBRAIN_API_KEY = os.getenv("FUSIONBRAIN_API_KEY")
FUSIONBRAIN_SECRET_KEY = os.getenv("FUSION_SECRET_KEY")

# --- Генерация статьи ---
def generate_article():
    prompt = "Проанализируй последние тренды в искусственном интеллекте и высоких технологиях и напиши статью на 400-600 слов."
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        r = requests.post("https://api.groq.com/v1/chat/completions", headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
        text = data["choices"][0]["message"]["content"]
        return text.strip()
    except Exception as e:
        logging.error(f"❌ Ошибка генерации статьи: {e}")
        return None

# --- Генерация изображения через FusionBrain Kandinsky ---
class FusionBrainAPI:
    def __init__(self, api_key, secret_key):
        self.URL = "https://api-key.fusionbrain.ai/"
        self.AUTH_HEADERS = {
            "X-Key": f"Key {api_key}",
            "X-Secret": f"Secret {secret_key}"
        }

    def get_pipeline(self):
        r = requests.get(self.URL + "key/api/v1/pipelines", headers=self.AUTH_HEADERS)
        r.raise_for_status()
        data = r.json()
        return data[0]["id"]

    def generate(self, prompt, pipeline_id, width=1024, height=1024):
        params = {
            "type": "GENERATE",
            "numImages": 1,
            "width": width,
            "height": height,
            "generateParams": {"query": prompt}
        }
        files = {"pipeline_id": (None, pipeline_id), "params": (None, json.dumps(params), "application/json")}
        r = requests.post(self.URL + "key/api/v1/pipeline/run", headers=self.AUTH_HEADERS, files=files)
        r.raise_for_status()
        return r.json()["uuid"]

    def check_generation(self, uuid, attempts=15, delay=5):
        for _ in range(attempts):
            r = requests.get(self.URL + f"key/api/v1/pipeline/status/{uuid}", headers=self.AUTH_HEADERS)
            r.raise_for_status()
            data = r.json()
            if data["status"] == "DONE":
                return data["result"]["files"]
            elif data["status"] == "FAIL":
                raise Exception("Генерация изображения не удалась")
            time.sleep(delay)
        raise Exception("Превышено время ожидания генерации изображения")

def generate_image(title, slug):
    try:
        fusion = FusionBrainAPI(FUSIONBRAIN_API_KEY, FUSIONBRAIN_SECRET_KEY)
        pipeline_id = fusion.get_pipeline()
        uuid = fusion.generate(title, pipeline_id)
        files_base64 = fusion.check_generation(uuid)
        if files_base64:
            img_data = base64.b64decode(files_base64[0])
            img_path = os.path.join(IMAGES_DIR, f"{slug}.jpg")
            with open(img_path, "wb") as f:
                f.write(img_data)
            logging.info(f"✅ Изображение сохранено: {img_path}")
            return f"/images/posts/{slug}.jpg"
        return None
    except Exception as e:
        logging.error(f"❌ Ошибка генерации изображения: {e}")
        return "/images/placeholder.jpg"

# --- Сохранение статьи ---
def save_post(title, text, image_url):
    slug = slugify(title)
    filepath = os.path.join(POSTS_DIR, f"{slug}.md")
    date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    md_content = f"""---
title: "{title}"
date: {date}
draft: false
image: "{image_url}"
model: Groq GPT
---

{text}
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(md_content)
    logging.info(f"✅ Статья сохранена: {filepath}")
    return slug

# --- Обновление галереи ---
def update_gallery(title, image_url):
    slug = slugify(title)
    item = f"- src: \"{image_url}\"\n  alt: \"{title}\"\n  title: \"{title}\"\n"
    existing = ""
    if os.path.exists(GALLERY_FILE):
        with open(GALLERY_FILE, "r", encoding="utf-8") as f:
            existing = f.read()
    with open(GALLERY_FILE, "w", encoding="utf-8") as f:
        f.write(item + existing)
    logging.info(f"✅ Галерея обновлена: {GALLERY_FILE}")

# --- Основной процесс ---
def main():
    logging.info("📝 Генерация статьи...")
    article_text = generate_article()
    if not article_text:
        logging.error("❌ Статья не сгенерирована")
        return

    title = article_text.split("\n")[0][:80]  # берем первую строку как заголовок
    slug = slugify(title)
    logging.info(f"Заголовок: {title}")

    logging.info("🎨 Генерация изображения через FusionBrain...")
    image_url = generate_image(title, slug)

    save_post(title, article_text, image_url)
    update_gallery(title, image_url)

if __name__ == "__main__":
    main()
