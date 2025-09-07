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

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# API ключи
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Папки
POSTS_DIR = 'content/posts'
STATIC_DIR = 'static/images/posts'
GALLERY_FILE = 'data/gallery.yaml'
PLACEHOLDER = 'static/images/placeholder.jpg'

os.makedirs(POSTS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(os.path.dirname(PLACEHOLDER), exist_ok=True)
os.makedirs(os.path.dirname(GALLERY_FILE), exist_ok=True)

def safe_yaml_value(value):
    """Безопасное экранирование значений для YAML"""
    if not value:
        return ""
    value = str(value).replace('"', "'").replace(':', ' -').replace('\n', ' ').replace('\r', ' ')
    return value.strip()

# -------------------- Генерация статьи --------------------
def generate_article():
    header_prompt = "Проанализируй последние тренды в нейросетях и высоких технологиях и придумай привлекательный заголовок, не более восьми слов"
    
    try:
        logging.info("📝 Генерация заголовка через OpenRouter...")
        headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
        r = requests.post("https://openrouter.ai/api/v1/chat/completions",
                          headers=headers,
                          json={"model": "gpt-4o-mini", "messages":[{"role":"user","content":header_prompt}]})
        r.raise_for_status()
        title = r.json()["choices"][0]["message"]["content"].strip().strip('"')
        logging.info("✅ Заголовок получен через OpenRouter")
    except Exception as e:
        logging.warning(f"⚠️ OpenRouter заголовок не сработал: {e}")
        try:
            logging.info("📝 Генерация заголовка через Groq...")
            headers_groq = {"Authorization": f"Bearer {GROQ_API_KEY}"}
            r = requests.post("https://api.groq.com/v1/chat/completions",
                              headers=headers_groq,
                              json={"model": "gpt-4o-mini", "messages":[{"role":"user","content":header_prompt}]})
            r.raise_for_status()
            title = r.json()["choices"][0]["message"]["content"].strip().strip('"')
            logging.info("✅ Заголовок получен через Groq")
        except Exception as e:
            logging.error(f"❌ Ошибка генерации заголовка: {e}")
            title = "Статья о последних трендах в ИИ"

    content_prompt = f"Напиши статью 400-600 слов по заголовку: {title}"
    try:
        logging.info("📝 Генерация статьи через OpenRouter...")
        headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
        r = requests.post("https://openrouter.ai/api/v1/chat/completions",
                          headers=headers,
                          json={"model": "gpt-4o-mini", "messages":[{"role":"user","content":content_prompt}]})
        r.raise_for_status()
        text = r.json()["choices"][0]["message"]["content"].strip()
        logging.info("✅ Статья получена через OpenRouter")
        return title, text, "OpenRouter GPT"
    except Exception as e:
        logging.warning(f"⚠️ OpenRouter статья не сработала: {e}")
        try:
            logging.info("📝 Генерация статьи через Groq...")
            headers_groq = {"Authorization": f"Bearer {GROQ_API_KEY}"}
            r = requests.post("https://api.groq.com/v1/chat/completions",
                              headers=headers_groq,
                              json={"model": "gpt-4o-mini", "messages":[{"role":"user","content":content_prompt}]})
            r.raise_for_status()
            text = r.json()["choices"][0]["message"]["content"].strip()
            logging.info("✅ Статья получена через Groq")
            return title, text, "Groq GPT"
        except Exception as e:
            logging.error(f"❌ Ошибка генерации статьи: {e}")
            return title, "Статья временно недоступна.", "None"

# -------------------- Генерация изображения (перебор API) --------------------
def generate_image(title, slug):
    apis = [
        {"name": "Pollinations", "url": f"https://api.pollinations.ai/prompt/{title}", "method": "GET"},
        {"name": "DeepAI", "url": "https://api.deepai.org/api/text2img", "method": "POST",
         "headers": {"api-key": ""}, "data": lambda t: {"text": t}},
        {"name": "Clipdrop", "url": "https://clipdrop-api.co/text-to-image/v1", "method": "POST",
         "headers": {"x-api-key": ""}, "files": lambda t: {"prompt": t}},
        # Можно добавить новые API сюда
    ]

    for api in apis:
        try:
            logging.info(f"🖼 [Image] Пробуем API: {api['name']}")
            if api['method'] == "GET":
                r = requests.get(api['url'])
            else:
                r = requests.post(api['url'], headers=api.get("headers", {}), data=api.get("data", lambda t: {})(title), files=api.get("files", None) and api["files"](title))
            r.raise_for_status()

            if api['name'] == "Pollinations":
                with open(os.path.join(STATIC_DIR, f'{slug}.png'), 'wb') as f:
                    f.write(r.content)
                logging.info(f"✅ Изображение сохранено через {api['name']}")
                return f"/images/posts/{slug}.png"
            else:
                # Для API с JSON-ответом
                resp_json = r.json()
                # Попробуем получить URL изображения
                image_url = resp_json.get("output_url") or resp_json.get("imageUrl")
                if image_url:
                    img_data = requests.get(image_url).content
                    img_path = os.path.join(STATIC_DIR, f'{slug}.png')
                    with open(img_path, 'wb') as f:
                        f.write(img_data)
                    logging.info(f"✅ Изображение сохранено через {api['name']}")
                    return f"/images/posts/{slug}.png"
        except Exception as e:
            logging.warning(f"⚠️ {api['name']} не сработал: {e}")

    logging.warning("❌ Все API не сработали, используем PLACEHOLDER")
    return PLACEHOLDER

# -------------------- Сохранение статьи --------------------
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

# -------------------- Обновление галереи --------------------
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

# -------------------- Очистка старых статей --------------------
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

# -------------------- Главная функция --------------------
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
