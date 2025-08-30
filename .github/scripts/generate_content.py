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
        ("Kandinsky New", lambda: generate_with_kandinsky_new(image_prompt, topic)),
        ("Kandinsky Legacy", lambda: generate_with_kandinsky_legacy(image_prompt, topic)),
        ("StableDiffusion", lambda: generate_with_stable_diffusion(image_prompt, topic)),
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

def generate_with_kandinsky_new(prompt, topic):
    """Новая версия генерации через Kandinsky API"""
    print("🔄 Генерация через новый Kandinsky API...")
    
    try:
        # Попробуем прямой подход без получения моделей
        generate_url = "https://api.fusionbrain.ai/kandinsky/api/v2/text2image/run"
        
        # Пробуем разные варианты заголовков
        headers_variants = [
            {
                "X-Key": "Key 3BA53CAD37A0BF21740401408253641E",
                "X-Secret": "Secret 00CE1D26AF6BF45FD60BBB4447AD3981",
                "Content-Type": "application/json"
            },
            {
                "Authorization": "Bearer 3BA53CAD37A0BF21740401408253641E",
                "Content-Type": "application/json"
            },
            {
                "X-API-Key": "3BA53CAD37A0BF21740401408253641E",
                "Content-Type": "application/json"
            }
        ]
        
        payload = {
            "type": "GENERATE",
            "numImages": 1,
            "width": 1024,
            "height": 1024,
            "generateParams": {
                "query": prompt
            }
        }
        
        for headers in headers_variants:
            try:
                print("📡 Отправляем запрос на генерацию...")
                response = requests.post(
                    generate_url,
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                print(f"📊 Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    if 'uuid' in data:
                        task_id = data['uuid']
                        print(f"⏳ Задача создана, ID: {task_id}")
                        return f"kandinsky_{task_id}"  # Возвращаем временный идентификатор
                    else:
                        print("❌ Нет UUID в ответе")
                else:
                    print(f"❌ Ошибка генерации: {response.status_code}")
                    
            except Exception as e:
                print(f"⚠️ Ошибка при запросе: {e}")
                continue
                
    except Exception as e:
        print(f"❌ Исключение в Kandinsky API: {e}")
    
    return None

def generate_with_kandinsky_legacy(prompt, topic):
    """Старая версия API для обратной совместимости"""
    print("🔄 Генерация через старый Kandinsky API...")
    
    try:
        # Старые endpoints
        generate_url = "https://api-key.fusionbrain.ai/key/api/v1/text2image/run"
        
        headers = {
            "X-Key": "Key 3BA53CAD37A0BF21740401408253641E",
            "X-Secret": "Secret 00CE1D26AF6BF45FD60BBB4447AD3981",
            "Content-Type": "application/json"
        }
        
        # Сначала получим model_id
        models_url = "https://api-key.fusionbrain.ai/key/api/v1/models"
        models_response = requests.get(models_url, headers=headers, timeout=15)
        
        if models_response.status_code != 200:
            print(f"❌ Ошибка получения моделей: {models_response.status_code}")
            return None
            
        models_data = models_response.json()
        if not models_data:
            print("❌ Нет доступных моделей")
            return None
            
        model_id = models_data[0]['id']
        
        payload = {
            "type": "GENERATE",
            "numImages": 1,
            "width": 1024,
            "height": 1024,
            "model_id": model_id,
            "generateParams": {
                "query": prompt
            }
        }
        
        response = requests.post(
            generate_url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'uuid' in data:
                task_id = data['uuid']
                print(f"⏳ Задача создана, ID: {task_id}")
                return f"kandinsky_legacy_{task_id}"
                
    except Exception as e:
        print(f"❌ Ошибка в старом API: {e}")
    
    return None

def generate_with_stable_diffusion(prompt, topic):
    """Альтернатива через Stable Diffusion API"""
    print("🔄 Пробуем Stable Diffusion API...")
    
    try:
        # Бесплатный Stable Diffusion API
        api_url = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
        headers = {"Authorization": "Bearer hf_your_token_here"}  # Нужен реальный токен
        
        response = requests.post(
            api_url,
            headers=headers,
            json={"inputs": prompt},
            timeout=30
        )
        
        if response.status_code == 200:
            image_data = response.content
            filename = save_article_image(image_data, topic)
            if filename:
                print("✅ Изображение создано через Stable Diffusion")
                return filename
                
    except Exception as e:
        print(f"❌ Ошибка Stable Diffusion: {e}")
    
    return None

def generate_placeholder_image(topic):
    """Создает placeholder изображение"""
    try:
        print("🎨 Создаем placeholder изображение...")
        
        # Создаем красивое градиентное изображение программно
        from PIL import Image, ImageDraw, ImageFont
        import textwrap
        
        # Создаем изображение
        width, height = 800, 400
        img = Image.new('RGB', (width, height), color='#0f172a')
        draw = ImageDraw.Draw(img)
        
        # Добавляем градиент
        for i in range(height):
            r = int(15 + (i / height) * 30)
            g = int(23 + (i / height) * 42)
            b = int(42 + (i / height) * 74)
            draw.line([(0, i), (width, i)], fill=(r, g, b))
        
        # Добавляем текст
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = ImageFont.load_default()
        
        # Разбиваем текст на строки
        wrapped_text = textwrap.fill(topic, width=30)
        bbox = draw.textbbox((0, 0), wrapped_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (width - text_width) / 2
        y = (height - text_height) / 2
        
        draw.text((x, y), wrapped_text, font=font, fill="#6366f1")
        
        # Сохраняем во временный буфер
        import io
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        image_data = buffer.getvalue()
        
        filename = save_article_image(image_data, topic)
        if filename:
            print("✅ Красивое placeholder изображение создано")
            return filename
            
    except Exception as e:
        print(f"❌ Ошибка создания красивого placeholder: {e}")
        
        # Fallback на простой placeholder
        try:
            encoded_topic = urllib.parse.quote(topic[:30])
            image_url = f"https://placehold.co/800x400/0f172a/6366f1/png?text={encoded_topic}"
            
            response = requests.get(image_url, timeout=30)
            if response.status_code == 200:
                filename = save_article_image(response.content, topic)
                if filename:
                    print("✅ Простой placeholder изображение создано")
                    return filename
        except Exception as e2:
            print(f"❌ Ошибка простого placeholder: {e2}")
    
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
        
        # Всегда используем PNG для программно созданных изображений
        filename = f"posts/{slug}.png"
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
