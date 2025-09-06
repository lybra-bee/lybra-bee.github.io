#!/usr/bin/env python3
import os
import json
import requests
import random
from datetime import datetime, timezone
import shutil
import re
import base64
import time
import logging
from PIL import Image, ImageDraw, ImageFont

# ===== ЛОГИРОВАНИЕ =====
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ====== FusionBrain API ======
class FusionBrainAPI:
    def __init__(self, api_key, secret_key):
        self.URL = 'https://api-key.fusionbrain.ai/'
        self.AUTH_HEADERS = {
            'X-Key': f'Key {api_key}',
            'X-Secret': f'Secret {secret_key}',
        }
    
    def get_model(self):
        """Получаем pipeline ID"""
        try:
            response = requests.get(self.URL + 'key/api/v1/pipelines', headers=self.AUTH_HEADERS, timeout=10)
            if response.status_code == 200:
                pipelines = response.json()
                for pipeline in pipelines:
                    if "kandinsky" in pipeline.get("name", "").lower():
                        return pipeline['id']
                if pipelines:
                    return pipelines[0]['id']
            return None
        except Exception as e:
            logger.error(f"Ошибка получения моделей FusionBrain: {e}")
            return None
    
    def generate(self, prompt, width=512, height=512):
        """Создаем задачу генерации изображения"""
        pipeline_id = self.get_model()
        if not pipeline_id:
            logger.warning("⚠️ Pipeline не найден")
            return None
        params = {
            "type": "GENERATE",
            "numImages": 1,
            "width": width,
            "height": height,
            "generateParams": {"query": prompt}
        }
        files = {
            'params': (None, json.dumps(params), 'application/json'),
            'pipeline_id': (None, pipeline_id)
        }
        try:
            response = requests.post(self.URL + 'key/api/v1/pipeline/run', headers=self.AUTH_HEADERS, files=files, timeout=30)
            if response.status_code in [200, 201]:
                data = response.json()
                if data.get('uuid'):
                    logger.info(f"Задача FusionBrain создана: {data['uuid']}")
                    return data['uuid']
            logger.warning(f"Ошибка генерации FusionBrain: {response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Ошибка FusionBrain: {e}")
            return None

    def check_status(self, task_id, attempts=30, delay=6):
        """Проверка статуса задачи и получение base64"""
        for attempt in range(attempts):
            if attempt > 0:
                time.sleep(delay)
            logger.info(f"⏳ Проверка статуса FusionBrain (попытка {attempt+1}/{attempts})")
            try:
                response = requests.get(self.URL + f'key/api/v1/pipeline/status/{task_id}', headers=self.AUTH_HEADERS, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status')
                    if status == 'DONE':
                        result = data.get('result', {}).get('files', [])
                        if result:
                            return result[0]  # base64
                        return None
                    elif status == 'FAIL':
                        logger.warning(f"Генерация не удалась: {data.get('errorDescription', 'Unknown error')}")
                        return None
            except Exception as e:
                logger.error(f"Ошибка проверки статуса: {e}")
        logger.warning("Превышено количество попыток проверки статуса")
        return None

# ====== Утилиты ======
def generate_slug(title):
    slug = title.lower()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_-]+', '-', slug)
    slug = re.sub(r'^-+|-+$', '', slug)
    return slug

def save_image_bytes(image_data, title):
    os.makedirs("assets/images/posts", exist_ok=True)
    slug = generate_slug(title)
    filename = f"assets/images/posts/{slug}.png"
    with open(filename, "wb") as f:
        f.write(image_data)
    return filename

def generate_enhanced_placeholder(title):
    """Placeholder если API не сработал"""
    os.makedirs("assets/images/posts", exist_ok=True)
    slug = generate_slug(title)
    filename = f"assets/images/posts/{slug}.png"
    width, height = 800, 400
    img = Image.new('RGB', (width, height), color='#0f172a')
    draw = ImageDraw.Draw(img)
    draw.text((50, 180), title, fill='white')
    img.save(filename)
    return filename

# ====== Генерация статьи ======
def generate_article_prompt():
    trends = ["machine learning", "neural networks", "generative AI", "computer vision", "deep learning"]
    domains = ["web development", "mobile applications", "cloud computing", "data analysis", "cybersecurity"]
    trend = random.choice(trends)
    domain = random.choice(domains)
    prompt = f"Напиши статью на русском языке на тему '{trend} в {domain}'"
    return prompt, f"{trend} in {domain}"

def generate_fallback_content(prompt):
    sections = [
        "# Тенденции искусственного интеллекта в 2025 году",
        "## Введение", "Искусственный интеллект продолжает трансформировать отрасли...",
        "## Основные тенденции", "- Автоматизация процессов", "- Интеграция AI",
        "## Заключение", "Будущее AI многообещающее", "*Статья сгенерирована автоматически*"
    ]
    return "\n".join(sections)

def generate_article_content(prompt):
    groq_key = os.getenv('GROQ_API_KEY')
    if groq_key:
        try:
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                json={"model":"llama-3.1-8b-instant","messages":[{"role":"user","content":prompt}],"max_tokens":2000,"temperature":0.7},
                timeout=30
            )
            if resp.status_code == 200:
                return resp.json()['choices'][0]['message']['content'].strip(), "Groq"
        except Exception as e:
            logger.warning(f"Groq не сработал: {e}")
    # fallback
    return generate_fallback_content(prompt), "fallback"

def try_fusionbrain_api(title):
    api_key = os.getenv('FUSIONBRAIN_API_KEY')
    secret_key = os.getenv('FUSION_SECRET_KEY')
    if not api_key or not secret_key:
        return None
    fb = FusionBrainAPI(api_key, secret_key)
    prompt = f"{title}, digital art, futuristic, professional"
    task_id = fb.generate(prompt)
    if task_id:
        b64 = fb.check_status(task_id)
        if b64:
            return save_image_bytes(base64.b64decode(b64), title)
    return None

def generate_article_image(title):
    image_file = try_fusionbrain_api(title)
    if image_file:
        return image_file
    return generate_enhanced_placeholder(title)

def clean_old_articles(keep_last=3):
    os.makedirs("content/posts", exist_ok=True)
    posts = sorted([f for f in os.listdir("content/posts") if f.endswith(".md")], reverse=True)
    for post in posts[keep_last:]:
        os.remove(os.path.join("content/posts", post))

def generate_frontmatter(title, content, model, image_file):
    fm = f"---\ntitle: \"{title}\"\ndate: {datetime.now().isoformat()}\nimage: \"{image_file}\"\nmodel: \"{model}\"\n---\n\n{content}"
    return fm

def generate_content():
    clean_old_articles()
    prompt, topic = generate_article_prompt()
    content, model = generate_article_content(prompt)
    title = topic
    image_file = generate_article_image(title)
    slug = generate_slug(title)
    filename = f"content/posts/{datetime.now().strftime('%Y-%m-%d')}-{slug}.md"
    os.makedirs("content/posts", exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(generate_frontmatter(title, content, model, image_file))
    logger.info(f"Статья создана: {filename}")
    return filename

if __name__ == "__main__":
    generate_content()
