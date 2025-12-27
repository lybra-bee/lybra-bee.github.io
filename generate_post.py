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
from playwright.sync_api import sync_playwright

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

# Нет нужды в ключе для Puter.js!

FALLBACK_IMAGES = [
    "https://picsum.photos/1200/800?random=50",
    "https://picsum.photos/1200/800?random=51",
    "https://picsum.photos/1200/800?random=52",
    "https://picsum.photos/1200/800?random=53",
    "https://picsum.photos/1200/800?random=54",
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


# -------------------- Изображение: Puter.js + FLUX.1-schnell --------------------
def generate_image_puter(title):
    prompt = f"{title}, futuristic artificial intelligence, neural networks, cyberpunk aesthetic, photorealistic, highly detailed, cinematic lighting, vibrant neon colors, 8k resolution"

    html_code = f"""
    <html>
      <head>
        <script src="https://js.puter.com/v2/"></script>
      </head>
      <body>
        <script>
          puter.ai.txt2img("{prompt}", {{ 
            model: "black-forest-labs/FLUX.1-schnell"
          }}).then(img => {{
            document.body.appendChild(img);
          }});
        </script>
      </body>
    </html>
    """

    for attempt in range(5):
        try:
            logging.info(f"Генерация через Puter.js FLUX (попытка {attempt+1})...")
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.set_content(html_code, wait_until="networkidle")
                page.wait_for_selector("img", timeout=90000)  # Увеличил до 90 сек — генерация может занять время
                
                img_src = page.eval_on_selector("img", "el => el.src")
                
                if not img_src or not img_src.startswith("http"):
                    raise Exception("Нет валидного URL изображения")
                
                img_data = requests.get(img_src, timeout=60)
                if not img_data.ok:
                    raise Exception("Не удалось скачать изображение")
                
                timestamp = int(time.time())
                img_path = IMAGES_DIR / f"puter-flux-{timestamp}.jpg"
                with open(img_path, "wb") as f:
                    f.write(img_data.content)
                
                browser.close()
                logging.info(f"Изображение успешно сгенерировано: {img_path}")
                return str(img_path)

        except Exception as e:
            logging.warning(f"Ошибка Puter.js (попытка {attempt+1}): {e}")
            time.sleep(15)

    return None


def generate_image(title):
    img = generate_image_puter(title)
    if img:
        return img
    logging.warning("Puter.js не сработал → используем fallback (picsum)")
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

    def esc(text):
        return re.sub(r'([_*\[\]\(\)~`>#+\-=|{}.!])', r'\\\1', text)

    message = f"*Новая статья в блоге\\!*\n\n*{esc(title)}*\n\n{esc(teaser)}\n\n[Читать полностью →](https://lybra-ai.ru)\n\n#ИИ #LybraAI #искусственный_интеллект"

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
            logging
