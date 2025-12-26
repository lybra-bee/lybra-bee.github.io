import os
import re
import time
import json
import random
import logging
import datetime
import requests

# =========================
# CONFIG
# =========================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
HORDE_API_KEY = os.getenv("HORDE_API_KEY")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

POSTS_DIR = "_posts"
IMAGES_DIR = "assets/images/posts"

MAX_ARTICLE_ATTEMPTS = 3
MAX_IMAGE_WAIT = 180

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
# HELPERS
# =========================

def contains_politics(text: str) -> bool:
    banned = [
        "президент", "правительство", "закон", "политик", "выбор",
        "страна", "государств", "санкц", "войн", "указ"
    ]
    t = text.lower()
    return any(b in t for b in banned)

def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\wа-яё]+", "-", text)
    return text.strip("-")[:60]

# =========================
# ARTICLE (GROQ SAFE)
# =========================

def generate_article(topic: str):
    system_prompt = (
        "Ты профессиональный технический журналист по ИИ.\n"
        "ПИШИ СТРОГО БЕЗ ПОЛИТИКИ, СТРАН, ГОСУДАРСТВ, ЗАКОНОВ.\n"
        "Фокус: ИИ, генеративные модели, LLM, реальные кейсы, технологии.\n"
        "Формат ОБЯЗАТЕЛЕН."
    )

    user_prompt = (
        f"Тема: {topic}\n\n"
        "Формат ответа СТРОГО такой:\n\n"
        "ЗАГОЛОВОК: ...\n"
        "ТЕКСТ:\n"
        "...\n\n"
        "Запрещено:\n"
        "- политика\n"
        "- государства\n"
        "- лидеры\n"
        "- регулирование\n"
    )

    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama-3.1-70b-versatile",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.8,
            "max_tokens": 1800
        },
        timeout=60
    )

    if r.status_code != 200:
        log.error(f"❌ Groq HTTP {r.status_code}: {r.text}")
        r.raise_for_status()

    content = r.json()["choices"][0]["message"]["content"]

    title_match = re.search(r"ЗАГОЛОВОК:\s*(.+)", content)
    body_match = re.search(r"ТЕКСТ:\s*([\s\S]+)", content)

    if not title_match or not body_match:
        raise ValueError("❌ Неверный формат ответа от LLM")

    return title_match.group(1).strip(), body_match.group(1).strip()

# =========================
# IMAGE (STABLE HORDE)
# =========================

def build_image_prompt(title: str):
    return {
        "prompt": (
            "photorealistic photo, real world scene, cinematic lighting, "
            "DSLR photograph, shallow depth of field, ultra detailed, "
            f"concept: {title}"
        ),
        "negative": (
            "chart, graph, diagram, infographic, scheme, text, letters, "
            "numbers, logo, ui, interface, illustration, cartoon, anime"
        )
    }

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
                "steps": 28,
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

    if r.status_code != 200:
        raise RuntimeError(f"Horde error {r.status_code}: {r.text}")

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
                raise RuntimeError("Horde вернул пустой результат")

            img_url = gens[0]["img"]
            img = requests.get(img_url, timeout=30).content

            with open(out_path, "wb") as f:
                f.write(img)

            return out_path

        time.sleep(5)

    raise TimeoutError("Horde timeout")

# =========================
# TELEGRAM
# =========================

def send_telegram(title, body, image_path):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log.warning("⚠️ Telegram ключи отсутствуют, пропуск")
        return

    teaser = " ".join(body.split()[:30]) + "…"
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
        "ИИ в автоматизации контента",
        "Практическое применение генеративных моделей",
        "Как LLM используются в реальных продуктах",
        "Мультимодальные модели в 2025 году",
        "ИИ для создания и анализа контента"
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
        raise RuntimeError("Не удалось получить допустимую статью")

    today = datetime.date.today().isoformat()
    slug = slugify(title)
    post_path = f"{POSTS_DIR}/{today}-{slug}.md"

    img_prompt = build_image_prompt(title)
    img_id = horde_generate_async(img_prompt["prompt"], img_prompt["negative"])

    img_path = f"{IMAGES_DIR}/post-{int(time.time())}.png"
    horde_wait_and_download(img_id, img_path)

    with open(post_path, "w", encoding="utf-8") as f:
        f.write(f"""---
layout: post
title: "{title}"
date: {today}
image: /{img_path}
---

{body}
""")

    log.info(f"💾 Статья сохранена: {post_path}")

    send_telegram(title, body, img_path)

    log.info("✅ Успешно завершено")

# =========================

if __name__ == "__main__":
    main()
