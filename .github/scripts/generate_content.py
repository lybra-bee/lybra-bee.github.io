#!/usr/bin/env python3
import os
import json
import requests
import random
from datetime import datetime, timezone
import glob
import time

# -----------------------------
# Настройка генерации темы
# -----------------------------
def generate_ai_trend_topic():
    current_trends_2025 = [
        "Multimodal AI - интеграция текста, изображений и аудио",
        "AI агенты - автономные системы",
        "Квантовые вычисления и ML",
        "Нейроморфные вычисления",
        "Generative AI - создание контента и кода",
        "Edge AI - обработка данных на устройстве",
        "AI для кибербезопасности",
        "Этичный AI",
        "AI в healthcare",
        "Автономные системы",
        "AI оптимизация",
        "Доверенный AI",
        "AI для климата",
        "Персональные AI ассистенты",
        "AI в образовании"
    ]
    application_domains = [
        "в веб-разработке и cloud-native приложениях",
        "в мобильных приложениях и IoT экосистемах",
        "в облачных сервисах и распределенных системах",
        "в анализе больших данных",
        "в компьютерной безопасности",
        "в медицинской диагностике",
        "в финансовых технологиях",
        "в автономных транспортных системах",
        "в smart city и умной инфраструктуре",
        "в образовательных технологиях"
    ]
    trend = random.choice(current_trends_2025)
    domain = random.choice(application_domains)
    templates = [
        f"{trend} {domain} в 2025 году",
        f"Тенденции 2025: {trend} {domain}",
        f"{trend} - революционные изменения {domain} в 2025",
        f"Как {trend} трансформирует {domain} в 2025 году",
        f"Инновации 2025: {trend} для {domain}",
        f"{trend} - будущее {domain} в 2025 году",
        f"Практическое применение {trend} в {domain} 2025"
    ]
    return random.choice(templates)

# -----------------------------
# Генерация статьи через API
# -----------------------------
def generate_article_content(topic):
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    groq_key = os.getenv('GROQ_API_KEY')

    models_to_try = []

    if groq_key:
        groq_models = ["llama-3.1-8b-instant", "llama-3.2-1b-preview"]
        for m in groq_models:
            models_to_try.append((f"Groq-{m}", lambda m=m: generate_with_groq(groq_key, m, topic)))

    if openrouter_key:
        openrouter_models = ["anthropic/claude-3-haiku", "google/gemini-pro"]
        for m in openrouter_models:
            models_to_try.append((m, lambda m=m: generate_with_openrouter(openrouter_key, m, topic)))

    for model_name, func in models_to_try:
        try:
            print(f"🔄 Пробуем: {model_name}")
            result = func()
            if result and len(result.strip()) > 100:
                print(f"✅ Успешно через {model_name}")
                return result, model_name
            time.sleep(1)
        except Exception as e:
            print(f"⚠️ Ошибка {model_name}: {str(e)[:100]}")
            continue

    # fallback
    print("⚠️ Все API недоступны, создаем заглушку")
    fallback_content = f"""# {topic}

## Введение
{topic} - ключевое направление AI на 2025 год.

## Основные аспекты
- **Технологические инновации**: {topic} включает передовые разработки
- **Применение**: Технология используется в разных областях
- **Перспективы**: Ожидается рост и развитие

## Заключение
{topic} имеет большой потенциал для инноваций
"""
    return fallback_content, "fallback-generator"

# -----------------------------
# Groq API
# -----------------------------
def generate_with_groq(api_key, model_name, topic):
    prompt = f"Напиши техническую статью на тему: '{topic}'. 400-600 слов, Markdown, русский, стиль: для разработчиков"
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Content-Type":"application/json", "Authorization": f"Bearer {api_key}"},
        json={"model": model_name, "messages":[{"role":"user","content":prompt}], "max_tokens":1500, "temperature":0.7},
        timeout=30
    )
    if response.status_code == 200:
        data = response.json()
        return data['choices'][0]['message']['content'].strip()
    raise Exception(f"HTTP {response.status_code}: {response.text[:200]}")

# -----------------------------
# OpenRouter API
# -----------------------------
def generate_with_openrouter(api_key, model_name, topic):
    prompt = f"Напиши статью: '{topic}' 400-600 слов, Markdown, русский, для разработчиков"
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Content-Type":"application/json","Authorization":f"Bearer {api_key}"},
        json={"model": model_name, "messages":[{"role":"user","content":prompt}],"max_tokens":1500,"temperature":0.7},
        timeout=30
    )
    if response.status_code == 200:
        data = response.json()
        return data['choices'][0]['message']['content'].strip()
    raise Exception(f"HTTP {response.status_code}")

# -----------------------------
# Генерация изображения
# -----------------------------
def generate_image(topic, filename):
    # Перебор бесплатных генераторов изображений
    generators = [
        generate_image_openrouter,
        generate_image_deepai,
        generate_image_craiyon,
        generate_image_lexica
    ]
    for gen in generators:
        try:
            url = gen(topic, filename)
            if url:
                print(f"✅ Изображение сгенерировано через {gen.__name__}")
                return url
        except Exception as e:
            print(f"⚠️ Ошибка генерации через {gen.__name__}: {e}")
            continue
    print("❌ Все генераторы не сработали")
    return None

def generate_image_openrouter(topic, filename):
    key = os.getenv('OPENROUTER_API_KEY')
    if not key:
        raise Exception("Нет OPENROUTER_API_KEY")
    prompt = f"Создай иллюстрацию к статье: '{topic}'"
    response = requests.post(
        "https://openrouter.ai/api/v1/images/generations",
        headers={"Authorization": f"Bearer {key}"},
        json={"prompt":prompt,"size":"1024x1024"},
        timeout=30
    )
    if response.status_code == 200:
        data = response.json()
        image_base64 = data['data'][0]['b64_json']
        image_bytes = base64.b64decode(image_base64)
        os.makedirs("static/images/posts", exist_ok=True)
        with open(f"static/images/posts/{filename}", 'wb') as f:
            f.write(image_bytes)
        return f"images/posts/{filename}"
    raise Exception(f"HTTP {response.status_code}: {response.text}")

def generate_image_deepai(topic, filename):
    key = "6d27650a"
    response = requests.post(
        "https://api.deepai.org/api/text2img",
        headers={"api-key": key},
        data={"text": topic},
        timeout=30
    )
    if response.status_code == 200:
        data = response.json()
        image_url = data.get('output_url')
        if image_url:
            return image_url
    raise Exception(f"HTTP {response.status_code}: {response.text}")

def generate_image_craiyon(topic, filename):
    response = requests.post(
        "https://backend.craiyon.com/generate",
        json={"prompt": topic},
        timeout=30
    )
    if response.status_code == 200:
        data = response.json()
        if "images" in data:
            return data["images"][0]
    raise Exception(f"HTTP {response.status_code}: {response.text}")

def generate_image_lexica(topic, filename):
    response = requests.get(
        f"https://lexica.art/api/v1/search?q={requests.utils.quote(topic)}",
        timeout=30
    )
    if response.status_code == 200:
        data = response.json()
        if data.get("images"):
            return data["images"][0]["srcSmall"]
    raise Exception(f"HTTP {response.status_code}: {response.text}")

# -----------------------------
# Создание slug
# -----------------------------
def generate_slug(text):
    text = text.lower()
    text = ''.join(c for c in text if c.isalnum() or c in ' -')
    text = text.replace(' ', '-').replace('--','-')
    return text[:100]

# -----------------------------
# Frontmatter Hugo
# -----------------------------
def generate_frontmatter(title, content, image_filename):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    fm = f"""---
title: "{title}"
date: "{now}"
draft: false
tags: ["AI","Технологии","2025"]
categories: ["Искусственный интеллект"]
image: "/{image_filename}" 
summary: "Автоматически сгенерированная статья о {title}"
---
{content}
"""
    return fm

# -----------------------------
# Очистка старых статей
# -----------------------------
def clean_old_articles(keep_last=3):
    print(f"🧹 Очистка старых статей, оставляем {keep_last} последних...")
    try:
        articles = glob.glob("content/posts/*.md")
        articles.sort(key=os.path.getmtime, reverse=True)
        for a in articles[keep_last:]:
            try: os.remove(a)
            except: pass
    except Exception as e:
        print(f"⚠️ Ошибка очистки: {e}")

# -----------------------------
# Основная функция
# -----------------------------
def generate_content():
    print("🚀 Запуск генерации контента...")
    clean_old_articles(3)
    topic = generate_ai_trend_topic()
    print(f"📝 Тема: {topic}")
    content, model_used = generate_article_content(topic)
    slug = generate_slug(topic)
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    image_filename = f"{slug}.png"
    image_url = generate_image(topic, image_filename)
    frontmatter = generate_frontmatter(topic, content, image_filename if image_url else "")
    os.makedirs("content/posts", exist_ok=True)
    filepath = f"content/posts/{date}-{slug}.md"
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(frontmatter)
    print(f"✅ Статья создана: {filepath}")
    return filepath

if __name__ == "__main__":
    generate_content()
