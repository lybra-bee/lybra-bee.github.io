#!/usr/bin/env python3
"""
Автономная система генерации статей об ИИ 2025-2026
- Жёстко запрещена политика
- Генерация статьи и изображения
- Публикация в Telegram
- Полные логи генерации
"""

import datetime
import random
import os
import re
import json
import time
import glob
import logging
from typing import Dict, List

import requests
import yaml
from groq import Groq

# ---------- Настройка логирования ----------
logging.basicConfig(
    filename="generation.log",
    filemode="w",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger()

# ---------- Конфигурация ----------
EMBEDDED_TRENDS_FILE = "trends_cache.json"
TRENDS_UPDATE_INTERVAL = 86400  # 24 часа
BASE_URL = "https://lybra-ai.ru"

EMBEDDED_TRENDS = [
    {"id": "quantum_2025", "news": "Google Willow quantum chip achieves verifiable quantum advantage, 13000x faster", "keywords": ["quantum computing", "Google Willow"], "category": "hardware"},
    {"id": "m5_chip_2025", "news": "Apple M5 delivers 4x GPU performance for AI vs M4, Nvidia DGX Spark 1 petaflop", "keywords": ["Apple M5", "Nvidia DGX"], "category": "hardware"},
    {"id": "agentic_ai_2025", "news": "Multi-agent systems and Agentic AI integrate RAG for enterprise", "keywords": ["Agentic AI", "RAG"], "category": "software"},
    {"id": "medical_ai_2025", "news": "BInD model designs drugs without molecular data, FDA approved 223 AI devices", "keywords": ["AI drug discovery", "FDA"], "category": "healthcare"},
    {"id": "efficiency_2025", "news": "GPT-3.5 inference cost dropped 280x in 2 years, open-weights closed gap 1.7%", "keywords": ["model efficiency", "open weights"], "category": "optimization"},
]

posts_dir = "_posts"
assets_dir = "assets/images/posts"
os.makedirs(posts_dir, exist_ok=True)
os.makedirs(assets_dir, exist_ok=True)

# ---------- Вспомогательные функции ----------
def normalize_markdown(md: str) -> str:
    """Приводит вывод LLM к валидному Markdown (Jekyll-safe)"""
    if not md:
        return md
    md = re.sub(r"<[^>]+>", "", md)
    md = re.sub(r"(#+\s.*)", r"\n\1\n", md)
    md = re.sub(r"\n([*-]\s)", r"\n\n\1", md)
    md = re.sub(r"\n(\|.*\|)\n(\|[-: ]+\|)", r"\n\n\1\n\2", md)
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip() + "\n"

# ---------- Загрузка трендов ----------
def load_trends() -> List[Dict]:
    try:
        if os.path.exists(EMBEDDED_TRENDS_FILE):
            with open(EMBEDDED_TRENDS_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)
                if time.time() - cache.get("last_update", 0) < TRENDS_UPDATE_INTERVAL:
                    logger.info("✅ Тренды загружены из кэша")
                    return cache.get("trends", [])
    except Exception as e:
        logger.warning(f"⚠️ Ошибка кэша: {e}")
    return update_trends_cache()

def update_trends_cache() -> List[Dict]:
    logger.info("🔄 Обновление трендов...")
    trends: List[Dict] = []
    api_key = os.getenv("NEWSAPI_KEY")
    if api_key:
        try:
            resp = requests.get(
                "https://newsapi.org/v2/everything",
                headers={"X-Api-Key": api_key},
                params={"q": "artificial intelligence", "language": "en", "pageSize": 10},
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                for i, a in enumerate(data.get("articles", [])[:10]):
                    title = a.get("title", "")
                    trends.append({
                        "id": f"news_{i}_{int(time.time())}",
                        "news": title + ". " + (a.get("description") or ""),
                        "keywords": title.lower().split()[:5],
                        "category": "news"
                    })
        except Exception as e:
            logger.warning(f"❌ NewsAPI: {e}")
    if not trends:
        try:
            import feedparser
            feeds = [
                "https://www.artificialintelligence-news.com/feed/",
                "https://venturebeat.com/ai/feed/"
            ]
            ts = int(time.time())
            for url in feeds:
                feed = feedparser.parse(url)
                for i, e in enumerate(feed.entries[:5]):
                    title = e.get("title", "")
                    trends.append({
                        "id": f"rss_{i}_{ts}",
                        "news": title + ". " + e.get("description", "")[:200],
                        "keywords": title.lower().split()[:5],
                        "category": "rss"
                    })
        except Exception as e:
            logger.warning(f"❌ RSS: {e}")
    if not trends:
        logger.warning("⚠️ Используем встроенные тренды")
        trends = EMBEDDED_TRENDS
    try:
        with open(EMBEDDED_TRENDS_FILE, "w", encoding="utf-8") as f:
            json.dump({"last_update": int(time.time()), "trends": trends}, f)
    except Exception as e:
        logger.warning(f"⚠️ Не удалось сохранить кэш: {e}")
    return trends

# ---------- Генерация заголовка ----------
def generate_title(client: Groq, trend: Dict, article_type: str) -> str:
    prompt = (
        f"Создай ОДИН цепляющий заголовок (5–12 слов) для статьи типа '{article_type}'.\n"
        f"Тема: {trend['news']}.\n"
        "Стиль: конкретно, полезно, интригующе, с цифрами или результатом.\n"
        "Запрещено: политика, страны, регуляторы, законы, указы, лидеры.\n"
        "Разрешено: ИИ, технологии, продукты, исследования, рынок, метрики.\n"
        "Только заголовок, без кавычек."
    )
    resp = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "Русский тех-редактор. Делай заголовки, которые хочется открыть."},
            {"role": "user", "content": prompt},
        ],
        model="llama-3.1-8b-instant",
        max_tokens=30,
        temperature=1.0
    )
    title = resp.choices[0].message.content.strip()
    title = re.sub(r"[^\w\s-]", "", title)[:80]
    logger.info(f"📰 Заголовок: {title}")
    return title

# ---------- Генерация статьи ----------
def generate_article(client: Groq, trend: Dict, article_type: str) -> str:
    system_prompt = f"""Вы — опытный технический журналист по ИИ. Аудитория: разработчики, инженеры, фаундеры, тех-энтузиасты.
СТРОГО запрещено: политика, страны, регуляторы, законы, указы, лидеры, ведомства.
Фокус: цифры, сравнения, реальные кейсы, практическая польза
Формат: Markdown, ## подзаголовки, списки, таблицы, примеры
Тема: {trend['news']}
"""
    user_prompt = (
        f"Напишите полную статью типа '{article_type}' (1500–3000 слов).\n"
        "- минимум 2 таблицы\n"
        "- реальные метрики\n"
        "- практические примеры\n"
        "- выводы и прогнозы\n"
    )

    for attempt in range(3):
        resp = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="llama-3.3-70b-versatile",
            max_tokens=4000,
            temperature=0.85
        )
        content = normalize_markdown(resp.choices[0].message.content)
        if re.search(r"политик", content, re.IGNORECASE):
            logger.warning("⚠️ Обнаружена политика — регенерация")
            continue
        return content
    raise ValueError("Статья не прошла проверку на политику")

# ---------- Генерация изображения ----------
def generate_image(title, trend, post_num):
    path = f"{assets_dir}/post-{post_num}.png"

    # 1️⃣ HuggingFace
    try:
        from PIL import Image
        import io
        # здесь вставьте ваш код генерации HF
        # img_bytes = ...
        raise NotImplementedError
    except Exception as e:
        logger.warning(f"⚠️ HF ошибка: {e}")

    # 2️⃣ ClipDrop
    clipdrop_key = os.getenv("CLIPDROP_API_KEY")
    if clipdrop_key:
        try:
            prompt = f"Ultra-realistic photo of {title}. {trend['news'][:120]}. Cinematic, 8K."
            resp = requests.post(
                "https://clipdrop-api.co/text-to-image/v1",
                files={"prompt": (None, prompt)},
                headers={"x-api-key": clipdrop_key},
                timeout=90
            )
            if resp.status_code == 200:
                with open(path, "wb") as f:
                    f.write(resp.content)
                logger.info("🖼 ClipDrop image generated")
                return path
        except Exception as e:
            logger.warning(f"⚠️ ClipDrop ошибка: {e}")

    # 3️⃣ Fallback Matplotlib PNG
    try:
        import matplotlib.pyplot as plt
        years = ["2023","2024","2025"]
        values = [random.randint(40,100) for _ in years]
        plt.figure(figsize=(12,6))
        plt.plot(years, values, marker="o", linewidth=3)
        plt.title("AI Trend Growth")
        plt.tight_layout()
        plt.savefig(path, dpi=150)
        plt.close()
        logger.info("🖼 PNG fallback")
        return path
    except Exception as e:
        logger.error(f"❌ Fallback ошибка: {e}")
        return None

# ---------- Публикация в Telegram ----------
def send_telegram(title, content, image_path):
    if not os.getenv("TELEGRAM_BOT_TOKEN") or not os.getenv("TELEGRAM_CHAT_ID"):
        logger.warning("⚠️ Telegram пропущен (нет ключей)")
        return
    teaser = ' '.join(content.split()[:30]) + '…'

    def esc(text):
        return re.sub(r'([_*\[\]\(\)~`>#+\-=|{}.!])', r'\\\1', text)

    message = f"*Новая статья*\n\n{esc(teaser)}\n\n[Читать на сайте]({BASE_URL})\n\n{esc('#ИИ #LybraAI')}"
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/sendPhoto",
            data={"chat_id": os.getenv("TELEGRAM_CHAT_ID"),
                  "caption": message,
                  "parse_mode": "MarkdownV2"},
            files={"photo": open(image_path, "rb")}
        )
        logger.info(f"📢 Telegram статус: {resp.status_code}")
    except Exception as e:
        logger.error(f"❌ Telegram ошибка: {e}")

# ---------- MAIN ----------
def main():
    logger.info("🚀 Запуск генерации")
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    trends = load_trends()
    if not trends:
        logger.error("❌ Тренды не найдены")
        return False

    trend = random.choice(trends)
    article_type = random.choice(["Обзор", "Урок", "Статья", "Мастер-класс"])

    title = generate_title(client, trend, article_type)
    try:
        content = generate_article(client, trend, article_type)
    except ValueError as e:
        logger.error(f"❌ {e}")
        return False

    image_files = glob.glob(f"{assets_dir}/*.png") + glob.glob(f"{assets_dir}/*.jpg")
    post_num = len(image_files) + 1
    image_path = generate_image(title, trend, post_num)

    # Сохраняем статью
    today = datetime.date.today()
    slug = re.sub(r"[^\w-]", "-", title.lower())
    slug = re.sub(r"-{2,}", "-", slug).strip("-")[:50]
    filename = f"{posts_dir}/{today}-{slug}.md"
    front_matter = {
        "title": title,
        "date": f"{today} 00:00:00 +0000",
        "layout": "post",
        "image": f"/assets/images/posts/post-{post_num}.png",
        "description": f"{article_type.lower()} о {trend['keywords'][0]} 2025",
        "tags": ["ИИ", "технологии", article_type.lower()] + trend["keywords"],
    }
    with open(filename, "w", encoding="utf-8") as f:
        f.write("---\n")
        yaml.dump(front_matter, f, allow_unicode=True, sort_keys=False)
        f.write("---\n\n")
        f.write(content)
    logger.info(f"💾 Статья сохранена: {filename}")

    # Публикация в Telegram
    if image_path:
        send_telegram(title, content, image_path)
    return True

if __name__ == "__main__":
    success = main()
    raise SystemExit(0 if success else 1)
