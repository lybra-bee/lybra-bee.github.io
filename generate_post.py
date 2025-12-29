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

# Изменение: Увеличена длина ожидания для Horde (range до 200, sleep до 10 сек), чтобы дождаться очереди даже от 170+.
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

# Улучшенный транслит
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

# -------------------- Шаг 1: Разнообразный заголовок --------------------
def generate_title(topic):
    groq_model = "llama-3.3-70b-versatile"
    system_prompt = f"""Ты — профессиональный копирайтер и SMM-специалист для блога об искусственном интеллекте.
Создай ОДИН очень привлекательный, эмоциональный и кликабельный заголовок на русском языке по теме: "{topic}"

Правила:
- Длина: 8–16 слов
- Запрещено начинать с "Топ 5", "Топ 10", "5 секретов", "Топ секретов" и подобных шаблонов
- Используй мощные приёмы:
  • Вопросы ("Почему все говорят о...", "Что будет, если...")
  • Интрига и парадоксы ("ИИ, который пугает экспертов")
  • Будущее ("Что ждёт нас в 2026 году")
  • Драма ("Революция, которую никто не заметил")
  • "Как...", "Когда...", "Почему..."
- Включи год 2025 или 2026, если уместно
- Заголовок должен вызывать желание кликнуть немедленно
- Делай его живым, современным и естественным

Ответ строго: ЗАГОЛОВОК: [твой заголовок]"""

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    payload = {
        "model": groq_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Придумай лучший заголовок."}
        ],
        "max_tokens": 120,
        "temperature": 1.1,
    }

    for attempt in range(10):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=60)
            if r.status_code == 429:
                wait = (2 ** attempt) + random.uniform(0, 1)
                logging.warning(f"Rate limit Groq (429). Ждём {wait:.1f} сек...")
                time.sleep(wait)
                continue
            r.raise_for_status()
            text = r.json()["choices"][0]["message"]["content"].strip()
            match = re.search(r"ЗАГОЛОВОК:\s*(.+)", text, re.IGNORECASE | re.DOTALL)
            if match:
                title = match.group(1).strip().strip('"').strip("'").strip()
                if not re.search(r'^(топ|5|10|\d+)\s', title.lower()):
                    if 8 <= len(title.split()) <= 16:
                        logging.info(f"Сгенерирован заголовок: {title}")
                        return title
            logging.warning(f"Заголовок не прошёл фильтр — retry ({attempt+1}/10)")
        except Exception as e:
            logging.error(f"Ошибка генерации заголовка: {e}")
            time.sleep(2)

    fallbacks = [
        f"Почему {topic.lower()} меняет всё в 2025 году",
        f"ИИ переходит на новый уровень: эра {topic.lower()} началась",
        f"Что скрывают новые разработки в {topic.lower()}",
        f"2026 год начинается сейчас: прорыв в {topic.lower()}",
        f"Как {topic.lower()} уже влияет на нашу жизнь"
    ]
    title = random.choice(fallbacks)
    logging.info(f"Использован fallback-заголовок: {title}")
    return title

# -------------------- Шаг 2: План и тело статьи (теперь 3000–5000 знаков) --------------------
# Изменение: Промпты обновлены на "знаков" вместо "слов". Подсчёт total_chars = len(text) вместо слов.
# Уменьшены объёмы разделов для общей 3000–5000 знаков (примерно 500–800 слов, но по знакам).
def generate_outline(title):
    system_prompt = f"""Ты — эксперт по ИИ и технический писатель.
Создай детальный план статьи на русском языке по заголовку: "{title}"

Требования:
- Только подзаголовки ## (основные разделы) и ### (подразделы)
- 8–12 основных разделов (##), включая Введение и Заключение
- Под каждым ## — 1–3 ###
- Общий объём статьи должен быть 3000–5000 знаков
- Включи: примеры, кейсы, сравнения, технические детали, прогнозы

Ответ в чистом Markdown."""

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
                logging.warning(f"Rate limit. Ждём {wait:.1f} сек...")
                time.sleep(wait)
                continue
            r.raise_for_status()
            outline = r.json()["choices"][0]["message"]["content"].strip()
            logging.info("План статьи сгенерирован")
            return outline
        except Exception as e:
            logging.warning(f"Попытка {attempt+1} генерации плана: {e}")
            time.sleep(5)
    raise RuntimeError("Не удалось сгенерировать план")

def generate_section(title, outline, section_header):
    prompt = f"""Напиши подробный раздел статьи на русском языке.

Заголовок статьи: {title}
Полный план (для контекста):
{outline}

Текущий раздел:
## {section_header}

Требования:
- Объём: 300–600 знаков (обязательно!)
- Формат Markdown
- Подробные объяснения, примеры, кейсы, сравнения
- Доступный язык с техническими деталями
- Введение: 400–600 знаков с хуком
- Заключение: 500–700 знаков с выводами
- Только этот раздел!"""

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 400,
        "temperature": 0.8,
    }

    for attempt in range(6):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=150)
            if r.status_code == 429:
                wait = (2 ** attempt) * 3 + random.uniform(0, 5)
                logging.warning(f"Rate limit для '{section_header}'. Ждём {wait:.1f} сек...")
                time.sleep(wait)
                continue
            r.raise_for_status()
            text = r.json()["choices"][0]["message"]["content"].strip()
            char_count = len(text)
            if char_count >= 250:
                return text
            logging.warning(f"Раздел '{section_header}' короткий ({char_count} знаков) — retry")
            time.sleep(3)
        except Exception as e:
            logging.warning(f"Ошибка раздела '{section_header}': {e}")
            time.sleep(3)

    return f"В разделе «{section_header}» рассматриваются ключевые аспекты. Детальный анализ временно недоступен."

def generate_body(title):
    logging.info("Генерация плана статьи...")
    outline = generate_outline(title)

    section_headers = []
    for line in outline.split("\n"):
        line = line.strip()
        if re.match(r'^##\s+', line):
            header = re.sub(r'^##\s*', '', line).strip()
            if header:
                section_headers.append(header)

    if len(section_headers) < 8:
        section_headers = ["Введение", "История", "Технологии", "Модели", "Применение", "Проблемы", "Этика", "Будущее", "Заключение"]

    section_headers = section_headers[:12]
    logging.info(f"Будет сгенерировано {len(section_headers)} разделов")

    full_body = f"# {title}\n\n"
    total_chars = 0

    for i, header in enumerate(section_headers, 1):
        logging.info(f"Генерация раздела {i}/{len(section_headers)}: {header}")
        section_text = generate_section(title, outline, header)
        full_body += f"\n## {header}\n\n{section_text}\n\n"
        chars = len(section_text)
        total_chars += chars
        logging.info(f"Раздел готов ({chars} знаков, всего: {total_chars})")
        if i < len(section_headers):
            time.sleep(random.uniform(3, 6))

    logging.info(f"Статья полностью сгенерирована ({total_chars} знаков)")
    return full_body

# -------------------- Изображение: Stable Horde анонимный --------------------
# Изменение: Увеличен range до 200 (до ~30 мин ожидания), sleep до 10 сек, чтобы дождаться даже из очереди 170+.
def generate_image_horde(title):
    prompt = f"{title}, futuristic artificial intelligence, neural networks, cyberpunk aesthetic, photorealistic, highly detailed, cinematic lighting, vibrant neon colors, masterpiece, best quality"

    url_async = "https://stablehorde.net/api/v2/generate/async"
    payload = {
        "prompt": prompt,
        "models": ["FLUX.1 [schnell]", "SDXL 1.0"],
        "params": {
            "width": 512,
            "height": 512,
            "steps": 10,
            "cfg_scale": 7.0,
            "n": 1
        },
        "nsfw": False,
        "trusted_workers": False,
        "slow_workers": True
    }

    headers = {
        "apikey": "0000000000",
        "Content-Type": "application/json",
        "Client-Agent": "LybraBlogBot:1.0"
    }

    try:
        r = requests.post(url_async, json=payload, headers=headers, timeout=60)
        if not r.ok:
            logging.warning(f"Horde ошибка отправки: {r.status_code} {r.text}")
            return None

        job_id = r.json().get("id")
        if not job_id:
            return None

        logging.info(f"Horde задача создана: {job_id}")

        check_url = f"https://stablehorde.net/api/v2/generate/check/{job_id}"
        status_url = f"https://stablehorde.net/api/v2/generate/status/{job_id}"

        for _ in range(200):
            time.sleep(10)
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
                        logging.info(f"Изображение от Horde сохранено: {img_path}")
                        return str(img_path)
            queue = check.get("queue_position", "?")
            logging.info(f"Horde ожидание... позиция: {queue}")

    except Exception as e:
        logging.warning(f"Ошибка Horde: {e}")

    return None

def generate_image(title):
    local_path = generate_image_horde(title)
    if local_path and os.path.exists(local_path):
        return local_path

    fallback_url = random.choice(FALLBACK_IMAGES)
    logging.warning(f"Horde не сработал → fallback: {fallback_url}")
    return fallback_url

# -------------------- Сохранение поста --------------------
# Изменение: Frontmatter обновлён: title в кавычках, добавлен layout: post, date в формате YYYY-MM-DD.
def save_post(title, body, img_path=None):
    today = datetime.now().strftime("%Y-%m-%d")
    slug = re.sub(r'[^a-z0-9-]+', '-', translit(title)).strip('-')[:80]
    if len(slug) < 10:
        slug = "ai-news-" + ''.join(random.choices("abcdefghijklmnopqrstuvwxyz", k=10))

    filename = POSTS_DIR / f"{today}-{slug}.md"

    frontmatter = f'---\ntitle: "{title}"\nlayout: post\ndate: {today}\ncategories: ai\n'

    if img_path:
        if img_path.startswith("http"):
            frontmatter += f"image: {img_path}\n"
        else:
            rel_path = f"/assets/images/posts/{Path(img_path).name}"
            frontmatter += f"image: {rel_path}\n"

    frontmatter += "---\n\n"

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
        logging.warning("Telegram настройки отсутствуют")
        return

    if len(teaser_text) > 800:
        teaser_text = teaser_text[:800] + "…"

    caption = f"<b>Новая статья!</b>\n\n<b>{title}</b>\n\n{teaser_text}\n\n<i>Читать:</i> {article_url}"

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
            logging.info("Пост отправлен в Telegram!")
        else:
            logging.warning(f"Ошибка Telegram: {resp.status_code} {resp.text}")
    except Exception as e:
        logging.error(f"Ошибка отправки в Telegram: {e}")

# -------------------- MAIN --------------------
def main():
    try:
        topics = [
            "Мультимодальные модели ИИ",
            "Автономные ИИ-агенты",
            "ИИ в медицине",
            "Этика ИИ",
            "ИИ и творчество",
            "Будущее AGI",
            "ИИ в образовании",
            "Голосовые модели ИИ",
            "ИИ в повседневной жизни",
            "Квантовый ИИ"
        ]
        topic = random.choice(topics)
        logging.info(f"Выбрана тема: {topic}")

        title = generate_title(topic)
        body = generate_body(title)
        img_path = generate_image(title)

        _, article_url = save_post(title, body, img_path)

        teaser = " ".join(body.split()[:50]) + "…"
        send_to_telegram(title, teaser, img_path, article_url)

        logging.info("=== Пост успешно создан и опубликован ===")

    except Exception as e:
        logging.error(f"Критическая ошибка: {e}", exc_info=True)

if __name__ == "__main__":
    main()
