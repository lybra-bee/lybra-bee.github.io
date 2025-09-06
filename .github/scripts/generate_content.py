#!/usr/bin/env python3
import os
import json
import requests
import logging
import time
from slugify import slugify
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# API ключи
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
FUSION_API_KEY = os.getenv("FUSION_API_KEY")
FUSION_SECRET_KEY = os.getenv("FUSION_SECRET_KEY")

# URL генераторов
GROQ_API_URL = "https://api.groq.com/v1/chat/completions"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
FUSION_URL = "https://api-key.fusionbrain.ai/"

# Пути
POSTS_DIR = "content/posts"
IMAGES_DIR = "assets/images/posts"
GALLERY_FILE = "data/gallery.yaml"

os.makedirs(POSTS_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

# ----------------------------
# Функция генерации статьи
# ----------------------------
def generate_article():
    prompt = "Проанализируй последние тренды в искусственном интеллекте и высоких технологиях и напиши статью на 400-600 слов."
    
    # Попытка через Groq
    headers_groq = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    data_groq = {"model": "gpt-4", "messages": [{"role": "user", "content": prompt}]}
    try:
        r = requests.post(GROQ_API_URL, headers=headers_groq, json=data_groq)
        r.encoding = "utf-8"
        r.raise_for_status()
        result = r.json()
        text = result["choices"][0]["message"]["content"]
        logging.info("✅ Статья получена через Groq")
        return text, "Groq"
    except Exception as e:
        logging.warning(f"⚠️ Groq не сработал: {e}")

    # Попытка через OpenRouter
    headers_or = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
    data_or = {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}]}
    try:
        r = requests.post(OPENROUTER_API_URL, headers=headers_or, json=data_or)
        r.encoding = "utf-8"
        r.raise_for_status()
        result = r.json()
        text = result["choices"][0]["message"]["content"]
        logging.info("✅ Статья получена через OpenRouter")
        return text, "OpenRouter"
    except Exception as e2:
        logging.error(f"❌ Ошибка генерации статьи: {e2}")
        return None, None

# ----------------------------
# Класс FusionBrain
# ----------------------------
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
        return r.json()['uuid']

    def check_generation(self, request_id, attempts=10, delay=5):
        while attempts > 0:
            r = requests.get(self.URL + f'key/api/v1/pipeline/status/{request_id}', headers=self.AUTH_HEADERS)
            r.raise_for_status()
            data = r.json()
            if data['status'] == 'DONE':
                return data['result']['files']
            elif data['status'] == 'FAIL':
                raise Exception("Ошибка генерации изображения")
            attempts -= 1
            time.sleep(delay)
        raise TimeoutError("Превышено время ожидания генерации изображения")

# ----------------------------
# Генерация изображения
# ----------------------------
def generate_image(title, slug):
    try:
        fusion = FusionBrainAPI(FUSION_URL, FUSION_API_KEY, FUSION_SECRET_KEY)
        pipeline_id = fusion.get_pipeline()
        uuid = fusion.generate(title, pipeline_id)
        files = fusion.check_generation(uuid)
        img_data = requests.get(files[0]).content
        img_path = os.path.join(IMAGES_DIR, f"{slug}.png")
        with open(img_path, "wb") as f:
            f.write(img_data)
        logging.info(f"✅ Изображение сохранено: {img_path}")
        return img_path
    except Exception as e:
        logging.error(f"❌ Ошибка генерации изображения: {e}")
        return None

# ----------------------------
# Сохранение статьи
# ----------------------------
def save_post(title, text, model, img_path):
    slug = slugify(title)
    filename = os.path.join(POSTS_DIR, f"{slug}.md")
    img_rel = os.path.relpath(img_path, start="content") if img_path else ""
    front_matter = f"---\ntitle: \"{title}\"\ndate: {datetime.utcnow().isoformat()}Z\nmodel: {model}\nimage: /{img_rel}\n---\n\n"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(front_matter + text)
    logging.info(f"✅ Статья сохранена: {filename}")
    return slug

# ----------------------------
# Обновление галереи
# ----------------------------
def update_gallery(title, slug, img_path):
    import yaml
    gallery = []
    if os.path.exists(GALLERY_FILE):
        with open(GALLERY_FILE, "r", encoding="utf-8") as f:
            gallery = yaml.safe_load(f) or []

    gallery.insert(0, {"src": f"/{os.path.relpath(img_path, start='content')}", "alt": title, "title": title})
    with open(GALLERY_FILE, "w", encoding="utf-8") as f:
        yaml.dump(gallery, f, allow_unicode=True)
    logging.info(f"✅ Галерея обновлена: {GALLERY_FILE}")

# ----------------------------
# Основная функция
# ----------------------------
def main():
    text, model = generate_article()
    if not text:
        logging.error("❌ Статья не сгенерирована")
        return
    title = text.split("\n")[0][:50]  # Берем первую строку как заголовок
    slug = slugify(title)
    img_path = generate_image(title, slug)
    save_post(title, text, model, img_path)
    if img_path:
        update_gallery(title, slug, img_path)

if __name__ == "__main__":
    main()
