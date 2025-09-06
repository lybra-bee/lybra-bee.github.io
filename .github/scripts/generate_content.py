#!/usr/bin/env python3
import os
import requests
import logging
import base64
import shutil
import re
from datetime import datetime, timezone
import time

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Директории
CONTENT_DIR = "content/posts"
ASSETS_DIR = "assets/images/posts"
STATIC_DIR = "static/images/posts"

# Ключи из ENV
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
FUSIONBRAIN_API_KEY = os.getenv("FUSIONBRAIN_API_KEY")

# Утилита для слага
def slugify(text):
    return re.sub(r'[^a-z0-9-]', '', text.lower().replace(" ", "-"))[:50]

# === Генерация статьи ===
def generate_article():
    logging.info("📝 Генерация статьи...")

    prompt = (
        "Проанализируй последние тренды в искусственном интеллекте и высоких технологиях "
        "и напиши статью на русском языке, объемом 400–600 слов. "
        "В начале укажи заголовок в формате: 'Заголовок: ...'."
    )

    headers = {"Content-Type": "application/json"}
    body = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}]
    }

    # Пробуем OpenRouter
    if OPENROUTER_API_KEY:
        try:
            r = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={**headers, "Authorization": f"Bearer {OPENROUTER_API_KEY}"},
                json=body,
                timeout=60
            )
            r.raise_for_status()
            content = r.json()["choices"][0]["message"]["content"]
            logging.info("✅ Статья получена через OpenRouter")
            return content, "OpenRouter"
        except Exception as e:
            logging.warning(f"⚠️ OpenRouter не сработал: {e}")

    # Пробуем Groq
    if GROQ_API_KEY:
        try:
            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={**headers, "Authorization": f"Bearer {GROQ_API_KEY}"},
                json=body,
                timeout=60
            )
            r.raise_for_status()
            content = r.json()["choices"][0]["message"]["content"]
            logging.info("✅ Статья получена через Groq")
            return content, "Groq"
        except Exception as e:
            logging.warning(f"⚠️ Groq не сработал: {e}")

    raise RuntimeError("❌ Не удалось сгенерировать статью")

# === Извлечение заголовка ===
def extract_title(text):
    match = re.search(r"Заголовок:\s*(.+)", text)
    if match:
        return match.group(1).strip()
    return "AI и технологии: свежий обзор"

# === Генерация изображения ===
def generate_image(title, slug):
    logging.info("🎨 Генерация изображения через FusionBrain...")

    url = "https://api-key.fusionbrain.ai/key/api/v1/text2image/run"
    headers = {"X-Key": f"Key {FUSIONBRAIN_API_KEY}"}

    payload = {
        "type": "GENERATE",
        "style": "DEFAULT",
        "width": 1024,
        "height": 576,
        "num_images": 1,
        "text": f"Иллюстрация к статье: {title}. Современный стиль, hi-tech, искусственный интеллект."
    }

    r = requests.post(url, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    uuid = data.get("uuid")

    if not uuid:
        logging.error("❌ FusionBrain не вернул UUID задачи")
        return "/images/placeholder.jpg"

    # Ожидание результата
    status_url = f"https://api-key.fusionbrain.ai/key/api/v1/text2image/status/{uuid}"
    for i in range(20):  # до 60 секунд ожидания
        s = requests.get(status_url, headers=headers)
        s.raise_for_status()
        resp = s.json()

        if resp.get("status") == "DONE":
            img_b64 = resp["images"][0]
            img_data = base64.b64decode(img_b64)

            os.makedirs(ASSETS_DIR, exist_ok=True)
            os.makedirs(STATIC_DIR, exist_ok=True)

            img_path = os.path.join(ASSETS_DIR, f"{slug}.png")
            with open(img_path, "wb") as f:
                f.write(img_data)
            shutil.copy(img_path, os.path.join(STATIC_DIR, f"{slug}.png"))

            logging.info("✅ Изображение сохранено")
            return f"/images/posts/{slug}.png"

        logging.info(f"⌛ Ждём генерацию изображения... ({i+1}/20)")
        time.sleep(3)

    logging.error("⚠️ FusionBrain не успел сгенерировать изображение")
    return "/images/placeholder.jpg"

# === Сохранение статьи ===
def save_article(title, content, model, image_url):
    os.makedirs(CONTENT_DIR, exist_ok=True)
    slug = slugify(title)

    filename = os.path.join(
        CONTENT_DIR, f"{datetime.now().strftime('%Y-%m-%d')}-{slug}.md"
    )

    with open(filename, "w", encoding="utf-8") as f:
        f.write("---\n")
        f.write(f'title: "{title}"\n')
        f.write(f'date: {datetime.now(timezone.utc).isoformat()}\n')
        f.write(f'model: {model}\n')
        f.write(f'image: {image_url}\n')
        f.write("---\n\n")
        f.write(content)

    logging.info(f"✅ Статья сохранена: {filename}")

# === Очистка старых статей ===
def cleanup_articles():
    files = sorted(
        [os.path.join(CONTENT_DIR, f) for f in os.listdir(CONTENT_DIR)],
        key=os.path.getmtime,
        reverse=True
    )
    for old in files[5:]:
        os.remove(old)
        logging.info(f"🗑 Удалена старая статья: {old}")

# === Основной процесс ===
def main():
    content, model = generate_article()
    title = extract_title(content)
    slug = slugify(title)
    img_path = generate_image(title, slug)
    save_article(title, content, model, img_path)
    cleanup_articles()

if __name__ == "__main__":
    main()
