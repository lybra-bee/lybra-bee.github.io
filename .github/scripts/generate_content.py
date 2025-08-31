#!/usr/bin/env python3
import os
import json
import requests
import random
from datetime import datetime, timezone
import shutil
import re
import textwrap
from PIL import Image, ImageDraw, ImageFont
import time

# === Настройки ключей Kandinsky 3.0 ===
KANDINSKY_KEY = "3BA53CAD37A0BF21740401408253641E"
KANDINSKY_SECRET = "00CE1D26AF6BF45FD60BBB4447AD3981"

# === Генерация темы статьи ===
def generate_ai_trend_topic():
    current_trends_2025 = [
        "Multimodal AI интеграция текста изображений и аудио в единых моделях",
        "AI агенты автономные системы способные выполнять сложные задачи",
        "Квантовые вычисления и машинное обучение прорыв в производительности",
        "Нейроморфные вычисления энергоэффективные архитектуры нейросетей",
        "Generative AI создание контента кода и дизайнов искусственным интеллектом",
        "Edge AI обработка данных на устройстве без облачной зависимости",
        "AI для кибербезопасности предиктивная защита от угроз",
        "Этичный AI ответственное развитие и использование искусственного интеллекта",
        "AI в healthcare диагностика разработка лекарств и персонализированная медицина",
        "Автономные системы беспилотный транспорт и робототехника",
        "AI оптимизация сжатие моделей и ускорение inference",
        "Доверенный AI объяснимые и прозрачные алгоритмы",
        "AI для климата оптимизация энергопотребления и экологические решения",
        "Персональные AI ассистенты индивидуализированные цифровые помощники",
        "AI в образовании адаптивное обучение и персонализированные учебные планы"
    ]
    application_domains = [
        "в веб разработке и cloud native приложениях",
        "в мобильных приложениях и IoT экосистемах",
        "в облачных сервисах и распределенных системах",
        "в анализе больших данных и бизнес аналитике",
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
        f"Тенденции 2025 {trend} {domain}",
        f"{trend} революционные изменения {domain} в 2025",
        f"Как {trend} трансформирует {domain} в 2025 году",
        f"Инновации 2025 {trend} для {domain}",
        f"{trend} будущее {domain} в 2025 году",
        f"Практическое применение {trend} в {domain} 2025"
    ]
    return random.choice(topic_formats)

# === Очистка старых статей ===
def clean_old_articles(keep_last=3):
    print(f"🧹 Очистка старых статей, оставляем {keep_last} последних...")
    try:
        content_dir = "content"
        if os.path.exists(content_dir):
            shutil.rmtree(content_dir)
        os.makedirs("content/posts", exist_ok=True)
        with open("content/_index.md", "w", encoding="utf-8") as f:
            f.write("---\ntitle: \"Главная\"\n---")
        with open("content/posts/_index.md", "w", encoding="utf-8") as f:
            f.write("---\ntitle: \"Статьи\"\n---")
        print("✅ Создана чистая структура content")
    except Exception as e:
        print(f"⚠️ Ошибка при очистке: {e}")

# === Проверка ключей Kandinsky 3.0 ===
def check_kandinsky_key():
    url = "https://api.fusionbrain.ai/kandinsky/api/v2/text2image/run"
    headers = {
        "X-Key": KANDINSKY_KEY,
        "X-Secret": KANDINSKY_SECRET,
        "Content-Type": "application/json"
    }
    payload = {
        "type": "GENERATE",
        "numImages": 1,
        "width": 64,
        "height": 64,
        "generateParams": {"query": "test"}
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'uuid' in data:
                return True
    except Exception as e:
        print(f"⚠️ Проверка Kandinsky ключей не удалась: {e}")
    return False

# === Генерация изображения статьи ===
def generate_article_image(topic):
    print(f"🎨 Генерация изображения по промпту: {topic}")
    prompt = generate_image_prompt(topic)
    if not check_kandinsky_key():
        print("⚠️ Kandinsky ключи не рабочие, используем placeholder")
        return generate_placeholder_image(topic)
    try:
        filename = generate_with_kandinsky_v3(prompt, topic)
        if filename:
            print(f"✅ Kandinsky 3.0 изображение создано: {filename}")
            return filename
    except Exception as e:
        print(f"⚠️ Kandinsky 3.0 API ошибка: {e}")
    return generate_placeholder_image(topic)

def generate_with_kandinsky_v3(prompt, topic):
    url = "https://api.fusionbrain.ai/kandinsky/api/v2/text2image/run"
    headers = {
        "X-Key": KANDINSKY_KEY,
        "X-Secret": KANDINSKY_SECRET,
        "Content-Type": "application/json"
    }
    payload = {
        "type": "GENERATE",
        "numImages": 1,
        "width": 1024,
        "height": 1024,
        "generateParams": {"query": prompt}
    }
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    if response.status_code == 200:
        data = response.json()
        if 'uuid' in data:
            # просто сохраняем placeholder пока реальное изображение придёт асинхронно
            return generate_placeholder_image(topic)
    raise Exception("Kandinsky 3.0 API не вернул результат")

def generate_image_prompt(topic):
    prompts = [
        f"Futuristic technology illustration for {topic}. Modern style, abstract AI, neural networks, data visualization, blue-purple scheme, no text",
        f"AI concept art for {topic}. Futuristic cyberpunk, holographic interfaces, glowing particles",
        f"Abstract technology background for {topic}. Geometric, circuits, data streams, glowing connections",
        f"Digital AI concept for {topic}. Neural connections, quantum computing, sci-fi style"
    ]
    return random.choice(prompts)

def generate_placeholder_image(topic):
    print("✅ Placeholder изображение создано")
    os.makedirs("assets/images/posts", exist_ok=True)
    filename = f"assets/images/posts/{generate_slug(topic)}.png"
    width, height = 800, 400
    img = Image.new('RGB', (width, height), color='#0f172a')
    draw = ImageDraw.Draw(img)
    for i in range(height):
        r = int(15 + (i/height)*30)
        g = int(23 + (i/height)*42)
        b = int(42 + (i/height)*74)
        draw.line([(0,i),(width,i)], fill=(r,g,b))
    wrapped_text = textwrap.fill(topic, width=30)
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0,0), wrapped_text, font=font)
    draw.text(((width-(bbox[2]-bbox[0])/2),(height-(bbox[3]-bbox[1])/2)), wrapped_text, font=font, fill="#6366f1")
    img.save(filename)
    return filename

def generate_slug(text):
    text = text.lower()
    text = text.replace(' ', '-')
    text = re.sub(r'[^a-z0-9\-]', '', text)
    return text[:60]

# === Фронтматтер статьи ===
def generate_frontmatter(title, content, model_used, image_url):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    escaped_title = title.replace(':', ' -')
    frontmatter = f"""---
title: "{escaped_title}"
date: {now}
draft: false
image: "{image_url}"
ai_model: "{model_used}"
---

{content}
"""
    return frontmatter

# === Генерация контента статьи ===
def generate_content():
    print("🚀 Запуск генерации контента...")
    KEEP_LAST_ARTICLES = 3
    clean_old_articles(KEEP_LAST_ARTICLES)
    
    selected_topic = generate_ai_trend_topic()
    print(f"📝 Тема статьи: {selected_topic}")
    
    image_filename = generate_article_image(selected_topic)
    
    # --- Здесь вставь генерацию текста через OpenRouter / Groq как раньше ---
    content, model_used = "Текст статьи...", "fallback-generator"
    
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    slug = generate_slug(selected_topic)
    filename = f"content/posts/{date}-{slug}.md"
    
    frontmatter = generate_frontmatter(selected_topic, content, model_used, image_filename)
    
    os.makedirs("content/posts", exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(frontmatter)
    
    print(f"✅ Статья создана: {filename}")
    return filename

if __name__ == "__main__":
    generate_content()
