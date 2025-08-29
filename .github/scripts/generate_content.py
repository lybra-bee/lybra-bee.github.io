#!/usr/bin/env python3
import os
import json
import requests
import random
from datetime import datetime, timezone
import glob
import time
import base64

# ======== Настройка генераторов изображений ========
FREE_IMAGE_SERVICES = [
    "craiyon",
    "lorempicsum"
]

# ======== Генерация темы ========
def generate_ai_trend_topic():
    trends = [
        "Multimodal AI - интеграция текста, изображений и аудио",
        "AI агенты - автономные системы для сложных задач",
        "Квантовые вычисления и машинное обучение",
        "Нейроморфные вычисления - энергоэффективные архитектуры",
        "Generative AI - создание контента и кода ИИ",
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
    domains = [
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
    trend = random.choice(trends)
    domain = random.choice(domains)
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

# ======== Генерация статьи ========
def generate_article_content(topic):
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    groq_key = os.getenv('GROQ_API_KEY')

    models_to_try = []
    if groq_key:
        groq_models = ["llama-3.1-8b-instant"]
        for model_name in groq_models:
            models_to_try.append((f"Groq-{model_name}", lambda m=model_name: generate_with_groq(groq_key, m, topic)))
    if openrouter_key:
        openrouter_models = ["anthropic/claude-3-haiku"]
        for model_name in openrouter_models:
            models_to_try.append((model_name, lambda m=model_name: generate_with_openrouter(openrouter_key, m, topic)))

    for model_name, func in models_to_try:
        try:
            print(f"🔄 Пробуем: {model_name}")
            content = func()
            if content and len(content.strip()) > 100:
                print(f"✅ Успешно через {model_name}")
                return content, model_name
        except Exception as e:
            print(f"⚠️ Ошибка {model_name}: {str(e)[:100]}")
    print("⚠️ Все API недоступны, создаем заглушку")
    return f"# {topic}\n\nАвтоматически сгенерированная заглушка статьи.", "fallback-generator"

def generate_with_groq(api_key, model_name, topic):
    prompt = f"Напиши техническую статью на тему: {topic} на русском, 400-600 слов, Markdown."
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"model": model_name, "messages":[{"role":"user","content":prompt}]},
        timeout=30
    )
    data = response.json()
    if response.status_code == 200 and data.get('choices'):
        return data['choices'][0]['message']['content'].strip()
    raise Exception(f"HTTP {response.status_code}")

def generate_with_openrouter(api_key, model_name, topic):
    prompt = f"Напиши техническую статью на тему: {topic} на русском, 400-600 слов, Markdown."
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"model": model_name, "messages":[{"role":"user","content":prompt}]},
        timeout=30
    )
    data = response.json()
    if response.status_code == 200 and data.get('choices'):
        return data['choices'][0]['message']['content'].strip()
    raise Exception(f"HTTP {response.status_code}")

# ======== Генерация изображения ========
def generate_image_for_content(text, slug):
    os.makedirs("static/images/posts", exist_ok=True)
    for service in FREE_IMAGE_SERVICES:
        try:
            if service == "craiyon":
                url = "https://api.craiyon.com/generate"
                r = requests.post(url, json={"prompt": text}, timeout=30)
                if r.status_code == 200 and r.json().get("images"):
                    img_data = base64.b64decode(r.json()["images"][0])
                    path = f"static/images/posts/{slug}.png"
                    with open(path, "wb") as f: f.write(img_data)
                    return f"/images/posts/{slug}.png"
            elif service == "lorempicsum":
                path = f"static/images/posts/{slug}.jpg"
                img_url = f"https://picsum.photos/seed/{slug}/800/400"
                with open(path, "wb") as f: f.write(requests.get(img_url).content)
                return f"/images/posts/{slug}.jpg"
        except Exception as e:
            print(f"⚠️ Ошибка генерации через {service}: {e}")
    return ""

# ======== Служебные функции ========
def generate_slug(text):
    text = text.lower()
    text = ''.join(c for c in text if c.isalnum() or c in ' -')
    text = text.replace(' ', '-').replace('--','-').strip('-')
    return text[:100]

def generate_frontmatter(title, content, model_used, image_url):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return f"""---
title: "{title}"
date: {now}
draft: false
tags: ["AI","машинное обучение","технологии","2025"]
categories: ["Искусственный интеллект"]
summary: "Автоматически сгенерированная статья"
image: "{image_url}"
---
{content}
"""

def clean_old_articles(keep_last=3):
    print(f"🧹 Очистка старых статей, оставляем {keep_last} последних...")
    articles = glob.glob("content/posts/*.md")
    articles.sort(key=os.path.getmtime, reverse=True)
    for a in articles[keep_last:]:
        os.remove(a)
        print(f"❌ Удалено: {os.path.basename(a)}")

# ======== Основной процесс ========
def generate_content():
    print("🚀 Запуск генерации контента...")
    clean_old_articles(3)

    topic = generate_ai_trend_topic()
    print(f"📝 Тема: {topic}")

    content, model_used = generate_article_content(topic)
    slug = generate_slug(topic)
    image_url = generate_image_for_content(topic, slug)

    os.makedirs("content/posts", exist_ok=True)
    filename = f"content/posts/{datetime.now().strftime('%Y-%m-%d')}-{slug}.md"
    frontmatter = generate_frontmatter(topic, content, model_used, image_url)

    with open(filename, "w", encoding="utf-8") as f:
        f.write(frontmatter)

    print(f"✅ Статья создана: {filename}")

if __name__ == "__main__":
    generate_content()
