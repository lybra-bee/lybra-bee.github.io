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

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
CLOUDFLARE_API_KEY = os.environ.get("CLOUDFLARE_API_KEY")

POSTS_DIR = 'content/posts'
STATIC_DIR = 'static/images/posts'
GALLERY_FILE = 'data/gallery.yaml'
PLACEHOLDER = 'static/images/placeholder.jpg'

os.makedirs(POSTS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(os.path.dirname(PLACEHOLDER), exist_ok=True)
os.makedirs(os.path.dirname(GALLERY_FILE), exist_ok=True)

def safe_yaml_value(value):
    if not value: return ""
    return str(value).replace('"', "'").replace(':', ' -').replace('\n', ' ').replace('\r', ' ').strip()

def generate_with_cloudflare(prompt):
    """Генерация через Cloudflare AI"""
    try:
        if not CLOUDFLARE_API_KEY:
            return None
            
        logging.info("☁️ Пробуем Cloudflare AI...")
        headers = {
            "Authorization": f"Bearer {CLOUDFLARE_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": [
                {"role": "system", "content": "You are a helpful assistant that creates content in Russian."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1000
        }
        
        response = requests.post(
            "https://api.cloudflare.com/client/v4/accounts/.../ai/run/@cf/meta/llama-2-7b-chat-int8",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get('result', {}).get('response')
            
    except Exception as e:
        logging.warning(f"⚠️ Cloudflare AI не сработал: {e}")
    
    return None

def generate_article():
    header_prompt = "Придумай интересный заголовок о последних трендах в искусственном интеллекте и технологиях (не более 7 слов)"
    
    try:
        logging.info("📝 Генерация заголовка...")
        
        # Пробуем Cloudflare first
        title = generate_with_cloudflare(header_prompt)
        if title:
            logging.info("✅ Заголовок от Cloudflare AI")
        else:
            # Fallback to OpenRouter
            headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
            r = requests.post("https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json={"model": "gpt-4o-mini", "messages":[{"role":"user","content":header_prompt}]})
            r.raise_for_status()
            title = r.json()["choices"][0]["message"]["content"].strip().strip('"')
            logging.info("✅ Заголовок от OpenRouter")
        
        # Генерация текста
        content_prompt = f"Напиши подробную статью на русском языке 500-600 слов по заголовку: {title}"
        
        logging.info("📝 Генерация статьи...")
        text = generate_with_cloudflare(content_prompt)
        if text:
            logging.info("✅ Статья от Cloudflare AI")
            return title, text, "Cloudflare AI"
        else:
            # Fallback
            r = requests.post("https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json={"model": "gpt-4o-mini", "messages":[{"role":"user","content":content_prompt}]})
            r.raise_for_status()
            text = r.json()["choices"][0]["message"]["content"].strip()
            logging.info("✅ Статья от OpenRouter")
            return title, text, "OpenRouter GPT"
            
    except Exception as e:
        logging.error(f"❌ Ошибка генерации: {e}")
        return "Новые тренды в искусственном интеллекте 2024", 
               "Искусственный интеллект продолжает revolutionizing различные отрасли. Вот основные тренды...", 
               "Fallback"

def generate_image(title, slug):
    try:
        logging.info("🖼️ Создание изображения...")
        img_path = os.path.join(STATIC_DIR, f"{slug}.svg")
        
        # Создаем SVG с градиентом
        svg_content = f'''<svg width="1200" height="630" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#667eea"/>
                    <stop offset="100%" stop-color="#764ba2"/>
                </linearGradient>
            </defs>
            <rect width="100%" height="100%" fill="url(#grad)"/>
            <text x="600" y="300" font-family="Arial" font-size="48" fill="white" text-anchor="middle" font-weight="bold">
                {title}
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

def update_gallery(title, slug, image_path):
    """Обновляет галерею"""
    try:
        gallery = []
        if os.path.exists(GALLERY_FILE):
            try:
                with open(GALLERY_FILE, 'r', encoding='utf-8') as f:
                    gallery = yaml.safe_load(f) or []
            except:
                gallery = []

        # Правильный путь для изображения
        image_src = image_path if image_path.startswith('/') else f"/{image_path}"

        gallery.insert(0, {
            "title": safe_yaml_value(title), 
            "alt": safe_yaml_value(title), 
            "src": image_src,
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
    """Сохраняет статью с правильным frontmatter"""
    try:
        filename = os.path.join(POSTS_DIR, f'{slug}.md')
        
        # Убедимся, что путь к изображению правильный
        image_url = image_path if image_path.startswith('/') else f"/{image_path}"
        
        front_matter = {
            'title': safe_yaml_value(title),
            'date': datetime.now().strftime("%Y-%m-%dT%H:%M:%S+03:00"),
            'image': image_url,
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
        
    except Exception as e:
        logging.error(f"❌ Ошибка сохранения статьи: {e}")

def cleanup_old_posts(keep=5):
    """Очистка старых постов"""
    try:
        posts = sorted(glob.glob(os.path.join(POSTS_DIR, "*.md")), key=os.path.getmtime, reverse=True)
        
        if len(posts) > keep:
            for old_post in posts[keep:]:
                slug = os.path.splitext(os.path.basename(old_post))[0]
                
                # Удаляем статью
                os.remove(old_post)
                logging.info(f"🗑 Удалена старая статья: {old_post}")
                
                # Удаляем изображения
                for ext in ['.png', '.svg', '.jpg']:
                    img_path = os.path.join(STATIC_DIR, f"{slug}{ext}")
                    if os.path.exists(img_path):
                        os.remove(img_path)
                        logging.info(f"🗑 Удалено старое изображение: {img_path}")
                        
    except Exception as e:
        logging.error(f"❌ Ошибка очистки: {e}")

def main():
    try:
        logging.info("🚀 Запуск генерации контента...")
        
        # Генерируем статью
        title, text, model = generate_article()
        slug = slugify(title)
        logging.info(f"📄 Сгенерирована статья: {title}")
        
        # Генерируем изображение
        image_path = generate_image(title, slug)
        logging.info(f"🖼️ Сгенерировано изображение: {image_path}")
        
        # Сохраняем статью
        save_article(title, text, model, slug, image_path)
        
        # Обновляем галерею
        update_gallery(title, slug, image_path)
        
        # Очищаем старые посты
        cleanup_old_posts(keep=5)
        
        logging.info("🎉 Генерация завершена успешно!")
        
    except Exception as e:
        logging.error(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    main()
