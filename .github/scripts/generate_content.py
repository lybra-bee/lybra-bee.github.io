#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import requests
import random
import base64
import glob
from datetime import datetime
from typing import Optional, Tuple

# ==========
# Константы
# ==========
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
STABILITYAI_KEY = os.getenv("STABILITYAI_KEY")

POSTS_DIR = "content/posts"
IMAGES_DIR = "static/images/posts"   # кладём в static, чтобы Hugo точно отдал
KEEP_LAST_ARTICLES = 6               # сколько статей держать максимум

# ==========
# Утилиты
# ==========
def ensure_dirs():
    os.makedirs(POSTS_DIR, exist_ok=True)
    os.makedirs(IMAGES_DIR, exist_ok=True)

def transliterate_ru_to_en(text: str) -> str:
    table = {
        'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'e','ж':'zh','з':'z','и':'i','й':'y',
        'к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r','с':'s','т':'t','у':'u','ф':'f',
        'х':'h','ц':'ts','ч':'ch','ш':'sh','щ':'sch','ъ':'','ы':'y','ь':'','э':'e','ю':'yu','я':'ya'
    }
    res = []
    for ch in text.lower():
        if ch in table: res.append(table[ch])
        elif ch.isalnum(): res.append(ch)
        elif ch in [' ', '-', '_']: res.append('-')
        else: res.append('-')
    slug = ''.join(res)
    while '--' in slug: slug = slug.replace('--', '-')
    return slug.strip('-')[:70]

def generate_slug(topic: str) -> str:
    return transliterate_ru_to_en(topic)

def clean_old_articles(keep_last=KEEP_LAST_ARTICLES):
    files = sorted(glob.glob(f"{POSTS_DIR}/*.md"), key=os.path.getmtime, reverse=True)
    for path in files[keep_last:]:
        try:
            os.remove(path)
        except Exception as e:
            print(f"⚠️ Не удалось удалить {path}: {e}")

def write_file(path: str, content: bytes, binary: bool = False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    mode = "wb" if binary else "w"
    with open(path, mode, encoding=None if binary else "utf-8") as f:
        f.write(content)

# ==========
# LLM: выбор темы и генерация статьи
# ==========
def llm_chat_groq(prompt: str, model: str = "llama-3.1-8b-instant", max_tokens: int = 1400) -> str:
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY not set")
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "top_p": 0.9,
        "max_tokens": max_tokens
    }
    r = requests.post(url, headers=headers, json=body, timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f"Groq chat HTTP {r.status_code}: {r.text[:200]}")
    data = r.json()
    return data["choices"][0]["message"]["content"].strip()

def llm_chat_openrouter(prompt: str, model: str = "anthropic/claude-3-haiku") -> str:
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY not set")
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/lybra-bee",
        "X-Title": "AI Blog Generator",
    }
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 1400
    }
    r = requests.post(url, headers=headers, json=body, timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f"OpenRouter chat HTTP {r.status_code}: {r.text[:200]}")
    data = r.json()
    return data["choices"][0]["message"]["content"].strip()

def generate_topic() -> str:
    prompt = (
        "Сгенерируй ОДНУ конкретную тему статьи на русском про самые последние тренды "
        "в ИИ и высоких технологиях (2025). Короткий, техничный заголовок (до 80 символов), "
        "без кавычек."
    )
    # Groq → OpenRouter → список fallback
    try:
        topic = llm_chat_groq(prompt)
        topic = topic.splitlines()[0].strip().strip('"').strip()
        if topic:
            return topic
    except Exception as e:
        print(f"⚠️ Тема через Groq не получена: {e}")
    try:
        topic = llm_chat_openrouter(prompt)
        topic = topic.splitlines()[0].strip().strip('"').strip()
        if topic:
            return topic
    except Exception as e:
        print(f"⚠️ Тема через OpenRouter не получена: {e}")

    fallback = [
        "Мультимодальные модели: от восприятия к действиям",
        "AI-агенты в проде: оркестрация и безопасность",
        "Энергоэффективные нейроморфные вычисления в edge-AI",
        "Практика RAG 2.0 для корпоративных данных",
        "Сжатие LLM: квантование и дистилляция в 2025",
    ]
    return random.choice(fallback)

def generate_article(topic: str) -> Tuple[str, str]:
    prompt = (
        f"Напиши развёрнутую техстатью (400–700 слов) на тему: {topic}.\n"
        "Формат: Markdown, заголовки ##, списки, **жирный** для терминов.\n"
        "Язык: русский, аудитория: разработчики.\n"
        "Освети архитектуры, практику внедрения, риски и метрики качества.\n"
        "Фокус: 2025, реальные подходы, инструменты и паттерны."
    )
    # Groq → OpenRouter → fallback
    try:
        content = llm_chat_groq(prompt, model="llama-3.1-70b-versatile", max_tokens=1600)
        if len(content) > 300:
            return content, "Groq-llama-3.1-70b-versatile"
    except Exception as e:
        print(f"⚠️ Статья через Groq не получена: {e}")

    try:
        content = llm_chat_openrouter(prompt, model="anthropic/claude-3-haiku")
        if len(content) > 300:
            return content, "OpenRouter-claude-3-haiku"
    except Exception as e:
        print(f"⚠️ Статья через OpenRouter не получена: {e}")

    fallback = (
        f"# {topic}\n\n"
        "## Введение\n"
        "Ключевые тренды 2025 года в ИИ меняют подход к проектированию и эксплуатации систем.\n\n"
        "## Архитектура\n"
        "- **Трансформеры**, **мультимодальность**, **RAG**, **инференс на edge**.\n"
        "- Контроль качества: offline-метрики и online-эксперименты.\n\n"
        "## Практика\n"
        "- Деплой через контейнеры и серверлесс.\n"
        "- Наблюдаемость: трассировка токенов, латентность, стоимость.\n\n"
        "## Риски и безопасность\n"
        "- Prompt-инъекции, утечки, мониторинг и политика прав доступа.\n\n"
        "## Выводы\n"
        "Комбинация мультимодальности и экономичного инференса даёт бизнес-ценность уже сегодня."
    )
    return fallback, "fallback-generator"

# ==========
# Генерация изображений
# ==========
def craft_image_prompt(topic: str) -> str:
    """Получаем короткий англ. промпт через Groq/OpenRouter; если не получится — базовый."""
    ask = (
        f"Write a concise (max 2 sentences) English prompt for a futuristic, professional, "
        f"text-free tech illustration matching the article topic: '{topic}'. "
        "Blue/purple palette, abstract AI, neural nets, data flows."
    )
    try:
        return llm_chat_groq(ask, model="llama-3.1-8b-instant", max_tokens=80)
    except Exception:
        pass
    try:
        return llm_chat_openrouter(ask, model="mistralai/mistral-7b-instruct")
    except Exception:
        pass
    return f"Futuristic abstract AI illustration for '{topic}', no text, blue/purple palette, neural networks and data."

def save_image_bytes(topic: str, img_bytes: bytes) -> str:
    slug = generate_slug(topic)
    filename = f"{slug}.jpg"
    full_path = os.path.join(IMAGES_DIR, filename)
    write_file(full_path, img_bytes, binary=True)
    print(f"💾 Изображение сохранено: {full_path}")
    # публичный URL в Hugo (static/** публикуется как /)
    return f"/images/posts/{filename}"

def generate_image_with_groq(prompt: str, topic: str) -> Optional[str]:
    """
    Пытаемся через совместимый endpoint images/generations.
    Если у твоего аккаунта Groq нет image API — этот шаг просто упадёт и мы перейдём к Stability.
    """
    if not GROQ_API_KEY:
        return None
    url = "https://api.groq.com/openai/v1/images/generations"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    body = {"prompt": prompt, "n": 1, "size": "1024x512", "response_format": "b64_json"}
    r = requests.post(url, headers=headers, json=body, timeout=90)
    if r.status_code != 200:
        raise RuntimeError(f"Groq images HTTP {r.status_code}: {r.text[:200]}")
    data = r.json()
    b64 = data["data"][0].get("b64_json")
    if not b64:
        raise RuntimeError("Groq images: empty b64_json")
    img = base64.b64decode(b64)
    return save_image_bytes(topic, img)

def generate_image_with_stability(prompt: str, topic: str) -> Optional[str]:
    if not STABILITYAI_KEY:
        return None
    url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
    headers = {"Authorization": f"Bearer {STABILITYAI_KEY}", "Content-Type": "application/json", "Accept": "application/json"}
    body = {
        "text_prompts": [{"text": prompt, "weight": 1.0}],
        "cfg_scale": 7,
        "height": 512,
        "width": 1024,
        "samples": 1,
        "steps": 30,
        "style_preset": "digital-art"
    }
    r = requests.post(url, headers=headers, json=body, timeout=120)
    if r.status_code != 200:
        raise RuntimeError(f"Stability HTTP {r.status_code}: {r.text[:200]}")
    data = r.json()
    if not data.get("artifacts"):
        raise RuntimeError("Stability: no artifacts")
    img = base64.b64decode(data["artifacts"][0]["base64"])
    return save_image_bytes(topic, img)

def generate_article_image(topic: str) -> Optional[str]:
    print("🎨 Генерация изображения…")
    prompt = craft_image_prompt(topic)
    # Groq → Stability → None
    try:
        path = generate_image_with_groq(prompt, topic)
        if path: return path
    except Exception as e:
        print(f"⚠️ Groq image fail: {e}")
    try:
        path = generate_image_with_stability(prompt, topic)
        if path: return path
    except Exception as e:
        print(f"⚠️ Stability image fail: {e}")
    print("ℹ️ Изображение не создано — публикуем статью без него.")
    return None

# ==========
# Hugo пост
# ==========
def build_frontmatter(topic: str, content_md: str, model_used: str, image_url: Optional[str]) -> str:
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    tags = ["ai", "технологии", "2025", "генеративный-ии", "мультимодальность"]
    fm = {
        "title": topic,
        "date": now,
        "draft": False,
        "description": f"Автоматически сгенерированная статья про: {topic}",
        "tags": tags,
        "categories": ["Технологии"]
    }
    if image_url:
        fm["image"] = image_url
    front = "---\n" + "\n".join(
        [f'title: "{fm["title"]}"',
         f"date: {fm['date']}",
         f"draft: {str(fm['draft']).lower()}",
         f'description: "{fm["description"]}"',
         *( [f'image: "{fm["image"]}"'] if "image" in fm else [] ),
         f"tags: {json.dumps(fm['tags'], ensure_ascii=False)}",
         'categories: ["Технологии"]'
        ]) + "\n---\n\n"
    # Вставим заголовок и тело
    body = f"# {topic}\n\n" + (f"![]({image_url})\n\n" if image_url else "") + content_md + "\n\n---\n" \
           f"**Модель:** {model_used}  \n" \
           f"**Дата:** {now}  \n" \
           f"*Сгенерировано GitHub Actions*"
    return front + body

def write_post(topic: str, content_md: str, model_used: str, image_url: Optional[str]) -> str:
    date = datetime.now().strftime("%Y-%m-%d")
    slug = generate_slug(topic)
    path = f"{POSTS_DIR}/{date}-{slug}.md"
    fm = build_frontmatter(topic, content_md, model_used, image_url)
    write_file(path, fm.encode("utf-8"), binary=True)
    print(f"✅ Статья сохранена: {path}")
    return path

# ==========
# Main
# ==========
def main():
    print("=" * 60)
    print("🤖 AI CONTENT GENERATOR (Groq/OpenRouter + Groq/Stability Images)")
    print("=" * 60)
    ensure_dirs()
    clean_old_articles()

    print(f"🔑 OPENROUTER_API_KEY: {'✅' if OPENROUTER_API_KEY else '❌'}")
    print(f"🔑 GROQ_API_KEY: {'✅' if GROQ_API_KEY else '❌'}")
    print(f"🔑 STABILITYAI_KEY: {'✅' if STABILITYAI_KEY else '❌'}")

    topic = generate_topic()
    print(f"📝 Тема: {topic}")

    image_url = generate_article_image(topic)
    content_md, model_used = generate_article(topic)
    write_post(topic, content_md, model_used, image_url)

    print("🎉 Готово.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        # Не валим job: пускай Workflow продолжит сборку/деплой уже имеющегося
        # (некоторые шаги в workflow помечены как продолжить при ошибке)
        exit(0)
