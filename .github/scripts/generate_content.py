#!/usr/bin/env python3
import os
import json
import requests
import time
import base64
import logging
import shutil
from datetime import datetime
from slugify import slugify
import yaml

# Логирование
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
ASSETS_DIR = 'assets/images/posts'
STATIC_IMG_DIR = 'static/images/posts'
GALLERY_FILE = 'data/gallery.yaml'
PLACEHOLDER = 'static/images/placeholder.jpg'

for d in [POSTS_DIR, ASSETS_DIR, STATIC_IMG_DIR, os.path.dirname(PLACEHOLDER)]:
    os.makedirs(d, exist_ok=True)

# --------- Генерация через Groq / OpenRouter ---------
def query_groq_or_openrouter(prompt):
    # Groq основной
    try:
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
        r = requests.post("https://api.groq.com/v1/chat/completions",
                          headers=headers,
                          json={"model": "gpt-4o-mini", "messages":[{"role":"user","content":prompt}]})
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"], "Groq GPT"
    except Exception as e:
        logging.warning(f"⚠️ Groq не сработал: {e}")

    # OpenRouter запасной
    try:
        headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
        r = requests.post("https://openrouter.ai/api/v1/chat/completions",
                          headers=headers,
                          json={"model": "gpt-4o-mini", "messages":[{"role":"user","content":prompt}]})
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"], "OpenRouter GPT"
    except Exception as e:
        logging.error(f"❌ Ошибка генерации текста: {e}")
        return "Текст временно недоступен.", "None"

# --------- Генерация заголовка ---------
def generate_title():
    prompt = "Составь уникальный заголовок для статьи о последних трендах в искусственном интеллекте и высоких технологиях, 7-10 слов, привлекательный для читателя."
    title, model = query_groq_or_openrouter(prompt)
    # убираем лишние переносы строк
    title = " ".join(title.strip().split())
    return title, model

# --------- Генерация статьи по заголовку ---------
def generate_article_by_title(title):
    prompt = f"Напиши статью 400-600 слов по заголовку: {title}"
    text, model = query_groq_or_openrouter(prompt)
    return text, model

# --------- FusionBrain Image ---------
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
        img_path = os.path.join(ASSETS_DIR, f'{slug}.png')
        with open(img_path, 'wb') as f:
            f.write(img_bytes)

        # Копируем в static для Hugo
        os.makedirs(STATIC_IMG_DIR, exist_ok=True)
        static_img_path = os.path.join(STATIC_IMG_DIR, f'{slug}.png')
        shutil.copy(img_path, static_img_path)

        logging.info(f"✅ Изображение сохранено: {img_path}")
        return f"images/posts/{slug}.png"
    except Exception as e:
        logging.error(f"❌ Ошибка генерации изображения: {e}")
        return PLACEHOLDER

# --------- Сохранение статьи ---------
def save_article(title, text, model, slug, image_path):
    filename = os.path.join(POSTS_DIR, f'{slug}.md')
    date = datetime.now().strftime("%Y-%m-%d")
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"---\ntitle: \"{title}\"\ndate: {date}\nimage: \"/{image_path}\"\nmodel: {model}\ntags: [AI, Tech]\n---\n\n{text}")
    logging.info(f"✅ Статья сохранена: {filename}")

# --------- Обновление галереи ---------
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

# --------- Main ---------
def main():
    # Генерация заголовка
    title, title_model = generate_title()
    slug = slugify(title)

    # Генерация статьи по заголовку
    text, article_model = generate_article_by_title(title)

    # Генерация изображения
    image_path = generate_image(title, slug)

    # Сохранение
    save_article(title, text, article_model, slug, image_path)
    update_gallery(title, slug, image_path)

if __name__ == "__main__":
    main()
