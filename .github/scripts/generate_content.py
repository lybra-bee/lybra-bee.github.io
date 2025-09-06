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
import yaml

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

# Переменные окружения (ключи)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
FUSIONBRAIN_KEY = os.getenv("FUSIONBRAIN_KEY")
FUSIONBRAIN_SECRET = os.getenv("FUSIONBRAIN_SECRET")

# Папки
POSTS_DIR = "content/posts"
GALLERY_FILE = "data/gallery.yaml"

# ------------------- GROQ ------------------- #
def generate_article(prompt=None):
    if not prompt:
        prompt = "Проанализируй последние тренды в искусственном интеллекте и высоких технологиях и напиши статью на 400-600 слов."
    url = "https://api.groq.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    try:
        r = requests.post(url, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
        text = data['choices'][0]['message']['content']
        logging.info("✅ Статья получена через Groq")
        return text, "Groq GPT-4o-mini"
    except Exception as e:
        logging.error(f"❌ Ошибка генерации статьи: {e}")
        return None, None

# ------------------- FusionBrain ------------------- #
class FusionBrainAPI:
    def __init__(self):
        self.URL = "https://api-key.fusionbrain.ai/"
        self.AUTH_HEADERS = {
            'X-Key': f'Key {FUSIONBRAIN_KEY}',
            'X-Secret': f'Secret {FUSIONBRAIN_SECRET}',
        }

    def get_pipeline(self):
        r = requests.get(self.URL + 'key/api/v1/pipelines', headers=self.AUTH_HEADERS)
        r.raise_for_status()
        data = r.json()
        return data[0]['uuid']  # UUID первой модели Kandinsky

    def generate(self, prompt, pipeline_id, width=1024, height=1024):
        params = {
            "type": "GENERATE",
            "numImages": 1,
            "width": width,
            "height": height,
            "generateParams": {"query": prompt}
        }
        files = {
            'pipeline_id': (None, pipeline_id),
            'params': (None, json.dumps(params), 'application/json')
        }
        r = requests.post(self.URL + 'key/api/v1/pipeline/run', headers=self.AUTH_HEADERS, files=files)
        r.raise_for_status()
        data = r.json()
        return data['uuid']

    def check_generation(self, request_id, attempts=10, delay=5):
        while attempts > 0:
            r = requests.get(self.URL + f'key/api/v1/pipeline/status/{request_id}', headers=self.AUTH_HEADERS)
            r.raise_for_status()
            data = r.json()
            if data['status'] == 'DONE':
                return data['result']['files'][0]  # Base64
            elif data['status'] == 'FAIL':
                raise Exception("Ошибка генерации изображения")
            attempts -= 1
            time.sleep(delay)
        raise Exception("Превышено время ожидания генерации изображения")

# ------------------- Сохранение статьи ------------------- #
def save_article(title, text, model):
    slug = slugify(title)
    filename = f"{POSTS_DIR}/{slug}.md"
    date = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    content = f"---\ntitle: \"{title}\"\ndate: {date}\nmodel: {model}\nimage: /images/{slug}.png\ntype: posts\n---\n\n{text}\n"
    os.makedirs(POSTS_DIR, exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    logging.info(f"✅ Статья сохранена: {filename}")
    return slug

# ------------------- Сохранение изображения ------------------- #
def save_image(slug, b64_content):
    os.makedirs("static/images", exist_ok=True)
    path = f"static/images/{slug}.png"
    img_data = base64.b64decode(b64_content)
    with open(path, "wb") as f:
        f.write(img_data)
    logging.info(f"✅ Изображение сохранено: {path}")
    return f"/images/{slug}.png"

# ------------------- Обновление галереи ------------------- #
def update_gallery(slug, title, img_url):
    gallery = []
    if os.path.exists(GALLERY_FILE):
        with open(GALLERY_FILE, "r", encoding="utf-8") as f:
            gallery = yaml.safe_load(f) or []
    gallery.insert(0, {"src": img_url, "alt": title, "title": title})
    with open(GALLERY_FILE, "w", encoding="utf-8") as f:
        yaml.dump(gallery, f, allow_unicode=True)
    logging.info(f"✅ Галерея обновлена: {GALLERY_FILE}")

# ------------------- Основной блок ------------------- #
def main():
    logging.info("📝 Генерация статьи...")
    text, model = generate_article()
    if not text:
        logging.error("❌ Статья не сгенерирована")
        return

    title = text.split('\n')[0][:80]  # Заголовок — первая строка
    slug = save_article(title, text, model)

    logging.info("🎨 Генерация изображения через FusionBrain...")
    try:
        api = FusionBrainAPI()
        pipeline_id = api.get_pipeline()
        uuid = api.generate(title, pipeline_id)
        b64_image = api.check_generation(uuid)
        img_url = save_image(slug, b64_image)
        update_gallery(slug, title, img_url)
    except Exception as e:
        logging.error(f"❌ Ошибка генерации изображения: {e}")

if __name__ == "__main__":
    main()
