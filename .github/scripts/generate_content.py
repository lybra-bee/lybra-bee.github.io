#!/usr/bin/env python3
import os
import json
import requests
import random
from datetime import datetime, timezone
import base64
import time
import logging
from PIL import Image, ImageDraw

# ===== ЛОГИРОВАНИЕ =====
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
        pipeline_id = self.get_model()
        if not pipeline_id:
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
            if response.status_code in [200,201]:
                data = response.json()
                if data.get('uuid'):
                    logger.info(f"Задача FusionBrain создана: {data['uuid']}")
                    return data['uuid']
            return None
        except Exception as e:
            logger.error(f"Ошибка FusionBrain: {e}")
            return None

    def check_status(self, task_id, attempts=30, delay=6):
        for attempt in range(attempts):
            if attempt > 0:
                time.sleep(delay)
            try:
                response = requests.get(self.URL + f'key/api/v1/pipeline/status/{task_id}', headers=self.AUTH_HEADERS, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status')
                    if status == 'DONE':
                        files = data.get('result', {}).get('files', [])
                        if files:
                            return files[0]
                        return None
                    elif status == 'FAIL':
                        logger.warning(f"Генерация не удалась: {data.get('errorDescription', 'Unknown')}")
                        return None
            except Exception as e:
                logger.error(f"Ошибка проверки статуса: {e}")
        return None

# ===== УТИЛИТЫ =====
def generate_slug(title):
    slug = title.lower()
    slug = slug.replace(' ', '-')
    slug = ''.join(c for c in slug if c.isalnum() or c=='-')
    return slug

def save_image_bytes(image_data, title):
    os.makedirs("assets/images/posts", exist_ok=True)
    slug = generate_slug(title)
    filename = f"assets/images/posts/{slug}.png"
    with open(filename, "wb") as f:
        f.write(image_data)
    return filename

def generate_placeholder_image(title):
    os.makedirs("assets/images/posts", exist_ok=True)
    slug = generate_slug(title)
    filename = f"assets/images/posts/{slug}.png"
    img = Image.new('RGB', (800,400), color='#0f172a')
    draw = ImageDraw.Draw(img)
    draw.text((50,180), title, fill='white')
    img.save(filename)
    return filename

# ====== Генерация текста ======
def generate_article_prompt():
    trends = ["machine learning", "neural networks", "generative AI", "computer vision", "deep learning"]
    domains = ["web development", "mobile applications", "cloud computing", "data analysis", "cybersecurity"]
    trend = random.choice(trends)
    domain = random.choice(domains)
    prompt = f"Напиши статью на русском языке на тему '{trend} в {domain}'"
    return prompt, f"{trend} in {domain}"

def generate_fallback_content(prompt):
    return ("# Тенденции искусственного интеллекта в 2025 году\n"
            "## Введение\nИскусственный интеллект продолжает трансформировать отрасли...\n"
            "## Основные тенденции\n- Автоматизация процессов\n- Интеграция AI\n"
            "## Заключение\nБудущее AI многообещающее\n*Статья сгенерирована автоматически*")

def generate_article_content(prompt):
    # --- OpenRouter ---
    or_key = os.getenv('OPENROUTER_API_KEY')
    if or_key:
        try:
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {or_key}", "Content-Type": "application/json"},
                json={"model":"claude-3","messages":[{"role":"user","content":prompt}],"max_tokens":2000},
                timeout=30
            )
            if resp.status_code == 200:
                return resp.json()['choices'][0]['message']['content'].strip(), "OpenRouter"
        except Exception as e:
            logger.warning(f"OpenRouter не сработал: {e}")
    # --- Groq как запасной вариант ---
    groq_key = os.getenv('GROQ_API_KEY')
    if groq_key:
        try:
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                json={"model":"llama-3.1-8b-instant","messages":[{"role":"user","content":prompt}],"max_tokens":2000},
                timeout=30
            )
            if resp.status_code == 200:
                return resp.json()['choices'][0]['message']['content'].strip(), "Groq"
        except Exception as e:
            logger.warning(f"Groq не сработал: {e}")
    # --- Fallback ---
    return generate_fallback_content(prompt), "fallback"

# ====== Генерация изображения ======
def generate_article_image(title):
    fb_key = os.getenv('FUSIONBRAIN_API_KEY')
    fb_secret = os.getenv('FUSION_SECRET_KEY')
    if fb_key and fb_secret:
        fb = FusionBrainAPI(fb_key, fb_secret)
        prompt = f"{title}, digital art, futuristic, professional"
        task_id = fb.generate(prompt)
        if task_id:
            b64 = fb.check_status(task_id)
            if b64:
                try:
                    return save_image_bytes(base64.b64decode(b64), title)
                except:
                    pass
    return generate_placeholder_image(title)

# ====== Работа с файлами ======
def clean_old_articles(keep_last=3):
    os.makedirs("content/posts", exist_ok=True)
    posts = sorted([f for f in os.listdir("content/posts") if f.endswith(".md")], reverse=True)
    for post in posts[keep_last:]:
        os.remove(os.path.join("content/posts", post))

def generate_frontmatter(title, content, model, image_file):
    return f"---\ntitle: \"{title}\"\ndate: {datetime.now().isoformat()}\nimage: \"{image_file}\"\nmodel: \"{model}\"\n---\n\n{content}"

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
