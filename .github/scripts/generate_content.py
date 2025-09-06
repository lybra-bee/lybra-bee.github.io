#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import requests
import logging
import time
from datetime import datetime
from slugify import slugify
import yaml

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# =======================
# Настройки API
# =======================

# OpenRouter (или Groq) - рабочие ключи и URL как в старом скрипте
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "твоя_копия_ключа")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "твоя_копия_ключа")
GROQ_URL = "https://api.groq.com/v1/chat/completions"

# FusionBrain Kandinsky
FUSIONBRAIN_KEY = os.environ.get("FUSIONBRAIN_KEY", "твоя_копия_ключа")
FUSIONBRAIN_SECRET = os.environ.get("FUSIONBRAIN_SECRET", "твоя_копия_секрета")
FUSIONBRAIN_URL = "https://api-key.fusionbrain.ai/"


# =======================
# Генерация статьи
# =======================

def generate_article():
    prompt = "Проанализируй последние тренды в искусственном интеллекте и высоких технологиях и напиши статью на 400-600 слов."
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }

    try:
        r = requests.post(OPENROUTER_URL, headers=headers, json=data)
        r.raise_for_status()
        result = r.json()
        text = result['choices'][0]['message']['content']
        logging.info("✅ Статья получена через OpenRouter")
        return text, "OpenRouter GPT"
    except Exception as e:
        logging.error(f"❌ Ошибка генерации статьи: {e}")
        # Попытка через Groq
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
        data = {
            "model": "groq:chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
        try:
            r = requests.post(GROQ_URL, headers=headers, json=data)
            r.raise_for_status()
            result = r.json()
            text = result['choices'][0]['message']['content']
            logging.info("✅ Статья получена через Groq")
            return text, "Groq Chat"
        except Exception as e2:
            logging.error(f"❌ Ошибка генерации статьи: {e2}")
            return None, None

# =======================
# Генерация изображения
# =======================

class FusionBrainAPI:
    def __init__(self, url, api_key, secret_key):
        self.URL = url
        self.AUTH_HEADERS = {
            'X-Key': f'Key {api_key}',
            'X-Secret': f'Secret {secret_key}',
        }

    def get_pipeline(self):
        response = requests.get(self.URL + 'key/api/v1/pipelines', headers=self.AUTH_HEADERS)
        data = response.json()
        return data[0]['id']

    def generate(self, prompt, pipeline_id, images=1, width=1024, height=1024):
        params = {
            "type": "GENERATE",
            "numImages": images,
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
        response = requests.post(self.URL + 'key/api/v1/pipeline/run', headers=self.AUTH_HEADERS, files=data)
        response.raise_for_status()
        return response.json()['uuid']

    def check_generation(self, request_id, attempts=10, delay=10):
        while attempts > 0:
            response = requests.get(self.URL + 'key/api/v1/pipeline/status/' + request_id, headers=self.AUTH_HEADERS)
            data = response.json()
            if data['status'] == 'DONE':
                return data['result']['files']
            attempts -= 1
            time.sleep(delay)
        return None

def generate_image(prompt, slug):
    try:
        api = FusionBrainAPI(FUSIONBRAIN_URL, FUSIONBRAIN_KEY, FUSIONBRAIN_SECRET)
        pipeline_id = api.get_pipeline()
        uuid = api.generate(prompt, pipeline_id)
        files = api.check_generation(uuid)
        if not files:
            logging.error("❌ Ошибка генерации изображения: файл не получен")
            return None
        img_base64 = files[0]
        img_data = base64.b64decode(img_base64.split(",")[-1])
        os.makedirs("static/images/posts", exist_ok=True)
        img_path = f"static/images/posts/{slug}.png"
        with open(img_path, "wb") as f:
            f.write(img_data)
        logging.info(f"✅ Изображение сохранено: {img_path}")
        return f"/images/posts/{slug}.png"
    except Exception as e:
        logging.error(f"❌ Ошибка генерации изображения: {e}")
        return None

# =======================
# Сохранение статьи
# =======================

def save_post(title, text, model, image_path):
    slug = slugify(title)
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"content/posts/{slug}.md"
    os.makedirs("content/posts", exist_ok=True)
    content = f"""---
title: "{title}"
date: {date_str}
draft: false
type: posts
model: {model}
image: "{image_path if image_path else ''}"
---

{text}
"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    logging.info(f"✅ Статья сохранена: {filename}")
    return slug

# =======================
# Обновление галереи
# =======================

def update_gallery(title, image_path):
    slug = slugify(title)
    gallery_file = "data/gallery.yaml"
    os.makedirs("data", exist_ok=True)
    gallery = []
    if os.path.exists(gallery_file):
        with open(gallery_file, "r", encoding="utf-8") as f:
            gallery = yaml.safe_load(f) or []
    gallery.insert(0, {"title": title, "src": image_path, "alt": title})
    gallery = gallery[:20]  # оставляем последние 20
    with open(gallery_file, "w", encoding="utf-8") as f:
        yaml.safe_dump(gallery, f, allow_unicode=True)
    logging.info(f"✅ Галерея обновлена: {gallery_file}")

# =======================
# Основной процесс
# =======================

def main():
    text, model = generate_article()
    if not text:
        logging.error("❌ Статья не сгенерирована")
        return
    title = text.split("\n")[0][:60]  # заголовок берем из первых 60 символов
    slug = slugify(title)
    image_path = generate_image(title, slug)
    save_post(title, text, model, image_path)
    if image_path:
        update_gallery(title, image_path)

if __name__ == "__main__":
    main()
