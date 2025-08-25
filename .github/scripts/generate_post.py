import requests
import os
from datetime import datetime

# Конфигурация
HF_API_KEY = os.getenv('HF_API_KEY')
REPO_PATH = os.getenv('GITHUB_WORKSPACE', '.')

def generate_with_huggingface(prompt):
    """Генерация текста через Hugging Face"""
    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 500,
            "temperature": 0.7
        }
    }
    
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()[0]['generated_text']

def create_blog_post():
    """Создание нового поста"""
    topics = [
        "Веб-дизайн тенденции 2024",
        "JavaScript советы для начинающих",
        "CSS трюки для современного дизайна",
        "Автоматизация веб-разработки",
        "Нейросети в программировании"
    ]
    
    # Выбираем случайную тему
    topic = topics[datetime.now().day % len(topics)]
    
    # Генерируем контент
    prompt = f"{topic}. Напиши развернутую статью на эту тему для технического блога. Верни ответ в формате Markdown."
    content = generate_with_huggingface(prompt)
    
    # Создаем файл
    filename = f"content/posts/{datetime.now().strftime('%Y-%m-%d')}-{topic.lower().replace(' ', '-')}.md"
    
    front_matter = f"""---
title: "{topic}"
date: {datetime.now().isoformat()}
draft: false
description: "Автоматически сгенерированная статья"
tags: ["ai", "автоматизация"]
---

{content}
"""
    
    with open(os.path.join(REPO_PATH, filename), 'w', encoding='utf-8') as f:
        f.write(front_matter)
    
    print(f"Создан пост: {filename}")

if __name__ == "__main__":
    create_blog_post()
