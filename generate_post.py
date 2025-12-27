#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
import time
import random
import logging
import requests
from datetime import datetime
from pathlib import Path
import tempfile

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

# -------------------- Папки --------------------
POSTS_DIR = Path("_posts")
IMAGES_DIR = Path("assets/images/posts")
POSTS_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# -------------------- API ключи --------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
AIHORDE_API_KEY = os.getenv("AIHORDE_API_KEY", "0000000000")  # Анонимный по умолчанию, добавьте свой для приоритета

FALLBACK_IMAGES = [
    "https://picsum.photos/1200/800?random=80",
    "https://picsum.photos/1200/800?random=81",
    "https://picsum.photos/1200/800?random=82",
    "https://picsum.photos/1200/800?random=83",
    "https://picsum.photos/1200/800?random=84",
]

# -------------------- Шаг 1: Генерация заголовка --------------------
def generate_title(topic):
    # (код без изменений, как раньше)

# -------------------- Шаг 2: Генерация статьи --------------------
def generate_body(title):
    # (код без изменений, как раньше)

# -------------------- Изображение: AI Horde (улучшенная версия) --------------------
def generate_image_horde(title):
    prompt = f"{title}, futuristic artificial intelligence, neural networks, cyberpunk aesthetic, photorealistic, highly detailed, cinematic lighting, vibrant neon colors, 8k resolution, masterpiece, best quality"

    url_async = "https://stablehorde.net/api/v2/generate/async"  # Основной endpoint (stablehorde.net работает лучше)

    payload = {
        "prompt": prompt,
        "models": ["FLUX.1 [schnell]", "Flux.1 Dev", "SDXL 1.0"],  # Точные названия моделей на декабрь 2025
        "params": {
            "width": 1280,
            "height": 720,
            "steps": 30,
            "cfg_scale": 7.0,
            "n": 1
        },
        "nsfw": False,
        "trusted_workers": True,  # Только проверенные workers для качества
        "slow_workers": False
    }

    headers = {
        "apikey": AIHORDE_API_KEY,
        "Content-Type": "application/json",
        "Client-Agent": "LybraBlogBot:1.0:your@email.com"  # Рекомендуется для идентификации
    }

    try:
        logging.info("Отправка запроса в AI Horde...")
        r = requests.post(url_async, json=payload, headers=headers, timeout=60)
        if not r.ok:
            logging.warning(f"Ошибка отправки: {r.status_code} {r.text}")
            return None

        job = r.json()
        job_id = job.get("id")
        if not job_id:
            logging.warning(f"Нет job_id: {job}")
            return None

        logging.info(f"Задача создана: ID {job_id}")

        status_url = f"https://stablehorde.net/api/v2/generate/check/{job_id}"
        download_url = f"https://stablehorde.net/api/v2/generate/status/{job_id}"

        for poll in range(60):  # Макс 10 мин (по 10 сек)
            time.sleep(10)
            status_check = requests.get(status_url, headers=headers, timeout=60).json()
            if status_check.get("done"):
                final = requests.get(download_url, headers=headers, timeout=60).json()
                if final.get("generations"):
                    image_url = final["generations"][0]["img"]
                    img_data = requests.get(image_url, timeout=60)
                    if img_data.ok:
                        timestamp = int(time.time())
                        img_path = IMAGES_DIR / f"horde-{timestamp}.jpg"
                        with open(img_path, "wb") as f:
                            f.write(img_data.content)
                        logging.info(f"Изображение готово: {img_path}")
                        return str(img_path)

            wait_time = status_check.get("wait_time", 10)
            queue_pos = status_check.get("queue_position", 0)
            logging.info(f"Ожидание: ~{wait_time} сек, позиция в очереди: {queue_pos}")

    except Exception as e:
        logging.warning(f"Исключение в AI Horde: {e}")

    return None


def generate_image(title):
    img = generate_image_horde(title)
    if img:
        return img
    logging.warning("AI Horde не сработал (очередь/таймаут) → fallback picsum")
    return random.choice(FALLBACK_IMAGES)


# -------------------- Сохранение поста, Telegram, main --------------------
# (код без изменений из предыдущей версии)

if __name__ == "__main__":
    main()
