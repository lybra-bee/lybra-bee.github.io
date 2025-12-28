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
AIHORDE_API_KEY = os.getenv("AIHORDE_API_KEY", "0000000000")

SITE_URL = "https://lybra-ai.ru"

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

# Ручной транслит для slug
TRANSLIT_MAP = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch', 'ъ': '',
    'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
}

def translit(text):
    return ''.join(TRANSLIT_MAP.get(c.lower(), c.lower()) for c in text)

# -------------------- Шаг 1: Заголовок (с backoff) --------------------
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

# -------------------- Шаг 2: План и разделы (с backoff) --------------------
def generate_outline(title):
    system_prompt = f"""Ты — эксперт по ИИ и технический писатель.
Создай детальный план статьи на русском языке по заголовку: "{title}"

Требования:
- Только нумерованный список из 12–15 основных пунктов (включая Введение и Заключение)
- Каждый пункт — отдельный раздел или подраздел
- План должен быть очень подробным, чтобы общий объём готовой статьи составил не менее 2500 слов
- Используй подзаголовки уровня ## и ###
- Обязательно включи: примеры, кейсы, сравнения моделей, технические детали, прогнозы

Ответ в чистом Markdown, только список."""

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
            lines = [l.strip() for l in outline.split("\n") if l.strip() and re.match(r'^(\d+\.|##)', l.strip())]
            if len(lines) >= 10:
                logging.info(f"План статьи сгенерирован ({len(lines)} пунктов)")
                return outline
        except Exception as e:
            logging.warning(f"Попытка {attempt+1} генерации плана: {e}")
            time.sleep(5)
    raise RuntimeError("Не удалось сгенерировать план статьи")

def generate_section(title, outline, section_header):
    prompt = f"""Напиши подробный раздел статьи на русском языке.

Заголовок статьи: {title}
План статьи (для контекста):
{outline}

Текущий раздел:
{section_header}

Требования:
- Объём: 300–600 слов (обязательно!)
- Формат Markdown
- Подробные объяснения, примеры, кейсы, сравнения
- Доступный язык с техническими деталями
- Если Введение — 400–500 слов с хуком
- Если Заключение — 400–600 слов с выводами и прогнозами
- Только этот раздел, ничего больше!"""

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 4000,
        "temperature": 0.8,
    }

    for attempt in range(6):  # Больше попыток на случай rate limit
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=150)
            if r.status_code == 429:
                wait = (2 ** attempt) * 3 + random.uniform(0, 5)  # Дольше ждём
                logging.warning(f"Rate limit (429) для раздела '{section_header}'. Ждём {wait:.1f} сек...")
                time.sleep(wait)
                continue
            r.raise_for_status()
            text = r.json()["choices"][0]["message"]["content"].strip()
            word_count = len(text.split())
            if word_count >= 250:
                return text
            else:
                logging.warning(f"Раздел '{section_header}' короткий ({word_count} слов) — retry")
                time.sleep(3)
        except Exception as e:
            logging.warning(f"Ошибка генерации раздела '{section_header}' (попытка {attempt+1}): {e}")
            time.sleep(3)

    # Лучший fallback
    fallback = f"В этом разделе рассматриваются ключевые аспекты темы «{section_header}». " \
               f"Генеративный ИИ демонстрирует значительный прогресс, включая практические примеры применения, " \
               f"технические детали реализации и анализ перспектив развития. " \
               f"Детальный обзор временно недоступен из-за технических ограничений API."
    return fallback

def generate_body(title):
    logging.info("Генерация плана статьи...")
    outline = generate_outline(title)

    # Извлекаем заголовки разделов
    section_headers = []
    for line in outline.split("\n"):
        line = line.strip()
        header = re.sub(r'^\d+\.\s*', '', line)
        header = re.sub(r'^##\s*', '', header)
        if header:
            section_headers.append(header.strip())

    if len(section_headers) < 8:
        section_headers = ["Введение"] + section_headers + ["Заключение"]

    logging.info(f"Будет сгенерировано {len(section_headers)} разделов")

    full_body = f"# {title}\n\n"
    total_words = 0

    for i, header in enumerate(section_headers, 1):
        logging.info(f"Генерация раздела {i}/{len(section_headers)}: {header}")
        section_text = generate_section(title, outline, header)
        full_body += f"\n## {header}\n\n{section_text}\n\n"
        words = len(section_text.split())
        total_words += words
        logging.info(f"Раздел готов ({words} слов, всего: {total_words})")

        # Небольшая пауза между разделами, чтобы не превышать rate limit
        time.sleep(random.uniform(2, 5))

    logging.info(f"Статья полностью сгенерирована ({total_words} слов)")
    return full_body

# -------------------- Изображение (оптимизировано для низких kudos) --------------------
def generate_image_horde(title):
    prompt = f"{title}, futuristic artificial intelligence, neural networks, cyberpunk aesthetic, photorealistic, highly detailed, cinematic lighting, vibrant neon colors, masterpiece, best quality"

    url_async = "https://stablehorde.net/api/v2/generate/async"
    payload = {
        "prompt": prompt,
        "models": ["FLUX.1 [schnell]"],  # Только schnell — минимум kudos
        "params": {
            "width": 512,
            "height": 512,
            "steps": 6,          # 4–6 steps достаточно для schnell, сильно снижает kudos
            "cfg_scale": 3.5,    # Низкий CFG для schnell
            "n": 1
        },
        "nsfw": False,
        "trusted_workers": True,
        "slow_workers": False
    }

    headers = {
        "apikey": AIHORDE_API_KEY,
        "Content-Type": "application/json",
        "Client-Agent": "LybraBlogBot:1.1"
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

        for _ in range(40):  # Больше итераций на случай очереди
            time.sleep(6)
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
            logging.info(f"Ожидание... очередь: {check.get('queue_position', '?')}")
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

# -------------------- Сохранение и Telegram (без изменений) --------------------
# (оставляю тот же код, что был в предыдущей версии — он работает отлично)

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
