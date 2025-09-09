#!/usr/bin/env python3
import os
import json
import requests
import time
import logging
import glob
from datetime import datetime
from slugify import slugify
import yaml

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# API ключи из переменных окружения
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
CLOUDFLARE_API_KEY = os.environ.get("CLOUDFLARE_API_KEY")
ACCOUNT_ID = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "3799ba295e1ecd90aeb9c3d6e8173edb")  # поменяй на свой

POSTS_DIR = 'content/posts'
STATIC_DIR = 'static/images/posts'
GALLERY_FILE = 'data/gallery.yaml'
PLACEHOLDER = 'static/images/placeholder.jpg'

os.makedirs(POSTS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(os.path.dirname(PLACEHOLDER), exist_ok=True)
os.makedirs(os.path.dirname(GALLERY_FILE), exist_ok=True)

def safe_yaml_value(value):
    if not value: return ""
    return str(value).replace('"', "'").replace(':', ' -').replace('\n', ' ').replace('\r', ' ').strip()

# ---------------------- OpenRouter генерация ----------------------
def generate_with_openrouter(prompt):
    try:
        if not OPENROUTER_API_KEY:
            return None
        logging.info("🌐 Используем OpenRouter...")
        headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
        r = requests.post("https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json={
                "model": "gpt-4o-mini", 
                "messages":[{"role":"user","content":prompt}],
                "max_tokens": 1000
            },
            timeout=30
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip().strip('"')
    except Exception as e:
        logging.warning(f"⚠️ OpenRouter не сработал: {e}")
        return None

# ---------------------- Генерация статьи ----------------------
def generate_article():
    header_prompt = "Придумай интересный заголовок о последних трендах в искусственном интеллекте и технологиях 2025 года (не более 7 слов)"
    try:
        logging.info("📝 Генерация заголовка...")
        title = generate_with_openrouter(header_prompt)
        if not title:
            title = "Новые тренды в искусственном интеллекте 2025"
        logging.info(f"✅ Заголовок: {title}")

        content_prompt = f"Напиши подробную статью на русском языке 500-600 слов по заголовку: {title}. Сделай текст информативным и интересным."
        logging.info("📝 Генерация статьи...")
        text = generate_with_openrouter(content_prompt)
        if not text:
            text = f"""Искусственный интеллект продолжает революционизировать различные отрасли в 2025 году. Ключевые тренды:

1. **Генеративный AI** - новые модели стали еще мощнее
2. **Мультимодальность** - AI работает с текстом, изображениями и аудио
3. **Этический AI** - безопасность и этика на первом месте

Эти технологии меняют жизнь и бизнес."""
        return title, text, "AI Generator"
    except Exception as e:
        logging.error(f"❌ Ошибка генерации: {e}")
        fallback_text = "Искусственный интеллект продолжает развиваться быстрыми темпами."
        return "Развитие искусственного интеллекта 2025", fallback_text, "Fallback"

# ---------------------- Cloudflare генерация изображения ----------------------
def generate_image_cloudflare(prompt, slug):
    try:
        logging.info("🖼️ Генерация изображения через Cloudflare...")
        api_url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/run/@cf/images/generate"
        headers = {"Authorization": f"Bearer {CLOUDFLARE_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "input": [
                {"role": "system", "content": "You are an AI that generates beautiful images from text prompts."},
                {"role": "user", "content": prompt}
            ]
        }
        r = requests.post(api_url, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
        # Получаем URL сгенерированного изображения (пример структуры)
        image_url = data['result'][0]['url'] if 'result' in data and len(data['result']) > 0 else None
        if not image_url:
            raise Exception("Нет URL изображения в ответе Cloudflare")
        # Скачиваем и сохраняем локально
        local_path = os.path.join(STATIC_DIR, f"{slug}.png")
        img_data = requests.get(image_url).content
        with open(local_path, 'wb') as f:
            f.write(img_data)
        logging.info(f"✅ Изображение сохранено: {local_path}")
        return f"/images/posts/{slug}.png"
    except Exception as e:
        logging.error(f"❌ Ошибка при генерации изображения: {e}")
        return PLACEHOLDER

# ---------------------- Обновление галереи ----------------------
def update_gallery(title, slug, image_path):
    try:
        gallery = []
        if os.path.exists(GALLERY_FILE):
            try:
                with open(GALLERY_FILE, 'r', encoding='utf-8') as f:
                    gallery = yaml.safe_load(f) or []
            except Exception as e:
                logging.warning(f"⚠️ Ошибка чтения галереи: {e}")
                gallery = []

        image_src = image_path if image_path.startswith('/') else f"/{image_path}"
        gallery.insert(0, {
            "title": safe_yaml_value(title),
            "alt": safe_yaml_value(title),
            "src": image_src,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "tags": ["AI", "Tech"]
        })
        gallery = gallery[:20]
        with open(GALLERY_FILE, 'w', encoding='utf-8') as f:
            yaml.safe_dump(gallery, f, allow_unicode=True, default_flow_style=False)
        logging.info(f"✅ Галерея обновлена: {len(gallery)} изображений")
    except Exception as e:
        logging.error(f"❌ Ошибка обновления галереи: {e}")

# ---------------------- Сохранение статьи ----------------------
def save_article(title, text, model, slug, image_path):
    try:
        filename = os.path.join(POSTS_DIR, f'{slug}.md')
        image_url = image_path if image_path.startswith('/') else f"/{image_path}"
        front_matter = {
            'title': safe_yaml_value(title),
            'date': datetime.now().strftime("%Y-%m-%dT%H:%M:%S+03:00"),
            'image': image_url,
            'draft': False,
            'tags': ["AI", "Tech", "Нейросети"],
            'categories': ["Технологии"],
            'author': "AI Generator",
            'type': "posts",
            'description': safe_yaml_value(text[:150] + "..." if len(text) > 150 else text)
        }
        yaml_content = yaml.safe_dump(front_matter, allow_unicode=True, default_flow_style=False, sort_keys=False)
        content = f"""---
{yaml_content}---

{text}
"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        logging.info(f"✅ Статья сохранена: {filename}")
    except Exception as e:
        logging.error(f"❌ Ошибка сохранения статьи: {e}")

# ---------------------- Очистка старых постов ----------------------
def cleanup_old_posts(keep=5):
    try:
        posts = sorted(glob.glob(os.path.join(POSTS_DIR, "*.md")), key=os.path.getmtime, reverse=True)
        if len(posts) > keep:
            for old_post in posts[keep:]:
                slug = os.path.splitext(os.path.basename(old_post))[0]
                os.remove(old_post)
                logging.info(f"🗑 Удалена старая статья: {old_post}")
                for ext in ['.png', '.svg', '.jpg']:
                    img_path = os.path.join(STATIC_DIR, f"{slug}{ext}")
                    if os.path.exists(img_path):
                        os.remove(img_path)
                        logging.info(f"🗑 Удалено старое изображение: {img_path}")
    except Exception as e:
        logging.error(f"❌ Ошибка очистки: {e}")

# ---------------------- Main ----------------------
def main():
    try:
        logging.info("🚀 Запуск генерации контента...")
        title, text, model = generate_article()
        slug = slugify(title)
        logging.info(f"📄 Сгенерирована статья: {title}")

        # Генерация изображения через Cloudflare
        image_path = generate_image_cloudflare(title, slug)
        logging.info(f"🖼️ Сгенерировано изображение: {image_path}")

        save_article(title, text, model, slug, image_path)
        update_gallery(title, slug, image_path)
        cleanup_old_posts()
        logging.info("🎉 Генерация контента завершена!")
    except Exception as e:
        logging.error(f"❌ Ошибка в main: {e}")

if __name__ == "__main__":
    main()
