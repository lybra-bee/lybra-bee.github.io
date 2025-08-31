#!/usr/bin/env python3
import os
import json
import random
from datetime import datetime, timezone
import shutil
import re
import textwrap
from PIL import Image, ImageDraw, ImageFont
import time
import logging
import base64
import openai

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Проверка ключа OpenAI
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_KEY:
    logger.error("❌ OPENAI_API_KEY не установлен")
    exit(1)
openai.api_key = OPENAI_KEY

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
    logger.info(f"🧹 Очистка старых статей, оставляем {keep_last} последних...")
    content_dir = "content"
    posts_dir = os.path.join(content_dir, "posts")
    if os.path.exists(posts_dir):
        posts = sorted([f for f in os.listdir(posts_dir) if f.endswith('.md')], reverse=True)
        for post in posts[keep_last:]:
            os.remove(os.path.join(posts_dir, post))
            logger.info(f"🗑️ Удален старый пост: {post}")
    else:
        os.makedirs(posts_dir, exist_ok=True)
        with open("content/_index.md", "w", encoding="utf-8") as f:
            f.write("---\ntitle: \"Главная\"\n---")
        with open("content/posts/_index.md", "w", encoding="utf-8") as f:
            f.write("---\ntitle: \"Статьи\"\n---")
        logger.info("✅ Создана структура content")

# ======== Генерация текста через OpenAI GPT ========
def generate_article_content(topic):
    prompt = f"""
Напиши развернутую статью на тему: '{topic}' на русском языке.
Требования:
- Формат Markdown
- 400-600 слов
- Структура: введение, основные разделы, заключение
- Профессиональный стиль
- Конкретные примеры и кейсы
"""
    logger.info(f"📝 Генерация текста через OpenAI GPT")
    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000
        )
        content = response.choices[0].message.content.strip()
        return content, "OpenAI GPT-4"
    except Exception as e:
        logger.error(f"❌ Ошибка генерации текста: {e}")
        return generate_fallback_content(topic), "fallback-generator"

def generate_fallback_content(topic):
    sections = [
        f"# {topic}",
        "",
        "## Введение",
        f"Тема '{topic}' становится increasingly important в 2025 году.",
        "",
        "## Основные тенденции",
        "- Автоматизация процессов разработки",
        "- Интеграция AI в существующие workflow",
        "- Улучшение качества и скорости разработки",
        "",
        "## Практическое применение",
        "Компании внедряют AI решения для оптимизации своих процессов.",
        "",
        "## Заключение",
        "Будущее выглядит promising с развитием AI технологий.",
        "",
        "*Статья сгенерирована автоматически*"
    ]
    return "\n".join(sections)

# ======== Генерация изображения через DALL·E ========
def generate_article_image(topic):
    prompt = f"{topic}, digital art, futuristic, AI technology, 4k, high quality, trending"
    logger.info(f"🎨 Генерация изображения через OpenAI DALL·E: {topic}")
    try:
        response = openai.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1024"
        )
        image_base64 = response.data[0].b64_json
        image_bytes = base64.b64decode(image_base64)
        return save_image_bytes(image_bytes, topic)
    except Exception as e:
        logger.error(f"❌ Ошибка генерации изображения: {e}")
        return generate_enhanced_placeholder(topic)

def save_image_bytes(image_data, topic):
    try:
        os.makedirs("assets/images/posts", exist_ok=True)
        filename = f"assets/images/posts/{generate_slug(topic)}.png"
        with open(filename, "wb") as f:
            f.write(image_data)
        logger.info(f"💾 Изображение сохранено: {filename}")
        return filename
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения: {e}")
        return None

def generate_enhanced_placeholder(topic):
    os.makedirs("assets/images/posts", exist_ok=True)
    filename = f"assets/images/posts/{generate_slug(topic)}.png"
    width, height = 800, 400
    img = Image.new('RGB', (width, height), color='#0f172a')
    draw = ImageDraw.Draw(img)
    for i in range(height):
        r = int(15 + (i/height)*40)
        g = int(23 + (i/height)*60)
        b = int(42 + (i/height)*100)
        draw.line([(0, i), (width, i)], fill=(r, g, b))
    wrapped_text = textwrap.fill(topic, width=35)
    try:
        font = ImageFont.truetype("Arial.ttf", 22)
    except:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), wrapped_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (width - text_width) / 2
    y = (height - text_height) / 2
    draw.text((x+3, y+3), wrapped_text, font=font, fill="#000000")
    draw.text((x, y), wrapped_text, font=font, fill="#ffffff")
    img.save(filename)
    logger.info(f"💾 Placeholder изображение сохранено: {filename}")
    return filename

# ======== Помощь: slug и frontmatter ========
def generate_slug(text):
    slug = re.sub(r'[^\w\s-]', '', text).strip().lower()
    slug = re.sub(r'[\s_-]+', '-', slug)
    return slug

def generate_frontmatter(title, content, model_used, image_filename):
    frontmatter = f"""---
title: "{title}"
date: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}
image: "{image_filename}"
model: "{model_used}"
---
{content}
"""
    return frontmatter

# ======== Генерация статьи ========
def generate_content():
    logger.info("🚀 Запуск генерации контента...")
    clean_old_articles()
    topic = generate_ai_trend_topic()
    logger.info(f"📝 Тема: {topic}")
    image_filename = generate_article_image(topic)
    content, model_used = generate_article_content(topic)
    slug = generate_slug(topic)
    filename = f"content/posts/{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-{slug}.md"
    frontmatter = generate_frontmatter(topic, content, model_used, image_filename)
    os.makedirs("content/posts", exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(frontmatter)
    logger.info(f"✅ Статья создана: {filename}")
    return filename

# ======== Главная точка ========
if __name__ == "__main__":
    generate_content()
