#!/usr/bin/env python3
import os
import json
import requests
import random
from datetime import datetime
import glob
import base64
from PIL import Image
import io

def generate_content():
    # Конфигурация - сколько статей оставлять
    KEEP_LAST_ARTICLES = 3
    
    # Сначала почистим старые статьи
    clean_old_articles(KEEP_LAST_ARTICLES)
    
    # Генерируем актуальную тему на основе трендов AI и технологий
    selected_topic = generate_ai_trend_topic()
    print(f"📝 Актуальная тема: {selected_topic}")
    
    # Генерируем изображение для статьи
    image_filename = generate_article_image(selected_topic)
    image_markdown = f"![{selected_topic}]({image_filename})" if image_filename else ""
    
    # Попытка генерации контента через OpenRouter
    api_key = os.getenv('OPENROUTER_API_KEY')
    content = ""
    model_used = "Локальная генерация"
    api_success = False
    
    if api_key and api_key != "":
        # ПРОВЕРЕННЫЕ РАБОЧИЕ МОДЕЛИ (в приоритетном порядке)
        working_models = [
            "mistralai/mistral-7b-instruct",      # ✅ ПРОВЕРЕНА - РАБОТАЕТ
            "google/gemini-pro",                  # ✅ Высокий приоритет
            "anthropic/claude-3-haiku",           # ✅ Качественная модель
            "meta-llama/llama-3-8b-instruct",     # ✅ Популярная модель
            "huggingfaceh4/zephyr-7b-beta",       # ✅ Бесплатная
        ]
        
        # Перебираем модели пока не найдем рабочую
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
                                "content": f"Напиши техническую статью на тему: {selected_topic}. Используй Markdown форматирование с подзаголовками ##, **жирным шрифтом** для ключевых терминов и нумерованными списками. Ответ на русском языке, объем 300-400 слов. Сделай статью информативной, технически точной и полезной для разработчиков. Освещи последние тренды 2024-2025 года."
                            }
                        ],
                        "max_tokens": 600,
                        "temperature": 0.7,
                        "top_p": 0.9
                    },
                    timeout=15
                )
                
                print(f"📊 Статус ответа: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    if 'choices' in data and len(data['choices']) > 0:
                        content = data['choices'][0]['message']['content']
                        model_used = selected_model
                        api_success = True
                        print(f"✅ Успешная генерация через {selected_model}")
                        
                        # Очистка контента от лишних кавычек
                        content = content.replace('"""', '').replace("'''", "").strip()
                        break  # Выходим из цикла при успехе
                    else:
                        print(f"⚠️ Нет choices в ответе от {selected_model}")
                else:
                    error_msg = response.text[:100] if response.text else "No error message"
                    print(f"❌ Ошибка {response.status_code} от {selected_model}: {error_msg}")
                    
            except Exception as e:
                print(f"⚠️ Исключение с {selected_model}: {e}")
                continue  # Пробуем следующую модель
        
        if not api_success:
            print("❌ Все модели не сработали, используем fallback")
            content = generate_fallback_content(selected_topic)
    else:
        print("⚠️ API ключ не найден или пустой")
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
    
    # Покажем начало файла для проверки
    with open(filename, 'r', encoding='utf-8') as f:
        preview = f.read(400)
    print(f"📄 Предпросмотр:\n{preview}...")
    
    return filename

def generate_article_image(topic):
    """Генерирует изображение для статьи через AI API"""
    print("🎨 Генерация изображения для статьи...")
    
    # Используем бесплатные AI image generation API
    image_apis = [
        {"name": "Stable Diffusion", "url": "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"},
        {"name": "DALL-E", "url": "https://api.openai.com/v1/images/generations"},
    ]
    
    # Промпт для генерации изображения
    image_prompt = f"Technology illustration for article about {topic}. Modern, clean, professional style. Abstract technology concept with neural networks, data visualization, futuristic elements. Blue and purple color scheme. No text."
    
    for api in image_apis:
        try:
            if api["name"] == "Stable Diffusion":
                # Попробуем Hugging Face Stable Diffusion
                hf_token = os.getenv('HUGGINGFACE_TOKEN')
                if not hf_token:
                    continue
                    
                headers = {"Authorization": f"Bearer {hf_token}"}
                payload = {
                    "inputs": image_prompt,
                    "parameters": {
                        "width": 800,
                        "height": 400,
                        "num_inference_steps": 20,
                        "guidance_scale": 7.5
                    }
                }
                
                response = requests.post(api["url"], headers=headers, json=payload, timeout=30)
                
                if response.status_code == 200:
                    # Сохраняем изображение
                    image_data = response.content
                    return save_article_image(image_data, topic)
                    
            elif api["name"] == "DALL-E":
                # Попробуем DALL-E (если есть ключ)
                openai_key = os.getenv('OPENAI_API_KEY')
                if not openai_key:
                    continue
                    
                headers = {
                    "Authorization": f"Bearer {openai_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "dall-e-2",
                    "prompt": image_prompt,
                    "size": "800x400",
                    "n": 1
                }
                
                response = requests.post(api["url"], headers=headers, json=payload, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'data' in data and len(data['data']) > 0:
                        image_url = data['data'][0]['url']
                        image_response = requests.get(image_url, timeout=30)
                        if image_response.status_code == 200:
                            return save_article_image(image_response.content, topic)
                            
        except Exception as e:
            print(f"⚠️ Ошибка генерации изображения через {api['name']}: {e}")
            continue
    
    # Fallback - используем локальное изображение или placeholder
    print("❌ Не удалось сгенерировать изображение, используем fallback")
    return create_fallback_image(topic)

def save_article_image(image_data, topic):
    """Сохраняет сгенерированное изображение"""
    try:
        # Создаем папку для изображений
        os.makedirs("static/images/posts", exist_ok=True)
        
        # Генерируем имя файла
        slug = generate_slug(topic)
        filename = f"images/posts/{slug}.jpg"
        full_path = f"static/{filename}"
        
        # Сохраняем изображение
        with open(full_path, 'wb') as f:
            f.write(image_data)
        
        print(f"✅ Изображение сохранено: {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ Ошибка сохранения изображения: {e}")
        return None

def create_fallback_image(topic):
    """Создает fallback изображение"""
    try:
        # Создаем простое изображение программно
        from PIL import Image, ImageDraw, ImageFont
        import numpy as np
        
        # Создаем папку для изображений
        os.makedirs("static/images/posts", exist_ok=True)
        
        # Генерируем имя файла
        slug = generate_slug(topic)
        filename = f"images/posts/{slug}.jpg"
        full_path = f"static/{filename}"
        
        # Создаем простое изображение
        width, height = 800, 400
        image = Image.new('RGB', (width, height), color=(25, 25, 50))
        draw = ImageDraw.Draw(image)
        
        # Добавляем простой градиент
        for i in range(height):
            color = (25, 25, 50 + i//2)
            draw.line([(0, i), (width, i)], fill=color)
        
        # Добавляем техно-круги
        for i in range(3):
            x = random.randint(100, width-100)
            y = random.randint(100, height-100)
            size = random.randint(50, 150)
            draw.ellipse([x-size, y-size, x+size, y+size], outline=(100, 100, 255), width=3)
        
        # Сохраняем
        image.save(full_path, 'JPEG', quality=85)
        print(f"✅ Fallback изображение создано: {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ Ошибка создания fallback изображения: {e}")
        return None

def generate_ai_trend_topic():
    """Генерирует актуальную тему на основе трендов AI и технологий 2024-2025"""
    # ... (остается без изменений, как в предыдущей версии)
    # [код функции generate_ai_trend_topic]

def clean_old_articles(keep_last=3):
    """Оставляет только последние N статей, удаляет остальные"""
    # ... (остается без изменений)
    # [код функции clean_old_articles]

def generate_fallback_content(topic):
    """Генерация fallback контента на основе актуальной темы"""
    # ... (остается без изменений)
    # [код функции generate_fallback_content]

def generate_slug(topic):
    """Генерация slug из названия темы"""
    # ... (остается без изменений)
    # [код функции generate_slug]

def generate_frontmatter(topic, content, model_used, api_success, image_filename=None):
    """Генерация frontmatter и содержимого"""
    current_time = datetime.now()
    status = "✅ API генерация" if api_success else "⚠️ Локальная генерация"
    
    # Определяем теги на основе темы
    tags = ["искусственный-интеллект", "технологии", "инновации", "2024-2025"]
    if "веб" in topic.lower() or "web" in topic.lower():
        tags.append("веб-разработка")
    if "безопасность" in topic.lower() or "security" in topic.lower():
        tags.append("кибербезопасность")
    if "облако" in topic.lower() or "cloud" in topic.lower():
        tags.append("облачные-вычисления")
    if "данн" in topic.lower() or "data" in topic.lower():
        tags.append("анализ-данных")
    
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

{f'![]({image_filename})' if image_filename else ''}

{content}

---

### 🔧 Технические детали

- **Модель AI:** {model_used}
- **Дата генерации:** {current_time.strftime("%d.%m.%Y %H:%M UTC")}
- **Тема:** {topic}
- **Статус:** {status}
- **Уникальность:** Сохраняются только 3 последние статьи
- **Актуальность:** Тренды 2024-2025

> *Сгенерировано автоматически через GitHub Actions + OpenRouter*
"""

if __name__ == "__main__":
    generate_content()
