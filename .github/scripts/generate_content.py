#!/usr/bin/env python3
import os
import json
import requests
import time
import logging
from pathlib import Path
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Директории сайта
CONTENT_DIR = Path('content/posts')
GALLERY_DIR = Path('static/images/gallery')

def ensure_dir(path: Path):
    if path.exists():
        if not path.is_dir():
            logging.warning(f"{path} существует, но это не директория. Удаляем и создаём папку.")
            path.unlink()  # удаляем файл
            path.mkdir(parents=True, exist_ok=True)
    else:
        path.mkdir(parents=True, exist_ok=True)

ensure_dir(CONTENT_DIR)
ensure_dir(GALLERY_DIR)

# Ключи из GitHub Secrets
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
FUSION_API_KEY = os.environ.get('FUSIONBRAIN_API_KEY')
FUSION_SECRET_KEY = os.environ.get('FUSION_SECRET_KEY')

# FusionBrain API
class FusionBrainAPI:
    def __init__(self, api_key, secret_key):
        self.URL = 'https://api-key.fusionbrain.ai/'
        self.AUTH_HEADERS = {
            'X-Key': f'Key {api_key}',
            'X-Secret': f'Secret {secret_key}',
        }

    def get_pipeline(self):
        response = requests.get(self.URL + 'key/api/v1/pipelines', headers=self.AUTH_HEADERS)
        response.raise_for_status()
        data = response.json()
        return data[0]['id']  # выбираем первую доступную модель Kandinsky

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
            'pipeline_id': (None, pipeline_id),
            'params': (None, json.dumps(params), 'application/json')
        }
        response = requests.post(self.URL + 'key/api/v1/pipeline/run', headers=self.AUTH_HEADERS, files=data)
        response.raise_for_status()
        return response.json()['uuid']

    def check_generation(self, request_id, attempts=10, delay=10):
        for _ in range(attempts):
            response = requests.get(self.URL + f'key/api/v1/pipeline/status/{request_id}', headers=self.AUTH_HEADERS)
            response.raise_for_status()
            data = response.json()
            if data['status'] == 'DONE':
                return data['result']['files']
            time.sleep(delay)
        raise TimeoutError("Превышено время ожидания генерации изображения FusionBrain.")

fusion_api = FusionBrainAPI(FUSION_API_KEY, FUSION_SECRET_KEY)

# Генерация статьи через Groq
def generate_article():
    logging.info("📝 Генерация статьи через Groq")
    headers = {'Authorization': f'Bearer {GROQ_API_KEY}', 'Content-Type': 'application/json'}
    payload = {
        "prompt": "Напиши статью на русском языке про нейросети и высокие технологии, опираясь на последние тренды. Статья для блога.",
        "max_tokens": 1000
    }
    response = requests.post('https://api.groq.ai/v1/complete', headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()
    text = data['completion'].strip()
    # Заголовок – первая строка или первые 5 слов
    title = text.split('\n')[0].strip() or 'Новая статья'
    return title, text

def save_article(title, content, image_filename=None):
    slug = title.lower().replace(' ', '-').replace(':', '').replace('.', '')
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = CONTENT_DIR / f"{slug}.md"
    front_matter = f"---\ntitle: \"{title}\"\ndate: {date_str}\n"
    if image_filename:
        front_matter += f"image: {image_filename}\n"
    front_matter += "---\n\n"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(front_matter + content)
    logging.info(f"📄 Статья сохранена: {filename}")
    return filename

def generate_image_for_article(title):
    logging.info("🎨 Генерация изображения через FusionBrain")
    pipeline_id = fusion_api.get_pipeline()
    uuid = fusion_api.generate(title, pipeline_id)
    files = fusion_api.check_generation(uuid)
    # Получаем base64 изображения
    image_data = files[0]
    import base64
    image_bytes = base64.b64decode(image_data)
    image_filename = GALLERY_DIR / f"{title.lower().replace(' ', '_')}.png"
    with open(image_filename, 'wb') as f:
        f.write(image_bytes)
    logging.info(f"🖼 Изображение сохранено: {image_filename}")
    return f"/images/gallery/{image_filename.name}"

def main():
    title, content = generate_article()
    try:
        image_path = generate_image_for_article(title)
    except Exception as e:
        logging.error(f"❌ Ошибка генерации изображения FusionBrain: {e}")
        image_path = None
    save_article(title, content, image_path)

if __name__ == "__main__":
    main()
