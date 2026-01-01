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
    return ''.join(TRANSLIT_MAP.get(c, c) for c in text)

# -------------------- Шаг 1: Разнообразный заголовок --------------------
def generate_title(topic):
    groq_model = "llama-3.3-70b-versatile"
    system_prompt = f"""Ты — профессиональный копирайтер и SMM-специалист для блога об искусственном интеллекте.
Создай ОДИН очень привлекательный, эмоциональный и кликабельный заголовок на русском языке по теме: "{topic}"

Правила:
- Длина: 8–16 слов
- Запрещено начинать с "Топ 5", "Топ 10", "5 секретов", "Топ секретов" и подобных шаблонов
- Используй мощные приёмы:
  • Вопросы ("Почему все говорят о...", "Что будет, если...")
  • Интрига и парадоксы ("ИИ, который пугает экспертов")
  • Будущее ("Что ждёт нас в 2026 году")
  • Драма ("Революция, которую никто не заметил")
  • "Как...", "Когда...", "Почему..."
- Включи год 2025 или 2026, если уместно
- Заголовок должен вызывать желание кликнуть немедленно
- Делай его живым, современным и естественным

Ответ строго: ЗАГОЛОВОК: [твой заголовок]"""

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    payload = {
        "model": groq_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Придумай лучший заголовок."}
        ],
        "max_tokens": 120,
        "temperature": 1.1,
    }

    for attempt in range(10):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=60)
            if r.status_code == 429:
                wait = (2 ** attempt) + random.uniform(0, 1)
                logging.warning(f"Rate limit Groq (429). Ждём {wait:.1f} сек...")
                time.sleep(wait)
                continue
            r.raise_for_status()
            text = r.json()["choices"][0]["message"]["content"].strip()
            match = re.search(r"ЗАГОЛОВОК:\s*(.+)", text, re.IGNORECASE | re.DOTALL)
            if match:
                title = match.group(1).strip().strip('"').strip("'").strip()
                if not re.search(r'^(топ|5|10|\d+)\s', title.lower()):
                    if 8 <= len(title.split()) <= 16:
                        logging.info(f"Сгенерирован заголовок: {title}")
                        return title
            logging.warning(f"Заголовок не прошёл фильтр — retry ({attempt+1}/10)")
        except Exception as e:
            logging.error(f"Ошибка генерации заголовка: {e}")
            time.sleep(2)

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

# -------------------- Шаг 2: План и тело статьи — СТРОГО 3000–5000 знаков --------------------
def generate_outline(title):
    system_prompt = f"""Создай очень краткий план статьи по заголовку: "{title}"

- 5–7 основных разделов (##)
- Под каждым — 1 подраздел (###)
- Общий объём всей статьи: строго 3000–5000 знаков
- Только названия разделов, без текста

Ответ в чистом Markdown."""

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": "План."}],
        "max_tokens": 600,
        "temperature": 0.5,
    }

    for attempt in range(3):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=60)
            if r.status_code == 429:
                time.sleep(5)
                continue
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()
        except:
            time.sleep(3)
    return "## Введение\n### Краткий обзор\n## Основные тренды\n### Детали\n## Применение\n### Примеры\n## Риски\n### Анализ\n## Будущее\n### Прогнозы\n## Заключение\n### Итоги"

def generate_section(title, outline, section_header):
    prompt = f"""#РОЛЬ
Ты — автор увлекательных коротких текстов об ИИ для молодёжи.

#ЗАДАЧА
Напиши раздел "{section_header}" для статьи "{title}"

#КОНТЕКСТ
План статьи:
{outline}

#ТРЕБОВАНИЯ
- Объём: строго 400–700 знаков
- Разговорный тон, риторические вопросы, аналогии
- Фразы: "А знаете что?", "Представьте", "Честно говоря"
- Только текст раздела в Markdown

Напиши сейчас."""

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 200,  # Жёсткий лимит для коротких разделов
        "temperature": 0.9,
    }

    for attempt in range(5):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=120)
            if r.status_code == 429:
                time.sleep(5)
                continue
            r.raise_for_status()
            text = r.json()["choices"][0]["message"]["content"].strip()
            if 350 <= len(text) <= 750:
                return text
        except:
            time.sleep(3)

    return f"Короткий обзор раздела «{section_header}»."

def generate_body(title):
    outline = generate_outline(title)

    section_headers = [re.sub(r'^##\s*', '', line).strip() for line in outline.split("\n") if line.strip().startswith("##")]
    section_headers = section_headers[:7]  # Жёстко 5–7 разделов

    full_body = f"# {title}\n\n"
    total_chars = 0

    for i, header in enumerate(section_headers, 1):
        section_text = generate_section(title, outline, header)
        full_body += f"\n## {header}\n\n{section_text}\n\n"
        total_chars += len(section_text)
        logging.info(f"Раздел {i}: {len(section_text)} знаков (всего: {total_chars})")

    logging.info(f"Статья готова: {total_chars} знаков")
    return full_body

# -------------------- Изображение: Stable Horde --------------------
# (оставляем как есть — работает)

# -------------------- Сохранение поста — БЕЗ обложки в теле --------------------
def save_post(title, body, img_path=None):
    today = datetime.now()
    date_str = today.strftime("%Y-%m-%d")
    full_date_str = today.strftime("%Y-%m-%d 00:00:00 -0000")

    slug = re.sub(r'[^a-z0-9-]+', '-', translit(title)).strip('-')[:80]
    if len(slug) < 10:
        slug = "ai-news-" + ''.join(random.choices("abcdefghijklmnopqrstuvwxyz", k=10))

    filename = POSTS_DIR / f"{date_str}-{slug}.md"

    frontmatter_lines = [
        "---",
        f"title: {title.rstrip('.')}",
        f"date: {full_date_str}",
        "layout: post",
        "categories: ai",
        "tags:",
        "  - ИИ",
        "  - технологии",
        "  - 2026"
    ]

    if img_path:
        if img_path.startswith("http"):
            image_url = img_path
        else:
            image_url = f"/assets/images/posts/{Path(img_path).name}"
        frontmatter_lines.extend([
            f"image: {image_url}",
            f"image_alt: {title.rstrip('.')}",
            f"description: \"{title.rstrip('.')}: обзор трендов ИИ 2026\""
        ])

    frontmatter_lines.append("---")
    frontmatter = "\n".join(frontmatter_lines) + "\n\n"

    # БЕЗ обложки в теле — только frontmatter
    full_content = frontmatter + body

    try:
        filename.write_text(full_content, encoding="utf-8")
        logging.info(f"Пост сохранён: {filename}")
    except Exception as e:
        logging.error(f"Ошибка сохранения: {e}")
        raise

    article_url = f"{SITE_URL}/{slug}/"
    logging.info(f"Ссылка: {article_url}")
    return str(filename), article_url

# -------------------- Telegram и main --------------------
# (без изменений)

if __name__ == "__main__":
    main()
