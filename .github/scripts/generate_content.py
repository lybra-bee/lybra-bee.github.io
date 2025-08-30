#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import requests
import random
from datetime import datetime, timezone
import glob
import base64
import time
import re
from pathlib import Path

# ====== ВСТРОЕННЫЕ КЛЮЧИ ДЛЯ БЕСПЛАТНЫХ ГЕНЕРАТОРОВ (ПО ПРОСЬБЕ ПОЛЬЗОВАТЕЛЯ) ======
# Hugging Face — используем Inference API для text-to-image
HF_TOKEN = "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"

# DeepAI — бесплатный тариф (может ограничиваться)
DEEPAI_API_KEY = "98c841c4"

# ====== НАСТРОЙКИ ======
POSTS_DIR = Path("content/posts")
STATIC_IMG_DIR = Path("static/images/posts")
KEEP_LAST_ARTICLES = 3

# Модели Hugging Face для text-to-image (перебор по порядку)
HF_IMAGE_MODELS = [
    # быстрые/популярные
    "stabilityai/sdxl-turbo",
    "runwayml/stable-diffusion-v1-5",
    "stabilityai/stable-diffusion-2-1",
    # альтернативы
    "SG161222/Realistic_Vision_V5.1_noVAE",
]

def log(msg: str):
    print(msg, flush=True)

# ======================== ОСНОВНОЙ ПРОЦЕСС ========================

def generate_content():
    log("🚀 Запуск генерации контента...")

    # Чистим старые проблемные файлы в content/news (были битые YAML)
    cleanup_broken_news()

    # Оставляем только N последних статей
    clean_old_articles(KEEP_LAST_ARTICLES)

    # Тема дня
    selected_topic = generate_ai_trend_topic()
    log(f"📝 Актуальная тема 2025: {selected_topic}")

    # Сначала пробуем сгенерировать изображение (чтобы сразу знать путь)
    log("🎨 Генерация изображения...")
    image_url = generate_article_image(selected_topic)

    # Генерируем текст статьи (OpenRouter -> Groq -> fallback)
    content_md, model_used = generate_article_content(selected_topic)

    # Создаём файл статьи
    date_prefix = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    slug = generate_slug(selected_topic)
    filename = POSTS_DIR / f"{date_prefix}-{slug}.md"
    filename.parent.mkdir(parents=True, exist_ok=True)

    fm = generate_frontmatter(selected_topic, content_md, model_used, image_url)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(fm)

    log(f"✅ Статья создана: {filename}")
    return str(filename)


# ======================== ТЕМА ДНЯ ========================

def generate_ai_trend_topic():
    current_trends_2025 = [
        "Multimodal AI интеграция текста изображений и аудио в единых моделях",
        "AI агенты автономные системы способные выполнять сложные задачи",
        "Квантовые вычисления и машинное обучение прорыв в производительности",
        "Нейроморфные вычисления энергоэффективные архитектуры нейросетей",
        "Generative AI создание контента кода и дизайнов искусственным интеллектом",
        "Edge AI обработка данных на устройстве без облачной зависимости",
        "AI для кибербезопасности предиктивная защита от угроз",
        "Этичный AI ответственное развитие и использование искусственного интеллекта",
        "AI в healthcare диагностика разработка лекарств и персонализированная медицина",
        "Автономные системы беспилотный транспорт и робототехника",
        "AI оптимизация сжатие моделей и ускорение inference",
        "Доверенный AI объяснимые и прозрачные алгоритмы",
        "AI для климата оптимизация энергопотребления и экологические решения",
        "Персональные AI ассистенты индивидуализированные цифровые помощники",
        "AI в образовании адаптивное обучение и персонализированные учебные планы",
    ]

    application_domains = [
        "в веб разработке и cloud native приложениях",
        "в мобильных приложениях и IoT экосистемах",
        "в облачных сервисах и распределенных системах",
        "в анализе больших данных и бизнес аналитике",
        "в компьютерной безопасности и киберзащите",
        "в медицинской диагностике и биотехнологиях",
        "в финансовых технологиях и финтехе",
        "в автономных транспортных системах",
        "в smart city и умной инфраструктуре",
        "в образовательных технологиях и EdTech",
    ]

    trend = random.choice(current_trends_2025)
    domain = random.choice(application_domains)

    formats = [
        f"Тенденции 2025 {trend} {domain}",
        f"{trend} {domain} в 2025 году",
        f"{trend} революционные изменения {domain} в 2025",
        f"Как {trend} трансформирует {domain} в 2025 году",
        f"Инновации 2025 {trend} для {domain}",
        f"{trend} будущее {domain} в 2025 году",
        f"Практическое применение {trend} в {domain} 2025",
    ]
    return random.choice(formats)


# ======================== ГЕНЕРАЦИЯ ТЕКСТА ========================

def generate_article_content(topic: str):
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")

    models_to_try = []

    # 1) OpenRouter приоритет
    if openrouter_key:
        log("🔑 OpenRouter API ключ найден")
        for m in [
            "anthropic/claude-3-haiku",
            "mistralai/mistral-7b-instruct",
            "meta-llama/llama-3-8b-instruct",
            "google/gemini-pro",
        ]:
            models_to_try.append(
                (f"OpenRouter-{m}", lambda model=m: generate_with_openrouter(openrouter_key, model, topic))
            )

    # 2) Groq — запасной
    if groq_key:
        log("🔑 Groq API ключ найден")
        for m in [
            "llama-3.1-8b-instant",
            "llama-3.2-1b-preview",
            "llama-3.2-3b-preview",
            "mixtral-8x7b-32768",
            "gemma2-9b-it",
        ]:
            models_to_try.append(
                (f"Groq-{m}", lambda model=m: generate_with_groq(groq_key, model, topic))
            )

    # Перебор моделей
    for name, fn in models_to_try:
        try:
            log(f"🔄 Пробуем: {name}")
            text = fn()
            if isinstance(text, str) and len(text.strip()) > 150:
                log(f"✅ Успешно через {name}")
                return text.strip(), name
        except Exception as e:
            log(f"⚠️ Ошибка {name}: {str(e)[:200]}")
            time.sleep(0.5)

    # Fallback — простая заготовка
    log("⚠️ Все LLM недоступны, используем fallback-контент")
    content = f"""# {topic}

## Введение
{topic} — одно из ключевых направлений искусственного интеллекта в 2025 году.

## Технические аспекты
- **Модели**: современные архитектуры трансформеров и мультимодальные сети  
- **Инфраструктура**: облака, edge-вычисления, ускорители

## Применение
- Промышленность, финтех, здравоохранение и кибербезопасность

## Перспективы
Акцент на энергоэффективность, объяснимость, безопасность и интеграцию с ИоТ.

## Заключение
{topic} формирует новую технологическую норму для бизнеса и разработчиков.
"""
    return content, "fallback"


def generate_with_openrouter(api_key: str, model_name: str, topic: str) -> str:
    prompt = f"""Напиши развернутую техническую статью на тему: "{topic}".

Требования:
- Объем 500–800 слов
- Формат Markdown с подзаголовками ##
- Язык: русский
- Стиль: технический, для разработчиков и ИТ-архитекторов
- Фокус на 2025 год

Структура:
1) Введение и актуальность
2) Архитектура и техники (конкретные алгоритмы, фреймворки)
3) Кейсы внедрения
4) Ограничения, риски и безопасность
5) Перспективы и выводы

Используй **жирный** для терминов, списки и примеры."""

    r = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://github.com/lybra-bee",
            "X-Title": "AI Blog Generator",
        },
        json={
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1800,
            "temperature": 0.7,
        },
        timeout=60,
    )
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"]


def generate_with_groq(api_key: str, model_name: str, topic: str) -> str:
    prompt = f"""Напиши развернутую техническую статью на тему: "{topic}".

Требования:
- 500–800 слов, Markdown, подзаголовки ##
- Русский язык, технический стиль
- Аудитория: разработчики, DevOps, архитекты
- 2025 год, актуальные технологии и фреймворки

Добавь: **жирный** для ключевых терминов, списки и практические примеры."""

    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        json={
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1800,
            "temperature": 0.7,
            "top_p": 0.9,
        },
        timeout=60,
    )
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"]


# ======================== ГЕНЕРАЦИЯ ИЗОБРАЖЕНИЯ ========================

def generate_article_image(topic: str) -> str | None:
    """Пытаемся сгенерировать иллюстрацию к статье, возвращаем web-путь /images/posts/xxx.jpg"""
    prompt = generate_image_prompt(topic)
    slug = generate_slug(topic)
    STATIC_IMG_DIR.mkdir(parents=True, exist_ok=True)
    target_path = STATIC_IMG_DIR / f"{slug}.jpg"

    generators = [
        ("HuggingFace", lambda: generate_image_huggingface(prompt, target_path)),
        ("DeepAI",      lambda: generate_image_deepai(prompt, target_path)),
        ("Craiyon",     lambda: generate_image_craiyon(prompt, target_path)),
        ("Lexica",      lambda: fetch_image_lexica(prompt, target_path)),
        ("Picsum",      lambda: fetch_image_picsum(slug, target_path)),
    ]

    for name, fn in generators:
        try:
            log(f"🔄 Пробуем генератор: {name}")
            ok = fn()
            if ok and target_path.exists() and target_path.stat().st_size > 1024:
                log(f"✅ Успешно сгенерировано изображение через {name}")
                return f"/images/posts/{target_path.name}"
            else:
                log(f"⚠️ {name} вернул None")
        except Exception as e:
            log(f"⚠️ Ошибка генерации через {name}: {str(e)[:200]}")

    log("❌ Все генераторы не сработали — продолжаем без изображения")
    return None


def generate_image_huggingface(prompt: str, out_path: Path) -> bool:
    """Hugging Face Inference API — перебор моделей; ждём загрузку модели."""
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    for model in HF_IMAGE_MODELS:
        try:
            url = f"https://api-inference.huggingface.co/models/{model}"
            resp = requests.post(
                url,
                headers=headers,
                json={"inputs": prompt, "options": {"wait_for_model": True}},
                timeout=120,
            )
            # Иногда сервис возвращает JSON-ошибку
            ctype = resp.headers.get("content-type", "")
            if resp.status_code == 200 and "image" in ctype:
                out_path.write_bytes(resp.content)
                return True
            else:
                # Попробуем разобрать JSON, чтобы понять причину
                try:
                    j = resp.json()
                    log(f"ℹ️ HF {model} ответ: {j}")
                except Exception:
                    log(f"ℹ️ HF {model} контент-тип {ctype}, статус {resp.status_code}")
        except requests.HTTPError as e:
            log(f"HF {model} HTTPError: {e}")
        except Exception as e:
            log(f"HF {model} error: {e}")
    return False


def generate_image_deepai(prompt: str, out_path: Path) -> bool:
    """DeepAI text2img (бесплатные лимиты бывают)."""
    try:
        url = "https://api.deepai.org/api/text2img"
        resp = requests.post(
            url,
            headers={"Api-Key": DEEPAI_API_KEY},
            data={"text": prompt},
            timeout=60,
        )
        if resp.status_code != 200:
            log(f"DeepAI HTTP {resp.status_code}: {resp.text[:200]}")
            return False
        data = resp.json()
        img_url = data.get("output_url") or data.get("id")  # иногда другой ключ
        if not img_url:
            log(f"DeepAI: не вернул ссылку: {data}")
            return False
        # Скачиваем изображение по ссылке
        r2 = requests.get(img_url, timeout=60)
        if r2.status_code == 200:
            out_path.write_bytes(r2.content)
            return True
        log(f"DeepAI download HTTP {r2.status_code}")
        return False
    except Exception as e:
        log(f"DeepAI error: {e}")
        return False


def generate_image_craiyon(prompt: str, out_path: Path) -> bool:
    """Craiyon (часто ограничивает/блокирует). Возвращает base64 картинку."""
    try:
        url = "https://api.craiyon.com/v3/text-to-image"
        payload = {"prompt": prompt, "negative_prompt": "", "resolution": "1024x1024"}
        resp = requests.post(url, json=payload, timeout=120)
        if resp.status_code != 200:
            log(f"Craiyon HTTP {resp.status_code}: {resp.text[:200]}")
            return False
        data = resp.json()
        images_b64 = data.get("images") or []
        if not images_b64:
            return False
        img_bytes = base64.b64decode(images_b64[0])
        out_path.write_bytes(img_bytes)
        return True
    except Exception as e:
        log(f"Craiyon error: {e}")
        return False


def fetch_image_lexica(prompt: str, out_path: Path) -> bool:
    """Lexica — не генерация, а подбор похожей картинки (может блокироваться Cloudflare)."""
    try:
        q = re.sub(r"\s+", "+", prompt.strip())[:200]
        url = f"https://lexica.art/api/v1/search?q={q}"
        resp = requests.get(url, timeout=60)
        if resp.status_code != 200:
            log(f"Lexica HTTP {resp.status_code}")
            return False
        data = resp.json()
        imgs = data.get("images") or []
        if not imgs:
            return False
        # Берём полноразмерный src
        src = imgs[0].get("src") or imgs[0].get("srcSmall")
        if not src:
            return False
        r2 = requests.get(src, timeout=60)
        if r2.status_code == 200:
            out_path.write_bytes(r2.content)
            return True
        log(f"Lexica download HTTP {r2.status_code}")
        return False
    except Exception as e:
        log(f"Lexica error: {e}")
        return False


def fetch_image_picsum(seed: str, out_path: Path) -> bool:
    """Надёжный последний fallback: случайное изображение по seed."""
    try:
        url = f"https://picsum.photos/seed/{seed}/1024/1024"
        resp = requests.get(url, timeout=60)
        if resp.status_code == 200:
            out_path.write_bytes(resp.content)
            return True
        log(f"Picsum HTTP {resp.status_code}")
        return False
    except Exception as e:
        log(f"Picsum error: {e}")
        return False


def generate_image_prompt(topic: str) -> str:
    en = (
        f"Futuristic technology illustration for article about '{topic}'. "
        "Abstract neural networks, data flows, circuit patterns, holographic UI, "
        "clean corporate style, professional digital art, centered composition, "
        "high detail, 4k, no text, no watermark."
    )
    variants = [
        en,
        en + " Blue-purple palette, soft glow, cinematic lighting.",
        en + " Geometric shapes, depth of field, volumetric light.",
        en + " Cyberpunk accents, neon glows, high contrast.",
    ]
    return random.choice(variants)


# ======================== СЕРВИСНЫЕ ФУНКЦИИ ========================

def generate_slug(text: str) -> str:
    text = text.lower()
    text = text.replace(" ", "-")
    text = re.sub(r"[^a-z0-9\-]", "", text)  # только ascii
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:80] if text else "ai-2025"


def generate_frontmatter(title: str, content: str, model_used: str, image_url: str | None) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    # безопасный заголовок для YAML
    safe_title = (
        title.replace(":", " -")
             .replace('"', "")
             .replace("'", "")
             .replace("\\", "")
             .strip()
    )
    lines = [
        "---",
        f'title: "{safe_title}"',
        f"date: {now}",
        "draft: false",
        'tags: ["AI", "машинное обучение", "технологии", "2025"]',
        'categories: ["Искусственный интеллект"]',
        f'summary: "Автоматически сгенерированная статья (модель: {model_used})"',
    ]
    if image_url:
        lines.append(f'image: "{image_url}"')
    lines.append("---")
    lines.append(content.strip())
    return "\n".join(lines) + "\n"


def clean_old_articles(keep_last: int = 3):
    log(f"🧹 Очистка старых статей, оставляем {keep_last} последних...")
    try:
        POSTS_DIR.mkdir(parents=True, exist_ok=True)
        items = sorted(POSTS_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not items:
            log("📁 Нет статей для очистки")
            return
        to_delete = items[keep_last:]
        log(f"📊 Всего статей: {len(items)}")
        log(f"💾 Сохраняем: {len(items[:keep_last])}")
        log(f"🗑️ Удаляем: {len(to_delete)}")
        for p in to_delete:
            try:
                p.unlink()
                log(f"❌ Удалено: {p.name}")
            except Exception as e:
                log(f"⚠️ Не удалось удалить {p}: {e}")
    except Exception as e:
        log(f"⚠️ Ошибка при очистке статей: {e}")


def cleanup_broken_news():
    """Удаляем старые файлы в content/news, которые ломали Hugo из-за YAML."""
    news_dir = Path("content/news")
    if not news_dir.exists():
        return
    removed = 0
    for md in news_dir.glob("*.md"):
        try:
            md.unlink()
            removed += 1
        except Exception:
            pass
    if removed:
        log(f"🧽 Удалено проблемных файлов в content/news: {removed}")


# ======================== Точка входа ========================

if __name__ == "__main__":
    generate_content()
