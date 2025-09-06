#!/usr/bin/env python3
import os
import requests
import logging
import re
import shutil
import base64
import time
from datetime import datetime
import textwrap

# --- Логирование ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# --- Пути ---
POSTS_DIR = "content/posts"
ASSETS_DIR = "static/images/posts"
STATIC_DIR = "static/images/posts"

# --- Ключи ---
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
FUSIONBRAIN_API_KEY = os.getenv("FUSIONBRAIN_API_KEY")
FUSION_SECRET_KEY = os.getenv("FUSION_SECRET_KEY")

# --- Утилиты ---
def slugify(text):
    return re.sub(r"[^a-zA-Zа-яА-Я0-9]+", "-", text.lower()).strip("-")

def save_post(title, content, image, model):
    os.makedirs(POSTS_DIR, exist_ok=True)
    slug = slugify(title) + "-" + datetime.utcnow().strftime("%Y%m%d%H%M%S")
    filename = os.path.join(POSTS_DIR, f"{slug}.md")

    front_matter = textwrap.dedent(f"""\
    ---
    title: "{title}"
    date: {datetime.utcnow().isoformat()}
    image: {image}
    model: {model}
    slug: {slug}
    ---

    {content}
    """)

    with open(filename, "w", encoding="utf-8") as f:
        f.write(front_matter)

    logging.info(f"✅ Статья сохранена: {filename}")
    return slug

# --- Генерация статьи ---
def generate_article():
    prompt = (
        "Проанализируй последние тренды в искусственном интеллекте и высоких технологиях "
        "и напиши статью на 400-600 слов на русском языке. Используй живой стиль."
    )

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.8
    }

    try:
        r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        content = data["choices"][0]["message"]["content"]
        logging.info("✅ Статья получена через OpenRouter")
        return content
    except Exception as e:
        logging.error(f"❌ Ошибка OpenRouter: {e}")
        return None

# --- Генерация изображения через FusionBrain ---
def generate_image(title, slug):
    logging.info("🎨 Генерация изображения через FusionBrain...")

    headers = {
        "X-Key": f"Key {FUSIONBRAIN_API_KEY}",
        "X-Secret": f"Secret {FUSION_SECRET_KEY}"
    }

    # 1. Получаем список моделей
    models_url = "https://api.fusionbrain.ai/v1/models"
    r = requests.get(models_url, headers=headers, timeout=30)
    r.raise_for_status()
    models = r.json()
    if not models:
        logging.error("❌ FusionBrain не вернул список моделей")
        return "/images/placeholder.jpg"

    model_id = models[0]["id"]
    logging.info(f"Используем модель ID: {model_id}")

    # 2. Запускаем задачу
    run_url = "https://api.fusionbrain.ai/v1/text2image/run"
    params = {
        "type": "GENERATE",
        "style": "DEFAULT",
        "width": 1024,
        "height": 576,
        "num_images": 1,
        "text": f"Иллюстрация к статье: {title}. Современный стиль, hi-tech, искусственный интеллект."
    }

    files = {
        "model_id": (None, str(model_id)),
        "params": (None, str(params))
    }

    r = requests.post(run_url, headers=headers, files=files, timeout=60)
    r.raise_for_status()
    data = r.json()
    uuid = data.get("uuid")

    if not uuid:
        logging.error("❌ FusionBrain не вернул UUID задачи")
        return "/images/placeholder.jpg"

    # 3. Ожидание результата
    status_url = f"https://api.fusionbrain.ai/v1/text2image/status/{uuid}"
    for i in range(20):
        s = requests.get(status_url, headers=headers, timeout=30)
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

# --- Основной процесс ---
def main():
    logging.info("📝 Генерация статьи...")
    article = generate_article()
    if not article:
        logging.error("⚠️ Статья не сгенерирована")
        return

    # Заголовок = первая строка или первая фраза
    title = article.strip().split("\n")[0][:80]
    slug = slugify(title)

    img_path = generate_image(title, slug)

    save_post(title, article, img_path, "OpenRouter + FusionBrain")

if __name__ == "__main__":
    main()
