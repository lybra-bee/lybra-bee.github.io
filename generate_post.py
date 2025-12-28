#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import time
import random
import logging
import requests
import tempfile
from datetime import datetime
from pathlib import Path

# ==================== ИСПРАВЛЕНИЕ ГЛАВНОЙ ОШИБКИ ====================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# -------------------- Папки --------------------
POSTS_DIR = Path("_posts")
IMAGES_DIR = Path("assets/images/posts")
POSTS_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# -------------------- API ключи --------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
AIHORDE_API_KEY = os.getenv("AIHORDE_API_KEY", "0000000000")

SITE_URL = "https://lybra-ai.ru"  # Твой реальный домен

if AIHORDE_API_KEY == "0000000000":
    logging.warning("AI Horde в анонимном режиме — fallback на случайные изображения сразу")
    USE_AI_HORDE = False
else:
    logging.info("Используется персональный AIHORDE_API_KEY")
    USE_AI_HORDE = True

FALLBACK_IMAGES = [
    "https://picsum.photos/1024/768?random=1",
    "https://picsum.photos/1024/768?random=2",
    "https://picsum.photos/1024/768?random=3",
    "https://picsum.photos/1024/768?random=4",
    "https://picsum.photos/1024/768?random=5",
]

# Ручной транслит для slug (простой mapping)
TRANSLIT_MAP = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch', 'ъ': '',
    'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
}

def translit(text):
    return ''.join(TRANSLIT_MAP.get(c, c) for c in text.lower())

# -------------------- Шаг 1: Генерация заголовка --------------------
def generate_title(topic):
    groq_model = "llama-3.3-70b-versatile"
    system_prompt = f"""Ты — эксперт по SMM и копирайтингу для блога об ИИ.
Создай один яркий, кликабельный заголовок на русском языке на тему '{topic}'.
Длина: 10–15 слов. Используй приёмы: цифры, вопросы, "Как", "Почему", "Топ", "2025", "Революция", "Секреты".
Ответ строго в формате: ЗАГОЛОВОК: [твой заголовок]"""

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    payload = {
        "model": groq_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Создай заголовок."}
        ],
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
                    logging.info(f"Сгенерирован заголовок: {title}")
                    return title
        except Exception as e:
            logging.error(f"Попытка {attempt+1}/7 генерации заголовка: {e}")
            time.sleep(2 ** attempt)  # Exponential backoff

    raise RuntimeError("Не удалось сгенерировать валидный заголовок после 7 попыток")

# -------------------- Шаг 2: Генерация статьи --------------------
def generate_body(title):
    groq_model = "llama-3.3-70b-versatile"
    system_prompt = f"""Напиши полную статью для блога об ИИ по точному заголовку: "{title}"

Требования:
- Только на русском языке
- 2000–3000 слов (обязательно достигни этого: добавь детальные примеры, кейсы, сравнения, списки преимуществ/недостатков, будущие тенденции)
- Формат Markdown: ## Введение, ### Подразделы с деталями, #### Примеры, списки, таблицы, код (если релевантно, например Python для ИИ)
- Структура: Введение (200-300 слов) → Основная часть с 5-7 разделами и подпримерами (1500-2000 слов) → Заключение с рекомендациями (300-500 слов)
- Увлекательно, доступно, с практическими советами, без политики и нравоучений"""

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    payload = {
        "model": groq_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Напиши полную статью."}
        ],
        "max_tokens": 12000,
        "temperature": 0.85,
    }

    for attempt in range(5):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=300)  # Увеличил timeout для длинной генерации
            r.raise_for_status()
            body = r.json()["choices"][0]["message"]["content"].strip()
            word_count = len(body.split())
            if word_count > 1500:  # Минимальный порог для 2000+
                logging.info(f"Статья сгенерирована ({word_count} слов)")
                return body
            else:
                logging.warning(f"Статья слишком короткая ({word_count} слов) — retry")
        except Exception as e:
            logging.error(f"Попытка {attempt+1}/5 генерации статьи: {e}")
            time.sleep(2 ** attempt)  # Exponential backoff

    raise RuntimeError("Не удалось сгенерировать статью достаточной длины")

# -------------------- Изображение: AI Horde + fallback --------------------
def generate_image_horde(title):
    prompt = f"{title}, futuristic artificial intelligence, neural networks, cyberpunk aesthetic, photorealistic, highly detailed, cinematic lighting, vibrant neon colors, masterpiece, best quality"

    url_async = "https://stablehorde.net/api/v2/generate/async"
    payload = {
        "prompt": prompt,
        "models": ["FLUX.1 [schnell]", "Flux.1 Dev", "SDXL 1.0"],
        "params": {
            "width": 512,  # Уменьшил для лимитов
            "height": 512,
            "steps": 15,
            "cfg_scale": 7.0,
            "n": 1
        },
        "nsfw": False,
        "trusted_workers": True,
        "slow_workers": False
    }

    headers = {
        "apikey": AIHORDE_API_KEY,
        "Content-Type": "application/json",
        "Client-Agent": "LybraBlogBot:1.0:contact@example.com"
    }

    try:
        r = requests.post(url_async, json=payload, headers=headers, timeout=60)
        if not r.ok:
            logging.warning(f"AI Horde ошибка отправки: {r.status_code} {r.text}")
            return None

        job_id = r.json().get("id")
        if not job_id:
            return None

        logging.info(f"AI Horde задача создана: {job_id}")

        check_url = f"https://stablehorde.net/api/v2/generate/check/{job_id}"
        status_url = f"https://stablehorde.net/api/v2/generate/status/{job_id}"

        for _ in range(30):  # Уменьшил итерации
            time.sleep(5)  # Короткий sleep
            check = requests.get(check_url, headers=headers).json()
            if check.get("done"):
                final = requests.get(status_url, headers=headers).json()
                if final.get("generations"):
                    img_url = final["generations"][0]["img"]
                    img_data = requests.get(img_url, timeout=60)
                    if img_data.ok:
                        filename = f"horde-{int(time.time())}.jpg"
                        img_path = IMAGES_DIR / filename
                        img_path.write_bytes(img_data.content)
                        logging.info(f"Изображение сохранено: {img_path}")
                        return str(img_path)
            logging.info(f"Ожидание... очередь: {check.get('queue_position', '?')}, время: {check.get('wait_time', '?')}s")

    except Exception as e:
        logging.warning(f"Ошибка AI Horde: {e}")

    return None

def generate_image(title):
    if not USE_AI_HORDE:
        fallback_url = random.choice(FALLBACK_IMAGES)
        logging.warning("Анонимный режим — прямой fallback")
        return fallback_url

    local_path = generate_image_horde(title)
    if local_path and os.path.exists(local_path):
        return local_path

    fallback_url = random.choice(FALLBACK_IMAGES)
    logging.warning(f"AI Horde не сработал → fallback: {fallback_url}")
    return fallback_url

# -------------------- Сохранение поста --------------------
def save_post(title, body, img_path=None):
    today = datetime.now().strftime("%Y-%m-%d")
    slug = re.sub(r'[^a-z0-9-]+', '-', translit(title)).strip('-')[:80]
    if len(slug) < 10:
        slug = "ai-news-" + ''.join(random.choices("abcdefghijklmnopqrstuvwxyz", k=10))

    filename = POSTS_DIR / f"{today}-{slug}.md"

    frontmatter = f"---\ntitle: {title}\ndate: {today}\ncategories: ai\n"

    if img_path and not img_path.startswith("http"):
        rel_path = f"/assets/images/posts/{Path(img_path).name}"
        frontmatter += f"image: {rel_path}\n"

    frontmatter += "---\n\n"

    if img_path and not img_path.startswith("http"):
        img_name = Path(img_path).name
        frontmatter += f"![Обложка: {title}]({{{{ site.baseurl }}}}/assets/images/posts/{img_name})\n\n"

    full_content = frontmatter + body

    filename.write_text(full_content, encoding="utf-8")
    article_url = f"{SITE_URL}/{slug}/"
    logging.info(f"Пост сохранён: {filename}")
    logging.info(f"Ссылка на статью: {article_url}")

    return str(filename), article_url

# -------------------- Telegram: КРАСИВЫЙ ТИЗЕР --------------------
def send_to_telegram(title, teaser_text, image_path, article_url):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logging.warning("Telegram токен или чат не указаны — пропуск отправки")
        return

    # Обрезаем teaser если слишком длинный (Telegram caption max 1024 chars)
    if len(teaser_text) > 800:
        teaser_text = teaser_text[:800] + "…"

    # Важно: ссылка в КОНЦЕ подписи → Telegram покажет тизер сайта
    caption = f"<b>Новая статья в блоге!</b>\n\n" \
              f"<b>{title}</b>\n\n" \
              f"{teaser_text}\n\n" \
              f"<i>Читать полностью:</i> {article_url}"

    try:
        # Подготавливаем фото
        if image_path.startswith("http"):
            photo_data = requests.get(image_path, timeout=30).content
            photo_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            photo_file.write(photo_data)
            photo_file.close()
            photo_path_local = photo_file.name
        else:
            photo_path_local = image_path

        with open(photo_path_local, "rb") as photo:
            resp = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto",
                data={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "caption": caption,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": False  # Явно включаем превью
                },
                files={"photo": photo},
                timeout=60
            )

        # Удаляем временный файл
        if image_path.startswith("http"):
            os.unlink(photo_path_local)

        if resp.status_code == 200:
            logging.info("Пост успешно отправлен в Telegram с изображением и тизером!")
        else:
            logging.warning(f"Ошибка Telegram: {resp.status_code} {resp.text}")

    except Exception as e:
        logging.error(f"Критическая ошибка отправки в Telegram: {e}")

# -------------------- MAIN --------------------
def main():
    try:
        topics = [
            "ИИ в автоматизации контента",
            "Мультимодальные модели ИИ",
            "Генеративный ИИ в 2025 году",
            "Автономные ИИ-агенты",
            "ИИ в креативных профессиях",
            "Будущее нейросетей и AGI",
            "ИИ и обработка естественного языка",
            "Этичные вопросы ИИ",
            "ИИ в медицине и науке"
        ]
        topic = random.choice(topics)
        logging.info(f"Выбрана тема: {topic}")

        title = generate_title(topic)
        body = generate_body(title)
        img_path = generate_image(title)

        post_file, article_url = save_post(title, body, img_path)

        # Тизер — первые 50 слов статьи
        teaser = " ".join(body.split()[:50]) + "…"

        send_to_telegram(title, teaser, img_path, article_url)

        logging.info("=== Пост полностью создан, сохранён и опубликован в Telegram ===")

    except Exception as e:
        logging.error(f"Критическая ошибка в main: {e}", exc_info=True)

if __name__ == "__main__":
    main()
