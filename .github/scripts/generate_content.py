#!/usr/bin/env python3
import os
import json
import requests
import time
import logging
import glob
import re
import datetime
from datetime import datetime
from slugify import slugify
import yaml

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
CLOUDFLARE_API_KEY = os.environ.get("CLOUDFLARE_API_KEY")
CLOUDFLARE_ACCOUNT_ID = os.environ.get("CLOUDFLARE_ACCOUNT_ID")  # добавляем
CLOUDFLARE_IMAGE_ENDPOINT = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/images/v1" if CLOUDFLARE_ACCOUNT_ID else None

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
    try:
        if not OPENROUTER_API_KEY:
            return None
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

def generate_article():
    header_prompt = "Придумай интересный заголовок о последних трендах в искусственном интеллекте и технологиях (не более 7 слов). Не используй старые годы."
    try:
        logging.info("📝 Генерация заголовка...")
        title = generate_with_openrouter(header_prompt)
        if not title:
            title = "Новые тренды в искусственном интеллекте"
        # фиксируем год
        now_year = datetime.now().year
        title = re.sub(r"20(2[0-4])", str(now_year), title)
        logging.info(f"✅ Заголовок: {title}")

        content_prompt = f"Напиши подробную статью на русском языке 500-600 слов по заголовку: {title}. Сделай текст информативным и интересным, с упоминанием {now_year} года."
        logging.info("📝 Генерация статьи...")
        text = generate_with_openrouter(content_prompt)
        if not text:
            text = f"""Искусственный интеллект продолжает революционизировать различные отрасли. В {now_year} году мы наблюдаем несколько ключевых трендов:

1. **Генеративный AI**  
2. **Мультимодальность**  
3. **Этический AI**  

Эти технологии меняют нашу повседневную жизнь и бизнес-процессы."""
        return title, text, "AI Generator"
    except Exception as e:
        logging.error(f"❌ Ошибка генерации: {e}")
        fallback_text = "Искусственный интеллект продолжает развиваться быстрыми темпами."
        return "Развитие искусственного интеллекта", fallback_text, "Fallback"

def generate_image(title, slug):
    """Попытка сгенерировать изображение через Cloudflare"""
    try:
        if not CLOUDFLARE_API_KEY or not CLOUDFLARE_IMAGE_ENDPOINT:
            logging.warning("⚠️ Cloudflare API ключ или endpoint не настроены, используется заглушка.")
            return f"/images/posts/{slug}.svg"

        logging.info("🖼️ Генерация изображения через Cloudflare...")
        prompt = f"Обложка статьи: {title}. Визуальный стиль — современный, футуристичный, минимализм."

        headers = {
            "Authorization": f"Bearer {CLOUDFLARE_API_KEY}"
        }
        files = {
            "requireSignedURLs": (None, "false"),
            "metadata": (None, json.dumps({"title": title})),
            "file": (f"{slug}.png", prompt, "text/plain")
        }

        r = requests.post(CLOUDFLARE_IMAGE_ENDPOINT, headers=headers, files=files, timeout=60)
        r.raise_for_status()
        result = r.json()

        if result.get("success"):
            cf_id = result["result"]["id"]
            cf_url = result["result"]["variants"][0]

            img_path = os.path.join(STATIC_DIR, f"{slug}.png")
            img_data = requests.get(cf_url, timeout=60)
            with open(img_path, "wb") as f:
                f.write(img_data.content)

            logging.info(f"✅ Изображение сохранено: {img_path}")
            return f"/images/posts/{slug}.png"
        else:
            logging.error(f"❌ Ошибка Cloudflare: {result}")
            return f"/images/posts/{slug}.svg"
    except Exception as e:
        logging.error(f"❌ Ошибка при генерации изображения: {e}")
        return f"/images/posts/{slug}.svg"

def update_gallery(title, slug, image_path):
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

def main():
    try:
        logging.info("🚀 Запуск генерации контента...")
        title, text, model = generate_article()
        slug = slugify(title)
        logging.info(f"📄 Сгенерирована статья: {title}")

        image_path = generate_image(title, slug)
        save_article(title, text, model, slug, image_path)
        update_gallery(title, slug, image_path)
        cleanup_old_posts(keep=5)
        logging.info("🎉 Генерация завершена успешно!")
    except Exception as e:
        logging.error(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    main()
