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
        return None
    
    print(f"🔑 GigaChat Client ID: {client_id[:10]}...{client_id[-6:]}")
    print(f"🔑 GigaChat Client Secret: {client_secret[:10]}...{client_secret[-6:]}")
    
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
        print(f"📊 GigaChat status: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            print("✅ GigaChat token получен")
            return token_data.get("access_token")
        else:
            print(f"❌ Ошибка GigaChat: {response.text[:200]}")
            return None
    except Exception as e:
        print(f"❌ Исключение при получении токена GigaChat: {e}")
        return None

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
    KEEP_LAST_ARTICLES = 3
    clean_old_articles(KEEP_LAST_ARTICLES)
    
    selected_topic = generate_ai_trend_topic()
    print(f"📝 Актуальная тема 2025: {selected_topic}")
    
    image_filename = generate_article_image(selected_topic)
    content, model_used = generate_article_content(selected_topic)
    
    date = datetime.now().strftime("%Y-%m-%d")
    slug = generate_slug(selected_topic)
    filename = f"content/posts/{date}-{slug}.md"
    
    frontmatter = generate_frontmatter(selected_topic, content, model_used, True, image_filename)
    
    os.makedirs("content/posts", exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(frontmatter)
    
    print(f"✅ Статья создана: {filename}")
    return filename

def generate_article_content(topic):
    """Генерирует содержание статьи через доступные API"""
    api_key = os.getenv('OPENROUTER_API_KEY')
    gigachat_token = get_gigachat_token()
    
    models_to_try = []
    
    # Сначала OpenRouter (он работает)
    if api_key:
        openrouter_models = [
            "anthropic/claude-3-haiku",
            "google/gemini-pro",
            "mistralai/mistral-7b-instruct",
            "meta-llama/llama-3-8b-instruct",
        ]
        for model_name in openrouter_models:
            models_to_try.append((model_name, lambda m=model_name: generate_with_openrouter(api_key, m, topic)))
    
    # Затем GigaChat (если заработает)
    if gigachat_token:
        models_to_try.append(("GigaChat-2-Max", lambda: generate_with_gigachat(gigachat_token, topic, "GigaChat-2-Max")))
        models_to_try.append(("GigaChat-2-Pro", lambda: generate_with_gigachat(gigachat_token, topic, "GigaChat-2-Pro")))
    
    for model_name, generate_func in models_to_try:
        try:
            print(f"🔄 Пробуем: {model_name}")
            result = generate_func()
            if result:
                print(f"✅ Успешно через {model_name}")
                return result, model_name
        except Exception as e:
            print(f"⚠️ Ошибка {model_name}: {e}")
            continue
    
    raise Exception("❌ Все AI API недоступны. Проверьте настройки и подключение.")

def generate_with_gigachat(token, topic, model_name):
    """Генерация через GigaChat с выбором модели"""
    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    
    prompt = f"""Напиши развернутую техническую статью на тему: "{topic}".

Требования к статье:
- Объем: 500-700 слов
- Формат: Markdown с подзаголовками ## и ###
- Язык: русский, технический стиль
- Аудитория: разработчики и IT-специалисты
- Актуальность: фокус на 2025 год и перспективы развития

Структура статьи:
1. Введение и актуальность темы в 2025 году
2. Технические детали и архитектурные особенности
3. Практические примеры реализации
4. Кейсы использования и лучшие практики
5. Перспективы развития и тренды
6. Заключение и выводы

Используй:
- **Жирный шрифт** для ключевых терминов
- Списки для перечисления преимуществ и особенностей
- Технические детали и конкретные примеры
- Ссылки на современные технологии и frameworks 2025 года"""
    
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 2000,
        "repetition_penalty": 1.1
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=60)
    
    if response.status_code == 200:
        data = response.json()
        return data['choices'][0]['message']['content']
    raise Exception(f"HTTP {response.status_code}: {response.text}")

def generate_with_openrouter(api_key, model_name, topic):
    """Генерация через OpenRouter"""
    prompt = f"""Напиши развернутую техническую статью на тему: "{topic}".

Требования:
- Объем: 500-700 слов
- Формат: Markdown с подзаголовками
- Язык: русский, технический стиль
- Аудитория: разработчики
- Фокус на 2025 год и современные тренды

Структура:
1. Введение и актуальность 2025
2. Технические детали
3. Практические примеры
4. Кейсы использования
5. Перспективы развития
6. Заключение

Используй:
- **Жирный шрифт** для терминов
- Списки и конкретные примеры
- Современные технологии 2025 года"""
    
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
            return content.replace('"""', '').replace("'''", "").strip()
    
    raise Exception(f"HTTP {response.status_code}")

def generate_article_image(topic):
    """Генерация изображения через AI API"""
    print("🎨 Генерация изображения через AI API...")
    
    image_prompt = f"Technology illustration 2025 for article about {topic}. Modern, futuristic, professional style. Abstract technology concept with AI, neural networks, data visualization. Blue and purple color scheme. No text."
    
    apis_to_try = [
        {"name": "Stability AI", "function": try_stability_ai},
        {"name": "HuggingFace Stable Diffusion", "function": try_huggingface_sd},
        {"name": "DeepAI Text2Img", "function": try_deepai_api}
    ]
    
    for api in apis_to_try:
        try:
            print(f"🔄 Пробуем {api['name']}")
            result = api['function'](image_prompt, topic)
            if result:
                return result
        except Exception as e:
            print(f"⚠️ Ошибка в {api['name']}: {e}")
            continue
    
    print("❌ Все AI API для изображений недоступны, продолжаем без изображения")
    return None

def try_stability_ai(prompt, topic):
    """Пробуем Stability AI с правильными разрешениями для SDXL"""
    try:
        stability_key = os.getenv('STABILITYAI_KEY')
        if not stability_key:
            print("ℹ️ STABILITYAI_KEY не найден")
            return None
        
        print(f"🔑 Stability key: {stability_key[:10]}...{stability_key[-6:]}")
        
        # Правильный эндпоинт для SDXL
        url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
        
        headers = {
            "Authorization": f"Bearer {stability_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Разрешенные размеры для SDXL
        allowed_dimensions = [
            (1024, 1024), (1152, 896), (1216, 832), 
            (1344, 768), (1536, 640), (640, 1536),
            (768, 1344), (832, 1216), (896, 1152)
        ]
        
        # Выбираем случайное разрешение из разрешенных
        width, height = random.choice(allowed_dimensions)
        
        payload = {
            "text_prompts": [{"text": prompt, "weight": 1.0}],
            "cfg_scale": 7,
            "height": height,
            "width": width,
            "samples": 1,
            "steps": 30,
            "style_preset": "digital-art"
        }
        
        print(f"📐 Размер изображения: {width}x{height}")
        
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        print(f"📊 Stability AI status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'artifacts' in data and data['artifacts']:
                image_data = base64.b64decode(data['artifacts'][0]['base64'])
                filename = save_article_image(image_data, topic)
                if filename:
                    print("✅ Изображение создано через Stability AI")
                    return filename
        else:
            print(f"❌ Stability AI error: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Ошибка Stability AI: {e}")
    
    return None

def try_huggingface_sd(prompt, topic):
    """Пробуем Stable Diffusion через Hugging Face"""
    hf_token = os.getenv('HUGGINGFACE_TOKEN')
    
    models = [
        "stabilityai/stable-diffusion-2-1",
        "runwayml/stable-diffusion-v1-5",
        "prompthero/openjourney"
    ]
    
    for model in models:
        try:
            headers = {}
            if hf_token:
                headers["Authorization"] = f"Bearer {hf_token}"
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "width": 800,
                    "height": 400,
                    "num_inference_steps": 20,
                    "guidance_scale": 7.5
                }
            }
            
            response = requests.post(
                f"https://api-inference.huggingface.co/models/{model}",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                filename = save_article_image(response.content, topic)
                if filename:
                    print(f"✅ Изображение создано через {model}")
                    return filename
            elif response.status_code == 503:
                print(f"⏳ Модель {model} загружается, пробуем следующую...")
                continue
                
        except Exception as e:
            print(f"⚠️ Ошибка с моделью {model}: {e}")
            continue
    
    return None

def try_deepai_api(prompt, topic):
    """Пробуем DeepAI API (бесплатный тариф)"""
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
                        print("✅ Изображение создано через DeepAI")
                        return filename
                        
    except Exception as e:
        print(f"❌ Ошибка DeepAI API: {e}")
    
    return None

def save_article_image(image_data, topic):
    """Сохраняет сгенерированное изображение"""
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
        print(f"❌ Ошибка сохранения изображения: {e}")
        return None

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

def generate_slug(topic):
    """Генерация slug из названия темы"""
    slug = topic.lower()
    replacements = {' ': '-', ':': '', '(': '', ')': '', '/': '-', '\\': '-', '.': '', ',': '', '--': '-'}
    for old, new in replacements.items():
        slug = slug.replace(old, new)
    slug = ''.join(c for c in slug if c.isalnum() or c == '-')
    while '--' in slug:
        slug = slug.replace('--', '-')
    return slug[:50]

def generate_frontmatter(topic, content, model_used, api_success, image_filename=None):
    """Генерация frontmatter"""
    current_time = datetime.now()
    
    tags = ["искусственный-интеллект", "технологии", "инновации", "2025", "ai"]
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
- **Год актуальности:** 2025
- **Статус:** Чистая AI генерация

> *Сгенерировано автоматически через GitHub Actions*
"""

if __name__ == "__main__":
    try:
        generate_content()
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        exit(1)
