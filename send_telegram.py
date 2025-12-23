import os
import re
import requests

POST_FILE = os.getenv("POST_FILE")
IMAGE_URL = os.getenv("image_url")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID  = os.getenv("TELEGRAM_CHAT_ID")

if not POST_FILE or not os.path.exists(POST_FILE):
    print("⚠️ Пост не найден — Telegram пропущен")
    exit(0)

with open(POST_FILE, encoding="utf-8") as f:
    content = f.read().split('---')[-1].strip()

teaser = " ".join(content.split()[:35]) + "…"

def esc(text):
    return re.sub(r'([_*\[\]\(\)~`>#+\-=|{}.!])', r'\\\1', text)

message = (
    "*Новая статья про ИИ*\n\n"
    f"{esc(teaser)}\n\n"
    "[Читать на сайте](https://lybra-ai.ru)\n\n"
    f"{esc('#ИИ #AI #LybraAI')}"
)

try:
    photo = requests.get(IMAGE_URL, timeout=20).content

    resp = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
        data={
            "chat_id": CHAT_ID,
            "caption": message,
            "parse_mode": "MarkdownV2"
        },
        files={"photo": photo},
        timeout=30
    )

    print("✅ Telegram status:", resp.status_code)

except Exception as e:
    print("⚠️ Ошибка Telegram:", e)
