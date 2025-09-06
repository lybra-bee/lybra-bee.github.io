#!/usr/bin/env python3
import os
import requests
import json
import random
from datetime import datetime, timezone
import logging
import base64
import hashlib
import hmac
from pathlib import Path

# === Настройка логов ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# === API ключи ===
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
FUSIONBRAIN_API_KEY = os.getenv("FUSIONBRAIN_API_KEY")
FUSION_SECRET_KEY = os.getenv("FUSION_SECRET_KEY")

# === Пути ===
CONTENT_DIR = Path("content/posts")
IMAGES_DIR = Path("assets/images/posts")

CONTENT_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# === Генерация статьи ===
def generate_article():
    logging.info("📝 Генерация статьи через OpenRouter / Groq")

    prompt = (
        "Напиши свежую статью на русском языке о нейросетях и высоких технологиях, "
        "основываясь на последних мировых трендах. Обязательно придумай красивый заголовок."
    )

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        text = data["choices"][0]["message"]["content"].strip()

        # Разделяем заголовок и текст
        if "\n" in text:
            title, body = text.split("\n", 1)
        else:
            title, body = "Статья о нейросетях", text

        return title.strip("# ").strip(), body.strip()
    except Exception as e:
        logging.error(f"Ошибка при генерации статьи: {e}")
        return "Ошибка генерации", "Не удалось получить статью."


# === Генерация изображения через FusionBrain ===
def generate_image(prompt, filename):
    logging.info("🎨 Генерация изображения через FusionBrain")

    url = "https://api-key.fusionbrain.ai/text2image/run"
    nonce = str(int(datetime.now().timestamp()))
    sign = hmac.new(FUSION_SECRET_KEY.encode(), nonce.encode(), hashlib.sha256).hexdigest()

    headers = {
        "X-Key": f"Key {FUSIONBRAIN_API_KEY}",
        "X-Nonce": nonce,
        "X-Sign": f"Signature {sign}",
    }

    payload = {"text": prompt, "size": "1024x1024"}
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=120)
        r.raise_for_status()
        data = r.json()
        if "image" in data:
            image_b64 = data["image"]
            img_path = IMAGES_DIR / filename
            with open(img_path, "wb") as f:
                f.write(base64.b64decode(image_b64))
            logging.info(f"✅ Картинка сохранена: {img_path}")
            return str(img_path)
        else:
            logging.warning("FusionBrain не вернул картинку")
            return None
    except Exception as e:
        logging.error(f"Ошибка при генерации изображения: {e}")
        return None


# === Сохранение статьи ===
def save_article(title, body, image_filename):
    safe_title = title.replace('"', "'")
    slug = "-".join(title.lower().split()[:6])
    filename = CONTENT_DIR / f"{slug}.md"

    front_matter = [
        "---",
        f'title: "{safe_title}"',
        f'date: {datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")}',
        f'image: "/images/posts/{image_filename}"',
        'tags: ["Нейросети", "Технологии"]',
        "---",
    ]

    content = "\n".join(front_matter) + "\n\n" + body
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

    logging.info(f"📄 Статья сохранена: {filename}")


# === Основной запуск ===
def main():
    title, body = generate_article()
    image_filename = f"{title.replace(' ', '_')}.png"

    image_path = generate_image(title, image_filename)
    if not image_path:
        image_filename = "default.png"  # если картинка не сгенерировалась

    save_article(title, body, image_filename)


if __name__ == "__main__":
    main()
