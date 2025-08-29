#!/usr/bin/env python3
import os
import json
import requests
import random
from datetime import datetime, timezone
import glob
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
    print("🚀 Запуск генерации контента...")
    KEEP_LAST_ARTICLES = 3
    clean_old_articles(KEEP_LAST_ARTICLES)

    selected_topic = generate_ai_trend_topic()
    print(f"📝 Актуальная тема 2025: {selected_topic}")

    # Генерируем текст статьи
    content, model_used = generate_article_content(selected_topic)

    # Генерируем изображение для статьи
    image_url = generate_image_for_article(content)

    # Создаем файл статьи
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    slug = generate_slug(selected_topic)
    filename = f"content/posts/{date}-{slug}.md"
    frontmatter = generate_frontmatter(selected_topic, content, model_used, image_url)

    os.makedirs("content/posts", exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(frontmatter)

    print(f"✅ Статья создана: {filename}")
    return filename

def generate_article_content(topic):
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    groq_key = os.getenv('GROQ_API_KEY')
    models_to_try = []

    if groq_key:
        groq_models = ["llama-3.1-8b-instant", "llama-3.2-1b-preview"]
        for model_name in groq_models:
            models_to_try.append((f"Groq-{model_name}", lambda m=model_name: generate_with_groq(groq_key, m, topic)))

    if openrouter_key:
        openrouter_models = ["anthropic/claude-3-haiku","google/gemini-pro"]
        for model_name in openrouter_models:
            models_to_try.append((model_name, lambda m=model_name: generate_with_openrouter(openrouter_key, m, topic)))

    for model_name, generate_func in models_to_try:
        try:
            print(f"🔄 Пробуем: {model_name}")
            result = generate_func()
            if result and len(result.strip()) > 100:
                print(f"✅ Успешно через {model_name}")
                return result, model_name
            time.sleep(1)
        except Exception as e:
            print(f"⚠️ Ошибка {model_name}: {str(e)[:200]}")
            continue

    print("⚠️ Все API недоступны, создаем заглушку")
    fallback_content = f"""# {topic}

## Введение
{topic} - это важное направление в развитии искусственного интеллекта на 2025 год.

## Основные аспекты
- **Технологические инновации**: {topic} включает передовые разработки в области AI
- **Практическое применение**: Технология находит применение в различных отраслях
- **Перспективы развития**: Ожидается значительный рост в ближайшие годы

## Технические детали
Модели искусственного интеллекта для {topic} используют современные архитектуры нейросетей.

## Заключение
{topic} представляет собой ключевое направление развития искусственного интеллекта.
"""
    return fallback_content, "fallback-generator"

# ----------------- Генерация изображений -----------------
def generate_image_for_article(article_text):
    print("🎨 Генерация изображения для статьи...")
    image_services = [
        ("Raphael AI", lambda txt: generate_with_raphael(txt)),
        ("n8n AI", lambda txt: generate_with_n8n(txt)),
        ("DeepAI", lambda txt: generate_with_deepai(txt))
    ]
    for service_name, func in image_services:
        try:
            print(f"🔄 Пробуем: {service_name}")
            image_url = func(article_text)
            if image_url and image_url.strip().startswith("http"):
                print(f"✅ Успешно через {service_name}: {image_url}")
                return image_url
            else:
                print(f"⚠️ Сервис {service_name} вернул пустой или некорректный URL: {image_url}")
        except Exception as e:
            print(f"⚠️ Ошибка {service_name}: {str(e)[:200]}")
            continue
    print("⚠️ Все сервисы недоступны, изображение не создано")
    return None

def generate_with_raphael(text):
    response = requests.post("https://api.raphaelai.org/generate", json={"prompt": text, "size": "1024x1024"})
    print("Raphael AI response:", response.text)
    data = response.json()
    return data.get("image_url")

def generate_with_n8n(text):
    response = requests.post("https://n8n.io/tools/ai-image-generator", json={"prompt": text,"width":1024,"height":1024})
    print("n8n AI response:", response.text)
    data = response.json()
    return data.get("image")

def generate_with_deepai(text):
    response = requests.post("https://api.deepai.org/api/text2img", data={"text": text})
    print("DeepAI response:", response.text)
    data = response.json()
    return data.get("output_url")

# ----------------- Остальные функции -----------------
def generate_with_groq(api_key, model_name, topic):
    prompt = f"Напиши статью: {topic}..."
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model_name, "messages":[{"role":"user","content":prompt}],"max_tokens":1500}
    )
    if response.status_code == 200:
        data = response.json()
        return data['choices'][0]['message']['content']
    raise Exception(f"HTTP {response.status_code}: {response.text[:200]}")

def generate_with_openrouter(api_key, model_name, topic):
    prompt = f"Напиши статью: {topic}..."
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}","Content-Type":"application/json"},
        json={"model": model_name, "messages":[{"role":"user","content":prompt}],"max_tokens":1500}
    )
    if response.status_code == 200:
        data = response.json()
        return data['choices'][0]['message']['content']
    raise Exception(f"HTTP {response.status_code}")

def generate_slug(text):
    text = text.lower()
    text = ''.join(c for c in text if c.isalnum() or c in ' -')
    text = text.replace(' ', '-').replace('--','-')
    return text[:100]

def generate_frontmatter(title, content, model_used, image_url):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    img_line = f'image: "{image_url}"' if image_url else ''
    frontmatter = f"""---
title: "{title}"
date: {now}
draft: false
tags: ["AI","машинное обучение","технологии","2025"]
categories: ["Искусственный интеллект"]
summary: "Автоматически сгенерированная статья"
{img_line}
---
{content}
"""
    return frontmatter

def clean_old_articles(keep_last=3):
    print(f"🧹 Очистка старых статей, оставляем {keep_last} последних...")
    try:
        articles = glob.glob("content/posts/*.md")
        if not articles:
            print("📁 Нет статей для очистки")
            return
        articles.sort(key=os.path.getmtime, reverse=True)
        for article_path in articles[keep_last:]:
            try:
                os.remove(article_path)
                print(f"❌ Удалено: {os.path.basename(article_path)}")
            except Exception as e:
                print(f"⚠️ Ошибка удаления {article_path}: {e}")
    except Exception as e:
        print(f"⚠️ Ошибка при очистке статей: {e}")

if __name__ == "__main__":
    generate_content()
