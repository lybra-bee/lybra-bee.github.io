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

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Пути сохранения
POSTS_DIR = "content/posts"
IMAGES_DIR = "static/images"
GALLERY_FILE = "data/gallery.yaml"

# Генерация статьи через Groq и OpenRouter
def generate_article():
    prompt = "Проанализируй последние тренды в искусственном интеллекте и высоких технологиях и напиши статью на 400-600 слов."
    headers_groq = {
        "Authorization": f"Bearer {os.getenv('GROQ_KEY')}",
        "Content-Type": "application/json"
    }
    groq_payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        r = requests.post("https://api.groq.com/v1/chat/completions", headers=headers_groq, json=groq_payload, timeout=60)
        r.raise_for_status()
        text = r.json()["choices"][0]["message"]["content"]
        logging.info("✅ Статья получена через Groq")
        return text, "Groq"
    except Exception as e:
        logging.warning(f"⚠️ Groq не сработал: {e}")

    # Запасной вариант: OpenRouter
    headers_or = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_KEY')}",
        "Content-Type": "application/json"
    }
    payload_or = {
        "model": "gpt-4.1-mini",
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers_or, json=payload_or, timeout=60)
        r.raise_for_status()
        text = r.json()["completion"]
        logging.info("✅ Статья получена через OpenRouter")
        return text, "OpenRouter"
    except Exception as e:
        logging.error(f"❌ Ошибка генерации статьи: {e}")
        return None, None

# Генерация изображения через FusionBrain/Kandinsky
class FusionBrainAPI:
    def __init__(self):
        self.URL = "https://api-key.fusionbrain.ai/"
        self.AUTH_HEADERS = {
            "X-Key": f"Key {os.getenv('FUSIONBRAIN_API_KEY')}",
            "X-Secret": f"Secret {os.getenv('FUSION_SECRET_KEY')}"
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
        files = {
            "pipeline_id": (None, pipeline_id),
            "params": (None, json.dumps(params), "application/json")
        }
        r = requests.post(self.URL + "key/api/v1/pipeline/run", headers=self.AUTH_HEADERS, files=files)
        r.raise_for_status()
        return r.json()["uuid"]

    def check_generation(self, uuid, attempts=10, delay=5):
        while attempts > 0:
            r = requests.get(self.URL + "key/api/v1/pipeline/status/" + uuid, headers=self.AUTH_HEADERS)
            r.raise_for_status()
            data = r.json()
            if data["status"] == "DONE":
                return data["result"]["files"][0]
            elif data["status"] == "FAIL":
                raise Exception("Ошибка генерации изображения")
            time.sleep(delay)
            attempts -= 1
        raise Exception("Превышено время ожидания генерации изображения")

def generate_image(prompt, filename_slug):
    try:
        api = FusionBrainAPI()
        pipeline_id = api.get_pipeline()
        uuid = api.generate(prompt, pipeline_id)
        img_base64 = api.check_generation(uuid)
        img_data = base64.b64decode(img_base64)
        img_path = os.path.join(IMAGES_DIR, f"{filename_slug}.png")
        with open(img_path, "wb") as f:
            f.write(img_data)
        logging.info(f"✅ Изображение сохранено: {img_path}")
        return img_path
    except Exception as e:
        logging.error(f"❌ Ошибка генерации изображения: {e}")
        return None

# Обновление галереи
def update_gallery(title, image_path, slug):
    entry = f"- src: /{image_path}\n  alt: {title}\n  title: {title}\n"
    if os.path.exists(GALLERY_FILE):
        with open(GALLERY_FILE, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        content = ""
    content = entry + content
    with open(GALLERY_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    logging.info(f"✅ Галерея обновлена: {GALLERY_FILE}")

# Сохранение статьи
def save_article(title, text):
    slug = slugify(title)
    filename = os.path.join(POSTS_DIR, f"{slug}.md")
    if not os.path.exists(POSTS_DIR):
        os.makedirs(POSTS_DIR)
    front_matter = f"---\ntitle: \"{title}\"\ndate: {datetime.now().isoformat()}\nimage: /{IMAGES_DIR}/{slug}.png\nmodel: generated\n---\n\n"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(front_matter + text)
    logging.info(f"✅ Статья сохранена: {filename}")
    return slug

# Основной поток
def main():
    text, model = generate_article()
    if text is None:
        logging.error("❌ Статья не сгенерирована")
        return

    title = text.split("\n")[0][:80]  # берем первую строку как заголовок
    slug = save_article(title, text)
    img_path = generate_image(title, slug)
    if img_path:
        update_gallery(title, img_path, slug)

if __name__ == "__main__":
    main()
