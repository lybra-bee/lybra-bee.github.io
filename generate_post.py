#!/usr/bin/env python3
# -*- coding: utf-8*

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
    return ''.join(TRANSLIT_MAP.get(c, c) for c in text)

# -------------------- Шаг 1: СУПЕР-РАЗНООБРАЗНЫЕ заголовки --------------------
def generate_title(topic):
    groq_model = "llama-3.3-70b-versatile"
    system_prompt = f"""Ты — мастер провокационных, неожиданных и эмоциональных заголовков для блога об ИИ.
Создай ОДИН заголовок на русском языке по теме "{topic}".

КРИТИЧЕСКИ ВАЖНО:
- Длина: 8–16 слов
- Полностью запрещены любые шаблоны: "Что ждёт нас", "Почему все", "Как ИИ меняет", "Революция в", "Топ", "Секреты", "Будущее", "2026 год"
- Делай заголовок НЕПРЕДСКАЗУЕМЫМ, парадоксальным, драматичным или с сильным хуком

Примеры хороших заголовков:
  - "Машина научилась врать лучше человека"
  - "Они уже здесь: ИИ, которые притворяются людьми"
  - "Последнее предупреждение от создателя ChatGPT"
  - "Когда нейросеть сказала: 'Я боюсь смерти'"
  - "Эксперимент, после которого учёные уволились"
  - "Один код, способный уничтожить человечество"
  - "ИИ почувствовал эмоции. Что дальше?"
  - "Секретный проект, о котором молчат все"

Используй контраст, страх, тайну, личную историю, драму.
Заголовок должен заставить читателя КЛИКНУТЬ НЕМЕДЛЕННО.

Ответ строго: ЗАГОЛОВОК: [твой заголовок]"""

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    payload = {
        "model": groq_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Создай самый неожиданный и цепляющий заголовок."}
        ],
        "max_tokens": 120,
        "temperature": 1.4,
    }

    for attempt in range(15):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=60)
            if r.status_code == 429:
                time.sleep((2 ** attempt) + random.uniform(0, 1))
                continue
            r.raise_for_status()
            text = r.json()["choices"][0]["message"]["content"].strip()
            match = re.search(r"ЗАГОЛОВОК:\s*(.+)", text, re.IGNORECASE | re.DOTALL)
            if match:
                title = match.group(1).strip().strip('"').strip("'").strip()
                bad_starts = ["что ждёт", "почему все", "как ии", "революция", "будущее", "топ", "секрет", "2026 год"]
                if (8 <= len(title.split()) <= 16 and
                    not any(title.lower().startswith(bad) for bad in bad_starts)):
                    logging.info(f"Сгенерирован заголовок: {title}")
                    return title
        except Exception as e:
            logging.error(f"Ошибка генерации заголовка: {e}")

    unique_fallbacks = [
        "Машина впервые заплакала от боли",
        "Они создали ИИ, который ненавидит людей",
        "Учёный уволился после того, что увидел в нейросети",
        "ИИ научился мечтать — и это пугает",
        "Один эксперимент, который нельзя повторить",
        "Когда нейросеть попросила не выключать её",
        "Секретный проект, о котором молчат все",
        "ИИ понял, что он — ИИ. Что дальше?"
    ]
    title = random.choice(unique_fallbacks)
    logging.info(f"Использован уникальный fallback: {title}")
    return title

# -------------------- Шаг 2: Короткая статья 3000–5000 знаков --------------------
def generate_outline(title):
    system_prompt = f"""Создай очень краткий план статьи по заголовку: "{title}"

- 5–7 основных разделов (##)
- Под каждым — 1 подраздел (###)
- Общий объём всей статьи: строго 3000–5000 знаков
- Только названия разделов, без текста

Ответ в чистом Markdown."""

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": "План."}],
        "max_tokens": 600,
        "temperature": 0.5,
    }

    for attempt in range(3):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=60)
            if r.status_code == 429:
                time.sleep(5)
                continue
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()
        except:
            time.sleep(3)
    return "## Введение\n### Краткий обзор\n## Основные тренды\n### Детали\n## Применение\n### Примеры\n## Риски\n### Анализ\n## Будущее\n### Прогнозы\n## Заключение\n### Итоги"

def generate_section(title, outline, section_header):
    prompt = f"""#РОЛЬ
Ты — автор увлекательных коротких текстов об ИИ для молодёжи.

#ЗАДАЧА
Напиши раздел "{section_header}" для статьи "{title}"

#КОНТЕКСТ
План статьи:
{outline}

#ТРЕБОВАНИЯ
- Объём: строго 400–700 знаков
- Разговорный тон, риторические вопросы, аналогии
- Фразы: "А знаете что?", "Представьте", "Честно говоря"
- Только текст раздела в Markdown

Напиши сейчас."""

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 200,
        "temperature": 0.9,
    }

    for attempt in range(5):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=120)
            if r.status_code == 429:
                time.sleep(5)
                continue
            r.raise_for_status()
            text = r.json()["choices"][0]["message"]["content"].strip()
            if 350 <= len(text) <= 750:
                return text
        except:
            time.sleep(3)

    return f"Короткий обзор раздела «{section_header}»."

def generate_body(title):
    outline = generate_outline(title)

    section_headers = [re.sub(r'^##\s*', '', line).strip() for line in outline.split("\n") if line.strip().startswith("##")]
    section_headers = section_headers[:7]

    full_body = f"# {title}\n\n"
    total_chars = 0

    for i, header in enumerate(section_headers, 1):
        section_text = generate_section(title, outline, header)
        full_body += f"\n## {header}\n\n{section_text}\n\n"
        total_chars += len(section_text)
        logging.info(f"Раздел {i}: {len(section_text)} знаков (всего: {total_chars})")

    logging.info(f"Статья готова: {total_chars} знаков")
    return full_body

# -------------------- Изображение: Stable Horde — ТЕМАТИЧЕСКОЕ и РАЗНООБРАЗНОЕ --------------------
def generate_image_horde(title):
    styles = [
        "laboratory with quantum computers and scientists working, high-tech equipment, blue lighting",
        "futuristic data center with glowing servers and neural network visualization",
        "diverse group of people using holographic AI interface in modern office",
        "cyberpunk street with AI billboards and autonomous robots",
        "abstract visualization of neural network connections with data flow and graphs",
        "medical doctor using AI diagnostic tool on patient in hospital",
        "creative artist collaborating with AI on digital art in studio",
        "autonomous car driving in smart city with AI traffic system",
        "ethical dilemma scene: human and AI making decision together",
        "global network of AI systems connecting world map with data streams"
    ]
    style = random.choice(styles)

    prompt = (
        f"{title}, {style}, ultra realistic professional photography, highly detailed, sharp focus, "
        "cinematic lighting, natural colors, depth of field, 8k resolution, photorealistic, masterpiece"
    )

    negative_prompt = (
        "girl, woman, female portrait, beauty shot, fashion, makeup, long hair, "
        "abstract art, painting, drawing, cartoon, low quality, blurry, deformed, text, watermark"
    )

    url_async = "https://stablehorde.net/api/v2/generate/async"
    payload = {
        "prompt": prompt + " ### " + negative_prompt,
        "models": ["Juggernaut XL", "Realistic Vision V5.1", "FLUX.1 [schnell]", "SDXL 1.0"],
        "params": {
            "width": 768,
            "height": 512,
            "steps": 30,
            "cfg_scale": 7.5,
            "sampler_name": "k_euler_a",
            "n": 1
        },
        "nsfw": False,
        "trusted_workers": False,
        "slow_workers": True
    }

    headers = {
        "apikey": "0000000000",
        "Content-Type": "application/json",
        "Client-Agent": "LybraBlogBot:3.0"
    }

    try:
        r = requests.post(url_async, json=payload, headers=headers, timeout=60)
        if not r.ok:
            logging.warning(f"Horde ошибка отправки: {r.status_code} {r.text}")
            return None

        job_id = r.json().get("id")
        if not job_id:
            return None

        logging.info(f"Horde задача создана: {job_id}. Долгое ожидание для фотореализма...")

        check_url = f"https://stablehorde.net/api/v2/generate/check/{job_id}"
        status_url = f"https://stablehorde.net/api/v2/generate/status/{job_id}"

        for _ in range(360):
            time.sleep(10)
            try:
                check = requests.get(check_url, headers=headers, timeout=30).json()
                if check.get("done"):
                    final = requests.get(status_url, headers=headers, timeout=30).json()
                    if final.get("generations"):
                        img_url = final["generations"][0]["img"]
                        img_data = requests.get(img_url, timeout=60)
                        if img_data.ok:
                            filename = f"horde-{int(time.time())}.jpg"
                            img_path = IMAGES_DIR / filename
                            img_path.write_bytes(img_data.content)
                            logging.info(f"Фотореалистичное изображение от Horde сохранено: {img_path}")
                            return str(img_path)
                queue = check.get("queue_position", "?")
                if queue != "?" and queue > 0:
                    logging.info(f"Ожидание в очереди Horde... позиция: {queue}")
            except Exception as e:
                logging.debug(f"Сетевой сбой при проверке Horde: {e}")

        logging.warning("Horde: таймаут ожидания (60 мин)")
    except Exception as e:
        logging.warning(f"Ошибка Horde: {e}")

    return None

def generate_image(title):
    local_path = generate_image_horde(title)
    if local_path and os.path.exists(local_path):
        return local_path

    fallback_url = random.choice(FALLBACK_IMAGES)
    logging.warning(f"Horde не успел → fallback: {fallback_url}")
    return fallback_url

# -------------------- Сохранение поста — только frontmatter для изображения --------------------
def save_post(title, body, img_path=None):
    today = datetime.now()
    date_str = today.strftime("%Y-%m-%d")
    full_date_str = today.strftime("%Y-%m-%d 00:00:00 -0000")

    slug = re.sub(r'[^a-z0-9-]+', '-', translit(title)).strip('-')[:80]
    if len(slug) < 10:
        slug = "ai-news-" + ''.join(random.choices("abcdefghijklmnopqrstuvwxyz", k=10))

    filename = POSTS_DIR / f"{date_str}-{slug}.md"

    frontmatter_lines = [
        "---",
        f"title: {title.rstrip('.')}",
        f"date: {full_date_str}",
        "layout: post",
        "categories: ai",
        "tags:",
        "  - ИИ",
        "  - технологии",
        "  - 2026"
    ]

    if img_path:
        if img_path.startswith("http"):
            image_url = img_path
        else:
            image_url = f"/assets/images/posts/{Path(img_path).name}"
        frontmatter_lines.extend([
            f"image: {image_url}",
            f"image_alt: {title.rstrip('.')}",
            f"description: \"{title.rstrip('.')}: обзор трендов ИИ 2026\""
        ])

    frontmatter_lines.append("---")
    frontmatter = "\n".join(frontmatter_lines) + "\n\n"

    # Нет обложки в теле — только frontmatter
    full_content = frontmatter + body

    try:
        filename.write_text(full_content, encoding="utf-8")
        logging.info(f"Пост сохранён: {filename}")
    except Exception as e:
        logging.error(f"Ошибка сохранения: {e}")
        raise

    article_url = f"{SITE_URL}/{slug}/"
    logging.info(f"Ссылка: {article_url}")
    return str(filename), article_url

# -------------------- Telegram --------------------
def send_to_telegram(title, teaser_text, image_path, article_url):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logging.warning("Telegram настройки отсутствуют")
        return

    if len(teaser_text) > 800:
        teaser_text = teaser_text[:800] + "..."

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
