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
HF_API_TOKEN = os.getenv("HF_API_TOKEN")  # Обязательно добавить в GitHub Secrets

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
            r = requests.post(url, headers=headers, json=payload, timeout=60)
            r.raise_for_status()
            text = r.json()["choices"][0]["message"]["content"]
            match = re.search(r"ЗАГОЛОВОК:\s*(.+)", text, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                if len(title.split()) >= 8:
                    return title
        except Exception as e:
            logging.error(f"Title error: {e}")
            time.sleep(3)
    raise RuntimeError("Failed to generate valid title")


# -------------------- Шаг 2: Генерация статьи по заголовку --------------------
def generate_body(title):
    groq_model = "llama-3.3-70b-versatile"
    system_prompt = f"""Напиши полную статью для блога об ИИ по заголовку: "{title}"

Требования:
- На русском языке
- 600-900 слов
- ОБЯЗАТЕЛЬНО используй Markdown-заголовки: один главный ## Введение, несколько ### для основных разделов, #### для подразделов
- Структура: Введение → Основные пункты/разделы с примерами → Заключение
- Без политики, скандалов, морали или регуляций
- Текст увлекательный, с примерами и выводами"""

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    payload = {
        "model": groq_model,
        "messages": [{"role": "system", "content": system_prompt},
                     {"role": "user", "content": "Напиши статью."}],
        "max_tokens": 3000,
        "temperature": 0.8,
    }

    for attempt in range(5):
        logging.info(f"Body attempt {attempt+1} for title: {title[:50]}...")
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=120)
            r.raise_for_status()
            body = r.json()["choices"][0]["message"]["content"].strip()
            if len(body.split()) > 300:
                return body
        except Exception as e:
            logging.error(f"Body error: {e}")
            time.sleep(5)
    raise RuntimeError("Failed to generate article body")


# -------------------- Изображение: Stable Diffusion (бесплатно через HF) --------------------
def generate_image_sd(title):
    if not HF_API_TOKEN:
        logging.warning("HF_API_TOKEN отсутствует, пропускаем Stable Diffusion")
        return None

    model = "runwayml/stable-diffusion-v1-5"
    url = f"https://api-inference.huggingface.co/models/{model}"
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}

    full_prompt = f"{title}, photorealistic, high resolution, detailed, professional photography, futuristic AI theme, 8k"

    payload = {"inputs": full_prompt}

    for attempt in range(5):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=60)
            if r.status_code == 503:
                logging.info("Модель загружается, ждём 20 секунд...")
                time.sleep(20)
                continue
            if not r.ok:
                logging.warning(f"SD ошибка {r.status_code}: {r.text}")
                return None

            timestamp = int(time.time())
            img_path = IMAGES_DIR / f"post-{timestamp}.jpg"
            with open(img_path, "wb") as f:
                f.write(r.content)
            logging.info(f"Изображение сгенерировано через Stable Diffusion: {img_path}")
            return str(img_path)
        except Exception as e:
            logging.warning(f"Ошибка запроса SD: {e}")
            time.sleep(10)
    return None


def generate_image(title):
    img = generate_image_sd(title)
    if img:
        return img
    logging.warning("Stable Diffusion не сработал → используем fallback-изображение")
    return random.choice(FALLBACK_IMAGES)


# -------------------- Сохранение поста --------------------
def save_post(title, body, img_path=None):
    today = datetime.now().strftime("%Y-%m-%d")
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', title.lower()).strip('-')[:100]
    if not slug or len(slug) < 10:
        slug = "ai-post-" + ''.join(filter(str.isdigit, today))

    filename = POSTS_DIR / f"{today}-{slug}.md"

    content = f"---\ntitle: {title}\ndate: {today}\ncategories: ai\n"

    # Добавляем обложку в front matter, если изображение локальное
    if img_path and not img_path.startswith('http'):
        rel_path = f"/assets/images/posts/{Path(img_path).name}"
        content += f"image: {rel_path}\n"

    content += "---\n\n"

    # Вставляем изображение в начало статьи (только если локальное)
    if img_path and not img_path.startswith('http'):
        image_name = Path(img_path).name
        # Самый простой и надёжный способ — без сложной экранировки скобок
        content += f"![{title}]({{{{ site.baseurl }}}}/assets/images/posts/{image_name})\n\n"

    content += body

    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

    logging.info(f"Пост сохранён: {filename}")
    return filename


# -------------------- Отправка в Telegram --------------------
def send_to_telegram(title, body, image_path):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logging.warning("Ключи Telegram отсутствуют, пропускаем отправку")
        return

    teaser = ' '.join(body.split()[:40]) + '…'

    def esc(text):
        return re.sub(r'([_*\[\]\(\)~`>#+\-=|{}.!])', r'\\\1', text)

    message = f"*Новая статья в блоге!*\n\n*{esc(title)}*\n\n{esc(teaser)}\n\n[Читать полностью →](https://lybra-ai.ru)\n\n#ИИ #LybraAI #искусственный_интеллект"

    try:
        if image_path.startswith('http'):
            r = requests.get(image_path, timeout=30)
            if not r.ok:
                logging.warning(f"Не удалось скачать fallback-изображение: {r.status_code}")
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
                data={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "caption": message,
                    "parse_mode": "MarkdownV2",
                    "disable_web_page_preview": True
                },
                files={"photo": photo},
                timeout=60
            )

        if resp.status_code != 200:
            logging.warning(f"Ошибка Telegram {resp.status_code}: {resp.text}")
        else:
            logging.info("Пост успешно отправлен в Telegram")

        if image_path.startswith('http'):
            os.unlink(image_file)

    except Exception as e:
        logging.warning(f"Ошибка отправки в Telegram: {e}")


# -------------------- MAIN --------------------
def main():
    topics = [
        "ИИ в автоматизации контента",
        "Мультимодальные модели",
        "Генеративные модели 2025",
        "Агенты ИИ и автономные системы",
        "ИИ в креативных профессиях"
    ]
    topic = random.choice(topics)

    logging.info(f"Выбрана тема: {topic}")

    title = generate_title(topic)
    body = generate_body(title)
    img_path = generate_image(title)

    post_file = save_post(title, body, img_path)
    send_to_telegram(title, body, img_path)

    logging.info("=== Пост успешно создан и опубликован ===")


if __name__ == "__main__":
    main()
