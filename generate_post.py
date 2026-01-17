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

# -------------------- API ключи --------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY не установлен!")

SITE_URL = "https://lybra-ai.ru"

FALLBACK_IMAGES = [
    "https://picsum.photos/1024/768?random=1",
    "https://picsum.photos/1024/768?random=2",
    "https://picsum.photos/1024/768?random=3",
    "https://picsum.photos/1024/768?random=4",
    "https://picsum.photos/1024/768?random=5",
]

# -------------------- Стили статей --------------------
ARTICLE_STYLES = {
    "guide": "пошаговый практический гайд",
    "business": "прикладная статья для бизнеса и маркетинга",
    "developer": "технический разбор для разработчиков",
    "content": "практика автоматизации контента и медиа"
}

ARTICLE_STYLE = random.choice(list(ARTICLE_STYLES.keys()))
ARTICLE_STYLE_DESC = ARTICLE_STYLES[ARTICLE_STYLE]

logging.info(f"Стиль статьи: {ARTICLE_STYLE} — {ARTICLE_STYLE_DESC}")

# -------------------- Транслит --------------------
TRANSLIT_MAP = {
    'а': 'a','б': 'b','в': 'v','г': 'g','д': 'd','е': 'e','ё': 'yo',
    'ж': 'zh','з': 'z','и': 'i','й': 'y','к': 'k','л': 'l','м': 'm',
    'н': 'n','о': 'o','п': 'p','р': 'r','с': 's','т': 't','у': 'u',
    'ф': 'f','х': 'kh','ц': 'ts','ч': 'ch','ш': 'sh','щ': 'shch',
    'ъ': '','ы': 'y','ь': '','э': 'e','ю': 'yu','я': 'ya'
}

def translit(text):
    return ''.join(TRANSLIT_MAP.get(c, c) for c in text.lower())

# -------------------- Заголовок --------------------
def generate_title(topic):
    prompt = f"""
Ты пишешь {ARTICLE_STYLE_DESC}.

Создай ОДИН заголовок на русском языке.
Тема: {topic}

Требования:
- практическая польза
- конкретный результат
- без футуризма
- без философии
- без слов: будущее, революция, AGI, осознал
- 8–14 слов

Формат:
ЗАГОЛОВОК: ...
"""

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.6,
        "max_tokens": 120
    }

    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
        json=payload,
        timeout=60
    )
    text = r.json()["choices"][0]["message"]["content"]
    return re.sub(r"ЗАГОЛОВОК:\s*", "", text).strip()

# -------------------- План --------------------
def generate_outline(title):
    prompt = f"""
Ты пишешь {ARTICLE_STYLE_DESC}.
Статья строго прикладная.

Заголовок: {title}

Сделай план:
- 6–8 разделов
- формат инструкции
- без прогнозов
- без абстракций
- только практика

Markdown, только заголовки.
"""

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.4,
        "max_tokens": 1200
    }

    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
        json=payload,
        timeout=60
    )
    return r.json()["choices"][0]["message"]["content"]

# -------------------- Раздел --------------------
def generate_section(title, outline, header):
    prompt = f"""
Ты пишешь {ARTICLE_STYLE_DESC}.

Раздел: {header}
Статья: {title}

Требования:
- 800–1200 знаков
- конкретные действия
- примеры
- чеклисты допустимы
- никакой философии

Только текст.
"""

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 600
    }

    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
        json=payload,
        timeout=90
    )
    return r.json()["choices"][0]["message"]["content"].strip()

# -------------------- Тело статьи --------------------
def generate_body(title):
    outline = generate_outline(title)
    headers = [l.replace("##", "").strip() for l in outline.splitlines() if l.startswith("##")]

    body = f"# {title}\n\n"
    total = 0

    for h in headers:
        text = generate_section(title, outline, h)
        body += f"## {h}\n\n{text}\n\n"
        total += len(text)

    logging.info(f"Объём статьи: {total} знаков")
    return body

# -------------------- Изображение --------------------
def generate_image(title):
    styles = [
        "person working at laptop with AI dashboard",
        "computer screen with analytics and charts",
        "developer workspace with code editor",
        "business analyst using AI tool on screen",
        "content creator automating workflow on computer"
    ]

    prompt = f"{title}, {random.choice(styles)}, realistic photo, office, natural light"

    payload = {
        "prompt": prompt,
        "models": ["Realistic Vision V5.1", "SDXL 1.0"],
        "params": {"width": 768, "height": 512, "steps": 25}
    }

    try:
        r = requests.post("https://stablehorde.net/api/v2/generate/async", json=payload, timeout=30)
        return random.choice(FALLBACK_IMAGES)
    except:
        return random.choice(FALLBACK_IMAGES)

# -------------------- Сохранение --------------------
def save_post(title, body, img):
    date = datetime.now().strftime("%Y-%m-%d")
    slug = re.sub(r'[^a-z0-9-]+', '-', translit(title))[:80]
    path = POSTS_DIR / f"{date}-{slug}.md"

    fm = f"""---
title: "{title}"
date: {date}
layout: post
categories: ai
tags: [ИИ, практика]
image: {img}
---

"""
    path.write_text(fm + body, encoding="utf-8")
    return f"{SITE_URL}/{slug}/"

# -------------------- Telegram --------------------
def send_to_telegram(title, body, img, url):
    if not TELEGRAM_BOT_TOKEN:
        return
    teaser = " ".join(body.split()[:60]) + "..."
    caption = f"<b>{title}</b>\n\n{teaser}\n\n{url}"

    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto",
        data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption, "parse_mode": "HTML"},
        files={"photo": requests.get(img).content}
    )

# -------------------- MAIN --------------------
def main():
    topics = [
        "Автоматизация задач с ИИ",
        "Использование ИИ в бизнесе",
        "ИИ для программистов",
        "Генерация контента с ИИ",
        "Оптимизация процессов с ИИ"
    ]

    topic = random.choice(topics)
    title = generate_title(topic)
    body = generate_body(title)
    img = generate_image(title)
    url = save_post(title, body, img)
    send_to_telegram(title, body, img, url)

    logging.info("=== DONE ===")

if __name__ == "__main__":
    main()
