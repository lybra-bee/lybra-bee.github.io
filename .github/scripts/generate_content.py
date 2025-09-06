#!/usr/bin/env python3
import os
import json
import requests
import time
import base64
import logging
from datetime import datetime
from slugify import slugify
import yaml

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# API ключи
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
FUSION_API_KEY = os.environ.get("FUSIONBRAIN_API_KEY")
FUSION_SECRET_KEY = os.environ.get("FUSION_SECRET_KEY")
BASE_URL = 'https://api-key.fusionbrain.ai/'

AUTH_HEADERS = {
    'X-Key': f'Key {FUSION_API_KEY}',
    'X-Secret': f'Secret {FUSION_SECRET_KEY}',
}

# Папки
POSTS_DIR = 'content/posts'
STATIC_DIR = 'static/images/posts'
GALLERY_FILE = 'data/gallery.yaml'
PLACEHOLDER = 'static/images/placeholder.jpg'

os.makedirs(POSTS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(os.path.dirname(PLACEHOLDER), exist_ok=True)

def generate_title():
    prompt = "Составь короткий привлекательный заголовок для статьи о последних трендах в искусственном интеллекте и высоких технологиях."
    # OpenRouter
    try:
        headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
        logging.info("📝 Генерация заголовка через OpenRouter...")
        r = requests.post("https://openrouter.ai/api/v1/chat/completions",
                          headers=headers,
                          json={"model": "gpt-4o-mini", "messages":[{"role":"user","content":prompt}]})
        r.raise_for_status()
        title = r.json()["choices"][0]["message"]["content"].strip()
        logging.info(f"✅ Заголовок получен через OpenRouter: {title}")
        return title
    except Exception as e:
        logging.warning(f"⚠️ OpenRouter не сработал: {e}")

    # Groq fallback
    try:
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
        logging.info("📝 Генерация заголовка через Groq...")
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                          headers=headers,
                          json={"model": "gpt-4o-mini", "messages":[{"role":"user","content":prompt}]})
        r.raise_for_status()
        title = r.json()["choices"][0]["message"]["content"].strip()
        logging.info(f"✅ Заголовок получен через Groq: {title}")
        return title
    except Exception as e:
        logging.error(f"❌ Ошибка генерации заголовка: {e}")
        return "Последние тренды в ИИ и технологиях"

def generate_article(title):
    prompt = f"Напиши статью на 400-600 слов по заголовку: {title}"
    # OpenRouter
    try:
        headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
        logging.info("📝 Генерация статьи через OpenRouter...")
        r = requests.post("https://openrouter.ai/api/v1/chat/completions",
                          headers=headers,
                          json={"model": "gpt-4o-mini", "messages":[{"role":"user","content":prompt}]})
        r.raise_for_status()
        text = r.json()["choices"][0]["message"]["content"]
        logging.info("✅ Статья получена через OpenRouter")
        return text, "OpenRouter GPT"
    except Exception as e:
        logging.warning(f"⚠️ OpenRouter не сработал: {e}")

    # Groq fallback
    try:
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
        logging.info("📝 Генерация статьи через Groq...")
        r = requests.post("https://api.groq.com/v1/chat/completions",
                          headers=headers,
                          json={"model": "gpt-4o-mini", "messages":[{"role":"user","content":prompt}]})
        r.raise_for_status()
        text = r.json()["choices"][0]["message"]["content"]
        logging.info("✅ Статья получена через Groq")
        return text, "Groq GPT"
    except Exception as e:
        logging.error(f"❌ Ошибка генерации статьи: {e}")
        return "Статья временно недоступна.", "None"

def get_pipeline_id():
    r = requests.get(BASE_URL + 'key/api/v1/pipelines', headers=AUTH_HEADERS)
    r.raise_for_status()
    return r.json()[0]['id']

def generate_image(title, slug):
    try:
        pipeline_id = get_pipeline_id()
        params = {
            "type": "GENERATE",
            "numImages": 1,
            "width": 1024,
            "height": 1024,
            "generateParams": {"query": title}
        }
        files = {
            'pipeline_id': (None, pipeline_id),
            'params': (None, json.dumps(params), 'application/json')
        }
        r = requests.post(BASE_URL + 'key/api/v1/pipeline/run', headers=AUTH_HEADERS, files=files)
        r.raise_for_status()
        uuid = r.json()['uuid']

        for _ in range(20):
            r_status = requests.get(BASE_URL + f'key/api/v1/pipeline/status/{uuid}', headers=AUTH_HEADERS)
            r_status.raise_for_status()
            data = r_status.json()
            if data['status'] == 'DONE':
                image_base64 = data['result']['files'][0]
                break
            time.sleep(3)
        else:
            logging.warning("❌ Изображение не сгенерировано за отведённое время")
            return PLACEHOLDER

        img_bytes = base64.b64decode(image_base64)
        img_path = os.path.join(STATIC_DIR, f'{slug}.png')
        os.makedirs(os.path.dirname(img_path), exist_ok=True)
        with open(img_path, 'wb') as f:
            f.write(img_bytes)

        logging.info(f"✅ Изображение сохранено: {img_path}")
        return f"images/posts/{slug}.png"
    except Exception as e:
        logging.error(f"❌ Ошибка генерации изображения: {e}")
        return PLACEHOLDER

def save_article(title, text, model, slug, image_path):
    filename = os.path.join(POSTS_DIR, f'{slug}.md')
    date = datetime.now().strftime("%Y-%m-%d")
    # Убираем двойные кавычки из заголовка в YAML
    title_yaml = title.replace('"', "'")
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"---\ntitle: '{title_yaml}'\ndate: {date}\nimage: '/{image_path}'\nmodel: {model}\ntags: [AI, Tech]\n---\n\n{text}")
    logging.info(f"✅ Статья сохранена: {filename}")

def update_gallery(title, slug, image_path):
    gallery = []
    if os.path.exists(GALLERY_FILE):
        with open(GALLERY_FILE, 'r', encoding='utf-8') as f:
            gallery = yaml.safe_load(f) or []

    gallery.insert(0, {"title": title, "alt": title, "src": f"/{image_path}"})
    gallery = gallery[:20]  # максимум 20 изображений

    with open(GALLERY_FILE, 'w', encoding='utf-8') as f:
        yaml.safe_dump(gallery, f, allow_unicode=True)
    logging.info(f"✅ Галерея обновлена: {GALLERY_FILE}")

def main():
    title = generate_title()
    slug = slugify(title)

    text, model = generate_article(title)
    image_path = generate_image(title, slug)

    save_article(title, text, model, slug, image_path)
    update_gallery(title, slug, image_path)

if __name__ == "__main__":
    main()
