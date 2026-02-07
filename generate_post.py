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

log = logging.getLogger()

POSTS_DIR = Path("_posts")
IMAGES_DIR = Path("assets/images/posts")

POSTS_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
HORDE_API_KEY = os.getenv("HORDE_API_KEY")

SITE_URL = "https://lybra-ai.ru"

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY не установлен!")

FALLBACK_IMAGES = [
    "https://picsum.photos/1024/768?random=1",
    "https://picsum.photos/1024/768?random=2",
    "https://picsum.photos/1024/768?random=3",
    "https://picsum.photos/1024/768?random=4",
]

TRANSLIT_MAP = {
    'а': 'a','б': 'b','в': 'v','г': 'g','д': 'd','е': 'e','ё': 'yo','ж': 'zh','з': 'z',
    'и': 'i','й': 'y','к': 'k','л': 'l','м': 'm','н': 'n','о': 'o','п': 'p','р': 'r',
    'с': 's','т': 't','у': 'u','ф': 'f','х': 'kh','ц': 'ts','ч': 'ch','ш': 'sh',
    'щ': 'shch','ъ': '','ы': 'y','ь': '','э': 'e','ю': 'yu','я': 'ya'
}

def translit(text):
    return ''.join(TRANSLIT_MAP.get(c, c) for c in text.lower())

# -------------------- GOOGLE TRENDS --------------------
def get_google_trends_topic():
    log.info("🌍 Fetching Google Trends topic")
    try:
        r = requests.get("https://trends.google.com/trends/hottrends/visualize/internal/data", timeout=10)
        if not r.ok:
            return "AI tools"
        topics = re.findall(r'"title":\{"query":"([^"]+)"', r.text)
        if topics:
            topic = random.choice(topics)
            log.info(f"🔥 Google Trends topic: {topic}")
            return topic + " practical AI"
    except Exception as e:
        log.warning(f"Google Trends failed: {e}")

    return "AI tools practical"

# -------------------- GROQ REQUEST --------------------
def groq_request(prompt, max_tokens=900, temperature=0.6):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature
    }

    for attempt in range(4):
        try:
            log.info(f"Groq request attempt {attempt+1}/4")
            r = requests.post(url, headers=headers, json=payload, timeout=60)

            if r.status_code == 429:
                time.sleep(3)
                continue

            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]

        except Exception as e:
            log.warning(f"Groq retry error: {e}")
            time.sleep(2)

    raise RuntimeError("Groq failed after retries")

# -------------------- TITLE --------------------
def generate_title(topic):
    log.info(f"✍️ Generating title: {topic}")

    prompt = f"""
Сгенерируй ОДИН прикладной заголовок статьи на русском.

Тема: {topic}

Требования:
- 8–14 слов
- Практическая польза
- Без футуризма
- Без философии
- Конкретная выгода

Формат ответа:
ЗАГОЛОВОК: ...
"""

    text = groq_request(prompt, max_tokens=120)
    log.info(f"Groq title raw: {text}")

    match = re.search(r"ЗАГОЛОВОК:\s*(.+)", text)
    if match:
        title = match.group(1).strip()
        log.info(f"✅ Title: {title}")
        return title

    fallback = "Как эффективно применять ИИ в практических задачах"
    log.warning(f"⚠ Using fallback title: {fallback}")
    return fallback

# -------------------- OUTLINE --------------------
def generate_outline(title):
    log.info("📚 Generating outline")

    prompt = f"""
Создай план ПРАКТИЧЕСКОЙ статьи по заголовку:

"{title}"

Формат:
- 6–9 разделов ##
- Реальные советы
- Кейсы
- Ошибки
- Инструменты

Ответ только Markdown.
"""

    outline = groq_request(prompt, max_tokens=900, temperature=0.4)
    log.info("✅ Outline generated")
    return outline

# -------------------- SECTION --------------------
def generate_section(title, outline, section):
    log.info(f"🧩 Generating section: {section}")

    prompt = f"""
Статья: "{title}"

Раздел: {section}

Контекст плана:
{outline}

Требования:
- 900–1500 знаков
- Практика
- Примеры
- Кейсы
- Без воды
"""

    return groq_request(prompt, max_tokens=900, temperature=0.65)

# -------------------- BODY --------------------
def generate_body(title):
    log.info("📝 Generating article body")

    outline = generate_outline(title)
    headers = [re.sub(r'^##\s*', '', l) for l in outline.splitlines() if l.startswith("##")]

    body = f"# {title}\n\n"
    total = 0

    for h in headers:
        text = generate_section(title, outline, h)
        body += f"## {h}\n\n{text}\n\n"
        total += len(text)

    log.info(f"📏 Body length: {total}")

    if total < 8000:
        raise RuntimeError("Статья слишком короткая")

    return body

# -------------------- IMAGE (HORDE) --------------------
def generate_image_horde(title):
    log.info("🎨 Horde image generation started")

    styles = [
        "developer working with AI",
        "machine learning workflow",
        "neural network visualization",
        "coding with AI assistant",
        "AI automation in real business"
    ]

    style = random.choice(styles)
    prompt = f"{title}, {style}, ultra realistic, professional photography, 8k"
    negative_prompt = "girl, woman, cartoon, blurry, watermark"

    url_async = "https://stablehorde.net/api/v2/generate/async"

    payload = {
        "prompt": prompt + " ### " + negative_prompt,
        "models": ["Juggernaut XL", "Realistic Vision V5.1", "SDXL 1.0"],
        "params": {
            "width": 768,
            "height": 512,
            "steps": 30,
            "cfg_scale": 7.5,
            "sampler_name": "k_euler_a",
            "n": 1
        },
        "nsfw": False,
        "trusted_workers": False,
        "slow_workers": True
    }

    headers = {
        "apikey": HORDE_API_KEY,  # Используем API ключ из переменной окружения
        "Client-Agent": "LybraBlogBot:3.0",
        "Content-Type": "application/json"
    }

    try:
        log.info("📡 Sending Horde request")
        r = requests.post(url_async, json=payload, headers=headers, timeout=60)

        if not r.ok:
            log.warning(f"Horde failed: {r.text}")
            return None

        job_id = r.json().get("id")
        if not job_id:
            log.warning("No Horde job id")
            return None

        log.info(f"🧩 Horde job id: {job_id}")

        check_url = f"https://stablehorde.net/api/v2/generate/check/{job_id}"
        status_url = f"https://stablehorde.net/api/v2/generate/status/{job_id}"

        for i in range(45):
            time.sleep(8)
            check = requests.get(check_url, headers=headers).json()

            queue = check.get("queue_position")
            waiting = check.get("waiting")
            done = check.get("done")

            log.info(f"⏳ Horde progress: queue={queue}, waiting={waiting}, done={done}")

            if done:
                final = requests.get(status_url, headers=headers).json()

                if final.get("generations"):
                    img_url = final["generations"][0]["img"]
                    log.info(f"📥 Downloading image: {img_url}")

                    img_data = requests.get(img_url, timeout=60).content
                    path = IMAGES_DIR / f"horde-{int(time.time())}.jpg"
                    path.write_bytes(img_data)

                    log.info(f"🖼 Horde image saved: {path}")
                    return str(path)

        log.warning("⏱ Horde timeout")
        return None

    except Exception as e:
        log.exception(f"Horde exception: {e}")
        return None

def generate_image(title):
    local = generate_image_horde(title)
    if local and os.path.exists(local):
        return local

    fallback = random.choice(FALLBACK_IMAGES)
    log.warning(f"⚠ Using fallback image: {fallback}")
    return fallback

# -------------------- SAVE POST --------------------
def save_post(title, body, image):
    date = datetime.now()
    slug = re.sub(r'[^a-z0-9-]+', '-', translit(title)).strip('-')[:80]
    file = POSTS_DIR / f"{date:%Y-%m-%d}-{slug}.md"

    image_url = image if image.startswith("http") else "/assets/images/posts/" + Path(image).name

    front = f"""---
title: "{title}"
date: {date:%Y-%m-%d 00:00:00 -0000}
layout: post
categories: ai
image: {image_url}
---

"""

    file.write_text(front + body, encoding="utf-8")
    log.info(f"📝 Post saved: {file}")

# -------------------- TELEGRAM --------------------
def send_to_telegram(title, teaser, image):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log.warning("Telegram disabled")
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

    log.info("📬 Telegram sent")

# -------------------- CLEAN POSTS --------------------
def cleanup_posts(limit=70):
    posts = sorted(POSTS_DIR.glob("*.md"))
    if len(posts) <= limit:
        return

    to_delete = posts[:-limit]
    for p in to_delete:
        log.info(f"🧹 Removing old post: {p}")
        p.unlink()

# -------------------- MAIN --------------------
def main():
    log.info("=== START ===")

    topic = get_google_trends_topic()
    log.info(f"🎯 Topic: {topic}")

    title = generate_title(topic)
    body = generate_body(title)

    image = generate_image(title)
    log.info(f"🖼 Image: {image}")

    save_post(title, body, image)

    teaser = " ".join(body.split()[:40]) + "..."
    send_to_telegram(title, teaser, image)

    cleanup_posts()

    log.info("=== DONE ===")

if __name__ == "__main__":
    main()
