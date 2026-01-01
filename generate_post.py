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

POSTS_DIR = Path("_posts")
IMAGES_DIR = Path("assets/images/posts")
POSTS_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

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

# (generate_title, generate_outline, generate_section, generate_body, generate_image_horde, generate_image — без изменений)

# -------------------- Сохранение поста — ИСПРАВЛЕННЫЙ FRONTMATTER --------------------
def save_post(title, body, img_path=None):
    today = datetime.now()
    date_str = today.strftime("%Y-%m-%d")
    full_date_str = today.strftime("%Y-%m-%d 00:00:00 -0000")

    slug = re.sub(r'[^a-z0-9-]+', '-', translit(title)).strip('-')[:80]
    if len(slug) < 10:
        slug = "ai-news-" + ''.join(random.choices("abcdefghijklmnopqrstuvwxyz", k=10))

    filename = POSTS_DIR / f"{date_str}-{slug}.md"

    # Правильное формирование frontmatter с отступами для tags
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
            image_url = f"assets/images/posts/{Path(img_path).name}"
        frontmatter_lines.extend([
            f"image: {image_url}",
            f"image_alt: {title.rstrip('.')}",
            f"description: Статья об ИИ: {title.rstrip('.')}"
        ])

    frontmatter_lines.append("---")
    frontmatter = "\n".join(frontmatter_lines) + "\n\n"

    # Обложка в теле с site.baseurl — надёжно для всех тем
    if img_path:
        cover_img = image_url if 'image_url' in locals() else '/assets/images/placeholder.jpg'
        body_start = f"![Обложка: {title}]({{{{ site.baseurl }}}}/{cover_img})\n\n"
    else:
        body_start = ""

    full_content = frontmatter + body_start + body

    try:
        filename.write_text(full_content, encoding="utf-8")
        logging.info(f"Пост сохранён с правильным frontmatter: {filename}")
    except Exception as e:
        logging.error(f"Ошибка сохранения: {e}")
        raise

    article_url = f"{SITE_URL}/{slug}/"
    logging.info(f"Ссылка: {article_url}")
    return str(filename), article_url

# (send_to_telegram и main — без изменений)

if __name__ == "__main__":
    main()
