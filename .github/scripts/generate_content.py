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

# ====== Настройки ======
DEEPAI_KEY = "98c841c4"
HF_TOKEN = "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"

# ====== Генерация темы ======
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

# ====== Основная генерация ======
def generate_content():
    print("🚀 Запуск генерации контента...")
    KEEP_LAST_ARTICLES = 3
    clean_old_articles(KEEP_LAST_ARTICLES)
    
    topic = generate_ai_trend_topic()
    print(f"📝 Актуальная тема 2025: {topic}")

    # Генерация изображения: HuggingFace первым
    image_filename = generate_article_image(topic)
    content, model_used = generate_article_content(topic)

    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    slug = generate_slug(topic)
    filename = f"content/posts/{date}-{slug}.md"

    frontmatter = generate_frontmatter(topic, content, model_used, image_filename)
    
    os.makedirs("content/posts", exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(frontmatter)

    print(f"✅ Статья создана: {filename}")
    return filename

# ====== Генерация текста ======
def generate_article_content(topic):
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    groq_key = os.getenv('GROQ_API_KEY')
    models_to_try = []

    if openrouter_key:
        openrouter_models = [
            "anthropic/claude-3-haiku",
            "google/gemini-pro",
            "mistralai/mistral-7b-instruct",
            "meta-llama/llama-3-8b-instruct"
        ]
        for m in openrouter_models:
            models_to_try.append((f"OpenRouter-{m}", lambda m=m: generate_with_openrouter(openrouter_key, m, topic)))

    if groq_key:
        groq_models = ["llama-3.1-8b-instant", "llama-3.2-1b-preview", "llama-3.2-3b-preview"]
        for m in groq_models:
            models_to_try.append((f"Groq-{m}", lambda m=m: generate_with_groq(groq_key, m, topic)))

    for model_name, gen_func in models_to_try:
        try:
            print(f"🔄 Пробуем: {model_name}")
            result = gen_func()
            if result and len(result.strip()) > 100:
                print(f"✅ Успешно через {model_name}")
                return result, model_name
            time.sleep(1)
        except Exception as e:
            print(f"⚠️ Ошибка {model_name}: {str(e)[:100]}")
    
    print("⚠️ Все API недоступны, создаем заглушку")
    fallback_content = f"# {topic}\n\nАвтоматическая статья-заглушка."
    return fallback_content, "fallback-generator"

def generate_with_openrouter(api_key, model_name, topic):
    prompt = f"Напиши статью на тему: {topic}, 400-600 слов, Markdown, русский, технический стиль"
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        json={"model": model_name, "messages":[{"role":"user","content":prompt}], "max_tokens":1500},
        timeout=30
    )
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content'].strip()
    raise Exception(f"HTTP {response.status_code}")

def generate_with_groq(api_key, model_name, topic):
    prompt = f"Напиши статью на тему: {topic}, 400-600 слов, Markdown, русский, технический стиль"
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model_name, "messages":[{"role":"user","content":prompt}], "max_tokens":1500},
        timeout=30
    )
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content'].strip()
    raise Exception(f"HTTP {response.status_code}: {response.text[:200]}")

# ====== Генерация изображений ======
def generate_article_image(topic):
    generators = [
        ("HuggingFace", generate_image_huggingface),
        ("DeepAI", generate_image_deepai),
        ("Craiyon", generate_image_craiyon),
        ("Lexica", generate_image_lexica),
        ("Artbreeder", generate_image_artbreeder),
        ("Picsum", generate_image_picsum)
    ]
    for name, func in generators:
        print(f"🔄 Пробуем генератор: {name}")
        img = func(topic)
        if img:
            print(f"✅ Успешно сгенерировано изображение через {name}")
            return img
        else:
            print(f"⚠️ {name} вернул None")
    print("⚠️ Не удалось создать изображение, используем заглушку")
    return None

def save_article_image(image_data, topic):
    os.makedirs("assets/images/posts", exist_ok=True)
    slug = generate_slug(topic)
    filename = f"posts/{slug}.png"
    full_path = f"assets/images/{filename}"
    with open(full_path, 'wb') as f:
        f.write(image_data)
    return f"/images/{filename}"

# ====== Реализация генераторов ======
def generate_image_huggingface(topic):
    try:
        url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        payload = {"inputs": topic}
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        if r.status_code == 200:
            return save_article_image(r.content, topic)
    except: pass
    return None

def generate_image_deepai(topic):
    try:
        url = "https://api.deepai.org/api/text2img"
        headers = {"Api-Key": DEEPAI_KEY}
        r = requests.post(url, data={"text": topic}, headers=headers, timeout=30)
        if r.status_code == 200:
            img_url = r.json().get("output_url")
            img_data = requests.get(img_url).content
            return save_article_image(img_data, topic)
    except: pass
    return None

def generate_image_craiyon(topic):
    try:
        url = f"https://api.craiyon.com/v3/?prompt={topic}"
        r = requests.get(url, timeout=30)
        if r.status_code == 200:
            b64 = r.json()['images'][0]
            img_data = base64.b64decode(b64)
            return save_article_image(img_data, topic)
    except: pass
    return None

def generate_image_lexica(topic):
    try:
        r = requests.get(f"https://lexica.art/api/v1/search?q={topic}", timeout=30)
        if r.status_code == 200 and r.json()['images']:
            img_url = r.json()['images'][0]['srcSmall']
            img_data = requests.get(img_url).content
            return save_article_image(img_data, topic)
    except: pass
    return None

def generate_image_artbreeder(topic):
    return generate_image_picsum(topic)

def generate_image_picsum(topic):
    r = requests.get("https://picsum.photos/1024", timeout=30)
    return save_article_image(r.content, topic)

# ====== Утилиты ======
def generate_slug(text):
    text = text.lower()
    text = text.replace(' ', '-')
    text = re.sub(r'[^a-z0-9\-]', '', text)
    text = re.sub(r'-+', '-', text)
    return text[:60].strip('-')

def generate_frontmatter(title, content, model_used, image_url):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    title_safe = title.replace(':',' -').replace('"','').replace("'","")
    fm = [
        "---",
        f'title: "{title_safe}"',
        f"date: {now}",
        "draft: false",
        'tags: ["AI","машинное обучение","технологии","2025"]',
        'categories: ["Искусственный интеллект"]',
        'summary: "Автоматически сгенерированная статья"'
    ]
    if image_url:
        fm.append(f'image: "{image_url}"')
    fm.append("---")
    fm.append(content)
    return "\n".join(fm)

def clean_old_articles(keep_last=3):
    print(f"🧹 Очистка старых статей, оставляем {keep_last} последних...")
    try:
        articles = glob.glob("content/posts/*.md")
        if not articles: return
        articles.sort(key=os.path.getmtime, reverse=True)
        for f in articles[keep_last:]:
            os.remove(f)
            slug = os.path.basename(f).replace('.md','')
            img_path = f"assets/images/posts/{slug}.png"
            if os.path.exists(img_path):
                os.remove(img_path)
    except Exception as e:
        print(f"⚠️ Ошибка очистки: {e}")

# ====== Запуск ======
if __name__ == "__main__":
    generate_content()
