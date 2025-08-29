#!/usr/bin/env python3
import os
import json
import requests
import random
from datetime import datetime, timezone
import glob
import time

PLACEHOLDER_IMAGE = "https://via.placeholder.com/800x450.png?text=AI+Image"

def generate_ai_trend_topic():
    """Генерирует актуальную тему на основе трендов AI 2025"""
    trends = [
        "Multimodal AI", "AI агенты", "Квантовые вычисления и ML",
        "Нейроморфные вычисления", "Generative AI", "Edge AI",
        "AI для кибербезопасности", "Этичный AI", "AI в healthcare",
        "Автономные системы", "AI оптимизация", "Доверенный AI",
        "AI для климата", "Персональные AI ассистенты", "AI в образовании"
    ]
    domains = [
        "в веб-разработке", "в мобильных приложениях", "в облачных сервисах",
        "в анализе больших данных", "в кибербезопасности", "в медицинской диагностике",
        "в финтехе", "в автономных транспортных системах", "в smart city",
        "в образовательных технологиях"
    ]
    trend = random.choice(trends)
    domain = random.choice(domains)
    formats = [
        f"{trend} {domain} в 2025 году",
        f"Тенденции 2025: {trend} {domain}",
        f"{trend} - революционные изменения {domain} в 2025",
        f"Как {trend} трансформирует {domain} в 2025 году",
        f"Инновации 2025: {trend} для {domain}"
    ]
    return random.choice(formats)

def generate_slug(text):
    text = text.lower()
    text = ''.join(c for c in text if c.isalnum() or c in ' -')
    text = text.replace(' ', '-')
    text = text.replace('--', '-')
    return text[:100]

def clean_old_articles(keep_last=3):
    """Удаляет старые статьи, оставляя только последние N"""
    articles = glob.glob("content/posts/*.md")
    if not articles:
        return
    articles.sort(key=os.path.getmtime, reverse=True)
    for old_article in articles[keep_last:]:
        try:
            os.remove(old_article)
        except: pass

def generate_article_content(topic):
    """Попытка генерации статьи через API"""
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    # Только пример, Groq или другие можно добавить позже
    prompt = f"Напиши техническую статью на тему: '{topic}' на русском языке, Markdown."
    if openrouter_key:
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {openrouter_key}", "Content-Type": "application/json"},
                json={"model": "anthropic/claude-3-haiku", "messages":[{"role":"user","content":prompt}], "max_tokens": 1500}
            )
            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                if content.strip(): 
                    return content
        except: pass
    # fallback
    return f"# {topic}\n\nЭто автоматическая статья о '{topic}' для демонстрации функционала блога."

def generate_frontmatter(title, image_url):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    frontmatter = f"""---
title: "{title}"
date: {now}
draft: false
tags: ["AI","машинное обучение","технологии","2025"]
categories: ["Искусственный интеллект"]
summary: "Автоматически сгенерированная статья о {title}"
image: "{image_url}"
---
"""
    return frontmatter

def generate_content():
    print("🚀 Запуск генерации контента...")
    clean_old_articles(3)
    topic = generate_ai_trend_topic()
    print(f"📝 Тема: {topic}")
    slug = generate_slug(topic)
    filename = f"content/posts/{datetime.now().strftime('%Y-%m-%d')}-{slug}.md"
    os.makedirs("content/posts", exist_ok=True)

    content_body = generate_article_content(topic)
    # Пока placeholder для изображения
    frontmatter = generate_frontmatter(topic, PLACEHOLDER_IMAGE)

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(frontmatter + content_body)

    print(f"✅ Статья создана: {filename}")
    return filename

if __name__ == "__main__":
    generate_content()
