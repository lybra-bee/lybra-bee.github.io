#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import json
import time
import yaml
import uuid
import math
import shutil
import random
import string
import logging
import datetime
import requests
from pathlib import Path
from typing import List

from groq import Groq
from PIL import Image
from io import BytesIO

# ================== НАСТРОЙКИ ==================

POSTS_DIR = Path("_posts")
IMAGES_DIR = Path("assets/images/posts")
LOG_FILE = "generation.log"

POSTS_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

MODEL = "llama-3.3-70b-versatile"

MAX_ARTICLE_TRIES = 2

# ================== ЛОГИ ==================

def log(msg: str):
    print(msg)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

# ================== АНТИ-ПОЛИТИКА ==================

POLITICAL_PATTERNS = [
    r"\bвыбор",
    r"\bпрезидент",
    r"\bправитель",
    r"\bгос",
    r"\bсанкц",
    r"\bзакон",
    r"\bуказ",
    r"\bминистер",
    r"\bпарламент",
    r"\bпарт",
    r"\bстрана\b",
    r"\bвойн",
]

def detect_politics(text: str) -> bool:
    text = text.lower()
    return any(re.search(p, text) for p in POLITICAL_PATTERNS)

# ================== ТРЕНДЫ ==================

SAFE_TRENDS = [
    "Практическое применение генеративного ИИ в бизнесе",
    "Инструменты автоматизации с использованием LLM",
    "Как инженеры используют ИИ для ускорения разработки",
    "Будущее мультимодальных моделей",
    "AI-агенты и автономные системы",
    "Open Source модели и их применение",
]

def get_trend() -> str:
    trend = random.choice(SAFE_TRENDS)
    log(f"📰 Тренд: {trend}")
    return trend

# ================== LLM ==================

def build_article_prompt(trend: str) -> str:
    return f"""
Ты — профессиональный технический автор.

СТРОГО ЗАПРЕЩЕНО:
- политика
- государства
- законы
- указы
- страны
- руководители стран
- выборы
- войны
- санкции

РАЗРЕШЕНО ТОЛЬКО:
- искусственный интеллект
- LLM
- генеративные модели
- инструменты
- инженерные подходы
- бизнес-применение
- стартапы
- исследования
- Open Source

Тема статьи:
{trend}

Требования:
- интересная подача
- практическая польза
- живой язык
- без упоминаний политики в любом виде

Формат:
- Заголовок
- 4–6 абзацев
"""

def generate_article(client: Groq, trend: str) -> str:
    prompt = build_article_prompt(trend)

    completion = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
    )

    article = completion.choices[0].message.content.strip()
    return article

# ================== ИЗОБРАЖЕНИЕ ==================

def generate_image(prompt: str) -> Path:
    image_path = IMAGES_DIR / f"post-{int(time.time())}.png"

    # ---- Stability AI ----
    stab_key = os.getenv("STABILITYAI_KEY")
    if stab_key:
        try:
            r = requests.post(
                "https://api.stability.ai/v2beta/stable-image/generate/core",
                headers={
                    "Authorization": f"Bearer {stab_key}",
                    "Accept": "image/png"
                },
                files={
                    "prompt": (None, prompt),
                    "output_format": (None, "png")
                },
                timeout=60
            )
            if r.status_code == 200:
                with open(image_path, "wb") as f:
                    f.write(r.content)
                log("🖼️ Изображение: Stability AI")
                return image_path
        except Exception as e:
            log(f"⚠️ Stability AI ошибка: {e}")

    # ---- HuggingFace ----
    hf_token = os.getenv("HF_API_TOKEN")
    if hf_token:
        try:
            r = requests.post(
                "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0",
                headers={"Authorization": f"Bearer {hf_token}"},
                json={"inputs": prompt},
                timeout=60
            )
            if r.status_code == 200:
                img = Image.open(BytesIO(r.content))
                img.save(image_path, format="PNG")
                log("🖼️ Изображение: HuggingFace")
                return image_path
        except Exception as e:
            log(f"⚠️ HF ошибка: {e}")

    # ---- FALLBACK ----
    img = Image.new("RGB", (1024, 1024), (30, 30, 30))
    img.save(image_path, format="PNG")
    log("🖼️ Изображение: fallback")
    return image_path

# ================== СОХРАНЕНИЕ ==================

def save_post(title: str, content: str, image_name: str):
    today = datetime.date.today()
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", title.lower()).strip("-")
    filename = POSTS_DIR / f"{today}-{slug}.md"

    front_matter = {
        "layout": "post",
        "title": title,
        "image": f"/assets/images/posts/{image_name}",
        "date": today.isoformat()
    }

    with open(filename, "w", encoding="utf-8") as f:
        f.write("---\n")
        yaml.dump(front_matter, f, allow_unicode=True)
        f.write("---\n\n")
        f.write(content)

    log(f"💾 Пост сохранён: {filename}")

# ================== MAIN ==================

def main() -> bool:
    log("🚀 Запуск генерации")

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    trend = get_trend()

    article = None
    for attempt in range(MAX_ARTICLE_TRIES):
        article = generate_article(client, trend)

        if detect_politics(article):
            log("⚠️ Обнаружена политика, регенерация")
            trend = random.choice(SAFE_TRENDS)
            continue

        break

    if not article:
        log("❌ Не удалось сгенерировать статью")
        return False

    lines = article.splitlines()
    title = lines[0].replace("Заголовок:", "").strip()
    body = "\n".join(lines[1:]).strip()

    log(f"📰 Заголовок: {title}")

    img_prompt = f"Photorealistic illustration about: {trend}, ultra realistic, cinematic light"
    image_path = generate_image(img_prompt)

    save_post(title, body, image_path.name)

    log("✅ Генерация завершена")
    return True

# ================== ENTRY ==================

if __name__ == "__main__":
    today = datetime.date.today()
    success = main()
    raise SystemExit(0 if success else 1)
