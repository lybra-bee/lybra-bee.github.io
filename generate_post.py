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

# ---------------- logging ----------------
LOG_FILE = "generation.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, encoding="utf-8")
    ],
)
log = logging.getLogger(__name__)

# ---------------- Optional Google Trends ----------------
try:
    from pytrends.request import TrendReq
except Exception:
    TrendReq = None

# ---------------- Paths ----------------
ROOT = Path(".")
POSTS_DIR = ROOT / "_posts"
IMAGES_DIR = ROOT / "assets" / "images" / "posts"
POSTS_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# ---------------- API keys ----------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
HORDE_API_KEY = os.getenv("HORDE_API_KEY") or os.getenv("AIHORDE_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SITE_URL = os.getenv("SITE_URL", "https://lybra-ai.ru")

# ---------------- History ----------------
HISTORY_FILE = ROOT / ".topics_history"
MAX_HISTORY = 80

def load_history():
    if HISTORY_FILE.exists():
        return HISTORY_FILE.read_text(encoding="utf-8").splitlines()
    return []

def save_history(hist):
    HISTORY_FILE.write_text("\n".join(hist[-MAX_HISTORY:]), encoding="utf-8")

# ---------------- Topic categories ----------------
TOPIC_CATEGORIES = {
    "dev": [
        "инструменты разработчика ИИ",
        "AI для программистов",
        "open-source AI проекты",
        "автоматизация Python"
    ],
    "local_ai": [
        "локальные LLM",
        "запуск ИИ на ПК",
        "self-hosted AI",
        "офлайн AI инструменты"
    ],
    "experiments": [
        "эксперименты с нейросетями",
        "тест новых моделей ИИ",
        "сравнение AI моделей"
    ],
    "automation": [
        "AI автоматизация задач",
        "боты для Telegram",
        "генерация контента ИИ"
    ],
    "productivity": [
        "AI для личной продуктивности",
        "инструменты для создателей контента"
    ],
    "business_light": [
        "AI для фрилансеров",
        "AI для стартапов",
        "монетизация ИИ"
    ]
}

# ---------------- Fallback topics ----------------
FALLBACK_TOPICS = [
    "Лучшие open-source AI инструменты 2026",
    "Как запустить локальную LLM дома",
    "AI автоматизация рутины Python",
    "Создание AI-ассистента своими руками",
    "AI-бот для Telegram с нуля",
    "Сравнение популярных нейросетей",
]

# ---------------- Rate limit Groq ----------------
LAST_REQUEST_TS = 0
MIN_INTERVAL = float(os.getenv("GROQ_MIN_INTERVAL", "1.5"))

def rate_limit():
    global LAST_REQUEST_TS
    diff = time.time() - LAST_REQUEST_TS
    if diff < MIN_INTERVAL:
        time.sleep(MIN_INTERVAL - diff)
    LAST_REQUEST_TS = time.time()

def groq_chat(prompt, max_tokens=1200, temperature=0.6, attempts=4):
    if not GROQ_API_KEY:
        raise RuntimeError("No GROQ_API_KEY")

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature
    }

    for i in range(attempts):
        try:
            rate_limit()
            log.info("Groq request attempt %d/%d", i+1, attempts)
            r = requests.post(url, headers=headers, json=payload, timeout=90)

            if r.status_code == 429:
                time.sleep(min(30, 2 ** i))
                continue

            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]

        except Exception as e:
            log.warning("Groq error: %s", e)
            time.sleep(min(10, 2 ** i))

    raise RuntimeError("Groq failed")

# ---------------- Trending topics ----------------
def get_google_trends():
    if not TrendReq:
        return []
    try:
        pytrends = TrendReq(hl="ru-RU", tz=180)
        pytrends.build_payload(["искусственный интеллект"], timeframe="now 7-d")
        rq = pytrends.related_queries()
        if rq and "искусственный интеллект" in rq:
            df = rq["искусственный интеллект"]["top"]
            return df["query"].tolist()
    except:
        return []
    return []

def get_balanced_topic():
    history = [h.lower() for h in load_history()]

    # Try trends
    trends = get_google_trends()
    random.shuffle(trends)

    for t in trends:
        if t.lower() not in history:
            history.append(t)
            save_history(history)
            log.info("Trend topic selected: %s", t)
            return t

    # Category rotation
    cat = random.choice(list(TOPIC_CATEGORIES.keys()))
    topic = random.choice(TOPIC_CATEGORIES[cat])

    if topic.lower() not in history:
        history.append(topic)
        save_history(history)
        log.info("Category topic selected: %s", topic)
        return topic

    fallback = random.choice(FALLBACK_TOPICS)
    history.append(fallback)
    save_history(history)
    log.warning("Fallback topic: %s", fallback)
    return fallback

# ---------------- Title ----------------
def generate_title(topic):
    prompt = f"""
Сгенерируй ОДИН практичный заголовок статьи на русском.

Тема: {topic}

Правила:
- 8–14 слов
- Максимум практики
- Без футуризма
- Без клише
Формат:
ЗАГОЛОВОК: текст
"""
    text = groq_chat(prompt, max_tokens=120)
    m = re.search(r"ЗАГОЛОВОК:\s*(.+)", text)
    return m.group(1).strip() if m else f"{topic} — практическое руководство"

# ---------------- Body ----------------
def generate_body(title):
    prompt = f"""
Напиши ПОЛНОЦЕННУЮ практическую статью.

Тема: {title}

Требования:
- 6–8 разделов
- Кейсы
- Пошаговые инструкции
- Ошибки
- Вывод
- 8000–12000 знаков
Markdown
"""
    text = groq_chat(prompt, max_tokens=1800)
    return text if len(text) > 4000 else f"# {title}\n\n(Ошибка генерации)"

# ---------------- Images ----------------
FALLBACK_IMAGES = [
    "https://picsum.photos/1024/768?random=1",
    "https://picsum.photos/1024/768?random=2"
]

def generate_image(title):
    filename = IMAGES_DIR / f"fallback-{int(time.time())}.png"
    url = random.choice(FALLBACK_IMAGES)

    try:
        r = requests.get(url, timeout=30)
        if r.ok:
            filename.write_bytes(r.content)
            log.info("Image saved: %s", filename)
            return str(filename)
    except:
        pass

    return url

# ---------------- Save post ----------------
TRANSLIT_MAP = {c: c for c in "abcdefghijklmnopqrstuvwxyz0123456789- "}
def translit(text):
    return re.sub(r'[^a-z0-9-]+', '-', text.lower())

def save_post(title, body, image_path):
    date = datetime.now()
    slug = translit(title)[:80]
    filename = POSTS_DIR / f"{date.strftime('%Y-%m-%d')}-{slug}.md"

    image_url = f"/assets/images/posts/{Path(image_path).name}"

    fm = f"""---
title: "{title}"
date: {date.strftime('%Y-%m-%d 00:00:00 -0000')}
layout: post
image: "{image_url}"
tags: ["ИИ","разработка","инструменты"]
---

"""

    filename.write_text(fm + body, encoding="utf-8")
    log.info("Post saved: %s", filename)

# ---------------- Telegram ----------------
def send_to_telegram(title, body, image):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    teaser = " ".join(body.split()[:40]) + "..."
    caption = f"<b>{title}</b>\n\n{teaser}\n\n{SITE_URL}"

    files = {"photo": open(image, "rb")} if os.path.exists(image) else None
    data = {"chat_id": TELEGRAM_CHAT_ID, "caption": caption, "parse_mode": "HTML"}

    requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto", data=data, files=files)

# ---------------- MAIN ----------------
def main():
    log.info("=== START ===")

    topic = get_balanced_topic()
    log.info("Topic: %s", topic)

    title = generate_title(topic)
    log.info("Title: %s", title)

    body = generate_body(title)
    log.info("Body length: %d", len(body))

    image = generate_image(title)
    log.info("Image: %s", image)

    save_post(title, body, image)
    send_to_telegram(title, body, image)

    log.info("=== DONE ===")

if __name__ == "__main__":
    main()
