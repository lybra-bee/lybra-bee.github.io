#!/usr/bin/env python3
import os
import json
import requests
import time
import logging
from datetime import datetime
from slugify import slugify

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# -----------------------
# Настройки
# -----------------------
POSTS_DIR = "content/posts"
GALLERY_FILE = "data/gallery.yaml"
IMAGE_DIR = "assets/images/posts"
IMAGE_WIDTH = 1024
IMAGE_HEIGHT = 1024

# -----------------------
# Функции генерации статьи через Groq
# -----------------------
def generate_article():
    prompt = "Проанализируй последние тренды в искусственном интеллекте и высоких технологиях и напиши статью на 400-600 слов."
    headers = {
        "Authorization": f"Bearer {os.environ['GROQ_API_KEY']}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role":"user","content": prompt}]
    }
    try:
        logging.info("📝 Генерация статьи...")
        r = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
        text = data['choices'][0]['message']['content']
        title = text.split('\n')[0][:60]  # первая строка как заголовок
        logging.info("✅ Статья получена через Groq")
        return text, title
    except Exception as e:
        logging.error(f"❌ Ошибка генерации статьи: {e}")
        return None, None

# -----------------------
# Класс для FusionBrain Kandinsky
# -----------------------
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
        r = requests.post(self.URL + 'key/api/v1/pipeline/run', headers=self.AUTH_HEADERS, files=data)
        r.raise_for_status()
        uuid = r.json()['uuid']
        return uuid

    def check_generation(self, uuid, attempts=20, delay=5):
        while attempts > 0:
            r = requests.get(self.URL + f'key/api/v1/pipeline/status/{uuid}', headers=self.AUTH_HEADERS)
            r.raise_for_status()
            data = r.json()
            if data['status'] == 'DONE':
                return data['result']['files'][0]  # URL изображения
            elif data['status'] == 'FAIL':
                raise Exception(f"Ошибка генерации изображения: {data.get('errorDescription')}")
            attempts -= 1
            time.sleep(delay)
        raise TimeoutError("Превышено время ожидания генерации изображения")

# -----------------------
# Сохранение статьи и изображения
# -----------------------
def save_article(text, title):
    slug = slugify(title)
    filename = f"{slug}.md"
    path = os.path.join(POSTS_DIR, filename)
    os.makedirs(POSTS_DIR, exist_ok=True)
    content = f"---\ntitle: \"{title}\"\ndate: {datetime.utcnow().isoformat()}\nimage: /images/posts/{slug}.png\nmodel: Groq GPT-4o-mini\n---\n\n{text}"
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    logging.info(f"✅ Статья сохранена: {path}")
    return slug

def save_image_from_url(url, slug):
    os.makedirs(IMAGE_DIR, exist_ok=True)
    path = os.path.join(IMAGE_DIR, f"{slug}.png")
    r = requests.get(url, stream=True)
    r.raise_for_status()
    with open(path, "wb") as f:
        for chunk in r.iter_content(1024):
            f.write(chunk)
    logging.info(f"✅ Изображение сохранено: {path}")
    return path

def update_gallery(slug, title):
    os.makedirs(os.path.dirname(GALLERY_FILE), exist_ok=True)
    entry = f"- src: /images/posts/{slug}.png\n  alt: {title}\n  title: {title}\n"
    if os.path.exists(GALLERY_FILE):
        with open(GALLERY_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        content = entry + content
    else:
        content = entry
    with open(GALLERY_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    logging.info(f"✅ Галерея обновлена: {GALLERY_FILE}")

# -----------------------
# Основной workflow
# -----------------------
def main():
    text, title = generate_article()
    if not text or not title:
        logging.error("❌ Статья не сгенерирована")
        return

    slug = save_article(text, title)

    try:
        fb = FusionBrainAPI('https://api-key.fusionbrain.ai/', os.environ['FUSIONBRAIN_API_KEY'], os.environ['FUSION_SECRET_KEY'])
        pipeline_id = fb.get_pipeline()
        uuid = fb.generate(title, pipeline_id, IMAGE_WIDTH, IMAGE_HEIGHT)
        img_url = fb.check_generation(uuid)
        save_image_from_url(img_url, slug)
    except Exception as e:
        logging.error(f"❌ Ошибка генерации изображения: {e}")

    update_gallery(slug, title)

if __name__ == "__main__":
    main()
