#!/usr/bin/env python3
import os
import json
import requests
import random
from datetime import datetime, timezone
import shutil
import re
from PIL import Image, ImageDraw, ImageFont
import time
import logging
import base64

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ===== FusionBrain API =====
class FusionBrainAPI:
    def __init__(self, api_key, secret_key):
        self.URL = 'https://api-key.fusionbrain.ai/'
        self.AUTH_HEADERS = {
            'X-Key': f'Key {api_key}',
            'X-Secret': f'Secret {secret_key}',
        }

    def get_model(self):
        try:
            response = requests.get(
                self.URL + 'key/api/v1/pipelines',
                headers=self.AUTH_HEADERS,
                timeout=10
            )
            if response.status_code == 200:
                pipelines = response.json()
                for pipeline in pipelines:
                    if "kandinsky" in pipeline.get("name", "").lower():
                        return pipeline['id']
                return pipelines[0]['id']
            return None
        except Exception as e:
            logger.error(f"Ошибка получения моделей FusionBrain: {e}")
            return None

    def generate(self, prompt, width=512, height=512):
        try:
            pipeline_id = self.get_model()
            if not pipeline_id:
                logger.error("Не удалось получить pipeline ID")
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
            response = requests.post(
                self.URL + 'key/api/v1/pipeline/run',
                headers=self.AUTH_HEADERS,
                files=files,
                timeout=30
            )
            if response.status_code in [200, 201]:
                data = response.json()
                if data.get('uuid'):
                    logger.info(f"Задача FusionBrain создана: {data['uuid']}")
                    return data['uuid']
            logger.warning(f"Ошибка генерации FusionBrain: {response.status_code} - {response.text}")
            return None
        except Exception as e:
            logger.error(f"Ошибка генерации FusionBrain: {e}")
            return None

    def check_status(self, task_id, attempts=30, delay=6):
        try:
            for attempt in range(attempts):
                if attempt > 0:
                    time.sleep(delay)
                logger.info(f"Проверка статуса FusionBrain (попытка {attempt + 1}/{attempts})")
                response = requests.get(
                    self.URL + f'key/api/v1/pipeline/status/{task_id}',
                    headers=self.AUTH_HEADERS,
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status')
                    if status == 'DONE':
                        result = data.get('result', {})
                        images = result.get('files', [])
                        if images:
                            return images[0]
                    elif status == 'FAIL':
                        logger.warning(f"Генерация FusionBrain не удалась: {data.get('errorDescription')}")
                        return None
            logger.warning("Превышено количество попыток проверки статуса")
            return None
        except Exception as e:
            logger.error(f"Ошибка проверки статуса FusionBrain: {e}")
            return None

# ======= Генерация промпта статьи =======
def generate_article_prompt():
    trends = ["machine learning", "neural networks", "generative AI", 
              "computer vision", "natural language processing", "deep learning",
              "reinforcement learning", "transfer learning", "federated learning",
              "edge AI", "explainable AI", "ethical AI", "quantum machine learning",
              "autonomous systems", "computer vision"]
    domains = ["web development", "mobile applications", "cloud computing",
               "data analysis", "cybersecurity", "healthcare technology",
               "financial technology", "autonomous vehicles", "smart cities",
               "IoT ecosystems", "blockchain technology", "e-commerce",
               "education technology", "robotics", "augmented reality"]
    trend = random.choice(trends)
    domain = random.choice(domains)
    prompt = f"""Напиши статью на русском языке на тему "{trend} в {domain}".

Требования:
- Формат: Markdown
- Объем: 400-600 слов
- Структура: заголовок, введение, основные разделы, заключение
- Стиль: профессиональный, информативный
- Фокус: инновации, тенденции 2024-2025 годов"""
    return prompt, f"{trend} in {domain}"

# ======= Очистка старых статей =======
def clean_old_articles(keep_last=3):
    posts_dir = "content/posts"
    if os.path.exists(posts_dir):
        posts = sorted([f for f in os.listdir(posts_dir) if f.endswith(".md")], reverse=True)
        for post in posts[keep_last:]:
            os.remove(os.path.join(posts_dir, post))
            logger.info(f"Удален старый пост: {post}")
    else:
        os.makedirs(posts_dir, exist_ok=True)
        with open("content/_index.md", "w") as f:
            f.write("---\ntitle: \"Главная\"\n---")
        with open("content/posts/_index.md", "w") as f:
            f.write("---\ntitle: \"Статьи\"\n---")
        logger.info("Создана структура content")

# ======= Генерация текста =======
def generate_article_content(prompt):
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        try:
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                json={"model":"llama-3.1-8b-instant", "messages":[{"role":"user","content":prompt}], "max_tokens":2000},
                timeout=30
            )
            if resp.status_code == 200:
                return resp.json()['choices'][0]['message']['content'].strip(), "Groq"
        except Exception as e:
            logger.warning(f"Ошибка Groq: {e}")
    # OpenRouter фолбек
    try:
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}", "Content-Type":"application/json"},
            json={"model":"gpt-4o-mini", "messages":[{"role":"user","content":prompt}], "max_tokens":2000},
            timeout=30
        )
        if resp.status_code == 200:
            return resp.json()['choices'][0]['message']['content'].strip(), "OpenRouter"
    except Exception as e:
        logger.warning(f"Ошибка OpenRouter: {e}")
    # Локальный fallback
    return generate_fallback_content(prompt), "Fallback"

def generate_fallback_content(prompt):
    return "# Статья\n\n## Введение\nТекст автоматически сгенерирован как fallback.\n"

# ======= Генерация изображения =======
def generate_article_image(title):
    methods = [try_fusionbrain_api, try_craiyon_api, try_lexica_art_api, generate_enhanced_placeholder]
    for method in methods:
        try:
            result = method(title)
            if result:
                return result
        except Exception as e:
            logger.warning(f"Ошибка {method.__name__}: {e}")
    return generate_enhanced_placeholder(title)

def try_fusionbrain_api(title):
    api_key = os.getenv('FUSIONBRAIN_API_KEY')
    secret_key = os.getenv('FUSION_SECRET_KEY')
    if not api_key or not secret_key:
        return None
    fb = FusionBrainAPI(api_key, secret_key)
    task_id = fb.generate(f"{title}, digital art, futuristic technology", width=512, height=512)
    if task_id:
        image_base64 = fb.check_status(task_id)
        if image_base64:
            return save_image_bytes(base64.b64decode(image_base64), title)
    return None

def try_craiyon_api(title):
    try:
        resp = requests.post("https://api.craiyon.com/generate", json={"prompt": title}, timeout=60)
        if resp.status_code == 200:
            data = resp.json()
            if "images" in data and data["images"]:
                return save_image_bytes(base64.b64decode(data["images"][0]), title)
    except:
        pass
    return None

def try_lexica_art_api(title):
    try:
        search_response = requests.get(f"https://lexica.art/api/v1/search?q={requests.utils.quote(title)}", timeout=20)
        if search_response.status_code == 200:
            data = search_response.json()
            if data.get('images'):
                img_url = data['images'][0]['src']
                img_data = requests.get(img_url, timeout=30).content
                return save_image_bytes(img_data, title)
    except:
        pass
    return None

def generate_enhanced_placeholder(title):
    os.makedirs("assets/images/posts", exist_ok=True)
    slug = generate_slug(title)
    filename = f"assets/images/posts/{slug}.png"
    img = Image.new('RGB', (800, 400), color='#0f172a')
    draw = ImageDraw.Draw(img)
    draw.text((20, 150), title, fill=(255,255,255))
    img.save(filename)
    return filename

def save_image_bytes(image_data, title):
    os.makedirs("assets/images/posts", exist_ok=True)
    slug = generate_slug(title)
    filename = f"assets/images/posts/{slug}.png"
    with open(filename, "wb") as f:
        f.write(image_data)
    return filename

def generate_slug(title):
    return re.sub(r'[^a-zA-Z0-9]+', '-', title.lower()).strip('-')

# ======= Сборка статьи =======
def generate_content():
    clean_old_articles()
    prompt, topic = generate_article_prompt()
    content, model_used = generate_article_content(prompt)
    title = extract_title_from_content(content, topic)
    image_filename = generate_article_image(title)
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    slug = generate_slug(title)
    filename = f"content/posts/{date}-{slug}.md"
    frontmatter = f"---\ntitle: \"{title}\"\ndate: {date}\nimage: \"{image_filename}\"\nmodel: \"{model_used}\"\n---\n\n{content}"
    os.makedirs("content/posts", exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(frontmatter)
    logger.info(f"Статья создана: {filename}")
    return filename

def extract_title_from_content(content, fallback_topic):
    lines = content.splitlines()
    for line in lines:
        if line.startswith("# "):
            return line.replace("# ", "").strip()
    return fallback_topic

if __name__ == "__main__":
    generate_content()
