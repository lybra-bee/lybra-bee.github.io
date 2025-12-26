import os
import re
import time
import json
import random
import logging
import requests
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageDraw

# =========================
# НАСТРОЙКИ
# =========================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
HORDE_API_KEY = os.getenv("HORDE_API_KEY")

POSTS_DIR = Path("_posts")
IMG_DIR = Path("assets/images/posts")
POSTS_DIR.mkdir(parents=True, exist_ok=True)
IMG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(message)s"
)

# =========================
# АНТИ-ПОЛИТИКА
# =========================
POLITICAL_WORDS = [
    "президент", "партия", "выбор", "государств",
    "закон", "политик", "санкц", "войн"
]

def has_politics(text: str) -> bool:
    t = text.lower()
    return any(w in t for w in POLITICAL_WORDS)

# =========================
# НАДЁЖНЫЙ ПАРСЕР
# =========================
def parse_article(raw: str) -> tuple[str, str]:
    raw = raw.strip()

    title = None
    body = None

    m_title = re.search(r"ЗАГОЛОВОК[:\-]?\s*(.+)", raw, re.IGNORECASE)
    m_body = re.search(r"ТЕКСТ[:\-]?\s*(.+)", raw, re.IGNORECASE | re.S)

    if m_title:
        title = m_title.group(1).strip()
    else:
        # fallback — первая строка
        title = raw.splitlines()[0][:120]

    if m_body:
        body = m_body.group(1).strip()
    else:
        # fallback — всё кроме первой строки
        body = "\n".join(raw.splitlines()[1:]).strip()

    return title, body

# =========================
# ГЕНЕРАЦИЯ СТАТЬИ
# =========================
def generate_article(topic: str) -> tuple[str, str]:
    prompt = f"""
Ты пишешь технологическую статью.
СТРОГО ЗАПРЕЩЕНО:
- политика
- государство
- выборы
- геополитика

Тема: {topic}

Формат желателен:
ЗАГОЛОВОК:
ТЕКСТ:
"""

    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        },
        timeout=60
    )

    raw = r.json()["choices"][0]["message"]["content"]
    return parse_article(raw)

# =========================
# STABLE HORDE
# =========================
HORDE_HEADERS = {
    "apikey": HORDE_API_KEY,
    "Client-Agent": "Lybrabee:1.0:github.com/lybra-bee",
    "Content-Type": "application/json"
}

def horde_generate_async(prompt: str) -> str:
    payload = {
        "prompt": prompt,
        "params": {
            "sampler_name": "k_euler",
            "steps": 28,
            "cfg_scale": 7,
            "width": 768,
            "height": 512
        },
        "nsfw": False,
        "models": ["Realistic Vision"],
        "r2": True
    }

    r = requests.post(
        "https://stablehorde.net/api/v2/generate/async",
        headers=HORDE_HEADERS,
        json=payload,
        timeout=30
    )
    r.raise_for_status()
    return r.json()["id"]

def horde_wait_and_download(tid: str) -> bytes:
    for _ in range(40):
        r = requests.get(
            f"https://stablehorde.net/api/v2/generate/status/{tid}",
            headers=HORDE_HEADERS,
            timeout=30
        )
        data = r.json()
        if data.get("done") and data.get("generations"):
            return requests.get(data["generations"][0]["img"], timeout=30).content
        time.sleep(3)
    raise TimeoutError("Stable Horde timeout")

def generate_image(title: str) -> Path:
    try:
        logging.info("🎨 Stable Horde генерация изображения")
        prompt = f"Photorealistic, ultra-detailed, cinematic lighting, {title}"
        tid = horde_generate_async(prompt)
        img = horde_wait_and_download(tid)

        path = IMG_DIR / f"post-{int(time.time())}.png"
        with open(path, "wb") as f:
            f.write(img)
        return path
    except Exception as e:
        logging.error(f"❌ Horde ошибка: {e}")
        img = Image.new("RGB", (768, 512), "#111")
        ImageDraw.Draw(img).text((40, 240), title[:80], fill="white")
        path = IMG_DIR / f"fallback-{int(time.time())}.png"
        img.save(path)
        return path

# =========================
# MAIN
# =========================
def main():
    logging.info("🚀 Запуск генерации")

    trends = [
        "Будущее мультимодальных моделей",
        "Как инженеры используют LLM",
        "AI в автоматизации бизнеса",
        "Генеративные модели в 2025",
        "Как ИИ меняет разработку ПО"
    ]

    for attempt in range(3):
        topic = random.choice(trends)
        logging.info(f"✍️ Попытка {attempt+1}: {topic}")

        title, body = generate_article(topic)
        if has_politics(body):
            logging.warning("⚠️ Обнаружена политика — регенерация")
            continue
        break
    else:
        raise RuntimeError("Не удалось получить аполитичную статью")

    img_path = generate_image(title)

    date = datetime.now().strftime("%Y-%m-%d")
    slug = re.sub(r"[^\w]+", "-", title.lower())
    post_path = POSTS_DIR / f"{date}-{slug}.md"

    with open(post_path, "w", encoding="utf-8") as f:
        f.write(f"""---
title: "{title}"
image: /{img_path}
---

{body}
""")

    logging.info(f"💾 Статья сохранена: {post_path}")
    logging.info("✅ Успешно завершено")

if __name__ == "__main__":
    main()
