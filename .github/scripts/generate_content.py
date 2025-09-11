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

# Принудительный вывод логов в stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# ---------------------------
# Конфигурация
# ---------------------------
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
# Groq отключаем, так как он часто падает
GALLERY_SRC_DIR = 'static/images/posts'
GALLERY_DEST_DIR = 'assets/gallery'
POSTS_DIR = 'content/posts'
GALLERY_FILE = 'data/gallery.yaml'
PLACEHOLDER = 'static/images/placeholder.jpg'

os.makedirs(POSTS_DIR, exist_ok=True)
os.makedirs(GALLERY_SRC_DIR, exist_ok=True)
os.makedirs(GALLERY_DEST_DIR, exist_ok=True)
os.makedirs(os.path.dirname(PLACEHOLDER), exist_ok=True)
os.makedirs(os.path.dirname(GALLERY_FILE), exist_ok=True)

# ---------------------------
# Утилиты
# ---------------------------
def safe_yaml_value(value):
    if not value: return ""
    return str(value).replace('"', "'").replace(':', ' -').replace('\n', ' ').replace('\r', ' ').strip()

# ---------------------------
# Генерация через OpenRouter
# ---------------------------
def generate_with_openrouter(prompt, max_tokens=1000):
    if not OPENROUTER_API_KEY:
        logging.warning("⚠️ OpenRouter API ключ не найден.")
        return None
    try:
        logging.info("🌐 Используем OpenRouter...")
        headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
        r = requests.post("https://openrouter.ai/api/v1/chat/completions",
                          headers=headers,
                          json={
                              "model": "gpt-4o-mini",
                              "messages": [{"role":"user","content":prompt}],
                              "max_tokens": max_tokens
                          },
                          timeout=60)
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"].strip()
        logging.info("✅ OpenRouter ответ получен")
        return content
    except Exception as e:
        logging.warning(f"⚠️ OpenRouter не сработал: {e}")
        return None

# ---------------------------
# Генерация статьи
# ---------------------------
def generate_article():
    header_prompt = "Придумай интересный заголовок о последних трендах в искусственном интеллекте и технологиях (не более 7 слов)"
    logging.info("📝 Генерация заголовка...")
    title = generate_with_openrouter(header_prompt, max_tokens=50)
    if not title:
        title = "Новые тренды в искусственном интеллекте 2025"
        logging.warning("⚠️ Не удалось получить заголовок от API — fallback")
    logging.info(f"✅ Заголовок: {title}")

    content_prompt = f"Напиши подробную статью на русском языке 500-600 слов по заголовку: {title}. Сделай текст информативным и интересным."
    logging.info("📝 Генерация текста статьи...")
    text = generate_with_openrouter(content_prompt, max_tokens=1500)
    if not text:
        text = f"""Искусственный интеллект продолжает революционизировать различные отрасли. В 2025 году мы наблюдаем несколько ключевых трендов:

1. **Генеративный AI** - модели типа GPT стали доступны широкой публике
2. **Мультимодальность** - AI работает с текстом, изображениями и аудио одновременно
3. **Этический AI** - повышенное внимание к безопасности и этике

Эти технологии меняют нашу повседневную жизнь и бизнес-процессы."""
        logging.warning("⚠️ Все генераторы не сработали — fallback")
    return title, text, "OpenRouter"

# ---------------------------
# Создание SVG-заглушки
# ---------------------------
def generate_image(title, slug):
    try:
        logging.info("🖼️ Создание SVG-заглушки для изображения...")
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
        logging.info(f"✅ Изображение создано: {img_path}")
        return f"/images/posts/{slug}.svg"
    except Exception as e:
        logging.error(f"❌ Ошибка создания изображения: {e}")
        return PLACEHOLDER

# ---------------------------
# Сохранение статьи
# ---------------------------
def save_article(title, text, model, slug, image_path):
    try:
        filename = os.path.join(POSTS_DIR, f"{slug}.md")
        image_url = image_path if image_path.startswith('/') else f"/{image_path}"
        front_matter = {
            'title': safe_yaml_value(title),
            'date': datetime.now().strftime("%Y-%m-%dT%H:%M:%S+03:00"),
            'image': image_url,
            'draft': False,
            'tags': ["AI","Tech","Нейросети"],
            'categories': ["Технологии"],
            'author': model,
            'type': "posts",
            'description': safe_yaml_value(text[:150]+"..." if len(text)>150 else text)
        }
        yaml_content = yaml.safe_dump(front_matter, allow_unicode=True, default_flow_style=False, sort_keys=False)
        content = f"---\n{yaml_content}---\n\n{text}"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        logging.info(f"✅ Статья сохранена: {filename}")
    except Exception as e:
        logging.error(f"❌ Ошибка сохранения статьи: {e}")

# ---------------------------
# Обновление галереи
# ---------------------------
def update_gallery(slug, title, image_path):
    try:
        # Копируем изображение в assets/gallery
        dest_path = os.path.join(GALLERY_DEST_DIR, f"{slug}.svg")
        shutil.copy(image_path.lstrip('/'), dest_path)

        # Загружаем текущую галерею
        gallery = []
        if os.path.exists(GALLERY_FILE):
            with open(GALLERY_FILE,'r',encoding='utf-8') as f:
                gallery = yaml.safe_load(f) or []

        gallery.insert(0,{
            'title': safe_yaml_value(title),
            'alt': safe_yaml_value(title),
            'src': f"/assets/gallery/{slug}.svg",
            'date': datetime.now().strftime("%Y-%m-%d"),
            'tags': ["AI","Tech"]
        })

        with open(GALLERY_FILE,'w',encoding='utf-8') as f:
            yaml.safe_dump(gallery,f,allow_unicode=True,default_flow_style=False)
        logging.info(f"✅ Галерея обновлена: {len(gallery)} изображений")
    except Exception as e:
        logging.error(f"❌ Ошибка обновления галереи: {e}")

# ---------------------------
# Очистка старых постов
# ---------------------------
def cleanup_old_posts(keep=10):
    posts = sorted(glob.glob(os.path.join(POSTS_DIR,"*.md")), key=os.path.getmtime, reverse=True)
    for old_post in posts[keep:]:
        slug = os.path.splitext(os.path.basename(old_post))[0]
        os.remove(old_post)
        logging.info(f"🗑 Удалена старая статья: {old_post}")
        # Удаляем изображения
        for ext in ['.svg','.png','.jpg']:
            img_path = os.path.join(GALLERY_SRC_DIR,f"{slug}{ext}")
            if os.path.exists(img_path):
                os.remove(img_path)
                logging.info(f"🗑 Удалено старое изображение: {img_path}")
        # Удаляем из assets/gallery
        gallery_img = os.path.join(GALLERY_DEST_DIR,f"{slug}.svg")
        if os.path.exists(gallery_img):
            os.remove(gallery_img)
            logging.info(f"🗑 Удалено старое изображение из галереи: {gallery_img}")

# ---------------------------
# Main
# ---------------------------
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
