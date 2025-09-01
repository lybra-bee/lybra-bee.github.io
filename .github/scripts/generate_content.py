#!/usr/bin/env python3
import os
import json
import random
from datetime import datetime, timezone
import shutil
import re
import textwrap
from PIL import Image, ImageDraw, ImageFont
import logging
import base64
import requests
import openai

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Ключи из секретов GitHub
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
FAL_API_KEY = os.getenv("FAL_API_KEY")

if OPENAI_KEY:
    openai.api_key = OPENAI_KEY

# ======== Генерация темы ========
def generate_ai_trend_topic():
    trends = [
        "Multimodal AI интеграция текста изображений и аудио",
        "AI агенты автономные системы",
        "Квантовые вычисления и машинное обучение",
        "Нейроморфные вычисления энергоэффективные архитектуры",
        "Generative AI создание контента и дизайнов",
        "Edge AI обработка данных на устройстве",
        "AI для кибербезопасности",
        "Этичный AI ответственное развитие",
        "AI в healthcare и персонализированная медицина",
        "Автономные системы и робототехника"
    ]
    domains = [
        "в веб разработке и cloud native приложениях",
        "в мобильных приложениях и IoT экосистемах",
        "в анализе больших данных и бизнес аналитике",
        "в компьютерной безопасности и киберзащите",
        "в образовательных технологиях и EdTech"
    ]
    trend = random.choice(trends)
    domain = random.choice(domains)
    return f"{trend} {domain} в 2025 году"

# ======== Очистка старых статей ========
def clean_old_articles(keep_last=3):
    posts_dir = "content/posts"
    if os.path.exists(posts_dir):
        posts = sorted([f for f in os.listdir(posts_dir) if f.endswith('.md')], reverse=True)
        for post in posts[keep_last:]:
            os.remove(os.path.join(posts_dir, post))
            logger.info(f"🗑️ Удален старый пост: {post}")
    else:
        os.makedirs(posts_dir, exist_ok=True)
        os.makedirs("content", exist_ok=True)
        with open("content/_index.md", "w", encoding="utf-8") as f:
            f.write("---\ntitle: \"Главная\"\n---")
        with open("content/posts/_index.md", "w", encoding="utf-8") as f:
            f.write("---\ntitle: \"Статьи\"\n---")
        logger.info("✅ Создана структура content")

# ======== Генерация текста ========
def generate_article_content(topic):
    if not OPENAI_KEY:
        return generate_fallback_content(topic), "fallback-generator"
    prompt = f"Напиши развернутую статью на тему: '{topic}' на русском языке. Формат Markdown, 400-600 слов."
    try:
        resp = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000
        )
        content = resp.choices[0].message.content.strip()
        return content, "OpenAI GPT-4"
    except Exception as e:
        logger.warning(f"❌ OpenAI GPT ошибка: {e}")
        return generate_fallback_content(topic), "fallback-generator"

def generate_fallback_content(topic):
    return f"# {topic}\n\n## Введение\nАвтоматически сгенерированная статья.\n\n## Основное\nКонтент отсутствует.\n\n## Заключение\nСгенерировано fallback."

# ======== Генерация изображения ========
def generate_article_image(topic):
    os.makedirs("assets/images/posts", exist_ok=True)
    filename = f"assets/images/posts/{generate_slug(topic)}.png"

    # 1. FAL API
    if FAL_API_KEY:
        try:
            logger.info("🎨 Пробуем FAL API...")
            url = "https://api.openfml.com/v1/generate-image"
            headers = {"Authorization": f"Bearer {FAL_API_KEY}"}
            resp = requests.post(url, json={"prompt": topic, "size": "1024x1024"}, headers=headers, timeout=60)
            data = resp.json()
            if resp.status_code == 200 and "image" in data:
                img_bytes = base64.b64decode(data["image"])
                with open(filename, "wb") as f:
                    f.write(img_bytes)
                logger.info(f"✅ Изображение получено через FAL API: {filename}")
                return filename
        except Exception as e:
            logger.warning(f"⚠️ FAL API не сработал: {e}")

    # 2. Craiyon (без ключа)
    try:
        logger.info("🎨 Пробуем Craiyon...")
        resp = requests.post("https://api.craiyon.com/v3", json={"prompt": topic}, timeout=60)
        if resp.status_code == 200 and "images" in resp.json():
            img_url = resp.json()["images"][0]
            img_data = requests.get(img_url, timeout=30).content
            with open(filename, "wb") as f:
                f.write(img_data)
            logger.info(f"✅ Изображение получено через Craiyon: {filename}")
            return filename
    except Exception as e:
        logger.warning(f"⚠️ Craiyon не сработал: {e}")

    # 3. OpenAI DALL·E
    if OPENAI_KEY:
        try:
            logger.info("🎨 Пробуем DALL·E...")
            resp = openai.images.generate(model="gpt-image-1", prompt=topic, size="1024x1024")
            img_bytes = base64.b64decode(resp.data[0].b64_json)
            with open(filename, "wb") as f:
                f.write(img_bytes)
            logger.info(f"✅ Изображение получено через DALL·E: {filename}")
            return filename
        except Exception as e:
            logger.warning(f"⚠️ DALL·E не сработал: {e}")

    # 4. Плейсхолдер
    return generate_placeholder(topic, filename)

def generate_placeholder(topic, filename):
    width, height = 800, 400
    img = Image.new("RGB", (width, height), "#0f172a")
    draw = ImageDraw.Draw(img)
    wrapped = textwrap.fill(topic, width=35)
    try:
        font = ImageFont.truetype("Arial.ttf", 22)
    except:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), wrapped, font=font)
    x = (width - (bbox[2]-bbox[0]))/2
    y = (height - (bbox[3]-bbox[1]))/2
    draw.text((x+3, y+3), wrapped, font=font, fill="#000000")
    draw.text((x, y), wrapped, font=font, fill="#ffffff")
    img.save(filename)
    logger.info(f"💾 Placeholder изображение сохранено: {filename}")
    return filename

# ======== Вспомогательные ========
def generate_slug(text):
    slug = re.sub(r"[^\w\s-]", "", text).strip().lower()
    slug = re.sub(r"[\s_-]+", "-", slug)
    return slug

def generate_frontmatter(title, content, model_used, image_filename):
    return f"""---
title: "{title}"
date: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}
image: "{image_filename}"
model: "{model_used}"
---
{content}
"""

# ======== Генерация статьи ========
def generate_content():
    logger.info("🚀 Запуск генерации контента...")
    clean_old_articles()
    topic = generate_ai_trend_topic()
    logger.info(f"📝 Тема: {topic}")
    image_filename = generate_article_image(topic)
    content, model_used = generate_article_content(topic)
    slug = generate_slug(topic)
    os.makedirs("content/posts", exist_ok=True)
    filename = f"content/posts/{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-{slug}.md"
    frontmatter = generate_frontmatter(topic, content, model_used, image_filename)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(frontmatter)
    logger.info(f"✅ Статья создана: {filename}")
    return filename

if __name__ == "__main__":
    generate_content()
