import os
import re
import time
import json
import uuid
import random
import logging
import requests
from datetime import datetime
from pathlib import Path

# ================== НАСТРОЙКИ ==================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
HORDE_API_KEY = os.getenv("HORDE_API_KEY")

GROQ_MODEL = "llama3-70b-8192"  # АКТУАЛЬНАЯ модель
POSTS_DIR = Path("_posts")
IMAGES_DIR = Path("assets/images")
POSTS_DIR.mkdir(exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# ================== ЛОГИ ==================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(message)s"
)

# ================== GROQ ==================
def generate_article(topic: str):
    prompt = f"""
Ты — профессиональный техноблогер.

Сгенерируй статью строго в формате:

ЗАГОЛОВОК: ...
ТЕКСТ:
...

Тема: {topic}
Язык: русский
Стиль: экспертный, живой
Объём: 3–5 абзацев
"""

    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": GROQ_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        },
        timeout=60
    )

    if r.status_code != 200:
        logging.error(f"❌ Groq HTTP {r.status_code}: {r.text}")
        raise RuntimeError("Groq error")

    data = r.json()["choices"][0]["message"]["content"]

    title_match = re.search(r"ЗАГОЛОВОК:\s*(.+)", data)
    body_match = re.search(r"ТЕКСТ:\s*([\s\S]+)", data)

    if not title_match or not body_match:
        raise ValueError("Неверный формат ответа Groq")

    return title_match.group(1).strip(), body_match.group(1).strip()

# ================== HORDE ==================
def horde_generate_async(prompt):
    r = requests.post(
        "https://stablehorde.net/api/v2/generate/async",
        headers={
            "apikey": HORDE_API_KEY,
            "Content-Type": "application/json"
        },
        json={
            "prompt": prompt,
            "params": {
                "steps": 25,
                "sampler_name": "k_euler",
                "cfg_scale": 7,
                "width": 768,
                "height": 512
            },
            "models": ["Realistic Vision"],
            "nsfw": False
        },
        timeout=60
    )

    if r.status_code != 202:
        logging.error(f"Horde async error {r.status_code}: {r.text}")
        return None

    return r.json()["id"]

def horde_wait_and_download(task_id):
    while True:
        r = requests.get(f"https://stablehorde.net/api/v2/generate/status/{task_id}")
        data = r.json()

        if data["done"]:
            if not data["generations"]:
                return None

            img_url = data["generations"][0]["img"]
            img_data = requests.get(img_url).content

            filename = f"{uuid.uuid4().hex}.png"
            path = IMAGES_DIR / filename

            with open(path, "wb") as f:
                f.write(img_data)

            return path

        time.sleep(3)

def generate_image(prompt):
    task = horde_generate_async(prompt)
    if not task:
        return None
    return horde_wait_and_download(task)

# ================== FALLBACK КАРТИНКА ==================
def fallback_image():
    url = "https://picsum.photos/768/512"
    data = requests.get(url).content
    path = IMAGES_DIR / f"fallback_{uuid.uuid4().hex}.jpg"
    with open(path, "wb") as f:
        f.write(data)
    return path

# ================== MAIN ==================
def main():
    logging.info("🚀 Запуск генерации")

    topics = [
        "ИИ в автоматизации контента",
        "Генеративные модели в 2025",
        "Будущее AI-блогинга",
        "Как нейросети меняют медиа",
        "ИИ для бизнеса и маркетинга"
    ]

    topic = random.choice(topics)
    logging.info(f"✍️ Попытка: {topic}")

    title, body = generate_article(topic)

    img_prompt = f"Фотореалистичное изображение, иллюстрирующее тему: {title}, стиль — современный, высокое качество"
    img_path = generate_image(img_prompt)

    if not img_path:
        logging.warning("⚠️ Horde недоступен — fallback image")
        img_path = fallback_image()

    date = datetime.now().strftime("%Y-%m-%d")
    slug = re.sub(r"[^\w]+", "-", title.lower()).strip("-")
    post_file = POSTS_DIR / f"{date}-{slug}.md"

    with open(post_file, "w", encoding="utf-8") as f:
        f.write(f"""---
layout: post
title: "{title}"
image: /{img_path.as_posix()}
---

{body}
""")

    logging.info("✅ Пост успешно создан")
    return True

if __name__ == "__main__":
    main()
