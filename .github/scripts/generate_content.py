#!/usr/bin/env python3
import os
import json
import requests
import time
from pathlib import Path
import logging
import re
import shutil

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Пути
CONTENT_DIR = Path('content/posts')
GALLERY_DIR = Path('static/images/gallery')
MAX_ARTICLES = 5

CONTENT_DIR.mkdir(parents=True, exist_ok=True)
GALLERY_DIR.mkdir(parents=True, exist_ok=True)

# Ключи из секретов GitHub Actions
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
FUSIONBRAIN_API_KEY = os.getenv('FUSIONBRAIN_API_KEY')
FUSION_SECRET_KEY = os.getenv('FUSION_SECRET_KEY')

# Groq - генерация статьи
def generate_article():
    logging.info("📝 Генерация статьи через Groq")
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    payload = {
        "prompt": "Сгенерируй статью на русском языке про нейросети и высокие технологии с упором на последние тренды 2025 года.",
        "max_tokens": 1200
    }
    response = requests.post("https://api.groq.com/v1/generate", headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()
    article_text = data['text'] if 'text' in data else data.get('output', '')
    # Заголовок из первой строки
    title = article_text.split('\n')[0]
    logging.info(f"📌 Заголовок статьи: {title}")
    return title, article_text

# FusionBrain Kandinsky 3.0 - генерация изображения
class FusionBrainAPI:
    def __init__(self, api_key, secret_key):
        self.URL = 'https://api-key.fusionbrain.ai/'
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
        response = requests.post(self.URL + 'key/api/v1/pipeline/run', headers=self.AUTH_HEADERS, files=data)
        response.raise_for_status()
        return response.json()['uuid']

    def check_generation(self, uuid, attempts=10, delay=5):
        for _ in range(attempts):
            response = requests.get(self.URL + f'key/api/v1/pipeline/status/{uuid}', headers=self.AUTH_HEADERS)
            data = response.json()
            if data['status'] == 'DONE':
                return data['result']['files'][0]  # Base64 изображения
            elif data['status'] in ['FAIL', 'CANCELLED']:
                raise Exception("Ошибка генерации изображения: " + str(data))
            time.sleep(delay)
        raise TimeoutError("Превышено время ожидания генерации изображения")

# Сохраняем статью
def save_article(title, text, image_filename):
    safe_title = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '-')
    filename = CONTENT_DIR / f"{safe_title}.md"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"---\n")
        f.write(f"title: \"{title}\"\n")
        f.write(f"image: \"/images/gallery/{image_filename}\"\n")
        f.write(f"date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"---\n\n")
        f.write(text)
    logging.info(f"📄 Статья сохранена: {filename}")
    return filename

# Ограничиваем количество статей
def cleanup_old_articles():
    files = sorted(CONTENT_DIR.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True)
    for old_file in files[MAX_ARTICLES:]:
        old_file.rename('content/posts/archive_' + old_file.name)

def main():
    title, article_text = generate_article()

    fusion = FusionBrainAPI(FUSIONBRAIN_API_KEY, FUSION_SECRET_KEY)
    pipeline_id = fusion.get_pipeline()

    try:
        uuid = fusion.generate(title, pipeline_id)
        image_base64 = fusion.check_generation(uuid)
        import base64
        image_data = base64.b64decode(image_base64)
        image_filename = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '-') + ".png"
        image_path = GALLERY_DIR / image_filename
        with open(image_path, 'wb') as f:
            f.write(image_data)
        logging.info(f"🎨 Изображение сохранено: {image_path}")
    except Exception as e:
        logging.error(f"❌ Ошибка генерации изображения FusionBrain: {e}")
        image_filename = "default.png"

    save_article(title, article_text, image_filename)
    cleanup_old_articles()

if __name__ == "__main__":
    main()
