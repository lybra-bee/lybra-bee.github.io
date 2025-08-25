#!/usr/bin/env python3
import os
import json
import requests
import random
from datetime import datetime

def generate_content():
    # Конфигурация
    topics = [
        "Веб-фреймворки 2024: React, Vue, Svelte",
        "Serverless архитектура для веб-приложений", 
        "Искусственный интеллект в веб-разработке",
        "Прогрессивные веб-приложения (PWA)",
        "Кибербезопасность веб-приложений"
    ]
    
    selected_topic = random.choice(topics)
    print(f"📝 Тема: {selected_topic}")
    
    # Попытка генерации через OpenRouter
    api_key = os.getenv('OPENROUTER_API_KEY')
    content = ""
    
    if api_key:
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                },
                json={
                    "model": "google/palm-2-chat-bison-32k:free",
                    "messages": [
                        {
                            "role": "user",
                            "content": f"Напиши короткий технический абзац о {selected_topic} на русском. 100-200 слов."
                        }
                    ],
                    "max_tokens": 300
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data['choices'][0]['message']['content']
                print("✅ Успешная генерация через API")
            else:
                raise Exception(f"API error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Ошибка API: {e}")
            content = f"Это статья о {selected_topic}. Сгенерировано автоматически."
    else:
        print("⚠️ API ключ не найден")
        content = f"Это статья о {selected_topic}. Сгенерировано автоматически."
    
    # Создаем файл
    date = datetime.now().strftime("%Y-%m-%d")
    slug = selected_topic.lower().replace(' ', '-').replace(':', '')[:30]
    filename = f"content/posts/{date}-{slug}.md"
    
    frontmatter = f"""---
title: "{selected_topic}"
date: {datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}
draft: false
tags: ["веб-разработка", "технологии"]
---

# {selected_topic}

{content}

> *Сгенерировано автоматически {datetime.now().strftime("%d.%m.%Y %H:%M")}*
"""
    
    os.makedirs("content/posts", exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(frontmatter)
    
    print(f"✅ Файл создан: {filename}")
    return filename

if __name__ == "__main__":
    generate_content()
