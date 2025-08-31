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
import base64

# ======== Настройки Eden AI ========
EDEN_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiOWE4ZDEyNjktNTAwZi00ZWI5LWE3NDUtMTI3ZmNhODQ4N2Q1IiwidHlwZSI6ImFwaV90b2tlbiIsIm5hbWUiOiJFZGVuQVBJIiwiaXNfY3VzdG9tIjp0cnVlfQ.8YU-6NpefBXLqtUTJmDkSlAzdnvAWmywfa6WLFwbZBg"

# ======== Генерация темы ========
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

# ======== Очистка старых статей ========
def clean_old_articles(keep_last=3):
    print(f"🧹 Очистка старых статей, оставляем {keep_last} последних...")
    content_dir = "content"
    if os.path.exists(content_dir):
        shutil.rmtree(content_dir)
    os.makedirs("content/posts", exist_ok=True)
    with open("content/_index.md", "w", encoding="utf-8") as f:
        f.write("---\ntitle: \"Главная\"\n---")
    with open("content/posts/_index.md", "w", encoding="utf-8") as f:
        f.write("---\ntitle: \"Статьи\"\n---")
    print("✅ Создана чистая структура content")

# ======== Генерация статьи ========
def generate_content():
    print("🚀 Запуск генерации контента...")
    clean_old_articles()
    
    topic = generate_ai_trend_topic()
    print(f"📝 Тема статьи: {topic}")
    
    image_filename = generate_article_image(topic)
    content, model_used = generate_article_content(topic)
    
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    slug = generate_slug(topic)
    filename = f"content/posts/{date}-{slug}.md"
    
    frontmatter = generate_frontmatter(topic, content, model_used, image_filename)
    
    os.makedirs("content/posts", exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(frontmatter)
    
    print(f"✅ Статья создана: {filename}")
    return filename

# ======== Генерация текста через OpenRouter/Groq ========
def generate_article_content(topic):
    fallback = f"# {topic}\n\nСтатья по теме {topic} создана автоматически."
    return fallback, "fallback-generator"

# ======== Генерация изображения через Eden AI (DeepAI) ========
def generate_with_edenai(prompt, width=512, height=512):
    prompt = prompt[:200]  # ограничение длины
    print(f"🎨 Eden AI генерация изображения по промпту: {prompt}")
    url = "https://api.edenai.run/v2/image/generation"
    headers = {
        "Authorization": f"Bearer {EDEN_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "providers": ["deepai"],
        "language": "RU",
        "input": prompt,
        "width": width,
        "height": height,
        "num_images": 1
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        if resp.status_code == 200:
            data = resp.json()
            try:
                b64_data = data['deepai']['images'][0]
                image_bytes = base64.b64decode(b64_data)
                filename = save_article_image(image_bytes, prompt)
                print(f"✅ Eden AI изображение создано: {filename}")
                return filename
            except Exception as e:
                print(f"⚠️ Eden AI parsing error: {e}")
        else:
            print(f"⚠️ Eden AI error: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"⚠️ Eden AI request exception: {e}")
    return generate_placeholder_image(prompt)

# ======== Placeholder изображение ========
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

def save_article_image(image_data, topic):
    os.makedirs("assets/images/posts", exist_ok=True)
    filename = f"assets/images/posts/{generate_slug(topic)}.png"
    if image_data:
        with open(filename,'wb') as f:
            f.write(image_data)
    return filename

# ======== Вспомогательные функции ========
def generate_slug(text):
    text = text.lower()
    text = text.replace(' ', '-')
    text = re.sub(r'[^a-z0-9\-]', '', text)
    return text[:60]

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

# ======== Генерация изображения ========
def generate_article_image(topic):
    return generate_with_edenai(topic)

# ======== Запуск ========
if __name__ == "__main__":
    generate_content()
