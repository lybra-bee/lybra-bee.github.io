#!/usr/bin/env python3
import os
import json
import requests
import logging
from datetime import datetime
from slugify import slugify
import base64
import time
import yaml

# === Настройка логирования ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# === Ключи и URL ===
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
FUSIONBRAIN_KEY = os.environ.get("FUSIONBRAIN_KEY")
FUSIONBRAIN_SECRET = os.environ.get("FUSIONBRAIN_SECRET")

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
FUSIONBRAIN_URL = "https://api-key.fusionbrain.ai/"

# === Промпт для статьи ===
PROMPT = "Проанализируй последние тренды в искусственном интеллекте и высоких технологиях и напиши статью на 400-600 слов."

# === Пути ===
POSTS_DIR = "content/posts/"
IMAGES_DIR = "static/images/"
GALLERY_FILE = "data/gallery.yaml"

os.makedirs(POSTS_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

# === Функция генерации статьи через Groq ===
def generate_article_groq():
    try:
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": PROMPT}]
        }
        r = requests.post(GROQ_URL, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
        text = data["choices"][0]["message"]["content"]
        return text, "Groq"
    except Exception as e:
        logging.warning(f"⚠️ Groq не сработал: {e}")
        return None, None

# === Функция генерации статьи через OpenRouter ===
def generate_article_openrouter():
    try:
        headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": PROMPT}]
        }
        r = requests.post(OPENROUTER_URL, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
        text = data["choices"][0]["message"]["content"]
        return text, "OpenRouter"
    except Exception as e:
        logging.error(f"❌ OpenRouter не сработал: {e}")
        return None, None

# === Класс для работы с FusionBrain Kandinsky ===
class FusionBrainAPI:
    def __init__(self, url, api_key, secret_key):
        self.URL = url
        self.AUTH_HEADERS = {
            'X-Key': f'Key {api_key}',
            'X-Secret': f'Secret {secret_key}',
        }

    def get_pipeline(self):
        response = requests.get(self.URL + 'key/api/v1/pipelines', headers=self.AUTH_HEADERS)
        response.raise_for_status()
        data = response.json()
        return data[0]['id']

    def generate_image(self, prompt, pipeline_id, width=1024, height=1024):
        params = {
            "type": "GENERATE",
            "numImages": 1,
            "width": width,
            "height": height,
            "generateParams": {
                "query": prompt
            }
        }
        data = {
            'pipeline_id': (None, pipeline_id),
            'params': (None, json.dumps(params), 'application/json')
        }
        r = requests.post(self.URL + 'key/api/v1/pipeline/run', headers=self.AUTH_HEADERS, files=data)
        r.raise_for_status()
        uuid = r.json()['uuid']
        return uuid

    def check_generation(self, request_id, attempts=10, delay=10):
        while attempts > 0:
            r = requests.get(self.URL + f'key/api/v1/pipeline/status/{request_id}', headers=self.AUTH_HEADERS)
            r.raise_for_status()
            data = r.json()
            if data['status'] == 'DONE':
                return data['result']['files'][0]
            elif data['status'] == 'FAIL':
                raise Exception(f"Генерация изображения не удалась: {data.get('errorDescription')}")
            attempts -= 1
            time.sleep(delay)
        raise Exception("Таймаут ожидания изображения")

# === Сохранение статьи ===
def save_article(title, text, model):
    slug = slugify(title)
    date = datetime.utcnow().strftime("%Y-%m-%d")
    filename = f"{POSTS_DIR}{slug}.md"
    content = f"""---
title: "{title}"
date: {date}T00:00:00Z
draft: false
model: {model}
image: "/images/{slug}.png"
---

{text}
"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    logging.info(f"✅ Статья сохранена: {filename}")
    return slug

# === Сохранение изображения ===
def save_image(image_b64, slug):
    img_data = base64.b64decode(image_b64)
    path = f"{IMAGES_DIR}{slug}.png"
    with open(path, "wb") as f:
        f.write(img_data)
    logging.info(f"✅ Изображение сохранено: {path}")

# === Обновление галереи ===
def update_gallery(title, slug):
    entry = {"title": title, "src": f"/images/{slug}.png", "alt": title}
    gallery = []
    if os.path.exists(GALLERY_FILE):
        with open(GALLERY_FILE, "r", encoding="utf-8") as f:
            gallery = yaml.safe_load(f) or []
    gallery = [entry] + gallery[:9]  # оставляем максимум 10
    with open(GALLERY_FILE, "w", encoding="utf-8") as f:
        yaml.dump(gallery, f, allow_unicode=True)
    logging.info(f"✅ Галерея обновлена: {GALLERY_FILE}")

# === Главная функция ===
def main():
    logging.info("📝 Генерация статьи...")

    text, model = generate_article_groq()
    if not text:
        text, model = generate_article_openrouter()
        if not text:
            logging.error("❌ Статья не сгенерирована")
            return

    title = text.split("\n")[0][:60]  # первая строка как заголовок
    slug = save_article(title, text, model)

    logging.info("🎨 Генерация изображения через FusionBrain...")
    try:
        fb = FusionBrainAPI(FUSIONBRAIN_URL, FUSIONBRAIN_KEY, FUSIONBRAIN_SECRET)
        pipeline_id = fb.get_pipeline()
        uuid = fb.generate_image(title, pipeline_id)
        image_b64 = fb.check_generation(uuid)
        save_image(image_b64, slug)
    except Exception as e:
        logging.error(f"❌ Ошибка генерации изображения: {e}")

    update_gallery(title, slug)

if __name__ == "__main__":
    main()
