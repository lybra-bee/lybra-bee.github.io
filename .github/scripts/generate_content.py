#!/usr/bin/env python3
import os
import json
import requests
import random
from datetime import datetime, timezone
import glob
import re
import time

# -------------------
# Генерация темы статьи
# -------------------
def generate_ai_trend_topic():
    trends = [
        "Multimodal AI", "AI агенты", "Квантовые вычисления и машинное обучение",
        "Нейроморфные вычисления", "Generative AI", "Edge AI", "AI для кибербезопасности",
        "Этичный AI", "AI в healthcare", "Автономные системы", "AI оптимизация",
        "Доверенный AI", "AI для климата", "Персональные AI ассистенты", "AI в образовании"
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

# -------------------
# Создание slug
# -------------------
def generate_slug(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\- ]', '', text)
    text = text.replace(' ', '-')
    text = re.sub(r'-+', '-', text)
    return text[:100]

# -------------------
# Генерация frontmatter для Hugo
# -------------------
def generate_frontmatter(title, date, image_url):
    return f"""---
title: "{title}"
date: "{date}"
draft: false
tags: ["AI","машинное обучение","технологии","2025"]
categories: ["Искусственный интеллект"]
summary: "Автоматически сгенерированная статья о {title}"
image: "{image_url}"
---
"""

# -------------------
# Очистка старых статей
# -------------------
def clean_old_articles(keep_last=3):
    articles = glob.glob("content/posts/*.md")
    if not articles:
        return
    articles.sort(key=os.path.getmtime, reverse=True)
    for article in articles[keep_last:]:
        os.remove(article)

# -------------------
# Генерация текста статьи через OpenRouter/Groq
# -------------------
def generate_article_content(topic):
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    groq_key = os.getenv('GROQ_API_KEY')
    models_to_try = []

    if groq_key:
        groq_models = ["llama-3.1-8b-instant"]
        for m in groq_models:
            models_to_try.append((f"Groq-{m}", lambda m=m: generate_with_groq(groq_key, m, topic)))

    if openrouter_key:
        openrouter_models = ["anthropic/claude-3-haiku"]
        for m in openrouter_models:
            models_to_try.append((m, lambda m=m: generate_with_openrouter(openrouter_key, m, topic)))

    for model_name, func in models_to_try:
        try:
            print(f"Пробуем: {model_name}")
            result = func()
            if result and len(result.strip()) > 100:
                print(f"Успешно через {model_name}")
                return result, model_name
            time.sleep(1)
        except Exception as e:
            print(f"Ошибка {model_name}: {e}")
            continue

    # fallback
    return f"# {topic}\n\nКонтент временно недоступен.", "fallback-generator"

def generate_with_groq(api_key, model_name, topic):
    prompt = f"Напиши развернутую техническую статью на тему: {topic} на русском языке, 400-600 слов."
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"model": model_name, "messages":[{"role":"user","content":prompt}], "max_tokens":1500},
        timeout=30
    )
    r.raise_for_status()
    data = r.json()
    return data['choices'][0]['message']['content']

def generate_with_openrouter(api_key, model_name, topic):
    prompt = f"Напиши развернутую техническую статью на тему: {topic} на русском языке, 400-600 слов."
    r = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"model": model_name, "messages":[{"role":"user","content":prompt}], "max_tokens":1500},
        timeout=30
    )
    r.raise_for_status()
    data = r.json()
    return data['choices'][0]['message']['content']

# -------------------
# Генерация изображения через бесплатные API
# -------------------
def generate_image_placeholder():
    return "/images/posts/placeholder.png"

# -------------------
# Главная функция генерации статьи
# -------------------
def generate_content():
    print("🚀 Запуск генерации контента...")
    clean_old_articles(3)

    topic = generate_ai_trend_topic()
    print(f"📝 Тема: {topic}")

    content, model_used = generate_article_content(topic)

    slug = generate_slug(topic)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    filename = f"content/posts/{date_str}-{slug}.md"

    # placeholder image
    image_url = generate_image_placeholder()

    os.makedirs("content/posts", exist_ok=True)
    frontmatter = generate_frontmatter(topic, date_str, image_url)

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(frontmatter + "\n" + content)

    print(f"✅ Статья создана: {filename}")
    return filename

if __name__ == "__main__":
    generate_content()
