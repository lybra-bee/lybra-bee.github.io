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

SITE_URL = "https://lybra-ai.ru"

FALLBACK_IMAGES = [
    "https://picsum.photos/1024/768?random=1",
    "https://picsum.photos/1024/768?random=2",
    "https://picsum.photos/1024/768?random=3",
    "https://picsum.photos/1024/768?random=4",
    "https://picsum.photos/1024/768?random=5",
]

# Улучшенный транслит
TRANSLIT_MAP = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
    'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
}

def translit(text):
    text = text.lower()
    result = []
    for c in text:
        result.append(TRANSLIT_MAP.get(c, c))
    return ''.join(result)

# -------------------- Шаг 1: Разнообразный заголовок --------------------
# (оставляем как есть — работает отлично)

def generate_title(topic):
    # ... (тот же код, что и раньше)

    # (полный код функции из предыдущей версии)

    fallbacks = [
        f"Почему {topic.lower()} меняет всё в 2026 году",
        f"ИИ переходит на новый уровень: эра {topic.lower()} началась",
        f"Что скрывают новые разработки в {topic.lower()}",
        f"2026 год начинается сейчас: прорыв в {topic.lower()}",
        f"Как {topic.lower()} уже влияет на нашу жизнь"
    ]
    title = random.choice(fallbacks)
    logging.info(f"Использован fallback-заголовок: {title}")
    return title

# -------------------- Шаг 2: План и тело статьи (3000–5000 знаков) --------------------
# (оставляем как есть — с твоим адаптированным промптом)

# ... (generate_outline, generate_section, generate_body — как в последней версии с твоим промптом)

# -------------------- Изображение: Stable Horde с фотореализмом --------------------
def generate_image_horde(title):
    # Мощный промпт для фотореализма
    prompt = (
        f"{title}, ultra realistic professional photography, beautiful futuristic scene with artificial intelligence elements, "
        "highly detailed human interacting with holographic AI interface, cyberpunk city at night with neon lights, "
        "sharp focus, cinematic lighting, natural skin textures, realistic eyes, depth of field, 8k resolution, "
        "photorealistic, masterpiece, award winning photo"
    )

    negative_prompt = (
        "abstract, painting, drawing, illustration, cartoon, anime, low quality, blurry, deformed, ugly, extra limbs, "
        "geometric shapes, lines, wireframe, text, watermark, logo, signature, overexposed, underexposed"
    )

    url_async = "https://stablehorde.net/api/v2/generate/async"
    payload = {
        "prompt": prompt + " ### " + negative_prompt,
        "models": ["Juggernaut XL", "Realistic Vision V5.1", "FLUX.1 [schnell]", "SDXL 1.0"],
        "params": {
            "width": 768,
            "height": 512,
            "steps": 28,
            "cfg_scale": 7.5,
            "sampler_name": "k_euler_a",
            "n": 1
        },
        "nsfw": False,
        "trusted_workers": False,
        "slow_workers": True
    }

    headers = {
        "apikey": "0000000000",
        "Content-Type": "application/json",
        "Client-Agent": "LybraBlogBot:2.0"
    }

    try:
        r = requests.post(url_async, json=payload, headers=headers, timeout=60)
        if not r.ok:
            logging.warning(f"Horde ошибка отправки: {r.status_code} {r.text}")
            return None

        job_id = r.json().get("id")
        if not job_id:
            return None

        logging.info(f"Horde задача создана: {job_id}. Долгое ожидание для фотореализма...")

        check_url = f"https://stablehorde.net/api/v2/generate/check/{job_id}"
        status_url = f"https://stablehorde.net/api/v2/generate/status/{job_id}"

        # До 60 минут ожидания — хватит на любую очередь
        for _ in range(360):
            time.sleep(10)
            try:
                check = requests.get(check_url, headers=headers, timeout=30).json()
                if check.get("done"):
                    final = requests.get(status_url, headers=headers, timeout=30).json()
                    if final.get("generations"):
                        img_url = final["generations"][0]["img"]
                        img_data = requests.get(img_url, timeout=60)
                        if img_data.ok:
                            filename = f"horde-{int(time.time())}.jpg"
                            img_path = IMAGES_DIR / filename
                            img_path.write_bytes(img_data.content)
                            logging.info(f"Фотореалистичное изображение от Horde сохранено: {img_path}")
                            return str(img_path)
                queue = check.get("queue_position", "?")
                if queue != "?" and queue > 0:
                    logging.info(f"Ожидание в очереди Horde... позиция: {queue}")
            except Exception as e:
                logging.debug(f"Сетевой сбой при проверке Horde: {e}")

        logging.warning("Horde: таймаут ожидания (60 мин)")
    except Exception as e:
        logging.warning(f"Ошибка Horde: {e}")

    return None

def generate_image(title):
    local_path = generate_image_horde(title)
    if local_path and os.path.exists(local_path):
        return local_path

    fallback_url = random.choice(FALLBACK_IMAGES)
    logging.warning(f"Horde не успел → fallback: {fallback_url}")
    return fallback_url

# -------------------- Сохранение поста и Telegram --------------------
# (оставляем как в последней версии — с title в кавычках, layout: post и т.д.)

# -------------------- MAIN --------------------
# (как раньше)

if __name__ == "__main__":
    main()
