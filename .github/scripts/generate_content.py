#!/usr/bin/env python3
import os
import json
import requests
import random
from datetime import datetime, timezone
import glob
import base64
import time
import re

# ======== ТЕМЫ И ДОМЕНЫ ========
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
        "AI в образовании адаптивное обучение и персонализированные учебные планы"
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
        "в образовательных технологиях и EdTech"
    ]
    
    trend = random.choice(current_trends_2025)
    domain = random.choice(application_domains)
    
    topic_formats = [
        f"{trend} {domain} в 2025 году",
        f"Тенденции 2025 {trend} {domain}",
        f"{trend} революционные изменения {domain} в 2025",
        f"Как {trend} трансформирует {domain} в 2025 году",
        f"Инновации 2025 {trend} для {domain}",
        f"{trend} будущее {domain} в 2025 году",
        f"Практическое применение {trend} в {domain} 2025"
    ]
    
    return random.choice(topic_formats)

# ======== СЛУЧАЙНЫЙ SLUG ========
def generate_slug(text):
    text = text.lower()
    text = text.replace(' ', '-')
    text = text.replace('--', '-')
    text = re.sub(r'[^a-z0-9\-]', '', text)
    text = re.sub(r'-+', '-', text)
    text = text.strip('-')
    return text[:60]

# ======== FRONTMATTER ========
def generate_frontmatter(title, content, model_used, image_url):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    escaped_title = title.replace(':', ' -').replace('"', '').replace("'", "").replace('\\','')
    frontmatter_lines = [
        "---",
        f'title: "{escaped_title}"',
        f"date: {now}",
        "draft: false",
        'tags: ["AI", "машинное обучение", "технологии", "2025"]',
        'categories: ["Искусственный интеллект"]',
        'summary: "Автоматически сгенерированная статья об искусственном интеллекте"'
    ]
    if image_url:
        frontmatter_lines.append(f'image: "{image_url}"')
    frontmatter_lines.append("---")
    frontmatter_lines.append(content)
    return "\n".join(frontmatter_lines)

# ======== УДАЛЕНИЕ СТАРЫХ СТАТЕЙ ========
def clean_old_articles(keep_last=3):
    print(f"🧹 Очистка старых статей, оставляем {keep_last} последних...")
    try:
        articles = glob.glob("content/posts/*.md")
        if not articles:
            print("📁 Нет статей для очистки")
            return
        articles.sort(key=os.path.getmtime, reverse=True)
        articles_to_keep = articles[:keep_last]
        articles_to_delete = articles[keep_last:]
        print(f"📊 Всего статей: {len(articles)}")
        print(f"💾 Сохраняем: {len(articles_to_keep)}")
        print(f"🗑️ Удаляем: {len(articles_to_delete)}")
        for article_path in articles_to_delete:
            try:
                os.remove(article_path)
                print(f"❌ Удалено: {os.path.basename(article_path)}")
                slug = os.path.basename(article_path).replace('.md', '')
                image_path = f"assets/images/posts/{slug}.png"
                if os.path.exists(image_path):
                    os.remove(image_path)
                    print(f"❌ Удалено изображение: {slug}.png")
            except Exception as e:
                print(f"⚠️ Ошибка удаления {article_path}: {e}")
    except Exception as e:
        print(f"⚠️ Ошибка при очистке статей: {e}")

# ======== ГЕНЕРАЦИЯ ИЗОБРАЖЕНИЙ ========
def generate_image_huggingface(topic):
    HF_TOKEN = "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"
    print("🔄 Пробуем генератор: HuggingFace")
    try:
        url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        payload = {"inputs": topic, "options": {"wait_for_model": True}}
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        if r.status_code == 200:
            data = r.content
            filename = save_article_image(data, topic)
            return filename
        else:
            print(f"⚠️ Hugging Face не сработал: {r.status_code}")
            return None
    except Exception as e:
        print(f"⚠️ Hugging Face ошибка: {e}")
        return None

def generate_image_deepai(topic):
    DEEPAI_KEY = "98c841c4"
    print("🔄 Пробуем генератор: DeepAI")
    try:
        r = requests.post("https://api.deepai.org/api/text2img",
                          data={'text': topic},
                          headers={'api-key': DEEPAI_KEY}, timeout=30)
        if r.status_code == 200:
            data = r.json()
            if 'output_url' in data:
                return data['output_url']
        return None
    except Exception as e:
        print(f"⚠️ DeepAI вернул None: {e}")
        return None

def generate_image_craiyon(topic):
    print("🔄 Пробуем генератор: Craiyon")
    return None  # Простейший заглушка

def generate_image_lexica(topic):
    print("🔄 Пробуем генератор: Lexica")
    return None

def generate_image_artbreeder(topic):
    print("🔄 Пробуем генератор: Artbreeder")
    return f"/images/posts/{generate_slug(topic)}.png"  # Заглушка

def save_article_image(image_data, topic):
    try:
        os.makedirs("assets/images/posts", exist_ok=True)
        slug = generate_slug(topic)
        filename = f"posts/{slug}.png"
        full_path = f"assets/images/{filename}"
        if isinstance(image_data, bytes):
            with open(full_path, 'wb') as f:
                f.write(image_data)
        print(f"✅ Изображение создано через генератор и сохранено: {filename}")
        return f"/images/{filename}"
    except Exception as e:
        print(f"❌ Ошибка сохранения изображения: {e}")
        return None

def generate_article_image(topic):
    generators = [
        generate_image_huggingface,
        generate_image_deepai,
        generate_image_craiyon,
        generate_image_lexica,
        generate_image_artbreeder
    ]
    for gen in generators:
        try:
            image_filename = gen(topic)
            if image_filename:
                return image_filename
        except Exception as e:
            print(f"⚠️ {gen.__name__} вернул None: {e}")
    print("⚠️ Генерация изображения не удалась, продолжаем без изображения")
    return None

# ======== ГЕНЕРАЦИЯ СТАТЬИ ========
def generate_article_content(topic):
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    groq_key = os.getenv('GROQ_API_KEY')
    models_to_try = []

    if openrouter_key:
        openrouter_models = [
            "anthropic/claude-3-haiku",
            "google/gemini-pro", 
            "mistralai/mistral-7b-instruct",
            "meta-llama/llama-3-8b-instruct",
        ]
        for model_name in openrouter_models:
            models_to_try.append((model_name, lambda m=model_name: generate_with_openrouter(openrouter_key, m, topic)))

    if groq_key:
        groq_models = [
            "llama-3.1-8b-instant",
            "llama-3.2-1b-preview",
            "llama-3.2-3b-preview",
            "mixtral-8x7b-32768",
            "gemma2-9b-it"
        ]
        for model_name in groq_models:
            models_to_try.append((f"Groq-{model_name}", lambda m=model_name: generate_with_groq(groq_key, m, topic)))

    for model_name, generate_func in models_to_try:
        try:
            print(f"🔄 Пробуем: {model_name}")
            result = generate_func()
            if isinstance(result, tuple):
                content_str = result[0]
            else:
                content_str = result
            if content_str and len(content_str.strip()) > 100:
                print(f"✅ Успешно через {model_name}")
                return content_str, model_name
            time.sleep(1)
        except Exception as e:
            print(f"⚠️ Ошибка {model_name}: {str(e)[:100]}")
            continue

    print("⚠️ Все API недоступны, создаем заглушку")
    fallback_content = f"""# {topic}

## Введение
{topic} - это важное направление в развитии искусственного интеллекта на 2025 год.

## Основные аспекты
- **Технологические инновации**: {topic} включает передовые разработки в области AI
- **Практическое применение**: Технология находит применение в различных отраслях
- **Перспективы развития**: Ожидается значительный рост в ближайшие годы

## Технические детали
Модели искусственного интеллекта для {topic} используют современные архитектуры нейросетей.

## Заключение
{topic} представляет собой ключевое направление развития искусственного интеллекта.
"""
    return fallback_content, "fallback-generator"

def generate_with_openrouter(api_key, model_name, topic):
    prompt = f"""Напиши развернутую техническую статью на тему: "{topic}"."""
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type":"application/json"},
        json={"model": model_name, "messages":[{"role":"user","content":prompt}], "max_tokens":1500, "temperature":0.7},
        timeout=30
    )
    data = response.json()
    if "choices" in data and len(data["choices"]) > 0:
        return data["choices"][0]["message"]["content"]
    return None

def generate_with_groq(api_key, model_name, topic):
    prompt = f"Напиши статью: {topic}"
    response = requests.post(
        f"https://api.groq.ai/v1/generate?model={model_name}",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"prompt": prompt, "max_output_tokens":1500},
        timeout=30
    )
    data = response.json()
    if "output_text" in data:
        return data["output_text"]
    return None

# ======== MAIN ========
def generate_content():
    print("🚀 Запуск генерации контента...")
    clean_old_articles(keep_last=3)

    topic = generate_ai_trend_topic()
    print(f"📝 Актуальная тема 2025: {topic}")

    image_filename = generate_article_image(topic)

    content, model_used = generate_article_content(topic)

    slug = generate_slug(topic)
    filename = f"content/posts/{slug}.md"
    frontmatter = generate_frontmatter(topic, content, model_used, image_filename)

    os.makedirs("content/posts", exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(frontmatter)

    print(f"✅ Статья создана: {filename}")

if __name__ == "__main__":
    generate_content()
