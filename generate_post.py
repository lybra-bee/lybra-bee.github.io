#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
import time
import random
import logging
from datetime import datetime
from pathlib import Path
import tempfile
import requests
import hashlib

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

POSTS_DIR = Path("_posts")
IMAGES_DIR = Path("assets/images/posts")
POSTS_DIR.mkdir(exist_ok=True)
IMAGES_DIR.mkdir(exist_ok=True)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def telegram_escape(text):
    escaped = ""
    for char in text:
        if char in r'_*[]()~`>#+=|{}.!-':
            escaped += '\\' + char
        else:
            escaped += char
    return escaped

def generate_deterministic_image(title):
    title_hash = hashlib.md5(title.encode()).hexdigest()
    seed = int(title_hash[:8], 16) % 1000
    img_url = f"https://picsum.photos/seed/ai-{seed}/1024/1024"
    logging.info(f"Image: {img_url}")
    return img_url

def generate_title(topic):
    if not GROQ_API_KEY:
        return f"ИИ {topic} 2025"
    
    prompt = f"Заголовок для ИИ-блога: {topic}"
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 60,
        "temperature": 0.8,
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=20)
        r.raise_for_status()
        text = r.json()["choices"][0]["message"]["content"].strip()
        title = text.split('
')[0].strip()[:100]
        if len(title.split()) >= 6:
            logging.info(f"Title: {title}")
            return title
    except:
        pass
    
    fallback = f"ИИ революция: {topic}"
    logging.warning(f"Fallback: {fallback}")
    return fallback

def generate_body(title):
    if not GROQ_API_KEY:
        return f"# {title}

Статья про {title.lower()}.

## Преимущества
1. Быстрее
2. Дешевле
3. Лучше

## Заключение
Начните использовать сегодня!"
    
    prompt = f"Статья ИИ-блог: {title}. Русский, 600 слов."
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    payload = {
        "model": "llama-3.3-70b-versatile", 
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2000,
        "temperature": 0.7,
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        body = r.json()["choices"][0]["message"]["content"].strip()
        if len(body) > 1000:
            logging.info("Body OK")
            return body
    except:
        pass
    
    fallback = f"# {title}

{title} меняет мир ИИ.

Начните использовать прямо сейчас!"
    logging.warning("Fallback body")
    return fallback

def save_post(title, body, image_url):
    today = datetime.now().strftime("%Y-%m-%d")
    slug = re.sub(r'[^a-zа-я0-9]', '-', title.lower())[:60].strip('-')
    filename = POSTS_DIR / f"{today}-{slug}.md"
    
    frontmatter = f"""---
title: "{title}"
date: {today}
image: /assets/images/posts/post-{int(time.time())}.jpg
---

{body}

![cover]({image_url})
"""
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(frontmatter)
    logging.info(f"Saved: {filename}")
    return filename

def send_to_telegram(title, body, image_url):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logging.warning("No Telegram")
        return

    teaser = ' '.join(body.split()[:15]) + '...'
    message = f"*{title}*\
\
{telegram_escape(teaser)}\
\
[Читать](https://lybra-ai.ru)"

    try:
        r = requests.get(image_url, timeout=10)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        temp_file.write(r.content)
        temp_file.close()

        with open(temp_file.name, "rb") as photo:
            resp = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto",
                data={"chat_id": TELEGRAM_CHAT_ID, "caption": message, "parse_mode": "MarkdownV2"},
                files={"photo": photo}
            )
        
        if resp.status_code == 200:
            logging.info("Telegram OK")
        os.unlink(temp_file.name)
    except:
        logging.warning("Telegram failed")

def main():
    topics = ["автоматизация контента", "нейросети 2025", "генеративный ИИ", "ИИ бизнес"]
    topic = random.choice(topics)

    logging.info(f"Topic: {topic}")
    
    title = generate_title(topic)
    body = generate_body(title)
    image_url = generate_deterministic_image(title)
    
    save_post(title, body, image_url)
    send_to_telegram(title, body, image_url)
    
    logging.info("DONE")

if __name__ == "__main__":
    main()
