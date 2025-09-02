#!/usr/bin/env python3
import os
import json
import random
from datetime import datetime, timezone
import re
import textwrap
from PIL import Image, ImageDraw, ImageFont
import logging
import base64
import requests

# ===== Настройка логирования =====
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ===== Ключи API =====
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
GROQ_KEY = os.getenv("GROQ_API_KEY")
FALAI_KEY = os.getenv("FAL_API_KEY")

# ===== Генерация темы =====
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

# ===== Очистка старых статей =====
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

# ===== Генерация текста через OpenRouter/Groq =====
def generate_article_content(topic):
    logger.info(f"📝 Генерация текста для темы: {topic}")
    # Пример запроса к OpenRouter
    if OPENROUTER_KEY:
        try:
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"}
            data = {
                "model": "gpt-4",
                "messages": [{"role": "user", "content": f"Напиши статью на русском на тему: {topic}, 400-600 слов, Markdown"}],
                "temperature": 0.7
            }
            resp = requests.post(url, headers=headers, json=data, timeout=60)
            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"]
                return content, "OpenRouter GPT"
        except Exception as e:
            logger.warning(f"⚠️ OpenRouter не сработал: {e}")
    # fallback
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

# ===== Генерация изображений через FAL AI =====
def generate_article_image(topic):
    prompt = f"{topic}, digital art, futuristic, AI technology, 4k, high quality, trending"
    os.makedirs("assets/images/posts", exist_ok=True)
    filename = f"assets/images/posts/{generate_slug(topic)}.png"

    if FALAI_KEY:
        try:
            url = "https://api.fal.ai/generate-image"
            headers = {"Authorization": f"Bearer {FALAI_KEY}", "Content-Type": "application/json"}
            data = {"prompt": prompt, "size": "1024x1024"}
            resp = requests.post(url, headers=headers, json=data, timeout=60)
            if resp.status_code == 200:
                img_data = base64.b64decode(resp.json()["image_base64"])
                with open(filename, "wb") as f:
                    f.write(img_data)
                logger.info(f"✅ Изображение получено через FAL AI: {filename}")
                return filename
        except Exception as e:
            logger.warning(f"⚠️ FAL AI не сработал: {e}")

    return generate_enhanced_placeholder(topic)

# ===== Плейсхолдер =====
def generate_enhanced_placeholder(topic):
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

# ===== Вспомогательные =====
def generate_slug(text, max_length=60):
    slug = re.sub(r'[^\w\s-]', '', text).strip().lower()
    slug = re.sub(r'[\s_-]+', '-', slug)
    if len(slug) > max_length:
        slug = slug[:max_length].rstrip('-')
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

# ===== Генерация статьи =====
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

# ===== Главная точка =====
if __name__ == "__main__":
    generate_content()
