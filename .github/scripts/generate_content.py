#!/usr/bin/env python3
import os
import glob
import logging
from datetime import datetime
from slugify import slugify
import yaml

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

POSTS_DIR = 'content/posts'
STATIC_DIR = 'static/images/posts'
GALLERY_FILE = 'data/gallery.yaml'
PLACEHOLDER = 'static/images/placeholder.jpg'

os.makedirs(POSTS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(os.path.dirname(GALLERY_FILE), exist_ok=True)

def safe_yaml_value(value):
    if not value: return ""
    return str(value).replace('"', "'").replace(':', ' -').replace('\n', ' ').replace('\r', ' ').strip()

def generate_article():
    """Генерация заголовка и текста (стабильная версия)"""
    title = f"Искусственный интеллект {datetime.now().year}: Тренды, меняющие мир"
    text = f"""Искусственный интеллект продолжает революционизировать различные отрасли. В {datetime.now().year} году мы наблюдаем несколько ключевых трендов:

1. Генеративный AI - модели типа GPT стали доступны широкой публике.
2. Мультимодальность - AI работает с текстом, изображениями и аудио одновременно.
3. Этический AI - повышенное внимание к безопасности и этике.

Эти технологии меняют нашу повседневную жизнь и бизнес-процессы."""
    return title, text, "AI Generator"

def generate_image(title, slug):
    """Создание SVG-заглушки для статьи"""
    try:
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
        logging.info(f"✅ Изображение создано: {img_path}")
        return f"/images/posts/{slug}.svg"
    except Exception as e:
        logging.error(f"❌ Ошибка создания изображения: {e}")
        return PLACEHOLDER

def update_gallery():
    """Обновляет галерею по всем изображениям в STATIC_DIR"""
    try:
        gallery = []
        files = sorted(glob.glob(os.path.join(STATIC_DIR, "*.*")), key=os.path.getmtime, reverse=True)
        for f in files:
            name = os.path.splitext(os.path.basename(f))[0]
            gallery.append({
                "title": name,
                "alt": name,
                "src": f"/images/posts/{os.path.basename(f)}",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "tags": ["AI", "Tech"]
            })
        # Ограничиваем 20 элементами
        gallery = gallery[:20]

        with open(GALLERY_FILE, 'w', encoding='utf-8') as f:
            yaml.safe_dump(gallery, f, allow_unicode=True, default_flow_style=False)
        logging.info(f"✅ Галерея обновлена: {len(gallery)} изображений")
    except Exception as e:
        logging.error(f"❌ Ошибка обновления галереи: {e}")

def save_article(title, text, model, slug, image_path):
    """Сохраняет статью с frontmatter"""
    try:
        filename = os.path.join(POSTS_DIR, f'{slug}.md')
        front_matter = {
            'title': safe_yaml_value(title),
            'date': datetime.now().strftime("%Y-%m-%dT%H:%M:%S+03:00"),
            'image': image_path,
            'draft': False,
            'tags': ["AI", "Tech", "Нейросети"],
            'categories': ["Технологии"],
            'author': model,
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
    """Очистка старых статей, изображения оставляем"""
    try:
        posts = sorted(glob.glob(os.path.join(POSTS_DIR, "*.md")), key=os.path.getmtime, reverse=True)
        if len(posts) > keep:
            for old_post in posts[keep:]:
                os.remove(old_post)
                logging.info(f"🗑 Удалена старая статья: {old_post}")
    except Exception as e:
        logging.error(f"❌ Ошибка очистки: {e}")

def main():
    try:
        logging.info("🚀 Запуск генерации контента...")

        title, text, model = generate_article()
        slug = slugify(title)
        logging.info(f"📄 Сгенерирована статья: {title}")

        image_path = generate_image(title, slug)
        logging.info(f"🖼️ Сгенерировано изображение: {image_path}")

        save_article(title, text, model, slug, image_path)

        update_gallery()

        cleanup_old_posts(keep=5)

        logging.info("🎉 Генерация завершена успешно!")
    except Exception as e:
        logging.error(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    main()
