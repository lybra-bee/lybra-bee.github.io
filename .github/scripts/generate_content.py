#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import time
import logging
import requests
from slugify import slugify
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Пути для сохранения
POSTS_DIR = "content/posts/"
GALLERY_FILE = "data/gallery.yaml"

# =========================
# Генерация статьи
# =========================
def generate_article():
    prompt = "Проанализируй последние тренды в искусственном интеллекте и высоких технологиях и напиши статью на 400-600 слов."
    
    # Основной генератор: Groq
    headers_groq = {
        "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
        "Content-Type": "application/json"
    }
    payload_groq = {
        "model": "openai/gpt-oss-20b",
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        r = requests.post("https://api.groq.com/v1/chat/completions", headers=headers_groq, json=payload_groq, timeout=60)
        r.raise_for_status()
        text = r.json()["choices"][0]["message"]["content"]
        logging.info("✅ Статья получена через Groq")
        return text, "Groq"
    except Exception as e:
        logging.warning(f"⚠️ Groq не сработал: {e}")

    # Запасной генератор: OpenRouter
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

# =========================
# Генерация изображения через FusionBrain Kandinsky
# =========================
class FusionBrainAPI:
    def __init__(self):
        self.URL = "https://api-key.fusionbrain.ai/"
        self.AUTH_HEADERS = {
            "X-Key": f"Key {os.getenv('FUSIONBRAIN_API_KEY')}",
            "X-Secret": f"Secret {os.getenv('FUSION_SECRET_KEY')}"
        }

    def get_pipeline(self):
        response = requests.get(self.URL + "key/api/v1/pipelines", headers=self.AUTH_HEADERS)
        response.raise_for_status()
        data = response.json()
        return data[0]["id"]

    def generate(self, prompt, pipeline_id, width=1024, height=1024):
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
            "pipeline_id": (None, pipeline_id),
            "params": (None, json.dumps(params), "application/json")
        }
        response = requests.post(self.URL + "key/api/v1/pipeline/run", headers=self.AUTH_HEADERS, files=data)
        response.raise_for_status()
        return response.json()["uuid"]

    def check_generation(self, request_id, attempts=10, delay=10):
        while attempts > 0:
            response = requests.get(self.URL + f"key/api/v1/pipeline/status/{request_id}", headers=self.AUTH_HEADERS)
            response.raise_for_status()
            data = response.json()
            if data["status"] == "DONE":
                return data["result"]["files"]
            attempts -= 1
            time.sleep(delay)
        return None

def generate_image(title, slug):
    api = FusionBrainAPI()
    try:
        pipeline_id = api.get_pipeline()
        uuid = api.generate(title, pipeline_id)
        files = api.check_generation(uuid)
        if files:
            img_path = f"assets/images/posts/{slug}.png"
            img_data = requests.get(files[0]).content
            os.makedirs(os.path.dirname(img_path), exist_ok=True)
            with open(img_path, "wb") as f:
                f.write(img_data)
            logging.info(f"✅ Изображение сохранено: {img_path}")
            return img_path
        else:
            logging.error("❌ Изображение не было сгенерировано")
            return None
    except Exception as e:
        logging.error(f"❌ Ошибка генерации изображения: {e}")
        return None

# =========================
# Сохранение статьи и обновление галереи
# =========================
def save_article(title, text):
    slug = slugify(title)
    date = datetime.now().strftime("%Y-%m-%d")
    filename = os.path.join(POSTS_DIR, f"{slug}.md")
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"---\ntitle: {title}\ndate: {date}\n---\n\n{text}")
    logging.info(f"✅ Статья сохранена: {filename}")
    return slug

def update_gallery(slug, img_path):
    import yaml
    os.makedirs(os.path.dirname(GALLERY_FILE), exist_ok=True)
    gallery = []
    if os.path.exists(GALLERY_FILE):
        with open(GALLERY_FILE, "r", encoding="utf-8") as f:
            gallery = yaml.safe_load(f) or []
    gallery.append({"slug": slug, "image": img_path})
    with open(GALLERY_FILE, "w", encoding="utf-8") as f:
        yaml.safe_dump(gallery, f, allow_unicode=True)
    logging.info(f"✅ Галерея обновлена: {GALLERY_FILE}")

# =========================
# Главная функция
# =========================
def main():
    text, source = generate_article()
    if not text:
        logging.error("❌ Статья не сгенерирована")
        return

    # Берем заголовок из первых 6 слов текста
    title = " ".join(text.split()[:6])
    slug = save_article(title, text)
    img_path = generate_image(title, slug)
    if img_path:
        update_gallery(slug, img_path)

if __name__ == "__main__":
    main()
