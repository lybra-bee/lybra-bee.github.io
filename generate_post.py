#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Автогенерация статьи + изображения + Telegram
Stable / GitHub Actions ready
"""

import os
import re
import json
import time
import yaml
import glob
import random
import logging
import datetime
from io import BytesIO
from typing import List, Dict

import requests
from groq import Groq

# =======================
# CONFIG
# =======================

POSTS_DIR = "_posts"
ASSETS_DIR = "assets/images/posts"
TRENDS_FILE = "trends_cache.json"

MAX_RETRIES_ARTICLE = 3

# =======================
# LOGGING
# =======================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
)
log = logging.getLogger("GEN")

# =======================
# EMBEDDED TRENDS
# =======================

EMBEDDED_TRENDS = [
    {
        "news": "Large Language Models accelerate software development workflows",
        "keywords": ["LLM", "software", "engineering"],
    },
    {
        "news": "Multimodal AI systems combine vision, audio and text",
        "keywords": ["multimodal AI", "vision models"],
    },
    {
        "news": "AI inference efficiency improves by 200 percent in two years",
        "keywords": ["AI efficiency", "inference"],
    },
]

# =======================
# HELPERS
# =======================

POLITICAL_WORDS = [
    "президент", "правительство", "государств", "политик",
    "выбор", "партия", "закон", "указ", "санкц"
]

def contains_politics(text: str) -> bool:
    t = text.lower()
    return any(w in t for w in POLITICAL_WORDS)

def slugify(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"\s+", "-", text)[:60]

def normalize_md(md: str) -> str:
    md = re.sub(r"<[^>]+>", "", md)
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip() + "\n"

# =======================
# TRENDS
# =======================

def load_trends() -> List[Dict]:
    if os.path.exists(TRENDS_FILE):
        try:
            with open(TRENDS_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)
                if time.time() - cache.get("ts", 0) < 86400:
                    log.info("✅ Тренды из кэша")
                    return cache["trends"]
        except Exception as e:
            log.warning(f"Cache error: {e}")

    log.info("⚠️ Используем встроенные тренды")
    return EMBEDDED_TRENDS

# =======================
# TEXT GENERATION
# =======================

def generate_title(client: Groq, trend: Dict) -> str:
    prompt = f"""
Создай один технический заголовок (5–10 слов).
Тема: {trend['news']}
СТРОГО запрещено: политика, страны, лидеры, правительства.
"""

    r = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "Русский техредактор по ИИ"},
            {"role": "user", "content": prompt},
        ],
        max_tokens=40,
        temperature=0.8,
    )
    return r.choices[0].message.content.strip()

def generate_article(client: Groq, trend: Dict) -> str:
    prompt = f"""
Напиши техническую статью (1000–1500 слов) на русском языке.
Тема: {trend['news']}

СТРОГО ЗАПРЕЩЕНО:
- политика
- страны
- лидеры
- правительства

Формат Markdown, таблицы приветствуются.
"""

    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "Технический журналист по ИИ"},
            {"role": "user", "content": prompt},
        ],
        max_tokens=3500,
        temperature=0.7,
    )

    return normalize_md(r.choices[0].message.content)

# =======================
# IMAGE GENERATION
# =======================

def image_from_huggingface(prompt: str, out_path: str) -> bool:
    token = os.getenv("HF_API_TOKEN")
    if not token:
        return False

    try:
        r = requests.post(
            "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1",
            headers={"Authorization": f"Bearer {token}"},
            json={"inputs": prompt},
            timeout=60,
        )
        img = BytesIO(r.content)
        from PIL import Image
        Image.open(img).save(out_path)
        log.info("🖼 HF OK")
        return True
    except Exception as e:
        log.warning(f"HF fail: {e}")
        return False

def image_from_stability(prompt: str, out_path: str) -> bool:
    key = os.getenv("STABILITYAI_KEY")
    if not key:
        return False

    try:
        r = requests.post(
            "https://api.stability.ai/v2beta/stable-image/generate/sd3",
            headers={
                "Authorization": f"Bearer {key}",
                "Accept": "image/png",
            },
            files={"prompt": (None, prompt)},
            timeout=60,
        )
        if r.status_code == 200:
            with open(out_path, "wb") as f:
                f.write(r.content)
            log.info("🖼 Stability OK")
            return True
    except Exception as e:
        log.warning(f"Stability fail: {e}")
    return False

def image_fallback_chart(out_path: str) -> bool:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        years = ["2023", "2024", "2025"]
        values = [80, 150, 260]

        plt.figure(figsize=(10, 5))
        plt.plot(years, values, marker="o")
        plt.title("AI Technology Growth")
        plt.tight_layout()
        plt.savefig(out_path, dpi=150)
        plt.close()

        log.info("📊 Fallback chart")
        return True
    except Exception as e:
        log.error(f"Chart fail: {e}")
        return False

def generate_image(title: str, out_path: str) -> None:
    prompt = f"Ultra realistic illustration of {title}, futuristic AI technology, 8k"

    generators = [
        image_from_huggingface,
        image_from_stability,
        lambda p, o: image_fallback_chart(o),
    ]

    for gen in generators:
        if gen(prompt, out_path):
            return

    raise RuntimeError("Image generation failed")

# =======================
# TELEGRAM
# =======================

def send_telegram(title: str, image_path: str, url: str) -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat:
        log.warning("⚠️ Telegram пропущен (нет ключей)")
        return

    with open(image_path, "rb") as f:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendPhoto",
            data={
                "chat_id": chat,
                "caption": f"*Новая статья*\n\n{title}\n\n{url}",
                "parse_mode": "Markdown",
            },
            files={"photo": f},
            timeout=30,
        )

    log.info("📢 Telegram отправлен")

# =======================
# MAIN
# =======================

def main():
    log.info("🚀 Запуск генерации")

    os.makedirs(POSTS_DIR, exist_ok=True)
    os.makedirs(ASSETS_DIR, exist_ok=True)

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    trends = load_trends()
    trend = random.choice(trends)

    for attempt in range(1, MAX_RETRIES_ARTICLE + 1):
        log.info(f"✍️ Попытка {attempt}")
        title = generate_title(client, trend)
        article = generate_article(client, trend)

        if not contains_politics(title + article):
            break
        log.warning("⚠️ Политика обнаружена — реген")
    else:
        raise RuntimeError("Не удалось убрать политику")

    today = datetime.date.today().isoformat()
    slug = slugify(title)
    post_path = f"{POSTS_DIR}/{today}-{slug}.md"

    img_index = len(glob.glob(f"{ASSETS_DIR}/*.png")) + 1
    img_path = f"{ASSETS_DIR}/post-{img_index}.png"

    generate_image(title, img_path)

    front = {
        "title": title,
        "date": f"{today} 00:00:00 +0000",
        "layout": "post",
        "image": f"/assets/images/posts/post-{img_index}.png",
        "tags": ["ИИ", "технологии"],
    }

    with open(post_path, "w", encoding="utf-8") as f:
        f.write("---\n")
        yaml.dump(front, f, allow_unicode=True)
        f.write("---\n\n")
        f.write(article)

    log.info(f"💾 Статья сохранена: {post_path}")

    send_telegram(title, img_path, "https://lybra-ai.ru")

    log.info("✅ Успешно завершено")

# =======================

if __name__ == "__main__":
    main()
