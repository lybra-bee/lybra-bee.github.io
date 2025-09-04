#!/usr/bin/env python3
import os
import json
import requests
import random
from datetime import datetime, timezone
import shutil
import re
import textwrap
from PIL import Image, ImageDraw, ImageFont
import time
import logging
import argparse
import base64

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class FusionBrainAPI:
    def __init__(self, api_key, secret_key):
        self.URL = 'https://api-key.fusionbrain.ai/'
        self.AUTH_HEADERS = {
            'X-Key': f'Key {api_key}',
            'X-Secret': f'Secret {secret_key}',
        }
    
    def get_model(self):
        """Получаем доступную модель через pipelines endpoint"""
        try:
            response = requests.get(
                self.URL + 'key/api/v1/pipelines',
                headers=self.AUTH_HEADERS,
                timeout=10
            )
            if response.status_code == 200:
                pipelines = response.json()
                if pipelines:
                    # Ищем Kandinsky pipeline
                    for pipeline in pipelines:
                        if "kandinsky" in pipeline.get("name", "").lower():
                            return pipeline['id']
                    # Если не нашли Kandinsky, возвращаем первый доступный
                    return pipelines[0]['id']
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка получения моделей FusionBrain: {e}")
            return None
    
    def generate(self, prompt, width=512, height=512):
        """Генерация изображения через правильный эндпоинт"""
        try:
            # Получаем pipeline ID
            pipeline_id = self.get_model()
            if not pipeline_id:
                logger.error("❌ Не удалось получить pipeline ID")
                return None
            
            params = {
                "type": "GENERATE",
                "numImages": 1,
                "width": width,
                "height": height,
                "generateParams": {
                    "query": prompt
                }
            }
            
            # Правильный формат данных согласно документации
            files = {
                'params': (None, json.dumps(params), 'application/json'),
                'pipeline_id': (None, pipeline_id)
            }
            
            response = requests.post(
                self.URL + 'key/api/v1/pipeline/run',
                headers=self.AUTH_HEADERS,
                files=files,
                timeout=30
            )
            
            # Код 201 - это УСПЕШНЫЙ ответ!
            if response.status_code in [200, 201]:
                data = response.json()
                # Статус INITIAL с UUID - это нормальный ответ при успешном создании задачи
                if data.get('uuid'):
                    logger.info(f"✅ Задача FusionBrain создана: {data['uuid']}")
                    return data['uuid']
                else:
                    logger.warning(f"⚠️ Неожиданный ответ FusionBrain: {data}")
                    return None
            else:
                logger.warning(f"⚠️ Ошибка генерации FusionBrain: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Ошибка генерации FusionBrain: {e}")
            return None
    
    def check_status(self, task_id, attempts=30, delay=6):
        """Проверка статуса генерации"""
        try:
            for attempt in range(attempts):
                if attempt > 0:  # Не спать перед первой проверкой
                    time.sleep(delay)
                    
                logger.info(f"⏳ Проверка статуса FusionBrain (попытка {attempt + 1}/{attempts})")
                
                response = requests.get(
                    self.URL + f'key/api/v1/pipeline/status/{task_id}',
                    headers=self.AUTH_HEADERS,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status')
                    
                    if status == 'DONE':
                        result = data.get('result', {})
                        images = result.get('files', [])
                        if images:
                            logger.info("✅ Генерация FusionBrain завершена успешно!")
                            return images[0]
                        else:
                            logger.warning("⚠️ Нет изображений в ответе")
                            return None
                    elif status == 'FAIL':
                        error_msg = data.get('errorDescription', 'Unknown error')
                        logger.warning(f"⚠️ Генерация FusionBrain не удалась: {error_msg}")
                        return None
                    elif status in ['INITIAL', 'PROCESSING']:
                        if attempt % 5 == 0:  # Логируем каждые 5 попыток
                            logger.info(f"⏳ Статус FusionBrain: {status}")
                        # Продолжаем ждать
                        continue
                    else:
                        logger.warning(f"⚠️ Неизвестный статус FusionBrain: {status}")
                        return None
                else:
                    logger.warning(f"⚠️ Ошибка статуса FusionBrain: {response.status_code}")
            
            logger.warning("⚠️ Превышено количество попыток проверки статуса")
            return None
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки статуса FusionBrain: {e}")
            return None

# ======== Генерация промпта для статьи ========
def generate_article_prompt():
    """Генерируем промпт для статьи на основе трендов"""
    trends = [
        "AI", "машинное обучение", "нейросети", "генеративный AI", 
        "компьютерное зрение", "обработка естественного языка"
    ]
    
    domains = [
        "веб-разработка", "мобильные приложения", "облачные технологии",
        "анализ данных", "кибербезопасность", "медицинские технологии"
    ]
    
    trend = random.choice(trends)
    domain = random.choice(domains)
    
    prompt = f"""Напиши статью на тему "{trend} в {domain}" на русском языке.

Требования:
- Формат: Markdown
- Объем: 300-500 слов
- Структура: заголовок, введение, основной текст, заключение
- Стиль: технический, информативный
- Фокус: практическое применение и тренды 2024-2025 годов"""
    
    return prompt, f"{trend} в {domain}"

# ======== Очистка старых статей ========
def clean_old_articles(keep_last=3):
    """Очистка старых статей"""
    logger.info(f"🧹 Очистка старых статей, оставляем {keep_last} последних...")
    
    content_dir = "content"
    posts_dir = os.path.join(content_dir, "posts")
    
    if os.path.exists(posts_dir):
        posts = [f for f in os.listdir(posts_dir) if f.endswith('.md') and os.path.isfile(os.path.join(posts_dir, f))]
        posts.sort(reverse=True)
        
        for post in posts[keep_last:]:
            post_path = os.path.join(posts_dir, post)
            os.remove(post_path)
            logger.info(f"🗑️ Удален старый пост: {post}")

# ======== Генерация статьи ========
def generate_content():
    logger.info("🚀 Запуск генерации контента...")
    
    # Проверка переменных окружения
    check_environment_variables()
    
    clean_old_articles()
    
    # Генерируем промпт и тему
    prompt, topic = generate_article_prompt()
    logger.info(f"📝 Тема статьи: {topic}")
    
    # Генерируем содержание статьи
    content, model_used = generate_article_content(prompt)
    
    # Извлекаем заголовок из сгенерированного контента
    title = extract_title_from_content(content, topic)
    logger.info(f"📌 Извлеченный заголовок: {title}")
    
    # Генерируем изображение на основе заголовка
    image_filename = generate_article_image(title)
    
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    slug = generate_slug(title)
    filename = f"content/posts/{date}-{slug}.md"
    
    frontmatter = generate_frontmatter(title, content, model_used, image_filename)
    
    # Создаем директории если не существуют
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(frontmatter)
    
    logger.info(f"✅ Статья создана: {filename}")
    
    # Проверяем что файл действительно создан
    if os.path.exists(filename):
        logger.info(f"✅ Файл статьи существует: {os.path.abspath(filename)}")
    else:
        logger.error(f"❌ Файл статьи не создан: {filename}")
    
    return filename

def extract_title_from_content(content, fallback_topic):
    """Извлекаем заголовок из сгенерированного контента"""
    try:
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('# ') and len(line) > 2:
                title = line.replace('# ', '').strip()
                if 5 <= len(title) <= 100:
                    return title
    except:
        pass
    
    return fallback_topic

def check_environment_variables():
    """Проверка переменных окружения"""
    env_vars = {
        'GROQ_API_KEY': os.getenv('GROQ_API_KEY'),
        'FUSIONBRAIN_API_KEY': os.getenv('FUSIONBRAIN_API_KEY'),
        'FUSION_SECRET_KEY': os.getenv('FUSION_SECRET_KEY')
    }
    
    logger.info("🔍 Проверка переменных окружения:")
    for var_name, var_value in env_vars.items():
        status = "✅ установлен" if var_value else "❌ отсутствует"
        logger.info(f"   {var_name}: {status}")

# ======== Генерация текста через Groq ========
def generate_article_content(prompt):
    groq_key = os.getenv('GROQ_API_KEY')
    
    if not groq_key:
        logger.warning("⚠️ Нет доступных API ключей для генерации текста")
        fallback = generate_fallback_content(prompt)
        return fallback, "fallback-generator"

    models_to_try = [
        ("llama-3.1-8b-instant", lambda: generate_with_groq(groq_key, "llama-3.1-8b-instant", prompt)),
        ("llama-3.2-1b-preview", lambda: generate_with_groq(groq_key, "llama-3.2-1b-preview", prompt)),
        ("llama-3.1-70b-versatile", lambda: generate_with_groq(groq_key, "llama-3.1-70b-versatile", prompt))
    ]

    for model_name, generate_func in models_to_try:
        try:
            logger.info(f"🔄 Пробуем генерацию текста: {model_name}")
            result = generate_func()
            if result and len(result.strip()) > 100:
                logger.info(f"✅ Успешно через {model_name}")
                return result, model_name
            else:
                logger.warning(f"⚠️ Пустой ответ от {model_name}")
        except Exception as e:
            logger.error(f"❌ Ошибка {model_name}: {e}")
            continue

    logger.warning("⚠️ Все модели не сработали, используем fallback")
    fallback = generate_fallback_content(prompt)
    return fallback, "fallback-generator"

def generate_fallback_content(prompt):
    """Fallback контент"""
    return f"""# {prompt.split('"')[1] if '"' in prompt else "AI и технологии"}

## Введение
Искусственный интеллект продолжает развиваться быстрыми темпами, предлагая новые возможности для различных отраслей.

## Основные направления
- Автоматизация процессов
- Улучшение пользовательского опыта
- Оптимизация бизнес-процессов

## Заключение
Будущее выглядит многообещающе с развитием AI технологий.

*Статья сгенерирована автоматически*"""

def generate_with_groq(api_key, model_name, prompt):
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model_name, 
            "messages":[{"role":"user","content":prompt}], 
            "max_tokens": 1500,
            "temperature": 0.7
        },
        timeout=30
    )
    
    if resp.status_code == 200:
        data = resp.json()
        return data['choices'][0]['message']['content'].strip()
    else:
        raise Exception(f"Groq API error {resp.status_code}: {resp.text}")

# ======== Генерация изображений ========
def generate_article_image(title):
    """Генерация изображения"""
    logger.info(f"🎨 Генерация изображения для: {title}")
    
    methods = [try_fusionbrain_api, generate_enhanced_placeholder]
    
    for method in methods:
        try:
            logger.info(f"🔄 Пробуем метод: {method.__name__}")
            result = method(title)
            if result:
                logger.info(f"✅ Изображение создано через {method.__name__}")
                return result
        except Exception as e:
            logger.error(f"❌ Ошибка в {method.__name__}: {e}")
            continue
    
    return generate_enhanced_placeholder(title)

def try_fusionbrain_api(title):
    """FusionBrain API"""
    api_key = os.getenv('FUSIONBRAIN_API_KEY')
    secret_key = os.getenv('FUSION_SECRET_KEY')
    
    if not api_key or not secret_key:
        logger.warning("⚠️ FusionBrain ключи не найдены")
        return None
    
    try:
        fb_api = FusionBrainAPI(api_key, secret_key)
        
        english_prompt = f"{title}, digital art, technology, futuristic, professional"
        logger.info(f"🎨 Генерация через FusionBrain: {english_prompt}")
        
        task_id = fb_api.generate(english_prompt, width=512, height=512)
        
        if task_id:
            logger.info(f"✅ Задача создана, task_id: {task_id}")
            
            image_base64 = fb_api.check_status(task_id, attempts=20, delay=5)
            if image_base64:
                logger.info(f"✅ Получено изображение")
                image_data = base64.b64decode(image_base64)
                return save_image_bytes(image_data, title)
        return None
            
    except Exception as e:
        logger.error(f"❌ Ошибка FusionBrain: {e}")
        return None

def save_image_bytes(image_data, title):
    """Сохранение изображения"""
    try:
        os.makedirs("assets/images/posts", exist_ok=True)
        filename = f"assets/images/posts/{generate_slug(title)}.png"
        
        with open(filename, "wb") as f:
            f.write(image_data)
        
        if os.path.exists(filename):
            logger.info(f"💾 Изображение сохранено: {filename}")
            return filename
        return None
            
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения: {e}")
        return None

def generate_enhanced_placeholder(title):
    """Создание placeholder"""
    try:
        os.makedirs("assets/images/posts", exist_ok=True)
        filename = f"assets/images/posts/{generate_slug(title)}.png"
        
        img = Image.new('RGB', (800, 400), color='#1a365d')
        draw = ImageDraw.Draw(img)
        
        # Простой текст
        try:
            font = ImageFont.load_default()
        except:
            font = None
        
        text = f"{title}\nAI Generated"
        draw.text((50, 150), text, fill="white", font=font)
        
        img.save(filename)
        logger.info(f"🎨 Создан placeholder: {filename}")
        return filename
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания placeholder: {e}")
        return None

# ======== Вспомогательные функции ========
def generate_slug(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9а-яё\s]', '', text)
    text = text.replace(' ', '-')
    text = re.sub(r'-+', '-', text)
    return text[:50]

def generate_frontmatter(title, content, model_used, image_url):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    frontmatter = f"""---
title: "{title.replace('"', "'")}"
date: {now}
draft: false
image: "{image_url}"
ai_model: "{model_used}"
tags: ["ai", "технологии"]
categories: ["Искусственный интеллект"]
summary: "Автоматически сгенерированная статья"
---

{content}
"""
    return frontmatter

# ======== Запуск ========
def main():
    parser = argparse.ArgumentParser(description='Генератор AI контента')
    parser.add_argument('--count', type=int, default=1, help='Количество статей')
    args = parser.parse_args()
    
    print("🚀 Запуск генератора контента...")
    
    try:
        for i in range(args.count):
            print(f"\n📄 Генерация статьи {i+1}/{args.count}...")
            filename = generate_content()
            
            if filename and os.path.exists(filename):
                print(f"✅ Статья создана: {filename}")
            else:
                print("❌ Ошибка создания статьи")
                
        print("\n🎉 Генерация завершена!")
        
    except Exception as e:
        print(f"💥 Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
