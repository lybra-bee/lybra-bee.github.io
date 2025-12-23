#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import time
import yaml
import random
import logging
import datetime
import requests
from pathlib import Path
from typing import Optional
from io import BytesIO

from groq import Groq
from PIL import Image

# ===================== КОНФИГ =====================

POSTS_DIR = Path("_posts")
IMAGES_DIR = Path("assets/images/posts")
LOG_FILE = "generation.log"

MAX_ARTICLE_ATTEMPTS = 4

POSTS_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# ===================== ЛОГИ =====================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ],
)

log = logging.info

# ===================== АНТИ-ПОЛИТИКА =====================

POLITICAL_PATTERNS = [
    r"\bгос",
    r"\bгосударств",
    r"\bпрезидент",
    r"\bминистр",
    r"\bпарламент",
    r"\bзакон",
    r"\bуказ",
    r"\bвыбор",
    r"\bсанкц",
    r"\bвойн",
    r"\bстрана\b",
    r"\bполитик",
]

def contains_politics(text: str) -> bool:
    t = text.lower()
    return any(re.search(p, t) for p in POLITICAL_PATTERNS)

# ===================== ТЕМЫ =====================

SAFE_TOPICS = [
    "Практическое применение генеративного ИИ в 2025 году",
    "Как инженеры используют LLM для ускорения разработки",
    "AI-агенты и автономные системы: архитектура и кейсы",
    "Мультимодальные модели: реальные сценарии использования",
    "Open Source инструменты ИИ, которые применяют на практике",
]

# ===================== ГЕНЕРАЦИЯ СТАТЬИ =====================

def generate_article(client: Groq, topic: str) -> str:
    prompt = f"""
Ты — опытный технический журналист в сфере ИИ и высоких технологий.

СТРОГО ЗАПРЕЩЕНО (КРИТИЧЕСКОЕ ТРЕБОВАНИЕ):
- политика
- государства
- страны
- законы
- указы
- регуляторы
- лидеры
- выборы
- войны
- санкции
- международные отношения

ЕСЛИ ТЫ ХОТЯ БЫ УПОМЯНЕШЬ ЧТО-ТО ИЗ ЭТОГО — ОТВЕТ СЧИТАЕТСЯ НЕВЕРНЫМ.

РАЗРЕШЕНО:
- искусственный интеллект
- LLM
- генеративные модели
- нейросети
- инструменты
- инженерные подходы
- бизнес-применение
- исследования
- метрики
- практические кейсы

Тема статьи:
{topic}

Формат ответа:
1. Заголовок (одна строка)
2. Пустая строка
3. Основной текст (5–7 абзацев, без списков законов и стран)
"""

    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.85,
        max_tokens=3000,
    )

    return r.choices[0].message.content.strip()

# ===================== ИЗОБРАЖЕНИЕ =====================

def generate_image(prompt: str) -> Path:
    filename = f"post-{int(time.time())}.png"
    path = IMAGES_DIR / filename

    # Stability AI
    if os.getenv("STABILITYAI_KEY"):
        try:
            r = requests.post(
                "https://api.stability.ai/v2beta/stable-image/generate/core",
                headers={
                    "Authorization": f"Bearer {os.getenv('STABILITYAI_KEY')}",
                    "Accept": "image/png"
                },
                files={"prompt": (None, prompt)},
                timeout=60
            )
            if r.status_code == 200:
                path.write_bytes(r.content)
                log("🖼 PNG создано (Stability AI)")
                return path
        except Exception as e:
            log(f"⚠️ Stability AI ошибка: {e}")

    # HuggingFace
    if os.getenv("HF_API_TOKEN"):
        try:
            r = requests.post(
                "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0",
                headers={"Authorization": f"Bearer {os.getenv('HF_API_TOKEN')}"},
                json={"inputs": prompt},
                timeout=60
            )
            img = Image.open(BytesIO(r.content))
            img.save(path, "PNG")
            log("🖼 PNG создано (HuggingFace)")
            return path
        except Exception as e:
            log(f"⚠️ HuggingFace ошибка: {e}")

    Image.new("RGB", (1024, 1024), (30, 30, 30)).save(path)
    log("🖼 PNG fallback")
    return path

# ===================== СОХРАНЕНИЕ =====================

def save_post(title: str, body: str, image_name: str) -> Path:
    today = datetime.date.today()
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:50]
    file = POSTS_DIR / f"{today}-{slug}.md"

    fm = {
        "layout": "post",
        "title": title,
        "date": f"{today} 00:00:00 +0000",
        "image": f"/assets/images/posts/{image_name}",
        "tags": ["ИИ", "AI", "LLM"],
    }

    with open(file, "w", encoding="utf-8") as f:
        f.write("---\n")
        yaml.dump(fm, f, allow_unicode=True, sort_keys=False)
        f.write("---\n\n")
        f.write(body)

    log(f"💾 Статья сохранена: {file}")
    return file

# ===================== TELEGRAM =====================

def send_to_telegram(title: str, teaser: str, image_path: Path):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat:
        log("⚠️ Telegram пропущен (нет ключей)")
        return

    def esc(t):
        return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', t)

    msg = (
        f"*Новая статья*\n\n"
        f"*{esc(title)}*\n\n"
        f"{esc(teaser)}…\n\n"
        f"[Читать на сайте](https://lybra-ai.ru)\n\n"
        f"#ИИ #LybraAI"
    )

    r = requests.post(
        f"https://api.telegram.org/bot{token}/sendPhoto",
        data={"chat_id": chat, "caption": msg, "parse_mode": "MarkdownV2"},
        files={"photo": image_path.open("rb")}
    )

    log(f"📢 Telegram статус: {r.status_code}")

# ===================== MAIN =====================

def main() -> bool:
    log("🚀 Запуск генерации")

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    article = None
    topic = None

    for attempt in range(1, MAX_ARTICLE_ATTEMPTS + 1):
        topic = random.choice(SAFE_TOPICS)
        log(f"✍️ Попытка {attempt}: {topic}")

        article = generate_article(client, topic)

        if contains_politics(article):
            log("⚠️ Обнаружена политика — регенерация")
            continue

        break
    else:
        log("❌ Не удалось получить безопасную статью")
        return False

    lines = article.splitlines()
    title = lines[0].strip()
    body = "\n".join(lines[1:]).strip()

    log(f"📰 Заголовок: {title}")

    image = generate_image(
        f"Ultra realistic photo illustration, cinematic lighting, modern technology, {topic}"
    )

    save_post(title, body, image.name)

    teaser = " ".join(body.split()[:30])
    send_to_telegram(title, teaser, image)

    log("✅ Успешно завершено")
    return True

# ===================== ENTRY =====================

if __name__ == "__main__":
    success = main()
    raise SystemExit(0 if success else 1)
