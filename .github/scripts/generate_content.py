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

# ======== Генерация промпта для статьи ========
def generate_article_prompt():
    """Генерируем промпт для статьи на основе трендов"""
    trends = [
        "мультимодальный искусственный интеллект",
        "автономные AI агенты", 
        "квантовые вычисления и машинное обучение",
        "нейроморфные вычисления",
        "генеративный искусственный интеллект",
        "периферийный искусственный интеллект (Edge AI)",
        "искусственный интеллект для кибербезопасности",
        "этичный искусственный интеллект",
        "искусственный интеллект в здравоохранении",
        "автономные транспортные системы",
        "оптимизация AI моделей",
        "доверенный искусственный интеллект", 
        "искусственный интеллект для экологии",
        "персональные AI ассистенты",
        "искусственный интеллект в образовании"
    ]
    
    domains = [
        "веб разработка и cloud native приложения",
        "мобильные приложения и IoT экосистемы",
        "облачные сервисы и распределенные системы",
        "анализ больших данных и бизнес аналитика",
        "компьютерная безопасность и киберзащита",
        "медицинская диагностика и биотехнологии",
        "финансовые технологии и финтех",
        "автономные транспортные системы",
        "умные города и инфраструктура",
        "образовательные технологии и EdTech"
    ]
    
    trend = random.choice(trends)
    domain = random.choice(domains)
    
    prompt = f"""Проанализируй последние тренды в области искусственного интеллекта и высоких технологий и напиши развернутую статью на тему: "{trend} в {domain} в 2025 году".

Требования к статье:
- Формат: Markdown
- Объем: 400-600 слов
- Структура: заголовок, введение, основные разделы, заключение
- Стиль: профессиональный, информативный
- Контент: конкретные примеры, кейсы использования, практические применения
- Фокус: инновации, тенденции 2025 года, перспективы развития

Статья должна быть полезной для технических специалистов, разработчиков и IT-менеджеров."""
    
    return prompt, f"{trend} в {domain} в 2025 году"

# ======== Очистка старых статей ========
def clean_old_articles(keep_last=3):
    logger.info(f"🧹 Очистка старых статей, оставляем {keep_last} последних...")
    content_dir = "content"
    if os.path.exists(content_dir):
        posts_dir = os.path.join(content_dir, "posts")
        if os.path.exists(posts_dir):
            posts = sorted([f for f in os.listdir(posts_dir) if f.endswith('.md')], 
                          reverse=True)
            for post in posts[keep_last:]:
                os.remove(os.path.join(posts_dir, post))
                logger.info(f"🗑️ Удален старый пост: {post}")
    else:
        os.makedirs("content/posts", exist_ok=True)
        with open("content/_index.md", "w", encoding="utf-8") as f:
            f.write("---\ntitle: \"Главная\"\n---")
        with open("content/posts/_index.md", "w", encoding="utf-8") as f:
            f.write("---\ntitle: \"Статьи\"\n---")
        logger.info("✅ Создана структура content")

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
    
    os.makedirs("content/posts", exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(frontmatter)
    
    logger.info(f"✅ Статья создана: {filename}")
    return filename

def extract_title_from_content(content, fallback_topic):
    """Извлекаем заголовок из сгенерированного контента"""
    try:
        # Ищем первый заголовок Markdown (начинается с #)
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('# ') and len(line) > 2:
                # Убираем Markdown синтаксис
                title = line.replace('# ', '').strip()
                if 10 <= len(title) <= 100:  # Проверяем reasonable длину
                    return title
    except:
        pass
    
    # Если не нашли заголовок, используем fallback
    return fallback_topic

def check_environment_variables():
    """Проверка всех необходимых переменных окружения"""
    env_vars = {
        'OPENROUTER_API_KEY': os.getenv('OPENROUTER_API_KEY'),
        'GROQ_API_KEY': os.getenv('GROQ_API_KEY'),
        'HF_API_TOKEN': os.getenv('HF_API_TOKEN'),
        'REPLICATE_API_TOKEN': os.getenv('REPLICATE_API_TOKEN')
    }
    
    logger.info("🔍 Проверка переменных окружения:")
    for var_name, var_value in env_vars.items():
        status = "✅ установлен" if var_value else "❌ отсутствует"
        logger.info(f"   {var_name}: {status}")

# ======== Генерация текста через OpenRouter/Groq ========
def generate_article_content(prompt):
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    groq_key = os.getenv('GROQ_API_KEY')
    models_to_try = []

    if groq_key:
        groq_models = ["llama-3.1-8b-instant", "llama-3.2-1b-preview", "llama-3.1-70b-versatile"]
        for model_name in groq_models:
            models_to_try.append((f"Groq-{model_name}", lambda m=model_name: generate_with_groq(groq_key, m, prompt)))
    if openrouter_key:
        openrouter_models = ["anthropic/claude-3-haiku", "anthropic/claude-3-sonnet", "google/gemini-pro-1.5"]
        for model_name in openrouter_models:
            models_to_try.append((model_name, lambda m=model_name: generate_with_openrouter(openrouter_key, m, prompt)))

    # Если нет API ключей, используем fallback
    if not models_to_try:
        logger.warning("⚠️ Нет доступных API ключей для генерации текста")
        fallback = generate_fallback_content(prompt)
        return fallback, "fallback-generator"

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
    """Fallback контент если все API не работают"""
    sections = [
        "# Тенденции искусственного интеллекта в 2025 году",
        "",
        "## Введение",
        "Искусственный интеллект продолжает трансформировать различные отрасли и сферы деятельности. В 2025 году мы ожидаем значительные advancements в области AI технологий.",
        "",
        "## Основные тенденции",
        "- Автоматизация сложных процессов",
        "- Интеграция AI в повседневные workflow",
        "- Улучшение качества и скорости обработки данных",
        "- Развитие мультимодальных моделей",
        "",
        "## Практическое применение",
        "Компании внедряют AI решения для оптимизации бизнес-процессов и создания инновационных продуктов.",
        "",
        "## Заключение",
        "Будущее выглядит многообещающе с развитием искусственного интеллекта и машинного обучения.",
        "",
        "*Статья сгенерирована автоматически*"
    ]
    return "\n".join(sections)

def generate_with_groq(api_key, model_name, prompt):
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model_name, 
            "messages":[{"role":"user","content":prompt}], 
            "max_tokens": 2000,
            "temperature": 0.7,
            "top_p": 0.9
        },
        timeout=30
    )
    
    if resp.status_code == 200:
        data = resp.json()
        return data['choices'][0]['message']['content'].strip()
    else:
        raise Exception(f"Groq API error {resp.status_code}: {resp.text}")

def generate_with_openrouter(api_key, model_name, prompt):
    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}", 
            "Content-Type": "application/json",
            "HTTP-Referer": "https://ai-content-generator.com",
            "X-Title": "AI Content Generator"
        },
        json={
            "model": model_name, 
            "messages":[{"role":"user","content":prompt}], 
            "max_tokens": 2000,
            "temperature": 0.7,
            "top_p": 0.9
        },
        timeout=30
    )
    
    if resp.status_code == 200:
        data = resp.json()
        return data['choices'][0]['message']['content'].strip()
    else:
        raise Exception(f"OpenRouter API error {resp.status_code}: {resp.text}")

# ======== Генерация изображений ========
def generate_article_image(title):
    """Генерация изображения на основе заголовка статьи"""
    logger.info(f"🎨 Генерация изображения для: {title}")
    
    # Пробуем разные методы
    methods = [
        try_craiyon_api,
        try_lexica_art_api,
        generate_enhanced_placeholder
    ]
    
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

def try_craiyon_api(title):
    """Craiyon API - старая стабильная версия"""
    try:
        english_prompt = f"{title}, digital art, futuristic technology, AI, 2025, professional"
        logger.info(f"🎨 Генерация через Craiyon: {english_prompt}")
        
        response = requests.post(
            "https://api.craiyon.com/generate",
            json={"prompt": english_prompt},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("images") and len(data["images"]) > 0:
                image_data = base64.b64decode(data["images"][0])
                return save_image_bytes(image_data, title)
            else:
                logger.warning("⚠️ Craiyon не вернул изображения")
        else:
            logger.warning(f"⚠️ Ошибка Craiyon API: {response.status_code}")
            
    except Exception as e:
        logger.error(f"❌ Ошибка Craiyon: {e}")
    
    return None

def try_lexica_art_api(title):
    """Lexica Art API - поиск существующих AI изображений"""
    try:
        prompt = f"{title}, digital art, futuristic"
        
        search_response = requests.get(
            f"https://lexica.art/api/v1/search?q={requests.utils.quote(prompt)}",
            timeout=20
        )
        
        if search_response.status_code == 200:
            data = search_response.json()
            if data.get('images') and len(data['images']) > 0:
                image_url = data['images'][0]['src']
                img_data = requests.get(image_url, timeout=30).content
                return save_image_bytes(img_data, title)
                
    except Exception as e:
        logger.error(f"❌ Ошибка Lexica Art: {e}")
    
    return None

def save_image_bytes(image_data, title):
    """Сохранение изображения из bytes"""
    try:
        os.makedirs("assets/images/posts", exist_ok=True)
        filename = f"assets/images/posts/{generate_slug(title)}.png"
        
        with open(filename, "wb") as f:
            f.write(image_data)
        
        logger.info(f"💾 Изображение сохранено: {filename}")
        return filename
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения изображения: {e}")
        return None

def generate_enhanced_placeholder(title):
    """Улучшенный placeholder с AI-стилем"""
    try:
        os.makedirs("assets/images/posts", exist_ok=True)
        filename = f"assets/images/posts/{generate_slug(title)}.png"
        width, height = 800, 400
        
        img = Image.new('RGB', (width, height), color='#0f172a')
        draw = ImageDraw.Draw(img)
        
        # Градиентный фон
        for i in range(height):
            r = int(15 + (i/height)*40)
            g = int(23 + (i/height)*60)
            b = int(42 + (i/height)*100)
            draw.line([(0, i), (width, i)], fill=(r, g, b))
        
        # Сетка
        for i in range(0, width, 40):
            draw.line([(i, 0), (i, height)], fill=(255, 255, 255, 25))
        for i in range(0, height, 40):
            draw.line([(0, i), (width, i)], fill=(255, 255, 255, 25))
        
        # Текст
        wrapped_text = textwrap.fill(title, width=35)
        
        try:
            font = ImageFont.truetype("Arial.ttf", 22)
        except:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
            except:
                font = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), wrapped_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (width - text_width) / 2
        y = (height - text_height) / 2
        
        draw.text((x+3, y+3), wrapped_text, font=font, fill="#000000")
        draw.text((x, y), wrapped_text, font=font, fill="#ffffff")
        
        draw.rectangle([(10, height-35), (120, height-10)], fill="#6366f1")
        draw.text((15, height-30), "AI GENERATED", font=ImageFont.load_default(), fill="#ffffff")
        
        img.save(filename)
        logger.info(f"🎨 Создан placeholder: {filename}")
        return filename
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания placeholder: {e}")
        return "assets/images/default.png"

# ======== Вспомогательные функции ========
def generate_slug(text):
    text = text.lower()
    text = text.replace(' ', '-')
    text = re.sub(r'[^a-z0-9\-]', '', text)
    text = re.sub(r'-+', '-', text)
    return text[:60]

def generate_frontmatter(title, content, model_used, image_url):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    escaped_title = title.replace(':', ' -').replace('"', "'")
    
    frontmatter = f"""---
title: "{escaped_title}"
date: {now}
draft: false
image: "{image_url}"
ai_model: "{model_used}"
tags: ["ai", "технологии", "2025"]
categories: ["Искусственный интеллект"]
summary: "Автоматически сгенерированная статья о тенденциях AI в 2025 году"
---

{content}
"""
    return frontmatter

# ======== Запуск ========
def main():
    parser = argparse.ArgumentParser(description='Генератор AI контента')
    parser.add_argument('--debug', action='store_true', help='Включить debug режим')
    parser.add_argument('--count', type=int, default=1, help='Количество статей для генерации')
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.info("🔧 Debug режим включен")
    
    print("🚀 Запуск генератора контента...")
    print("=" * 50)
    
    check_environment_variables()
    print("=" * 50)
    
    try:
        for i in range(args.count):
            print(f"\n📄 Генерация статьи {i+1}/{args.count}...")
            filename = generate_content()
            print(f"✅ Статья создана: {filename}")
            
            if i < args.count - 1:
                time.sleep(2)
                
        print("\n🎉 Все статьи успешно сгенерированы!")
        
    except Exception as e:
        print(f"💥 Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
