#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
import time
import json
import random
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path
import base64
import tempfile
import uuid

# 🔥 АВТОУСТАНОВКА ЗАВИСИМОСТЕЙ (1 раз)
def install_requirements():
    required = ['requests', 'beautifulsoup4']
    for package in required:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            logging.info(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install_requirements()

# Теперь импортируем после установки
import requests
from bs4 import BeautifulSoup

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

# 🔥 GIGACHAT КЛЮЧИ (твои данные)
GIGACHAT_CREDS = "Y2U4NDJmZDYtYjVlMS00ZTQ0LWE1ZWUtZTQ3ZTQ3ODMyOGVhOmIzM2UxNzljLTMwMjYtNDZiYi1hYWEzLTA3NDAzMzlkMTc2Yg=="
SCOPE = "GIGACHAT_API_PERS"

FALLBACK_IMAGES = [
    "https://picsum.photos/800/600?random=1",
    "https://picsum.photos/800/600?random=2",
    "https://picsum.photos/800/600?random=3",
]

# -------------------- Шаг 1: Генерация заголовка --------------------
def generate_title(topic):
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY required")
        
    groq_model = "llama-3.3-70b-versatile"
    system_prompt = f"""Ты — эксперт по SMM и копирайтингу для блога об ИИ.
    Создай один яркий, кликабельный заголовок на тему '{topic}'.
    Заголовок должен быть на русском, содержать 10-15 слов, использовать приёмы: цифры, вопросы, слова "Как", "Почему", "Топ", "Будущее", "Революция", "Секреты", "2025" и т.д.
    Он должен вызывать любопытство и желание кликнуть.
    Формат ответа строго: ЗАГОЛОВОК: [твой заголовок]"""

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    payload = {
        "model": groq_model,
        "messages": [{"role": "system", "content": system_prompt},
                     {"role": "user", "content": "Создай заголовок."}],
        "max_tokens": 100,
        "temperature": 1.0,
    }

    for attempt in range(7):
        logging.info(f"Title attempt {attempt+1}: {topic}")
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=30)
            r.raise_for_status()
            text = r.json()["choices"][0]["message"]["content"]
            match = re.search(r"ЗАГОЛОВОК:s*(.+)", text, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                if len(title.split()) >= 8:
                    return title
        except Exception as e:
            logging.error(f"Title error: {e}")
            time.sleep(2)
    raise RuntimeError("Failed to generate valid title")

# -------------------- Шаг 2: Генерация статьи по заголовку --------------------
def generate_body(title):
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY required")
        
    groq_model = "llama-3.3-70b-versatile"
    system_prompt = f"""Напиши полную информативную статью для блога об ИИ по заголовку: "{title}"
    Статья на русском, 600-900 слов, с абзацами, без политики, скандалов, морали или регуляций.
    Сделай текст увлекательным, с примерами и выводами."""

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    payload = {
        "model": groq_model,
        "messages": [{"role": "system", "content": system_prompt},
                     {"role": "user", "content": "Напиши статью."}],
        "max_tokens": 2000,
        "temperature": 0.8,
    }

    for attempt in range(5):
        logging.info(f"Body attempt {attempt+1} for title: {title[:50]}...")
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=60)
            r.raise_for_status()
            body = r.json()["choices"][0]["message"]["content"].strip()
            if len(body.split()) > 300:
                return body
        except Exception as e:
            logging.error(f"Body error: {e}")
            time.sleep(3)
    raise RuntimeError("Failed to generate article body")

# 🔥 Шаг 3: GigaChat Kandinsky --------------------
def generate_image_gigachat(prompt, timeout=300):
    """GigaChat API: 100+ изображений/сутки БЕСПЛАТНО"""
    logging.info(f"GigaChat: generating '{prompt[:50]}...'")
    
    start_time = time.time()
    try:
        # 1. Токен (30 мин)
        token_url = "https://gigachat.devices.sberbank.ru/api/v1/oauth"
        token_data = {"scope": SCOPE}
        token_headers = {
            "Authorization": f"Basic {GIGACHAT_CREDS}",
            "Content-Type": "application/x-www-form-urlencoded",
            "RqUID": re.sub(r"[^0-9a-f-]", "", str(uuid.uuid4()))
        }
        token_resp = requests.post(token_url, data=token_data, headers=token_headers, timeout=30)
        token_resp.raise_for_status()
        access_token = token_resp.json()["access_token"]
        
        # 2. Генерация
        chat_url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
        chat_payload = {
            "model": "GigaChat Pro",
            "messages": [
                {"role": "system", "content": "Генерируй изображения Kandinsky 3.1"},
                {"role": "user", "content": prompt + ", реалистично, высокое качество, 4k"}
            ],
            "max_tokens": 1000,
            "temperature": 0.7,
            "function_call": "auto"
        }
        chat_headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "RqUID": re.sub(r"[^0-9a-f-]", "", str(uuid.uuid4()))
        }
        chat_resp = requests.post(chat_url, json=chat_payload, headers=chat_headers, timeout=120)
        chat_resp.raise_for_status()
        
        content = chat_resp.json()["choices"][0]["message"]["content"]
        soup = BeautifulSoup(content, "html.parser")
        img_tag = soup.find("img")
        
        if not img_tag or not img_tag.get("src"):
            logging.warning("GigaChat: no image in response")
            return None
        
        file_id = img_tag.get("src")
        
        # 3. Скачиваем
        img_url = f"https://gigachat.devices.sberbank.ru/api/v1/files/{file_id}/content"
        img_headers = {"Authorization": f"Bearer {access_token}", "Accept": "image/jpeg"}
        img_resp = requests.get(img_url, headers=img_headers, timeout=30)
        img_resp.raise_for_status()
        
        img_path = IMAGES_DIR / f"post-{int(time.time())}.jpg"
        with open(img_path, "wb") as f:
            f.write(img_resp.content)
        logging.info(f"✅ GigaChat image: {img_path}")
        return str(img_path)
        
    except Exception as e:
        logging.warning(f"GigaChat error: {e}")
        return None

def generate_image(title):
    """Приоритет: GigaChat → fallback"""
    img = generate_image_gigachat(title)
    if img:
        return img
    logging.warning("GigaChat failed → using fallback URL")
    return random.choice(FALLBACK_IMAGES)

# -------------------- Сохранение --------------------
def save_post(title, body):
    today = datetime.now().strftime("%Y-%m-%d")
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', title.lower()).strip('-')[:100]
    if not slug or len(slug) < 10:
        slug = "ai-revolution-" + today.replace("-", "")
    filename = POSTS_DIR / f"{today}-{slug}.md"
    
    frontmatter = f"""---
title: {title}
date: {today}
---

"""
    
    content = frontmatter + body
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    logging.info(f"Saved post: {filename}")
    return filename

# -------------------- Telegram --------------------
def send_to_telegram(title, body, image_path):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logging.warning("Telegram keys absent, skipping")
        return

    teaser = ' '.join(body.split()[:30]) + '...'
    def esc(text): 
        return re.sub(r'([_*[]()~`>#+-=|{}.!])', r'\\\u0001', text)
    message = f"*Новая статья*\
\
{esc(teaser)}\
\
[Читать на сайте](https://lybra-ai.ru)\
\
{esc('#ИИ #LybraAI')}"

    try:
        if image_path.startswith('http'):
            r = requests.get(image_path, timeout=10)
            if not r.ok:
                logging.warning(f"Failed to download fallback image: {r.status_code}")
                return
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
            temp_file.write(r.content)
            temp_file.close()
            image_file = temp_file.name
        else:
            image_file = image_path

        with open(image_file, "rb") as photo:
            resp = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto",
                data={"chat_id": TELEGRAM_CHAT_ID, "caption": message, "parse_mode": "MarkdownV2"},
                files={"photo": photo},
                timeout=30
            )

        if resp.status_code != 200:
            logging.warning(f"Telegram error {resp.status_code}: {resp.text}")
        else:
            logging.info(f"Telegram status {resp.status_code}")

        if image_path.startswith('http'):
            os.unlink(image_file)
    except Exception as e:
        logging.warning(f"Telegram error: {e}")

# -------------------- MAIN --------------------
def main():
    topics = ["ИИ в автоматизации контента", "Мультимодальные модели", "Генеративные модели 2025"]
    topic = random.choice(topics)

    title = generate_title(topic)
    body = generate_body(title)
    img_path = generate_image(title)
    save_post(title, body)
    send_to_telegram(title, body, img_path)
    logging.info("=== DONE ===")

if __name__ == "__main__":
    main()
