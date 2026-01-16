#!/usr/bin/env python3
# -*- coding: utf-8*

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

# -------------------- Транслит --------------------
TRANSLIT_MAP = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
    'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
}

def translit(text):
    text = text.lower()
    return ''.join(TRANSLIT_MAP.get(c, c) for c in text)

# -------------------- Заголовок --------------------
def generate_title(topic):
    system_prompt = f"""
Ты — профессиональный редактор технического блога про ИИ.

Создай ОДИН заголовок на русском по теме "{topic}",
но подай её как ПРАКТИЧЕСКИЙ МАТЕРИАЛ.

Требования:
- 8–16 слов
- Формат: гайд / инструкция / мастер-класс / практический разбор
- Без философии и футурологии
- Заголовок должен обещать реальную пользу

Запрещено:
- «будущее», «революция», «AGI», «2026», абстракции

Ответ строго:
ЗАГОЛОВОК: ...
"""

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "system", "content": system_prompt}],
        "max_tokens": 120,
        "temperature": 1.1,
    }

    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
        json=payload,
        timeout=60
    )
    text = r.json()["choices"][0]["message"]["content"]
    return re.sub(r"ЗАГОЛОВОК:\s*", "", text).strip()

# -------------------- СТАТЬЯ (ИЗМЕНЁН ПРОМПТ) --------------------
def generate_body(title):
    system_prompt = f"""
Ты — практикующий инженер и архитектор ИИ.

Напиши ПОЛЕЗНУЮ статью в формате:
урок / гайд / мастер-класс / обзор / лайфхак.

Тема определяется заголовком:
"{title}"

СТРОГО:
- Только практическая работа с нейросетями
- Ускорение инференса, оптимизация, агенты, пайплайны, интеграции
- Только актуальные подходы (последние 6–12 месяцев)
- Никаких устаревших API и методов
- Без философии и отвлечённых рассуждений

СТРУКТУРА:
## Зачем это нужно
## Проблема
## Практическое решение
## Советы и приёмы
## Ошибки и ограничения
## Итог

ФОРМАТ:
- Markdown
- 3000–5000 знаков
"""

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "system", "content": system_prompt}],
        "max_tokens": 1800,
        "temperature": 0.9,
    }

    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
        json=payload,
        timeout=120
    )
    return r.json()["choices"][0]["message"]["content"].strip()

# -------------------- Horde изображение --------------------
def generate_image(title):
    fallback_url = random.choice(FALLBACK_IMAGES)
    logging.warning(f"Изображение fallback: {fallback_url}")
    return fallback_url

# -------------------- Сохранение поста --------------------
def save_post(title, body, img_path=None):
    today = datetime.now()
    date_str = today.strftime("%Y-%m-%d")
    full_date_str = today.strftime("%Y-%m-%d 00:00:00 -0000")

    slug = re.sub(r'[^a-z0-9-]+', '-', translit(title)).strip('-')[:80]
    if len(slug) < 10:
        slug = "ai-post-" + ''.join(random.choices("abcdefghijklmnopqrstuvwxyz", k=10))

    filename = POSTS_DIR / f"{date_str}-{slug}.md"

    frontmatter = "---\n"
    frontmatter += f"title: \"{title}\"\n"
    frontmatter += f"date: {full_date_str}\n"
    frontmatter += "layout: post\n"
    frontmatter += "categories: ai\n"
    frontmatter += "tags: [ИИ, нейросети, практика]\n"

    if img_path:
        frontmatter += f"image: {img_path}\n"
        frontmatter += f"image_alt: \"{title}\"\n"
        frontmatter += f"description: \"{title} — практический разбор\"\n"

    frontmatter += "---\n\n"

    filename.write_text(frontmatter + body, encoding="utf-8")
    article_url = f"{SITE_URL}/{slug}/"
    return str(filename), article_url

# -------------------- Telegram --------------------
def send_to_telegram(title, teaser_text, image_path, article_url):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return

    caption = f"<b>{title}</b>\n\n{teaser_text}\n\n{article_url}"

    with requests.get(image_path, stream=True) as img:
        resp = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto",
            data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption, "parse_mode": "HTML"},
            files={"photo": img.raw}
        )

# -------------------- MAIN --------------------
def main():
    topics = [
        "Оптимизация инференса LLM",
        "Автономные ИИ-агенты",
        "Мультимодальные пайплайны",
        "Запуск ИИ локально",
        "Связка нескольких нейросетей",
        "Оптимизация GPU и CPU для ИИ",
        "Интеграция ИИ в приложения"
    ]

    topic = random.choice(topics)
    title = generate_title(topic)
    body = generate_body(title)
    img_path = generate_image(title)

    _, article_url = save_post(title, body, img_path)
    teaser = " ".join(body.split()[:40]) + "..."
    send_to_telegram(title, teaser, img_path, article_url)

    logging.info("=== ГОТОВО ===")

if __name__ == "__main__":
    main()
