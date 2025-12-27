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
def generate_image_horde(prompt, timeout=600):
    url = "https://stablehorde.net/api/v2/generate/async"
    headers = {
        "apikey": HORDE_API_KEY,
        "Client-Agent": "LybraAI Bot:1.0:github.com/lybra-bee"
    }
    full_prompt = prompt + ", photorealistic, high resolution, detailed, relevant to article content"
    payload = {"prompt": full_prompt, "params": {"width":512, "height":512, "steps":30}}

    start_time = time.time()
    while time.time() - start_time < timeout:
        r = requests.post(url, headers=headers, json=payload)
        if r.status_code == 429:
            logging.warning("Horde limit reached, ждем 10 секунд")
            time.sleep(10)
            continue
        if not r.ok:
            logging.warning(f"Horde returned {r.status_code}: {r.text}")
            break
        task_id = r.json().get("id")
        if not task_id:
            break
        # Polling
        for _ in range(100):
            time.sleep(5)
            resp = requests.get(f"https://stablehorde.net/api/v2/generate/check/{task_id}", headers=headers)
            if resp.status_code != 200:
                continue
            result = resp.json()
            if result.get("done"):
                status_resp = requests.get(f"https://stablehorde.net/api/v2/generate/status/{task_id}", headers=headers)
                if status_resp.status_code == 200:
                    status_result = status_resp.json()
                    img_data = status_result["generations"][0]["img"]
                    img_path = IMAGES_DIR / f"post-{int(time.time())}.png"
                    with open(img_path, "wb") as f:
                        f.write(base64.b64decode(img_data))
                    return str(img_path)
            # Optional: use wait_time
            wait = result.get("wait_time", 5)
            time.sleep(max(5, wait))
    logging.warning("Horde failed → fallback")
    return None

def generate_image_clipdrop(prompt):
    url = "https://clipdrop-api.co/text-to-image/v1"
    headers = {"x-api-key": CLIPDROP_API_KEY}
    full_prompt = prompt + ", photorealistic, high resolution, detailed, relevant to article content"
    try:
        r = requests.post(url, headers=headers, files={'prompt': (None, full_prompt, 'text/plain')})
        if r.status_code != 200:
            logging.warning(f"ClipDrop returned {r.status_code}: {r.text}")
            return None
        img_path = IMAGES_DIR / f"post-{int(time.time())}.png"
        with open(img_path, "wb") as f:
            f.write(r.content)
        return str(img_path)
    except Exception as e:
        logging.warning(f"ClipDrop error: {e}")
        return None

def generate_image(prompt):
    img = generate_image_horde(prompt)
    if img:
        return img
    img = generate_image_clipdrop(prompt)
    if img:
        return img
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
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logging.warning("Telegram ключи отсутствуют, пропускаем")
        return
    teaser = ' '.join(body.split()[:30]) + '…'
    def esc(text): return re.sub(r'([_*\[\]\(\)~`>#+\-=|{}.!])', r'\\\1', text)
    message = f"*Новая статья*\n\n{esc(teaser)}\n\n[Читать на сайте](https://lybra-ai.ru)\n\n{esc('#ИИ #LybraAI')}"
    try:
        if image_path.startswith('http'):
            r = requests.get(image_path)
            r.raise_for_status()
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            temp_file.write(r.content)
            temp_file.close()
            image_file = temp_file.name
        else:
            image_file = image_path
        resp = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto",
            data={"chat_id": TELEGRAM_CHAT_ID, "caption": message, "parse_mode": "MarkdownV2"},
            files={"photo": open(image_file, "rb")}
        )
        logging.info(f"Telegram status {resp.status_code}")
        if image_path.startswith('http'):
            os.unlink(image_file)
    except Exception as e:
        logging.warning(f"Telegram error: {e}")

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
