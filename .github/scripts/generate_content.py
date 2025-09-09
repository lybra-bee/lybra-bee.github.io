#!/usr/bin/env python3
import os
import requests
import logging
from datetime import datetime
from slugify import slugify
import yaml

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Папки и файлы
POSTS_DIR = 'content/posts'
STATIC_DIR = 'static/images/posts'
GALLERY_FILE = 'data/gallery.yaml'
PLACEHOLDER = 'static/images/placeholder.jpg'

os.makedirs(POSTS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(os.path.dirname(GALLERY_FILE), exist_ok=True)

# ----------------------------
# Настройка Cloudflare AI
# ----------------------------
API_BASE_URL = "https://api.cloudflare.com/client/v4/accounts/3799ba295e1ecd90aeb9c3d6e8173edb/ai/run/"
HEADERS = {"Authorization": "Bearer YOUR_TOKEN_HERE"}  # сюда потом секрет

def generate_cf_image(prompt, filename):
    """Генерация изображения через Cloudflare AI"""
    try:
        logging.info("🌐 Генерация изображения через Cloudflare AI...")
        inputs = [
            { "role": "system", "content": "You are an AI that generates high-quality illustrative images" },
            { "role": "user", "content": prompt }
        ]
        response = requests.post(f"{API_BASE_URL}@cf/images/generate", headers=HEADERS, json={"messages": inputs})
        response.raise_for_status()
        result = response.json()

        # Предполагаем, что Cloudflare возвращает base64 изображения
        img_base64 = result["result"]["files"][0]["data"]  # адаптировать под реальный ответ
        import base64
        img_data = base64.b64decode(img_base64)

        path = os.path.join(STATIC_DIR, filename)
        with open(path, "wb") as f:
            f.write(img_data)

        logging.info(f"✅ Изображение сохранено: {path}")
        return f"/images/posts/{filename}"

    except Exception as e:
        logging.error(f"❌ Ошибка при генерации изображения: {e}")
        return PLACEHOLDER

# ----------------------------
# Генерация статьи
# ----------------------------
def generate_article():
    """Пример заголовка и текста"""
    title = f"Новые тренды AI в {datetime.now().year}"
    text = (
        f"Искусственный интеллект активно развивается. В {datetime.now().year} появляются новые возможности "
        "для генерации изображений, текста и музыки. Эта статья рассказывает о последних трендах."
    )
    return title, text

# ----------------------------
# Обновление галереи
# ----------------------------
def update_gallery(title, filename):
    try:
        gallery = []
        if os.path.exists(GALLERY_FILE):
            with open(GALLERY_FILE, "r", encoding="utf-8") as f:
                gallery = yaml.safe_load(f) or []

        gallery.insert(0, {
            "title": title,
            "alt": title,
            "src": f"/images/posts/{filename}",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "tags": ["AI", "Tech"]
        })

        gallery = gallery[:20]

        with open(GALLERY_FILE, "w", encoding="utf-8") as f:
            yaml.safe_dump(gallery, f, allow_unicode=True)

        logging.info(f"✅ Галерея обновлена: {len(gallery)} изображений")
    except Exception as e:
        logging.error(f"❌ Ошибка обновления галереи: {e}")

# ----------------------------
# Сохранение статьи
# ----------------------------
def save_article(title, text, filename, image_path):
    front_matter = {
        'title': title,
        'date': datetime.now().strftime("%Y-%m-%dT%H:%M:%S+03:00"),
        'image': image_path,
        'draft': False,
        'tags': ["AI", "Tech"],
        'categories': ["Технологии"],
        'author': "AI Generator",
        'type': "posts",
        'description': text[:150] + "..." if len(text) > 150 else text
    }
    filepath = os.path.join(POSTS_DIR, filename.replace(".svg", ".md"))
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("---\n")
        yaml.safe_dump(front_matter, f, allow_unicode=True)
        f.write("---\n\n")
        f.write(text)
    logging.info(f"✅ Статья сохранена: {filepath}")

# ----------------------------
# Main
# ----------------------------
def main():
    title, text = generate_article()
    slug = slugify(title)
    image_filename = f"{slug}.png"

    image_path = generate_cf_image(title, image_filename)
    save_article(title, text, image_filename, image_path)
    update_gallery(title, image_filename)
    logging.info("🎉 Генерация завершена!")

if __name__ == "__main__":
    main()
