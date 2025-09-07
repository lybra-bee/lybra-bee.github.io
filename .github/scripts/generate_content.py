#!/usr/bin/env python3
import os
import json
import requests
import time
import base64
import logging
import glob
import re
from datetime import datetime
from slugify import slugify
import yaml

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# API ключи из environment variables
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Папки (соответствуют вашей структуре Hugo)
POSTS_DIR = 'content/posts'
STATIC_DIR = 'assets/images/posts'
GALLERY_FILE = 'data/gallery.yaml'
PLACEHOLDER = 'assets/images/placeholder.jpg'

os.makedirs(POSTS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(os.path.dirname(PLACEHOLDER), exist_ok=True)
os.makedirs(os.path.dirname(GALLERY_FILE), exist_ok=True)

def safe_yaml_value(value):
    if not value:
        return ""
    value = str(value).replace('"', "'").replace(':', ' -').replace('\n', ' ').replace('\r', ' ')
    return value.strip()

def generate_article():
    header_prompt = "Проанализируй последние тренды в нейросетях и высоких технологиях и придумай привлекательный заголовок, не более восьми слов"
    
    # Генерация заголовка
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

    # Генерация текста
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

def generate_image_with_free_api(title, slug):
    """Бесплатные API для генерации изображений"""
    
    # 1. Попробуем Hugging Face API
    try:
        logging.info("🎨 Пробуем Hugging Face API...")
        
        api_url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1"
        
        payload = {
            "inputs": f"digital art, high quality, professional, {title}",
        }
        
        response = requests.post(api_url, json=payload, timeout=120)
        
        if response.status_code == 200:
            img_path = os.path.join(STATIC_DIR, f"{slug}.png")
            with open(img_path, 'wb') as f:
                f.write(response.content)
            logging.info(f"✅ Изображение Hugging Face сохранено: {img_path}")
            return f"/images/posts/{slug}.png"
            
    except Exception as e:
        logging.warning(f"⚠️ Hugging Face не сработал: {e}")
    
    # 2. Попробуем другой публичный API
    try:
        logging.info("🎨 Пробуем публичный AI API...")
        
        api_url = "https://api.vyro.ai/v1/imagine/api/generations"
        
        payload = {
            "prompt": f"digital art, high quality, {title}",
            "style": "realistic",
            "ratio": "1:1"
        }
        
        response = requests.post(api_url, json=payload, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('image_url'):
                img_data = requests.get(data['image_url'], timeout=30).content
                img_path = os.path.join(STATIC_DIR, f"{slug}.png")
                
                with open(img_path, 'wb') as f:
                    f.write(img_data)
                
                logging.info(f"✅ Изображение публичного API сохранено: {img_path}")
                return f"/images/posts/{slug}.png"
                
    except Exception as e:
        logging.warning(f"⚠️ Публичный API не сработал: {e}")
    
    return None

def generate_ai_image(title, slug):
    """Генерация изображения с помощью AI"""
    try:
        logging.info("🎨 Генерация AI изображения...")
        
        # Пробуем бесплатные API
        image_path = generate_image_with_free_api(title, slug)
        if image_path:
            return image_path
            
        # Если API не сработали, создаем качественное SVG
        return generate_quality_svg_image(title, slug)
        
    except Exception as e:
        logging.error(f"❌ Ошибка генерации AI изображения: {e}")
        return generate_quality_svg_image(title, slug)

def generate_quality_svg_image(title, slug):
    """Создает качественное SVG изображение"""
    try:
        logging.info("🖼️ Создание качественного SVG изображения...")
        
        img_path = os.path.join(STATIC_DIR, f"{slug}.svg")
        safe_title = title.replace('"', '&quot;').replace('&', '&amp;')
        
        # Разбиваем текст на строки
        words = safe_title.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            if len(test_line) <= 25:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Создаем красивое SVG с градиентом
        svg_content = f'''<svg width="1200" height="630" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630">
            <defs>
                <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#667eea" />
                    <stop offset="100%" stop-color="#764ba2" />
                </linearGradient>
                <filter id="shadow" x="-50%" y="-50%" width="200%" height="200%">
                    <feGaussianBlur in="SourceAlpha" stdDeviation="20" result="blur"/>
                    <feOffset in="blur" dx="10" dy="10" result="offsetBlur"/>
                    <feFlood flood-color="#000000" flood-opacity="0.5" result="offsetColor"/>
                    <feComposite in="offsetColor" in2="offsetBlur" operator="in" result="offsetBlur"/>
                    <feBlend in="SourceGraphic" in2="offsetBlur" mode="normal"/>
                </filter>
            </defs>
            
            <rect width="1200" height="630" fill="url(#gradient)" />
            
            <!-- Декоративные элементы -->
            <circle cx="100" cy="100" r="50" fill="white" opacity="0.1" />
            <circle cx="1100" cy="500" r="80" fill="white" opacity="0.1" />
            <circle cx="300" cy="400" r="40" fill="white" opacity="0.1" />
            
            <!-- Основной текст -->
            <g font-family="Arial, sans-serif" fill="white" text-anchor="middle">
                {"".join(f'<text x="600" y="{250 + i*60}" font-size="36" font-weight="bold" filter="url(#shadow)">{line}</text>' 
                         for i, line in enumerate(lines))}
            </g>
            
            <!-- Подпись -->
            <text x="600" y="580" font-family="Arial, sans-serif" font-size="20" fill="white" opacity="0.8" text-anchor="middle">
                AI Generated Content • {datetime.now().strftime("%d.%m.%Y")}
            </text>
            
            <!-- Иконка AI -->
            <g transform="translate(50, 550)" font-family="Arial, sans-serif" font-size="16" fill="white">
                <rect x="0" y="0" width="30" height="30" rx="5" fill="white" opacity="0.2" />
                <text x="15" y="20" text-anchor="middle" font-weight="bold">AI</text>
            </g>
        </svg>'''
        
        with open(img_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)
        
        logging.info(f"✅ Качественное SVG изображение создано: {img_path}")
        return f"/images/posts/{slug}.svg"
        
    except Exception as e:
        logging.error(f"❌ Ошибка создания SVG изображения: {e}")
        return PLACEHOLDER

def generate_image(title, slug):
    """Основная функция генерации изображения"""
    # Пробуем AI генерацию
    image_path = generate_ai_image(title, slug)
    if image_path:
        return image_path
    
    # Если все не сработало - заглушка
    logging.warning("❌ Все методы генерации изображений не сработали")
    return PLACEHOLDER

def save_article(title, text, model, slug, image_path):
    filename = os.path.join(POSTS_DIR, f'{slug}.md')
    
    # Front matter для Hugo
    front_matter = {
        'title': safe_yaml_value(title),
        'date': datetime.now().strftime("%Y-%m-%dT%H:%M:%S+03:00"),
        'image': image_path,
        'draft': False,
        'tags': ["AI", "Tech", "Нейросети"],
        'categories': ["Технологии"],
        'author': "AI Generator",
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
        "src": image_path,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "tags": ["AI", "Tech"]
    })
    
    # Ограничиваем галерею 20 последними изображениями
    gallery = gallery[:20]

    try:
        with open(GALLERY_FILE, 'w', encoding='utf-8') as f:
            yaml.safe_dump(gallery, f, allow_unicode=True, default_flow_style=False)
        logging.info(f"✅ Галерея обновлена: {GALLERY_FILE}")
    except Exception as e:
        logging.error(f"❌ Ошибка сохранения галереи: {e}")

def cleanup_old_posts(keep=10):
    try:
        posts = sorted(
            glob.glob(os.path.join(POSTS_DIR, "*.md")),
            key=os.path.getmtime,
            reverse=True
        )
        if len(posts) > keep:
            for old in posts[keep:]:
                # Также удаляем соответствующие изображения
                slug = os.path.splitext(os.path.basename(old))[0]
                image_path = os.path.join(STATIC_DIR, f"{slug}.png")
                image_svg_path = os.path.join(STATIC_DIR, f"{slug}.svg")
                
                logging.info(f"🗑 Удаляю старую статью: {old}")
                os.remove(old)
                
                # Удаляем изображения если существуют
                for img_path in [image_path, image_svg_path]:
                    if os.path.exists(img_path):
                        os.remove(img_path)
                        logging.info(f"🗑 Удаляю старое изображение: {img_path}")
                        
    except Exception as e:
        logging.error(f"❌ Ошибка очистки старых постов: {e}")

def main():
    try:
        logging.info("🚀 Запуск генерации статьи...")
        title, text, model = generate_article()
        slug = slugify(title)
        logging.info(f"📄 Сгенерирована статья: {title}")
        
        image_path = generate_image(title, slug)
        logging.info(f"🖼️ Сгенерировано изображение: {image_path}")
        
        save_article(title, text, model, slug, image_path)
        update_gallery(title, slug, image_path)
        cleanup_old_posts(keep=10)
        
        logging.info("🎉 Генерация завершена успешно!")
        
    except Exception as e:
        logging.error(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    main()
