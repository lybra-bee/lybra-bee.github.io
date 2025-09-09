#!/usr/bin/env python3
import os
import yaml
import glob
import logging
from datetime import datetime
from slugify import slugify
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

POSTS_DIR = 'content/posts'
STATIC_DIR = 'static/images/posts'
GALLERY_FILE = 'data/gallery.yaml'
PLACEHOLDER = 'static/images/placeholder.jpg'

os.makedirs(POSTS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(os.path.dirname(GALLERY_FILE), exist_ok=True)
os.makedirs(os.path.dirname(PLACEHOLDER), exist_ok=True)

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

def safe_yaml_value(value):
    if not value:
        return ""
    return str(value).replace('"', "'").replace(':', ' -').replace('\n', ' ').strip()

def generate_with_openrouter(prompt):
    try:
        if not OPENROUTER_API_KEY:
            return None
        headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json={
                "model": "gpt-4o-mini",
                "messages":[{"role":"user","content":prompt}],
                "max_tokens": 1000
            },
            timeout=30
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logging.warning(f"⚠️ OpenRouter не сработал: {e}")
        return None

def generate_article():
    header_prompt = "Придумай интересный заголовок 2025 о последних трендах в искусственном интеллекте и технологиях (не более 7 слов, только 2025)"
    title = generate_with_openrouter(header_prompt)
    if not title:
        title = "Искусственный интеллект 2025: Тренды, меняющие мир"
    logging.info(f"📄 Заголовок: {title}")

    content_prompt = f"Напиши подробную статью на русском языке 500-600 слов по заголовку: {title}. Сделай текст информативным и интересным."
    text = generate_with_openrouter(content_prompt)
    if not text:
        text = f"""Искусственный интеллект продолжает революционизировать различные отрасли. В 2025 году мы наблюдаем несколько ключевых трендов:

1. **Генеративный AI** - модели типа GPT стали доступны широкой публике
2. **Мультимодальность** - AI работает с текстом, изображениями и аудио одновременно
3. **Этический AI** - повышенное внимание к безопасности и этике

Эти технологии меняют нашу повседневную жизнь и бизнес-процессы."""

    return title, text

def generate_svg_image(title, slug):
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
        <text x="600" y="300" font-family="Arial" font-size="48" fill="white" text-anchor="middle" font-weight="bold">
            {safe_title}
        </text>
        <text x="600" y="380" font-family="Arial" font-size="24" fill="rgba(255,255,255,0.8)" text-anchor="middle">
            AI Generated Content
        </text>
    </svg>'''
    with open(img_path, 'w', encoding='utf-8') as f:
        f.write(svg_content)
    return f"/images/posts/{slug}.svg"

def save_article(title, text, slug, image_path):
    filename = os.path.join(POSTS_DIR, f"{slug}.md")
    front_matter = {
        'title': safe_yaml_value(title),
        'date': datetime.now().strftime("%Y-%m-%dT%H:%M:%S+03:00"),
        'image': image_path,
        'draft': False,
        'tags': ["AI", "Tech", "Нейросети"],
        'categories': ["Технологии"],
        'author': "AI Generator",
        'type': "posts",
        'description': safe_yaml_value(text[:150] + "..." if len(text) > 150 else text)
    }
    yaml_content = yaml.safe_dump(front_matter, allow_unicode=True, default_flow_style=False, sort_keys=False)
    content = f"---\n{yaml_content}---\n\n{text}\n"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    logging.info(f"✅ Статья сохранена: {filename}")

def update_gallery(title, slug, image_path):
    gallery = []
    if os.path.exists(GALLERY_FILE):
        try:
            with open(GALLERY_FILE, 'r', encoding='utf-8') as f:
                gallery = yaml.safe_load(f) or []
        except:
            gallery = []
    gallery.insert(0, {
        "title": safe_yaml_value(title),
        "alt": safe_yaml_value(title),
        "src": image_path,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "tags": ["AI", "Tech"]
    })
    gallery = gallery[:20]
    with open(GALLERY_FILE, 'w', encoding='utf-8') as f:
        yaml.safe_dump(gallery, f, allow_unicode=True, default_flow_style=False)
    logging.info(f"✅ Галерея обновлена: {len(gallery)} изображений")

def cleanup_old_posts(keep=5):
    posts = sorted(glob.glob(os.path.join(POSTS_DIR, "*.md")), key=os.path.getmtime, reverse=True)
    if len(posts) > keep:
        for old_post in posts[keep:]:
            os.remove(old_post)
            logging.info(f"🗑 Удалена старая статья: {old_post}")

def main():
    logging.info("🚀 Запуск генерации контента...")
    title, text = generate_article()
    slug = slugify(title)
    image_path = generate_svg_image(title, slug)
    save_article(title, text, slug, image_path)
    update_gallery(title, slug, image_path)
    cleanup_old_posts(keep=5)
    logging.info("🎉 Генерация завершена успешно!")

if __name__ == "__main__":
    main()
