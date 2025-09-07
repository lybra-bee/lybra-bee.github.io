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

# API ключи из environment variables
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
FUSIONBRAIN_API_KEY = os.environ.get("FUSIONBRAIN_API_KEY")
FUSION_SECRET_KEY = os.environ.get("FUSION_SECRET_KEY")

# Папки (соответствуют вашей структуре Hugo)
POSTS_DIR = 'content/posts'
STATIC_DIR = 'assets/images/posts'  # Изменено на assets для Hugo
GALLERY_FILE = 'data/gallery.yaml'
PLACEHOLDER = 'assets/images/placeholder.jpg'  # Изменено на assets

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

def generate_image_with_fusionbrain(title, slug):
    """Генерация изображения через FusionBrain API"""
    try:
        if not FUSIONBRAIN_API_KEY or not FUSION_SECRET_KEY:
            logging.warning("❌ Ключи FusionBrain не настроены")
            return None
            
        logging.info("🎨 Генерация изображения через FusionBrain...")
        
        # 1. Получаем ID модели
        models_url = "https://api.fusionbrain.ai/web/api/v1/models"
        models_response = requests.get(models_url)
        models_data = models_response.json()
        
        if not models_data or 'id' not in models_data[0]:
            logging.warning("❌ Не удалось получить модели FusionBrain")
            return None
            
        model_id = models_data[0]['id']
        
        # 2. Генерируем изображение
        generate_url = f"https://api.fusionbrain.ai/web/api/v1/text2image/run?model_id={model_id}"
        
        headers = {
            "X-Key": f"Key {FUSIONBRAIN_API_KEY}",
            "X-Secret": f"Secret {FUSION_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "type": "GENERATE",
            "style": "UHD",
            "width": 1024,
            "height": 1024,
            "num_images": 1,
            "generateParams": {
                "query": f"digital art, high quality, {title}"
            }
        }
        
        response = requests.post(generate_url, headers=headers, json=payload)
        response.raise_for_status()
        
        generate_data = response.json()
        uuid = generate_data.get('uuid')
        
        if not uuid:
            logging.warning("❌ Не получили UUID для генерации")
            return None
        
        # 3. Ждем завершения генерации
        max_attempts = 30
        for attempt in range(max_attempts):
            time.sleep(2)
            
            check_url = f"https://api.fusionbrain.ai/web/api/v1/text2image/status/{uuid}"
            status_response = requests.get(check_url, headers=headers)
            status_data = status_response.json()
            
            if status_data.get('status') == 'DONE':
                images = status_data.get('images', [])
                if images:
                    # Декодируем base64 изображение
                    image_data = base64.b64decode(images[0])
                    img_path = os.path.join(STATIC_DIR, f"{slug}.png")
                    
                    with open(img_path, 'wb') as f:
                        f.write(image_data)
                    
                    logging.info(f"✅ Изображение FusionBrain сохранено: {img_path}")
                    return f"/images/posts/{slug}.png"
            
            elif status_data.get('status') == 'FAIL':
                logging.warning("❌ Ошибка генерации FusionBrain")
                break
                
        logging.warning("❌ Таймаут генерации FusionBrain")
        return None
        
    except Exception as e:
        logging.error(f"❌ Ошибка FusionBrain: {e}")
        return None

def generate_simple_image(title, slug):
    """Создает простое текстовое изображение"""
    try:
        logging.info("🖼️ Создание простого текстового изображения...")
        
        # Создаем SVG изображение с текстом
        img_path = os.path.join(STATIC_DIR, f"{slug}.svg")
        safe_title = title.replace('"', '&quot;').replace('&', '&amp;')
        
        svg_content = f'''<svg width="1024" height="1024" xmlns="http://www.w3.org/2000/svg">
            <rect width="100%" height="100%" fill="#2D2D3C"/>
            <text x="512" y="512" font-family="Arial, sans-serif" font-size="40" fill="white" 
                  text-anchor="middle" dominant-baseline="middle">
                {safe_title}
            </text>
            <text x="20" y="1004" font-family="Arial, sans-serif" font-size="20" fill="#C8C8C8">
                Generated by AI
            </text>
        </svg>'''
        
        with open(img_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)
        
        logging.info(f"✅ SVG изображение создано: {img_path}")
        return f"/images/posts/{slug}.svg"
        
    except Exception as e:
        logging.error(f"❌ Ошибка создания SVG изображения: {e}")
        return None

def generate_image(title, slug):
    """Основная функция генерации изображения"""
    # Пробуем FusionBrain сначала
    image_path = generate_image_with_fusionbrain(title, slug)
    if image_path:
        return image_path
    
    # Fallback: простое SVG изображение
    image_path = generate_simple_image(title, slug)
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
