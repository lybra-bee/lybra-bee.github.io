#!/usr/bin/env python3
import os
import json
import requests
import time
import base64
import logging
import glob
from datetime import datetime
from slugify import slugify
import yaml

# =========================
# Настройка логирования
# =========================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# =========================
# API ключи и настройки
# =========================
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
SUBNP_BASE_URL = "https://t2i.mcpcore.xyz"

# =========================
# Папки и файлы
# =========================
POSTS_DIR = 'content/posts'
STATIC_DIR = 'static/images/posts'
GALLERY_FILE = 'data/gallery.yaml'
PLACEHOLDER = 'static/images/placeholder.jpg'

os.makedirs(POSTS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(os.path.dirname(PLACEHOLDER), exist_ok=True)
os.makedirs(os.path.dirname(GALLERY_FILE), exist_ok=True)

# =========================
# Утилиты
# =========================
def safe_yaml_value(value):
    if not value:
        return ""
    value = str(value).replace('"', "'").replace(':', ' -').replace('\n', ' ').replace('\r', ' ')
    return value.strip()

# =========================
# Генерация статьи
# =========================
def generate_article():
    header_prompt = "Проанализируй последние тренды в нейросетях и высоких технологиях и придумай привлекательный заголовок, не более восьми слов"
    
    # Генерация заголовка
    title = None
    for name, key, url in [
        ("OpenRouter", OPENROUTER_API_KEY, "https://openrouter.ai/api/v1/chat/completions"),
        ("Groq", GROQ_API_KEY, "https://api.groq.com/v1/chat/completions")
    ]:
        try:
            logging.info(f"📝 Генерация заголовка через {name}...")
            headers = {"Authorization": f"Bearer {key}"}
            r = requests.post(url, headers=headers,
                              json={"model": "gpt-4o-mini", "messages":[{"role":"user","content":header_prompt}]})
            r.raise_for_status()
            title = r.json()["choices"][0]["message"]["content"].strip().strip('"')
            logging.info(f"✅ Заголовок получен через {name}")
            break
        except Exception as e:
            logging.warning(f"⚠️ {name} заголовок не сработал: {e}")
    if not title:
        title = "Статья о последних трендах в ИИ"

    # Генерация текста
    content_prompt = f"Напиши статью 400-600 слов по заголовку: {title}"
    text = None
    model_used = None
    for name, key, url in [
        ("OpenRouter", OPENROUTER_API_KEY, "https://openrouter.ai/api/v1/chat/completions"),
        ("Groq", GROQ_API_KEY, "https://api.groq.com/v1/chat/completions")
    ]:
        try:
            logging.info(f"📝 Генерация статьи через {name}...")
            headers = {"Authorization": f"Bearer {key}"}
            r = requests.post(url, headers=headers,
                              json={"model": "gpt-4o-mini", "messages":[{"role":"user","content":content_prompt}]})
            r.raise_for_status()
            text = r.json()["choices"][0]["message"]["content"].strip()
            model_used = name
            logging.info(f"✅ Статья получена через {name}")
            break
        except Exception as e:
            logging.warning(f"⚠️ {name} статья не сработала: {e}")
    if not text:
        text = "Статья временно недоступна."
        model_used = "None"

    return title, text, model_used

# =========================
# Генерация изображения через SubNP
# =========================
def generate_image(title, slug):
    try:
        logging.info("[SubNP] Запрос на генерацию изображения...")
        payload = {
            "prompt": title,
            "model": "turbo"
        }
        r = requests.post(f"{SUBNP_BASE_URL}/api/free/generate", json=payload, timeout=60)
        r.raise_for_status()

        # SSE-поток имитируем через простой цикл с ожиданием
        # Поскольку прямой SSE в requests сложен, проверим сразу JSON
        try:
            data = r.json()
        except Exception:
            logging.error("❌ SubNP вернул не JSON, используем PLACEHOLDER")
            return PLACEHOLDER

        # Если сразу есть imageUrl
        image_url = data.get("imageUrl")
        if not image_url:
            logging.warning("⚠️ SubNP не вернул imageUrl, используем PLACEHOLDER")
            return PLACEHOLDER

        # Скачиваем изображение
        img_data = requests.get(image_url).content
        img_path = os.path.join(STATIC_DIR, f"{slug}.png")
        with open(img_path, 'wb') as f:
            f.write(img_data)
        logging.info(f"✅ Изображение сохранено: {img_path}")
        return f"/images/posts/{slug}.png"

    except Exception as e:
        logging.error(f"❌ Ошибка генерации изображения: {e}")
        return PLACEHOLDER

# =========================
# Сохранение статьи
# =========================
def save_article(title, text, model, slug, image_path):
    filename = os.path.join(POSTS_DIR, f'{slug}.md')
    front_matter = {
        'title': safe_yaml_value(title),
        'date': datetime.now().strftime("%Y-%m-%dT%H:%M:%S+03:00"),
        'image': image_path if image_path.startswith('/') else f'/{image_path}',
        'model': safe_yaml_value(model),
        'tags': ["AI", "Tech"],
        'draft': False,
        'categories': ["Технологии"]
    }
    yaml_content = yaml.safe_dump(front_matter, allow_unicode=True, default_flow_style=False, sort_keys=False)
    content = f"""---
{yaml_content}---

{text}
"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    logging.info(f"✅ Статья сохранена: {filename}")

# =========================
# Обновление галереи
# =========================
def update_gallery(title, slug, image_path):
    gallery = []
    if os.path.exists(GALLERY_FILE):
        try:
            with open(GALLERY_FILE, 'r', encoding='utf-8') as f:
                gallery = yaml.safe_load(f) or []
        except Exception as e:
            logging.error(f"❌ Ошибка чтения галереи: {e}")
            gallery = []

    gallery.insert(0, {
        "title": safe_yaml_value(title),
        "alt": safe_yaml_value(title),
        "src": image_path if image_path.startswith('/') else f'/{image_path}'
    })
    gallery = gallery[:20]

    try:
        with open(GALLERY_FILE, 'w', encoding='utf-8') as f:
            yaml.safe_dump(gallery, f, allow_unicode=True, default_flow_style=False)
        logging.info(f"✅ Галерея обновлена: {GALLERY_FILE}")
    except Exception as e:
        logging.error(f"❌ Ошибка сохранения галереи: {e}")

# =========================
# Очистка старых статей
# =========================
def cleanup_old_posts(keep=10):
    try:
        posts = sorted(
            glob.glob(os.path.join(POSTS_DIR, "*.md")),
            key=os.path.getmtime,
            reverse=True
        )
        if len(posts) > keep:
            for old in posts[keep:]:
                logging.info(f"🗑 Удаляю старую статью: {old}")
                os.remove(old)
    except Exception as e:
        logging.error(f"❌ Ошибка очистки старых постов: {e}")

# =========================
# Main
# =========================
def main():
    try:
        title, text, model = generate_article()
        slug = slugify(title)
        image_path = generate_image(title, slug)
        save_article(title, text, model, slug, image_path)
        update_gallery(title, slug, image_path)
        cleanup_old_posts(keep=10)
        logging.info("🎉 Генерация статьи завершена успешно!")
    except Exception as e:
        logging.error(f"❌ Критическая ошибка в main: {e}")

if __name__ == "__main__":
    main()
