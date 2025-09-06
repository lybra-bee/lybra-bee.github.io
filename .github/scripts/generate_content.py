#!/usr/bin/env python3
import os
import json
import requests
import time
import yaml
from datetime import datetime
from slugify import slugify
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Параметры генерации ---
PROMPT = "Проанализируй последние тренды в искусственном интеллекте и высоких технологиях и напиши статью на 400-600 слов."
ARTICLES_DIR = "content/posts"
IMAGES_DIR = "assets/images/posts"
GALLERY_FILE = "data/gallery.yaml"

# --- API ключи из env ---
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
FUSION_API_KEY = os.environ.get("FUSIONBRAIN_API_KEY")
FUSION_SECRET_KEY = os.environ.get("FUSION_SECRET_KEY")

# --- Создаём директории ---
os.makedirs(ARTICLES_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(os.path.dirname(GALLERY_FILE), exist_ok=True)

# --- Функция генерации статьи через Groq ---
def generate_article():
    logging.info("📝 Генерация статьи...")
    url = "https://api.groq.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": PROMPT}]
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        text = r.json()["choices"][0]["message"]["content"]
        # Используем первую строку как заголовок
        title = text.strip().split("\n")[0][:100]
        return text, title
    except Exception as e:
        logging.error(f"❌ Ошибка генерации статьи: {e}")
        return None, None

# --- Класс для работы с FusionBrain Kandinsky ---
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
        return data[0]['uuid']  # Берём первую доступную pipeline

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
        return r.json()['uuid']

    def check_generation(self, request_id, attempts=10, delay=5):
        while attempts > 0:
            r = requests.get(self.URL + f'key/api/v1/pipeline/status/{request_id}', headers=self.AUTH_HEADERS)
            r.raise_for_status()
            data = r.json()
            if data['status'] == 'DONE':
                return data['result']['files']
            if data['status'] == 'FAIL':
                raise Exception("❌ Ошибка генерации изображения")
            attempts -= 1
            time.sleep(delay)
        raise TimeoutError("⏱️ Таймаут ожидания изображения")

def generate_image(title, slug):
    logging.info("🎨 Генерация изображения через FusionBrain...")
    try:
        api = FusionBrainAPI('https://api-key.fusionbrain.ai/', FUSION_API_KEY, FUSION_SECRET_KEY)
        pipeline_id = api.get_pipeline()
        uuid = api.generate(title, pipeline_id)
        files = api.check_generation(uuid)
        if files:
            img_data = requests.get(files[0]).content
            filename = f"{slug}.png"
            path = os.path.join(IMAGES_DIR, filename)
            with open(path, "wb") as f:
                f.write(img_data)
            return filename
        return None
    except Exception as e:
        logging.error(f"❌ Ошибка генерации изображения: {e}")
        return None

# --- Сохраняем статью и обновляем галерею ---
def save_article(text, title, image_filename):
    slug = slugify(title)
    filename = os.path.join(ARTICLES_DIR, f"{slug}.md")
    date_str = datetime.now().strftime("%Y-%m-%d")
    content = f"---\ntitle: \"{title}\"\ndate: {date_str}\nimage: /images/posts/{image_filename}\nmodel: GPT-4o-mini\ntags: [AI, Tech]\n---\n\n{text}"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    logging.info(f"✅ Статья сохранена: {filename}")
    # Обновляем gallery.yaml
    gallery = []
    if os.path.exists(GALLERY_FILE):
        with open(GALLERY_FILE, "r", encoding="utf-8") as f:
            gallery = yaml.safe_load(f) or []
    gallery.append({
        "src": f"/images/posts/{image_filename}",
        "alt": title,
        "title": title
    })
    with open(GALLERY_FILE, "w", encoding="utf-8") as f:
        yaml.dump(gallery, f, allow_unicode=True)
    logging.info(f"✅ Галерея обновлена: {GALLERY_FILE}")

# --- Главная логика ---
def main():
    text, title = generate_article()
    if not text or not title:
        logging.error("❌ Статья не сгенерирована")
        return
    slug = slugify(title)
    image_filename = generate_image(title, slug)
    if not image_filename:
        # Создаём заглушку
        image_filename = "placeholder.jpg"
    save_article(text, title, image_filename)

if __name__ == "__main__":
    main()
