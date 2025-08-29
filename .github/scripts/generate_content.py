#!/usr/bin/env python3
import os
import json
import requests
import random
from datetime import datetime, timezone
import glob
import base64
import time

# ---------- Тема статьи ----------
def generate_ai_trend_topic():
    trends = [
        "Multimodal AI - интеграция текста, изображений и аудио",
        "AI агенты - автономные системы",
        "Generative AI - создание контента и кода",
        "Edge AI - обработка данных на устройстве",
        "AI для кибербезопасности",
        "AI в healthcare",
        "AI в образовании"
    ]
    domains = [
        "в веб-разработке",
        "в мобильных приложениях",
        "в облачных сервисах",
        "в бизнес-аналитике",
        "в медицинской диагностике",
        "в образовательных технологиях"
    ]
    trend = random.choice(trends)
    domain = random.choice(domains)
    return f"{trend} {domain} в 2025 году"

# ---------- Очистка старых статей ----------
def clean_old_articles(keep_last=3):
    print(f"🧹 Очистка старых статей, оставляем {keep_last} последних...")
    articles = glob.glob("content/posts/*.md")
    if not articles:
        return
    articles.sort(key=os.path.getmtime, reverse=True)
    for a in articles[keep_last:]:
        try:
            os.remove(a)
            print(f"❌ Удалено: {os.path.basename(a)}")
        except Exception as e:
            print(f"⚠️ Ошибка удаления {a}: {e}")

# ---------- Генерация статьи ----------
def generate_article_content(topic):
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    groq_key = os.getenv('GROQ_API_KEY')

    models = []
    if groq_key:
        groq_models = ["llama-3.1-8b-instant"]
        for m in groq_models:
            models.append((f"Groq-{m}", lambda m=m: generate_with_groq(groq_key, m, topic)))
    if openrouter_key:
        openrouter_models = ["anthropic/claude-3-haiku"]
        for m in openrouter_models:
            models.append((m, lambda m=m: generate_with_openrouter(openrouter_key, m, topic)))

    for name, func in models:
        try:
            print(f"🔄 Пробуем: {name}")
            content = func()
            if content and len(content.strip()) > 100:
                print(f"✅ Успешно через {name}")
                return content, name
            time.sleep(1)
        except Exception as e:
            print(f"⚠️ Ошибка {name}: {e}")
    # fallback
    print("⚠️ Все API недоступны, создаем заглушку")
    fallback = f"# {topic}\n\nЭто автоматически сгенерированная статья о {topic}."
    return fallback, "fallback"

# ---------- Генерация через Groq ----------
def generate_with_groq(api_key, model_name, topic):
    prompt = f"Напиши развернутую техническую статью на тему: {topic}"
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model_name, "messages":[{"role":"user","content":prompt}], "max_tokens":1500},
        timeout=30
    )
    if response.status_code == 200:
        data = response.json()
        return data['choices'][0]['message']['content'].strip()
    raise Exception(f"HTTP {response.status_code}: {response.text[:200]}")

# ---------- Генерация через OpenRouter ----------
def generate_with_openrouter(api_key, model_name, topic):
    prompt = f"Напиши техническую статью на тему: {topic}"
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model_name, "messages":[{"role":"user","content":prompt}], "max_tokens":1500},
        timeout=30
    )
    if response.status_code == 200:
        data = response.json()
        return data['choices'][0]['message']['content'].strip()
    raise Exception(f"HTTP {response.status_code}")

# ---------- Генерация изображения ----------
def generate_image(text, filename):
    generators = [generate_image_openrouter, generate_image_craiyon, generate_image_deepai]
    for gen in generators:
        try:
            result = gen(text, filename)
            if result:
                return result
        except Exception as e:
            print(f"⚠️ Ошибка генерации через {gen.__name__}: {e}")
    print("❌ Все генераторы не сработали")
    return None

# OpenRouter Images
def generate_image_openrouter(text, filename):
    key = os.getenv('OPENROUTER_API_KEY')
    if not key:
        raise Exception("Нет OPENROUTER_API_KEY")
    prompt = text
    response = requests.post(
        "https://openrouter.ai/api/v1/images/generations",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model":"openai-image-1","prompt":prompt,"size":"1024x1024","n":1},
        timeout=30
    )
    if response.status_code == 200:
        data = response.json()
        img_data = data['data'][0]['b64_json']
        with open(filename, 'wb') as f:
            f.write(base64.b64decode(img_data))
        print(f"✅ Изображение сохранено: {filename}")
        return filename
    raise Exception(f"HTTP {response.status_code}")

# Craiyon (без токена)
def generate_image_craiyon(text, filename):
    response = requests.post("https://backend.craiyon.com/generate", json={"prompt": text})
    if response.status_code == 200:
        img_data = response.json()['images'][0]
        with open(filename, 'wb') as f:
            f.write(base64.b64decode(img_data))
        print(f"✅ Изображение сохранено (Craiyon): {filename}")
        return filename
    return None

# DeepAI (с бесплатным токеном)
def generate_image_deepai(text, filename):
    token = "6d27650a"
    response = requests.post(
        "https://api.deepai.org/api/text2img",
        data={"text": text},
        headers={"api-key": token}
    )
    if response.status_code == 200:
        data = response.json()
        img_url = data.get("output_url")
        if img_url:
            img_data = requests.get(img_url).content
            with open(filename, 'wb') as f:
                f.write(img_data)
            print(f"✅ Изображение сохранено (DeepAI): {filename}")
            return filename
    return None

# ---------- Генерация slug ----------
def generate_slug(text):
    text = text.lower()
    text = ''.join(c for c in text if c.isalnum() or c in ' -')
    text = text.replace(' ','-').replace('--','-')
    return text[:100]

# ---------- Генерация frontmatter ----------
def generate_frontmatter(title, content, image_filename):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    fm = f"""---
title: "{title}"
date: {now}
draft: false
tags: ["AI","Технологии","2025"]
categories: ["Искусственный интеллект"]
image: "/{image_filename}"  # подтягивается в блог
summary: "Автоматически сгенерированная статья о {title}"
---
{content}
"""
    return fm

# ---------- Основная функция ----------
def generate_content():
    print("🚀 Запуск генерации контента...")
    clean_old_articles(keep_last=3)

    topic = generate_ai_trend_topic()
    print(f"📝 Тема: {topic}")
    
    content, model = generate_article_content(topic)

    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    slug = generate_slug(topic)
    filename_md = f"content/posts/{date}-{slug}.md"
    image_filename = f"static/images/posts/{slug}.png"
    os.makedirs("content/posts", exist_ok=True)
    os.makedirs("static/images/posts", exist_ok=True)

    # Генерация изображения
    generate_image(content, image_filename)

    # Сохраняем статью с frontmatter
    frontmatter = generate_frontmatter(topic, content, f"images/posts/{slug}.png")
    with open(filename_md,'w',encoding='utf-8') as f:
        f.write(frontmatter)
    print(f"✅ Статья создана: {filename_md}")
    return filename_md

if __name__ == "__main__":
    generate_content()
