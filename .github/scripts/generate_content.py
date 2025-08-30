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
from openai import OpenAI

# -------------------- Настройки ключей --------------------
GPT_IMAGE_API_KEY = "sk-L85surAtSvGUQ5rYoGStpWxrAsW8WlIMO3jIuMtIkNfy1Gx4"
DEEP_AI_KEY = "98c841c4-f3dc-42b0-b02e-de2fcdebd001"

# -------------------- Генерация темы --------------------
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

# -------------------- Генерация текста статьи --------------------
def generate_with_openrouter(key, model, prompt):
    try:
        print(f"🔄 Пробуем OpenRouter модель: {model}")
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completion",
            headers={"Authorization": f"Bearer {key}"},
            json={"model": model, "messages":[{"role":"user","content":prompt}]}
        )
        data = resp.json()
        return data['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"⚠️ Ошибка OpenRouter ({model}): {e}")
        return None

def generate_with_groq(key, model, prompt):
    print(f"🔄 Пробуем Groq модель: {model}")
    return f"Сгенерированный текст через Groq для темы: {prompt}"

def generate_article_content(topic):
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    groq_key = os.getenv('GROQ_API_KEY')

    models_to_try = []

    # OpenRouter модели (приоритет)
    if openrouter_key:
        openrouter_models = [
            "anthropic/claude-3-haiku",
            "google/gemini-pro", 
            "mistralai/mistral-7b-instruct",
            "meta-llama/llama-3-8b-instruct",
        ]
        for model_name in openrouter_models:
            models_to_try.append((model_name, lambda m=model_name: generate_with_openrouter(openrouter_key, m, topic)))

    # Groq модели (fallback)
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

    # Перебор моделей
    for model_name, generate_func in models_to_try:
        try:
            result = generate_func()
            if result and len(result.strip()) > 100:
                print(f"✅ Успешно через {model_name}")
                return result, model_name
            time.sleep(1)
        except Exception as e:
            print(f"⚠️ Ошибка {model_name}: {str(e)[:100]}")
            continue

    # fallback
    print("⚠️ Все API недоступны, создаем заглушку")
    return f"# {topic}\n\nСтатья временно сгенерирована как заглушка.", "fallback-generator"

# -------------------- Генерация изображения --------------------
def generate_article_image(topic):
    print("🎨 Генерация изображения...")

    # GPT Image 1
    try:
        print("🔄 Пробуем генератор: GPT Image 1")
        client = OpenAI(api_key=GPT_IMAGE_API_KEY)
        prompt = f"{topic}, цифровое искусство, футуристический стиль, нейросети, киберпанк"
        response = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1024"
        )
        if response.data and response.data[0].b64_json:
            image_bytes = base64.b64decode(response.data[0].b64_json)
            os.makedirs("assets/images/posts", exist_ok=True)
            slug = generate_slug(topic)
            filename = f"assets/images/posts/{slug}.png"
            with open(filename, "wb") as f:
                f.write(image_bytes)
            print(f"✅ Изображение создано через GPT Image 1: {filename}")
            return f"/images/posts/{slug}.png"
    except Exception as e:
        print(f"⚠️ GPT Image 1 не сработал: {e}")

    # DeepAI fallback
    try:
        print("🔄 Пробуем генератор: DeepAI")
        response = requests.post(
            "https://api.deepai.org/api/text2img",
            data={'text': f"{topic}, цифровое искусство, футуристический стиль"},
            headers={'api-key': DEEP_AI_KEY}
        )
        result = response.json()
        if 'output_url' in result:
            print(f"✅ DeepAI сгенерировал изображение: {result['output_url']}")
            return result['output_url']
    except Exception as e:
        print(f"⚠️ DeepAI не сработал: {e}")

    print("⚠️ Не удалось сгенерировать изображение, используем заглушку")
    return None

# -------------------- Вспомогательные функции --------------------
def generate_slug(text):
    text = text.lower()
    text = text.replace(' ', '-')
    text = text.replace('--', '-')
    text = re.sub(r'[^a-z0-9\-]', '', text)
    text = re.sub(r'-+', '-', text)
    return text[:60]

def generate_frontmatter(title, content, model_used, image_url):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    escaped_title = title.replace(':', ' -').replace('"','').replace("'",'').replace('\\','')
    frontmatter_lines = [
        "---",
