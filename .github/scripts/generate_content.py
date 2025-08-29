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

# --- Настройки ---
KEEP_LAST_ARTICLES = 3
DEEP_AI_KEY = "98c841c4"  # токен для DeepAI

# --- Генерация актуальной темы ---
def generate_ai_trend_topic():
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

# --- Генерация статьи через API ---
def generate_article_content(topic):
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    groq_key = os.getenv('GROQ_API_KEY')
    
    models_to_try = []
    if groq_key:
        groq_models = ["llama-3.1-8b-instant","llama-3.2-1b-preview","mixtral-8x7b-32768"]
        for model_name in groq_models:
            models_to_try.append((f"Groq-{model_name}", lambda m=model_name: generate_with_groq(groq_key, m, topic)))
    if openrouter_key:
        openrouter_models = ["anthropic/claude-3-haiku","google/gemini-pro","meta-llama/llama-3-8b-instruct"]
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
            print(f"⚠️ Ошибка {model_name}: {str(e)[:100]}")
            continue
    
    print("⚠️ Все API недоступны, создаем заглушку")
    fallback_content = f"# {topic}\n\nАвтоматически сгенерированная статья по теме {topic}."
    return fallback_content, "fallback-generator"

def generate_with_groq(api_key, model_name, topic):
    prompt = f"Напиши техническую статью на тему: '{topic}' на русском языке, 400-600 слов."
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Content-Type":"application/json","Authorization":f"Bearer {api_key}"},
        json={"model": model_name, "messages":[{"role":"user","content":prompt}],"max_tokens":1500,"temperature":0.7}
    )
    if response.status_code == 200:
        data = response.json()
        return data['choices'][0]['message']['content'].strip()
    raise Exception(f"HTTP {response.status_code}: {response.text[:200]}")

def generate_with_openrouter(api_key, model_name, topic):
    prompt = f"Напиши техническую статью на тему: '{topic}' на русском языке, 400-600 слов."
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Content-Type":"application/json","Authorization":f"Bearer {api_key}"},
        json={"model": model_name, "messages":[{"role":"user","content":prompt}],"max_tokens":1500,"temperature":0.7}
    )
    if response.status_code == 200:
        data = response.json()
        return data['choices'][0]['message']['content'].strip()
    raise Exception(f"HTTP {response.status_code}")

# --- Генерация изображений ---
def generate_image(topic):
    # Перебор бесплатных генераторов в порядке приоритета
    generators = [
        generate_image_deepai,
        generate_image_craiyon,
        generate_image_lexica
    ]
    for gen in generators:
        try:
            url = gen(topic)
            if url:
                print(f"✅ Изображение сгенерировано через {gen.__name__}")
                return url
        except Exception as e:
            print(f"⚠️ Ошибка генерации через {gen.__name__}: {e}")
            continue
    print("❌ Все генераторы не сработали, используем placeholder")
    return "https://via.placeholder.com/800x450.png?text=AI+Image"

def generate_image_deepai(topic):
    response = requests.post(
        "https://api.deepai.org/api/text2img",
        headers={"api-key": DEEP_AI_KEY},
        data={"text": topic}
    )
    if response.status_code == 200:
        data = response.json()
        return data.get("output_url")
    raise Exception(f"HTTP {response.status_code}: {response.text[:200]}")

def generate_image_craiyon(topic):
    response = requests.post(
        "https://backend.craiyon.com/generate",
        json={"prompt": topic}
    )
    if response.status_code == 200:
        data = response.json()
        if data.get("images"):
            return data["images"][0]
    raise Exception(f"HTTP {response.status_code}")

def generate_image_lexica(topic):
    # Только пример, может не работать без токена
    response = requests.get(f"https://lexica.art/api/v1/search?q={urllib.parse.quote(topic)}")
    if response.status_code == 200:
        data = response.json()
        if data.get("images"):
            return data["images"][0]["src"]
    raise Exception(f"HTTP {response.status_code}")

# --- Вспомогательные функции ---
def generate_slug(text):
    text = text.lower()
    text = ''.join(c for c in text if c.isalnum() or c in ' -')
    text = text.replace(' ', '-').replace('--','-')
    return text[:100]

def generate_frontmatter(title, content, model_used, image_url):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    frontmatter = f"""---
title: "{title}"
date: {now}
draft: false
tags: ["AI","машинное обучение","технологии","2025"]
categories: ["Искусственный интеллект"]
summary: "Автоматически сгенерированная статья об искусственном интеллекте"
image: "{image_url}"
---
{content}
"""
    return frontmatter

def clean_old_articles(keep_last=KEEP_LAST_ARTICLES):
    print(f"🧹 Очистка старых статей, оставляем {keep_last} последних...")
    try:
        articles = glob.glob("content/posts/*.md")
        if not articles:
            return
        articles.sort(key=os.path.getmtime, reverse=True)
        for article_path in articles[keep_last:]:
            try:
                os.remove(article_path)
                print(f"❌ Удалено: {os.path.basename(article_path)}")
            except Exception as e:
                print(f"⚠️ Ошибка удаления {article_path}: {e}")
    except Exception as e:
        print(f"⚠️ Ошибка при очистке: {e}")

# --- Основная функция ---
def generate_content():
    print("🚀 Запуск генерации контента...")
    clean_old_articles()
    topic = generate_ai_trend_topic()
    print(f"📝 Тема: {topic}")
    content, model_used = generate_article_content(topic)
    image_url = generate_image(topic)
    slug = generate_slug(topic)
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    filename = f"content/posts/{date}-{slug}.md"
    frontmatter = generate_frontmatter(topic, content, model_used, image_url)
    os.makedirs("content/posts", exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(frontmatter)
    print(f"✅ Статья создана: {filename}")
    return filename

if __name__ == "__main__":
    generate_content()
