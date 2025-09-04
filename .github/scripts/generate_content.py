import os
import requests
import base64
import time
import logging
from datetime import datetime
from pathlib import Path
import random
import string
from PIL import Image, ImageDraw, ImageFont

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# ==========================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ==========================

def slugify(value: str) -> str:
    """Убираем спецсимволы для имени файла"""
    return "".join(c if c.isalnum() else "-" for c in value).strip("-").lower()


def save_image_bytes(image_bytes, title):
    """Сохраняем изображение из байтов"""
    images_dir = Path("assets/images/posts")
    images_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{datetime.now().strftime('%Y-%m-%d')}-{slugify(title)}.png"
    filepath = images_dir / filename

    with open(filepath, "wb") as f:
        f.write(image_bytes)

    logger.info(f"✅ Сохранено изображение: {filepath}")
    return str(filepath)


def save_article(title, content, image_path):
    """Сохраняем статью в content/posts"""
    posts_dir = Path("content/posts")
    posts_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{datetime.now().strftime('%Y-%m-%d')}-{slugify(title)}.md"
    filepath = posts_dir / filename

    front_matter = f"""---
title: "{title}"
date: {datetime.now().strftime('%Y-%m-%d')}
image: /{image_path}
draft: false
---

"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(front_matter + content)

    logger.info(f"✅ Статья создана: {filepath}")


# ==========================
# PLACEHOLDER IMAGE
# ==========================

def generate_enhanced_placeholder(title):
    """Создание placeholder-картинки"""
    images_dir = Path("assets/images/posts")
    images_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{datetime.now().strftime('%Y-%m-%d')}-{slugify(title)}.png"
    filepath = images_dir / filename

    img = Image.new("RGB", (800, 400), color=(200, 200, 200))
    draw = ImageDraw.Draw(img)

    text = "No Image Available"
    font = ImageFont.load_default()
    text_w, text_h = draw.textsize(text, font=font)
    draw.text(((800 - text_w) / 2, (400 - text_h) / 2), text, fill=(50, 50, 50), font=font)

    img.save(filepath)
    logger.info(f"🎨 Создан placeholder: {filepath}")
    return str(filepath)


# ==========================
# FUSIONBRAIN API
# ==========================

class FusionBrainAPI:
    def __init__(self, api_key, secret_key):
        self.api_key = api_key
        self.secret_key = secret_key
        self.url = "https://api.fusionbrain.ai"

    def generate(self, prompt, width=512, height=512):
        headers = {
            "X-Key": f"Key {self.api_key}",
            "X-Secret": f"Secret {self.secret_key}",
        }
        data = {
            "type": "GENERATE",
            "width": width,
            "height": height,
            "num_images": 1,
            "prompt": prompt,
        }
        r = requests.post(f"{self.url}/key/api/v1/text2image/run", headers=headers, json=data)
        if r.status_code == 201:
            task_id = r.json()["uuid"]
            return task_id
        else:
            logger.warning(f"⚠️ Ошибка генерации FusionBrain: {r.status_code} - {r.text}")
            return None

    def check_status(self, task_id, attempts=40, delay=3):
        headers = {
            "X-Key": f"Key {self.api_key}",
            "X-Secret": f"Secret {self.secret_key}",
        }
        for i in range(attempts):
            r = requests.get(f"{self.url}/key/api/v1/text2image/status/{task_id}", headers=headers)
            if r.status_code == 200:
                status = r.json().get("status")
                if status == "DONE":
                    return r.json()["images"][0]
                elif status == "FAIL":
                    logger.warning("⚠️ FusionBrain: задание не удалось")
                    return None
                else:
                    time.sleep(delay)
            else:
                logger.warning(f"⚠️ Ошибка статуса FusionBrain: {r.status_code} - {r.text}")
                return None
        return None

    def generate_and_wait(self, prompt, width=512, height=512, attempts=40, delay=3):
        """Создание задачи и ожидание результата"""
        task_id = self.generate(prompt, width, height)
        if not task_id:
            return None
        logger.info(f"⏳ Ожидание генерации FusionBrain, task_id: {task_id}")
        return self.check_status(task_id, attempts=attempts, delay=delay)


def try_fusionbrain_api(title):
    """FusionBrain API с ожиданием результата"""
    api_key = os.getenv("FUSIONBRAIN_API_KEY")
    secret_key = os.getenv("FUSION_SECRET_KEY")

    if not api_key or not secret_key:
        logger.warning("⚠️ FusionBrain ключи не найдены")
        return None

    try:
        fb_api = FusionBrainAPI(api_key, secret_key)
        english_prompt = f"{title}, digital art, futuristic technology, AI, 2025, professional, high quality"
        logger.info(f"🎨 Генерация через FusionBrain: {english_prompt}")

        image_base64 = fb_api.generate_and_wait(english_prompt)
        if image_base64:
            image_data = base64.b64decode(image_base64)
            return save_image_bytes(image_data, title)
        else:
            logger.warning("⚠️ Генерация FusionBrain не завершилась успешно")
    except Exception as e:
        logger.error(f"❌ Ошибка FusionBrain: {e}")
    return None


# ==========================
# CRAIYON API
# ==========================

def try_craiyon_api(title):
    try:
        english_prompt = f"{title}, digital art, futuristic technology, AI, 2025, professional"
        logger.info(f"🎨 Генерация через Craiyon: {english_prompt}")
        r = requests.post("https://backend.craiyon.com/generate", json={"prompt": english_prompt})
        if r.status_code == 200:
            image_base64 = r.json()["images"][0]
            image_data = base64.b64decode(image_base64)
            return save_image_bytes(image_data, title)
        else:
            logger.warning(f"⚠️ Ошибка Craiyon API: {r.status_code}")
    except Exception as e:
        logger.error(f"❌ Ошибка Craiyon: {e}")
    return None


# ==========================
# LEXICA API
# ==========================

def try_lexica_art_api(title):
    try:
        logger.info("🔄 Пробуем метод: try_lexica_art_api")
        query = f"{title}, futuristic digital art, AI, professional"
        r = requests.get(f"https://lexica.art/api/v1/search?q={query}")
        if r.status_code == 200:
            data = r.json()
            if "images" in data and len(data["images"]) > 0:
                img_url = data["images"][0]["src"]
                img_data = requests.get(img_url).content
                return save_image_bytes(img_data, title)
        else:
            logger.warning(f"⚠️ Ошибка Lexica API: {r.status_code}")
    except Exception as e:
        logger.error(f"❌ Ошибка Lexica: {e}")
    return None


# ==========================
# ОСНОВНОЙ PIPELINE
# ==========================

def generate_content(title, content):
    logger.info(f"📌 Извлеченный заголовок: {title}")
    logger.info(f"🎨 Генерация изображения для: {title}")

    image_path = None
    for method in [try_fusionbrain_api, try_craiyon_api, try_lexica_art_api]:
        image_path = method(title)
        if image_path:
            break

    if not image_path:
        logger.info("🔄 Пробуем метод: generate_enhanced_placeholder")
        image_path = generate_enhanced_placeholder(title)

    save_article(title, content, image_path)


# ==========================
# ЗАПУСК
# ==========================

if __name__ == "__main__":
    logger.info("🚀 Запуск генератора контента...")
    # Здесь можно подключить свою генерацию текста статьи
    test_title = "Этичный искусственный интеллект в финансовые технологии и финтех в 2025 году"
    test_content = "Тестовый контент статьи..."
    generate_content(test_title, test_content)
