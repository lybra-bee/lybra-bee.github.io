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

# Логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# API ключи
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# SubNP
SUBNP_URL = "https://subnp.com/api/free/generate"

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
    if not value:
        return ""
    return str(value).replace('"', "'").replace(':', ' -').replace('\n', ' ').replace('\r', ' ').strip()


# === Генерация заголовка и статьи ===
def generate_article():
    header_prompt = "Придумай привлекательный заголовок (≤ 8 слов) о нейросетях и технологиях."

    try:
        logging.info("📝 Генерация заголовка через OpenRouter...")
        r = requests.post("https://openrouter.ai/api/v1/chat/completions",
                          headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
                          json={"model": "gpt-4o-mini",
                                "messages":[{"role":"user","content":header_prompt}]})
        r.raise_for_status()
        title = r.json()["choices"][0]["message"]["content"].strip().strip('"')
        logging.info("✅ Заголовок через OpenRouter")
    except Exception as e:
        logging.warning(f"⚠️ OpenRouter заголовок не сработал: {e}")
        try:
            logging.info("📝 Генерация заголовка через Groq...")
            r = requests.post("https://api.groq.com/v1/chat/completions",
                              headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                              json={"model": "gpt-4o-mini",
                                    "messages":[{"role":"user","content":header_prompt}]})
            r.raise_for_status()
            title = r.json()["choices"][0]["message"]["content"].strip().strip('"')
            logging.info("✅ Заголовок через Groq")
        except Exception as e:
            logging.error(f"❌ Ошибка генерации заголовка: {e}")
            title = "Новые тренды в ИИ"

    content_prompt = f"Напиши статью 400-600 слов по заголовку: {title}"
    try:
        logging.info("📝 Генерация статьи через OpenRouter...")
        r = requests.post("https://openrouter.ai/api/v1/chat/completions",
                          headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
                          json={"model": "gpt-4o-mini",
                                "messages":[{"role":"user","content":content_prompt}]})
        r.raise_for_status()
        text = r.json()["choices"][0]["message"]["content"].strip()
        logging.info("✅ Статья через OpenRouter")
        return title, text, "OpenRouter GPT"
    except Exception as e:
        logging.warning(f"⚠️ OpenRouter статья не сработала: {e}")
        try:
            logging.info("📝 Генерация статьи через Groq...")
            r = requests.post("https://api.groq.com/v1/chat/completions",
                              headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                              json={"model": "gpt-4o-mini",
                                    "messages":[{"role":"user","content":content_prompt}]})
            r.raise_for_status()
            text = r.json()["choices"][0]["message"]["content"].strip()
            logging.info("✅ Статья через Groq")
            return title, text, "Groq GPT"
        except Exception as e:
            logging.error(f"❌ Ошибка генерации статьи: {e}")
            return title, "Статья временно недоступна.", "None"


# === Генерация изображения ===
def generate_image(title, slug):
    try:
        logging.info("[SubNP] Запрос на генерацию...")
        r = requests.post(SUBNP_URL,
                          headers={"Content-Type": "application/json"},
                          json={"prompt": title, "model": "turbo"},
                          stream=True)
        r.raise_for_status()

        image_url = None
        for line in r.iter_lines():
            if not line:
                continue
            if line.startswith(b"data: "):
                try:
                    data = json.loads(line[len(b"data: "):].decode("utf-8"))
                    if data.get("status") == "complete" and "imageUrl" in data:
                        image_url = data["imageUrl"]
                        break
                except Exception:
                    continue

        if not image_url:
            logging.error("[SubNP] Не получили complete -> imageUrl")
            return PLACEHOLDER

        img = requests.get(image_url)
        img.raise_for_status()
        img_path = os.path.join(STATIC_DIR, f"{slug}.png")
        with open(img_path, "wb") as f:
            f.write(img.content)
        logging.info(f"✅ Изображение сохранено: {img_path}")
        return f"/images/posts/{slug}.png"

    except Exception as e:
        logging.error(f"❌ Ошибка генерации через SubNP: {e}")
        return PLACEHOLDER


# === Сохранение статьи ===
def save_article(title, text, model, slug, image_path):
    filename = os.path.join(POSTS_DIR, f'{slug}.md')
    front_matter = {
        'title': safe_yaml_value(title),
        'date': datetime.now().strftime("%Y-%m-%dT%H:%M:%S+03:00"),
        'image': image_path,
        'model': safe_yaml_value(model),
        'tags': ["AI", "Tech"],
        'draft': False,
        'categories': ["Технологии"]
    }
    yaml_content = yaml.safe_dump(front_matter, allow_unicode=True, sort_keys=False)
    content = f"---\n{yaml_content}---\n\n{text}\n"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    logging.info(f"✅ Статья сохранена: {filename}")


# === Обновление галереи ===
def update_gallery(title, slug, image_path):
    gallery = []
    if os.path.exists(GALLERY_FILE):
        with open(GALLERY_FILE, 'r', encoding='utf-8') as f:
            gallery = yaml.safe_load(f) or []
    gallery.insert(0, {"title": safe_yaml_value(title), "alt": safe_yaml_value(title), "src": image_path})
    gallery = gallery[:20]
    with open(GALLERY_FILE, 'w', encoding='utf-8') as f:
        yaml.safe_dump(gallery, f, allow_unicode=True, sort_keys=False)
    logging.info(f"✅ Галерея обновлена: {GALLERY_FILE}")


# === Очистка старых постов ===
def cleanup_old_posts(keep=10):
    posts = sorted(glob.glob(os.path.join(POSTS_DIR, "*.md")), key=os.path.getmtime, reverse=True)
    if len(posts) > keep:
        for old in posts[keep:]:
            logging.info(f"🗑 Удаляю старую статью: {old}")
            os.remove(old)


def main():
    try:
        title, text, model = generate_article()
        slug = slugify(title)
        image_path = generate_image(title, slug)
        save_article(title, text, model, slug, image_path)
        update_gallery(title, slug, image_path)
        cleanup_old_posts(keep=10)
        logging.info("🎉 Генерация завершена успешно!")
    except Exception as e:
        logging.error(f"❌ Критическая ошибка: {e}")


if __name__ == "__main__":
    main()
