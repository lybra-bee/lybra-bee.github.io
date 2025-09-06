#!/usr/bin/env python3
import os
import json
import requests
import yaml
import re
from datetime import datetime, timezone
import logging
import textwrap
import base64
import shutil
import random

# === НАСТРОЙКИ ===
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
FUSIONBRAIN_API_KEY = os.getenv("FUSIONBRAIN_API_KEY")

CONTENT_DIR = "content/posts"
ASSETS_DIR = "assets/images/posts"
STATIC_DIR = "static/images/posts"
DATA_DIR = "data"

os.makedirs(CONTENT_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

PROMPT = "Проанализируй последние тренды в искусственном интеллекте и высоких технологиях и напиши статью на 400-600 слов."


# === ФУНКЦИИ ===
def generate_article():
    logging.info("📝 Генерация статьи...")
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": [{"role": "user", "content": PROMPT}],
        "max_tokens": 1000
    }
    r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
    r.raise_for_status()
    content = r.json()["choices"][0]["message"]["content"]

    # Если статья не в Markdown, добавим заголовок
    if not content.startswith("# "):
        first_line = content.split(".")[0][:80]
        content = f"# {first_line}\n\n{content}"

    return content.strip()


def extract_title(content):
    match = re.match(r"# (.+)", content)
    if match:
        return match.group(1).strip()
    return "AI статья"


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def generate_image(title, slug):
    logging.info("🎨 Генерация изображения...")
    headers = {"Authorization": f"Bearer {FUSIONBRAIN_API_KEY}"}
    payload = {"prompt": f"Иллюстрация к статье: {title}. Современный стиль, hi-tech, AI."}
    r = requests.post("https://api.fusionbrain.ai/v1/text2image", headers=headers, json=payload)
    r.raise_for_status()
    data = r.json()
    if "image_base64" in data:
        img_data = base64.b64decode(data["image_base64"])
        img_path = os.path.join(ASSETS_DIR, f"{slug}.png")
        with open(img_path, "wb") as f:
            f.write(img_data)
        shutil.copy(img_path, os.path.join(STATIC_DIR, f"{slug}.png"))
        return f"/images/posts/{slug}.png"
    return "/images/placeholder.jpg"


def update_gallery(img_path, title):
    yaml_path = os.path.join(DATA_DIR, "gallery.yaml")
    json_path = os.path.join(DATA_DIR, "gallery.json")

    entry = {"src": img_path, "alt": title, "title": title}

    gallery = []
    if os.path.exists(yaml_path):
        with open(yaml_path, "r", encoding="utf-8") as f:
            try:
                gallery = yaml.safe_load(f) or []
            except Exception:
                gallery = []

    gallery.insert(0, entry)

    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(gallery, f, allow_unicode=True)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(gallery, f, ensure_ascii=False, indent=2)


def save_article(content, title, slug, img_path):
    filename = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S")
    filepath = os.path.join(CONTENT_DIR, f"{filename}-{slug}.md")
    meta = textwrap.dedent(f"""\
    ---
    title: "{title}"
    date: {datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")}
    model: GPT-4o-mini
    image: {img_path}
    ---
    """)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(meta + "\n" + content)
    logging.info(f"✅ Статья сохранена: {filepath}")


# === ОСНОВНОЙ ПРОЦЕСС ===
def main():
    content = generate_article()
    title = extract_title(content)
    slug = slugify(title)
    img_path = generate_image(title, slug)
    save_article(content, title, slug, img_path)
    update_gallery(img_path, title)


if __name__ == "__main__":
    main()
