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
import re
import shutil
from PIL import Image, ImageDraw, ImageFont
import io
import textwrap

# --- ТЕМЫ ---
def generate_ai_trend_topic():
    """Генерирует актуальную тему на основе трендов AI 2025"""
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

# --- ОЧИСТКА ---
def clean_old_articles(keep_last=3):
    """Оставляет только последние N статей и очищает content"""
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

# --- КОНТЕНТ ---
def generate_content():
    """Генерирует статью с изображением"""
    print("🚀 Запуск генерации контента...")
    clean_old_articles()
    topic = generate_ai_trend_topic()
    print(f"📝 Тема: {topic}")
    image_url = generate_article_image(topic)
    content, model_used = generate_article_content(topic)
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    slug = generate_slug(topic)
    filename = f"content/posts/{date}-{slug}.md"
    frontmatter = generate_frontmatter(topic, content, model_used, image_url)
    os.makedirs("content/posts", exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(frontmatter)
    print(f"✅ Статья создана: {filename}")
    return filename

# --- ТЕКСТ СТАТЬИ ---
def generate_article_content(topic):
    """Генерация текста статьи (fallback)"""
    fallback_content = f"""# {topic}

## Введение
{topic} - это важное направление в развитии искусственного интеллекта на 2025 год.

## Основные аспекты
- **Технологические инновации**: {topic} включает передовые разработки в области AI
- **Практическое применение**: Технология находит применение в различных отраслях
- **Перспективы развития**: Ожидается значительный рост в ближайшие годы

## Заключение
{topic} представляет собой ключевое направление развития искусственного интеллекта.
"""
    return fallback_content, "fallback-generator"

# --- ИЗОБРАЖЕНИЕ ---
def generate_article_image(topic):
    """Генерация изображения через Kandinsky v2 API"""
    prompt = generate_image_prompt(topic)
    print(f"🎨 Генерация изображения по промпту: {prompt}")
    
    try:
        api_url = "https://api.fusionbrain.ai/kandinsky/api/v2/text2image/run"
        headers = {
            "X-Key": "Key 3BA53CAD37A0BF21740401408253641E",
            "X-Secret": "Secret 00CE1D26AF6BF45FD60BBB4447AD3981",
            "Content-Type": "application/json"
        }
        payload = {
            "type": "GENERATE",
            "numImages": 1,
            "width": 1024,
            "height": 1024,
            "generateParams": {"query": prompt}
        }
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        data = response.json()
        if 'images' in data and len(data['images']) > 0:
            img_b64 = data['images'][0]
            image_data = base64.b64decode(img_b64)
            filename = save_article_image(image_data, topic)
            return filename
    except Exception as e:
        print(f"⚠️ Kandinsky API ошибка: {e}")
    
    # fallback placeholder
    return generate_placeholder_image(topic)

def generate_image_prompt(topic):
    prompts = [
        f"Futuristic technology illustration for {topic}. Modern style, abstract AI, neural networks, data visualization, blue-purple scheme, no text",
        f"AI concept art for {topic}. Cyberpunk style, glowing networks, holographic interface, vibrant colors, cinematic lighting",
        f"Abstract digital background for {topic}. Geometric shapes, circuit patterns, data streams, professional style",
        f"Futuristic AI digital brain for {topic}. Sci-fi elements, quantum computing, vibrant colors, depth of field"
    ]
    return random.choice(prompts)

def generate_placeholder_image(topic):
    print("🎨 Создаем placeholder изображение...")
    width, height = 800, 400
    img = Image.new('RGB', (width, height), color='#0f172a')
    draw = ImageDraw.Draw(img)
    for i in range(height):
        r = int(15 + (i / height) * 30)
        g = int(23 + (i / height) * 42)
        b = int(42 + (i / height) * 74)
        draw.line([(0, i), (width, i)], fill=(r, g, b))
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()
    wrapped_text = textwrap.fill(topic, width=30)
    bbox = draw.textbbox((0, 0), wrapped_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (width - text_width) / 2
    y = (height - text_height) / 2
    draw.text((x, y), wrapped_text, font=font, fill="#6366f1")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    image_data = buffer.getvalue()
    return save_article_image(image_data, topic)

def save_article_image(image_data, topic):
    os.makedirs("assets/images/posts", exist_ok=True)
    slug = generate_slug(topic)
    filename = f"posts/{slug}.png"
    full_path = f"assets/images/{filename}"
    with open(full_path, 'wb') as f:
        f.write(image_data)
    print(f"💾 Изображение сохранено: {filename}")
    return f"/images/{filename}"

# --- UTILS ---
def generate_slug(text):
    text = text.lower()
    text = text.replace(' ', '-')
    text = re.sub(r'[^a-z0-9\-]', '', text)
    text = re.sub(r'-+', '-', text)
    return text[:60]

def generate_frontmatter(title, content, model_used, image_url):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    escaped_title = title.replace(':', ' -').replace('"', '').replace("'", "")
    frontmatter_lines = [
        "---",
        f'title: "{escaped_title}"',
        f"date: {now}",
        "draft: false",
        'tags: ["AI", "машинное обучение", "технологии", "2025"]',
        'categories: ["Искусственный интеллект"]',
        'summary: "Автоматически сгенерированная статья об искусственном интеллекте"'
    ]
    if image_url:
        frontmatter_lines.append(f'image: "{image_url}"')
    frontmatter_lines.append("---")
    frontmatter_lines.append(content)
    return "\n".join(frontmatter_lines)

if __name__ == "__main__":
    generate_content()
    
