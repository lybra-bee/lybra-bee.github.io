#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
import time
import json
import random
import logging
import requests
from datetime import datetime
from pathlib import Path
import base64
import tempfile

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

# -------------------- Папки --------------------
POSTS_DIR = Path("_posts")
IMAGES_DIR = Path("assets/images/posts")
POSTS_DIR.mkdir(exist_ok=True)
IMAGES_DIR.mkdir(exist_ok=True)

# -------------------- API ключи --------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
FUSIONBRAIN_API_KEY = os.getenv("FUSIONBRAIN_API_KEY")
FUSION_SECRET_KEY = os.getenv("FUSION_SECRET_KEY")

FALLBACK_IMAGES = [
    "https://picsum.photos/800/600?random=1",
    "https://picsum.photos/800/600?random=2",
    "https://picsum.photos/800/600?random=3",
]

# -------------------- Шаг 1: Генерация заголовка --------------------
def generate_title(topic):
    groq_model = "llama-3.3-70b-versatile"
    system_prompt = f"""Ты — эксперт по SMM и копирайтингу для блога об ИИ.
    Создай один яркий, кликабельный заголовок на тему '{topic}'.
    Заголовок должен быть на русском, содержать 10-15 слов, использовать приёмы: цифры, вопросы, слова "Как", "Почему", "Топ", "Будущее", "Революция", "Секреты", "2025" и т.д.
    Он должен вызывать любопытство и желание кликнуть.
    Формат ответа строго: ЗАГОЛОВОК: [твой заголовок]"""

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    payload = {
        "model": groq_model,
        "messages": [{"role": "system", "content": system_prompt},
                     {"role": "user", "content": "Создай заголовок."}],
        "max_tokens": 100,
        "temperature": 1.0,
    }

    for attempt in range(7):
        logging.info(f"Title attempt {attempt+1}: {topic}")
        try:
            r = requests.post(url, headers=headers, json=payload)
            r.raise_for_status()
            text = r.json()["choices"][0]["message"]["content"]
            match = re.search(r"ЗАГОЛОВОК:\s*(.+)", text, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                if len(title.split()) >= 8:  # Минимум 8 слов для надёжности
                    return title
        except Exception as e:
            logging.error(f"Title error: {e}")
            time.sleep(2)
    raise RuntimeError("Failed to generate valid title")

# -------------------- Шаг 2: Генерация статьи по заголовку --------------------
def generate_body(title):
    groq_model = "llama-3.3-70b-versatile"
    system_prompt = f"""Напиши полную информативную статью для блога об ИИ по заголовку: "{title}"
    Статья на русском, 600-900 слов, с абзацами, без политики, скандалов, морали или регуляций.
    Сделай текст увлекательным, с примерами и выводами."""

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    payload = {
        "model": groq_model,
        "messages": [{"role": "system", "content": system_prompt},
                     {"role": "user", "content": "Напиши статью."}],
        "max_tokens": 2000,
        "temperature": 0.8,
    }

    for attempt in range(5):
        logging.info(f"Body attempt {attempt+1} for title: {title[:50]}...")
        try:
            r = requests.post(url, headers=headers, json=payload)
            r.raise_for_status()
            body = r.json()["choices"][0]["message"]["content"].strip()
            if len(body.split()) > 300:  # Минимум ~300 слов
                return body
        except Exception as e:
            logging.error(f"Body error: {e}")
            time.sleep(3)
    raise RuntimeError("Failed to generate article body")

# -------------------- Шаг 3: Изображение (Kandinsky) --------------------
def generate_image_kandinsky(prompt, timeout=600):
    if not FUSIONBRAIN_API_KEY or not FUSION_SECRET_KEY:
        logging.warning("Kandinsky keys absent, skipping")
        return None

    base_url = "https://api-key.fusionbrain.ai/key/api/v1"
    headers = {
        "X-Key": f"Key {FUSIONBRAIN_API_KEY}",
        "X-Secret": f"Secret {FUSION_SECRET_KEY}",
    }

    try:
        r = requests.get(f"{base_url}/pipelines", headers=headers)
        if not r.ok:
            logging.warning(f"Kandinsky pipelines error {r.status_code}: {r.text[:200]}")
            return None
        models = r.json()
        model_id = models[0]["id"]
    except Exception as e:
        logging.warning(f"Kandinsky model fetch error: {e}")
        return None

    full_prompt = prompt + ", photorealistic, high resolution, detailed, professional photography, relevant to AI theme"

    params = {
        "type": "GENERATE",
        "numImages": 1,
        "width": 1024,
        "height": 1024,
        "generateParams": {"query": full_prompt}
    }

    files = {
        "model_id": (None, model_id),
        "params": (None, json.dumps(params), "application/json")
    }

    start_time = time.time()
    try:
        r = requests.post(f"{base_url}/text2image/run", headers=headers, files=files)
        if not r.ok:
            logging.warning(f"Kandinsky run error {r.status_code}: {r.text[:200]}")
            return None
        uuid = r.json()["uuid"]
    except Exception as e:
        logging.warning(f"Kandinsky run request error: {e}")
        return None

    while time.time() - start_time < timeout:
        try:
            r = requests.get(f"{base_url}/text2image/status/{uuid}", headers=headers)
            if not r.ok:
                time.sleep(10)
                continue
            data = r.json()
            status = data["status"]
            if status == "DONE":
                img_data = data["images"][0]
                img_path = IMAGES_DIR / f"post-{int(time.time())}.jpg"
                with open(img_path, "wb") as f:
                    f.write(base64.b64decode(img_data))
                logging.info(f"Image generated by Kandinsky: {img_path}")
                return str(img_path)
            elif status == "FAILED":
                logging.warning("Kandinsky generation failed")
                return None
            time.sleep(10)
        except Exception:
            time.sleep(10)

    logging.warning("Kandinsky timeout → fallback")
    return None

def generate_image(title):
    img = generate_image_kandinsky(title)
    if img:
        return img
    logging.warning("Kandinsky failed → using fallback URL")
    return random.choice(FALLBACK_IMAGES)

# -------------------- Сохранение --------------------
def save_post(title, body):
    today = datetime.now().strftime("%Y-%m-%d")
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', title.lower()).strip('-')[:100]  # Обрезаем для безопасности
    if not slug or len(slug) < 10:
        slug = "ai-revolution-" + today.replace("-", "")
    filename = POSTS_DIR / f"{today}-{slug}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"---\ntitle: {title}\ndate: {today}\n---\n\n{body}\n")
    logging.info(f"Saved post: {filename}")
    return filename

# -------------------- Telegram --------------------
def send_to_telegram(title, body, image_path):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logging.warning("Telegram keys absent, skipping")
        return

    teaser = ' '.join(body.split()[:30]) + '…'
    def esc(text): return re.sub(r'([_*\[\]\(\)~`>#+\-=|{}.!])', r'\\\1', text)
    message = f"*Новая статья*\n\n{esc(teaser)}\n\n[Читать на сайте](https://lybra-ai.ru)\n\n{esc('#ИИ #LybraAI')}"

    try:
        if image_path.startswith('http'):
            r = requests.get(image_path)
            if not r.ok:
                logging.warning(f"Failed to download fallback image: {r.status_code}")
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
                files={"photo": photo}
            )

        if resp.status_code != 200:
            logging.warning(f"Telegram error {resp.status_code}: {resp.text}")
        else:
            logging.info(f"Telegram status {resp.status_code}")

        if image_path.startswith('http'):
            os.unlink(image_file)
    except Exception as e:
        logging.warning(f"Telegram error: {e}")

# -------------------- MAIN --------------------
def main():
    topics = ["ИИ в автоматизации контента", "Мультимодальные модели", "Генеративные модели 2025"]
    topic = random.choice(topics)

    title = generate_title(topic)
    body = generate_body(title)
    img_path = generate_image(title)
    save_post(title, body)
    send_to_telegram(title, body, img_path)
    logging.info("=== DONE ===")

if __name__ == "__main__":
    main()
