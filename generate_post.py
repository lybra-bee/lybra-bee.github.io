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
from collections import deque

# ================== LOGGING ==================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
log = logging.getLogger(__name__)

# ================== PATHS ==================
POSTS_DIR = Path("_posts")
IMAGES_DIR = Path("assets/images/posts")
MEMORY_FILE = Path("ai_topic_memory.json")

POSTS_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# ================== ENV ==================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

SITE_URL = "https://lybra-ai.ru"

if not GROQ_API_KEY:
    raise RuntimeError("❌ GROQ_API_KEY не установлен")

# ================== FALLBACK IMAGES ==================
FALLBACK_IMAGES = [
    "https://picsum.photos/1024/768?random=1",
    "https://picsum.photos/1024/768?random=2",
    "https://picsum.photos/1024/768?random=3",
]

# ================== TRANSLIT ==================
TRANSLIT_MAP = {
    'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'yo','ж':'zh','з':'z','и':'i','й':'y',
    'к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r','с':'s','т':'t','у':'u','ф':'f',
    'х':'kh','ц':'ts','ч':'ch','ш':'sh','щ':'shch','ъ':'','ы':'y','ь':'','э':'e','ю':'yu','я':'ya'
}

def translit(text):
    return ''.join(TRANSLIT_MAP.get(c, c) for c in text.lower())

# ================== MEMORY ==================
def load_memory():
    if MEMORY_FILE.exists():
        return json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
    return {"topics": []}

def save_memory(mem):
    MEMORY_FILE.write_text(json.dumps(mem, ensure_ascii=False, indent=2), encoding="utf-8")

# ================== GOOGLE TRENDS TOPIC ==================
def fetch_google_trends_topic():
    log.info("🌍 Fetching Google Trends topic")
    try:
        r = requests.get("https://trends.google.com/trends/hottrends", timeout=10)
        text = r.text.lower()
        candidates = re.findall(r"ai|machine learning|llm|chatgpt|openai|deep learning", text)
        if candidates:
            topic = random.choice(candidates)
            log.info(f"🔥 Google Trends topic: {topic}")
            return f"{topic} practical AI"
    except Exception as e:
        log.warning(f"Google Trends error: {e}")
    return None

# ================== SMART TOPIC GENERATION ==================
def generate_topic():
    mem = load_memory()
    used = set(mem["topics"])

    base_prompt = """
Сгенерируй ОДНУ новую актуальную тему статьи про нейросети и AI.

Правила:
- Только практика
- Для разработчиков и энтузиастов
- Без футуризма
- Без бизнеса
- Без повторов прошлых тем
- Актуально на 2025–2026
- Примеры: ускорение inference, fine-tuning, агенты, open-source, локальные модели, multimodal

Формат ответа:
ТЕМА: ...
"""

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}

    for attempt in range(4):
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": base_prompt}],
            "temperature": 0.9,
            "max_tokens": 120
        }

        r = requests.post(url, headers=headers, json=payload, timeout=60)
        text = r.json()["choices"][0]["message"]["content"]

        match = re.search(r"ТЕМА:\s*(.+)", text)
        if match:
            topic = match.group(1).strip()
            if topic not in used:
                mem["topics"].append(topic)
                save_memory(mem)
                log.info(f"🧠 Topic selected: {topic}")
                return topic

    fallback = "Практическое использование AI для разработчиков"
    log.warning(f"⚠ Fallback topic: {fallback}")
    return fallback

# ================== TITLE ==================
def generate_title(topic):
    log.info(f"✍️ Generating title: {topic}")

    prompt = f"""
Сделай прикладной заголовок статьи.

Тема: {topic}

Требования:
- 8–14 слов
- Практика
- Без футуризма
- Без воды
- Конкретная польза

Формат:
ЗАГОЛОВОК: ...
"""

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}

    for attempt in range(3):
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 120
        }

        r = requests.post(url, headers=headers, json=payload, timeout=60)
        text = r.json()["choices"][0]["message"]["content"]
        log.info(f"Groq title raw: {text}")

        match = re.search(r"ЗАГОЛОВОК:\s*(.+)", text)
        if match:
            title = match.group(1).strip()
            if 6 <= len(title.split()) <= 16:
                log.info(f"✅ Title: {title}")
                return title

    fallback = "Практическое использование нейросетей для реальных задач разработчика"
    log.warning(f"⚠ Title fallback: {fallback}")
    return fallback

# ================== OUTLINE ==================
def generate_outline(title):
    log.info("📚 Generating outline")

    prompt = f"""
Создай план практической статьи:

"{title}"

Требования:
- 6–9 разделов ##
- Только практика
- Кейсы, ошибки, советы
- Без философии

Формат: Markdown
"""

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.4,
        "max_tokens": 800
    }

    r = requests.post(url, headers=headers, json=payload, timeout=60)
    outline = r.json()["choices"][0]["message"]["content"]
    log.info("✅ Outline generated")
    return outline

# ================== SECTION ==================
def generate_section(title, outline, section):
    log.info(f"🧩 Generating section: {section}")

    prompt = f"""
Статья: "{title}"
Раздел: {section}

Контекст плана:
{outline}

Правила:
- 900–1500 знаков
- Практика
- Команды, примеры, код
- Ошибки и советы
- Без воды
"""

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}

    for attempt in range(3):
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.6,
            "max_tokens": 800
        }

        r = requests.post(url, headers=headers, json=payload, timeout=60)

        if r.status_code == 429:
            log.warning("⏳ Groq rate limit — waiting")
            time.sleep(5)
            continue

        r.raise_for_status()
        text = r.json()["choices"][0]["message"]["content"].strip()

        if len(text) > 600:
            return text

    return "⚠ Раздел не удалось сгенерировать, пропущен."

# ================== BODY ==================
def generate_body(title):
    outline = generate_outline(title)
    headers = [re.sub(r'^##\s*', '', l) for l in outline.splitlines() if l.startswith("##")]

    body = f"# {title}\n\n"
    total = 0

    for h in headers:
        section_text = generate_section(title, outline, h)
        body += f"## {h}\n\n{section_text}\n\n"
        total += len(section_text)

    log.info(f"📏 Body length: {total}")

    if total < 6000:
        raise RuntimeError("❌ Article too short")

    return body

# ================== IMAGE (UNCHANGED — YOUR HORDE) ==================
def generate_image_horde(title):
    styles = [
        "realistic ai lab",
        "developer working with AI",
        "neural network visualization",
        "machine learning workflow",
        "coding with AI assistant"
    ]
    style = random.choice(styles)

    prompt = f"{title}, {style}, ultra realistic, professional photography, 8k"

    negative_prompt = "girl, woman, cartoon, blurry, watermark"

    url_async = "https://stablehorde.net/api/v2/generate/async"
    payload = {
        "prompt": prompt + " ### " + negative_prompt,
        "models": ["Juggernaut XL", "Realistic Vision V5.1", "SDXL 1.0"],
        "params": {"width": 768, "height": 512, "steps": 30, "cfg_scale": 7.5},
        "nsfw": False
    }

    headers = {"apikey": "0000000000", "Client-Agent": "LybraBlogBot:3.0"}

    try:
        r = requests.post(url_async, json=payload, headers=headers, timeout=60)
        if not r.ok:
            return None

        job_id = r.json().get("id")
        if not job_id:
            return None

        check_url = f"https://stablehorde.net/api/v2/generate/check/{job_id}"
        status_url = f"https://stablehorde.net/api/v2/generate/status/{job_id}"

        for _ in range(36):
            time.sleep(10)
            check = requests.get(check_url, headers=headers).json()
            if check.get("done"):
                final = requests.get(status_url, headers=headers).json()
                if final.get("generations"):
                    img_url = final["generations"][0]["img"]
                    img_data = requests.get(img_url).content
                    path = IMAGES_DIR / f"horde-{int(time.time())}.jpg"
                    path.write_bytes(img_data)
                    log.info(f"🖼 Image saved: {path}")
                    return str(path)
    except Exception as e:
        log.warning(f"Horde error: {e}")

    return None

def generate_image(title):
    img = generate_image_horde(title)
    if img and os.path.exists(img):
        return img
    fallback = random.choice(FALLBACK_IMAGES)
    log.warning(f"⚠ Using fallback image: {fallback}")
    return fallback

# ================== SAVE POST ==================
def save_post(title, body, image):
    date = datetime.now()
    slug = re.sub(r'[^a-z0-9-]+', '-', translit(title)).strip('-')[:80]
    file = POSTS_DIR / f"{date:%Y-%m-%d}-{slug}.md"

    front = f"""---
title: "{title}"
date: {date:%Y-%m-%d 00:00:00 -0000}
layout: post
categories: ai
image: {image if image.startswith('http') else '/assets/images/posts/' + Path(image).name}
---

"""

    file.write_text(front + body, encoding="utf-8")
    log.info(f"📝 Post saved: {file}")
    return SITE_URL

# ================== CLEAN OLD POSTS ==================
def cleanup_old_posts(limit=70):
    posts = sorted(POSTS_DIR.glob("*.md"), reverse=True)
    if len(posts) > limit:
        for p in posts[limit:]:
            log.info(f"🧹 Removing old post: {p}")
            p.unlink()

# ================== TELEGRAM ==================
def send_to_telegram(title, teaser, image):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log.warning("Telegram disabled")
        return

    caption = f"<b>{title}</b>\n\n{teaser}\n\n👉 {SITE_URL}"

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

# ================== MAIN ==================
def main():
    log.info("=== START ===")

    topic = fetch_google_trends_topic() or generate_topic()
    log.info(f"🎯 Topic: {topic}")

    title = generate_title(topic)
    body = generate_body(title)
    image = generate_image(title)

    save_post(title, body, image)

    teaser = " ".join(body.split()[:45]) + "..."
    send_to_telegram(title, teaser, image)

    cleanup_old_posts()

    log.info("=== DONE ===")

if __name__ == "__main__":
    main()
