#!/usr/bin/env python3
import os
import json
import requests
import random
import logging
import time
from pathlib import Path
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Пути
BASE_DIR = Path(__file__).parent.parent
CONTENT_DIR = BASE_DIR / "content/posts"
GALLERY_DIR = BASE_DIR / "static/images/gallery"

# Проверяем директорию галереи
if GALLERY_DIR.exists() and not GALLERY_DIR.is_dir():
    logging.warning(f"{GALLERY_DIR} существует, но это не директория. Удаляем и создаём папку.")
    GALLERY_DIR.unlink()  # удаляем файл

GALLERY_DIR.mkdir(parents=True, exist_ok=True)
CONTENT_DIR.mkdir(parents=True, exist_ok=True)

# Ключи из секретов GitHub Actions
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
FUSIONBRAIN_API_KEY = os.environ.get("FUSIONBRAIN_API_KEY")
FUSION_SECRET_KEY = os.environ.get("FUSION_SECRET_KEY")

# Генерация статьи через Groq
def generate_article():
    logging.info("📝 Генерация статьи через Groq")
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"} if GROQ_API_KEY else {}
    payload = {
        "prompt": "Напиши статью на русском языке о последних трендах в нейросетях и высоких технологиях, стиль информационный, объем около 500 слов.",
        "max_output_tokens": 1000
    }
    try:
        if GROQ_API_KEY:
            response = requests.post("https://api.groq.ai/v1/complete", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            content = data.get("completion", "")
        else:
            # Фолбек без ключа: используем public API https://api.quotable.io/random как заглушку текста
            logging.warning("❌ GROQ API недоступен, используем фолбек")
            content = "Это пример статьи о нейросетях и высоких технологиях. Появились новые тренды..."
        title = content.split('\n')[0][:50]  # заголовок берем из первой строки
        return title, content
    except Exception as e:
        logging.error(f"Ошибка при генерации статьи: {e}")
        raise

# Генерация изображения через FusionBrain
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
        return data[0]['uuid']

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
        return []

def generate_image(prompt):
    logging.info("🎨 Генерация изображения через FusionBrain")
    try:
        api = FusionBrainAPI('https://api-key.fusionbrain.ai/', FUSIONBRAIN_API_KEY, FUSION_SECRET_KEY)
        pipeline_id = api.get_pipeline()
        uuid = api.generate(prompt, pipeline_id)
        files = api.check_generation(uuid)
        if files:
            image_data = files[0]
            image_path = GALLERY_DIR / f"{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
            with open(image_path, "wb") as f:
                f.write(bytes(image_data, 'utf-8'))  # Base64 нужно будет декодировать при необходимости
            return image_path.name
        else:
            logging.warning("❌ Изображение не сгенерировано")
            return ""
    except Exception as e:
        logging.error(f"❌ Ошибка генерации изображения FusionBrain: {e}")
        return ""

# Сохранение статьи
def save_article(title, content, image_name):
    filename = f"{title.replace(' ', '-').lower()[:50]}.md"
    filepath = CONTENT_DIR / filename
    md_content = f"""---
title: "{title}"
date: {datetime.now().isoformat()}
image: "/images/gallery/{image_name}"
---

{content}
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(md_content)
    logging.info(f"📄 Статья сохранена: {filepath.name}")

# Очищаем старые статьи, оставляем последние 5
def cleanup_articles():
    files = sorted(CONTENT_DIR.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True)
    for f in files[5:]:
        f.unlink()
        logging.info(f"🧹 Удалена старая статья: {f.name}")

def main():
    title, content = generate_article()
    image_name = generate_image(title)
    save_article(title, content, image_name)
    cleanup_articles()

if __name__ == "__main__":
    main()
