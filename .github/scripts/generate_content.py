#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import requests
import random
import time
import logging
import textwrap
import base64
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import re

# ===== Настройка логирования =====
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ===== Пути =====
CONTENT_DIR = Path("content/posts")
GALLERY_DIR = Path("assets/images/posts")
MAX_ARTICLES = 5

# ===== Проверка и создание директорий =====
CONTENT_DIR.mkdir(parents=True, exist_ok=True)
GALLERY_DIR.mkdir(parents=True, exist_ok=True)

# ===== Переменные окружения =====
GROQ_KEY = os.getenv("GROQ_API_KEY")
FUSION_KEY = os.getenv("FUSIONBRAIN_API_KEY")
FUSION_SECRET = os.getenv("FUSION_SECRET_KEY")

# ===== Генерация статьи через Groq =====
def generate_text(prompt: str) -> str:
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    data = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 2000,
    }
    resp = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data, timeout=30)
    if resp.status_code != 200:
        logger.warning(f"⚠️ Groq вернул статус {resp.status_code}: {resp.text}")
        return fallback_article()
    return resp.json()['choices'][0]['message']['content'].strip()

# ===== Fallback статья =====
def fallback_article() -> str:
    return (
        "# Искусственный интеллект и высокие технологии\n\n"
        "## Введение\n"
        "Искусственный интеллект продолжает активно развиваться, внедряясь в различные отрасли.\n\n"
        "## Основные тенденции\n"
        "- Генеративные нейросети\n"
        "- Автономные системы\n"
        "- Компьютерное зрение\n\n"
        "## Заключение\n"
        "Будущее технологий обещает множество инноваций.\n"
    )

# ===== Генерация изображения через FusionBrain =====
def generate_image(title: str) -> str:
    url = "https://api-key.fusionbrain.ai/text2image/run"
    headers = {"X-Key": FUSION_KEY, "X-Secret": FUSION_SECRET}
    prompt = f"{title}, digital art, futuristic, high quality, professional"
    data = {"prompt": prompt, "width": 512, "height": 512, "num_images": 1}
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=60)
        resp.raise_for_status()
        img_base64 = resp.json()['images'][0]
        img_bytes = base64.b64decode(img_base64)
        filename = GALLERY_DIR / f"{slugify(title)}.png"
        with open(filename, "wb") as f:
            f.write(img_bytes)
        logger.info(f"✅ Изображение создано: {filename}")
        return f"/{filename}"
    except Exception as e:
        logger.error(f"❌ Ошибка генерации изображения FusionBrain: {e}")
        return "/assets/images/default.png"

# ===== Слаг =====
def slugify(text: str) -> str:
    text = re.sub(r'[^a-zA-Z0-9а-яА-Я\s]', '', text).lower()
    text = re.sub(r'\s+', '-', text).strip('-')
    timestamp = str(int(time.time()))[-4:]
    return f"{text[:40]}-{timestamp}"

# ===== Сохранение статьи =====
def save_article(title: str, content: str, image_path: str):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    slug = slugify(title)
    filename = CONTENT_DIR / f"{slug}.md"
    frontmatter = f"""---
title: "{title}"
date: {now}
draft: false
image: "{image_path}"
tags: ["AI", "технологии", "2025"]
categories: ["Искусственный интеллект"]
summary: "Автоматически сгенерированная статья"
---

{content}
"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(frontmatter)
    logger.info(f"📄 Статья сохранена: {filename}")
    return filename

# ===== Ограничение количества статей =====
def prune_old_articles():
    articles = sorted(CONTENT_DIR.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True)
    if len(articles) <= MAX_ARTICLES:
        return
    for old in articles[MAX_ARTICLES:]:
        old.unlink()
        logger.info(f"🗑️ Удалена старая статья: {old}")

# ===== Основная генерация =====
def main():
    logger.info("📝 Генерация статьи через Groq")
    prompt = "Напиши статью на русском языке про нейросети и высокие технологии. Формат Markdown, 400-600 слов."
    content = generate_text(prompt)
    title_line = content.splitlines()[0].replace("#", "").strip()
    title = title_line if title_line else "Нейросети и высокие технологии"
    logger.info(f"📌 Заголовок статьи: {title}")

    logger.info("🎨 Генерация изображения через FusionBrain")
    image_path = generate_image(title)

    save_article(title, content, image_path)
    prune_old_articles()

if __name__ == "__main__":
    main()
