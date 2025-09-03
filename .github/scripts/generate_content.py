import requests
import os
import time
import argparse
import re
import html
from datetime import datetime
import feedparser
from bs4 import BeautifulSoup

def clean_text(text):
    """Очистка текста от HTML тегов и мусора"""
    if not text:
        return ""
    
    # Декодируем HTML entities
    text = html.unescape(text)
    
    # Удаляем HTML теги
    text = re.sub(r'<[^>]*>', '', text)
    
    # Удаляем URL и специальные символы
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'[^\w\sа-яА-ЯёЁ.,!?;-]', ' ', text)
    
    # Убираем лишние пробелы
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def get_trending_topics():
    """Получение актуальных тем"""
    try:
        topics = []
        
        # Актуальные темы по AI и технологиям
        current_trends = [
            "Новые возможности GPT-5 и искусственного интеллекта",
            "Генеративный ИИ в бизнесе 2024",
            "Нейросети для автоматизации контента",
            "Машинное обучение в веб-разработке",
            "ИИ и кибербезопасность: новые вызовы",
            "Этические аспекты искусственного интеллекта",
            "Автоматизация с помощью языковых моделей",
            "Компьютерное зрение и обработка изображений",
            "ИИ в медицине и здравоохранении",
            "Будущее работы в эпоху искусственного интеллекта",
            "Генерация видео с помощью нейросетей",
            "Персональные ИИ-ассистенты 2024",
            "Квантовые вычисления и машинное обучение",
            "ИИ для климатических изменений и экологии",
            "Нейроинтерфейсы и взаимодействие с мозгом",
            "Большие языковые модели в образовании",
            "Автономные системы и робототехника",
            "Диффузионные модели для генерации изображений",
            "Мультимодальные AI системы",
            "Edge computing и искусственный интеллект"
        ]
        
        # Пробуем получить темы из RSS (с улучшенной обработкой)
        rss_feeds = [
            "https://habr.com/ru/rss/articles/?fl=ru",
            "https://news.ycombinator.com/rss"
        ]
        
        for feed_url in rss_feeds:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:3]:  # Берем только первые 3
                    if 'title' in entry:
                        clean_title = clean_text(entry.title)
                        if clean_title and len(clean_title) > 20 and len(clean_title) < 120:
                            # Проверяем, что это не HTML и не содержит ссылок
                            if not any(char in clean_title for char in ['<', '>', 'http', '://']):
                                topics.append(clean_title)
            except Exception as e:
                print(f"⚠️ Ошибка парсинга RSS: {e}")
                continue
        
        topics.extend(current_trends)
        
        # Фильтруем и удаляем дубликаты
        unique_topics = []
        seen = set()
        for topic in topics:
            if (topic and topic not in seen and 
                15 <= len(topic) <= 100 and
                not any(char in topic for char in ['<', '>', 'http', '://'])):
                unique_topics.append(topic)
                seen.add(topic)
        
        return unique_topics[:20]
        
    except Exception as e:
        print(f"❌ Ошибка получения трендов: {e}")
        # Возвращаем гарантированно хорошие темы
        return [
            "Искусственный интеллект в веб-разработке 2024",
            "Генеративный ИИ для создания контента",
            "Машинное обучение и большие данные",
            "Нейросети в бизнес-автоматизации",
            "Будущее искусственного интеллекта"
        ]

def generate_article(topic, api_type="groq"):
    """Генерация статьи через Groq или OpenRouter"""
    try:
        # Дополнительная проверка темы
        if (not topic or len(topic) < 10 or len(topic) > 150 or
            any(char in topic for char in ['<', '>', 'http', '://'])):
            print(f"⚠️ Пропускаем некорректную тему: {topic}")
            return None
            
        if api_type == "groq":
            api_key = os.getenv('GROQ_API_KEY')
            url = "https://api.groq.com/openai/v1/chat/completions"
            model = "llama-3.1-70b-versatile"
        else:
            api_key = os.getenv('OPENROUTER_API_KEY')
            url = "https://openrouter.ai/api/v1/chat/completions"
            model = "meta-llama/llama-3.1-70b"
        
        if not api_key:
            print(f"❌ {api_type.upper()}_API_KEY not found")
            return None
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        if api_type == "openrouter":
            headers.update({
                "HTTP-Referer": "https://github.com/lybra-bee/lybra-bee.github.io",
                "X-Title": "AI Content Generator"
            })
        
        # Системный промпт
        system_prompt = """Ты профессиональный технический писатель и эксперт по искусственному интеллекту. 
Пиши подробные, информативные статьи на русском языке. Используй Markdown форматирование."""

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user", 
                    "content": f"Напиши подробную статью на тему: '{topic}'. Объем: 1000-1500 слов. Формат: Markdown."
                }
            ],
            "max_tokens": 3000,
            "temperature": 0.7
        }
        
        print(f"📝 Генерирую статью через {api_type.upper()}: {topic}")
        response = requests.post(url, headers=headers, json=payload, timeout=90)
        response.raise_for_status()
        
        content = response.json()['choices'][0]['message']['content']
        print(f"✅ Статья сгенерирована! Длина: {len(content)} символов")
        
        return content
        
    except Exception as e:
        print(f"❌ Ошибка генерации статьи ({api_type}): {e}")
        return None

def generate_image(prompt):
    """Генерация изображения через Hugging Face"""
    try:
        HF_TOKEN = os.getenv('HF_API_TOKEN')
        if not HF_TOKEN:
            print("⚠️ HF_API_TOKEN not found, пропускаем генерацию изображения")
            return None
        
        # Упрощаем промпт для изображения
        image_prompt = f"{prompt}, digital art, professional, 4k quality"
        print(f"🎨 Генерирую изображение: {image_prompt}")
        
        API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        
        payload = {
            "inputs": image_prompt,
            "parameters": {
                "width": 512,
                "height": 512
            }
        }
        
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 200:
            filename = f"image_{int(time.time())}.png"
            filepath = f"static/images/posts/{filename}"
            
            with open(filepath, "wb") as f:
                f.write(response.content)
            
            print(f"✅ Изображение создано: {filepath}")
            return filepath
        else:
            print(f"⚠️ Ошибка генерации изображения: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Ошибка генерации изображения: {e}")
        return None

def save_article(content, topic, image_path=None):
    """Сохранение статьи с front matter"""
    try:
        import re
        from datetime import date
        
        # Создаем SEO-дружественное имя файла
        clean_topic = re.sub(r'[^a-zA-Z0-9а-яА-Я\s]', '', topic)
        filename = re.sub(r'\s+', '-', clean_topic.lower())[:50]
        
        today = date.today().strftime("%Y-%m-%d")
        full_filename = f"content/posts/{today}-{filename}.md"
        
        # Front matter для Hugo
        front_matter = f"""---
title: "{topic}"
date: {today}
draft: false
description: "Статья о {topic}"
categories: ["Искусственный Интеллект"]
tags: ["ai", "технологии"]
"""
        
        # Добавляем изображение если есть
        if image_path:
            image_filename = os.path.basename(image_path)
            front_matter += f"image: \"/images/posts/{image_filename}\"\n"
        
        front_matter += "---\n"
        
        full_content = front_matter + content
        
        with open(full_filename, 'w', encoding='utf-8') as f:
            f.write(full_content)
        
        print(f"💾 Статья сохранена: {full_filename}")
        return full_filename
        
    except Exception as e:
        print(f"❌ Ошибка сохранения статьи: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description='AI Content Generator')
    parser.add_argument('--count', type=int, default=1, help='Number of articles')
    parser.add_argument('--debug', action='store_true', help='Debug mode')
    
    args = parser.parse_args()
    
    print("🔄 Запуск генератора контента...")
    print(f"📊 Количество статей: {args.count}")
    
    # Получаем актуальные темы
    print("📡 Получаю актуальные темы...")
    topics = get_trending_topics()
    
    if not topics:
        print("❌ Не удалось получить темы, используем fallback")
        topics = [
            "Искусственный интеллект в веб-разработке",
            "Генеративный ИИ для создания контента",
            "Машинное обучение и большие данные"
        ]
    
    selected_topics = topics[:args.count]
    print(f"🎯 Выбранные темы: {selected_topics}")
    
    generated_count = 0
    
    for i, topic in enumerate(selected_topics):
        print(f"\n📖 Генерация {i+1}/{len(selected_topics)}: {topic}")
        
        # Генерируем статью
        content = generate_article(topic, "groq")
        if not content:
            content = generate_article(topic, "openrouter")
        
        if content:
            # Генерируем изображение
            image_path = generate_image(topic)
            
            # Сохраняем статью
            article_path = save_article(content, topic, image_path)
            if article_path:
                generated_count += 1
                print(f"✅ Успешно: статья + {'изображение' if image_path else 'без изображения'}")
        else:
            print(f"❌ Не удалось сгенерировать статью")
    
    print(f"\n🎉 Генерация завершена! Успешно: {generated_count}/{len(selected_topics)}")

if __name__ == "__main__":
    main()
