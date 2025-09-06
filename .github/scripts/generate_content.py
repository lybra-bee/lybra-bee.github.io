#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import time
import requests
import logging
from datetime import datetime
from slugify import slugify
import yaml
import base64

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ===== Параметры генерации =====
GROQ_API_URL = "https://api.groq.com/v1/chat/completions"
GROQ_API_KEY = "ВАШ_GROQ_KEY"

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = "ВАШ_OPENROUTER_KEY"

FUSIONBRAIN_URL = "https://api-key.fusionbrain.ai/"
FUSIONBRAIN_KEY = "ВАШ_FUSIONBRAIN_KEY"
FUSIONBRAIN_SECRET = "ВАШ_FUSIONBRAIN_SECRET"

POSTS_DIR = "content/posts"
IMAGES_DIR = "static/images/posts"
GALLERY_FILE = "data/gallery.yaml"

# ===== Функции генерации статьи =====
def generate_article():
    prompt = "Проанализируй последние тренды в искусственном интеллекте и высоких технологиях и напиши статью на 400-600 слов."
    headers_groq = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    data_groq = {"model": "gpt-4", "messages": [{"role": "user", "content": prompt}]}

    try:
        r = requests.post(GROQ_API_URL, headers=headers_groq, json=data_groq)
        r.raise_for_status()
        result = r.json()
        text = result["choices"][0]["message"]["content"]
        logging.info("✅ Статья получена через Groq")
        return text, "Groq"
    except Exception as e:
        logging.warning(f"⚠️ Groq не сработал: {e}")
        # Пытаемся через OpenRouter
        headers_or = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
        data_or = {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}]}
        try:
            r = requests.post(OPENROUTER_API_URL, headers=headers_or, json=data_or)
            r.raise_for_status()
            result = r.json()
            text = result["choices"][0]["message"]["content"]
            logging.info("✅ Статья получена через OpenRouter")
            return text, "OpenRouter"
        except Exception as e2:
            logging.error(f"❌ Ошибка генерации статьи: {e2}")
            return None, None

# ===== Функции генерации изображения =====
class FusionBrainAPI:
    def __init__(self, url, api_key, secret_key):
        self.URL = url
        self.AUTH_HEADERS = {
            'X-Key': f'Key {api_key}',
            'X-Secret': f'Secret {secret_key}',
        }

    def get_pipeline(self):
        response = requests.get(self.URL + "key/api/v1/pipelines", headers=self.AUTH_HEADERS)
        response.raise_for_status()
        data = response.json()
        return data[0]['id']

    def generate(self, prompt, pipeline_id, width=1024, height=1024):
        params = {
            "type": "GENERATE",
            "numImages": 1,
            "width": width,
            "height": height,
            "generateParams": {"query": prompt}
        }
        data = {
            'pipeline_id': (None, pipeline_id),
            'params': (None, json.dumps(params), 'application/json')
        }
        r = requests.post(self.URL + "key/api/v1/pipeline/run", headers=self.AUTH_HEADERS, files=data)
        r.raise_for_status()
        return r.json()['uuid']

    def check_generation(self, request_id, attempts=10, delay=5):
        while attempts > 0:
            r = requests.get(self.URL + f"key/api/v1/pipeline/status/{request_id}", headers=self.AUTH_HEADERS)
            r.raise_for_status()
            data = r.json()
            if data['status'] == 'DONE':
                return data['result']['files'][0]
            time.sleep(delay)
            attempts -= 1
        return None

def generate_image(title, slug):
    try:
        api = FusionBrainAPI(FUSIONBRAIN_URL, FUSIONBRAIN_KEY, FUSIONBRAIN_SECRET)
        pipeline_id = api.get_pipeline()
        uuid = api.generate(title, pipeline_id)
        file_url = api.check_generation(uuid)
        if not file_url:
            logging.error("❌ Не удалось получить изображение")
            return None

        img_data = requests.get(file_url).content
        img_path = os.path.join(IMAGES_DIR, f"{slug}.png")
        os.makedirs(IMAGES_DIR, exist_ok=True)
        with open(img_path, "wb") as f:
            f.write(img_data)
        logging.info(f"✅ Изображение сохранено: {img_path}")
        return img_path
    except Exception as e:
        logging.error(f"❌ Ошибка генерации изображения: {e}")
        return None

# ===== Сохранение статьи =====
def save_article(title, text, model):
    slug = slugify(title)
    os.makedirs(POSTS_DIR, exist_ok=True)
    filename = os.path.join(POSTS_DIR, f"{slug}.md")
    date_str = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    content = f"""---
title: "{title}"
date: {date_str}
model: {model}
image: /images/posts/{slug}.png
---

{text}
"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    logging.info(f"✅ Статья сохранена: {filename}")
    return slug

# ===== Обновление галереи =====
def update_gallery(slug, title):
    os.makedirs(os.path.dirname(GALLERY_FILE), exist_ok=True)
    gallery = []
    if os.path.exists(GALLERY_FILE):
        with open(GALLERY_FILE, "r", encoding="utf-8") as f:
            gallery = yaml.safe_load(f) or []
    gallery.append({
        "src": f"/images/posts/{slug}.png",
        "alt": title,
        "title": title
    })
    with open(GALLERY_FILE, "w", encoding="utf-8") as f:
        yaml.safe_dump(gallery, f, allow_unicode=True)
    logging.info(f"✅ Галерея обновлена: {GALLERY_FILE}")

# ===== Основной процесс =====
def main():
    title = f"Последние тренды AI {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
    text, model = generate_article()
    if not text:
        logging.error("❌ Статья не сгенерирована")
        return

    slug = slugify(title)
    img_path = generate_image(title, slug)  # картинка по заголовку
    save_article(title, text, model)
    if img_path:
        update_gallery(slug, title)

if __name__ == "__main__":
    main()
