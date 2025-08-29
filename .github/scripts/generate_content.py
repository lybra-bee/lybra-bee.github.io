#!/usr/bin/env python3
import os
import json
import requests
import random
from datetime import datetime, timezone
import glob
import base64
import time
import urllib.parse

def generate_ai_trend_topic():
    """Генерирует актуальную тему на основе реальных трендов AI 2025"""
    
    current_trends_2025 = [
        "Multimodal AI - интеграция текста, изображений и аудио в единых моделях",
        "AI агенты - автономные системы способные выполнять сложные задачи",
        "Квантовые вычисления и машинное обучение - прорыв в производительности",
        "Нейроморфные вычисления - энергоэффективные архитектуры нейросетей",
        "Generative AI - создание контента, кода и дизайнов искусственным интеллектом",
        "Edge AI - обработка данных на устройстве без облачной зависимости",
        "AI для кибербезопасности - предиктивная защита от угроз",
        "Этичный AI - ответственное развитие и использование искусственного интеллекта",
        "AI в healthcare - диагностика, разработка лекарств и персонализированная медицина",
        "Автономные системы - беспилотный транспорт и робототехника",
        "AI оптимизация - сжатие моделей и ускорение inference",
        "Доверенный AI - объяснимые и прозрачные алгоритмы",
        "AI для климата - оптимизация энергопотребления и экологические решения",
        "Персональные AI ассистенты - индивидуализированные цифровые помощники",
        "AI в образовании - адаптивное обучение и персонализированные учебные планы"
    ]
    
    application_domains = [
        "в веб-разработке и cloud-native приложениях",
        "в мобильных приложениях и IoT экосистемах",
        "в облачных сервисах и распределенных системах",
        "в анализе больших данных и бизнес-аналитике",
        "в компьютерной безопасности и киберзащите",
        "в медицинской диагностике и биотехнологиях",
        "в финансовых технологиях и финтехе",
        "в автономных транспортных системах",
        "в smart city и умной инфраструктуре",
        "в образовательных технологиях и EdTech"
    ]
    
    trend = random.choice(current_trends_2025)
    domain = random.choice(application_domains)
    
    topic_formats = [
        f"{trend} {domain} в 2025 году",
        f"Тенденции 2025: {trend} {domain}",
        f"{trend} - революционные изменения {domain} в 2025",
        f"Как {trend} трансформирует {domain} в 2025 году",
        f"Инновации 2025: {trend} для {domain}",
        f"{trend} - будущее {domain} в 2025 году",
        f"Практическое применение {trend} в {domain} 2025"
    ]
    
    return random.choice(topic_formats)

def generate_content():
    """Генерирует контент статьи через AI API"""
    print("🚀 Запуск генерации контента...")
    
    KEEP_LAST_ARTICLES = 3
    clean_old_articles(KEEP_LAST_ARTICLES)
    
    selected_topic = generate_ai_trend_topic()
    print(f"📝 Актуальная тема 2025: {selected_topic}")
    
    # Генерируем изображение через Stability AI
    image_filename = generate_article_image(selected_topic)
    
    # Генерируем текст статьи
    content, model_used = generate_article_content(selected_topic)
    
    # Создаем файл статьи
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    slug = generate_slug(selected_topic)
    filename = f"content/posts/{date}-{slug}.md"
    
    frontmatter = generate_frontmatter(selected_topic, content, model_used, image_filename)
    
    os.makedirs("content/posts", exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(frontmatter)
    
    print(f"✅ Статья создана: {filename}")
    return filename

def generate_article_content(topic):
    """Генерация содержания статьи через доступные API"""
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    groq_key = os.getenv('GROQ_API_KEY')
    
    models_to_try = []
    
    # Добавляем Groq модели (актуальные версии)
    if groq_key:
        print("🔑 Groq API ключ найден")
        groq_models = [
            "llama-3.1-8b-instant",  # Быстрая и бесплатная
            "llama-3.2-1b-preview",  # Новая версия
            "llama-3.2-3b-preview",  # Новая версия
            "mixtral-8x7b-32768",    # Хорошая для текста
            "gemma2-9b-it"           # Современная модель
        ]
        for model_name in groq_models:
            models_to_try.append((f"Groq-{model_name}", lambda m=model_name: generate_with_groq(groq_key, m, topic)))
    
    # Добавляем OpenRouter модели
    if openrouter_key:
        print("🔑 OpenRouter API ключ найден")
        openrouter_models = [
            "anthropic/claude-3-haiku",
            "google/gemini-pro", 
            "mistralai/mistral-7b-instruct",
            "meta-llama/llama-3-8b-instruct",
        ]
        for model_name in openrouter_models:
            models_to_try.append((model_name, lambda m=model_name: generate_with_openrouter(openrouter_key, m, topic)))
    
    # Пробуем все доступные модели
    for model_name, generate_func in models_to_try:
        try:
            print(f"🔄 Пробуем: {model_name}")
            result = generate_func()
            if result and len(result.strip()) > 100:  # Проверяем что контент не пустой
                print(f"✅ Успешно через {model_name}")
                return result, model_name
            time.sleep(1)
        except Exception as e:
            print(f"⚠️ Ошибка {model_name}: {str(e)[:100]}")
            continue
    
    # Fallback - создаем простой контент
    print("⚠️ Все API недоступны, создаем заглушку")
    fallback_content = f"""# {topic}

## Введение
{topic} - это важное направление в развитии искусственного интеллекта на 2025 год.

## Основные аспекты
- **Технологические инновации**: {topic} включает передовые разработки в области AI
- **Практическое применение**: Технология находит применение в различных отраслях
- **Перспективы развития**: Ожидается значительный рост в ближайшие годы

## Технические детали
Модели искусственного интеллекта для {topic} используют современные архитектуры нейросетей, включая трансформеры и генеративные модели.

## Заключение
{topic} представляет собой ключевое направление развития искусственного интеллекта с большим потенциалом для инноваций.
"""
    return fallback_content, "fallback-generator"

def generate_with_groq(api_key, model_name, topic):
    """Генерация через Groq API"""
    prompt = f"""Напиши развернутую техническую статью на тему: "{topic}".

Требования:
- Объем: 400-600 слов
- Формат: Markdown с подзаголовками ##
- Язык: русский, технический стиль
- Аудитория: разработчики и IT-специалисты
- Фокус на 2025 год и современные технологии

Структура:
1. Введение и актуальность темы
2. Технические особенности и архитектура
3. Примеры использования и кейсы
4. Перспективы развития
5. Заключение и выводы

Используй:
- **Жирный шрифт** для ключевых терминов
- Маркированные списки для перечислений
- Конкретные примеры и технические детали
- Современные технологии и frameworks"""

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        },
        json={
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1500,
            "temperature": 0.7,
            "top_p": 0.9
        },
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get('choices'):
            content = data['choices'][0]['message']['content']
            return content.strip()
    
    raise Exception(f"HTTP {response.status_code}: {response.text[:200]}")

def generate_with_openrouter(api_key, model_name, topic):
    """Генерация через OpenRouter"""
    prompt = f"""Напиши развернутую техническую статью на тему: "{topic}".

Требования:
- Объем: 400-600 слов
- Формат: Markdown с подзаголовками
- Язык: русский
- Стиль: технический, для разработчиков
- Фокус на 2025 год

Структура:
1. Введение
2. Основная часть с техническими деталями
3. Примеры использования
4. Заключение

Используй:
- **Жирный шрифт** для терминов
- Списки для перечисления
- Конкретные примеры и технологии"""
    
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://github.com/lybra-bee",
            "X-Title": "AI Blog Generator"
        },
        json={
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1500,
            "temperature": 0.7
        },
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get('choices'):
            content = data['choices'][0]['message']['content']
            return content.strip()
    
    raise Exception(f"HTTP {response.status_code}")

def generate_article_image(topic):
    """Генерация изображения через Stability AI"""
    print("🎨 Генерация изображения через Stability AI...")
    
    stability_key = os.getenv('STABILITYAI_KEY')
    if not stability_key:
        print("ℹ️ STABILITYAI_KEY не найден, пропускаем генерацию изображения")
        return None
    
    try:
        # Генерируем промпт для изображения
        image_prompt = generate_image_prompt(topic)
        print(f"📝 Промпт для изображения: {image_prompt}")
        
        # Используем Stability AI API
        url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
        
        headers = {
            "Authorization": f"Bearer {stability_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Правильные параметры для Stable Diffusion XL
        payload = {
            "text_prompts": [
                {
                    "text": image_prompt,
                    "weight": 1.0
                }
            ],
            "cfg_scale": 7,
            "height": 1024,  # Правильный размер для SDXL
            "width": 1024,   # Правильный размер для SDXL
            "samples": 1,
            "steps": 30,
            "style_preset": "digital-art"
        }
        
        print("🔄 Отправка запроса к Stability AI...")
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            if 'artifacts' in data and data['artifacts']:
                image_data = base64.b64decode(data['artifacts'][0]['base64'])
                filename = save_article_image(image_data, topic)
                if filename:
                    print("✅ Изображение создано через Stability AI")
                    return filename
                else:
                    print("❌ Ошибка сохранения изображения")
            else:
                print(f"❌ Нет artifacts в ответе: {data}")
        else:
            print(f"❌ Stability AI error: {response.status_code}")
            print(f"❌ Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Ошибка Stability AI: {e}")
    
    print("⚠️ Генерация изображения не удалась, продолжаем без изображения")
    return None

def generate_image_prompt(topic):
    """Генерирует промпт для изображения на английском"""
    prompts = [
        f"Technology illustration for article about {topic}. Modern futuristic style, abstract technology concept with neural networks, AI, data visualization. Blue and purple color scheme, professional digital art, no text",
        f"AI technology concept art for {topic}. Futuristic cyberpunk style, glowing neural networks, holographic interfaces, digital particles. Dark background with vibrant colors, cinematic lighting",
        f"Abstract technology background for {topic}. Geometric shapes, circuit patterns, data streams, glowing connections. Professional corporate style, clean design, technology theme",
        f"Futuristic AI concept for {topic}. Digital brain, neural connections, data flow, quantum computing elements. Sci-fi style, vibrant colors, depth of field"
    ]
    
    return random.choice(prompts)

def save_article_image(image_data, topic):
    """Сохраняет сгенерированное изображение"""
    try:
        os.makedirs("assets/images/posts", exist_ok=True)
        slug = generate_slug(topic)
        filename = f"posts/{slug}.png"  # Используем PNG для лучшего качества
        full_path = f"assets/images/{filename}"
        
        with open(full_path, 'wb') as f:
            f.write(image_data)
        
        print(f"💾 Изображение сохранено: {filename}")
        return f"/images/{filename}"
        
    except Exception as e:
        print(f"❌ Ошибка сохранения изображения: {e}")
        return None

def generate_slug(text):
    """Создает slug из текста"""
    text = text.lower()
    text = ''.join(c for c in text if c.isalnum() or c in ' -')
    text = text.replace(' ', '-')
    text = text.replace('--', '-')
    return text[:100]

def generate_frontmatter(title, content, model_used, image_url):
    """Генерирует frontmatter для Hugo"""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    frontmatter = f"""---
title: "{title}"
date: {now}
draft: false
tags: ["AI", "машинное обучение", "технологии", "2025"]
categories: ["Искусственный интеллект"]
summary: "Автоматически сгенерированная статья об искусственном интеллекте"
"""
    
    if image_url:
        frontmatter += f"image: \"{image_url}\"\n"
    
    frontmatter += f"""---
{content}
"""
    return frontmatter

def clean_old_articles(keep_last=3):
    """Оставляет только последние N статей"""
    print(f"🧹 Очистка старых статей, оставляем {keep_last} последних...")
    
    try:
        articles = glob.glob("content/posts/*.md")
        if not articles:
            print("📁 Нет статей для очистки")
            return
        
        articles.sort(key=os.path.getmtime, reverse=True)
        articles_to_keep = articles[:keep_last]
        articles_to_delete = articles[keep_last:]
        
        print(f"📊 Всего статей: {len(articles)}")
        print(f"💾 Сохраняем: {len(articles_to_keep)}")
        print(f"🗑️ Удаляем: {len(articles_to_delete)}")
        
        for article_path in articles_to_delete:
            try:
                os.remove(article_path)
                print(f"❌ Удалено: {os.path.basename(article_path)}")
                
                # Также удаляем связанное изображение если есть
                slug = os.path.basename(article_path).replace('.md', '')
                image_path = f"assets/images/posts/{slug}.png"
                if os.path.exists(image_path):
                    os.remove(image_path)
                    print(f"❌ Удалено изображение: {slug}.png")
                    
            except Exception as e:
                print(f"⚠️ Ошибка удаления {article_path}: {e}")

    except Exception as e:
        print(f"⚠️ Ошибка при очистке статей: {e}")

if __name__ == "__main__":
    generate_content()
