#!/usr/bin/env python3
import os
import json
import requests
import random
from datetime import datetime
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

    # Генерируем изображение
    image_filename = generate_article_image(selected_topic)

    # Генерируем текст статьи
    content, model_used = generate_article_content(selected_topic)

    # Создаем файл статьи
    date = datetime.now().strftime("%Y-%m-%d")
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
    groq_key = os.getenv('GROQ_API_KEY')

    if groq_key:
        print("🔑 Groq API ключ найден")
        try:
            content = generate_with_groq(groq_key, "llama-3.1-8b-instant", topic)
            return content, "Groq-llama-3.1-8b-instant"
        except Exception as e:
            print(f"⚠️ Ошибка генерации через Groq: {e}")

    # Fallback - создаем простой контент
    fallback_content = f"""# {topic}

## Введение
{topic} - это важное направление в развитии искусственного интеллекта на 2025 год.

## Основные аспекты
- **Технологические инновации**: {topic} включает передовые разработки в области AI
- **Практическое применение**: Технология находит применение в различных отраслях
- **Перспективы развития**: Ожидается значительный рост в ближайшие годы

## Заключение
{topic} представляет собой ключевое направление развития искусственного интеллекта с большим потенциалом для инноваций.
"""
    return fallback_content, "fallback-generator"

def generate_with_groq(api_key, model_name, topic):
    """Генерация текста через Groq"""
    prompt = f"Напиши подробную техническую статью на тему: {topic} на русском языке, markdown, 400-600 слов."
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
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
        if data.get("choices"):
            return data["choices"][0]["message"]["content"].strip()
    raise Exception(f"HTTP {response.status_code}: {response.text[:200]}")

def generate_article_image(topic):
    """Генерация изображения через Groq или Stability AI"""
    groq_key = os.getenv('GROQ_API_KEY')
    stability_key = os.getenv('STABILITYAI_KEY')
    image_filename = None

    if groq_key:
        try:
            prompt = f"Generate a futuristic technology image for article topic: {topic}."
            image_filename = generate_image_with_groq(groq_key, prompt, topic)
            if image_filename:
                return image_filename
        except Exception as e:
            print(f"⚠️ Groq image error: {e}")

    if stability_key:
        try:
            prompt = f"Futuristic AI tech illustration for article: {topic}."
            image_filename = generate_image_with_stability(stability_key, prompt, topic)
            if image_filename:
                return image_filename
        except Exception as e:
            print(f"⚠️ Stability AI image error: {e}")

    print("ℹ️ Не удалось создать изображение, пропускаем")
    return None

def generate_image_with_groq(api_key, prompt, topic):
    response = requests.post(
        "https://api.groq.com/openai/v1/images/generations",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"prompt": prompt, "size": "1024x512", "n": 1},
        timeout=30
    )
    if response.status_code == 200:
        data = response.json()
        if data.get("data"):
            image_data = base64.b64decode(data["data"][0]["b64_json"])
            return save_article_image(image_data, topic)
    raise Exception(f"Groq image generation failed: {response.text[:200]}")

def generate_image_with_stability(api_key, prompt, topic):
    response = requests.post(
        "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "text_prompts": [{"text": prompt}],
            "width": 1024,
            "height": 512,
            "samples": 1
        },
        timeout=30
    )
    if response.status_code == 200:
        data = response.json()
        if data.get("artifacts"):
            image_data = base64.b64decode(data["artifacts"][0]["base64"])
            return save_article_image(image_data, topic)
    raise Exception(f"Stability AI image generation failed: {response.text[:200]}")

def save_article_image(image_data, topic):
    os.makedirs("assets/images/posts", exist_ok=True)
    slug = generate_slug(topic)
    filename = f"posts/{slug}.jpg"
    full_path = f"assets/images/{filename}"
    with open(full_path, "wb") as f:
        f.write(image_data)
    print(f"💾 Изображ
