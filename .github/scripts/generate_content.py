#!/usr/bin/env python3
import os
import json
import requests
import random
from datetime import datetime, timezone
import glob
import time
import base64

# -----------------------
# Генерация темы статьи
# -----------------------
def generate_ai_trend_topic():
    trends = [
        "Multimodal AI - интеграция текста, изображений и аудио",
        "AI агенты - автономные системы выполнения задач",
        "Квантовые вычисления и машинное обучение",
        "Нейроморфные вычисления - энергоэффективные архитектуры",
        "Generative AI - создание контента и кода",
        "Edge AI - обработка данных на устройстве",
        "AI для кибербезопасности",
        "Этичный AI - ответственное использование AI",
        "AI в healthcare - диагностика и персонализированная медицина",
        "Автономные системы - робототехника и беспилотный транспорт",
        "AI оптимизация - ускорение inference",
        "Доверенный AI - объяснимые алгоритмы",
        "AI для климата - оптимизация энергопотребления",
        "Персональные AI ассистенты",
        "AI в образовании - адаптивное обучение"
    ]
    domains = [
        "в веб-разработке и cloud-native приложениях",
        "в мобильных приложениях и IoT",
        "в облачных сервисах и распределенных системах",
        "в анализе больших данных",
        "в кибербезопасности",
        "в медицинской диагностике",
        "в финтехе",
        "в автономных транспортных системах",
        "в smart city",
        "в EdTech"
    ]
    trend = random.choice(trends)
    domain = random.choice(domains)
    return f"{trend} {domain} в 2025 году"

# -----------------------
# Очистка старых статей
# -----------------------
def clean_old_articles(keep_last=3):
    articles = glob.glob("content/posts/*.md")
    if not articles:
        return
    articles.sort(key=os.path.getmtime, reverse=True)
    for f in articles[keep_last:]:
        try:
            os.remove(f)
        except:
            pass

# -----------------------
# Слаг для файлов
# -----------------------
def generate_slug(text):
    text = text.lower()
    text = ''.join(c if c.isalnum() or c==' ' else '-' for c in text)
    text = text.strip('- ')
    text = text.replace(' ', '-')
    while '--' in text:
        text = text.replace('--','-')
    return text[:100]

# -----------------------
# Frontmatter Hugo
# -----------------------
def generate_frontmatter(title, image_url):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    frontmatter = f"""---
title: "{title}"
date: "{now}"
draft: false
tags: ["AI","машинное обучение","технологии","2025"]
categories: ["Искусственный интеллект"]
summary: "Автоматически сгенерированная статья о {title}"
image: "{image_url}"
---
"""
    return frontmatter

# -----------------------
# Генерация статьи через API
# -----------------------
def generate_article_content(topic):
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    groq_key = os.getenv('GROQ_API_KEY')
    
    models_to_try = []
    if groq_key:
        groq_models = ["llama-3.1-8b-instant"]
        for m in groq_models:
            models_to_try.append(lambda m=m: generate_with_groq(groq_key, m, topic))
    if openrouter_key:
        openrouter_models = ["anthropic/claude-3-haiku"]
        for m in openrouter_models:
            models_to_try.append(lambda m=m: generate_with_openrouter(openrouter_key, m, topic))
    
    for func in models_to_try:
        try:
            result = func()
            if result and len(result.strip())>100:
                return result
        except:
            continue
    # fallback
    return f"# {topic}\n\nАвтоматически сгенерированная статья. Контент недоступен через API."

def generate_with_groq(api_key, model_name, topic):
    prompt = f"Напиши статью на тему: {topic} (Markdown, русский, 400-600 слов)"
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}","Content-Type":"application/json"},
        json={"model": model_name, "messages":[{"role":"user","content":prompt}],"max_tokens":1500}
    )
    data = resp.json()
    return data['choices'][0]['message']['content'].strip()

def generate_with_openrouter(api_key, model_name, topic):
    prompt = f"Напиши статью на тему: {topic} (Markdown, русский, 400-600 слов)"
    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}","Content-Type":"application/json"},
        json={"model": model_name, "messages":[{"role":"user","content":prompt}],"max_tokens":1500}
    )
    data = resp.json()
    return data['choices'][0]['message']['content'].strip()

# -----------------------
# Генерация изображения
# -----------------------
def generate_image_deepai(text_prompt):
    key = "98c841c4"  # токен
    try:
        resp = requests.post(
            "https://api.deepai.org/api/text2img",
            data={"text": text_prompt},
            headers={"Api-Key": key},
            timeout=20
        )
        data = resp.json()
        return data.get("output_url")
    except:
        return None

def generate_image_craiyon(text_prompt):
    try:
        resp = requests.post(
            "https://api.craiyon.com/generate",
            json={"prompt": text_prompt},
            timeout=20
        )
        data = resp.json()
        images = data.get("images")
        if images:  # base64
            img_data = base64.b64decode(images[0])
            filename = "static/images/posts/temp_image.png"
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename,'wb') as f:
                f.write(img_data)
            return "/images/posts/temp_image.png"
    except:
        return None

def generate_image_placeholder():
    return "/images/posts/placeholder.png"

# -----------------------
# Основная функция
# -----------------------
def generate_content():
    print("🚀 Запуск генерации контента...")
    clean_old_articles()
    topic = generate_ai_trend_topic()
    print(f"📝 Тема: {topic}")
    
    content = generate_article_content(topic)
    
    # Генерация изображения
    image_url = generate_image_deepai(topic)
    if not image_url:
        image_url = generate_image_craiyon(topic)
    if not image_url:
        image_url = generate_image_placeholder()
    
    slug = generate_slug(topic)
    filename = f"content/posts/{datetime.now().strftime('%Y-%m-%d')}-{slug}.md"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    frontmatter = generate_frontmatter(topic, image_url)
    with open(filename,'w',encoding='utf-8') as f:
        f.write(frontmatter + "\n" + content)
    
    print(f"✅ Статья создана: {filename}")
    return filename

# -----------------------
# Запуск
# -----------------------
if __name__ == "__main__":
    generate_content()
