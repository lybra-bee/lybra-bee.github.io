import os
import re
import json
import time
import logging
import random
import datetime
import requests

# =========================
# CONFIG
# =========================

HORDE_API_KEY = os.getenv("HORDE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

POSTS_DIR = "_posts"
IMAGES_DIR = "assets/images/posts"

MAX_ARTICLE_ATTEMPTS = 3
MAX_IMAGE_WAIT = 180  # seconds

os.makedirs(POSTS_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

# =========================
# LOGGING
# =========================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
    handlers=[
        logging.FileHandler("generation.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

log = logging.getLogger()

# =========================
# UTILS
# =========================

def contains_politics(text: str) -> bool:
    banned = [
        "президент", "правительство", "закон", "политик", "выбор",
        "страна", "государств", "санкц", "войн", "указ"
    ]
    t = text.lower()
    return any(b in t for b in banned)

def slugify(text):
    text = text.lower()
    text = re.sub(r"[^\wа-яё]+", "-", text)
    return text.strip("-")[:60]

# =========================
# ARTICLE GENERATION
# =========================

def generate_article(topic: str):
    prompt = f"""
Ты — профессиональный техно-журналист.

ЗАПРЕЩЕНО:
- политика
- государства
- законы
- регуляторы
- страны
- лидеры
- конфликты

РАЗРЕШЕНО ТОЛЬКО:
- искусственный интеллект
- генеративные модели
- LLM
- computer vision
- практическое применение
- реальные кейсы
- тренды 2025

Формат строго:

ЗАГОЛОВОК: ...
ТЕКСТ:
...

Тема: {topic}
"""

    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
        json={
            "model": "llama-3.1-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.9
        },
        timeout=60
    )
    r.raise_for_status()

    data = r.json()["choices"][0]["message"]["content"]

    title_match = re.search(r"ЗАГОЛОВОК:\s*(.+)", data)
    body_match = re.search(r"ТЕКСТ:\s*([\s\S]+)", data)

    if not title_match or not body_match:
        raise ValueError("Неверный формат статьи")

    return title_match.group(1).strip(), body_match.group(1).strip()

# =========================
# IMAGE PROMPT BUILDER
# =========================

def build_image_prompt(title: str) -> dict:
    return {
        "prompt": f"""
photorealistic photograph, real world scene,
cinematic lighting, shallow depth of field,
DSLR photo, 35mm lens, ultra detailed,
people, technology, realistic materials,
NO text, NO charts, NO graphs,
concept: {title}
""",
        "negative": (
            "chart, graph, diagram, infographic, scheme, ui, interface, "
            "text, letters, numbers, logo, watermark, illustration, "
            "drawing, cartoon, anime"
        )
    }

# =========================
# STABLE HORDE
# =========================

def horde_generate_async(prompt, negative):
    r = requests.post(
        "https://stablehorde.net/api/v2/generate/async",
        headers={
            "apikey": HORDE_API_KEY,
            "Content-Type": "application/json"
        },
        json={
            "prompt": prompt,
            "params": {
                "sampler_name": "k_euler",
                "steps": 30,
                "cfg_scale": 7,
                "width": 768,
                "height": 512,
                "negative_prompt": negative
            },
            "models": [
                "Realistic Vision",
                "Juggernaut XL",
                "Absolute Reality"
            ],
            "nsfw": False
        },
        timeout=30
    )

    if r.status_code == 403:
        raise RuntimeError("Horde: 403 Forbidden (ключ или лимит)")

    r.raise_for_status()
    return r.json()["id"]

def horde_wait_and_download(task_id, out_path):
    start = time.time()

    while time.time() - start < MAX_IMAGE_WAIT:
        r = requests.get(
            f"https://stablehorde.net/api/v2/generate/status/{task_id}",
            timeout=15
        )
        r.raise_for_status()
        data = r.json()

        if data.get("done"):
            gens = data.get("generations")
            if not gens:
                raise RuntimeError("Horde: пустая генерация")

            img_url = gens[0]["img"]
            img = requests.get(img_url, timeout=30).content

            with open(out_path, "wb") as f:
                f.write(img)

            return out_path

        time.sleep(5)

    raise TimeoutError("Horde: таймаут генерации")

# =========================
# TELEGRAM
# =========================

def send_telegram(title, text, image_path):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log.warning("⚠️ Telegram ключи отсутствуют, пропускаем")
        return

    teaser = " ".join(text.split()[:30]) + "…"

    msg = f"*Новая статья*\n\n{teaser}\n\n#ИИ #LybraAI"

    r = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto",
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "caption": msg,
            "parse_mode": "Markdown"
        },
        files={"photo": open(image_path, "rb")},
        timeout=30
    )

    log.info(f"📢 Telegram статус: {r.status_code}")

# =========================
# MAIN
# =========================

def main():
    log.info("🚀 Запуск генерации")

    topics = [
        "Практическое применение генеративного ИИ в 2025",
        "Как LLM меняют разработку ПО",
        "Мультимодальные модели в реальных продуктах",
        "ИИ в автоматизации контента",
        "Будущее компьютерного зрения"
    ]

    for attempt in range(1, MAX_ARTICLE_ATTEMPTS + 1):
        topic = random.choice(topics)
        log.info(f"✍️ Попытка {attempt}: {topic}")

        title, body = generate_article(topic)

        if contains_politics(title + body):
            log.warning("⚠️ Обнаружена политика — регенерация")
            continue

        log.info(f"📰 Заголовок: {title}")
        break
    else:
        raise RuntimeError("Не удалось сгенерировать допустимую статью")

    today = datetime.date.today().isoformat()
    slug = slugify(title)
    post_path = f"{POSTS_DIR}/{today}-{slug}.md"

    image_prompt = build_image_prompt(title)
    img_id = horde_generate_async(
        image_prompt["prompt"],
        image_prompt["negative"]
    )

    img_num = int(time.time())
    img_path = f"{IMAGES_DIR}/post-{img_num}.png"

    try:
        horde_wait_and_download(img_id, img_path)
    except Exception as e:
        log.error(f"❌ Изображение не создано: {e}")
        img_path = None

    with open(post_path, "w", encoding="utf-8") as f:
        f.write(f"""---
layout: post
title: "{title}"
date: {today}
image: /{img_path if img_path else 'assets/images/default.png'}
---

{body}
""")

    log.info(f"💾 Статья сохранена: {post_path}")

    if img_path:
        send_telegram(title, body, img_path)

    log.info("✅ Успешно завершено")
    return True


if __name__ == "__main__":
    success = main()
    raise SystemExit(0 if success else 1)
