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
SUBNP_BASE_URL = "https://subnp.com"

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

def download_and_save_image(image_url, slug):
    """Скачивание и сохранение изображения"""
    try:
        # Проверяем, не является ли URL уже локальным путем
        if image_url.startswith('/'):
            return image_url
            
        img_data = requests.get(image_url, timeout=30).content
        img_path = os.path.join(STATIC_DIR, f"{slug}.png")
        
        with open(img_path, 'wb') as f:
            f.write(img_data)
        
        logging.info(f"✅ Изображение сохранено: {img_path}")
        return f"/images/posts/{slug}.png"
        
    except Exception as e:
        logging.error(f"❌ Ошибка сохранения изображения {image_url}: {e}")
        return PLACEHOLDER

def try_fallback_generation(title, slug):
    """Fallback методы генерации изображений"""
    logging.info("🔄 Пробуем альтернативные методы генерации...")
    
    # 1. Попробуем старый эндпоинт на всякий случай
    try:
        logging.info("[SubNP Fallback] Пробуем старый эндпоинт /api/free/generate...")
        response = requests.post("https://subnp.com/api/free/generate",
                               headers={"Content-Type": "application/json"},
                               json={"prompt": title, "model": "turbo"},
                               timeout=60)
        
        if response.status_code == 200:
            # Пробуем обработать как SSE поток
            for line in response.text.split('\n'):
                if line.startswith('data: '):
                    try:
                        data = json.loads(line[6:])
                        if data.get('imageUrl'):
                            return download_and_save_image(data['imageUrl'], slug)
                    except:
                        continue
    except:
        pass
    
    # 2. Генерация простого изображения с текстом
    try:
        logging.info("[Fallback] Создание простого изображения с текстом...")
        from PIL import Image, ImageDraw, ImageFont
        import textwrap
        
        # Создаем изображение
        img = Image.new('RGB', (1024, 1024), color=(45, 45, 60))
        d = ImageDraw.Draw(img)
        
        # Пробуем разные шрифты
        font_size = 40
        try:
            # Попробуем стандартные шрифты
            try:
                font = ImageFont.truetype("Arial.ttf", font_size)
            except:
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
                except:
                    font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
        
        # Форматируем текст
        wrapped_text = textwrap.fill(title, width=30)
        bbox = d.textbbox((0, 0), wrapped_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Центрируем текст
        x = (1024 - text_width) / 2
        y = (1024 - text_height) / 2
        
        d.text((x, y), wrapped_text, fill=(255, 255, 255), font=font)
        
        # Добавляем watermark
        d.text((20, 980), "Generated by AI", fill=(200, 200, 200, 128), font=ImageFont.load_default())
        
        # Сохраняем
        img_path = os.path.join(STATIC_DIR, f"{slug}.png")
        img.save(img_path)
        
        logging.info(f"✅ Fallback изображение создано: {img_path}")
        return f"/images/posts/{slug}.png"
        
    except Exception as e:
        logging.error(f"❌ Ошибка создания fallback изображения: {e}")
    
    # 3. Возвращаем стандартную заглушку
    return PLACEHOLDER

def generate_image(title, slug):
    """
    Генерация изображения через SubNP API согласно документации
    https://subnp.com/ru/free-api
    """
    try:
        logging.info("[SubNP] Запрос на генерацию изображения...")
        
        # Согласно документации, правильный эндпоинт и параметры
        url = "https://subnp.com/api/v1/image/generation"
        
        # Формируем промпт согласно рекомендациям SubNP
        # Добавляем контекст для лучшего качества изображения
        enhanced_prompt = f"digital art, high quality, article illustration, {title}"
        
        payload = {
            "prompt": enhanced_prompt,
            "model": "flux",  # Согласно документации, доступные модели: flux, turbo, magic
            "width": 1024,
            "height": 1024,
            "steps": 20,
            "guidance_scale": 7.5,
            "negative_prompt": "blurry, low quality, text, watermark, signature"
        }
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        logging.info(f"[SubNP] Отправка запроса с промптом: {enhanced_prompt}")
        
        response = requests.post(url, 
                               headers=headers, 
                               json=payload,
                               timeout=120)
        
        logging.info(f"[SubNP] Статус ответа: {response.status_code}")
        
        if response.status_code != 200:
            logging.warning(f"⚠️ SubNP вернул статус {response.status_code}")
            return try_fallback_generation(title, slug)
        
        # Парсим ответ согласно документации SubNP
        data = response.json()
        
        # Проверяем различные возможные форматы ответа
        if data.get('status') == 'success' and data.get('data'):
            image_url = data['data'].get('url')
            if image_url:
                logging.info(f"[SubNP] Изображение сгенерировано: {image_url}")
                return download_and_save_image(image_url, slug)
        
        # Альтернативный формат ответа
        if data.get('imageUrl'):
            logging.info(f"[SubNP] Изображение сгенерировано: {data['imageUrl']}")
            return download_and_save_image(data['imageUrl'], slug)
        
        # Еще один возможный формат
        if data.get('url'):
            logging.info(f"[SubNP] Изображение сгенерировано: {data['url']}")
            return download_and_save_image(data['url'], slug)
        
        # Если ни один формат не подошел, логируем ответ для отладки
        logging.warning(f"⚠️ Неожиданный формат ответа SubNP: {json.dumps(data, ensure_ascii=False)[:200]}...")
        return try_fallback_generation(title, slug)
        
    except requests.exceptions.Timeout:
        logging.error("❌ Таймаут при генерации изображения")
        return try_fallback_generation(title, slug)
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Ошибка сети при генерации изображения: {e}")
        return try_fallback_generation(title, slug)
    except Exception as e:
        logging.error(f"❌ Неожиданная ошибка при генерации изображения: {e}")
        return try_fallback_generation(title, slug)

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
