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
FAL_API_KEY = os.getenv("FAL_API_KEY")  # ← Новый ключ!

FALLBACK_IMAGES = [
    "https://picsum.photos/1200/800?random=1",
    "https://picsum.photos/1200/800?random=2",
    "https://picsum.photos/1200/800?random=3",
    "https://picsum.photos/1200/800?random=4",
    "https://picsum.photos/1200/800?random=5",
]

# -------------------- Генерация заголовка и статьи (без изменений) --------------------
# (оставляем функции generate_title и generate_body как были — они работают отлично)

# -------------------- Изображение: fal.ai (Flux Schnell — быстро и качественно) --------------------
def generate_image_fal(title):
    if not FAL_API_KEY:
        logging.warning("FAL_API_KEY отсутствует — используем fallback")
        return None

    # Модель Flux.1 Schnell — бесплатная, быстрая, отличное качество
    url = "https://fal.run/fal-ai/flux/schnell"

    prompt = f"{title}, futuristic artificial intelligence theme, photorealistic, highly detailed, professional photography, cinematic lighting, 8k resolution"

    payload = {
        "prompt": prompt,
        "image_size": "landscape_16_9",  # 1280x720 — хорошее соотношение для обложки
        "num_inference_steps": 28,
        "guidance_scale": 7.5,
        "num_images": 1,
        "sync_mode": True  # Синхронный режим — ждём результат сразу
    }

    headers = {
        "Authorization": f"Key {FAL_API_KEY}",
        "Content-Type": "application/json"
    }

    for attempt in range(5):
        try:
            logging.info(f"Генерация изображения через fal.ai Flux (попытка {attempt+1})...")
            r = requests.post(url, json=payload, headers=headers, timeout=120)

            if r.status_code == 402 or r.status_code == 403:
                logging.warning("fal.ai: лимит кредитов исчерпан или ключ неверный")
                return None
            if not r.ok:
                logging.warning(f"fal.ai ошибка {r.status_code}: {r.text}")
                time.sleep(5)
                continue

            result = r.json()
            image_url = result["images"][0]["url"]

            # Скачиваем
            img_data = requests.get(image_url, timeout=60)
            if not img_data.ok:
                logging.warning("Не удалось скачать изображение")
                continue

            timestamp = int(time.time())
            img_path = IMAGES_DIR / f"fal-flux-{timestamp}.jpg"
            with open(img_path, "wb") as f:
                f.write(img_data.content)

            logging.info(f"Изображение успешно сгенерировано: {img_path}")
            return str(img_path)

        except Exception as e:
            logging.warning(f"Ошибка fal.ai: {e}")
            time.sleep(10)

    return None


def generate_image(title):
    img = generate_image_fal(title)
    if img:
        return img
    logging.warning("fal.ai не сработал → используем fallback")
    return random.choice(FALLBACK_IMAGES)


# -------------------- Остальные функции (save_post, send_to_telegram, main) --------------------
# Оставляем без изменений — они уже идеальны

if __name__ == "__main__":
    main()
