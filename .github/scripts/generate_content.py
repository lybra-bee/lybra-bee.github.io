import requests
import os
import time
import argparse
import json
import random
from datetime import datetime, timedelta
import feedparser
from PIL import Image
import io

def get_trending_topics():
    """Получение актуальных тем из RSS и новостей"""
    try:
        topics = []
        
        # RSS источники для актуальных тем
        rss_feeds = [
            "https://habr.com/ru/rss/articles/?fl=ru",
            "https://news.ycombinator.com/rss",
            "https://www.reddit.com/r/MachineLearning/.rss"
        ]
        
        for feed_url in rss_feeds:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:10]:
                    if 'title' in entry:
                        topics.append(entry.title)
                        if 'summary' in entry:
                            topics.append(entry.summary[:100])
            except:
                continue
        
        # Добавляем актуальные темы по AI
        current_trends = [
            "Новые возможности GPT-5 и ИИ будущего",
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
            "Нейроинтерфейсы и brain-computer interfaces"
        ]
        
        topics.extend(current_trends)
        return list(set(topics))[:20]  # Убираем дубли
        
    except Exception as e:
        print(f"❌ Ошибка получения трендов: {e}")
        return [
            "Искусственный интеллект в веб-разработке 2024",
            "Генеративный ИИ для создания контента",
            "Машинное обучение и большие данные",
            "Нейросети в бизнес-автоматизации"
        ]

def generate_article(topic, api_type="groq"):
    """Генерация статьи через Groq или OpenRouter"""
    try:
        if api_type == "groq":
            api_key = os.getenv('GROQ_API_KEY')
            url = "https://api.groq.com/openai/v1/chat/completions"
            model = "llama-3.1-70b-versatile"
        else:
            api_key = os.getenv('OPENROUTER_API_KEY')
            url = "https://openrouter.ai/api/v1/chat/completions"
            model = "meta-llama/llama-3.1-70b"
        
        if not api_key:
            raise ValueError(f"{api_type.upper()}_API_KEY not found")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        if api_type == "openrouter":
            headers.update({
                "HTTP-Referer": "https://github.com/lybra-bee/lybra-bee.github.io",
                "X-Title": "AI Content Generator"
            })
        
        # Системный промпт для качественной статьи
        system_prompt = """Ты профессиональный технический писатель и эксперт по искусственному интеллекту. 
Пиши подробные, информативные и хорошо структурированные статьи на русском языке. 
Используй заголовки H2, H3, списки и примеры. Статья должна быть полезной и практичной."""

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user", 
                    "content": f"Напиши развернутую статью на тему: '{topic}'. Объем: 1500-2000 слов. Включи практические примеры, кейсы использования и будущие тренды. Формат: Markdown с заголовками ## и ###."
                }
            ],
            "max_tokens": 4000,
            "temperature": 0.7,
            "top_p": 0.9
        }
        
        print(f"📝 Генерирую статью через {api_type.upper()}: {topic}")
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        
        content = response.json()['choices'][0]['message']['content']
        print(f"✅ Статья сгенерирована! Длина: {len(content)} символов")
        
        return content
        
    except Exception as e:
        print(f"❌ Ошибка генерации статьи ({api_type}): {e}")
        return None

def generate_image(prompt, retry_count=0):
    """Генерация изображения через Hugging Face с fallback"""
    try:
        # Сначала пробуем Hugging Face
        HF_TOKEN = os.getenv('HF_API_TOKEN')
        if HF_TOKEN and retry_count < 2:
            try:
                print(f"🎨 Пробую Hugging Face: {prompt}")
                
                API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
                headers = {"Authorization": f"Bearer {HF_TOKEN}"}
                
                payload = {
                    "inputs": f"{prompt}, digital art, futuristic, professional, 4k, ultra detailed, high quality",
                    "parameters": {
                        "width": 1024,
                        "height": 512,
                        "num_inference_steps": 25,
                        "guidance_scale": 7.5
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
                    print(f"⚠️ HF вернул {response.status_code}, пробую fallback...")
            except:
                pass
        
        # Fallback: Replicate
        REPLICATE_TOKEN = os.getenv('REPLICATE_API_TOKEN')
        if REPLICATE_TOKEN:
            try:
                print(f"🔄 Пробую Replicate: {prompt}")
                
                response = requests.post(
                    "https://api.replicate.com/v1/predictions",
                    headers={
                        "Authorization": f"Token {REPLICATE_TOKEN}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "version": "ac732df83cea7fff18b8472768c88ad041fa750ff7682a21affe81863cbe77e4",
                        "input": {
                            "prompt": f"{prompt}, digital art, professional, 4k quality",
                            "width": 1024,
                            "height": 512,
                            "num_outputs": 1
                        }
                    },
                    timeout=60
                )
                
                if response.status_code == 200:
                    prediction_id = response.json()['id']
                    
                    # Ждем завершения
                    for _ in range(10):
                        time.sleep(5)
                        status_response = requests.get(
                            f"https://api.replicate.com/v1/predictions/{prediction_id}",
                            headers={"Authorization": f"Token {REPLICATE_TOKEN}"}
                        )
                        
                        if status_response.json()['status'] == 'succeeded':
                            image_url = status_response.json()['output'][0]
                            img_data = requests.get(image_url).content
                            
                            filename = f"image_{int(time.time())}.png"
                            filepath = f"static/images/posts/{filename}"
                            
                            with open(filepath, "wb") as f:
                                f.write(img_data)
                            
                            print(f"✅ Изображение создано через Replicate: {filepath}")
                            return filepath
                
            except:
                pass
        
        # Final fallback: Unsplash
        UNSPLASH_KEY = os.getenv('UNSPLASH_API_KEY')
        if UNSPLASH_KEY:
            try:
                print(f"🌅 Пробую Unsplash: {prompt}")
                
                search_url = "https://api.unsplash.com/search/photos"
                headers = {"Authorization": f"Client-ID {UNSPLASH_KEY}"}
                
                search_response = requests.get(
                    search_url,
                    headers=headers,
                    params={"query": prompt, "per_page": 1},
                    timeout=30
                )
                
                if search_response.status_code == 200:
                    results = search_response.json()['results']
                    if results:
                        image_url = results[0]['urls']['regular']
                        img_data = requests.get(image_url).content
                        
                        filename = f"unsplash_{int(time.time())}.jpg"
                        filepath = f"static/images/posts/{filename}"
                        
                        with open(filepath, "wb") as f:
                            f.write(img_data)
                        
                        print(f"✅ Изображение с Unsplash: {filepath}")
                        return filepath
            except:
                pass
        
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
description: "Автоматически сгенерированная статья на тему {topic}"
categories: ["Искусственный Интеллект", "Технологии"]
tags: ["ai", "генерация", "технологии", "нейросети"]
---
"""
        
        # Добавляем изображение если есть
        if image_path:
            image_filename = os.path.basename(image_path)
            front_matter = front_matter.replace('---', f'---\nimage: "/images/posts/{image_filename}"')
        
        full_content = front_matter + "\n" + content
        
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
    selected_topics = random.sample(topics, min(args.count, len(topics)))
    
    generated_count = 0
    
    for i, topic in enumerate(selected_topics):
        print(f"\n📖 Генерация {i+1}/{len(selected_topics)}: {topic}")
        
        # Генерируем статью
        content = generate_article(topic, "groq")
        if not content:
            content = generate_article(topic, "openrouter")
        
        if content:
            # Генерируем изображение
            image_prompt = f"{topic}, digital art, futuristic style"
            image_path = generate_image(image_prompt)
            
            # Сохраняем статью
            article_path = save_article(content, topic, image_path)
            if article_path:
                generated_count += 1
        else:
            print(f"❌ Не удалось сгенерировать статью: {topic}")
    
    print(f"\n✅ Генерация завершена! Успешно: {generated_count}/{len(selected_topics)}")

if __name__ == "__main__":
    main()
