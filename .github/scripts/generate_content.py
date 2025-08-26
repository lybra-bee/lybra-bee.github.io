#!/usr/bin/env python3
import os
import json
import requests
import random
from datetime import datetime
import glob
import base64
import time

def get_gigachat_token():
    """Получает Access Token для GigaChat API"""
    client_id = os.getenv('GIGACHAT_CLIENT_ID')
    client_secret = os.getenv('GIGACHAT_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("❌ GIGACHAT_CLIENT_ID или GIGACHAT_CLIENT_SECRET не найдены")
        print("ℹ️  Добавьте секреты в GitHub Settings → Secrets → Actions")
        return None
    
    # Формируем Authorization Key
    auth_string = f"{client_id}:{client_secret}"
    auth_key = base64.b64encode(auth_string.encode()).decode()
    
    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "RqUID": f"rq-{random.randint(100000, 999999)}-{int(time.time())}",
        "Authorization": f"Basic {auth_key}"
    }
    data = {
        "scope": "GIGACHAT_API_PERS"
    }
    
    try:
        response = requests.post(url, headers=headers, data=data, verify=False, timeout=30)
        if response.status_code == 200:
            token_data = response.json()
            return token_data.get("access_token")
        else:
            print(f"❌ Ошибка получения токена GigaChat: {response.status_code}")
            print(f"📋 Ответ: {response.text[:200]}...")
            return None
    except Exception as e:
        print(f"❌ Исключение при получении токена GigaChat: {e}")
        return None

def generate_content():
    # Конфигурация
    KEEP_LAST_ARTICLES = 3
    
    # Очистка старых статей
    clean_old_articles(KEEP_LAST_ARTICLES)
    
    # Генерируем тему
    selected_topic = generate_ai_trend_topic()
    print(f"📝 Выбрана тема: {selected_topic}")
    
    # Генерируем изображение (приоритет: GigaChat → другие API)
    image_filename = generate_article_image(selected_topic)
    
    # Генерируем контент
    content, model_used, api_success = generate_article_content(selected_topic)
    
    # Создаем файл статьи
    date = datetime.now().strftime("%Y-%m-%d")
    slug = generate_slug(selected_topic)
    filename = f"content/posts/{date}-{slug}.md"
    
    frontmatter = generate_frontmatter(selected_topic, content, model_used, api_success, image_filename)
    
    os.makedirs("content/posts", exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(frontmatter)
    
    print(f"✅ Статья создана: {filename}")
    return filename

def generate_article_content(topic):
    """Генерирует содержание статьи через доступные API"""
    api_key = os.getenv('OPENROUTER_API_KEY')
    gigachat_token = get_gigachat_token()
    
    content = ""
    model_used = "Локальная генерация"
    api_success = False
    
    # Порядок приоритета моделей
    models_to_try = []
    
    # 1. GigaChat (если доступен)
    if gigachat_token:
        models_to_try.append(("GigaChat", lambda: generate_with_gigachat(gigachat_token, topic)))
    
    # 2. OpenRouter модели (если доступны)
    if api_key:
        openrouter_models = [
            "anthropic/claude-3-haiku",
            "google/gemini-pro",
            "mistralai/mistral-7b-instruct",
            "meta-llama/llama-3-8b-instruct",
        ]
        for model_name in openrouter_models:
            models_to_try.append((model_name, lambda m=model_name: generate_with_openrouter(api_key, m, topic)))
    
    # Пробуем все доступные модели
    for model_name, generate_func in models_to_try:
        try:
            print(f"🔄 Пробуем: {model_name}")
            result = generate_func()
            if result:
                content = result
                model_used = model_name
                api_success = True
                print(f"✅ Успешно через {model_name}")
                break
        except Exception as e:
            print(f"⚠️ Ошибка {model_name}: {e}")
            continue
    
    # Fallback
    if not content:
        print("❌ Все API недоступны, используем локальную генерацию")
        content = generate_fallback_content(topic)
    
    return content, model_used, api_success

def generate_with_gigachat(token, topic):
    """Генерация через GigaChat"""
    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    
    prompt = f"""Напиши техническую статью на тему: "{topic}".

Требования:
- Markdown форматирование
- Подзаголовки ## и ###
- **Жирный шрифт** для терминов
- 300-400 слов, русский язык
- Информативно для разработчиков
- Практические примеры

Структура:
1. Введение
2. Основные концепции  
3. Практическое применение
4. Перспективы
5. Заключение"""
    
    payload = {
        "model": "GigaChat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 1500
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=45)
    
    if response.status_code == 200:
        data = response.json()
        return data['choices'][0]['message']['content']
    raise Exception(f"HTTP {response.status_code}")

def generate_with_openrouter(api_key, model_name, topic):
    """Генерация через OpenRouter"""
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://github.com",
            "X-Title": "AI Blog Generator"
        },
        json={
            "model": model_name,
            "messages": [{
                "role": "user",
                "content": f"Напиши техническую статью на тему: {topic}. Используй Markdown, подзаголовки ##, **жирный шрифт**. Русский язык, 300-400 слов, информативно для разработчиков."
            }],
            "max_tokens": 800,
            "temperature": 0.7
        },
        timeout=25
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get('choices'):
            content = data['choices'][0]['message']['content']
            return content.replace('"""', '').replace("'''", "").strip()
    
    raise Exception(f"HTTP {response.status_code}")

def generate_article_image(topic):
    """Генерирует изображение через AI API"""
    print("🎨 Генерация изображения...")
    
    image_prompt = f"Technology illustration for article about {topic}. Modern, clean, professional style. Abstract technology concept with neural networks, data visualization. Blue and purple color scheme. No text."
    
    # Порядок приоритета API для изображений
    apis_to_try = [
        ("GigaChat", try_gigachat_image),
        ("HuggingFace", try_huggingface_api),
        ("DeepAI", try_deepai_api)
    ]
    
    for api_name, api_func in apis_to_try:
        try:
            print(f"🔄 Пробуем {api_name} для изображения")
            result = api_func(image_prompt, topic)
            if result:
                return result
        except Exception as e:
            print(f"⚠️ Ошибка {api_name}: {e}")
            continue
    
    # Fallback изображение
    return create_fallback_image(image_prompt, topic)

def try_gigachat_image(prompt, topic):
    """Генерация изображения через GigaChat"""
    token = get_gigachat_token()
    if not token:
        return None
    
    try:
        # GigaChat может использовать разные endpoints для изображений
        # Проверяем доступные endpoints
        url = "https://gigachat.devices.sberbank.ru/api/v1/models"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            models = response.json()
            print(f"📋 Доступные модели GigaChat: {[m.get('id') for m in models.get('data', [])]}")
        
        # Пробуем генерацию изображения (если endpoint доступен)
        # Note: GigaChat может не иметь image generation в текущем API
        # В этом случае используем fallback
        return None
        
    except Exception as e:
        print(f"❌ GigaChat image error: {e}")
        return None

# Остальные функции (try_huggingface_api, try_deepai_api, create_fallback_image, 
# generate_ai_trend_topic, clean_old_articles, generate_fallback_content, 
# generate_slug, generate_frontmatter) остаются без изменений

# ... (остальные функции из предыдущего скрипта)

def try_huggingface_api(prompt, topic):
    """Пробуем Hugging Face API"""
    hf_token = os.getenv('HUGGINGFACE_TOKEN')
    if not hf_token:
        return None
    
    try:
        models = [
            "stabilityai/stable-diffusion-2-1",
            "runwayml/stable-diffusion-v1-5"
        ]
        
        for model in models:
            try:
                headers = {"Authorization": f"Bearer {hf_token}"}
                payload = {
                    "inputs": prompt,
                    "parameters": {
                        "width": 800,
                        "height": 400,
                        "num_inference_steps": 25
                    }
                }
                
                response = requests.post(
                    f"https://api-inference.huggingface.co/models/{model}",
                    headers=headers,
                    json=payload,
                    timeout=45
                )
                
                if response.status_code == 200:
                    filename = save_article_image(response.content, topic)
                    if filename:
                        print(f"✅ Изображение через {model}")
                        return filename
                
            except Exception as e:
                print(f"⚠️ Ошибка {model}: {e}")
                continue
                
    except Exception as e:
        print(f"❌ HuggingFace error: {e}")
    
    return None

def try_deepai_api(prompt, topic):
    """Пробуем DeepAI API"""
    try:
        headers = {
            "api-key": "quickstart-QUdJIGlzIGNvbWluZy4uLi4K",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "text": prompt,
            "grid_size": "1",
            "width": "800",
            "height": "400"
        }
        
        response = requests.post(
            "https://api.deepai.org/api/text2img",
            headers=headers,
            data=data,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'output_url' in data:
                image_response = requests.get(data['output_url'], timeout=30)
                if image_response.status_code == 200:
                    filename = save_article_image(image_response.content, topic)
                    if filename:
                        print("✅ Изображение через DeepAI")
                        return filename
                        
    except Exception as e:
        print(f"❌ DeepAI error: {e}")
    
    return None

def save_article_image(image_data, topic):
    """Сохраняет изображение"""
    try:
        os.makedirs("static/images/posts", exist_ok=True)
        slug = generate_slug(topic)
        filename = f"images/posts/{slug}.jpg"
        full_path = f"static/{filename}"
        
        with open(full_path, 'wb') as f:
            f.write(image_data)
        
        print(f"💾 Изображение сохранено: {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")
        return None

def create_fallback_image(prompt, topic):
    """Создает fallback изображение"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        import numpy as np
        
        os.makedirs("static/images/posts", exist_ok=True)
        slug = generate_slug(topic)
        filename = f"images/posts/{slug}.jpg"
        full_path = f"static/{filename}"
        
        # Создаем качественное техно-изображение
        width, height = 800, 400
        image = Image.new('RGB', (width, height), color=(20, 25, 45))
        draw = ImageDraw.Draw(image)
        
        # Градиентный фон
        for y in range(height):
            color = (
                int(20 + y * 0.1),
                int(25 + y * 0.08), 
                int(45 + y * 0.12)
            )
            draw.line([(0, y), (width, y)], fill=color)
        
        # Техно-элементы
        draw.rectangle([15, 15, width-15, height-15], outline=(70, 130, 255), width=2)
        
        # Сетка и точки
        for i in range(0, width, 40):
            alpha = random.randint(30, 80)
            draw.line([(i, 0), (i, height)], fill=(70, 130, 255, alpha), width=1)
        
        for i in range(0, height, 40):
            alpha = random.randint(30, 80)
            draw.line([(0, i), (width, i)], fill=(70, 130, 255, alpha), width=1)
        
        # Случайные линии и точки
        for _ in range(25):
            x1, y1 = random.randint(20, width-20), random.randint(20, height-20)
            x2, y2 = x1 + random.randint(-150, 150), y1 + random.randint(-80, 80)
            color = (random.randint(50, 150), random.randint(100, 200), 255)
            draw.line([(x1, y1), (x2, y2)], fill=color, width=random.randint(1, 3))
        
        for _ in range(50):
            x = random.randint(30, width-30)
            y = random.randint(30, height-30)
            size = random.randint(2, 6)
            color = (random.randint(100, 200), random.randint(150, 230), 255)
            draw.ellipse([x, y, x+size, y+size], fill=color)
        
        # Сохраняем с высоким качеством
        image.save(full_path, 'JPEG', quality=95, optimize=True)
        print("🎨 Создано fallback изображение")
        return filename
        
    except Exception as e:
        print(f"❌ Ошибка создания fallback: {e}")
        return None

def generate_ai_trend_topic():
    """Генерирует актуальную тему"""
    tech_domains = [
        "искусственный интеллект", "машинное обучение", "генеративные AI",
        "компьютерное зрение", "обработка естественного языка", "большие языковые модели"
    ]
    
    current_trends = [
        "трансформеры и attention механизмы", "мультимодальные AI системы",
        "few-shot обучение", "нейросети с памятью", "обучение с подкреплением"
    ]
    
    applications = [
        "в веб-разработке", "в мобильных приложениях", "в облачных сервисах",
        "в анализе данных", "в компьютерной безопасности"
    ]
    
    domain = random.choice(tech_domains)
    trend = random.choice(current_trends)
    application = random.choice(applications)
    
    topic_formats = [
        f"{trend}: новые возможности в {domain} {application}",
        f"{domain} 2025: как {trend} меняют {application}",
        f"{trend} в {domain} - перспективы {application}"
    ]
    
    selected_topic = random.choice(topic_formats)
    if random.random() > 0.3:
        selected_topic = f"{selected_topic} в 2024-2025"
    
    return selected_topic

def clean_old_articles(keep_last=3):
    """Оставляет только последние N статей"""
    print(f"🧹 Очистка старых статей, оставляем {keep_last} последних...")
    
    articles = glob.glob("content/posts/*.md")
    if not articles:
        print("📁 Нет статей для очистки")
        return
    
    articles.sort(key=os.path.getmtime)
    articles_to_keep = articles[-keep_last:]
    articles_to_delete = articles[:-keep_last]
    
    print(f"📊 Всего статей: {len(articles)}")
    print(f"💾 Сохраняем: {len(articles_to_keep)}")
    print(f"🗑️ Удаляем: {len(articles_to_delete)}")
    
    for article_path in articles_to_delete:
        try:
            os.remove(article_path)
            print(f"❌ Удалено: {os.path.basename(article_path)}")
        except Exception as e:
            print(f"⚠️ Ошибка удаления {article_path}: {e}")

def generate_fallback_content(topic):
    """Генерация fallback контента"""
    return f"""## {topic}

В 2024-2025 годах **{topic.split(':')[0]}** продолжает активно развиваться и трансформировать технологический ландшафт.

### Ключевые тенденции

- **Передовые алгоритмы** и архитектуры нейросетей
- **Улучшенная эффективность** и оптимизация вычислений  
- **Интеграция с облачными платформами** и распределенными системами
- **Повышенная безопасность** и этические considerations
- **Автоматизация** сложных задач и процессов

### Технологический impact

Современные разработчики используют cutting-edge инструменты для создания инновационных решений. Экосистема быстро эволюционирует, предлагая новые возможности для оптимизации workflow."""

def generate_slug(topic):
    """Генерация slug из названия темы"""
    slug = topic.lower()
    replacements = {' ': '-', ':': '', '(': '', ')': '', '/': '-', '\\': '-', '.': '', ',': ''}
    for old, new in replacements.items():
        slug = slug.replace(old, new)
    slug = ''.join(c for c in slug if c.isalnum() or c == '-')
    while '--' in slug:
        slug = slug.replace('--', '-')
    return slug[:40]

def generate_frontmatter(topic, content, model_used, api_success, image_filename=None):
    """Генерация frontmatter"""
    current_time = datetime.now()
    status = "✅ API генерация" if api_success else "⚠️ Локальная генерация"
    
    tags = ["искусственный-интеллект", "технологии", "инновации", "2024-2025"]
    image_section = f"image: /{image_filename}\n" if image_filename else ""
    
    return f"""---
title: "{topic}"
date: {datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}
draft: false
description: "Автоматически сгенерированная статья о {topic}"
{image_section}tags: {json.dumps(tags, ensure_ascii=False)}
categories: ["Технологии"]
---

# {topic}

{f'![](/{image_filename})' if image_filename else ''}

{content}

---

### 🔧 Технические детали

- **Модель AI:** {model_used}
- **Дата генерации:** {current_time.strftime("%d.%m.%Y %H:%M UTC")}
- **Тема:** {topic}
- **Статус:** {status}
- **Уникальность:** Сохраняются только 3 последние статьи

> *Сгенерировано автоматически через GitHub Actions*
"""

if __name__ == "__main__":
    generate_content()
