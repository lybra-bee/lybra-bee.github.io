#!/usr/bin/env python3
import os
import json
import requests
import random
from datetime import datetime
import glob
import base64
import time

def generate_content():
    # Конфигурация - сколько статей оставлять
    KEEP_LAST_ARTICLES = 3
    
    # Сначала почистим старые статьи
    clean_old_articles(KEEP_LAST_ARTICLES)
    
    # Генерируем актуальную тему на основе трендов AI и технологий
    selected_topic = generate_ai_trend_topic()
    print(f"📝 Актуальная тема: {selected_topic}")
    
    # Генерируем изображение для статьи через реальные AI API
    image_filename = generate_article_image(selected_topic)
    
    # Попытка генерации контента через OpenRouter
    api_key = os.getenv('OPENROUTER_API_KEY')
    content = ""
    model_used = "Локальная генерация"
    api_success = False
    
    if api_key and api_key != "":
        working_models = [
            "mistralai/mistral-7b-instruct",
            "google/gemini-pro",
            "anthropic/claude-3-haiku",
            "meta-llama/llama-3-8b-instruct",
        ]
        
        for selected_model in working_models:
            try:
                print(f"🔄 Пробуем модель: {selected_model}")
                
                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {api_key}",
                        "HTTP-Referer": "https://github.com",
                        "X-Title": "AI Blog Generator"
                    },
                    json={
                        "model": selected_model,
                        "messages": [
                            {
                                "role": "user",
                                "content": f"Напиши техническую статью на тему: {selected_topic}. Используй Markdown форматирование с подзаголовками ##, **жирным шрифтом** для ключевых терминов. Ответ на русском языке, объем 300-400 слов. Сделай статью информативной и полезной для разработчиков."
                            }
                        ],
                        "max_tokens": 600,
                        "temperature": 0.7
                    },
                    timeout=20
                )
                
                print(f"📊 Статус ответа: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    if 'choices' in data and len(data['choices']) > 0:
                        content = data['choices'][0]['message']['content']
                        model_used = selected_model
                        api_success = True
                        print(f"✅ Успешная генерация через {selected_model}")
                        content = content.replace('"""', '').replace("'''", "").strip()
                        break
                else:
                    print(f"❌ Ошибка {response.status_code} от {selected_model}")
                    
            except Exception as e:
                print(f"⚠️ Исключение с {selected_model}: {e}")
                continue
        
        if not api_success:
            print("❌ Все модели не сработали, используем fallback")
            content = generate_fallback_content(selected_topic)
    else:
        print("⚠️ API ключ не найден, используем локальную генерацию")
        content = generate_fallback_content(selected_topic)
    
    # Создаем новую статью
    date = datetime.now().strftime("%Y-%m-%d")
    slug = generate_slug(selected_topic)
    filename = f"content/posts/{date}-{slug}.md"
    
    frontmatter = generate_frontmatter(selected_topic, content, model_used, api_success, image_filename)
    
    os.makedirs("content/posts", exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(frontmatter)
    
    print(f"✅ Файл создан: {filename}")
    return filename

def generate_article_image(topic):
    """Генерирует изображение через реальные AI API"""
    print("🎨 Генерация изображения через AI API...")
    
    # Промпт для генерации изображения
    image_prompt = f"Technology illustration for article about {topic}. Modern, clean, professional style. Abstract technology concept with neural networks, data visualization. Blue and purple color scheme. No text."
    
    # Попробуем разные бесплатные API по очереди
    apis_to_try = [
        {"name": "HuggingFace Stable Diffusion", "function": try_huggingface_api},
        {"name": "DeepAI", "function": try_deepai_api},
        {"name": "Fallback", "function": create_fallback_image}
    ]
    
    for api in apis_to_try:
        try:
            print(f"🔄 Пробуем {api['name']}...")
            result = api['function'](image_prompt, topic)
            if result:
                return result
        except Exception as e:
            print(f"⚠️ Ошибка в {api['name']}: {e}")
            continue
    
    return create_fallback_image(image_prompt, topic)

def try_huggingface_api(prompt, topic):
    """Пробуем Hugging Face Stable Diffusion API"""
    hf_token = os.getenv('HUGGINGFACE_TOKEN')
    if not hf_token:
        return None
    
    try:
        # Попробуем несколько моделей
        models = [
            "stabilityai/stable-diffusion-2-1",
            "runwayml/stable-diffusion-v1-5",
            "prompthero/openjourney"
        ]
        
        for model in models:
            try:
                headers = {"Authorization": f"Bearer {hf_token}"}
                payload = {
                    "inputs": prompt,
                    "parameters": {
                        "width": 800,
                        "height": 400,
                        "num_inference_steps": 25,
                        "guidance_scale": 7.5
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
                        print(f"✅ Изображение создано через {model}")
                        return filename
                else:
                    print(f"❌ Модель {model} не ответила: {response.status_code}")
                    
            except Exception as e:
                print(f"⚠️ Ошибка с моделью {model}: {e}")
                continue
                
    except Exception as e:
        print(f"❌ Ошибка HuggingFace API: {e}")
    
    return None

def try_deepai_api(prompt, topic):
    """Пробуем DeepAI API (бесплатный)"""
    try:
        # DeepAI имеет бесплатный тариф с ограничениями
        headers = {
            "api-key": "quickstart-QUdJIGlzIGNvbWluZy4uLi4K",  # Бесплатный ключ
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

def create_fallback_image(prompt, topic):
    """Создает fallback изображение с помощью Pillow"""
    try:
        from PIL import Image, ImageDraw
        
        os.makedirs("static/images/posts", exist_ok=True)
        slug = generate_slug(topic)
        filename = f"images/posts/{slug}.jpg"
        full_path = f"static/{filename}"
        
        # Создаем качественное fallback изображение
        width, height = 800, 400
        image = Image.new('RGB', (width, height), color=(25, 25, 50))
        draw = ImageDraw.Draw(image)
        
        # Градиентный фон
        for i in range(height):
            r = 25 + i // 8
            g = 25 + i // 12
            b = 50 + i // 6
            draw.line([(0, i), (width, i)], fill=(r, g, b))
        
        # Техно-элементы
        draw.rectangle([20, 20, width-20, height-20], outline=(100, 100, 255), width=2)
        
        # Точки и линии
        for _ in range(50):
            x1, y1 = random.randint(30, width-30), random.randint(30, height-30)
            x2, y2 = x1 + random.randint(-100, 100), y1 + random.randint(-50, 50)
            draw.line([(x1, y1), (x2, y2)], fill=(80, 180, 255), width=1)
        
        # Сохраняем с высоким качеством
        image.save(full_path, 'JPEG', quality=95, optimize=True)
        print("🎨 Создано качественное fallback изображение")
        return filename
        
    except Exception as e:
        print(f"❌ Ошибка создания fallback изображения: {e}")
        return None

def generate_ai_trend_topic():
    """Генерирует актуальную тему на основе трендов AI и технологий"""
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
    """Генерация frontmatter и содержимого"""
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
