#!/usr/bin/env python3
import os
import json
import requests
import random
from datetime import datetime
import glob
import base64
import time
import urllib.parse

def generate_ai_trend_topic():
    """Генерирует актуальную тему на основе реальных трендов AI 2025"""
    
    current_trends_2025 = [
        "Multimodal AI - интеграция текста, изображений и аудио в единых моделях",
        "AI агенты - автономные системы способные выполнять сложные задачи",
        "Квантовые вычисления и машинное обучение - прорыв в производительности",
        "Нейроморфные вычисления - энергоэффективные архитектуры нейросетей",
        "Generative AI - создание контента, кода и дизайнов искусственным интеллектом",
        "Edge AI - обработка данных на устройстве без облачной зависимости",
        "AI для кибербезопасности - предиктивная защита от угроз",
        "Этичный AI - ответственное развитие и использование искусственного интеллекта",
        "AI в healthcare - диагностика, разработка лекарств и персонализированная медицина",
        "Автономные системы - беспилотный транспорт и робототехника",
        "AI оптимизация - сжатие моделей и ускорение inference",
        "Доверенный AI - объяснимые и прозрачные алгоритмы",
        "AI для климата - оптимизация энергопотребления и экологические решения",
        "Персональные AI ассистенты - индивидуализированные цифровые помощники",
        "AI в образовании - адаптивное обучение и персонализированные учебные планы"
    ]
    
    application_domains = [
        "в веб-разработке и cloud-native приложениях",
        "в мобильных приложениях и IoT экосистемах",
        "в облачных сервисах и распределенных системах",
        "в анализе больших данных и бизнес-аналитике",
        "в компьютерной безопасности и киберзащите",
        "в медицинской диагностике и биотехнологиях",
        "в финансовых технологиях и финтехе",
        "в автономных транспортных системах",
        "в smart city и умной инфраструктуре",
        "в образовательных технологиях и EdTech"
    ]
    
    trend = random.choice(current_trends_2025)
    domain = random.choice(application_domains)
    
    topic_formats = [
        f"{trend} {domain} в 2025 году",
        f"Тенденции 2025: {trend} {domain}",
        f"{trend} - революционные изменения {domain} в 2025",
        f"Как {trend} трансформирует {domain} в 2025 году",
        f"Инновации 2025: {trend} для {domain}",
        f"{trend} - будущее {domain} в 2025 году",
        f"Практическое применение {trend} в {domain} 2025"
    ]
    
    return random.choice(topic_formats)

def generate_content():
    """Генерирует контент статьи через AI API"""
    print("🚀 Запуск генерации контента...")
    
    KEEP_LAST_ARTICLES = 3
    clean_old_articles(KEEP_LAST_ARTICLES)
    
    selected_topic = generate_ai_trend_topic()
    print(f"📝 Актуальная тема 2025: {selected_topic}")
    
    # Генерируем изображение
    image_filename = generate_article_image(selected_topic)
    
    # Генерируем текст статьи
    content, model_used = generate_article_content(selected_topic)
    
    # Создаем файл статьи
    date = datetime.now().strftime("%Y-%m-%d")
    slug = generate_slug(selected_topic)
    filename = f"content/posts/{date}-{slug}.md"
    
    frontmatter = generate_frontmatter(selected_topic, content, model_used, image_filename)
    
    os.makedirs("content/posts", exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(frontmatter)
    
    print(f"✅ Статья создана: {filename}")
    return filename

def generate_article_content(topic):
    """Генерация содержания статьи через доступные API"""
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    groq_key = os.getenv('GROQ_API_KEY')
    
    models_to_try = []
    
    if groq_key:
        print("🔑 Groq API ключ найден")
        groq_models = ["llama-3.1-8b-instant", "llama-3.1-70b-versatile"]
        for model_name in groq_models:
            models_to_try.append((f"Groq-{model_name}", lambda m=model_name: generate_with_groq(groq_key, m, topic)))
    
    if openrouter_key:
        print("🔑 OpenRouter API ключ найден")
        openrouter_models = ["anthropic/claude-3-haiku", "google/gemini-pro"]
        for model_name in openrouter_models:
            models_to_try.append((model_name, lambda m=model_name: generate_with_openrouter(openrouter_key, m, topic)))
    
    for model_name, generate_func in models_to_try:
        try:
            print(f"🔄 Пробуем: {model_name}")
            result = generate_func()
            if result and len(result.strip()) > 100:
                print(f"✅ Успешно через {model_name}")
                return result, model_name
            time.sleep(1)
        except Exception as e:
            print(f"⚠️ Ошибка {model_name}: {str(e)[:100]}")
            continue
    
    fallback_content = f"""# {topic}

## Введение
{topic} - это важное направление в развитии искусственного интеллекта на 2025 год.

## Основные аспекты
- **Технологические инновации**: {topic} включает передовые разработки в области AI
- **Практическое применение**: Технология находит применение в различных отраслях
- **Перспективы развития**: Ожидается значительный рост в ближайшие годы
"""
    return fallback_content, "fallback-generator"

def generate_with_groq(api_key, model_name, topic):
    prompt = f"""Напиши развернутую техническую статью на тему: "{topic}"."""
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        },
        json={"model": model_name, "messages": [{"role": "user", "content": prompt}], "max_tokens": 1500},
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get('choices'):
            return data['choices'][0]['message']['content'].strip()
    raise Exception(f"HTTP {response.status_code}: {response.text[:200]}")

def generate_with_openrouter(api_key, model_name, topic):
    prompt = f"""Напиши развернутую техническую статью на тему: "{topic}"."""
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        json={"model": model_name, "messages": [{"role": "user", "content": prompt}], "max_tokens": 1500},
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get('choices'):
            return data['choices'][0]['message']['content'].strip()
    raise Exception(f"HTTP {response.status_code}")

def generate_article_image(topic):
    """Генерируем изображение через Groq или Stability AI"""
    print("🎨 Генерация изображения...")
    image_prompt = generate_image_prompt_with_groq(topic)
    groq_key = os.getenv('GROQ_API_KEY')
    stability_key = os.getenv('STABILITYAI_KEY')
    
    if groq_key:
        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/images/generations",
                headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                json={"model": "llama-3.1-8b-instant", "prompt": image_prompt, "size": "1024x512"}
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("data") and len(data["data"]) > 0:
                    image_data = base64.b64decode(data["data"][0]["b64_json"])
                    return save_article_image(image_data, topic)
        except Exception as e:
            print(f"⚠️ Ошибка Groq Image: {e}")
    
    if stability_key:
        try:
            url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
            headers = {"Authorization": f"Bearer {stability_key}", "Content-Type": "application/json"}
            payload = {"text_prompts": [{"text": image_prompt}], "width": 1024, "height": 512, "samples": 1}
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if 'artifacts' in data and data['artifacts']:
                    image_data = base64.b64decode(data['artifacts'][0]['base64'])
                    return save_article_image(image_data, topic)
        except Exception as e:
            print(f"⚠️ Ошибка Stability AI Image: {e}")
    
    print("ℹ️ Не удалось сгенерировать изображение, пропускаем")
    return None

def generate_image_prompt_with_groq(topic):
    return f"Modern technology illustration for article about {topic}. Futuristic, professional, AI theme."

def save_article_image(image_data, topic):
    try:
        os.makedirs("assets/images/posts", exist_ok=True)
        slug = generate_slug(topic)
        filename = f"posts/{slug}.jpg"
        full_path = f"assets/images/{filename}"
        with open(full_path, 'wb') as f:
            f.write(image_data)
        print(f"💾 Изображение сохранено: {filename}")
        return f"/images/{filename}"
    except Exception as e:
        print(f"❌ Ошибка сохранения изображения: {e}")
        return None

def clean_old_articles(keep_last=3):
    articles = glob.glob("content/posts/*.md")
    articles.sort(key=os.path.getmtime, reverse=True)
    for article_path in articles[keep_last:]:
        try:
            os.remove(article_path)
            slug = os.path.basename(article_path).replace('.md','')
            img_path = f"assets/images/posts/{slug}.jpg"
            if os.path.exists(img_path):
                os.remove(img_path)
        except: pass

def generate_slug(topic):
    slug = topic.lower().replace(" ", "-")
    return "".join(c for c in slug if c.isalnum() or c=="-")[:50]

def generate_frontmatter(topic, content, model_used, image_filename=None):
    current_time = datetime.now()
    tags = ["искусственный-интеллект","технологии","инновации","2025","ai"]
    image_section = f"image: {image_filename}\n" if image_filename else ""
    return f"""---
title: "{topic}"
date: {current_time.strftime("%Y-%m-%dT%H:%M:%SZ")}
draft: false
description: "Автоматически сгенерированная статья о {topic}"
{image_section}tags: {json.dumps(tags, ensure_ascii=False)}
categories: ["Технологии"]
---

# {topic}

{f'![]({image_filename})' if image_filename else ''}

{content}

---

### 🔧 Технические детали

- **Модель AI:** {model_used}
- **Дата генерации:** {current_time.strftime("%d.%m.%Y %H:%M UTC")}
- **Тема:** {topic}
- **Год актуальности:** 2025
- **Статус:** Автоматическая генерация

> *Сгенерировано через GitHub Actions*
"""

if __name__ == "__main__":
    try:
        print("="*50)
        print("🤖 AI CONTENT GENERATOR")
        print("="*50)
        generate_content()
        print("="*50)
        print("✅ Генерация завершена успешно!")
        print("="*50)
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        exit(1)
