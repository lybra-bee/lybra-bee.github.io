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
FUSION_API_KEY = os.environ.get("FUSIONBRAIN_API_KEY")
FUSION_SECRET_KEY = os.environ.get("FUSION_SECRET_KEY")
BASE_URL = 'https://api-key.fusionbrain.ai/'

AUTH_HEADERS = {
    'X-Key': f'Key {FUSION_API_KEY}',
    'X-Secret': f'Secret {FUSION_SECRET_KEY}',
}

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
    """Безопасное экранирование значений для YAML"""
    if not value:
        return ""
    # Экранируем кавычки и убираем переносы строк
    value = str(value).replace('"', "'").replace('\n', ' ').replace('\r', ' ')
    # Убираем лишние пробелы
    value = ' '.join(value.split())
    return value.strip()

def generate_article():
    header_prompt = "Проанализируй последние тренды в нейросетях и высоких технологиях и на их основе придумай привлекательный заголовок, не более восьми слов, для статьи"
    
    try:
        logging.info("📝 Генерация заголовка через OpenRouter...")
        headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
        r = requests.post("https://openrouter.ai/api/v1/chat/completions",
                          headers=headers,
                          json={"model": "gpt-4o-mini", "messages":[{"role":"user","content":header_prompt}]})
        r.raise_for_status()
        title = r.json()["choices"][0]["message"]["content"].strip().strip('"')
        logging.info(f"✅ Заголовок получен: {title}")
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
            logging.info(f"✅ Заголовок получен: {title}")
        except Exception as e:
            logging.error(f"❌ Ошибка генерации заголовка: {e}")
            title = "Статья о последних трендах в ИИ"

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

def get_pipeline_id():
    try:
        r = requests.get(BASE_URL + 'key/api/v1/pipelines', headers=AUTH_HEADERS)
        r.raise_for_status()
        return r.json()[0]['id']
    except Exception as e:
        logging.error(f"❌ Ошибка получения pipeline ID: {e}")
        return None

def generate_image(title, slug):
    try:
        pipeline_id = get_pipeline_id()
        if not pipeline_id:
            logging.warning("❌ Не удалось получить pipeline ID")
            return PLACEHOLDER

        params = {
            "type": "GENERATE",
            "numImages": 1,
            "width": 1024,
            "height": 1024,
            "generateParams": {"query": title}
        }
        files = {
            'pipeline_id': (None, pipeline_id),
            'params': (None, json.dumps(params), 'application/json')
        }
        r = requests.post(BASE_URL + 'key/api/v1/pipeline/run', headers=AUTH_HEADERS, files=files)
        r.raise_for_status()
        uuid = r.json()['uuid']

        for _ in range(20):
            r_status = requests.get(BASE_URL + f'key/api/v1/pipeline/status/{uuid}', headers=AUTH_HEADERS)
            r_status.raise_for_status()
            data = r_status.json()
            if data['status'] == 'DONE':
                image_base64 = data['result']['files'][0]
                break
            time.sleep(3)
        else:
            logging.warning("❌ Изображение не сгенерировано за отведённое время")
            return PLACEHOLDER

        img_bytes = base64.b64decode(image_base64)
        img_path = os.path.join(STATIC_DIR, f'{slug}.png')
        with open(img_path, 'wb') as f:
            f.write(img_bytes)

        logging.info(f"✅ Изображение сохранено: {img_path}")
        return f"/images/posts/{slug}.png"
    except Exception as e:
        logging.error(f"❌ Ошибка генерации изображения: {e}")
        return PLACEHOLDER

def save_article(title, text, model, slug, image_path):
    filename = os.path.join(POSTS_DIR, f'{slug}.md')
    
    # Убедимся, что image_path правильный
    if image_path == PLACEHOLDER:
        image_path = "/images/placeholder.jpg"
    elif not image_path.startswith('/'):
        image_path = f'/{image_path}'
    
    # Создаем простой и надежный YAML front matter
    front_matter = {
        'title': safe_yaml_value(title),
        'date': datetime.now().isoformat(),
        'image': image_path,
        'model': safe_yaml_value(model),
        'tags': ['AI', 'Tech'],
        'draft': 'false',
        'categories': ['Технологии']
    }
    
    # Генерируем YAML вручную для полного контроля
    yaml_lines = ['---']
    for key, value in front_matter.items():
        if isinstance(value, list):
            # Исправлено: убрал обратный слеш из f-строки
            items = ', '.join([f'"{v}"' for v in value])
            yaml_lines.append(f'{key}: [{items}]')
        else:
            yaml_lines.append(f'{key}: "{value}"')
    yaml_lines.append('---')
    
    yaml_content = '\n'.join(yaml_lines)
    content = f"{yaml_content}\n\n{text}"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Проверяем содержимое файла
    with open(filename, 'r', encoding='utf-8') as f:
        content_check = f.read()
        logging.info(f"📄 Содержимое файла (первые 200 символов): {content_check[:200]}")
    
    logging.info(f"✅ Статья сохранена: {filename}")
    return True

def update_gallery(title, slug, image_path):
    gallery = []
    if os.path.exists(GALLERY_FILE):
        try:
            with open(GALLERY_FILE, 'r', encoding='utf-8') as f:
                gallery = yaml.safe_load(f) or []
        except Exception as e:
            logging.error(f"❌ Ошибка чтения галереи: {e}")
            gallery = []

    # Убедимся, что image_path правильный
    if image_path == PLACEHOLDER:
        image_path = "/images/placeholder.jpg"
    elif not image_path.startswith('/'):
        image_path = f'/{image_path}'

    gallery.insert(0, {
        "title": safe_yaml_value(title), 
        "alt": safe_yaml_value(title), 
        "src": image_path
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
        logging.info(f"📝 Слаг: {slug}")
        
        image_path = generate_image(title, slug)
        logging.info(f"🖼 Путь к изображению: {image_path}")
        
        # Сохраняем статью
        save_article(title, text, model, slug, image_path)
        update_gallery(title, slug, image_path)
        cleanup_old_posts(keep=10)
        logging.info("🎉 Генерация статьи завершена успешно!")
            
    except Exception as e:
        logging.error(f"❌ Критическая ошибка в main: {e}")

if __name__ == "__main__":
    main()
