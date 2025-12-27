#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
import time
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
FAL_API_KEY = os.getenv("FAL_API_KEY")  # Обязательно добавить в GitHub Secrets!

FALLBACK_IMAGES = [
    "https://picsum.photos/1200/800?random=1",
    "https://picsum.photos/1200/800?random=2",
    "https://picsum.photos/1200/800?random=3",
    "https://picsum.photos/1200/800?random=4",
    "https://picsum.photos/1200/800?random=5",
]

# -------------------- Шаг 1: Генерация заголовка --------------------
def generate_title(topic):
    groq_model = "llama-3.3-70b-versatile"
    system_prompt = f"""Ты — эксперт по SMM и копирайтингу для блога об ИИ.
    Создай один яркий, кликабельный заголовок на тему '{topic}'.
    Заголовок на русском, 10–15 слов, используй приёмы: цифры, вопросы, "Как", "Почему", "Топ", "2025", "Революция", "Секреты".
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
            logging.error(f"Ошибка генерации заголовка: {e}")
            time.sleep(3)
    raise RuntimeError("Не удалось сгенерировать заголовок")


# -------------------- Шаг 2: Генерация статьи --------------------
def generate_body(title):
    groq_model = "llama-3.3-70b-versatile"
    system_prompt = f"""Напиши полную статью для блога об ИИ по заголовку: "{title}"

Требования:
- На русском языке
- 600–900 слов
- Используй Markdown: ## Введение, ### разделы, #### подразделы
- Структура: Введение → Основная часть → Заключение
- Увлекательно, с примерами, без политики и морали"""

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
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=120)
            r.raise_for_status()
            body = r.json()["choices"][0]["message"]["content"].strip()
            if len(body.split()) > 300:
                return body
        except Exception as e:
            logging.error(f"Ошибка генерации статьи: {e}")
            time.sleep(5)
    raise RuntimeError("Не удалось сгенерировать статью")


# -------------------- Изображение: fal.ai (Flux Schnell) --------------------
def generate_image_fal(title):
    if not FAL_API_KEY:
        logging.warning("FAL_API_KEY отсутствует — используем fallback")
        return None

    url = "https://fal.run/fal-ai/flux/schnell"

    prompt = f"{title}, futuristic artificial intelligence theme, photorealistic, highly detailed, professional photography, cinematic lighting, 8k resolution, vibrant colors"

    payload = {
        "prompt": prompt,
        "image_size": "landscape_16_9",  # 1280×720
        "num_inference_steps": 28,
        "guidance_scale": 7.5,
        "num_images": 1,
        "sync_mode": True
    }

    headers = {
        "Authorization": f"Key {FAL_API_KEY}",
        "Content-Type": "application/json"
    }

    for attempt in range(5):
        try:
            logging.info(f"Генерация изображения через fal.ai Flux (попытка {attempt+1})...")
            r = requests.post(url, json=payload, headers=headers, timeout=120)

            if r.status_code in (402, 403):
                logging.warning("fal.ai: лимит кредитов исчерпан или неверный ключ")
                return None
            if not r.ok:
                logging.warning(f"fal.ai ошибка {r.status_code}: {r.text}")
                time.sleep(5)
                continue

            result = r.json()
            image_url = result["images"][0]["url"]

            img_data = requests.get(image_url, timeout=60)
            if not img_data.ok:
                logging.warning("Не удалось скачать изображение")
                continue

            timestamp = int(time.time())
            img_path = IMAGES_DIR / f"fal-flux-{timestamp}.jpg"
            with open(img_path, "wb") as f:
                f.write(img_data.content)

            logging.info(f"Изображение успешно сгенерировано: {img_path}")
            return str(img_path)

        except Exception as e:
            logging.warning(f"Ошибка fal.ai: {e}")
            time.sleep(10)

    return None


def generate_image(title):
    img = generate_image_fal(title)
    if img:
        return img
    logging.warning("fal.ai не сработал → используем fallback")
    return random.choice(FALLBACK_IMAGES)


# -------------------- Сохранение поста --------------------
def save_post(title, body, img_path=None):
    today = datetime.now().strftime("%Y-%m-%d")
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', title.lower()).strip('-')[:100]
    if len(slug) < 10:
        slug = "ai-post-" + today.replace("-", "")

    filename = POSTS_DIR / f"{today}-{slug}.md"

    content = f"---\ntitle: {title}\ndate: {today}\ncategories: ai\n"

    if img_path and not img_path.startswith('http'):
        rel_path = f"/assets/images/posts/{Path(img_path).name}"
        content += f"image: {rel_path}\n"

    content += "---\n\n"

    if img_path and not img_path.startswith('http'):
        image_name = Path(img_path).name
        content += f"![{title}]({{{{ site.baseurl }}}}/assets/images/posts/{image_name})\n\n"

    content += body

    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

    logging.info(f"Пост сохранён: {filename}")
    return filename


# -------------------- Telegram --------------------
def send_to_telegram(title, body, image_path):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return

    teaser = ' '.join(body.split()[:40]) + '…'
    def esc(text): return re.sub(r'([_*\[\]\(\)~`>#+\-=|{}.!])', r'\\\1', text)

    message = f"*Новая статья в блоге!*\n\n*{esc(title)}*\n\n{esc(teaser)}\n\n[Читать полностью →](https://lybra-ai.ru)\n\n#ИИ #LybraAI #искусственный_интеллект"

    try:
        if image_path.startswith('http'):
            r = requests.get(image_path, timeout=30)
            if not r.ok:
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
                data={"chat_id": TELEGRAM_CHAT_ID, "caption": message, "parse_mode": "MarkdownV2"},
                files={"photo": photo},
                timeout=60
            )

        if image_path.startswith('http'):
            os.unlink(image_file)

        if resp.status_code != 200:
            logging.warning(f"Telegram ошибка: {resp.status_code} {resp.text}")
        else:
            logging.info("Пост отправлен в Telegram")

    except Exception as e:
        logging.warning(f"Ошибка отправки в Telegram: {e}")


# -------------------- MAIN --------------------
def main():
    topics = [
        "ИИ в автоматизации контента",
        "Мультимодальные модели ИИ",
        "Генеративный ИИ в 2025 году",
        "Автономные ИИ-агенты",
        "ИИ в креативных профессиях",
        "Будущее нейросетей и AGI",
        "ИИ и обработка естественного языка"
    ]
    topic = random.choice(topics)
    logging.info(f"Тема дня: {topic}")

    title = generate_title(topic)
    body = generate_body(title)
    img_path = generate_image(title)

    save_post(title, body, img_path)
    send_to_telegram(title, body, img_path)

    logging.info("=== Пост успешно создан и опубликован ===")


if __name__ == "__main__":
    main()
