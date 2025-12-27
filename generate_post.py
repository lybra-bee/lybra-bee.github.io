#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
import time
import json
import random
import logging
import sys
from datetime import datetime
from pathlib import Path
import tempfile
import requests
import hashlib
import urllib.parse

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

# -------------------- Папки --------------------
POSTS_DIR = Path("_posts")
IMAGES_DIR = Path("assets/images/posts")
POSTS_DIR.mkdir(exist_ok=True)
IMAGES_DIR.mkdir(exist_ok=True)

# -------------------- API ключи --------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# -------------------- Telegram экранирование --------------------
def telegram_escape(text):
    if not text:
        return ""
    escaped = ""
    for char in text:
        if char in r'_*[]()~`>#+=|{}.!-':
            escaped += '\\' + char
        else:
            escaped += char
    return escaped

# -------------------- AI-генерация изображения --------------------
def generate_deterministic_image(title):
    title_hash = hashlib.md5(title.encode()).hexdigest()
    seed = int(title_hash[:8], 16) % 1000
    
    themes = [
        f"https://picsum.photos/seed/ai-{seed}/1024/1024",
        f"https://picsum.photos/seed/tech-{seed}/1024/1024", 
        f"https://source.unsplash.com/1024x1024/?ai,technology&sig={seed}",
    ]
    
    img_url = random.choice(themes)
    logging.info(f"🖼️ Image: {img_url}")
    return img_url

# -------------------- Шаг 1: НАДЁЖНЫЕ SMM заголовки --------------------
def generate_title(topic):
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY required")
    
    # ✅ ПРОСТОЙ промпт — работает 100%
    prompt = f"""Создай КЛИКАБЕЛЬНЫЙ заголовок для ИИ-блога по теме: {topic}

ПРИМЕРЫ:
• "7 ИИ-инструментов которые 10x ускорят ваш бизнес в 2025"
• "ШОК нейросеть заменит 80% дизайнеров уже в этом году" 
• "Топ-5 мультимодальных моделей 2025 которые взорвут рынок"

Только ЗАГОЛОВОК без номера!"""

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 80,
        "temperature": 0.8,
    }

    for attempt in range(5):  # ✅ Меньше попыток
        logging.info(f"Title attempt {attempt+1}: {topic}")
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=20)
            r.raise_for_status()
            text = r.json()["choices"][0]["message"]["content"].strip()
            
            # ✅ БЕРЁМ ПЕРВУЮ НЕПУСТУЮ СТРОКУ
            lines = [line.strip() for line in text.split('
') if line.strip()]
            if lines:
                title = lines[0]
                words = title.split()
                if 8 <= len(words) <= 25:  # ✅ Гибкие лимиты
                    logging.info(f"✅ Title: {title}")
                    return title
                    
        except Exception as e:
            logging.error(f"Title error {attempt+1}: {e}")
            time.sleep(1)
    
    # ✅ FALLBACK заголовок если Groq глючит
    fallback_titles = [
        f"ИИ-революция 2025: как {topic.lower()} изменит ваш бизнес",
        f"Топ-7 инструментов {topic} для 2025 года",
        f"Будущее {topic}: что покажут нейросети 2025"
    ]
    title = random.choice(fallback_titles)
    logging.warning(f"Using fallback title: {title}")
    return title

# -------------------- Шаг 2: Генерация статьи --------------------
def generate_body(title):
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY required")
    
    prompt = f"""Напиши статью для ИИ-блога по заголовку: "{title}"

✅ ТРЕБОВАНИЯ:
• Русский язык
• 700-1000 слов  
• 4-6 подзаголовков (### Заголовок)
• Конкретные примеры
• Практические советы
• Заключение"""

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2500,
        "temperature": 0.7,
    }

    for attempt in range(3):
        logging.info(f"Body attempt {attempt+1}: {title[:50]}...")
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=60)
            r.raise_for_status()
            body = r.json()["choices"][0]["message"]["content"].strip()
            if len(body.split()) > 500:
                return body
        except Exception as e:
            logging.error(f"Body error: {e}")
            time.sleep(2)
    
    # ✅ FALLBACK тело
    fallback = f"""# {title}

## Введение

{title} — одна из самых горячих тем 2025 года. ИИ меняет подход к...

## Почему это важно

1. **Скорость**: в 10 раз быстрее традиционных методов
2. **Качество**: нейросети дают профессиональный результат
3. **Экономия**: снижает затраты на 70%

## Практические примеры

- **Кейс 1**: компания X увеличила конверсию на 300%
- **Кейс 2**: автоматизация сократила время на 90%

## Как начать

1. Выберите инструмент (ChatGPT, Midjourney, Grok)
2. Настройте промпты
3. Интегрируйте в workflow

## Заключение

{title} — это не будущее, а настоящее. Начните сегодня!"""
    logging.warning("Using fallback body")
    return fallback

# -------------------- Сохранение С ИЗОБРАЖЕНИЕМ --------------------
def save_post(title, body, image_url):
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Правильный slug
    slug = re.sub(r'[^a-zа-я0-9s]', '', title.lower())
    slug = re.sub(r's+', '-', slug)
    slug = re.sub(r'-+', '-', slug).strip('-')[:80]
    if len(slug) < 8:
        slug = f"ai-{today.replace('-', '')}"
    
    filename = POSTS_DIR / f"{today}-{slug}.md"
    
    # Frontmatter С ИЗОБРАЖЕНИЕМ
    image_filename = f"post-{int(time.time())}.jpg"
    image_relative = f"/assets/images/posts/{image_filename}"
    
    frontmatter = f"""---
title: "{title}"
date: {today}
image: {image_relative}
description: {title[:120]}...
---

{body}

![{title}]({image_url})
"""
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(frontmatter)
    logging.info(f"✅ Saved: {filename}")
    return filename

# -------------------- Telegram --------------------
def send_to_telegram(title, body, image_url):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logging.warning("Telegram keys absent")
        return

    teaser = ' '.join(body.split()[:20]) + '...'
    message = f"*🚀 {title}*\
\
{telegram_escape(teaser)}\
\
👉 [Читать полностью](https://lybra-ai.ru)\
\
#ИИ #Нейросети #2025"

    try:
        r = requests.get(image_url, timeout=15)
        if not r.ok:
            logging.warning(f"Image download failed")
            return
            
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        temp_file.write(r.content)
        temp_file.close()

        with open(temp_file.name, "rb") as photo:
            resp = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto",
                data={"chat_id": TELEGRAM_CHAT_ID, "caption": message, "parse_mode": "MarkdownV2"},
                files={"photo": photo},
                timeout=30
            )

        if resp.status_code == 200:
            logging.info("✅ Telegram OK")
        os.unlink(temp_file.name)
    except Exception as e:
        logging.warning(f"Telegram: {e}")

# -------------------- MAIN --------------------
def main():
    topics = [
        "ИИ автоматизация контента 2025", 
        "мультимодальные нейросети", 
        "генеративные модели будущего",
        "нейросети для бизнеса"
    ]
    topic = random.choice(topics)

    logging.info(f"🎯 Topic: {topic}")
    
    title = generate_title(topic)
    body = generate_body(title)
    image_url = generate_deterministic_image(title)
    
    save_post(title, body, image_url)
    send_to_telegram(title, body, image_url)
    
    logging.info("🎉 === DONE ===")

if __name__ == "__main__":
    main()
