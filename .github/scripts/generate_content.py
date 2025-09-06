#!/usr/bin/env python3
import os
import json
import requests
import base64
import logging
import shutil
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import yaml
import re
import time

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
    
    def generate(self, prompt, width=1024, height=512):
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
    logger.info(f"Изображение сохранено в assets: {filename}")
    return f"/images/posts/{slug}.png"

def generate_placeholder_image(title):
    os.makedirs("assets/images/posts", exist_ok=True)
    slug = generate_slug(title)
    filename = f"assets/images/posts/{slug}.png"
    
    img = Image.new('RGB', (1024, 512), color='#0f172a')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        font = ImageFont.load_default()
    
    bbox = draw.textbbox((0, 0), title, font=font)
    x = (1024 - (bbox[2]-bbox[0])) / 2
    y = (512 - (bbox[3]-bbox[1])) / 2
    draw.text((x, y), title, fill='white', font=font)
    img.save(filename)
    
    logger.info(f"Placeholder создан: {filename}")
    return f"/images/posts/{slug}.png"

def copy_images_to_static():
    os.makedirs("static/images/posts", exist_ok=True)
    assets_dir = "assets/images/posts"
    if not os.path.exists(assets_dir):
        logger.warning(f"❌ {assets_dir} не существует")
        return False
    image_files = [f for f in os.listdir(assets_dir) if f.lower().endswith(('.png','.jpg','.jpeg'))]
    success = 0
    for img_file in image_files:
        try:
            shutil.copy2(os.path.join(assets_dir,img_file), os.path.join("static/images/posts",img_file))
            success += 1
        except Exception as e:
            logger.error(f"Ошибка копирования {img_file}: {e}")
    logger.info(f"Скопировано {success}/{len(image_files)} изображений")
    return success > 0

def update_hugo_data():
    os.makedirs("data", exist_ok=True)
    target_dir = "static/images/posts"
    gallery_images = []
    if os.path.exists(target_dir):
        for img_file in os.listdir(target_dir):
            if img_file.lower().endswith(('.png','.jpg','.jpeg')):
                name = os.path.splitext(img_file)[0].replace('-', ' ').title()
                gallery_images.append({
                    'src': f"/images/posts/{img_file}",
                    'alt': f"AI generated image: {name}",
                    'title': name,
                    'filename': img_file
                })
    if not gallery_images:
        gallery_images.append({
            'src': '/images/placeholder.jpg',
            'alt': 'AI generated images will appear here soon',
            'title': 'Gallery Placeholder',
            'filename': 'placeholder.jpg'
        })
    with open("data/gallery.yaml", "w", encoding="utf-8") as f:
        yaml.dump(gallery_images, f, allow_unicode=True, default_flow_style=False)
    with open("data/gallery.json", "w", encoding="utf-8") as f:
        json.dump(gallery_images, f, ensure_ascii=False, indent=2)
    logger.info(f"Данные галереи обновлены: {len(gallery_images)} изображений")

# ====== Генерация статьи ======
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
            response = requests.post(provider['url'], headers=provider['headers'], json=provider['data'], timeout=60)
            if response.status_code == 200:
                content = response.json()['choices'][0]['message']['content'].strip()
                logger.info(f"Статья сгенерирована через {provider['name']}")
                return content
            else:
                logger.warning(f"{provider['name']} вернул статус {response.status_code}")
        except Exception as e:
            logger.warning(f"{provider['name']} не сработал: {e}")
    # fallback
    logger.info("Используем fallback статью")
    return "# Тенденции AI 2025\n\nСтатья о последних трендах в AI и высоких технологиях.\n\n*Сгенерировано автоматически*"

def extract_title_from_markdown(md_text):
    for line in md_text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    # fallback
    return "AI Article"

def generate_frontmatter(title, content, image_path):
    frontmatter = {
        'title': title,
        'date': datetime.now().isoformat(),
        'draft': False,
        'image': image_path,
        'categories': ['AI'],
        'tags': ['автоматическая генерация', 'искусственный интеллект']
    }
    return f"---\n{yaml.dump(frontmatter, allow_unicode=True)}---\n\n{content}"

def clean_old_articles(keep_last=5):
    os.makedirs("content/posts", exist_ok=True)
    posts = [f for f in os.listdir("content/posts") if f.endswith(".md")]
    posts.sort(key=lambda x: os.path.getmtime(os.path.join("content/posts", x)), reverse=True)
    for post in posts[keep_last:]:
        try:
            os.remove(os.path.join("content/posts", post))
            logger.info(f"Удалена старая статья: {post}")
        except Exception as e:
            logger.error(f"Ошибка удаления {post}: {e}")

# ====== Основная функция ======
def generate_content():
    try:
        logger.info("=== НАЧАЛО ГЕНЕРАЦИИ СТАТЬИ ===")
        clean_old_articles(keep_last=5)
        prompt = "Проанализируй последние тренды в искусственном интеллекте и высоких технологиях и напиши статью на 400-600 слов."
        content = generate_article_content(prompt)
        title = extract_title_from_markdown(content)
        slug = re.sub(r'[^\w\s-]', '', title).replace(' ','-').lower()
        image_path = generate_placeholder_image(title)
        fb_key = os.getenv('FUSIONBRAIN_API_KEY')
        fb_secret = os.getenv('FUSION_SECRET_KEY')
        if fb_key and fb_secret:
            fb = FusionBrainAPI(fb_key, fb_secret)
            task_id = fb.generate(title, width=1024, height=512)
            if task_id:
                b64 = fb.check_status(task_id)
                if b64:
                    image_data = base64.b64decode(b64)
                    image_path = save_image_bytes(image_data, title)
        filename = f"content/posts/{datetime.now().strftime('%Y-%m-%d-%H%
