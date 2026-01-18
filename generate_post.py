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

# -------------------- Транслит --------------------
TRANSLIT_MAP = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
    'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
}

def translit(text):
    return ''.join(TRANSLIT_MAP.get(c, c) for c in text.lower())

# -------------------- Rate limit --------------------
LAST_REQUEST_TS = 0
MIN_INTERVAL = 2  # секунда между запросами

def rate_limit():
    global LAST_REQUEST_TS
    now = time.time()
    diff = now - LAST_REQUEST_TS
    if diff < MIN_INTERVAL:
        time.sleep(MIN_INTERVAL - diff)
    LAST_REQUEST_TS = time.time()

# -------------------- Groq helper --------------------
def groq_chat(prompt, model="llama-3.3-70b-versatile", max_tokens=1024, temp=0.7):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temp,
    }

    # rate limit
    rate_limit()

    for attempt in range(1, 6):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=60)
            if r.status_code == 429:
                wait = 2 ** attempt
                logging.warning(f"Groq 429 — ждем {wait}s (попытка {attempt}/5)")
                time.sleep(wait)
                continue

            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]

        except Exception as e:
            if attempt == 5:
                raise
            wait = 2 ** attempt
            logging.warning(f"Groq error: {e} — retry {attempt}/5 after {wait}s")
            time.sleep(wait)

# -------------------- Заголовок (прикладной) --------------------
def generate_title(topic):
    logging.info(f"Генерация заголовка для темы: {topic}")
    prompt = f"""
Сгенерируй ОДИН прикладной заголовок статьи на русском языке.

Тема: {topic}

Требования:
- 8–14 слов
- Практическая польза
- Без футуризма и философии
- Без слов: будущее, революция, секреты, что ждёт, почему все
- Формат: конкретная польза или задача

Ответ строго:
ЗАГОЛОВОК: ...
"""

    text = groq_chat(prompt, max_tokens=120, temp=0.7)

    match = re.search(r"ЗАГОЛОВОК:\s*(.+)", text)
    if not match:
        raise RuntimeError("Не удалось получить заголовок")

    title = match.group(1).strip()
    words = title.split()
    if len(words) < 6 or len(words) > 14:
        logging.warning(f"Неподходящая длина заголовка: {len(words)} слов")
        title = "Как быстро улучшить качество ответов ИИ в реальных задачах"
        logging.warning(f"Использован fallback-заголовок: {title}")

    logging.info(f"Заголовок: {title}")
    return title

# -------------------- Тело статьи (ОДИН запрос) --------------------
def generate_body(title):
    logging.info("Генерация тела статьи")

    prompt = f"""
Напиши ПОЛНОЦЕННУЮ прикладную статью на русском языке.

Тема: {title}

Формат:
- Урок / мастер-класс / обзор / лайфхак
- Практические советы, реальные кейсы, ошибки, чек-листы
- Без футуризма, философии, воды
- Объём: 8000–12000 знаков
- Структура: 6–8 разделов, каждый раздел с заголовком (##) и текстом
- В конце обязательно: "Вывод" с 3–5 пунктами

Ответ строго в Markdown.
"""

    body = groq_chat(prompt, max_tokens=1200, temp=0.6)

    if len(body) < 6000:
        raise RuntimeError("Статья слишком короткая")

    logging.info(f"Объём статьи: {len(body)} знаков")
    return body

# -------------------- ИЗОБРАЖЕНИЕ (НЕ ТРОГАТЬ) --------------------
def generate_image_horde(title):
    styles = [
        "laboratory with quantum computers, blue lighting",
        "futuristic data center with glowing servers",
        "people using holographic AI interface",
        "cyberpunk street with AI billboards",
        "abstract visualization of neural network",
        "doctor using AI diagnostic tool",
        "artist collaborating with AI",
        "autonomous car in smart city",
        "ethical dilemma: human and AI",
        "global network of AI systems"
    ]
    style = random.choice(styles)

    prompt = (
        f"{title}, {style}, ultra realistic professional photography, "
        "sharp focus, cinematic lighting, natural colors, 8k resolution"
    )

    negative_prompt = (
        "girl, woman, female portrait, fashion, makeup, long hair, "
        "abstract art, cartoon, low quality, blurry, deformed, text, watermark"
    )

    url_async = "https://stablehorde.net/api/v2/generate/async"
    payload = {
        "prompt": prompt + " ### " + negative_prompt,
        "models": ["Juggernaut XL", "Realistic Vision V5.1", "FLUX.1 [schnell]", "SDXL 1.0"],
        "params": {"width": 768, "height": 512, "steps": 30, "cfg_scale": 7.5, "sampler_name": "k_euler_a", "n": 1},
        "nsfw": False, "trusted_workers": False, "slow_workers": True
    }

    headers = {"apikey": "0000000000", "Content-Type": "application/json", "Client-Agent": "LybraBlogBot:3.0"}

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
                    return str(path)
    except:
        pass

    return None

def generate_image(title):
    local = generate_image_horde(title)
    if local and os.path.exists(local):
        return local
    return random.choice(FALLBACK_IMAGES)

# -------------------- Сохранение --------------------
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
    return SITE_URL

# -------------------- Telegram --------------------
def send_to_telegram(title, teaser, image):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
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

# -------------------- MAIN --------------------
def main():
    logging.info("=== START ===")

    topic = random.choice([
        "ИИ в бизнесе",
        "ИИ для разработчиков",
        "ИИ в маркетинге",
        "ИИ в аналитике",
        "ИИ в образовании",
        "ИИ в поддержке клиентов",
        "ИИ в безопасности",
        "ИИ в автоматизации процессов"
    ])

    logging.info(f"Тема дня: {topic}")

    title = generate_title(topic)
    body = generate_body(title)
    image = generate_image(title)
    save_post(title, body, image)

    teaser = " ".join(body.split()[:40]) + "..."
    send_to_telegram(title, teaser, image)

    logging.info("=== DONE ===")

if __name__ == "__main__":
    main()
