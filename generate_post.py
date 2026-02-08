#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import time
import json
import random
import logging
import requests
import tempfile
from datetime import datetime
from pathlib import Path

# -------------------- LOGGING --------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logging.info("=== START ===")

# -------------------- PATHS --------------------
POSTS_DIR = Path("_posts")
IMAGES_DIR = Path("assets/images/posts")

POSTS_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# -------------------- ENV --------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
FLUX_API_KEY = os.getenv("FLUX_API_KEY")

SITE_URL = "https://lybra-ai.ru"

if not GROQ_API_KEY:
    raise RuntimeError("❌ GROQ_API_KEY missing")

if not FLUX_API_KEY:
    logging.warning("⚠ FLUX_API_KEY missing — images fallback only")

# -------------------- FALLBACK IMAGES --------------------
FALLBACK_IMAGES = [
    "https://picsum.photos/1024/768?random=1",
    "https://picsum.photos/1024/768?random=2",
    "https://picsum.photos/1024/768?random=3",
    "https://picsum.photos/1024/768?random=4",
]

# -------------------- TRANSLIT --------------------
TRANSLIT_MAP = {
    'а': 'a','б': 'b','в': 'v','г': 'g','д': 'd','е': 'e','ё': 'yo',
    'ж': 'zh','з': 'z','и': 'i','й': 'y','к': 'k','л': 'l','м': 'm',
    'н': 'n','о': 'o','п': 'p','р': 'r','с': 's','т': 't','у': 'u',
    'ф': 'f','х': 'kh','ц': 'ts','ч': 'ch','ш': 'sh','щ': 'shch',
    'ъ': '','ы': 'y','ь': '','э': 'e','ю': 'yu','я': 'ya'
}

def translit(text):
    return ''.join(TRANSLIT_MAP.get(c, c) for c in text.lower())

# -------------------- GOOGLE TRENDS TOPIC --------------------
def fetch_google_trends_topic():
    logging.info("🌍 Fetching Google Trends topic")

    try:
        url = "https://trends.google.com/trends/hottrends/visualize/internal/data"
        r = requests.get(url, timeout=10)
        data = r.json()

        topics = []
        for block in data.get("trendsByDateList", []):
            for trend in block.get("trendsList", []):
                title = trend.get("title")
                if title:
                    topics.append(title)

        topic = random.choice(topics) if topics else "AI tools"
        logging.info(f"🔥 Google Trends topic: {topic}")
        return topic

    except Exception as e:
        logging.warning(f"Google Trends failed: {e}")
        return random.choice([
            "AI tools",
            "AI productivity",
            "AI for developers",
            "AI automation"
        ])

# -------------------- GROQ REQUEST --------------------
def groq_request(prompt, max_tokens=900, temperature=0.6, retries=4):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}

    for i in range(retries):
        logging.info(f"Groq request attempt {i+1}/{retries}")

        try:
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature
            }

            r = requests.post(url, headers=headers, json=payload, timeout=60)
            r.raise_for_status()

            return r.json()["choices"][0]["message"]["content"]

        except Exception as e:
            logging.warning(f"Groq error: {e}")
            time.sleep(2)

    raise RuntimeError("Groq failed")

# -------------------- TITLE --------------------
def generate_title(topic):
    prompt = f"""
Сгенерируй ОДИН прикладной заголовок статьи.

Тема: {topic}

Требования:
- 8–14 слов
- Только практическая польза
- Без футуризма
- Без воды

Формат:
ЗАГОЛОВОК: ...
"""

    raw = groq_request(prompt, max_tokens=120)
    logging.info(f"Groq title raw: {raw}")

    match = re.search(r"ЗАГОЛОВОК:\s*(.+)", raw)
    if not match:
        return "Практическое применение ИИ для решения реальных задач"

    title = match.group(1).strip()
    logging.info(f"✅ Title: {title}")
    return title

# -------------------- OUTLINE --------------------
def generate_outline(title):
    prompt = f"""
Создай план прикладной статьи:

"{title}"

Формат:
- 6–8 разделов ##
- Только практика
- Без философии

Markdown only.
"""

    return groq_request(prompt, max_tokens=900)

# -------------------- SECTION --------------------
def generate_section(title, outline, section):
    prompt = f"""
Статья: "{title}"
Раздел: {section}

Контекст плана:
{outline}

Требования:
- 900–1200 знаков
- Реальные советы
- Ошибки и кейсы
- Без воды
"""

    return groq_request(prompt, max_tokens=800)

# -------------------- BODY --------------------
def generate_body(title):
    logging.info("📚 Generating outline")
    outline = generate_outline(title)
    logging.info("✅ Outline generated")

    headers = [re.sub(r'^##\s*', '', l) for l in outline.splitlines() if l.startswith("##")]

    body = f"# {title}\n\n"
    total = 0

    for h in headers:
        logging.info(f"🧩 Generating section: {h}")
        text = generate_section(title, outline, h)
        body += f"## {h}\n\n{text}\n\n"
        total += len(text)

    logging.info(f"📏 Body length: {total}")

    if total < 6000:
        raise RuntimeError("❌ Article too short")

    return body

# -------------------- FLUX IMAGE --------------------
def generate_image_flux(title):
    if not FLUX_API_KEY:
        return None

    logging.info("🎨 Generating image via FLUX")

    url = "https://api.bfl.ml/v1/flux-pro-1.1"

    prompt = f"Professional illustration for article: {title}, realistic, sharp, editorial, high quality"

    headers = {
        "Authorization": f"Bearer {FLUX_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "prompt": prompt,
        "width": 1024,
        "height": 768,
        "steps": 30
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=90)
        r.raise_for_status()

        image_url = r.json().get("url")

        if not image_url:
            return None

        img = requests.get(image_url).content
        path = IMAGES_DIR / f"flux-{int(time.time())}.png"
        path.write_bytes(img)

        logging.info(f"🖼 Image saved: {path}")
        return str(path)

    except Exception as e:
        logging.warning(f"Flux image failed: {e}")
        return None

# -------------------- IMAGE FALLBACK --------------------
def generate_image(title):
    local = generate_image_flux(title)

    if local and os.path.exists(local):
        return local

    fallback = random.choice(FALLBACK_IMAGES)
    logging.warning(f"⚠ Using fallback image: {fallback}")
    return fallback

# -------------------- SAVE POST --------------------
def save_post(title, body, image):
    date = datetime.now()
    slug = re.sub(r'[^a-z0-9-]+', '-', translit(title)).strip('-')[:80]
    file = POSTS_DIR / f"{date:%Y-%m-%d}-{slug}.md"

    image_path = image if image.startswith("http") else "/assets/images/posts/" + Path(image).name

    front = f"""---
title: "{title}"
date: {date:%Y-%m-%d 00:00:00 -0000}
layout: post
categories: ai
image: {image_path}
---

"""

    file.write_text(front + body, encoding="utf-8")
    logging.info(f"📝 Post saved: {file}")
    return SITE_URL

# -------------------- TELEGRAM --------------------
def send_to_telegram(title, teaser, image):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logging.warning("Telegram disabled")
        return

    caption = f"<b>{title}</b>\n\n{teaser}\n\n<i>Читать:</i> {SITE_URL}"

    if image.startswith("http"):
        img = requests.get(image).content
        f = tempfile.NamedTemporaryFile(delete=False)
        f.write(img)
        f.close()
        image = f.name

    with open(image, "rb") as p:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto",
            data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption, "parse_mode": "HTML"},
            files={"photo": p},
        )

    logging.info("📬 Telegram sent")

# -------------------- CLEAN OLD POSTS --------------------
def cleanup_posts(limit=70):
    posts = sorted(POSTS_DIR.glob("*.md"), reverse=True)

    if len(posts) <= limit:
        return

    for old in posts[limit:]:
        logging.info(f"🧹 Removing old post: {old}")
        old.unlink()

# -------------------- MAIN --------------------
def main():
    topic = fetch_google_trends_topic()
    logging.info(f"🎯 Topic: {topic}")

    title = generate_title(topic)
    body = generate_body(title)
    image = generate_image(title)

    save_post(title, body, image)

    teaser = " ".join(body.split()[:40]) + "..."
    send_to_telegram(title, teaser, image)

    cleanup_posts()

    logging.info("=== DONE ===")

if __name__ == "__main__":
    main()
