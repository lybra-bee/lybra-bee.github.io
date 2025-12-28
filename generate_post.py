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
AIHORDE_API_KEY = os.getenv("AIHORDE_API_KEY", "0000000000")  # Теперь будет ваш настоящий ключ!

FALLBACK_IMAGES = [
    "https://picsum.photos/1024/768?random=10",
    "https://picsum.photos/1024/768?random=11",
    "https://picsum.photos/1024/768?random=12",
    "https://picsum.photos/1024/768?random=13",
    "https://picsum.photos/1024/768?random=14",
]

# -------------------- Генерация заголовка и статьи (без изменений) --------------------
# (generate_title и generate_body — оставляем как есть)

# -------------------- Изображение: AI Horde --------------------
def generate_image_horde(title):
    prompt = f"{title}, futuristic artificial intelligence, neural networks, cyberpunk aesthetic, photorealistic, highly detailed, cinematic lighting, vibrant neon colors, masterpiece, best quality"

    url_async = "https://stablehorde.net/api/v2/generate/async"

    payload = {
        "prompt": prompt,
        "models": ["FLUX.1 [schnell]", "Flux.1 Dev", "SDXL 1.0"],
        "params": {
            "width": 1024,
            "height": 768,   # 4:3 — меньше kudos, чем 1024x1024
            "steps": 20,
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


def generate_image(title):
    img = generate_image_horde(title)
    if img:
        return img
    logging.warning("AI Horde не сработал → используем fallback picsum")
    return random.choice(FALLBACK_IMAGES)


# -------------------- Сохранение поста (без изменений) --------------------
# (save_post — как в предыдущей версии)

# -------------------- Telegram — финальное безопасное сообщение --------------------
def send_to_telegram(title, body, image_path):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return

    teaser = ' '.join(body.split()[:60]) + '…'  # Увеличил до 60 слов для информативности

    def esc(text):
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

    # Самое безопасное: только жирный для заголовка, остальное — обычный текст
    message = f"*Новая статья в блоге!*\n\n{esc(title)}\n\n{esc(teaser)}\n\n[Читать полностью →](https://lybra-ai.ru)\n\n\\#ИИ \\#LybraAI \\#искусственный_интеллект"

    logging.info(f"Отправляемое сообщение в Telegram:\n{message}")

    try:
        if image_path.startswith('http'):
            r = requests.get(image_path, timeout=30)
            if not r.ok:
                return
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
            temp_file.write(r.content)
            temp_file.close()
            image_file = temp_file.name
        else:
            image_file = image_path

        with open(image_file, "rb") as photo:
            resp = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto",
                data={"chat_id": TELEGRAM_CHAT_ID, "caption": message, "parse_mode": "MarkdownV2"},
                files={"photo": photo},
                timeout=60
            )

        if image_path.startswith('http'):
            os.unlink(image_file)

        if resp.status_code != 200:
            logging.warning(f"Telegram ошибка: {resp.status_code} {resp.text}")
        else:
            logging.info("Пост успешно отправлен в Telegram")

    except Exception as e:
        logging.warning(f"Ошибка отправки в Telegram: {e}")


# -------------------- MAIN (с защитой) --------------------
def main():
    try:
        topics = [
            "ИИ в автоматизации контента",
            "Мультимодальные модели ИИ",
            "Генеративный ИИ в 2025 году",
            "Автономные ИИ-агенты",
            "ИИ в креативных профессиях",
            "Будущее нейросетей и AGI",
            "ИИ и обработка естественного языка"
        ]
        topic = random.choice(topics)
        logging.info(f"Тема дня: {topic}")

        title = generate_title(topic)
        body = generate_body(title)
        img_path = generate_image(title)

        save_post(title, body, img_path)
        send_to_telegram(title, body, img_path)

        logging.info("=== Пост успешно создан и опубликован ===")
    except Exception as e:
        logging.error(f"Критическая ошибка в main: {e}")


if __name__ == "__main__":
    main()
