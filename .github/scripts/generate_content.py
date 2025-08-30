#!/usr/bin/env python3
import os
import json
import requests
import random
from datetime import datetime, timezone
import glob
import base64
import time
import urllib.parse
import re
import shutil

def generate_ai_trend_topic():
    """Генерирует актуальную тему на основе реальных трендов AI 2025"""
    
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

def clean_old_articles(keep_last=3):
    """Оставляет только последние N статей и удаляет проблемные файлы"""
    print(f"🧹 Очистка старых статей, оставляем {keep_last} последних...")
    
    try:
        # Удаляем всю папку content и создаем заново
        content_dir = "content"
        if os.path.exists(content_dir):
            print(f"🗑️ Полная очистка папки content")
            shutil.rmtree(content_dir)
        
        # Создаем чистую структуру
        os.makedirs("content/posts", exist_ok=True)
        
        # Создаем обязательные файлы
        with open("content/_index.md", "w", encoding="utf-8") as f:
            f.write("---\ntitle: \"Главная\"\n---")
        
        with open("content/posts/_index.md", "w", encoding="utf-8") as f:
            f.write("---\ntitle: \"Статьи\"\n---")
            
        print("✅ Создана чистая структура content")

    except Exception as e:
        print(f"⚠️ Ошибка при очистке: {e}")

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
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
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
    
    # Добавляем Groq модели (актуальные версии)
    if groq_key:
        print("🔑 Groq API ключ найден")
        groq_models = [
            "llama-3.1-8b-instant",
            "llama-3.2-1b-preview",
            "llama-3.2-3b-preview",
            "mixtral-8x7b-32768",
            "gemma2-9b-it"
        ]
        for model_name in groq_models:
            models_to_try.append((f"Groq-{model_name}", lambda m=model_name: generate_with_groq(groq_key, m, topic)))
    
    # Добавляем OpenRouter модели
    if openrouter_key:
        print("🔑 OpenRouter API ключ найден")
        openrouter_models = [
            "anthropic/claude-3-haiku",
            "google/gemini-pro", 
            "mistralai/mistral-7b-instruct",
            "meta-llama/llama-3-8b-instruct",
        ]
        for model_name in openrouter_models:
            models_to_try.append((model_name, lambda m=model_name: generate_with_openrouter(openrouter_key, m, topic)))
    
    # Пробуем все доступные модели
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
    
    # Fallback - создаем простой контент
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

def generate_with_groq(api_key, model_name, topic):
    """Генерация через Groq API"""
    prompt = f"""Напиши развернутую техническую статью на тему: "{topic}".

Требования:
- Объем: 400-600 слов
- Формат: Markdown с подзаголовками ##
- Язык: русский, технический стиль
- Аудитория: разработчики и IT-специалисты
- Фокус на 2025 год и современные технологии

Структура:
1. Введение и актуальность темы
2. Технические особенности и архитектура
3. Примеры использования и кейсы
4. Перспективы развития
5. Заключение и выводы

Используй:
- **Жирный шрифт** для ключевых терминов
- Маркированные списки для перечислений
- Конкретные примеры и технические детали"""

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        },
        json={
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1500,
            "temperature": 0.7,
            "top_p": 0.9
        },
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get('choices'):
            content = data['choices'][0]['message']['content']
            return content.strip()
    
    raise Exception(f"HTTP {response.status_code}: {response.text[:200]}")

def generate_with_openrouter(api_key, model_name, topic):
    """Генерация через OpenRouter"""
    prompt = f"""Напиши развернутую техническую статья на тему: "{topic}".

Требования:
- Объем: 400-600 слов
- Формат: Markdown с подзаголовками
- Язык: русский
- Стиль: технический, для разработчиков
- Фокус на 2025 год

Структура:
1. Введение
2. Основная часть с техническими деталями
3. Примеры использования
4. Заключение

Используй:
- **Жирный шрифт** для терминов
- Списки для перечисления
- Конкретные примеры и технологии"""
    
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://github.com/lybra-bee",
            "X-Title": "AI Blog Generator"
        },
        json={
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1500,
            "temperature": 0.7
        },
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get('choices'):
            content = data['choices'][0]['message']['content']
            return content.strip()
    
    raise Exception(f"HTTP {response.status_code}")

def generate_article_image(topic):
    """Генерация изображения через доступные API"""
    print("🎨 Генерация изображения...")
    
    image_prompt = generate_image_prompt(topic)
    print(f"📝 Промпт: {image_prompt}")
    
    # Порядок приоритета API
    apis_to_try = [
        ("DeepAI", lambda: generate_with_deepai("98c841c4-f3dc-42b0-b02e-de2fcdebd001", image_prompt, topic)),
        ("Stability AI", lambda: generate_with_stability_ai(os.getenv('STABILITYAI_KEY'), image_prompt, topic)),
        ("Hugging Face", lambda: generate_with_huggingface("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", image_prompt, topic)),
        ("Placeholder", lambda: generate_placeholder_image(topic))
    ]
    
    for api_name, api_func in apis_to_try:
        try:
            print(f"🔄 Пробуем {api_name}...")
            result = api_func()
            if result:
                print(f"✅ Успешно через {api_name}")
                return result
            else:
                print(f"⚠️ {api_name} не вернул результат")
        except Exception as e:
            print(f"⚠️ {api_name} ошибка: {str(e)[:100]}")
            continue
    
    print("❌ Все API недоступны")
    return None

def generate_with_deepai(api_key, prompt, topic):
    """Генерация через DeepAI"""
    print("🔄 Генерация через DeepAI...")
    
    try:
        url = "https://api.deepai.org/api/text2img"
        
        headers = {
            "Api-Key": api_key
        }
        
        data = {
            "text": prompt,
            "grid_size": "1",
            "width": "800",
            "height": "400",
            "image_generator_version": "standard"
        }
        
        print("📡 Отправляем запрос к DeepAI...")
        response = requests.post(url, headers=headers, data=data, timeout=60)
        
        print(f"📊 DeepAI status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ DeepAI response: {data}")
            
            if 'output_url' in data and data['output_url']:
                print("📥 Загружаем изображение...")
                image_response = requests.get(data['output_url'], timeout=60)
                
                if image_response.status_code == 200:
                    filename = save_article_image(image_response.content, topic)
                    if filename:
                        print("✅ Изображение создано через DeepAI")
                        return filename
                else:
                    print(f"❌ Ошибка загрузки изображения: {image_response.status_code}")
            else:
                print("❌ Нет output_url в ответе DeepAI")
        else:
            print(f"❌ Ошибка DeepAI API: {response.text}")
            
    except Exception as e:
        print(f"❌ Исключение в DeepAI API: {e}")
    
    return None

def generate_with_stability_ai(api_key, prompt, topic):
    """Генерация через Stability AI"""
    if not api_key:
        return None
        
    try:
        url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        payload = {
            "text_prompts": [{"text": prompt, "weight": 1.0}],
            "cfg_scale": 7,
            "height": 1024,
            "width": 1024,
            "samples": 1,
            "steps": 30,
            "style_preset": "digital-art"
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            if 'artifacts' in data and data['artifacts']:
                image_data = base64.b64decode(data['artifacts'][0]['base64'])
                filename = save_article_image(image_data, topic)
                if filename:
                    print("✅ Изображение создано через Stability AI")
                    return filename
        else:
            print(f"❌ Stability AI error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка Stability AI: {e}")
    
    return None

def generate_with_huggingface(token, prompt, topic):
    """Генерация через Hugging Face API"""
    print(f"🔄 Генерация через Hugging Face...")
    
    models = [
        "runwayml/stable-diffusion-v1-5",
        "stabilityai/stable-diffusion-2-1", 
        "prompthero/openjourney"
    ]
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    for model in models:
        try:
            url = f"https://api-inference.huggingface.co/models/{model}"
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "num_inference_steps": 20,
                    "guidance_scale": 7.5,
                    "width": 512,
                    "height": 512
                }
            }
            
            print(f"🎨 Пробуем модель: {model}")
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                filename = save_article_image(response.content, topic)
                if filename:
                    print(f"✅ Успешно через {model}")
                    return filename
            elif response.status_code == 503:
                print(f"⏳ Модель {model} загружается...")
                continue
            else:
                print(f"❌ Ошибка {model}: {response.status_code}")
                
        except Exception as e:
            print(f"⚠️ Ошибка {model}: {e}")
            continue
    
    return None

def generate_placeholder_image(topic):
    """Создает placeholder изображение"""
    try:
        print("🎨 Создаем placeholder изображение...")
        
        encoded_topic = urllib.parse.quote(topic[:30])
        image_url = f"https://placehold.co/800x400/0f172a/6366f1/png?text={encoded_topic}"
        
        response = requests.get(image_url, timeout=30)
        if response.status_code == 200:
            filename = save_article_image(response.content, topic)
            if filename:
                print("✅ Placeholder изображение создано")
                return filename
    except Exception as e:
        print(f"❌ Ошибка создания placeholder: {e}")
    
    return None

def generate_image_prompt(topic):
    """Генерирует промпт для изображения на английском"""
    prompts = [
        f"Technology illustration for article about {topic}. Modern futuristic style, abstract technology concept with neural networks, AI, data visualization. Blue and purple color scheme, professional digital art, no text",
        f"AI technology concept art for {topic}. Futuristic cyberpunk style, glowing neural networks, holographic interfaces, digital particles. Dark background with vibrant colors, cinematic lighting",
        f"Abstract technology background for {topic}. Geometric shapes, circuit patterns, data streams, glowing connections. Professional corporate style, clean design, technology theme",
        f"Futuristic AI concept for {topic}. Digital brain, neural connections, data flow, quantum computing elements. Sci-fi style, vibrant colors, depth of field"
    ]
    
    return random.choice(prompts)

def save_article_image(image_data, topic):
    """Сохраняет сгенерированное изображение"""
    try:
        os.makedirs("assets/images/posts", exist_ok=True)
        slug = generate_slug(topic)
        
        # Определяем формат по содержимому
        if image_data.startswith(b'\xff\xd8\xff'):
            ext = "jpg"
        elif image_data.startswith(b'\x89PNG'):
            ext = "png"
        else:
            ext = "png"  # По умолчанию PNG
            
        filename = f"posts/{slug}.{ext}"
        full_path = f"assets/images/{filename}"
        
        with open(full_path, 'wb') as f:
            f.write(image_data)
        
        print(f"💾 Изображение сохранено: {filename}")
        return f"/images/{filename}"
        
    except Exception as e:
        print(f"❌ Ошибка сохранения изображения: {e}")
        return None

def generate_slug(text):
    """Создает безопасный slug из текста"""
    text = text.lower()
    text = text.replace(' ', '-')
    text = text.replace('--', '-')
    text = re.sub(r'[^a-z0-9\-]', '', text)
    text = re.sub(r'-+', '-', text)
    text = text.strip('-')
    return text[:60]

def generate_frontmatter(title, content, model_used, image_url):
    """Генерирует frontmatter для Hugo с безопасным экранированием"""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    escaped_title = title
    escaped_title = escaped_title.replace(':', ' -')
    escaped_title = escaped_title.replace('"', '')
    escaped_title = escaped_title.replace("'", "")
    escaped_title = escaped_title.replace('\\', '')
    
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

if __name__ == "__main__":
    generate_content()
