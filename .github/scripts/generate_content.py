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
import subprocess

def generate_ai_trend_topic():
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
    print("🚀 Запуск генерации контента...")
    
    KEEP_LAST_ARTICLES = 3
    clean_old_articles(KEEP_LAST_ARTICLES)
    
    selected_topic = generate_ai_trend_topic()
    print(f"📝 Актуальная тема 2025: {selected_topic}")
    
    # Генерация изображения
    image_filename = generate_article_image(selected_topic)
    
    # Генерация текста
    content, model_used = generate_article_content(selected_topic)
    
    # Создаём Markdown
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
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    groq_key = os.getenv('GROQ_API_KEY')
    
    models_to_try = []
    
    if groq_key:
        groq_models = ["llama-3.1-8b-instant"]
        for model_name in groq_models:
            models_to_try.append((f"Groq-{model_name}", lambda m=model_name: generate_with_groq(groq_key, m, topic)))
    
    if openrouter_key:
        openrouter_models = ["anthropic/claude-3-haiku"]
        for model_name in openrouter_models:
            models_to_try.append((model_name, lambda m=model_name: generate_with_openrouter(openrouter_key, m, topic)))
    
    for model_name, generate_func in models_to_try:
        try:
            print(f"🔄 Пробуем: {model_name}")
            result = generate_func()
            if result and len(result.strip()) > 100:
                print(f"✅ Успешно через {model_name}")
                return result, model_name
            time.sleep(1)
        except Exception as e:
            print(f"⚠️ Ошибка {model_name}: {str(e)[:100]}")
            continue
    
    fallback_content = f"# {topic}\n\nАвтоматическая статья о {topic}."
    return fallback_content, "fallback-generator"

def generate_with_groq(api_key, model_name, topic):
    prompt = f"Напиши техническую статью на тему: {topic}"
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Content-Type": "application/json","Authorization": f"Bearer {api_key}"},
        json={"model": model_name,"messages":[{"role":"user","content":prompt}],"max_tokens":1500,"temperature":0.7},
        timeout=30
    )
    if response.status_code == 200:
        data = response.json()
        if data.get('choices'):
            return data['choices'][0]['message']['content'].strip()
    raise Exception(f"HTTP {response.status_code}: {response.text[:200]}")

def generate_with_openrouter(api_key, model_name, topic):
    prompt = f"Напиши техническую статью на тему: {topic}"
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Content-Type": "application/json","Authorization": f"Bearer {api_key}"},
        json={"model": model_name,"messages":[{"role":"user","content":prompt}],"max_tokens":1500,"temperature":0.7},
        timeout=30
    )
    if response.status_code == 200:
        data = response.json()
        if data.get('choices'):
            return data['choices'][0]['message']['content'].strip()
    raise Exception(f"HTTP {response.status_code}")

def generate_article_image(topic):
    print("🎨 Генерация изображения...")
    groq_key = os.getenv('GROQ_API_KEY')
    stability_key = os.getenv('STABILITYAI_KEY')
    
    # Сначала Groq
    if groq_key:
        try:
            prompt = f"Create tech image prompt for article: {topic}"
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Content-Type": "application/json","Authorization": f"Bearer {groq_key}"},
                json={"model":"llama-3.1-8b-instant","messages":[{"role":"user","content":prompt}],"max_tokens":50},
                timeout=15
            )
            if response.status_code==200:
                data=response.json()
                img_prompt=data['choices'][0]['message']['content'].strip()
                filename=try_stability_ai(img_prompt, topic)
                if filename:
                    return filename
        except Exception as e:
            print(f"⚠️ Groq image prompt error: {e}")
    
    # Stability AI fallback
    if stability_key:
        filename = try_stability_ai(f"Tech futuristic image: {topic}", topic)
        if filename:
            return filename
    
    print("ℹ️ Не удалось создать изображение, пропускаем")
    return None

def try_stability_ai(prompt, topic):
    stability_key = os.getenv('STABILITYAI_KEY')
    if not stability_key:
        return None
    url="https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
    headers={"Authorization": f"Bearer {stability_key}","Content-Type":"application/json"}
    payload={"text_prompts":[{"text":prompt}],"cfg_scale":7,"height":512,"width":512,"samples":1,"steps":20}
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    if response.status_code==200:
        data=response.json()
        if 'artifacts' in data and data['artifacts']:
            img_data=base64.b64decode(data['artifacts'][0]['base64'])
            return save_article_image(img_data, topic)
    return None

def save_article_image(image_data, topic):
    try:
        os.makedirs("static/images/posts", exist_ok=True)
        slug = generate_slug(topic)
        filename=f"posts/{slug}.jpg"
        full_path=f"static/images/{filename}"
        with open(full_path,'wb') as f:
            f.write(image_data)
        return f"/images/{filename}"
    except:
        return None

def clean_old_articles(keep_last=3):
    articles=glob.glob("content/posts/*.md")
    articles.sort(key=os.path.getmtime, reverse=True)
    for article in articles[keep_last:]:
        os.remove(article)
        slug=os.path.basename(article).replace(".md","")
        img_path=f"static/images/posts/{slug}.jpg"
        if os.path.exists(img_path):
            os.remove(img_path)

def generate_slug(topic):
    slug = topic.lower()
    for ch in [' ',':','(',')','/','\\','.',',','--']:
        slug=slug.replace(ch,'-')
    slug=''.join(c for c in slug if c.isalnum() or c=='-')
    while '--' in slug:
        slug=slug.replace('--','-')
    return slug[:50]

def generate_frontmatter(topic, content, model_used, image_filename=None):
    frontmatter=f"---\ntitle: \"{topic}\"\ndate: {datetime.now().strftime('%Y-%m-%d')}\nmodel: {model_used}\n"
    if image_filename:
        frontmatter+=f"image: \"{image_filename}\"\n"
    frontmatter+="---\n\n"
    frontmatter+=content
    return frontmatter

if __name__=="__main__":
    filename = generate_content()
    print("📦 Генерация завершена, запускаем Hugo...")
    subprocess.run(["hugo", "--minify"])
