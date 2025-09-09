#!/usr/bin/env python3
import os
import yaml
import glob
import logging
from datetime import datetime
from slugify import slugify

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
    return str(value).replace('"', "'").replace(':', ' -').replace('\n', ' ').strip()

def generate_article():
    """Генерация заголовка и текста статьи (заглушка)"""
    try:
        # Заголовок с текущим годом
        current_year = datetime.now().year
        title = f"Искусственный интеллект {current_year}: Тренды, меняющие мир"
        logging.info(f"📄 Сгенерирована статья: {title}")
        
        text = f"""Искусственный интеллект продолжает стремительно развиваться. В {current_year} году ключевые направления:

1. Генеративный AI — новые модели для творчества
2. Мультимодальные системы — текст, изображение, аудио
3. Этический AI — безопасность и ответственность

Эти технологии изменяют бизнес и повседневную жизнь человека."""
        
        return title, text, "AI Generator"

    except Exception as e:
        logging.error(f"❌ Ошибка генерации статьи: {e}")
        return "Искусственный интеллект", "Текст временно недоступен", "Fallback"

def generate_image(title, slug):
    """Создание SVG-заглушки"""
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
        logging.info(f"🖼️ SVG-заглушка создана: {img_path}")
        return f"/images/posts/{slug}.svg"
    except Exception as e:
        logging.error(f"❌ Ошибка создания изображения: {e}")
        return PLACEHOLDER

def update_gallery():
    """Собираем все изображения из static/images/posts/ для галереи"""
    try:
        images = sorted(glob.glob(os.path.join(STATIC_DIR, '*.*')), key=os.path.getmtime, reverse=True)
        gallery = []
        for img_path in images:
            filename = os.path.basename(img_path)
            title = os.path.splitext(filename)[0]
            gallery.append({
                "title": title,
                "alt": title,
                "src": f"/images/posts/{filename}",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "tags": ["AI", "Tech"]
            })
        # Ограничим до 20 изображений
        gallery = gallery[:20]
        with open(GALLERY_FILE, 'w', encoding='utf-8') as f:
            yaml.safe_dump(gallery, f, allow_unicode=True, default_flow_style=False)
        logging.info(f"✅ Галерея обновлена: {len(gallery)} изображений")
    except Exception as e:
        logging.error(f"❌ Ошибка обновления галереи: {e}")

def save_article(title, text, model, slug, image_path):
    """Сохраняем статью с frontmatter"""
    try:
        filename = os.path.join(POSTS_DIR, f'{slug}.md')
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
    """Удаляем старые статьи, изображения оставляем для галереи"""
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
        image_path = generate_image(title, slug)
        save_article(title, text, model, slug, image_path)
        cleanup_old_posts(keep=5)
        update_gallery()
        logging.info("🎉 Генерация завершена успешно!")
    except Exception as e:
        logging.error(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    main()
