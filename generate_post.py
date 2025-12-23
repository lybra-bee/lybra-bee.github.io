#!/usr/bin/env python3
"""
Автономная система генерации статей об ИИ 2025–2026
"""

import datetime
import random
import os
import re
import json
import time
import glob
from typing import Dict, List

import requests
import yaml
from groq import Groq

# ---------- КОНФИГУРАЦИЯ ----------
EMBEDDED_TRENDS_FILE = "trends_cache.json"
TRENDS_UPDATE_INTERVAL = 86400
BASE_URL = "https://lybra-ai.ru"

# ---------- MARKDOWN NORMALIZER ----------
def normalize_markdown(md: str) -> str:
    if not md:
        return md
    md = re.sub(r"<[^>]+>", "", md)
    md = re.sub(r"(#+\s.*)", r"\n\1\n", md)
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip() + "\n"

# ---------- АНТИ-ПОЛИТИЧЕСКИЙ ФИЛЬТР ----------
POLITICAL_RE = re.compile(
    r"\b(государств|правительств|регулятор|закон|указ|санкц|выбор|министр|президент|парламент)\b",
    re.IGNORECASE
)

def is_political(text: str) -> bool:
    return bool(POLITICAL_RE.search(text or ""))

# ---------- TRENDS ----------
EMBEDDED_TRENDS = [
    {"id": "quantum", "news": "Quantum processors reached 13 000x speedup for AI workloads",
     "keywords": ["quantum computing", "AI hardware"], "category": "hardware"},
    {"id": "agents", "news": "Agentic AI systems automate complex workflows with RAG",
     "keywords": ["agentic ai", "rag"], "category": "software"},
    {"id": "efficiency", "news": "Inference costs dropped 280x enabling local AI",
     "keywords": ["ai efficiency", "open models"], "category": "optimization"},
]

def load_trends() -> List[Dict]:
    return EMBEDDED_TRENDS

# ---------- ЗАГОЛОВОК ----------
def generate_title(client: Groq, trend: Dict, article_type: str) -> str:
    prompt = (
        f"Создай один цепляющий заголовок (5–12 слов).\n"
        f"Тема: {trend['news']}.\n"
        "Только технологии и ИИ. Без политики. Без стран. Без регуляторов."
    )
    resp = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "Ты тех-редактор, делающий вирусные заголовки."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=40,
        temperature=1.0
    )
    return re.sub(r"[^\w\s-]", "", resp.choices[0].message.content.strip())[:80]

# ---------- СТАТЬЯ ----------
def generate_article(client: Groq, trend: Dict, article_type: str) -> str:
    system_prompt = f"""
Ты профессиональный журналист по ИИ и высоким технологиям.
СТРОГО ЗАПРЕЩЕНО:
- политика
- государства
- регуляторы
- законы
- указы
- чиновники

Разрешено:
- ИИ
- нейросети
- модели
- вычисления
- метрики
- кейсы
- цифры

Тема: {trend['news']}
"""

    user_prompt = (
        f"Напиши статью '{article_type}' (1500–3000 слов).\n"
        "- минимум 2 таблицы\n"
        "- реальные цифры\n"
        "- практическая польза\n"
    )

    for _ in range(2):
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=4000,
            temperature=0.85
        )
        text = normalize_markdown(resp.choices[0].message.content)
        if not is_political(text):
            return text

    return text  # если вдруг оба раза прошли одинаково

# ---------- ИЗОБРАЖЕНИЕ (PNG) ----------
def generate_image(title: str, trend: Dict, post_num: int) -> bool:
    prompt = (
        f"Ultra realistic photo illustration of {title}. {trend['news']}. "
        "Real world scene, cinematic lighting, photorealistic. "
        "NO charts, NO graphs, NO text, NO infographics."
    )

    path = f"{assets_dir}/post-{post_num}.png"

    clipdrop = os.getenv("CLIPDROP_API_KEY")
    if clipdrop:
        try:
            r = requests.post(
                "https://clipdrop-api.co/text-to-image/v1",
                headers={"x-api-key": clipdrop},
                files={"prompt": (None, prompt)},
                timeout=90
            )
            if r.status_code == 200:
                open(path, "wb").write(r.content)
                return True
        except Exception:
            pass

    # fallback: HF
    hf = os.getenv("HF_API_TOKEN")
    if hf:
        try:
            r = requests.post(
                "https://api-inference.huggingface.co/models/stabilityai/sdxl-turbo",
                headers={"Authorization": f"Bearer {hf}"},
                json={"inputs": prompt},
                timeout=90
            )
            if r.status_code == 200:
                open(path, "wb").write(r.content)
                return True
        except Exception:
            pass

    return False

# ---------- MAIN ----------
def main() -> bool:
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    trends = load_trends()
    trend = random.choice(trends)

    article_type = random.choice(["Обзор", "Статья", "Гайд"])

    title = generate_title(client, trend, article_type)
    content = generate_article(client, trend, article_type)

    generate_image(title, trend, post_num)

    front_matter = {
        "title": title,
        "date": f"{today} 00:00:00 +0000",
        "layout": "post",
        "image": f"/assets/images/posts/post-{post_num}.png",
        "description": f"{article_type} о ИИ и технологиях",
        "tags": ["ИИ", "технологии"],
    }

    slug = re.sub(r"[^\w-]", "-", title.lower())
    filename = f"{posts_dir}/{today}-{slug}.md"

    with open(filename, "w", encoding="utf-8") as f:
        f.write("---\n")
        yaml.dump(front_matter, f, allow_unicode=True, sort_keys=False)
        f.write("---\n\n")
        f.write(content)

    return True

# ---------- INIT ----------
if __name__ == "__main__":
    posts_dir = "_posts"
    assets_dir = "assets/images/posts"
    os.makedirs(posts_dir, exist_ok=True)
    os.makedirs(assets_dir, exist_ok=True)

    post_num = len(glob.glob(f"{assets_dir}/*.png")) + 1
    today = datetime.date.today()
    success = main()
    raise SystemExit(0 if success else 1)
