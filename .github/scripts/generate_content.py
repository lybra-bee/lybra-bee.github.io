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
    
    # Добавляем Groq модели в первую очередь (бесплатные и быстрые)
    if groq_key:
        print("🔑 Groq API ключ найден")
        groq_models = [
            "llama-3.1-8b-instant",  # Быстрая и бесплатная
            "llama-3.1-70b-versatile",  # Мощная
            "mixtral-8x7b-32768",  # Хорошая для текста
            "gemma-7b-it"  # Легкая и эффективная
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
            if result and len(result.strip()) > 100:  # Проверяем что контент не пустой
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
Модели искусственного интеллекта для {topic} используют современные архитектуры нейросетей, включая трансформеры и генеративные модели.

## Заключение
{topic} представляет собой ключевое направление развития искусственного интеллекта с большим потенциалом для инноваций.
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
- Конкретные примеры и технические детали
- Современные технологии и frameworks"""

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
    prompt = f"""Напиши развернутую техническую статью на тему: "{topic}".

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
    """Генерация изображения через AI API с использованием Groq для создания промптов"""
    print("🎨 Генерация изображения...")
    
    # Сначала генерируем качественный промпт для изображения с помощью Groq
    image_prompt = generate_image_prompt_with_groq(topic)
    
    apis_to_try = [
        {"name": "DeepAI Text2Img", "function": lambda p=image_prompt: try_deepai_api(p, topic)},
        {"name": "HuggingFace Free", "function": lambda p=image_prompt: try_huggingface_free(p, topic)},
        {"name": "Stability AI", "function": lambda p=image_prompt: try_stability_ai(p, topic)},
        {"name": "Dummy Image", "function": lambda p=image_prompt: try_dummy_image(p, topic)},
    ]
    
    for api in apis_to_try:
        try:
            print(f"🔄 Пробуем {api['name']}")
            result = api['function']()
            if result:
                return result
        except Exception as e:
            print(f"⚠️ Ошибка в {api['name']}: {e}")
            continue
    
    print("❌ Все AI API для изображений недоступны, продолжаем без изображения")
    return None

def generate_image_prompt_with_groq(topic):
    """Генерация качественного промпта для изображения с помощью Groq"""
    groq_key = os.getenv('GROQ_API_KEY')
    
    if not groq_key:
        print("ℹ️ GROQ_API_KEY не найден, используем стандартный промпт")
        return f"Technology illustration 2025 for article about {topic}. Modern, futuristic, professional style. Abstract technology concept with AI, neural networks, data visualization. Blue and purple color scheme. No text."
    
    try:
        prompt = f"""Создай подробное описание для изображения к статье на тему: "{topic}".

Требования:
- Описание должно быть на английском языке
- Стиль: современный, футуристический, технологический
- Цветовая схема: синие и фиолетовые тона
- Элементы: абстрактные технологии, нейросети, данные
- Формат: не более 2 предложений
- Не включать текст на изображении"""

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {groq_key}"
            },
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 100,
                "temperature": 0.8,
                "top_p": 0.9
            },
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('choices'):
                prompt_text = data['choices'][0]['message']['content'].strip()
                print(f"✅ Сгенерирован промпт для изображения: {prompt_text}")
                return prompt_text
                
    except Exception as e:
        print(f"⚠️ Ошибка генерации промпта через Groq: {e}")
    
    # Fallback промпт
    return f"Technology illustration 2025 for article about {topic}. Modern, futuristic, professional style. Abstract technology concept with AI, neural networks, data visualization. Blue and purple color scheme. No text."

def try_deepai_api(prompt, topic):
    """Пробуем DeepAI API с вашим токеном"""
    try:
        print("🔑 Используем DeepAI API с вашим токеном")
        
        headers = {
            "Api-Key": "6d27650a"  # Ваш реальный токен
        }
        
        data = {
            "text": prompt,
            "grid_size": "1",
            "width": "800", 
            "height": "400",
            "image_generator_version": "standard"
        }
        
        print("📡 Отправляем запрос к DeepAI...")
        response = requests.post(
            "https://api.deepai.org/api/text2img",
            headers=headers,
            data=data,
            timeout=60
        )
        
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

def try_huggingface_free(prompt, topic):
    """Бесплатный Hugging Face через неофициальный API"""
    try:
        print("🔑 Используем бесплатный Hugging Face API")
        
        # Попробуем несколько публичных моделей
        models = [
            "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5",
            "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1",
            "https://api-inference.huggingface.co/models/prompthero/openjourney"
        ]
        
        for model_url in models:
            try:
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
                    model_url,
                    json=payload,
                    timeout=45,
                    headers={"User-Agent": "AI-Blog-Generator/1.0"}
                )
                
                if response.status_code == 200:
                    filename = save_article_image(response.content, topic)
                    if filename:
                        print(f"✅ Изображение создано через {model_url.split('/')[-1]}")
                        return filename
                elif response.status_code == 503:
                    print(f"⏳ Модель загружается, пробуем следующую...")
                    continue
                else:
                    print(f"⚠️ Ошибка {response.status_code} для {model_url}")
                    
            except Exception as e:
                print(f"⚠️ Ошибка с моделью: {e}")
                continue
                
    except Exception as e:
        print(f"❌ Исключение в Hugging Face API: {e}")
    
    return None

def try_stability_ai(prompt, topic):
    """Пробуем Stability AI"""
    try:
        stability_key = os.getenv('STABILITYAI_KEY')
        if not stability_key:
            print("ℹ️ STABILITYAI_KEY не найден, пропускаем")
            return None
        
        print("🔑 Используем Stability AI")
        
        url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
        
        headers = {
            "Authorization": f"Bearer {stability_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        payload = {
            "text_prompts": [{"text": prompt, "weight": 1.0}],
            "cfg_scale": 7,
            "height": 512,
            "width": 512,
            "samples": 1,
            "steps": 20,
            "style_preset": "digital-art"
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
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

def try_dummy_image(prompt, topic):
    """Создает простое изображение через внешние сервисы"""
    try:
        print("🎨 Создаем изображение через внешний сервис")
        
        # Используем улучшенный placeholder с цветами вашего сайта
        encoded_topic = urllib.parse.quote(topic[:30])
        image_url = f"https://placehold.co/800x400/0f172a/6366f1/png?text={encoded_topic}"
        
        response = requests.get(image_url, timeout=30)
        if response.status_code == 200:
            filename = save_article_image(response.content, topic)
            if filename:
                print("✅ Изображение-заглушка создано")
                return filename
    except Exception as e:
        print(f"❌ Ошибка создания заглушки: {e}")
    
    return None

def save_article_image(image_data, topic):
    """Сохраняет сгенерированное изображение"""
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
    """Оставляет только последние N статей"""
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
                
                # Также удаляем связанное изображение если есть
                slug = os.path.basename(article_path).replace('.md', '')
                image_path = f"assets/images/posts/{slug}.jpg"
                if os.path.exists(image_path):
                    os.remove(image_path)
                    print(f"❌ Удалено изображение: {slug}.jpg")
                    
            except Exception as e:
                print(f"⚠️ Ошибка удаления {article_path}: {e}")
                
    except Exception as e:
        print(f"⚠️ Ошибка при очистке статей: {e}")

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

def generate_frontmatter(topic, content, model_used, image_filename=None):
    """Генерация frontmatter"""
    current_time = datetime.now()
    
    tags = ["искусственный-интеллект", "технологии", "инновации", "2025", "ai"]
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
        print("=" * 50)
        print("🤖 AI CONTENT GENERATOR")
        print("=" * 50)
        
        # Проверяем доступные API ключи
        openrouter_key = os.getenv('OPENROUTER_API_KEY')
        groq_key = os.getenv('GROQ_API_KEY')
        
        print(f"🔑 OPENROUTER_API_KEY: {'✅ есть' if openrouter_key else '❌ нет'}")
        print(f"🔑 GROQ_API_KEY: {'✅ есть' if groq_key else '❌ нет'}")
        
        generate_content()
        
        print("=" * 50)
        print("✅ Генерация завершена успешно!")
        print("=" * 50)
        
    except Exception as e:
        print("❌ Критическая ошибка:")
        print(f"Ошибка: {e}")
        print("🔄 Продолжаем без генерации контента")
        exit(0)
