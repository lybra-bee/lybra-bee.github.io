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
SUBNP_BASE_URL = "https://t2i.mcpcore.xyz"  # новый базовый URL

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

def get_available_models():
    """Получить список доступных моделей для генерации изображений"""
    try:
        logging.info("🔄 Получение списка доступных моделей...")
        response = requests.get(f"{SUBNP_BASE_URL}/api/free/models", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('success') and 'models' in data:
            models = [model['model'] for model in data['models']]
            logging.info(f"✅ Доступные модели: {', '.join(models)}")
            return models
        else:
            logging.warning("⚠️ Не удалось получить список моделей")
            return ['turbo']  # fallback модель
            
    except Exception as e:
        logging.warning(f"⚠️ Ошибка получения моделей: {e}")
        return ['turbo']  # fallback модель

def get_api_stats():
    """Получить статистику использования API"""
    try:
        logging.info("📊 Проверка статистики API...")
        response = requests.get(f"{SUBNP_BASE_URL}/api/free/stats", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        logging.info(f"📈 Статистика API: {data.get('totalRequests', 0)} запросов, "
                    f"успешность: {data.get('successRate', 0)}%, "
                    f"последний час: {data.get('lastHourRequests', 0)}")
        
        # Проверяем, не перегружен ли API
        last_hour_requests = data.get('lastHourRequests', 0)
        if last_hour_requests > 100:  # Если больше 100 запросов в час
            logging.warning("⚠️ API может быть перегружен")
            return False
        return True
        
    except Exception as e:
        logging.warning(f"⚠️ Ошибка получения статистики API: {e}")
        return True  # Продолжаем работу даже если статистика недоступна

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

def generate_image(title, slug):
    try:
        # Проверяем доступность API
        if not get_api_stats():
            logging.warning("⚠️ API может быть перегружен, используем заглушку")
            return PLACEHOLDER
        
        # Получаем доступные модели
        available_models = get_available_models()
        selected_model = available_models[0] if available_models else 'turbo'
        
        logging.info(f"[SubNP] Запрос на генерацию изображения с моделью '{selected_model}'...")
        payload = {"prompt": title, "model": selected_model}
        
        # Отправляем запрос с потоковой передачей
        response = requests.post(f"{SUBNP_BASE_URL}/api/free/generate", 
                               headers={"Content-Type": "application/json"}, 
                               json=payload, 
                               stream=True,
                               timeout=120)
        response.raise_for_status()
        
        image_url = None
        # Обрабатываем потоковые данные
        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith('data: '):
                try:
                    data = json.loads(line[6:])  # Убираем 'data: ' и парсим JSON
                    
                    if data.get('status') == 'processing':
                        progress = data.get('message', '')
                        if progress:
                            logging.info(f"[SubNP] Прогресс: {progress}")
                    
                    elif data.get('status') == 'complete' and data.get('imageUrl'):
                        image_url = data['imageUrl']
                        logging.info(f"[SubNP] Генерация завершена: {image_url}")
                        break
                    
                    elif data.get('status') == 'error':
                        error_msg = data.get('message', 'Неизвестная ошибка')
                        logging.error(f"[SubNP] Ошибка: {error_msg}")
                        break
                        
                except json.JSONDecodeError as e:
                    logging.warning(f"[SubNP] Ошибка парсинга JSON: {e}, строка: {line}")
                    continue
                except Exception as e:
                    logging.warning(f"[SubNP] Ошибка обработки данных: {e}")
                    continue

        if not image_url:
            logging.warning("❌ SubNP не вернул imageUrl, используем PLACEHOLDER")
            return PLACEHOLDER

        # Скачиваем изображение
        img_data = requests.get(image_url).content
        img_path = os.path.join(STATIC_DIR, f"{slug}.png")
        with open(img_path, 'wb') as f:
            f.write(img_data)
        logging.info(f"✅ Изображение сохранено: {img_path}")
        return f"/images/posts/{slug}.png"

    except requests.exceptions.Timeout:
        logging.error("❌ Таймаут при генерации изображения")
        return PLACEHOLDER
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Ошибка сети при генерации изображения: {e}")
        return PLACEHOLDER
    except Exception as e:
        logging.error(f"❌ Неожиданная ошибка при генерации изображения: {e}")
        return PLACEHOLDER

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
