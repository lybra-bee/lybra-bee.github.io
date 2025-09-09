#!/usr/bin/env python3
import os
import json
import requests
import logging
import glob
import base64
from datetime import datetime
from slugify import slugify
import yaml

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# API ключи
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
CLOUDFLARE_API_KEY = os.environ.get("CLOUDFLARE_API_KEY")
CLOUDFLARE_ACCOUNT_ID = os.environ.get("CLOUDFLARE_ACCOUNT_ID")  # Ваш Cloudflare Account ID

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


def generate_with_openrouter(prompt):
    """Генерация через OpenRouter"""
    try:
        if not OPENROUTER_API_KEY:
            return None
        headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1000
            },
            timeout=30
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip().strip('"')
    except Exception as e:
        logging.warning(f"⚠️ OpenRouter не сработал: {e}")
        return None


def generate_article():
    """Генерация заголовка и статьи"""
    header_prompt = "Придумай интересный заголовок о последних трендах в искусственном интеллекте и технологиях (не более 7 слов). Не используй прошлые года, всегда используй 2025."
    title = generate_with_openrouter(header_prompt)
    if not title:
        title = "Искусственный интеллект 2025: Тренды, меняющие мир"
    logging.info(f"✅ Заголовок: {title}")

    content_prompt = f"Напиши подробную статью на русском языке 500-600 слов по заголовку: {title}. Сделай текст информативным и интересным."
    text = generate_with_openrouter(content_prompt)
    if not text:
        text = f"""Искусственный интеллект продолжает революционизировать различные отрасли. В 2025 году мы наблюдаем несколько ключевых трендов:

1. **Генеративный AI** - модели типа GPT стали доступны широкой публике
2. **Мультимодальность** - AI работает с текстом, изображениями и аудио одновременно
3. **Этический AI** - повышенное внимание к безопасности и этике

Эти технологии меняют нашу повседневную жизнь и бизнес-процессы."""
    return title, text, "AI Generator"


def generate_image_cloudflare(prompt, slug):
    """Генерация изображения через Cloudflare AI Images"""
    if not CLOUDFLARE_API_KEY or not CLOUDFLARE_ACCOUNT_ID:
        logging.warning("⚠️ CLOUDFLARE_API_KEY или ACCOUNT_ID не установлены, используем placeholder")
        return PLACEHOLDER

    logging.info("🖼️ Генерация изображения через Cloudflare...")
    url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/@cf/images/generate"
    headers = {"Authorization": f"Bearer {CLOUDFLARE_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "@cf/images-gen-2",
        "prompt": prompt,
        "size": "1024x1024"
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        image_base64 = data['result']['images'][0]
        image_bytes = base64.b64decode(image_base64)
        image_path = os.path.join(STATIC_DIR, f"{slug}.png")
        with open(image_path, 'wb') as f:
            f.write(image_bytes)
        logging.info(f"✅ Изображение создано: {image_path}")
        return f"/images/posts/{slug}.png"
    except Exception as e:
        logging.error(f"❌ Ошибка при генерации изображения: {e}")
        return PLACEHOLDER


def update_gallery(title, slug, image_path):
    """Обновляет галерею"""
    try:
        gallery = []
        if os.path.exists(GALLERY_FILE):
            try:
                with open(GALLERY_FILE, 'r', encoding='utf-8') as f:
                    gallery = yaml.safe_load(f) or []
            except Exception as e:
                logging.warning(f"⚠️ Ошибка чтения галереи, создаем новую: {e}")
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


def save_article(title, text, model, slug, image_path):
    """Сохраняет статью с frontmatter"""
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
            'author': model,
            'type': "posts",
            'description': safe_yaml_value(text[:150] + "..." if len(text) > 150 else text)
        }
        yaml_content = yaml.safe_dump(front_matter, allow_unicode=True, default_flow_style=False, sort_keys=False)
        content = f"---\n{yaml_content}---\n\n{text}"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        logging.info(f"✅ Статья сохранена: {filename}")
    except Exception as e:
        logging.error(f"❌ Ошибка сохранения статьи: {e}")


def cleanup_old_posts(keep=5):
    """Очистка старых постов"""
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


def main():
    logging.info("🚀 Старт генерации контента...")
    cleanup_old_posts(keep=5)
    title, text, model = generate_article()
    slug = slugify(title)
    image_path = generate_image_cloudflare(title, slug)
    save_article(title, text, model, slug, image_path)
    update_gallery(title, slug, image_path)
    logging.info("🎉 Генерация завершена!")


if __name__ == "__main__":
    main()
