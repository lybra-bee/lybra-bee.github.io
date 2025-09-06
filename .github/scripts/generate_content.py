#!/usr/bin/env python3
import os
import requests
import logging
import json
import re
from datetime import datetime
from pathlib import Path

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Пути
POSTS_DIR = Path("content/posts")
IMAGES_DIR = Path("static/images/posts")
GALLERY_DIR = Path("static/images/gallery")

# Создание директорий (с проверкой существования)
for d in [POSTS_DIR, IMAGES_DIR, GALLERY_DIR]:
    if not d.exists():
        d.mkdir(parents=True, exist_ok=True)

# Ключи из секретов
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
FUSIONBRAIN_API_KEY = os.getenv("FUSIONBRAIN_API_KEY")
FUSION_SECRET_KEY = os.getenv("FUSION_SECRET_KEY")


def slugify(text: str) -> str:
    return re.sub(r"[^a-zA-Zа-яА-Я0-9]+", "-", text).strip("-").lower()


def generate_article() -> dict:
    """Генерация статьи про нейросети и высокие технологии"""
    logging.info("📝 Генерация статьи через OpenRouter / Groq")

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
    payload = {
        "model": "anthropic/claude-3.5-sonnet",
        "messages": [
            {"role": "system", "content": "Ты пишешь статью для AI-блога."},
            {
                "role": "user",
                "content": "Напиши статью на русском языке про последние тренды в области нейросетей и высоких технологий.",
            },
        ],
    }

    response = requests.post(url, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]

    # Заголовок = первая строка или первая фраза
    title = content.split("\n")[0].strip().replace("#", "")
    body = "\n".join(content.split("\n")[1:]).strip()

    return {"title": title, "body": body}


def generate_image(prompt: str, filename: str) -> str:
    """Генерация изображения через FusionBrain"""
    logging.info("🎨 Генерация изображения через FusionBrain")

    url = "https://api.fusionbrain.ai/v1/text2image/run"
    headers = {
        "X-Key": f"Key {FUSIONBRAIN_API_KEY}",
        "X-Secret": f"Secret {FUSION_SECRET_KEY}",
    }
    files = {
        "prompt": (None, prompt),
        "width": (None, "1024"),
        "height": (None, "576"),
    }

    response = requests.post(url, headers=headers, files=files, timeout=120)

    if response.status_code != 200:
        logging.error(f"Ошибка при генерации изображения: {response.text}")
        return ""

    out_path = IMAGES_DIR / filename
    with open(out_path, "wb") as f:
        f.write(response.content)

    # Копируем в галерею
    gallery_path = GALLERY_DIR / filename
    with open(gallery_path, "wb") as f:
        f.write(response.content)

    return str(out_path)


def save_post(title: str, body: str, image_path: str):
    """Сохраняем пост в Hugo"""
    slug = slugify(title)
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    frontmatter = [
        "---",
        f'title: "{title}"',
        f"date: {date}",
        f"slug: {slug}",
        f"image: /images/posts/{Path(image_path).name}" if image_path else "",
        "---",
    ]

    content = "\n".join(frontmatter) + "\n\n" + body
    out_file = POSTS_DIR / f"{slug}.md"

    with open(out_file, "w", encoding="utf-8") as f:
        f.write(content)

    logging.info(f"📄 Статья сохранена: {out_file}")


def cleanup_posts(keep: int = 5):
    """Удаляем старые статьи, оставляем последние N"""
    posts = sorted(POSTS_DIR.glob("*.md"), key=os.path.getmtime, reverse=True)
    for old in posts[keep:]:
        old.unlink()
        logging.info(f"🗑 Удалена старая статья: {old}")


def main():
    article = generate_article()
    filename = slugify(article["title"]) + ".jpg"
    image_path = generate_image(article["title"], filename)
    save_post(article["title"], article["body"], image_path)
    cleanup_posts()


if __name__ == "__main__":
    main()
