#!/usr/bin/env python3
import os
import sys
import json
import requests
import time
import logging
import glob
import shutil
from datetime import datetime
from slugify import slugify
import yaml

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
GALLERY_SRC_DIR = 'static/images/posts'
GALLERY_DEST_DIR = 'assets/gallery'
POSTS_DIR = 'content/posts'
GALLERY_FILE = 'data/gallery.yaml'
PLACEHOLDER = 'static/images/placeholder.svg'

os.makedirs(POSTS_DIR, exist_ok=True)
os.makedirs(GALLERY_SRC_DIR, exist_ok=True)
os.makedirs(GALLERY_DEST_DIR, exist_ok=True)
os.makedirs(os.path.dirname(PLACEHOLDER), exist_ok=True)
os.makedirs(os.path.dirname(GALLERY_FILE), exist_ok=True)

def safe_yaml_value(value):
    if not value:
        return ""
    return str(value).replace('"', "'").replace(':', ' -').replace('\n', ' ').replace('\r', ' ').strip()

def generate_with_groq(prompt, max_tokens=1000):
    if not GROQ_API_KEY:
        logging.warning("⚠️ Groq API ключ не найден.")
        return None
    try:
        logging.info("🌐 Используем Groq...")
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        r = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json={
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens
        }, timeout=60)
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"].strip()
        logging.info("✅ Groq ответ получен")
        return content
    except Exception as e:
        logging.warning(f"⚠️ Groq не сработал: {e}")
        return None

def generate_with_openrouter(prompt, max_tokens=1000):
    if not OPENROUTER_API_KEY:
        logging.warning("⚠️ OpenRouter API ключ не найден.")
        return None
    try:
        logging.info("🌐 Используем OpenRouter...")
        headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
        r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json={
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens
        }, timeout=60)
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"].strip()
        logging.info("✅ OpenRouter ответ получен")
        return content
    except Exception as e:
        logging.warning(f"⚠️ OpenRouter не сработал: {e}")
        return None

def generate_article():
    header_prompt = "Придумай интересный заголовок о последних трендах в искусственном интеллекте и технологиях (не более 7 слов)"
    logging.info("📝 Генерация заголовка...")
    title = generate_with_groq(header_prompt, max_tokens=50)
    model = "Groq"
    if not title:
        logging.info("🔄 Пробуем OpenRouter для заголовка...")
        title = generate_with_openrouter(header_prompt, max_tokens=50)
        model = "OpenRouter"
    if not title:
        title = "Новые тренды в ИИ 2025"
        model = "Fallback"
        logging.warning("⚠️ Не удалось получить заголовок — fallback")
    logging.info(f"✅ Заголовок: {title}")

    content_prompt = f"Напиши подробную статью на русском языке 500-600 слов по заголовку: {title}. Сделай текст информативным и интересным."
    logging.info("📝 Генерация текста статьи...")
    text = generate_with_groq(content_prompt, max_tokens=1500)
    if not text:
        logging.info("🔄 Пробуем OpenRouter для текста...")
        text = generate_with_openrouter(content_prompt, max_tokens=1500)
    if not text:
        text = """Искусственный интеллект продолжает революционизировать отрасли. В 2025 году ключевые тренды:

1. **Генеративный AI** - модели GPT доступны всем.
2. **Мультимодальность** - AI обрабатывает текст, изображения, аудио.
3. **Этический AI** - фокус на безопасности и этике."""
        logging.warning("⚠️ Все генераторы не сработали — fallback")
    return title, text, model

def generate_image(title, slug):
    logging.info("🖼️ Пробуем DeepAI для изображения...")
    prompt = f"{title}, futuristic AI theme, sci-fi style, high-tech"
    try:
        r = requests.post("https://api.deepai.org/api/text2img", data={"text": prompt}, timeout=30)
        r.raise_for_status()
        img_url = r.json()["output_url"]
        img_data = requests.get(img_url, timeout=30).content
        img_path = os.path.join(GALLERY_SRC_DIR, f"{slug}.png")
        with open(img_path, 'wb') as f:
            f.write(img_data)
        logging.info(f"✅ Изображение сгенерировано: {img_path}")
        return f"/images/posts/{slug}.png"
    except Exception as e:
        logging.error(f"❌ DeepAI не сработал: {e}")
        return generate_placeholder(title, slug)

def generate_placeholder(title, slug):
    logging.info("🖼️ Создание SVG-placeholder...")
    img_path = os.path.join(GALLERY_SRC_DIR, f"{slug}.svg")
    safe_title = title.replace('"', '').replace("'", "")
    svg_content = f'''<svg width="1200" height="630" xmlns="http://www.w3.org/2000/svg">
<defs><linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
<stop offset="0%" stop-color="#667eea"/>
<stop offset="100%" stop-color="#764ba2"/>
</linearGradient></defs>
<rect width="100%" height="100%" fill="url(#grad)"/>
<text x="600" y="300" font-family="Arial" font-size="48" fill="white" text-anchor="middle" font-weight="bold">{safe_title}</text>
<text x="600" y="380" font-family="Arial" font-size="24" fill="rgba(255,255,255,0.8)" text-anchor="middle">AI Generated Content</text>
</svg>'''
    with open(img_path, 'w', encoding='utf-8') as f:
        f.write(svg_content)
    logging.info(f"✅ Placeholder создан: {img_path}")
    return f"/images/posts/{slug}.svg"

def save_article(title, text, model, slug, image_path):
    try:
        filename = os.path.join(POSTS_DIR, f"{slug}.md")
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

def update_gallery(slug, title, image_path):
    try:
        ext = os.path.splitext(image_path)[1]
        dest_path = os.path.join(GALLERY_DEST_DIR, f"{slug}{ext}")
        shutil.copy(os.path.join(GALLERY_SRC_DIR, f"{slug}{ext}"), dest_path)
        gallery = []
        if os.path.exists(GALLERY_FILE):
            with open(GALLERY_FILE, 'r', encoding='utf-8') as f:
                gallery = yaml.safe_load(f) or []
        gallery.insert(0, {
            'title': safe_yaml_value(title),
            'alt': safe_yaml_value(title),
            'src': f"/assets/gallery/{slug}{ext}",
            'date': datetime.now().strftime("%Y-%m-%d"),
            'tags': ["AI", "Tech"]
        })
        with open(GALLERY_FILE, 'w', encoding='utf-8') as f:
            yaml.safe_dump(gallery, f, allow_unicode=True, default_flow_style=False)
        logging.info(f"✅ Галерея обновлена: {len(gallery)} изображений")
    except Exception as e:
        logging.error(f"❌ Ошибка обновления галереи: {e}")

def cleanup_old_posts(keep=10):
    posts = sorted(glob.glob(os.path.join(POSTS_DIR, "*.md")), key=os.path.getmtime, reverse=True)
    for old_post in posts[keep:]:
        os.remove(old_post)
        logging.info(f"🗑 Удалена старая статья: {old_post}")

def main():
    logging.info("🚀 Запуск генерации контента...")
    title, text, model = generate_article()
    slug = slugify(title)
    image_path = generate_image(title, slug)
    save_article(title, text, model, slug, image_path)
    update_gallery(slug, title, image_path)
    cleanup_old_posts(keep=10)
    logging.info("🎉 Генерация завершена успешно!")

if __name__ == "__main__":
    main()
