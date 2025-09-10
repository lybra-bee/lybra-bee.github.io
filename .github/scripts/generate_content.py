#!/usr/bin/env python3
import os
import shutil
import logging
from datetime import datetime
from slugify import slugify
import requests
import yaml

# --- Настройки ---
POSTS_DIR = "content/posts"
STATIC_IMG_DIR = "static/images/posts"
ASSETS_GALLERY_DIR = "assets/gallery"
GALLERY_FILE = "data/gallery.yaml"

# --- Логирование ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# --- Проверка директорий ---
os.makedirs(POSTS_DIR, exist_ok=True)
os.makedirs(STATIC_IMG_DIR, exist_ok=True)
os.makedirs(ASSETS_GALLERY_DIR, exist_ok=True)

# --- Функции ---

def generate_article_title():
    """Генерация заголовка через OpenRouter/GROQ (реальная генерация)"""
    prompt = ("Проанализируй современные кейсы применения искусственного интеллекта "
              "и высоких технологий и предложи интересный, уникальный заголовок статьи, "
              "например про применение AI в медицине, строительстве, новых технологиях, "
              "или пошаговый урок с нейросетью. Не ограничивайся словом 'тренды'.")
    # Здесь нужно реальное API
    response = requests.post(
        "https://api.openrouter.ai/v1/chat/completions",
        headers={"Authorization": f"Bearer {os.environ.get('OPENROUTER_API_KEY')}"},
        json={
            "model": "gpt-4.1-mini",
            "messages": [{"role": "user", "content": prompt}]
        }
    )
    data = response.json()
    title = data["choices"][0]["message"]["content"].strip()
    return title

def generate_article_text(title):
    """Генерация текста статьи через API"""
    prompt = f"Напиши подробную статью по заголовку: {title}"
    response = requests.post(
        "https://api.openrouter.ai/v1/chat/completions",
        headers={"Authorization": f"Bearer {os.environ.get('OPENROUTER_API_KEY')}"},
        json={
            "model": "gpt-4.1-mini",
            "messages": [{"role": "user", "content": prompt}]
        }
    )
    data = response.json()
    text = data["choices"][0]["message"]["content"].strip()
    return text

def generate_image(title):
    """Генерация изображения к статье (можно заменить на любой генератор)"""
    # В данном примере просто создаем заглушку
    filename = slugify(title) + ".png"
    static_path = os.path.join(STATIC_IMG_DIR, filename)
    with open(static_path, "wb") as f:
        f.write(requests.get("https://via.placeholder.com/800x400.png?text=" + title.replace(" ","+")).content)
    logging.info(f"Изображение сгенерировано: {static_path}")
    # Копируем в assets/gallery
    shutil.copy(static_path, os.path.join(ASSETS_GALLERY_DIR, filename))
    return filename

def save_article(title, text, img_filename):
    """Сохраняем статью в content/posts"""
    slug = slugify(title)
    post_file = os.path.join(POSTS_DIR, f"{slug}.md")
    front_matter = (
        f"---\n"
        f'title: "{title}"\n'
        f'date: "{datetime.now().strftime("%Y-%m-%d")}"\n'
        f'image: "/images/posts/{img_filename}"\n'
        f'tags: ["ai","tech"]\n'
        f"---\n\n"
        f"{text}\n"
    )
    with open(post_file, "w", encoding="utf-8") as f:
        f.write(front_matter)
    logging.info(f"Статья сохранена: {post_file}")

def update_gallery():
    """Обновление data/gallery.yaml из assets/gallery"""
    files = os.listdir(ASSETS_GALLERY_DIR)
    gallery_items = []
    for f in files:
        if f.lower().endswith((".png",".jpg",".jpeg",".svg")):
            gallery_items.append({
                "src": f"/assets/gallery/{f}",
                "alt": os.path.splitext(f)[0],
                "date": datetime.now().strftime("%Y-%m-%d")
            })
    with open(GALLERY_FILE, "w", encoding="utf-8") as f:
        yaml.dump(gallery_items, f, allow_unicode=True)
    logging.info(f"Галерея обновлена: {len(gallery_items)} элементов")

# --- Основной процесс ---
if __name__ == "__main__":
    logging.info("🚀 Запуск генерации статьи...")
    title = generate_article_title()
    text = generate_article_text(title)
    img_filename = generate_image(title)
    save_article(title, text, img_filename)
    update_gallery()
    logging.info("✅ Генерация завершена")
