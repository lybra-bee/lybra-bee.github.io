#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import time
import random
import logging
import requests
import tempfile
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# -------------------- Папки --------------------
POSTS_DIR = Path("_posts")
IMAGES_DIR = Path("assets/images/posts")
POSTS_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# -------------------- Ключи --------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
HORDE_API_KEY = os.getenv("HORDE_API_KEY", "0000000000")

SITE_URL = "https://lybra-ai.ru"

FALLBACK_IMAGES = [
    "https://picsum.photos/1024/768?random=11",
    "https://picsum.photos/1024/768?random=22",
    "https://picsum.photos/1024/768?random=33",
]

# -------------------- Транслит --------------------
TRANSLIT_MAP = {
    'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'yo','ж':'zh','з':'z',
    'и':'i','й':'y','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r',
    'с':'s','т':'t','у':'u','ф':'f','х':'kh','ц':'ts','ч':'ch','ш':'sh',
    'щ':'shch','ъ':'','ы':'y','ь':'','э':'e','ю':'yu','я':'ya'
}

def translit(text):
    return ''.join(TRANSLIT_MAP.get(c, c) for c in text.lower())

# -------------------- Заголовок --------------------
def generate_title(topic):
    prompt = f"""
Ты — редактор практического инженерного блога про нейросети.

Создай ОДИН заголовок:
- формат: гайд / мастер-класс / практический разбор
- строго прикладная тема
- без философии и футурологии
- 10–16 слов
- тема: {topic}

Ответ:
ЗАГОЛОВОК: ...
"""

    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
        json={
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "system", "content": prompt}],
            "max_tokens": 120,
            "temperature": 1.0
        },
        timeout=60
    )
    text = r.json()["choices"][0]["message"]["content"]
    return re.sub(r"ЗАГОЛОВОК:\s*", "", text).strip()

# -------------------- ДЛИННАЯ СТАТЬЯ --------------------
def generate_body(title):
    prompt = f"""
Ты — практикующий ML/AI инженер.

Напиши ОЧЕНЬ ПОДРОБНУЮ статью:
формат — урок / мастер-класс / инженерный гайд.

Заголовок:
"{title}"

ЖЁСТКИЕ ТРЕБОВАНИЯ:
- 6000–9000 знаков (НЕ МЕНЬШЕ)
- Только практическая работа с нейросетями
- Только актуальные инструменты (последние 6–12 месяцев)
- Реальные пайплайны, архитектуры, приёмы
- Можно псевдокод, списки, примеры

СТРУКТУРА:
## Зачем это нужно на практике
## Архитектура решения
## Пошаговая реализация
## Оптимизация и ускорение
## Частые ошибки
## Ограничения и риски
## Итог и что улучшить дальше

Запрещено:
- философия
- абстракции
- «в будущем»
"""

    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
        json={
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "system", "content": prompt}],
            "max_tokens": 3200,
            "temperature": 0.85
        },
        timeout=180
    )
    return r.json()["choices"][0]["message"]["content"]

# -------------------- Horde Image --------------------
def generate_image(title):
    prompt = f"realistic photo, AI engineering, servers, neural networks, data flow, {title}"

    r = requests.post(
        "https://stablehorde.net/api/v2/generate/async",
        headers={
            "apikey": HORDE_API_KEY,
            "Client-Agent": "LybraAI:4.0"
        },
        json={
            "prompt": prompt,
            "models": ["SDXL 1.0"],
            "params": {"width": 1024, "height": 576, "steps": 30},
            "nsfw": False
        },
        timeout=60
    )

    if not r.ok:
        return random.choice(FALLBACK_IMAGES)

    job_id = r.json()["id"]
    status_url = f"https://stablehorde.net/api/v2/generate/status/{job_id}"

    for _ in range(36):
        time.sleep(10)
        s = requests.get(status_url, timeout=30).json()
        if s.get("done") and s.get("generations"):
            img_url = s["generations"][0]["img"]
            img = requests.get(img_url).content
            path = IMAGES_DIR / f"horde-{int(time.time())}.jpg"
            path.write_bytes(img)
            return str(path)

    return random.choice(FALLBACK_IMAGES)

# -------------------- Save --------------------
def save_post(title, body, image):
    date = datetime.now()
    slug = re.sub(r'[^a-z0-9-]+', '-', translit(title))[:80]
    file = POSTS_DIR / f"{date:%Y-%m-%d}-{slug}.md"

    fm = f"""---
title: "{title}"
date: {date:%Y-%m-%d 00:00:00 -0000}
layout: post
categories: ai
tags: [ИИ, нейросети, практика]
image: {image}
image_alt: "{title}"
description: "{title} — подробный практический гайд"
---

"""
    file.write_text(fm + body, encoding="utf-8")
    return f"{SITE_URL}/{slug}/"

# -------------------- Telegram --------------------
def send_to_telegram(title, body, image, url):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return

    teaser = " ".join(body.split()[:60]) + "..."

    with requests.get(image, stream=True) as img:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto",
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "caption": f"<b>{title}</b>\n\n{teaser}\n\n{url}",
                "parse_mode": "HTML"
            },
            files={"photo": img.raw}
        )

# -------------------- MAIN --------------------
def main():
    topics = [
        "Оптимизация инференса LLM",
        "ИИ-агенты на практике",
        "Мультимодальные пайплайны",
        "Запуск нейросетей локально",
        "Ускорение генерации изображений",
        "Связка нескольких моделей"
    ]

    topic = random.choice(topics)
    title = generate_title(topic)
    body = generate_body(title)
    image = generate_image(title)
    url = save_post(title, body, image)
    send_to_telegram(title, body, image, url)

    logging.info("=== УСПЕХ ===")

if __name__ == "__main__":
    main()
