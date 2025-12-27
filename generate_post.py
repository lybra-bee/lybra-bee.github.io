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

FALLBACK_IMAGES = [
    "https://picsum.photos/1200/800?random=40",
    "https://picsum.photos/1200/800?random=41",
    "https://picsum.photos/1200/800?random=42",
    "https://picsum.photos/1200/800?random=43",
    "https://picsum.photos/1200/800?random=44",
]

# -------------------- Генерация заголовка и статьи (без изменений) --------------------
# (функции generate_title и generate_body — копируйте из предыдущей версии, они работают)

# -------------------- Изображение: Puter.js + FLUX.1-schnell --------------------
def generate_image_puter(title):
    prompt = f"{title}, futuristic artificial intelligence, neural networks, cyberpunk aesthetic, photorealistic, highly detailed, cinematic lighting, vibrant neon colors, 8k resolution"

    html_code = f"""
    <html>
    <body>
    <script src="https://js.puter.com/v2/"></script>
    <script>
    puter.ai.txt2img("{prompt}", {{ 
        model: "black-forest-labs/FLUX.1-schnell",
        disable_safety_checker: true 
    }}).then(img => {{
        document.body.appendChild(img);
    }});
    </script>
    </body>
    </html>
    """

    for attempt in range(5):
        try:
            logging.info(f"Генерация изображения через Puter.js FLUX (попытка {attempt+1})...")
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.set_content(html_code)
                page.wait_for_selector("img", timeout=60000)  # Ждём до 60 сек появления изображения
                
                img_element = page.query_selector("img")
                if not img_element:
                    raise Exception("Изображение не появилось")
                
                img_src = page.eval_on_selector("img", "el => el.src")
                
                if not img_src.startswith("http"):
                    raise Exception("Нет валидного URL изображения")
                
                img_data = requests.get(img_src, timeout=60)
                if not img_data.ok:
                    raise Exception("Не удалось скачать изображение")
                
                timestamp = int(time.time())
                img_path = IMAGES_DIR / f"puter-flux-{timestamp}.jpg"
                with open(img_path, "wb") as f:
                    f.write(img_data.content)
                
                browser.close()
                
                logging.info(f"Изображение успешно сгенерировано через Puter.js: {img_path}")
                return str(img_path)

        except Exception as e:
            logging.warning(f"Ошибка Puter.js (попытка {attempt+1}): {e}")
            time.sleep(10)

    return None


def generate_image(title):
    img = generate_image_puter(title)
    if img:
        return img
    logging.warning("Puter.js не сработал → используем fallback (picsum)")
    return random.choice(FALLBACK_IMAGES)


# -------------------- Остальные функции: save_post, send_to_telegram, main --------------------
# (копируйте из последней рабочей версии — с исправленным экранированием ! в Telegram)

if __name__ == "__main__":
    main()
