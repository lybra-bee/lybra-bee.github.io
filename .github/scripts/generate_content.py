#!/usr/bin/env python3
import os
import requests
import logging
import base64
import shutil
import time
import re
from datetime import datetime
import textwrap
import yaml

# === ЛОГИ ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# === НАСТРОЙКИ ===
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
FUSIONBRAIN_API_KEY = os.getenv("FUSIONBRAIN_API_KEY")
FUSION_SECRET_KEY = os.getenv("FUSION_SECRET_KEY")

POSTS_DIR = "content/posts"
ASSETS_DIR = "assets/images/posts"
STATIC_DIR = "static/images/posts"
GALLERY_FILE = "data/gallery.yaml"

MAX_POSTS = 5


# === УТИЛИТЫ ===
def slugify(text):
    text = text.lower()
    text = re.sub(r"[^a-zа-я0-9]+", "-", text)
    return text.strip("-")


def save_article(title, content, model, image_path, slug):
    os.makedirs(POSTS_DIR, exist_ok=True)

    filename = os.path.join(POSTS_DIR, f"{slug}.md")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(textwrap.dedent(f"""\
        ---
        title: "{title}"
        date: {datetime.utcnow().isoformat()}Z
        image: {image_path}
        model: {model}
        ---

        {content}
        """))

    logging.info(f"✅ Статья сохранена: {filename}")


def cleanup_old_posts():
    files = sorted(
        [os.path.join(POSTS_DIR, f) for f in os.listdir(POSTS_DIR) if f.endswith(".md")],
        key=os.path.getmtime,
        reverse=True
    )
    if len(files) > MAX_POSTS:
        for f in files[MAX_POSTS:]:
            os.remove(f)
            logging.info(f"🗑️ Удалена старая статья: {f}")


# === ГЕНЕРАЦИЯ ТЕКСТА ===
def generate_article():
    prompt = (
        "Проанализируй последние тренды в искусственном интеллекте и высоких технологиях "
        "и напиши уникальную аналитическую статью на 400-600 слов на русском языке. "
        "Структурируй текст абзацами. Дай привлекательный заголовок."
    )

    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
    data = {
        "model": "mistral-large-latest",
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        r = requests.post("https://openrouter.ai/api/v1/chat/completions",
                          headers=headers, json=data, timeout=60)
        r.raise_for_status()
        text = r.json()["choices"][0]["message"]["content"]
        logging.info("✅ Статья получена через OpenRouter")
        return text, "openrouter"
    except Exception as e:
        logging.warning(f"⚠️ OpenRouter не сработал: {e}")
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
        data["model"] = "llama-3.1-70b-versatile"
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                          headers=headers, json=data, timeout=60)
        r.raise_for_status()
        text = r.json()["choices"][0]["message"]["content"]
        logging.info("✅ Статья получена через Groq")
        return text, "groq"


# === ГЕНЕРАЦИЯ ИЗОБРАЖЕНИЯ ===
def generate_image(title, slug):
    logging.info("🎨 Генерация изображения через FusionBrain...")

    headers = {
        "X-Key": f"Key {FUSIONBRAIN_API_KEY}",
        "X-Secret": f"Secret {FUSION_SECRET_KEY}"
    }

    prompt = f"Иллюстрация к статье: {title}. Современный стиль, hi-tech, искусственный интеллект."
    params = {
        "type": "GENERATE",
        "style": "DEFAULT",
        "width": 1024,
        "height": 576,
        "num_images": 1,
        "text": prompt
    }

    files = {"params": (None, str(params))}
    url = "https://api-key.fusionbrain.ai/key/api/v1/text2image/run"
    r = requests.post(url, headers=headers, files=files, timeout=60)
    r.raise_for_status()
    data = r.json()
    uuid = data.get("uuid")

    if not uuid:
        logging.error("❌ FusionBrain не вернул UUID задачи")
        return "/images/placeholder.jpg"

    status_url = f"https://api-key.fusionbrain.ai/key/api/v1/text2image/status/{uuid}"
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


# === ОБНОВЛЕНИЕ ГАЛЕРЕИ ===
def update_gallery(image_path, title):
    os.makedirs("data", exist_ok=True)
    gallery = []

    if os.path.exists(GALLERY_FILE):
        with open(GALLERY_FILE, "r", encoding="utf-8") as f:
            gallery = yaml.safe_load(f) or []

    gallery.insert(0, {"src": image_path, "alt": title, "title": title})

    with open(GALLERY_FILE, "w", encoding="utf-8") as f:
        yaml.dump(gallery, f, allow_unicode=True)

    logging.info("🖼️ Галерея обновлена")


# === MAIN ===
def main():
    logging.info("📝 Генерация статьи...")
    text, model = generate_article()

    # Заголовок = первая строка или первая строка с #
    title_line = text.strip().split("\n")[0]
    title = re.sub(r"^#+\s*", "", title_line).strip()
    if len(title) < 5:
        title = "Новые тренды в искусственном интеллекте"

    slug = slugify(title)

    img_path = generate_image(title, slug)
    save_article(title, text, model, img_path, slug)
    cleanup_old_posts()
    update_gallery(img_path, title)


if __name__ == "__main__":
    main()
