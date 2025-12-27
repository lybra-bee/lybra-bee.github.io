#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, re, time, json, random, logging, requests
from datetime import datetime
from pathlib import Path
import base64
import tempfile

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

# -------------------- Папки --------------------
POSTS_DIR = Path("_posts")
IMAGES_DIR = Path("assets/images/posts")
POSTS_DIR.mkdir(exist_ok=True)
IMAGES_DIR.mkdir(exist_ok=True)

# -------------------- API ключи --------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
HORDE_API_KEY = os.getenv("HORDE_API_KEY")
CLIPDROP_API_KEY = os.getenv("CLIPDROP_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
FUSIONBRAIN_API_KEY = os.getenv("FUSIONBRAIN_API_KEY")
FUSION_SECRET_KEY = os.getenv("FUSION_SECRET_KEY")

FALLBACK_IMAGES = [
    "https://picsum.photos/800/600?random=1",
    "https://picsum.photos/800/600?random=2",
    "https://picsum.photos/800/600?random=3",
]

# -------------------- Статья --------------------
def generate_article(topic):
    groq_model = "llama-3.3-70b-versatile"
    system_prompt = f"Напиши статью на тему '{topic}' без политики, скандалов, морали. Заголовок должен быть уникальным."
    user_prompt = "Пожалуйста, сформируй текст: ЗАГОЛОВОК: ... ТЕКСТ: ..."

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    payload = {
        "model": groq_model,
        "messages": [{"role": "system", "content": system_prompt},
                     {"role": "user", "content": user_prompt}],
        "max_tokens": 1024,
        "temperature": 0.8,
    }

    forbidden_words = ["политика", "скандал", "мораль", "регуляция", "политик", "политический", "регулирование", "скандальный", "моральный"]

    for attempt in range(5):
        logging.info(f"Article attempt {attempt+1}: {topic}")
        try:
            r = requests.post(url, headers=headers, json=payload)
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.error(f"Groq error: {e}")
            time.sleep(2)
            continue
        data = r.json()
        text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        if not text:
            continue
        if any(word in text.lower() for word in forbidden_words):
            logging.warning("Обнаружен запрещенный контент — регенерация")
            continue
        title_match = re.search(r"ЗАГОЛОВОК:\s*(.+)", text)
        body_match = re.search(r"ТЕКСТ:\s*(.+)", text, re.DOTALL)
        if not title_match or not body_match:
            continue
        return title_match.group(1).strip(), body_match.group(1).strip()
    raise RuntimeError("Groq article generation failed")

# -------------------- Изображение --------------------
def generate_image_kandinsky(prompt, timeout=600):
    if not FUSIONBRAIN_API_KEY or not FUSION_SECRET_KEY:
        logging.warning("Kandinsky keys absent, skipping")
        return None

    base_url = "https://api-key.fusionbrain.ai/key/api/v1"
    headers = {
        "X-Key": f"Key {FUSIONBRAIN_API_KEY}",
        "X-Secret": f"Secret {FUSION_SECRET_KEY}",
    }

    # Get model_id (pipeline)
    try:
        r = requests.get(f"{base_url}/pipelines", headers=headers)
        if not r.ok:
            logging.warning(f"Kandinsky pipelines error {r.status_code}: {r.text}")
            return None
        models = r.json()
        model_id = models[0]["id"]  # First active TEXT2IMAGE, usually Kandinsky 3.1
    except Exception as e:
        logging.warning(f"Kandinsky model fetch error: {e}")
        return None

    full_prompt = prompt + ", photorealistic, high resolution, detailed, relevant to article content"

    # Request generation
    params = {"type": "GENERATE", "numImages": 1, "width": 1024, "height": 1024, "generateParams": {"query": full_prompt}}
    files = {
        "model_id": (None, model_id),
        "params": (None, json.dumps(params), "application/json")
    }

    start_time = time.time()
    try:
        r = requests.post(f"{base_url}/text2image/run", headers=headers, files=files)
        if not r.ok:
            logging.warning(f"Kandinsky run error {r.status_code}: {r.text}")
            return None
        uuid = r.json()["uuid"]
    except Exception as e:
        logging.warning(f"Kandinsky run error: {e}")
        return None

    # Polling
    while time.time() - start_time < timeout:
        try:
            r = requests.get(f"{base_url}/text2image/status/{uuid}", headers=headers)
            if not r.ok:
                time.sleep(10)
                continue
            data = r.json()
            status = data["status"]
            if status == "DONE":
                img_data = data["images"][0]
                img_path = IMAGES_DIR / f"post-{int(time.time())}.jpg"
                with open(img_path, "wb") as f:
                    f.write(base64.b64decode(img_data))
                logging.info(f"Image generated by Kandinsky: {img_path}")
                return str(img_path)
            elif status == "FAILED":
                logging.warning("Kandinsky generation failed")
                return None
            time.sleep(10)
        except Exception:
            time.sleep(10)
    logging.warning("Kandinsky timeout → fallback")
    return None

def generate_image_horde(prompt, timeout=900):
    # (оставляем как есть, код из предыдущей версии)
    # ... (полный код функции из предыдущего ответа)

def generate_image_clipdrop(prompt):
    # (оставляем как есть)

def generate_image(prompt):
    img = generate_image_kandinsky(prompt)
    if img:
        return img
    img = generate_image_horde(prompt)
    if img:
        return img
    img = generate_image_clipdrop(prompt)
    if img:
        return img
    logging.warning("All generators failed → using fallback URL")
    return random.choice(FALLBACK_IMAGES)

# -------------------- Сохранение --------------------
def save_post(title, body):
    today = datetime.now().strftime("%Y-%m-%d")
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', title.lower()).strip('-')
    if not slug:
        slug = "ai-post"
    filename = POSTS_DIR / f"{today}-{slug}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"---\ntitle: {title}\ndate: {today}\n---\n\n{body}\n")
    logging.info(f"Saved post: {filename}")
    return filename

# -------------------- Telegram --------------------
def send_to_telegram(title, body, image_path):
    # (оставляем как есть из предыдущей версии, с обработкой fallback)

# -------------------- MAIN --------------------
def main():
    topics = ["ИИ в автоматизации контента", "Мультимодальные модели", "Генеративные модели 2025"]
    topic = random.choice(topics)

    title, body = generate_article(topic)
    img_path = generate_image(title)
    post_file = save_post(title, body)
    send_to_telegram(title, body, img_path)
    logging.info("=== DONE ===")

if __name__ == "__main__":
    main()
