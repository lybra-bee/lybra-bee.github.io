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
    """Правильное экранирование MarkdownV2"""
    if not text:
        return ""
    escaped = ""
    for char in text:
        if char in r'_*[]()~`>#+=|{}.!-':
            escaped += '\\' + char
        else:
            escaped += char
    return escaped

# -------------------- AI-генерация изображения по хэшу заголовка --------------------
def generate_deterministic_image(title):
    """Детерминированное изображение по хэшу заголовка"""
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

# -------------------- Шаг 1: МОЩНЫЕ SMM заголовки --------------------
def generate_title(topic):
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY required")
        
    groq_model = "llama-3.3-70b-versatile"
    system_prompt = """Ты — ТОП SMM-специалист 2025 года. Создавай КЛИКАБЕЛЬНЫЕ заголовки для ИИ-блога.
    
    ФОРМУЛА УСПЕХА:
    1️⃣ Цифры: "7 способов", "Топ-5", "2025: 3x быстрее"
    2️⃣ Эмоции: "ШОКИРУЮЩИ", "РЕВОЛЮЦИЯ", "СЕКРЕТЫ"
    3️⃣ Вопросы: "Готовы ли вы?", "Зачем тратить время?"
    4️⃣ Срочность: "Сейчас", "2025", "Уже завтра"
    
    Примеры:
    - "7 ИИ-инструментов, которые 10x ускорят ваш бизнес в 2025"
    - "ШОК: эта нейросеть заменит 80% дизайнеров уже в этом году"
    
    Тема: '{topic}'
    Формат СТРОГО: ЗАГОЛОВОК: [твой вирусный заголовок, 12-18 слов]"""

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    payload = {
        "model": groq_model,
        "messages": [{"role": "system", "content": system_prompt.format(topic=topic)},
                     {"role": "user", "content": "Дай САМЫЙ кликабельный заголовок."}],
        "max_tokens": 150,
        "temperature": 0.9,
    }

    for attempt in range(10):
        logging.info(f"Title attempt {attempt+1}: {topic}")
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=30)
            r.raise_for_status()
            text = r.json()["choices"][0]["message"]["content"]
            match = re.search(r"ЗАГОЛОВОК:s*(.+)", text, re.IGNORECASE | re.DOTALL)
            if match:
                title = match.group(1).strip()
                words = title.split()
                if 12 <= len(words) <= 20:  # 12-20 слов для SMM
                    logging.info(f"✅ Title OK: {title[:60]}...")
                    return title
        except Exception as e:
            logging.error(f"Title error: {e}")
            time.sleep(2)
    raise RuntimeError("Failed to generate SMM title")

# -------------------- Шаг 2: Генерация статьи --------------------
def generate_body(title):
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY required")
        
    groq_model = "llama-3.3-70b-versatile"
    system_prompt = f"""Напиши ПОЛНУЮ статью для ИИ-блога по заголовку: "{title}"
    • Русский язык, 800-1200 слов
    • 5-7 подзаголовков (###)
    • Конкретные примеры, кейсы, цифры
    • Практические советы
    • Заключение с призывом к действию"""

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    payload = {
        "model": groq_model,
        "messages": [{"role": "system", "content": system_prompt},
                     {"role": "user", "content": "Напиши статью."}],
        "max_tokens": 3000,
        "temperature": 0.7,
    }

    for attempt in range(5):
        logging.info(f"Body attempt {attempt+1}: {title[:50]}...")
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=90)
            r.raise_for_status()
            body = r.json()["choices"][0]["message"]["content"].strip()
            if len(body.split()) > 600:
                return body
        except Exception as e:
            logging.error(f"Body error: {e}")
            time.sleep(3)
    raise RuntimeError("Failed to generate article")

# -------------------- Сохранение С ИЗОБРАЖЕНИЕМ ✅ --------------------
def save_post(title, body, image_url):
    today = datetime.now().strftime("%Y-%m-%d")
    
    # ✅ ПРАВИЛЬНЫЙ slug из заголовка
    slug = re.sub(r'[^a-zа-я0-9s]', '', title.lower())
    slug = re.sub(r's+', '-', slug)
    slug = re.sub(r'-+', '-', slug).strip('-')[:80]
    if len(slug) < 10:
        slug = f"ai-{today.replace('-', '')}"
    
    filename = POSTS_DIR / f"{today}-{slug}.md"
    
    # ✅ Frontmatter С ИЗОБРАЖЕНИЕМ
    image_relative = f"/assets/images/posts/post-{int(time.time())}.jpg"
    frontmatter = f"""---
title: "{title}"
date: {today}
image: {image_relative}
description: ИИ революция 2025: {title[:100]}...
---

{body}

![Постер]({image_url})
"""
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(frontmatter)
    logging.info(f"✅ Saved: {filename} (image: {image_relative})")
    return filename

# -------------------- Telegram --------------------
def send_to_telegram(title, body, image_url):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logging.warning("Telegram keys absent")
        return

    teaser = ' '.join(body.split()[:25]) + '...'
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
            logging.warning(f"Image download failed: {r.status_code}")
            return
            
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        temp_file.write(r.content)
        temp_file.close()
        image_file = temp_file.name

        with open(image_file, "rb") as photo:
            resp = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto",
                data={"chat_id": TELEGRAM_CHAT_ID, "caption": message, "parse_mode": "MarkdownV2"},
                files={"photo": photo},
                timeout=30
            )

        if resp.status_code == 200:
            logging.info("✅ Telegram OK")
        else:
            logging.warning(f"Telegram: {resp.status_code}")

        os.unlink(image_file)
    except Exception as e:
        logging.warning(f"Telegram error: {e}")

# -------------------- MAIN --------------------
def main():
    topics = [
        "ИИ в автоматизации контента 2025", 
        "Мультимодальные нейросети", 
        "Генеративные модели будущего",
        "Нейросети для бизнеса"
    ]
    topic = random.choice(topics)

    logging.info(f"🎯 Topic: {topic}")
    
    title = generate_title(topic)
    body = generate_body(title)
    image_url = generate_deterministic_image(title)
    
    save_post(title, body, image_url)
    send_to_telegram(title, body, image_url)
    
    logging.info("🎉 === POST PUBLISHED ===")

if __name__ == "__main__":
    main()
