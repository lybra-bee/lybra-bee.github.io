#!/usr/bin/env python3
import os
import json
import requests
import logging
import time
import base64
from datetime import datetime
from slugify import slugify

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Ключи и URL
OPENROUTER_KEY = os.environ.get("OPENROUTER_KEY")
FUSIONBRAIN_URL = "https://api-key.fusionbrain.ai/"
FUSIONBRAIN_KEY = os.environ.get("FUSIONBRAIN_KEY")
FUSIONBRAIN_SECRET = os.environ.get("FUSIONBRAIN_SECRET")


# ========== Функции генерации статьи ==========
def generate_article():
    prompt = "Проанализируй последние тренды в искусственном интеллекте и высоких технологиях и напиши статью на 400-600 слов."
    headers = {"Authorization": f"Bearer {OPENROUTER_KEY}"}
    data = {
        "model": "gpt-4.1-mini",
        "messages": [{"role": "user", "content": prompt}],
    }

    try:
        r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        r.raise_for_status()
        resp = r.json()
        text = resp["choices"][0]["message"]["content"]
        return text, "gpt-4.1-mini"
    except Exception as e:
        logging.error(f"❌ Ошибка генерации статьи: {e}")
        return None, None


# ========== Класс для FusionBrain ==========
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


# ========== Генерация изображения ==========
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
        if "," in img_base64:
            img_base64 = img_base64.split(",")[-1]

        img_data = base64.b64decode(img_base64)
        os.makedirs("static/images/posts", exist_ok=True)
        img_path = f"static/images/posts/{slug}.png"
        with open(img_path, "wb") as f:
            f.write(img_data)
        logging.info(f"✅ Изображение сохранено: {img_path}")
        return f"/images/posts/{slug}.png"
    except Exception as e:
        logging.error(f"❌ Ошибка генерации изображения: {e}")
        return None


# ========== Сохранение статьи ==========
def save_article(title, text, image_url, model):
    slug = slugify(title)
    os.makedirs("content/posts", exist_ok=True)
    filename = f"content/posts/{slug}.md"
    date = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    content = f"""---
title: "{title}"
date: {date}
image: "{image_url if image_url else ''}"
model: "{model}"
---

{text}
"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    logging.info(f"✅ Статья сохранена: {filename}")
    return slug


# ========== Обновление галереи ==========
def update_gallery(slug, title, image_url):
    os.makedirs("data", exist_ok=True)
    gallery_file = "data/gallery.yaml"
    gallery = []
    if os.path.exists(gallery_file):
        import yaml
        with open(gallery_file, "r", encoding="utf-8") as f:
            gallery = yaml.safe_load(f) or []

    gallery.insert(0, {"src": image_url, "alt": title, "title": title})
    gallery = gallery[:10]  # оставляем последние 10
    with open(gallery_file, "w", encoding="utf-8") as f:
        yaml.dump(gallery, f, allow_unicode=True)
    logging.info(f"✅ Галерея обновлена: {gallery_file}")


# ========== Главная функция ==========
def main():
    logging.info("📝 Генерация статьи...")
    text, model = generate_article()
    if not text:
        logging.error("❌ Статья не сгенерирована")
        return

    title = text.split("\n")[0][:100]  # первые 100 символов как заголовок
    slug = slugify(title)

    logging.info("🎨 Генерация изображения...")
    image_url = generate_image(title, slug)

    save_article(title, text, image_url, model)

    if image_url:
        update_gallery(slug, title, image_url)


if __name__ == "__main__":
    main()
