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
    client_id = os.getenv('GIGACHAT_CLIENT_ID')
    client_secret = os.getenv('GIGACHAT_CLIENT_SECRET')
    if not client_id or not client_secret:
        print("❌ GigaChat credentials missing")
        return None
    auth_string = f"{client_id}:{client_secret}"
    auth_key = base64.b64encode(auth_string.encode()).decode()
    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "RqUID": f"rq-{random.randint(100000,999999)}-{int(time.time())}",
        "Authorization": f"Basic {auth_key}"
    }
    data = {"scope":"GIGACHAT_API_PERS"}
    try:
        resp = requests.post(url, headers=headers, data=data, verify=False, timeout=30)
        if resp.status_code == 200:
            return resp.json().get("access_token")
    except Exception as e:
        print(f"❌ GigaChat token error: {e}")
    return None

def generate_ai_trend_topic():
    trends = [
        "Multimodal AI", "AI агенты", "Квантовые вычисления и ML",
        "Нейроморфные вычисления", "Generative AI", "Edge AI",
        "AI для кибербезопасности", "Этичный AI", "AI в healthcare",
        "Автономные системы", "AI оптимизация", "Доверенный AI",
        "AI для климата", "Персональные AI ассистенты", "AI в образовании"
    ]
    domains = [
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
    trend = random.choice(trends)
    domain = random.choice(domains)
    formats = [
        f"{trend} {domain} в 2025 году",
        f"Тенденции 2025: {trend} {domain}",
        f"{trend} - революционные изменения {domain} в 2025",
        f"Как {trend} трансформирует {domain} в 2025 году",
        f"Инновации 2025: {trend} для {domain}",
        f"{trend} - будущее {domain} в 2025 году",
        f"Практическое применение {trend} в {domain} 2025"
    ]
    return random.choice(formats)

def generate_slug(topic):
    slug = topic.lower()
    replacements = {' ': '-', ':': '', '(': '', ')': '', '/': '-', '\\': '-', '.': '', ',': '', '--': '-'}
    for old, new in replacements.items():
        slug = slug.replace(old,new)
    slug = ''.join(c for c in slug if c.isalnum() or c=='-')
    while '--' in slug:
        slug = slug.replace('--','-')
    return slug[:50]

def clean_old_articles(keep_last=3):
    articles = glob.glob("content/posts/*.md")
    if not articles:
        return
    articles.sort(key=os.path.getmtime)
    for f in articles[:-keep_last]:
        os.remove(f)

def save_article_image(image_data, topic):
    os.makedirs("static/images/posts", exist_ok=True)
    slug = generate_slug(topic)
    filename = f"images/posts/{slug}.jpg"
    full_path = f"static/{filename}"
    with open(full_path,'wb') as f:
        f.write(image_data)
    return filename

def generate_frontmatter(topic, content, model_used, image_filename=None):
    now = datetime.utcnow()
    tags = ["искусственный-интеллект","технологии","инновации","2025","ai"]
    image_line = f"image: {image_filename}\n" if image_filename else ""
    return f"""---
title: "{topic}"
date: {now.strftime("%Y-%m-%dT%H:%M:%SZ")}
draft: false
description: "Автоматически сгенерированная статья о {topic}"
{image_line}tags: {json.dumps(tags, ensure_ascii=False)}
categories: ["Технологии"]
---

# {topic}

{f'![]({image_filename})' if image_filename else ''}

{content}

---

### 🔧 Технические детали

- **Модель AI:** {model_used}
- **Дата генерации:** {now.strftime("%d.%m.%Y %H:%M UTC")}
- **Тема:** {topic}
- **Год актуальности:** 2025
- **Статус:** Чистая AI генерация

> *Сгенерировано автоматически через GitHub Actions*
"""

def generate_article_image(topic):
    print("🎨 Генерация изображения...")
    prompt = f"Technology illustration 2025 for article about {topic}. Futuristic, professional, AI concept."
    apis = [
        {"name":"Stability AI","func":try_stability_ai},
        {"name":"HuggingFace SD","func":try_huggingface_sd},
        {"name":"DeepAI","func":try_deepai_api},
        {"name":"GigaChat","func":try_gigachat_image}
    ]
    for api in apis:
        try:
            print(f"🔄 Пробуем {api['name']}")
            result = api['func'](prompt, topic)
            if result:
                return result
        except Exception as e:
            print(f"⚠️ Ошибка {api['name']}: {e}")
            continue
    print("❌ Не удалось сгенерировать изображение")
    return None

def try_stability_ai(prompt, topic):
    key = os.getenv('STABILITYAI_KEY')
    if not key:
        return None
    url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
    headers = {"Authorization": f"Bearer {key}", "Content-Type":"application/json"}
    payload = {"text_prompts":[{"text":prompt}], "width":1024,"height":1024,"samples":1,"steps":30,"cfg_scale":7}
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    if r.status_code == 200 and 'artifacts' in r.json() and r.json()['artifacts']:
        img_data = base64.b64decode(r.json()['artifacts'][0]['base64'])
        return save_article_image(img_data, topic)
    return None

def try_huggingface_sd(prompt, topic):
    token = os.getenv('HUGGINGFACE_TOKEN')
    models = ["stabilityai/stable-diffusion-2-1","runwayml/stable-diffusion-v1-5","prompthero/openjourney"]
    for model in models:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        payload = {"inputs":prompt,"parameters":{"width":800,"height":400,"num_inference_steps":20,"guidance_scale":7.5}}
        r = requests.post(f"https://api-inference.huggingface.co/models/{model}", headers=headers, json=payload, timeout=30)
        if r.status_code==200:
            return save_article_image(r.content, topic)
    return None

def try_deepai_api(prompt, topic):
    headers = {"api-key":"quickstart-QUdJIGlzIGNvbWluZy4uLi4K"}
    data = {"text":prompt}
    r = requests.post("https://api.deepai.org/api/text2img", headers=headers, data=data, timeout=30)
    if r.status_code==200:
        url = r.json().get('output_url')
        if url:
            img_r = requests.get(url, timeout=30)
            if img_r.status_code==200:
                return save_article_image(img_r.content, topic)
    return None

def try_gigachat_image(prompt, topic):
    token = get_gigachat_token()
    if not token:
        return None
    url = "https://gigachat.devices.sberbank.ru/api/v1/image/generate"
    headers = {"Authorization":f"Bearer {token}","Content-Type":"application/json"}
    payload = {"prompt":prompt,"size":"1024x1024"}
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    if r.status_code==200:
        data = r.json()
        if 'image_base64' in data:
            img_data = base64.b64decode(data['image_base64'])
            return save_article_image(img_data, topic)
    return None

def generate_article_content(topic):
    api_key = os.getenv('OPENROUTER_API_KEY')
    if api_key:
        prompt = f"Напиши развернутую техническую статью на тему: {topic} в Markdown, 500-700 слов."
        headers = {"Authorization":f"Bearer {api_key}","Content-Type":"application/json"}
        r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers,
                          json={"model":"mistralai/mistral-7b-instruct","messages":[{"role":"user","content":prompt}],"max_tokens":1500,"temperature":0.7})
        if r.status_code==200 and r.json().get('choices'):
            return r.json()['choices'][0]['message']['content'], "OpenRouter"
    return f"Статья по теме {topic} (контент AI)", "OpenRouter"

def generate_content():
    KEEP_LAST_ARTICLES = 3
    clean_old_articles(KEEP_LAST_ARTICLES)
    topic = generate_ai_trend_topic()
    slug = generate_slug(topic)
    date = datetime.now().strftime("%Y-%m-%d")
    filename = f"content/posts/{date}-{slug}.md"

    content, model_used = generate_article_content(topic)
    image_filename = generate_article_image(topic)

    frontmatter = generate_frontmatter(topic, content, model_used, image_filename)
    os.makedirs("content/posts", exist_ok=True)
    with open(filename,'w',encoding='utf-8') as f:
        f.write(frontmatter)

    print(f"✅ Статья создана: {filename}")
    return filename

if __name__=="__main__":
    try:
        generate_content()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        exit(1)
