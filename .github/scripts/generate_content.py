#!/usr/bin/env python3
import os
import json
import requests
import random
from datetime import datetime
import glob
import base64
import time

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
    KEEP_LAST_ARTICLES = 5
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
    """Генерация содержания статьи через доступные API"""
    api_key = os.getenv('OPENROUTER_API_KEY')
    
    models_to_try = []
    
    # OpenRouter модели
    if api_key:
        openrouter_models = [
            "anthropic/claude-3-haiku",
            "google/gemini-pro",
            "mistralai/mistral-7b-instruct",
            "meta-llama/llama-3-8b-instruct",
        ]
        for model_name in openrouter_models:
            models_to_try.append((model_name, lambda m=model_name: generate_with_openrouter(api_key, m, topic)))
    
    # Groq API
    groq_key = os.getenv('GROQ_API_KEY')
    if groq_key:
        groq_models = [
            "llama3-70b-8192",
            "mixtral-8x7b-32768",
            "gemma-7b-it"
        ]
        for model_name in groq_models:
            models_to_try.append((f"Groq-{model_name}", lambda m=model_name: generate_with_groq(groq_key, m, topic)))
    
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

def generate_with_groq(api_key, model_name, topic):
    """Генерация через Groq API"""
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
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
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
    
    raise Exception(f"HTTP {response.status_code}: {response.text}")

def generate_article_image(topic):
    """Генерация изображения через AI API"""
    print("🎨 Генерация изображения через AI API...")
    
    image_prompt = f"Technology illustration 2025 for article about {topic}. Modern, futuristic, professional style. Abstract technology concept with AI, neural networks, data visualization. Blue and purple color scheme. No text."
    
    apis_to_try = [
        {"name": "DeepAI Text2Img", "function": try_deepai_api},
        {"name": "HuggingFace Inference", "function": try_huggingface_inference},
        {"name": "Stability AI", "function": try_stability_ai},
        {"name": "Replicate API", "function": try_replicate_api},
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

def try_huggingface_inference(prompt, topic):
    """Пробуем Hugging Face Inference API"""
    try:
        hf_token = os.getenv('HUGGINGFACE_TOKEN')
        if not hf_token:
            print("ℹ️ HUGGINGFACE_TOKEN не найден, пропускаем")
            return None
            
        print("🔑 Используем Hugging Face Inference API")
        
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
                        "num_inference_steps": 20
                    }
                }
                
                response = requests.post(
                    f"https://api-inference.huggingface.co/models/{model}",
                    headers=headers,
                    json=payload,
                    timeout=60
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
            "height": 768,
            "width": 512,
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

def try_replicate_api(prompt, topic):
    """Пробуем Replicate API"""
    try:
        replicate_token = os.getenv('REPLICATE_API_TOKEN')
        if not replicate_token:
            print("ℹ️ REPLICATE_API_TOKEN не найден, пропускаем")
            return None
            
        print("🔑 Используем Replicate API")
        
        headers = {
            "Authorization": f"Token {replicate_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "version": "db21e45d3f7023abc2a46ee38a23973f6dce16bb082a930b0c49861f96d1e5bf",
            "input": {
                "prompt": prompt,
                "width": 800,
                "height": 400
            }
        }
        
        response = requests.post(
            "https://api.replicate.com/v1/predictions",
            headers=headers,
            json=payload,
            timeout=60
        )
        
        if response.status_code == 201:
            prediction_id = response.json()["id"]
            print(f"⏳ Ожидаем генерации изображения: {prediction_id}")
            
            # Ожидаем завершения генерации
            for _ in range(10):
                time.sleep(3)
                status_response = requests.get(
                    f"https://api.replicate.com/v1/predictions/{prediction_id}",
                    headers=headers
                )
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    if status_data["status"] == "succeeded":
                        image_url = status_data["output"]
                        image_response = requests.get(image_url, timeout=60)
                        if image_response.status_code == 200:
                            filename = save_article_image(image_response.content, topic)
                            if filename:
                                print("✅ Изображение создано через Replicate")
                                return filename
                        break
                    elif status_data["status"] == "failed":
                        print("❌ Генерация через Replicate не удалась")
                        break
            else:
                print("⏰ Таймаут ожидания Replicate")
                
    except Exception as e:
        print(f"❌ Исключение в Replicate API: {e}")
    
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

def clean_old_articles(keep_last=5):
    """Оставляет только последние N статей"""
    print(f"🧹 Очистка старых статей, оставляем {keep_last} последних...")
    
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
- **Статус:** Чистая AI генерация

> *Сгенерировано автоматически через GitHub Actions*
"""

if __name__ == "__main__":
    try:
        print("🚀 Запуск генерации контента...")
        generate_content()
        print("✅ Генерация завершена успешно!")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        exit(1)
