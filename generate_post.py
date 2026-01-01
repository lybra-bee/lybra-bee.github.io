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

POSTS_DIR = Path("_posts")
IMAGES_DIR = Path("assets/images/posts")
POSTS_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

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
    system_prompt = f"""Ты — гениальный копирайтер, мастер неожиданных и цепляющих заголовков для блога об ИИ.
Создай ОДИН заголовок на русском по теме "{topic}".

КРИТИЧЕСКИ ВАЖНО:
- Длина: 8–16 слов
- Запрещено использовать шаблоны: "Что ждёт нас в...", "Почему все говорят о...", "ИИ, который пугает...", "Революция в...", "Как ИИ меняет..."
- Делай заголовок НЕПРЕДСКАЗУЕМЫМ, ярким, провокационным или интригующим
Примеры хороших стилей:
  • "Когда машины начнут мечтать — и что это значит для нас"
  • "Эксперты молчат: главная угроза ИИ уже здесь"
  • "Один эксперимент, который изменил всё в ИИ"
  • "ИИ учится лгать — и делает это лучше людей"
  • "2026: год, когда ИИ перестанет быть инструментом"
  • "Секрет, который скрывают разработчики нейросетей"
  • "Машина почувствовала эмоции. Что дальше?"
- Используй контраст, парадокс, личный опыт, драму, тайну
- Делай так, чтобы читатель НЕ МОГ НЕ КЛИКНУТЬ

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
        "temperature": 1.3,  # Максимальная креативность
    }

    used_titles = set()

    for attempt in range(15):  # Больше попыток для разнообразия
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
                title_lower = title.lower()
                if (8 <= len(title.split()) <= 16 and
                    title not in used_titles and
                    not title_lower.startswith(("что ждёт", "почему все", "ии который", "революция", "как ии"))):
                    used_titles.add(title)
                    logging.info(f"Сгенерирован заголовок: {title}")
                    return title
        except Exception as e:
            logging.error(f"Ошибка генерации заголовка: {e}")

    # Ручной fallback с разнообразием
    unique_fallbacks = [
        f"Машина научилась чувствовать. А мы — нет",
        f"Один код, который может уничтожить человечество",
        f"Они уже среди нас: ИИ, которые притворяются людьми",
        f"Последнее предупреждение от создателей ИИ",
        f"Когда нейросеть сказала 'я боюсь умереть'",
        f"Секрет OpenAI, который никто не должен знать",
        f"2026: год, когда ИИ станет опаснее ядерного оружия",
        f"Эксперимент, после которого учёные уволились"
    ]
    title = random.choice(unique_fallbacks)
    logging.info(f"Использован уникальный fallback: {title}")
    return title

# -------------------- Шаг 2: Статья 3000–5000 знаков --------------------
def generate_outline(title):
    system_prompt = f"""Создай краткий план статьи по заголовку: "{title}"

- 6–8 основных разделов (##)
- Под каждым — 1–2 подраздела (###)
- Общий объём статьи: строго 3000–5000 знаков
- Темы: введение, история/принципы, применение, риски, прогнозы, заключение

Ответ только в Markdown."""

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": "План."}],
        "max_tokens": 800,
        "temperature": 0.6,
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
    return "## Введение\n### Обзор темы\n## Основные аспекты\n## Применение\n## Риски\n## Будущее\n## Заключение"

def generate_section(title, outline, section_header):
    prompt = f"""#РОЛЬ
Вы — автор увлекательных текстов об ИИ для молодёжи. Пиши живо, по-человечески, с эмоциями.

#ЗАДАЧА
Напиши раздел "{section_header}" для статьи "{title}"

#КОНТЕКСТ
План статьи:
{outline}

#ТРЕБОВАНИЯ
- Объём: 400–700 знаков
- Разговорный тон, риторические вопросы, аналогии
- Фразы: "А знаете что?", "Честно говоря", "Представьте"
- Чередуй короткие и длинные предложения
- Избегай клише и шаблонов
- Только текст раздела в Markdown

Напиши сейчас."""

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 300,  # Жёсткий лимит для контроля длины
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

    return f"В разделе «{section_header}» обсуждаются ключевые моменты темы."

def generate_body(title):
    outline = generate_outline(title)

    section_headers = [re.sub(r'^##\s*', '', line).strip() for line in outline.split("\n") if line.strip().startswith("##")]
    section_headers = section_headers[:8]  # Жёсткий лимит

    full_body = f"# {title}\n\n"
    total_chars = 0

    for i, header in enumerate(section_headers, 1):
        section_text = generate_section(title, outline, header)
        full_body += f"\n## {header}\n\n{section_text}\n\n"
        total_chars += len(section_text)
        logging.info(f"Раздел {i}/8: {len(section_text)} знаков (всего: {total_chars})")

    logging.info(f"Статья готова: {total_chars} знаков")
    return full_body

# -------------------- Изображение: Horde (как в последнем рабочем запуске) --------------------
# (оставляем ту же версию, что сработала — с 360 итерациями, 10 сек sleep, фотореалистичным промптом)

# -------------------- Остальные функции (save_post, send_to_telegram, main) --------------------
# (без изменений — работают идеально)

if __name__ == "__main__":
    main()
