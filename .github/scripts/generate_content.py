#!/usr/bin/env python3
import os
import json
import requests
import random
from datetime import datetime, timezone
import base64
import time
import logging
from PIL import Image, ImageDraw, ImageFont
import re

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
    
    img = Image.new('RGB', (800, 400), color='#0f172a')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("arial.ttf", 30)
    except:
        font = ImageFont.load_default()
    
    # Центрирование текста
    bbox = draw.textbbox((0, 0), title, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (800 - text_width) / 2
    y = (400 - text_height) / 2
    
    draw.text((x, y), title, fill='white', font=font)
    img.save(filename)
    
    return filename

# ====== Генерация текста ======
def generate_article_prompt():
    trends = ["machine learning", "neural networks", "generative AI", "computer vision", "deep learning"]
    domains = ["web development", "mobile applications", "cloud computing", "data analysis", "cybersecurity"]
    trend = random.choice(trends)
    domain = random.choice(domains)
    prompt = f"Напиши статью на русском языке на тему '{trend} в {domain}'. Статья должна содержать заголовок, введение, несколько разделов и заключение. Объем: 500-800 слов."
    return prompt, f"{trend} в {domain}"

def generate_fallback_content(prompt):
    return ("# Тенденции искусственного интеллекта в 2025 году\n\n"
            "## Введение\n\nИскусственный интеллект продолжает трансформировать отрасли, предлагая инновационные решения для сложных задач.\n\n"
            "## Основные тенденции\n\n- Автоматизация бизнес-процессов\n- Интеграция AI в повседневные приложения\n- Развитие генеративных моделей\n- Улучшение компьютерного зрения\n\n"
            "## Заключение\n\nБудущее искусственного интеллекта выглядит многообещающе, с постоянным ростом возможностей и применений.\n\n"
            "*Статья сгенерирована автоматически*")

def generate_article_content(prompt):
    providers = [
        {
            'name': 'OpenRouter',
            'env_key': 'OPENROUTER_API_KEY',
            'url': 'https://openrouter.ai/api/v1/chat/completions',
            'headers': {'Authorization': f'Bearer {os.getenv("OPENROUTER_API_KEY")}', 'Content-Type': 'application/json'},
            'data': {'model': 'anthropic/claude-3-sonnet', 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': 2000}
        },
        {
            'name': 'Groq',
            'env_key': 'GROQ_API_KEY',
            'url': 'https://api.groq.com/openai/v1/chat/completions',
            'headers': {'Authorization': f'Bearer {os.getenv("GROQ_API_KEY")}', 'Content-Type': 'application/json'},
            'data': {'model': 'llama-3.1-8b-instant', 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': 2000}
        }
    ]
    
    for provider in providers:
        api_key = os.getenv(provider['env_key'])
        if not api_key:
            logger.info(f"Пропуск {provider['name']}: API ключ не найден")
            continue
            
        try:
            logger.info(f"Попытка генерации через {provider['name']}")
            response = requests.post(
                provider['url'],
                headers=provider['headers'],
                json=provider['data'],
                timeout=45
            )
            
            if response.status_code == 200:
                content = response.json()['choices'][0]['message']['content'].strip()
                logger.info(f"Успешная генерация через {provider['name']}")
                return content, provider['name']
            else:
                logger.warning(f"{provider['name']} вернул статус {response.status_code}: {response.text}")
                
        except Exception as e:
            logger.warning(f"{provider['name']} не сработал: {e}")
    
    logger.info("Использование fallback контента")
    return generate_fallback_content(prompt), "fallback"

# ====== Генерация изображения ======
def generate_article_image(title):
    fb_key = os.getenv('FUSIONBRAIN_API_KEY')
    fb_secret = os.getenv('FUSION_SECRET_KEY')
    
    if fb_key and fb_secret:
        try:
            fb = FusionBrainAPI(fb_key, fb_secret)
            prompt = f"{title}, digital art, futuristic, professional, high quality"
            task_id = fb.generate(prompt, width=800, height=400)
            
            if task_id:
                logger.info(f"Ожидание генерации изображения...")
                b64 = fb.check_status(task_id)
                if b64:
                    try:
                        image_data = base64.b64decode(b64)
                        return save_image_bytes(image_data, title)
                    except Exception as e:
                        logger.error(f"Ошибка декодирования изображения: {e}")
        except Exception as e:
            logger.error(f"Ошибка FusionBrain API: {e}")
    
    logger.info("Создание placeholder изображения")
    return generate_placeholder_image(title)

# ====== Работа с файлами ======
def clean_old_articles(keep_last=3):
    os.makedirs("content/posts", exist_ok=True)
    posts = sorted([f for f in os.listdir("content/posts") if f.endswith(".md")], reverse=True)
    
    for post in posts[keep_last:]:
        file_path = os.path.join("content/posts", post)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Удалена старая статья: {post}")
            except Exception as e:
                logger.error(f"Ошибка удаления файла {post}: {e}")

def sanitize_title(title):
    """Очистка заголовка от специальных символов"""
    return re.sub(r'[^\w\s\-]', '', title)

def generate_frontmatter(title, content, model, image_file):
    sanitized_title = sanitize_title(title)
    return f"""---
title: "{sanitized_title}"
date: {datetime.now().isoformat()}
image: "{image_file}"
model: "{model}"
---

{content}
"""

def generate_content():
    try:
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
        
    except Exception as e:
        logger.error(f"Критическая ошибка в generate_content: {e}")
        return None
def update_index():
    """Обновляет индексную страницу со списком последних статей"""
    posts = sorted([f for f in os.listdir("content/posts") if f.endswith(".md")], reverse=True)
    
    index_content = """# Последние статьи\n\n"""
    
    for post in posts[:5]:
        with open(f"content/posts/{post}", "r", encoding="utf-8") as f:
            content = f.read()
            # Извлекаем заголовок из frontmatter
            title_match = re.search(r'title: "(.*?)"', content)
            if title_match:
                title = title_match.group(1)
                date = post.split("-")[:3]
                date_str = f"{date[2].split('.')[0]}.{date[1]}.{date[0]}"
                index_content += f"- [{title}](/content/posts/{post}) - {date_str}\n"
    
    with open("index.md", "w", encoding="utf-8") as f:
        f.write(index_content)

if __name__ == "__main__":
    generate_content()
