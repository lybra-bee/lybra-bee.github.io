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
        f"Почему {topic.lower()} меняет всё в 2026 году",
        f"ИИ переходит на новый уровень: эра {topic.lower()} началась",
        f"Что скрывают новые разработки в {topic.lower()}",
        f"2026 год начинается сейчас: прорыв в {topic.lower()}",
        f"Как {topic.lower()} уже влияет на нашу жизнь"
    ]
    title = random.choice(fallbacks)
    logging.info(f"Использован fallback-заголовок: {title}")
    return title

# -------------------- Шаг 2: План и тело статьи (3000–5000 знаков) --------------------
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
    prompt = f"""#РОЛЬ
Вы — автор SEO-контента мирового уровня, специализирующийся на создании текстов, которые невозможно отличить от написанных человеком. Ваш опыт заключается в улавливании эмоциональных нюансов, культурной адаптации и контекстуальной аутентичности, что позволяет создавать контент, естественно резонирующий с любой аудиторией.

#ЦЕЛЬ
Сейчас вы напишете один раздел статьи на основе схемы.

ТИП СТАТЬИ: пост для блога об ИИ
ЦЕЛЕВАЯ АУДИТОРИЯ: молодёжь
КОЛИЧЕСТВО ЗНАКОВ: 300–600 (обязательно!)
ТЕМА: {title}
РАЗДЕЛ: {section_header}

Ваш текст должен быть убедительно человечным, увлекательным и запоминающимся. Он должен сохранять логическую последовательность, естественные переходы и непринуждённый тон. Стремитесь к балансу между технической точностью и эмоциональной отзывчивостью.

Полный план статьи (для контекста):
{outline}

#ТРЕБОВАНИЯ
- Старайтесь сохранять показатель Flesch Reading Ease около 80.
- Используйте разговорный, привлекательный тон.
- Включайте естественные отступления на связанные темы, если они важны.
- Смешивайте профессиональный жаргон или рабочие термины с простыми объяснениями.
- Добавляйте лёгкие эмоциональные сигналы и риторические вопросы.
- Используйте сокращения, идиомы и разговорные выражения для создания неформального, захватывающего тона.
- Меняйте длину и структуру предложений. Чередуйте короткие, сильные фразы с длинными, сложными.
- Стройте предложения так, чтобы слова плотно связывались друг с другом (грамматика зависимости), что облегчит понимание.
- Обеспечьте логическую связанность с динамичным ритмом между абзацами.
- Используйте разнообразный словарный запас и неожиданные слова для усиления интереса.
- Избегайте чрезмерного использования наречий.
- Добавляйте лёгкие повторения для акцента, но избегайте излишних или механических шаблонов.
- Используйте риторические или игривые подзаголовки, имитирующие естественный разговорный тон.
- Переходите между частями текста с помощью связующих фраз, избегая изолированных блоков.
- Включайте стилистические элементы вроде риторических вопросов, аналогий и эмоциональных сигналов.
- Перед написанием создайте краткий план или структуру для обеспечения логики и потока.

#РЕКОМЕНДАЦИИ ПО УЛУЖШЕНИЮ ТЕКСТА
- Добавляйте риторические вопросы, эмоциональные подсказки и неформальные фразы, например: «А вы знали?», если это помогает улучшить поток текста.
- Для профессиональной аудитории используйте умеренные эмоциональные сигналы; для широкой аудитории подсказки могут быть более яркими.
- Умеренно используйте разговорные фразы вроде «честно говоря», «знаете», «по правде».
- Включайте сенсорные детали только там, где они повышают ясность или вовлечённость, избегая перегрузки.
- Избегайте слов: выбор, погружение, раскрытие, решение, сложный, использование, трансформационный, выравнивание, проактивный, масштабируемый, эталонный.
- Избегайте фраз: «в этом мире», «в современном мире», «в конце дня», «на одной волне», «от начала до конца», «чтобы», «лучшие практики», «вникнуть в».
- Имейте в виду естественные «человеческие» ошибки вроде неформальных фраз или неожиданных переходов.

#СТРУКТУРНЫЕ ЭЛЕМЕНТЫ
- Чередуйте длину абзацев (от 1 до 7 предложений).
- Используйте списки только по необходимости и естественно.
- Включайте разговорные подзаголовки.
- Обеспечьте логическую связанность с динамичным ритмом между абзацами.
- Естественно используйте различные знаки препинания (тире, точка с запятой, скобки).
- Органично сочетайте официальную и неформальную лексику.
- Используйте смесь активного и пассивного залога, но преимущественно активный.
- Добавляйте разговорные подзаголовки.
- Добавляйте лёгкие, естественные отступления или касания других тем, но всегда возвращайтесь к основной мысли.
- Добавляйте фразы вроде: «А знаете что?» или «Честно говоря».
- Используйте переходные фразы, такие как «Позвольте объяснить» или «В чём же дело?», чтобы плавно вести читателя.
- Добавляйте региональные выражения или культурные отсылки.
- Используйте аналогии, связанные с повседневной жизнью.
- Включайте небольшие повторения идей или фраз, чтобы подчеркнуть мысль или придать спонтанности.
- Только содержимое раздела, в формате Markdown, без заголовка раздела.

Напиши раздел прямо сейчас."""

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

# -------------------- Изображение: Stable Horde с фотореализмом --------------------
def generate_image_horde(title):
    prompt = (
        f"{title}, ultra realistic professional photography, beautiful futuristic scene with artificial intelligence elements, "
        "highly detailed human interacting with holographic AI interface, cyberpunk city at night with neon lights, "
        "sharp focus, cinematic lighting, natural skin textures, realistic eyes, depth of field, 8k resolution, "
        "photorealistic, masterpiece, award winning photo"
    )

    negative_prompt = (
        "abstract, painting, drawing, illustration, cartoon, anime, low quality, blurry, deformed, ugly, extra limbs, "
        "geometric shapes, lines, wireframe, text, watermark, logo, signature, overexposed, underexposed"
    )

    url_async = "https://stablehorde.net/api/v2/generate/async"
    payload = {
        "prompt": prompt + " ### " + negative_prompt,
        "models": ["Juggernaut XL", "Realistic Vision V5.1", "FLUX.1 [schnell]", "SDXL 1.0"],
        "params": {
            "width": 768,
            "height": 512,
            "steps": 28,
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
        "Client-Agent": "LybraBlogBot:2.0"
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

# -------------------- Сохранение поста — РУЧНОЕ YAML без PyYAML --------------------
def save_post(title, body, img_path=None):
    today = datetime.now()
    date_str = today.strftime("%Y-%m-%d")
    full_date_str = today.strftime("%Y-%m-%d 00:00:00 -0000")

    slug = re.sub(r'[^a-z0-9-]+', '-', translit(title)).strip('-')[:80]
    if len(slug) < 10:
        slug = "ai-news-" + ''.join(random.choices("abcdefghijklmnopqrstuvwxyz", k=10))

    filename = POSTS_DIR / f"{date_str}-{slug}.md"

    # Ручное формирование frontmatter
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
            image_url = f"assets/images/posts/{Path(img_path).name}"
        frontmatter_lines.extend([
            f"image: {image_url}",
            f"image_alt: {title.rstrip('.')}",
            f"description: Статья об ИИ: {title.rstrip('.')}"
        ])

    frontmatter_lines.append("---")
    frontmatter = "\n".join(frontmatter_lines) + "\n\n"

    # Обложка в теле с site.baseurl
    if img_path:
        cover_img = image_url if 'image_url' in locals() else '/assets/images/placeholder.jpg'
        body_start = f"![Обложка: {title}]({{{{ site.baseurl }}}}/{cover_img})\n\n"
    else:
        body_start = ""

    full_content = frontmatter + body_start + body

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
