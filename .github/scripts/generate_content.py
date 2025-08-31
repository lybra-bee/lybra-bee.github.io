#!/usr/bin/env python3
import os
import random
import requests
import shutil
import re
import textwrap
import time
import logging
import argparse
import base64
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageFont

# — Настройка логирования —
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# — Генерация случайной темы —
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
    choice = random.choice([
        f"{trend} {domain} в 2025 году",
        f"Тенденции 2025 {trend} {domain}",
        f"{trend} революционные изменения {domain} в 2025",
        f"Как {trend} трансформирует {domain} в 2025 году",
        f"Инновации 2025 {trend} для {domain}",
        f"{trend} будущее {domain} в 2025 году",
        f"Практическое применение {trend} в {domain} 2025"
    ])
    return choice

# — Очистка прошлых статей —
def clean_old_articles(keep_last=3):
    logger.info(f"🧹 Очистка старых статей, оставляем {keep_last}")
    content_dir = "content"
    posts_dir = os.path.join(content_dir, "posts")
    if os.path.isdir(posts_dir):
        posts = sorted([f for f in os.listdir(posts_dir) if f.endswith('.md')], reverse=True)
        for post in posts[keep_last:]:
            os.remove(os.path.join(posts_dir, post))
            logger.info(f"🗑 Удалён пост: {post}")
    else:
        os.makedirs("content/posts", exist_ok=True)
        with open("content/_index.md", "w", encoding="utf-8") as f:
            f.write("---\ntitle: \"Главная\"\n---")
        with open("content/posts/_index.md", "w", encoding="utf-8") as f:
            f.write("---\ntitle: \"Статьи\"\n---")
        logger.info("✅ Создана структура content")

# — Генерация текста через OpenRouter/Groq —
def generate_article_content(topic):
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    groq_key = os.getenv('GROQ_API_KEY')
    models_to_try = []

    if groq_key:
        for m in ["llama-3.1-8b-instant", "llama-3.2-1b-preview"]:
            models_to_try.append((f"Groq-{m}", lambda m=m: gen_with_groq(groq_key, m, topic)))
    if openrouter_key:
        for m in ["anthropic/claude-3-haiku", "google/gemini-pro"]:
            models_to_try.append((f"OpenRouter-{m}", lambda m=m: gen_with_openrouter(openrouter_key, m, topic)))

    if not models_to_try:
        logger.warning("⚠ Нет ключей для генерации текста — fallback")
        return generate_fallback_content(topic), "fallback"

    for name, func in models_to_try:
        try:
            logger.info(f"⏳ Пробуем {name}")
            result = func()
            if result and len(result.strip()) > 150:
                logger.info(f"✅ Успешно через {name}")
                return result, name
        except Exception as e:
            logger.error(f"❌ Ошибка {name}: {e}")

    logger.warning("⚠ Все модели не сработали — fallback")
    return generate_fallback_content(topic), "fallback"

def gen_with_groq(key, model, topic):
    prompt = f"Напиши статью **на русском**, Markdown, 400-600 слов: {topic}"
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}"}, json={
            "model": model,
            "messages":[{"role":"user","content":prompt}],
            "max_tokens":1500
        }, timeout=30
    )
    resp.raise_for_status()
    return resp.json()['choices'][0]['message']['content']

def gen_with_openrouter(key, model, topic):
    prompt = f"Напиши статью **на русском**, Markdown, ~500 слов: {topic}"
    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}"}, json={
            "model": model,
            "messages":[{"role":"user","content":prompt}],
            "max_tokens":1500
        }, timeout=30
    )
    resp.raise_for_status()
    return resp.json()['choices'][0]['message']['content']

def generate_fallback_content(topic):
    return f"# {topic}\n\nАвтоматически сгенерированная статья."

# — Генерация изображений через Eden AI —
EDENAI_KEY = os.getenv("EDENAI_API_KEY")
EDENAI_PROVIDERS = ["craiyon", "deepai", "dalle-mini"]

def generate_article_image(topic):
    logger.info(f"🎨 Генерация изображения: {topic}")
    if not EDENAI_KEY:
        logger.warning("❌ EDENAI_API_KEY отсутствует — placeholder")
        return generate_placeholder(topic)

    headers = {"Authorization": f"Bearer {EDENAI_KEY}", "Content-Type": "application/json"}
    prompt = topic[:150]

    for prov in EDENAI_PROVIDERS:
        payload = {"providers": prov, "text": prompt, "resolution": "512x512"}
        try:
            start = time.time()
            resp = requests.post("https://api.edenai.run/v2/image/generation", headers=headers, json=payload, timeout=60)
            dt = time.time() - start
            logger.info(f"⏱ {prov} → {resp.status_code} ({dt:.1f}s)")
            data = resp.json()

            if resp.status_code == 200:
                pd = data.get(prov)
                if pd and "items" in pd and isinstance(pd["items"], list):
                    url = pd["items"][0].get("image_resource_url") or pd["items"][0].get("url")
                    if url:
                        fn = save_image_from_url(url, topic)
                        logger.info(f"✅ Сгенерировано через {prov}")
                        return fn
            else:
                logger.warning(f"⚠ {prov} failed: {data}")
        except Exception as e:
            logger.error(f"❌ {prov} error: {e}")

    logger.warning("⚠ Все провайдеры Eden AI не сработали — placeholder")
    return generate_placeholder(topic)

def save_image_from_url(url, topic):
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        fn = f"assets/images/posts/{generate_slug(topic)}.png"
        os.makedirs(os.path.dirname(fn), exist_ok=True)
        with open(fn, "wb") as f:
            f.write(resp.content)
        return fn
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки картинки: {e}")
        return generate_placeholder(topic)

def generate_placeholder(topic):
    fn = f"assets/images/posts/{generate_slug(topic)}.png"
    os.makedirs(os.path.dirname(fn), exist_ok=True)
    img = Image.new("RGB", (800,400), "#0f172a")
    d = ImageDraw.Draw(img)
    txt = textwrap.fill(topic, width=30)
    font = ImageFont.load_default()
    bbox = d.textbbox((0,0), txt, font=font)
    d.text(((800-bbox[2])/2,(400-bbox[3])/2), txt, font=font, fill="#6366f1")
    img.save(fn)
    logger.info("🖼 Placeholder создан")
    return fn

# — Утилиты —
def generate_slug(t):
    return re.sub(r'[^a-z0-9\-]', '', re.sub(r'\s+','-', t.lower()))[:60]

def generate_frontmatter(title, content, model, image):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return f"""---
title: "{title.replace('"','“')}"
date: {now}
draft: false
image: "{image}"
ai_model: "{model}"
---

{content}
"""

# — Главная функция —
def generate_content():
    logger.info("🚀 Генерация...")

    clean_old_articles()
    topic = generate_ai_trend_topic()
    logger.info(f"Тема: {topic}")

    image = generate_article_image(topic)
    text, model = generate_article_content(topic)

    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    slug = generate_slug(topic)
    fn = f"content/posts/{date}-{slug}.md"
    os.makedirs(os.path.dirname(fn), exist_ok=True)
    with open(fn, "w", encoding="utf-8") as f:
        f.write(generate_frontmatter(topic, text, model, image))
    logger.info(f"✅ Статья: {fn}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=1, help="Сколько статей сгенерировать")
    args = parser.parse_args()

    for i in range(args.count):
        generate_content()
        time.sleep(2)
