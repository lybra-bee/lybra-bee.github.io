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
AIHORDE_API_KEY = os.getenv("AIHORDE_API_KEY", "0000000000")  # Зарегистрируйте ключ на stablehorde.net для лучшего приоритета!

FALLBACK_IMAGES = [
    "https://picsum.photos/1024/1024?random=1",
    "https://picsum.photos/1024/1024?random=2",
    "https://picsum.photos/1024/1024?random=3",
    "https://picsum.photos/1024/1024?random=4",
    "https://picsum.photos/1024/1024?random=5",
]

# -------------------- Генерация заголовка и статьи --------------------
# (функции generate_title и generate_body без изменений)

# -------------------- Изображение: AI Horde (низкая нагрузка для бесплатного использования) --------------------
def generate_image_horde(title):
    prompt = f"{title}, futuristic artificial intelligence, neural networks, cyberpunk aesthetic, photorealistic, highly detailed, cinematic lighting, vibrant neon colors, masterpiece, best quality"

    url_async = "https://stablehorde.net/api/v2/generate/async"

    payload = {
        "prompt": prompt,
        "models": ["FLUX.1 [schnell]", "Flux.1 Dev", "SDXL 1.0"],
        "params": {
            "width": 1024,    # Стандартный размер, низкие kudos
            "height": 1024,
            "steps": 20,      # Меньше steps = меньше kudos
            "cfg_scale": 7.0,
            "n": 1
        },
        "nsfw": False,
        "trusted_workers": True,
        "slow_workers": False
    }

    headers = {
        "apikey": AIHORDE_API_KEY,
        "Content-Type": "application/json",
        "Client-Agent": "LybraBlogBot:1.0:contact@example.com"
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

        check_url = f"https://stablehorde.net/api/v2/generate/check/{job_id}"
        status_url = f"https://stablehorde.net/api/v2/generate/status/{job_id}"

        for poll in range(60):
            time.sleep(10)
            check = requests.get(check_url, headers=headers, timeout=60).json()
            if check.get("done"):
                final = requests.get(status_url, headers=headers, timeout=60).json()
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

            wait = check.get("wait_time", 10)
            queue = check.get("queue_position", 0)
            logging.info(f"Ожидание ~{wait}s, позиция в очереди: {queue}")

    except Exception as e:
        logging.warning(f"Ошибка AI Horde: {e}")

    return None


# -------------------- Telegram (улучшенное экранирование) --------------------
def send_to_telegram(title, body, image_path):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return

    teaser = ' '.join(body.split()[:40]) + '…'

    def esc(text):
        # Экранируем все специальные символы MarkdownV2
        return (text.replace('\\', '\\\\')
                    .replace('_', '\\_')
                    .replace('*', '\\*')
                    .replace('[', '\\[')
                    .replace(']', '\\]')
                    .replace('(', '\\(')
                    .replace(')', '\\)')
                    .replace('~', '\\~')
                    .replace('`', '\\`')
                    .replace('>', '\\>')
                    .replace('#', '\\#')
                    .replace('+', '\\+')
                    .replace('-', '\\-')
                    .replace('=', '\\=')
                    .replace('|', '\\|')
                    .replace('{', '\\{')
                    .replace('}', '\\}')
                    .replace('.', '\\.')
                    .replace('!', '\\!'))

    message = f"*Новая статья в блоге\\!*\n\n*{esc(title)}*\n\n{esc(teaser)}\n\n[Читать полностью →](https://lybra-ai.ru)\n\n\\#ИИ \\#LybraAI \\#искусственный_интеллект"

    # ... (остальной код отправки без изменений)

# -------------------- Остальное без изменений --------------------

if __name__ == "__main__":
    main()
