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

SITE_URL = "https://lybra-ai.ru"

FALLBACK_IMAGES = [
    "https://picsum.photos/1024/768?random=1",
    "https://picsum.photos/1024/768?random=2",
    "https://picsum.photos/1024/768?random=3",
    "https://picsum.photos/1024/768?random=4",
    "https://picsum.photos/1024/768?random=5",
]

# Улучшенный транслит для правильных slug
TRANSLIT_MAP = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
    'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
}

def translit(text):
    text = text.lower()
    result = []
    for c in text:
        result.append(TRANSLIT_MAP.get(c, c))
    return ''.join(result)

# -------------------- Шаг 1: Заголовок --------------------
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
            if r.status_code == 429:
                wait = (2 ** attempt) + random.uniform(0, 1)
                logging.warning(f"Rate limit Groq (429). Ждём {wait:.1f} сек...")
                time.sleep(wait)
                continue
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
            time.sleep(2 ** attempt + random.uniform(0, 1))

    raise RuntimeError("Не удалось сгенерировать валидный заголовок")

# -------------------- Шаг 2: План и разделы --------------------
def generate_outline(title):
    system_prompt = f"""Ты — эксперт по ИИ и технический писатель.
Создай детальный план статьи на русском языке по заголовку: "{title}"

Требования:
- Используй только подзаголовки уровня ## (основные разделы) и ### (подразделы)
- Всего 8–12 основных разделов (##), включая Введение и Заключение
- Под каждым ## может быть 1–3 ###
- План должен обеспечивать объём статьи 3000–5000 слов
- Обязательно включи: примеры, кейсы, сравнения, технические детали, прогнозы

Ответ в чистом Markdown, без лишнего текста."""

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Создай план."}
        ],
        "max_tokens": 2000,
        "temperature": 0.7,
    }

    for attempt in range(5):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=60)
            if r.status_code == 429:
                wait = (2 ** attempt) * 2 + random.uniform(0, 5)
                logging.warning(f"Rate limit при генерации плана. Ждём {wait:.1f} сек...")
                time.sleep(wait)
                continue
            r.raise_for_status()
            outline = r.json()["choices"][0]["message"]["content"].strip()
            logging.info("План статьи сгенерирован")
            return outline
        except Exception as e:
            logging.warning(f"Попытка {attempt+1} генерации плана: {e}")
            time.sleep(5)
    raise RuntimeError("Не удалось сгенерировать план статьи")

def generate_section(title, outline, section_header):
    prompt = f"""Напиши подробный раздел статьи на русском языке.

Заголовок статьи: {title}
Полный план статьи (для контекста):
{outline}

Текущий раздел, который нужно написать:
## {section_header}

Требования:
- Объём: 350–600 слов (обязательно!)
- Формат Markdown
- Подробные объяснения, реальные примеры, кейсы, сравнения
- Доступный язык с техническими деталями
- Если это Введение — 400–600 слов с ярким хуком
- Если это Заключение — 500–700 слов с выводами и прогнозами
- Пиши только содержимое этого раздела!"""

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 4000,
        "temperature": 0.8,
    }

    for attempt in range(6):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=150)
            if r.status_code == 429:
                wait = (2 ** attempt) * 3 + random.uniform(0, 5)
                logging.warning(f"Rate limit (429) для раздела '{section_header}'. Ждём {wait:.1f} сек...")
                time.sleep(wait)
                continue
            r.raise_for_status()
            text = r.json()["choices"][0]["message"]["content"].strip()
            word_count = len(text.split())
            if word_count >= 300:
                return text
            else:
                logging.warning(f"Раздел '{section_header}' короткий ({word_count} слов) — retry")
                time.sleep(3)
        except Exception as e:
            logging.warning(f"Ошибка генерации раздела '{section_header}' (попытка {attempt+1}): {e}")
            time.sleep(3)

    fallback = f"В разделе «{section_header}» рассматриваются ключевые аспекты темы. Генеративный ИИ и обработка естественного языка продолжают развиваться, предлагая новые возможности и вызовы. Детальный анализ временно недоступен из-за технических ограничений."
    return fallback

def generate_body(title):
    logging.info("Генерация плана статьи...")
    outline = generate_outline(title)

    # Извлекаем только основные разделы (##)
    section_headers = []
    for line in outline.split("\n"):
        line = line.strip()
        if re.match(r'^##\s+', line):
            header = re.sub(r'^##\s*', '', line).strip()
            if header:
                section_headers.append(header)

    if len(section_headers) < 8:
        section_headers = [
            "Введение",
            "История развития",
            "Ключевые технологии",
            "Современные модели",
            "Примеры применения",
            "Проблемы и ограничения",
            "Этические аспекты",
            "Будущее и прогнозы",
            "Заключение"
        ]

    MAX_SECTIONS = 12
    section_headers = section_headers[:MAX_SECTIONS]
    
    logging.info(f"Будет сгенерировано {len(section_headers)} разделов (макс. {MAX_SECTIONS})")

    full_body = f"# {title}\n\n"
    total_words = 0

    for i, header in enumerate(section_headers, 1):
        logging.info(f"Генерация раздела {i}/{len(section_headers)}: {header}")
        section_text = generate_section(title, outline, header)
        full_body += f"\n## {header}\n\n{section_text}\n\n"
        words = len(section_text.split())
        total_words += words
        logging.info(f"Раздел готов ({words} слов, всего: {total_words})")

        if i < len(section_headers):
            time.sleep(random.uniform(3, 6))

    logging.info(f"Статья полностью сгенерирована ({total_words} слов)")
    return full_body

# -------------------- Изображение: Dezgo API (бесплатно, без ключа) --------------------
def generate_image_dezgo(title):
    prompt = f"{title}, futuristic artificial intelligence, neural networks, cyberpunk aesthetic, photorealistic, highly detailed, cinematic lighting, vibrant neon colors, masterpiece, best quality"

    url = "https://dezgo.com/api/text2image"
    payload = {
        "prompt": prompt,
        "negative_prompt": "blurry, low quality, deformed, ugly, text, watermark",
        "model": "flux_1_dev",  # Лучшее качество (Flux)
        "guidance": 7.5,
        "steps": 28,
        "sampler": "euler_a",
        "width": 768,
        "height": 512,
        "seed": -1
    }

    try:
        logging.info("Генерация изображения через Dezgo API...")
        r = requests.post(url, data=payload, timeout=180)
        if not r.ok:
            logging.warning(f"Dezgo ошибка: {r.status_code} {r.text}")
            return None

        data = r.json()
        img_url = data.get("image")
        if not img_url:
            logging.warning("Dezgo не вернул URL изображения")
            return None

        img_data = requests.get(img_url, timeout=60)
        if not img_data.ok:
            logging.warning("Не удалось скачать изображение от Dezgo")
            return None

        filename = f"dezgo-{int(time.time())}.jpg"
        img_path = IMAGES_DIR / filename
        img_path.write_bytes(img_data.content)
        logging.info(f"Изображение от Dezgo сохранено: {img_path}")
        return str(img_path)

    except Exception as e:
        logging.warning(f"Ошибка Dezgo: {e}")
        return None

def generate_image(title):
    local_path = generate_image_dezgo(title)
    if local_path and os.path.exists(local_path):
        return local_path

    fallback_url = random.choice(FALLBACK_IMAGES)
    logging.warning(f"Dezgo не сработал → fallback на picsum: {fallback_url}")
    return fallback_url

# -------------------- Сохранение поста --------------------
def save_post(title, body, img_path=None):
    today = datetime.now().strftime("%Y-%m-%d")
    slug = re.sub(r'[^a-z0-9-]+', '-', translit(title)).strip('-')[:80]
    if len(slug) < 10:
        slug = "ai-news-" + ''.join(random.choices("abcdefghijklmnopqrstuvwxyz", k=10))

    filename = POSTS_DIR / f"{today}-{slug}.md"

    frontmatter = f"---\ntitle: {title}\ndate: {today}\ncategories: ai\n"

    if img_path:
        if img_path.startswith("http"):
            frontmatter += f"image: {img_path}\n"
        else:
            rel_path = f"/assets/images/posts/{Path(img_path).name}"
            frontmatter += f"image: {rel_path}\n"

    frontmatter += "---\n\n"

    # Всегда добавляем картинку в тело поста
    frontmatter += f"![Обложка: {title}]({img_path if img_path else '/assets/images/placeholder.jpg'})\n\n"

    full_content = frontmatter + body
    filename.write_text(full_content, encoding="utf-8")

    article_url = f"{SITE_URL}/{slug}/"
    logging.info(f"Пост сохранён: {filename}")
    logging.info(f"Ссылка на статью: {article_url}")

    return str(filename), article_url

# -------------------- Telegram --------------------
def send_to_telegram(title, teaser_text, image_path, article_url):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logging.warning("Telegram токен или чат не указаны — пропуск")
        return

    if len(teaser_text) > 800:
        teaser_text = teaser_text[:800] + "…"

    caption = f"<b>Новая статья в блоге!</b>\n\n" \
              f"<b>{title}</b>\n\n" \
              f"{teaser_text}\n\n" \
              f"<i>Читать полностью:</i> {article_url}"

    try:
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
                    "disable_web_page_preview": False
                },
                files={"photo": photo},
                timeout=60
            )

        if image_path.startswith("http"):
            os.unlink(photo_path_local)

        if resp.ok:
            logging.info("Пост успешно отправлен в Telegram с изображением и тизером!")
        else:
            logging.warning(f"Ошибка Telegram: {resp.status_code} {resp.text}")
    except Exception as e:
        logging.error(f"Ошибка отправки в Telegram: {e}")

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

        _, article_url = save_post(title, body, img_path)

        teaser = " ".join(body.split()[:50]) + "…"
        send_to_telegram(title, teaser, img_path, article_url)

        logging.info("=== Пост полностью создан, сохранён и опубликован в Telegram ===")

    except Exception as e:
        logging.error(f"Критическая ошибка в main: {e}", exc_info=True)

if __name__ == "__main__":
    main()
