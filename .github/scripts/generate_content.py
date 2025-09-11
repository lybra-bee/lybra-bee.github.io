#!/usr/bin/env python3
import os
import json
import requests
import time
import logging
import glob
import shutil
from datetime import datetime
from slugify import slugify
import yaml

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Ключи API
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Директории
POSTS_DIR = 'content/posts'
STATIC_DIR = 'static/images/posts'
GALLERY_DIR = 'assets/gallery'
GALLERY_FILE = 'data/gallery.yaml'
PLACEHOLDER = 'static/images/placeholder.jpg'

os.makedirs(POSTS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(GALLERY_DIR, exist_ok=True)
os.makedirs(os.path.dirname(PLACEHOLDER), exist_ok=True)
os.makedirs(os.path.dirname(GALLERY_FILE), exist_ok=True)

def safe_yaml_value(value):
    if not value:
        return ""
    return str(value).replace('"', "'").replace(':', ' -').replace('\n', ' ').replace('\r', ' ').strip()

def generate_with_openrouter(prompt):
    try:
        if not OPENROUTER_API_KEY:
            return None
        logging.info("🌐 Используем OpenRouter...")
        headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
        r = requests.post("https://openrouter.ai/api/v1/chat/completions",
                          headers=headers,
                          json={"model": "gpt-4o-mini",
                                "messages":[{"role":"user","content":prompt}],
                                "max_tokens": 1000},
                          timeout=30)
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"].strip().strip('"')
        logging.info("✅ OpenRouter ответ получен")
        return content
    except Exception as e:
        logging.warning(f"⚠️ OpenRouter не сработал: {e}")
        return None

def generate_article():
    header_prompt = "Придумай интересный заголовок о последних трендах в искусственном интеллекте и технологиях (не более 7 слов)"
    logging.info("📝 Генерация заголовка...")
    title = generate_with_openrouter(header_prompt)
    if not title:
        title = "Новые тренды в искусственном интеллекте 2025"
        logging.warning("⚠️ Не удалось получить заголовок от API — fallback")
    logging.info(f"✅ Заголовок: {title}")

    content_prompt = f"Напиши подробную статью на русском языке 500-600 слов по заголовку: {title}. Сделай текст информативным и интересным."
    logging.info("📝 Генерация текста статьи...")
    text = generate_with_openrouter(content_prompt)
    if not text:
        text = f"""Искусственный интеллект продолжает революционизировать различные отрасли. В 2025 году мы наблюдаем несколько ключевых трендов:

1. **Генеративный AI** - модели типа GPT стали доступны широкой публике
2. **Мультимодальность** - AI работает с текстом, изображениями и аудио одновременно
3. **Этический AI** - повышенное внимание к безопасности и этике

Эти технологии меняют нашу повседневную жизнь и бизнес-процессы."""
        logging.warning("⚠️ Все генераторы не сработали — fallback")

    return title, text, "AI Generator"

def generate_image(title, slug):
    try:
        logging.info("🖼️ Создание SVG-заглушки для изображения...")
        img_path = os.path.join(STATIC_DIR, f"{slug}.svg")
        safe_title = title.replace('"', '').replace("'", "")
        svg_content = f'''<svg width="1200" height="630" xmlns="http://www.w3.org/2000/svg">
<defs>
<linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
<stop offset="0%" stop-color="#667eea"/>
<stop offset="100%" stop-color="#764ba2"/>
</linearGradient>
</defs>
<rect width="100%" height="100%" fill="url(#grad)"/>
<text x="600" y="300" font-family="Arial" font-size="48" fill="white" text-anchor="middle" font-weight="bold">{safe_title}</text>
<text x="600" y="380" font-family="Arial" font-size="24" fill="rgba(255,255,255,0.8)" text-anchor="middle">AI Generated Content</text>
</svg>'''
        with open(img_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)
        logging.info(f"✅ Изображение создано: {img_path}")
        return img_path
    except Exception as e:
        logging.error(f"❌ Ошибка создания изображения: {e}")
        return PLACEHOLDER

def update_gallery(slug):
    """Обновляет галерею из всех изображений в STATIC_DIR"""
    try:
        gallery = []
        for file in sorted(os.listdir(STATIC_DIR)):
            if file.endswith(('.svg', '.png', '.jpg')):
                src = os.path.join(STATIC_DIR, file)
                dst = os.path.join(GALLERY_DIR, file)
                shutil.copy2(src, dst)
                gallery.append({
                    "title": file,
                    "alt": file,
                    "src": f"/{dst.replace(os.sep, '/')}",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "tags": ["AI", "Tech"]
                })
        with open(GALLERY_FILE, 'w', encoding='utf-8') as f:
            yaml.safe_dump(gallery, f, allow_unicode=True, default_flow_style=False)
        logging.info(f"✅ Галерея обновлена: {len(gallery)} изображений")
    except Exception as e:
        logging.error(f"❌ Ошибка обновления галереи: {e}")

def save_article(title, text, model, slug, image_path):
    try:
        filename = os.path.join(POSTS_DIR, f'{slug}.md')
        image_url = f"/{image_path.replace(os.sep, '/')}"
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
        content = f"---\n{yaml_content}---\n\n{text}\n"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        logging.info(f"✅ Статья сохранена: {filename}")
    except Exception as e:
        logging.error(f"❌ Ошибка сохранения статьи: {e}")

def cleanup_old_posts(keep=10):
    try:
        posts = sorted(glob.glob(os.path.join(POSTS_DIR, "*.md")), key=os.path.getmtime, reverse=True)
        if len(posts) > keep:
            for old_post in posts[keep:]:
                slug = os.path.splitext(os.path.basename(old_post))[0]
                os.remove(old_post)
                logging.info(f"🗑 Удалена старая статья: {old_post}")
    except Exception as e:
        logging.error(f"❌ Ошибка очистки: {e}")

def main():
    logging.info("🚀 Запуск генерации контента...")
    title, text, model = generate_article()
    slug = slugify(title)
    image_path = generate_image(title, slug)
    save_article(title, text, model, slug, image_path)
    update_gallery(slug)
    cleanup_old_posts(keep=10)
    logging.info("🎉 Генерация завершена успешно!")

if __name__ == "__main__":
    main()
