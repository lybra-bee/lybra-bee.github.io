#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import json
import time
import glob
import random
import datetime
import logging
from typing import Dict, List

import requests
import yaml
from groq import Groq

# ================== ЛОГИ ==================
logging.basicConfig(
    filename="generation.log",
    level=logging.INFO,
    format="%(asctime)s | %(message)s"
)
log = logging.getLogger()

# ================== КОНФИГ ==================
POSTS_DIR = "_posts"
ASSETS_DIR = "assets/images/posts"
BASE_URL = "https://lybra-ai.ru"

HF_TOKEN = os.getenv("HF_API_TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")

MAX_ARTICLE_ATTEMPTS = 3

HF_MODELS = [
    "stabilityai/sdxl-turbo",
    "stabilityai/stable-diffusion-xl-base-1.0",
]

# ================== УТИЛИТЫ ==================
def contains_politics(text: str) -> bool:
    banned = [
        "президент", "выбор", "государств", "закон",
        "регулятор", "министр", "партия", "политик",
        "санкц", "страна", "правительств"
    ]
    t = text.lower()
    return any(b in t for b in banned)


def normalize_md(md: str) -> str:
    md = re.sub(r"<[^>]+>", "", md)
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip() + "\n"


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\wа-я0-9]+", "-", text)
    return re.sub(r"-{2,}", "-", text).strip("-")[:60]


# ================== ТРЕНД ==================
EMBEDDED_TRENDS = [
    {"news": "Практическое применение генеративного ИИ в 2025 году", "keywords": ["генеративный ИИ"]},
    {"news": "Мультимодальные модели и их использование в разработке", "keywords": ["LLM", "мультимодальность"]},
    {"news": "Как инженеры используют LLM для ускорения разработки", "keywords": ["LLM", "разработка"]},
]


# ================== ГЕНЕРАЦИЯ ЗАГОЛОВКА ==================
def generate_title(client: Groq, trend: Dict) -> str:
    prompt = (
        "Создай один цепляющий заголовок (5–10 слов).\n"
        "Тематика: ИИ, технологии, разработка.\n"
        "СТРОГО запрещено: политика, страны, государства, регуляторы.\n"
        f"Тема: {trend['news']}\n"
        "Только заголовок."
    )

    r = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=40,
        temperature=0.9
    )
    return r.choices[0].message.content.strip()


# ================== ГЕНЕРАЦИЯ СТАТЬИ ==================
def generate_article(client: Groq, trend: Dict) -> str:
    prompt = f"""
Вы — технический журналист по ИИ.
Аудитория: инженеры, разработчики, стартапы.

СТРОГО ЗАПРЕЩЕНО:
- политика
- государства
- регуляторы
- законы
- лидеры

ТЕМА:
{trend['news']}

ФОРМАТ:
- Markdown
- ## Подзаголовки
- 2 таблицы
- Практические примеры
- Прогнозы

Объём: 1200–2000 слов.
"""

    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=3500,
        temperature=0.85
    )
    return normalize_md(r.choices[0].message.content)


# ================== ИЗОБРАЖЕНИЯ ==================
def hf_generate(prompt: str, path: str, model: str) -> bool:
    try:
        log.info(f"🖼 HF модель: {model}")
        resp = requests.post(
            f"https://api-inference.huggingface.co/models/{model}",
            headers={"Authorization": f"Bearer {HF_TOKEN}"},
            json={"inputs": prompt},
            timeout=120
        )
        if resp.status_code == 200:
            with open(path, "wb") as f:
                f.write(resp.content)
            return True
    except Exception as e:
        log.info(f"❌ HF ошибка: {e}")
    return False


def pollinations_generate(prompt: str, path: str) -> bool:
    try:
        url = "https://image.pollinations.ai/prompt/" + requests.utils.quote(prompt)
        r = requests.get(url, timeout=60)
        if r.status_code == 200:
            with open(path, "wb") as f:
                f.write(r.content)
            return True
    except Exception as e:
        log.info(f"❌ Pollinations ошибка: {e}")
    return False


def fallback_png(path: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.figure(figsize=(10, 5))
    plt.text(0.5, 0.5, "AI • Technology • Future",
             fontsize=24, ha="center", va="center")
    plt.axis("off")
    plt.savefig(path, dpi=150)
    plt.close()


def generate_image(title: str, post_num: int) -> str:
    prompt = (
        "Ultra realistic photo, cinematic lighting, modern AI technology, "
        "servers, holograms, futuristic workspace, professional photography, "
        "no charts, no graphs, no diagrams, no text, no UI, photorealistic, 8k"
    )

    path = f"{ASSETS_DIR}/post-{post_num}.png"

    for model in HF_MODELS:
        if HF_TOKEN and hf_generate(prompt, path, model):
            log.info("✅ Изображение: HuggingFace")
            return path

    if pollinations_generate(prompt, path):
        log.info("✅ Изображение: Pollinations")
        return path

    fallback_png(path)
    log.info("🖼 PNG fallback")
    return path


# ================== TELEGRAM ==================
def send_telegram(title: str, teaser: str, image_path: str):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat:
        log.info("⚠️ Telegram ключи отсутствуют")
        return

    msg = f"*Новая статья*\n\n{teaser}\n\n[Читать на сайте]({BASE_URL})"

    r = requests.post(
        f"https://api.telegram.org/bot{token}/sendPhoto",
        data={"chat_id": chat, "caption": msg, "parse_mode": "Markdown"},
        files={"photo": open(image_path, "rb")}
    )
    log.info(f"📢 Telegram статус: {r.status_code}")


# ================== MAIN ==================
def main():
    log.info("🚀 Запуск генерации")

    os.makedirs(POSTS_DIR, exist_ok=True)
    os.makedirs(ASSETS_DIR, exist_ok=True)

    client = Groq(api_key=GROQ_KEY)
    trend = random.choice(EMBEDDED_TRENDS)

    for attempt in range(1, MAX_ARTICLE_ATTEMPTS + 1):
        log.info(f"✍️ Попытка {attempt}: {trend['news']}")

        title = generate_title(client, trend)
        article = generate_article(client, trend)

        if contains_politics(title + article):
            log.info("⚠️ Обнаружена политика — регенерация")
            continue

        today = datetime.date.today().isoformat()
        slug = slugify(title)
        filename = f"{POSTS_DIR}/{today}-{slug}.md"

        images = glob.glob(f"{ASSETS_DIR}/*.png")
        post_num = len(images) + 1

        image_path = generate_image(title, post_num)

        fm = {
            "title": title,
            "date": f"{today} 00:00:00 +0000",
            "layout": "post",
            "image": f"/{image_path}",
            "tags": ["ИИ", "AI", "технологии"],
        }

        with open(filename, "w", encoding="utf-8") as f:
            f.write("---\n")
            yaml.dump(fm, f, allow_unicode=True)
            f.write("---\n\n")
            f.write(article)

        teaser = " ".join(article.split()[:30]) + "…"
        send_telegram(title, teaser, image_path)

        log.info(f"💾 Статья сохранена: {filename}")
        log.info("✅ Успешно завершено")
        return

    raise RuntimeError("❌ Не удалось сгенерировать статью без политики")


if __name__ == "__main__":
    main()
