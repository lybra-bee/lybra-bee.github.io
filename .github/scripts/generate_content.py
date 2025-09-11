#!/usr/bin/env python3
import os
import json
import requests
import time
import logging
import glob
from datetime import datetime
from slugify import slugify
import yaml

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Ключи API ---
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# --- Пути ---
POSTS_DIR = 'content/posts'
STATIC_DIR = 'static/images/posts'
GALLERY_FILE = 'data/gallery.yaml'
PLACEHOLDER = 'static/images/placeholder.jpg'

os.makedirs(POSTS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(os.path.dirname(PLACEHOLDER), exist_ok=True)
os.makedirs(os.path.dirname(GALLERY_FILE), exist_ok=True)

# --- Утилиты ---
def safe_yaml_value(value):
    if not value: return ""
    return str(value).replace('"', "'").replace(':', ' -').replace('\n', ' ').replace('\r', ' ').strip()

# --- Генераторы ---
def generate_with_groq(prompt):
    """Попытка генерации через Groq API"""
    if not GROQ_API_KEY:
        logging.warning("⚠️ Groq API ключ не найден.")
        return None
    try:
        logging.info("🌐 Используем Groq...")
        # Пример запроса к Groq (замени на реальный API)
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
        r = requests.post("https://api.groq.ai/generate",
            headers=headers,
            json={"prompt": prompt, "max_tokens": 1000},
            timeout=30
        )
        r.raise_for_status()
        result = r.json().get("text", "").strip()
        logging.info("✅ Groq успешно сгенерировал текст.")
        return result if result else None
    except Exception as e:
        logging.warning(f"⚠️ Groq не сработал: {e}")
        return None

def generate_with_openrouter(prompt):
    """Попытка генерации через OpenRouter"""
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
                "messages":[{"role":"user","content":prompt}],
                "max_tokens": 1000
            },
            timeout=30
        )
        r.raise_for_status()
        result = r.json()["choices"][0]["message"]["content"].strip()
        logging.info("✅ OpenRouter успешно сгенерировал текст.")
        return result if result else None
    except Exception as e:
        logging.warning(f"⚠️ OpenRouter не сработал: {e}")
        return None

# --- Генерация статьи ---
def generate_article():
    # Промпт для заголовка (тот, который ты велел запомнить)
    header_prompt = ("Придумай интересный и цепляющий заголовок о последних трендах в "
                     "искусственном интеллекте и технологиях. Он должен быть не более 7 слов, "
                     "интригующим, современным, понятным широкой аудитории, "
                     "с акцентом на практическое применение технологий и их влияние на жизнь людей.")

    logging.info("📝 Генерация заголовка...")
    title = generate_with_groq(header_prompt)
    if not title:
        logging.info("🔄 Пытаемся через OpenRouter для заголовка...")
        title = generate_with_openrouter(header_prompt)
    if not title:
        logging.warning("⚠️ Не удалось получить заголовок от API — fallback")
        title = "Новые тренды в искусственном интеллекте 2025"
    logging.info(f"✅ Заголовок: {title}")

    # Промпт для текста статьи
    content_prompt = f"""
Напиши подробную, информативную и интересную статью на русском языке длиной 500-600 слов по заголовку: {title}.
Статья должна включать:
- Четкое введение, объясняющее суть темы
- Основную часть с минимум 3-4 логическими абзацами
- Заключение с выводами и перспективами
- Поддержку примерами и ссылками на реальные технологии и тренды
- Акцент на практическое применение и влияние на общество
- Текст должен быть уникальным, читабельным и легким для восприятия
Не используй списки меньше 2 пунктов, избегай сухой технической терминологии без пояснений.
"""

    logging.info("📝 Генерация текста статьи...")
    text = generate_with_groq(content_prompt)
    if not text:
        logging.info("🔄 Пытаемся через OpenRouter для текста статьи...")
        text = generate_with_openrouter(content_prompt)
    if not text:
        logging.warning("⚠️ Все генераторы не сработали — fallback")
        text = (f"Искусственный интеллект продолжает революционизировать различные отрасли. "
                "В 2025 году наблюдаются ключевые тренды: генеративный AI, мультимодальность, "
                "этический AI. Эти технологии меняют повседневную жизнь и бизнес-процессы.")
    return title, text, "AI Generator"

# --- Изображение ---
def generate_image(title, slug):
    try:
        logging.info("🖼️ Создание SVG-заглушки для изображения...")
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

# --- Галерея ---
def update_gallery(title, slug, image_path):
    try:
        gallery = []
        if os.path.exists(GALLERY_FILE):
            try:
                with open(GALLERY_FILE, 'r', encoding='utf-8') as f:
                    gallery = yaml.safe_load(f) or []
            except Exception as e:
                logging.warning(f"⚠️ Ошибка чтения галереи, создаем новую: {e}")
                gallery = []

        image_src = image_path if image_path.startswith('/') else f"/{image_path}"
        gallery.append({
            "title": safe_yaml_value(title),
            "alt": safe_yaml_value(title),
            "src": image_src,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "tags": ["AI", "Tech"]
        })

        with open(GALLERY_FILE, 'w', encoding='utf-8') as f:
            yaml.safe_dump(gallery, f, allow_unicode=True, default_flow_style=False)

        logging.info(f"✅ Галерея обновлена (всего {len(gallery)} изображений)")
    except Exception as e:
        logging.error(f"❌ Ошибка обновления галереи: {e}")

# --- Сохранение статьи ---
def save_article(title, text, model, slug, image_path):
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
        content = f"---\n{yaml_content}---\n\n{text}\n"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        logging.info(f"✅ Статья сохранена: {filename}")
    except Exception as e:
        logging.error(f"❌ Ошибка сохранения статьи: {e}")

# --- Очистка старых постов ---
def cleanup_old_posts(keep=10):
    try:
        posts = sorted(glob.glob(os.path.join(POSTS_DIR, "*.md")), key=os.path.getmtime, reverse=True)
        if len(posts) > keep:
            for old_post in posts[keep:]:
                slug = os.path.splitext(os.path.basename(old_post))[0]
                os.remove(old_post)
                logging.info(f"🗑 Удалён старый пост: {old_post}")
                for ext in ['.png', '.svg', '.jpg']:
                    img_path = os.path.join(STATIC_DIR, f"{slug}{ext}")
                    if os.path.exists(img_path):
                        os.remove(img_path)
                        logging.info(f"🗑 Удалено старое изображение: {img_path}")
    except Exception as e:
        logging.error(f"❌ Ошибка очистки: {e}")

# --- Основной запуск ---
def main():
    try:
        logging.info("🚀 Запуск генерации контента...")

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
