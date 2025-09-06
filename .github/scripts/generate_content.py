#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import requests
import time
import logging
from datetime import datetime
from slugify import slugify
import base64

# Логи
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Пути
POSTS_DIR = "content/posts"
IMAGES_DIR = "assets/images/posts"
GALLERY_FILE = "data/gallery.yaml"

# API ключи из переменных окружения
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
FUSION_API_KEY = os.getenv("FUSIONBRAIN_API_KEY")
FUSION_SECRET_KEY = os.getenv("FUSION_SECRET_KEY")

# Генерация статьи через OpenRouter
def generate_article():
    prompt = "Проанализируй последние тренды в искусственном интеллекте и высоких технологиях и напиши статью на 400-600 слов."
    
    headers_or = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
    payload_or = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }

    try:
        r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers_or, json=payload_or)
        r.raise_for_status()
        text = r.json()["choices"][0]["message"]["content"]
        logging.info("✅ Статья получена через OpenRouter")
        return text, "OpenRouter"
    except Exception as e:
        logging.warning(f"⚠️ OpenRouter не сработал: {e}")
    
    # fallback на Groq
    headers_groq = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload_groq = {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}], "temperature": 0.7}
    try:
        r = requests.post("https://api.groq.com/v1/chat/completions", headers=headers_groq, json=payload_groq)
        r.raise_for_status()
        text = r.json()["choices"][0]["message"]["content"]
        logging.info("✅ Статья получена через Groq")
        return text, "Groq"
    except Exception as e:
        logging.error(f"❌ Ошибка генерации статьи: {e}")
        return None, None

# FusionBrain API для Kandinsky
class FusionBrainAPI:
    def __init__(self, url, api_key, secret_key):
        self.URL = url
        self.AUTH_HEADERS = {
            "X-Key": f"Key {api_key}",
            "X-Secret": f"Secret {secret_key}"
        }

    def get_pipeline(self):
        r = requests.get(self.URL + "key/api/v1/pipelines", headers=self.AUTH_HEADERS)
        r.raise_for_status()
        return r.json()[0]["id"]

    def generate(self, prompt, pipeline_id, images=1, width=1024, height=1024):
        params = {
            "type": "GENERATE",
            "numImages": images,
            "width": width,
            "height": height,
            "generateParams": {"query": prompt}
        }
        data = {"pipeline_id": (None, pipeline_id), "params": (None, json.dumps(params), "application/json")}
        r = requests.post(self.URL + "key/api/v1/pipeline/run", headers=self.AUTH_HEADERS, files=data)
        r.raise_for_status()
        return r.json()["uuid"]

    def check_generation(self, request_id, attempts=20, delay=5):
        while attempts > 0:
            r = requests.get(self.URL + f"key/api/v1/pipeline/status/{request_id}", headers=self.AUTH_HEADERS)
            r.raise_for_status()
            data = r.json()
            if data.get("status") == "DONE":
                return data["result"]["files"]
            attempts -= 1
            time.sleep(delay)
        return []

# Генерация изображения
def generate_image(title, slug):
    try:
        api = FusionBrainAPI("https://api-key.fusionbrain.ai/", FUSION_API_KEY, FUSION_SECRET_KEY)
        pipeline_id = api.get_pipeline()
        uuid = api.generate(title, pipeline_id)
        files = api.check_generation(uuid)
        if not files:
            raise Exception("Нет файлов после генерации")
        img_data = base64.b64decode(files[0])
        os.makedirs(IMAGES_DIR, exist_ok=True)
        img_path = os.path.join(IMAGES_DIR, f"{slug}.jpg")
        with open(img_path, "wb") as f:
            f.write(img_data)
        logging.info(f"✅ Изображение сохранено: {img_path}")
        return img_path
    except Exception as e:
        logging.error(f"❌ Ошибка генерации изображения: {e}")
        return None

# Сохранение статьи
def save_article(title, text, model):
    slug = slugify(title)
    os.makedirs(POSTS_DIR, exist_ok=True)
    file_path = os.path.join(POSTS_DIR, f"{slug}.md")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(f"---\n")
        f.write(f"title: \"{title}\"\n")
        f.write(f"date: {datetime.utcnow().isoformat()}Z\n")
        f.write(f"model: {model}\n")
        f.write(f"image: /images/posts/{slug}.jpg\n")
        f.write(f"---\n\n{text}")
    logging.info(f"✅ Статья сохранена: {file_path}")
    return slug

# Обновление галереи
def update_gallery(slug, title):
    import yaml
    os.makedirs(os.path.dirname(GALLERY_FILE), exist_ok=True)
    gallery = []
    if os.path.exists(GALLERY_FILE):
        with open(GALLERY_FILE, "r", encoding="utf-8") as f:
            gallery = yaml.safe_load(f) or []
    entry = {"src": f"/images/posts/{slug}.jpg", "alt": title, "title": title}
    if entry not in gallery:
        gallery.insert(0, entry)
    with open(GALLERY_FILE, "w", encoding="utf-8") as f:
        yaml.dump(gallery, f, allow_unicode=True)
    logging.info(f"✅ Галерея обновлена: {GALLERY_FILE}")

# Главная функция
def main():
    text, model = generate_article()
    if not text:
        logging.error("❌ Статья не сгенерирована")
        return
    title = text.strip().split("\n")[0][:60]
    slug = save_article(title, text, model)
    generate_image(title, slug)
    update_gallery(slug, title)

if __name__ == "__main__":
    main()
