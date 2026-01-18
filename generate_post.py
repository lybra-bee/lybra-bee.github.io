#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import time
import random
import logging
import requests
import tempfile
from datetime import datetime
from pathlib import Path

# Optional: pytrends (Google Trends)
try:
    from pytrends.request import TrendReq
except Exception:
    TrendReq = None

# ---------------- logging ----------------
LOG_FILE = "generation.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, encoding="utf-8")
    ],
)

log = logging.getLogger(__name__)

# -------------------- Папки --------------------
ROOT = Path(".")
POSTS_DIR = ROOT / "_posts"
IMAGES_DIR = ROOT / "assets" / "images" / "posts"
POSTS_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# -------------------- История тем --------------------
HISTORY_FILE = ROOT / ".topics_history"
MAX_HISTORY = 40

def load_history():
    if not HISTORY_FILE.exists():
        return []
    try:
        return HISTORY_FILE.read_text(encoding="utf-8").splitlines()
    except Exception:
        return []

def save_history(history):
    try:
        HISTORY_FILE.write_text("\n".join(history[-MAX_HISTORY:]), encoding="utf-8")
    except Exception as e:
        log.warning("Не удалось сохранить историю тем: %s", e)

# -------------------- API ключи --------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
HORDE_API_KEY = os.getenv("HORDE_API_KEY") or os.getenv("AIHORDE_API_KEY")

SITE_URL = os.getenv("SITE_URL", "https://lybra-ai.ru")

if not GROQ_API_KEY:
    log.warning("GROQ_API_KEY не установлен — генерация через Groq не будет работать!")

# -------------------- Фолбэки --------------------
FALLBACK_IMAGES = [
    "https://picsum.photos/1024/768?random=1",
    "https://picsum.photos/1024/768?random=2",
    "https://picsum.photos/1024/768?random=3",
    "https://picsum.photos/1024/768?random=4",
    "https://picsum.photos/1024/768?random=5",
]

# -------------------- Транслит --------------------
TRANSLIT_MAP = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
    'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
}
def translit(text):
    return ''.join(TRANSLIT_MAP.get(c, c) for c in text.lower())

# -------------------- Rate limit & Groq helper --------------------
LAST_REQUEST_TS = 0
MIN_INTERVAL = float(os.getenv("GROQ_MIN_INTERVAL", "1.5"))  # sec between Groq requests

def rate_limit():
    global LAST_REQUEST_TS
    now = time.time()
    diff = now - LAST_REQUEST_TS
    if diff < MIN_INTERVAL:
        to_sleep = MIN_INTERVAL - diff
        log.debug("Rate limit sleep: %.2fs", to_sleep)
        time.sleep(to_sleep)
    LAST_REQUEST_TS = time.time()

def groq_chat(prompt, model=None, max_tokens=1200, temperature=0.6, attempts=4):
    """
    Универсальный вызов Groq chat completions с retry и rate limiting.
    model: строка модели, если None — используем стандарт.
    """
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY не задан")

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}

    # выбор модели: можно переопределить через переменную окружения GROQ_MODEL
    groq_model = model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    payload = {
        "model": groq_model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    last_exc = None
    for attempt in range(1, attempts + 1):
        try:
            rate_limit()
            log.info("Groq request (model=%s, max_tokens=%s) attempt %d/%d", groq_model, max_tokens, attempt, attempts)
            r = requests.post(url, headers=headers, json=payload, timeout=90)
            if r.status_code == 429:
                # Too many requests - exponential backoff
                wait = min(30, 2 ** attempt)
                log.warning("Groq 429 Too Many Requests — ждем %ds (attempt %d/%d)", wait, attempt, attempts)
                time.sleep(wait)
                last_exc = RuntimeError(f"429 attempt {attempt}")
                continue
            if r.status_code >= 500:
                wait = min(30, 2 ** attempt)
                log.warning("Groq server error %s — ждем %ds", r.status_code, wait)
                time.sleep(wait)
                last_exc = RuntimeError(f"Server {r.status_code}")
                continue

            r.raise_for_status()
            data = r.json()
            if "choices" in data and data["choices"]:
                text = data["choices"][0]["message"]["content"]
                log.debug("Groq response length: %d", len(text) if isinstance(text, str) else 0)
                return text
            else:
                log.warning("Groq вернул пустые choices")
                last_exc = RuntimeError("Empty choices")
        except Exception as e:
            log.warning("Groq request exception: %s (attempt %d/%d)", e, attempt, attempts)
            last_exc = e
            # short backoff
            time.sleep(min(10, 2 ** attempt))

    # если все попытки неуспешны — пробуем поднять полезную ошибку
    raise RuntimeError(f"Groq failed after {attempts} attempts: {last_exc}")

# -------------------- Google Trends (pytrends) --------------------
def get_trending_topic():
    log.info("Получение тренд-темы из Google Trends...")
    if TrendReq is None:
        log.warning("pytrends не установлен — используем резервную тему")
        return default_topic_fallback()

    try:
        pytrends = TrendReq(hl='ru-RU', tz=180)
        # seed by "искусственный интеллект" to get related queries
        pytrends.build_payload(kw_list=["искусственный интеллект"], timeframe='now 7-d')
        related = pytrends.related_queries()
        if not related or "искусственный интеллект" not in related:
            log.warning("Google Trends не вернул related queries")
            return default_topic_fallback()

        top_df = related["искусственный интеллект"].get("top")
        if top_df is None or top_df.empty:
            log.warning("Google Trends top is empty")
            return default_topic_fallback()

        trends = top_df["query"].tolist()
        log.info("Найдено трендов: %d", len(trends))
    except Exception as e:
        log.exception("Ошибка обращения к Google Trends: %s", e)
        return default_topic_fallback()

    history = [h.lower() for h in load_history()]
    for t in trends:
        if t and t.lower() not in history:
            history.append(t)
            save_history(history)
            log.info("Выбрана тренд-тема: %s", t)
            return t

    # все кандидаты уже были — возвращаем самый популярный с предупреждением
    fallback = trends[0]
    history.append(fallback)
    save_history(history)
    log.warning("Все тренды повторяются — возвращаем fallback: %s", fallback)
    return fallback

def default_topic_fallback():
    # fallback topic if trends fail
    candidates = [
        "ИИ в поддержке клиентов",
        "Автономные агенты для автоматизации задач",
        "Оптимизация инференса LLM",
        "Микросервисные архитектуры с моделью на edge",
        "Инструменты для разработки приложений с ИИ"
    ]
    return random.choice(candidates)

# -------------------- Заголовок --------------------
def generate_title(topic):
    log.info("Генерация заголовка для темы: %s", topic)
    prompt = (
        f"Сгенерируй ОДИН прикладной заголовок статьи на русском языке.\n\n"
        f"Тема: {topic}\n\n"
        "Требования:\n"
        "- 8–14 слов\n"
        "- Практическая польза\n"
        "- Без футуризма и философии\n"
        "- Без слов: будущее, революция, секреты, что ждёт, почему все\n"
        "- Формат: конкретная польза или задача\n\n"
        "Ответ строго:\nЗАГОЛОВОК: <текст>\n"
    )
    try:
        text = groq_chat(prompt, max_tokens=140, temperature=0.7)
    except Exception as e:
        log.exception("Groq заголовок failed: %s", e)
        # fallback simple title
        fallback = f"{topic} — практическое руководство"
        log.warning("Использован fallback заголовок: %s", fallback)
        return fallback

    log.info("Ответ Groq (заголовок): %.200s", text.replace("\n", " ")[:200])
    m = re.search(r"ЗАГОЛОВОК:\s*(.+)", text, flags=re.IGNORECASE)
    if m:
        title = m.group(1).strip().strip('"').strip("'")
        words = len(title.split())
        if 6 <= words <= 14:
            log.info("Заголовок принят: %s", title)
            return title
        else:
            log.warning("Неподходящая длина заголовка (%d слов): %s", words, title)
    # fallback
    fallback = f"{topic} — практическое руководство"
    log.warning("Использован fallback заголовок: %s", fallback)
    return fallback

# -------------------- Тело статьи (предпочтительно один большой запрос) --------------------
def generate_body_full(title):
    """
    Пытаемся сгенерировать всю статью единым запросом (рекомендуется).
    """
    log.info("Генерация полной статьи одним запросом (title=%s)", title)
    prompt = (
        f"Напиши ПОЛНОЦЕННУЮ прикладную статью на русском языке.\n\n"
        f"Тема: {title}\n\n"
        "Формат:\n"
        "- Практический урок / мастер-класс / обзор / лайфхак\n"
        "- 6–8 разделов с заголовками (##) и содержимым\n"
        "- Реальные кейсы, рекомендации, команды/шаблоны, ошибки и как их избежать\n"
        "- В конце раздел 'Вывод' с 3–5 пунктами\n"
        "- Объём: 8000–12000 знаков\n"
        "Ответ строго в Markdown."
    )
    try:
        # max_tokens - приблизительно, Groq может ограничить, поэтому выбираем разумно
        text = groq_chat(prompt, max_tokens=int(os.getenv("GROQ_MAX_TOKENS", "1800")), temperature=0.6)
        return text
    except Exception as e:
        log.exception("generate_body_full failed: %s", e)
        return None

# fallback: план + секции (если нужно)
def generate_body_by_sections(title):
    log.info("Генерация статьи по плану и разделам (fallback)")
    # шаг 1: получить план
    plan_prompt = (
        f"Создай план практической статьи по заголовку: '{title}'.\n"
        "- Формат: 6–8 разделов, в Markdown (## Заголовок)\n"
        "- Кратко, только названия разделов"
    )
    try:
        plan = groq_chat(plan_prompt, max_tokens=700, temperature=0.4)
    except Exception as e:
        log.exception("Не удалось получить план: %s", e)
        # fallback simple structure
        plan = "## Введение\n## Основы\n## Примеры\n## Практические советы\n## Ошибки и как их избежать\n## Вывод"

    log.info("План получен (первые 200 символов): %s", plan[:200].replace("\n"," "))
    headers = [re.sub(r'^##\s*', '', l).strip() for l in plan.splitlines() if l.strip().startswith("##")]
    if not headers:
        headers = ["Введение", "Основы", "Примеры", "Практические советы", "Ошибки", "Вывод"]

    body = f"# {title}\n\n"
    total = 0
    for h in headers:
        sec_prompt = (
            f"Напиши раздел статьи. Тема: '{title}'. Раздел: '{h}'. Контекст плана:\n{plan}\n\n"
            "- Требования: 700–1200 знаков, практический тон, примеры, шаги, ошибки.\n"
            "- Только текст раздела в Markdown (без повторения заголовка в начале)."
        )
        try:
            sec_text = groq_chat(sec_prompt, max_tokens=700, temperature=0.65)
        except Exception as e:
            log.warning("Ошибка генерации раздела '%s': %s", h, e)
            sec_text = f"Краткий обзор раздела {h}."

        sec_text = sec_text.strip()
        body += f"## {h}\n\n{sec_text}\n\n"
        total += len(sec_text)

    # Если объём всё ещё мал — добавим доп раздел
    if total < 7000:
        log.warning("Общий объём мал (%d) — добавляем дополнительный раздел", total)
        body += "## Дополнительно\n\nНесколько дополнительных практических советов и примеров.\n\n"

    log.info("Сформировано тело статьи (примерно %d знаков)", len(body))
    return body

def generate_body(title):
    # 1) пробуем полный запрос
    body = generate_body_full(title)
    if body and len(body) >= 7000:
        log.info("Полная статья получена и достаточной длины (%d)", len(body))
        return body
    # 2) если не получилось — пробуем секции
    log.warning("Полная статья не получена или короткая — используем секционный подход")
    body2 = generate_body_by_sections(title)
    if body2 and len(body2) >= 4000:
        log.info("Секционный подход дал результат (%d)", len(body2))
        return body2
    # 3) финальный fallback: даже если коротко — возвращаем что есть
    log.warning("Оба подхода не дали достаточной длины — возвращаем лучший результат")
    return body2 or (body or f"# {title}\n\nКороткое содержание по теме.")

# -------------------- Генерация изображения через Stable Horde --------------------
def generate_image_horde(title):
    log.info("Генерация изображения через Stable Horde")
    styles = [
        "laboratory with quantum computers, blue lighting",
        "futuristic data center with glowing servers",
        "people using holographic AI interface",
        "cyberpunk street with AI billboards",
        "abstract visualization of neural network",
        "doctor using AI diagnostic tool",
        "artist collaborating with AI",
        "autonomous car in smart city",
        "ethical dilemma: human and AI",
        "global network of AI systems"
    ]
    style = random.choice(styles)
    prompt = (
        f"{title}, {style}, ultra realistic professional photography, "
        "sharp focus, cinematic lighting, natural colors, 8k resolution, photorealistic"
    )
    negative_prompt = (
        "text, watermark, low quality, blurry, deformed, cartoon"
    )

    url_async = "https://stablehorde.net/api/v2/generate/async"
    payload = {
        "prompt": prompt + " ### " + negative_prompt,
        "models": ["Realistic Vision V5.1", "SDXL 1.0", "Juggernaut XL"],
        "params": {"width": 1024, "height": 576, "steps": 28, "cfg_scale": 7.5, "sampler_name": "k_euler_a", "n": 1},
        "nsfw": False,
        "trusted_workers": False,
        "slow_workers": True
    }
    headers = {"Content-Type": "application/json", "Client-Agent": "LybraBlogBot:4.0"}
    if HORDE_API_KEY:
        headers["apikey"] = HORDE_API_KEY

    try:
        r = requests.post(url_async, json=payload, headers=headers, timeout=60)
        if not r.ok:
            log.warning("Horde стартовая ошибка: %s %s", r.status_code, r.text[:200])
            return None
        job = r.json()
        job_id = job.get("id")
        if not job_id:
            log.warning("Horde не вернул job id")
            return None
        log.info("Horde job id: %s", job_id)

        check_url = f"https://stablehorde.net/api/v2/generate/check/{job_id}"
        status_url = f"https://stablehorde.net/api/v2/generate/status/{job_id}"

        # poll
        for i in range(36):  # ~6 minutes
            log.debug("Horde poll %d/36", i+1)
            time.sleep(10)
            try:
                check = requests.get(check_url, headers=headers, timeout=30)
                if not check.ok:
                    log.debug("Horde check status: %s", check.status_code)
                    continue
                check_json = check.json()
                if check_json.get("done"):
                    final = requests.get(status_url, headers=headers, timeout=30)
                    if not final.ok:
                        log.warning("Horde final status HTTP %s", final.status_code)
                        continue
                    final_json = final.json()
                    gens = final_json.get("generations") or []
                    if gens:
                        img_url = gens[0].get("img")
                        if img_url:
                            # download image
                            log.info("Horde returned image URL, downloading...")
                            img_resp = requests.get(img_url, timeout=60)
                            if img_resp.ok:
                                filename = f"horde-{int(time.time())}.png"
                                path = IMAGES_DIR / filename
                                path.write_bytes(img_resp.content)
                                log.info("Image saved: %s", path)
                                return str(path)
                    else:
                        log.warning("Horde done but no generations")
            except Exception as e:
                log.debug("Horde poll exception: %s", e)
        log.warning("Horde: polling timed out")
    except Exception as e:
        log.exception("Horde generation failed: %s", e)

    return None

def generate_image(title):
    # try horde
    img = generate_image_horde(title)
    if img and os.path.exists(img):
        return img
    # fallback: pick remote and download to local PNG to keep site consistent
    fallback = random.choice(FALLBACK_IMAGES)
    try:
        log.warning("Using fallback remote image: %s", fallback)
        r = requests.get(fallback, timeout=30)
        if r.ok:
            filename = f"fallback-{int(time.time())}.png"
            path = IMAGES_DIR / filename
            path.write_bytes(r.content)
            log.info("Fallback image saved: %s", path)
            return str(path)
    except Exception as e:
        log.warning("Failed to download fallback image: %s", e)
    return fallback

# -------------------- Save post --------------------
def save_post(title, body, image_path):
    date = datetime.now()
    date_str = date.strftime("%Y-%m-%d")
    full_date_str = date.strftime("%Y-%m-%d 00:00:00 -0000")

    slug = re.sub(r'[^a-z0-9-]+', '-', translit(title)).strip('-')[:80]
    if len(slug) < 6:
        slug = "ai-" + ''.join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=8))

    filename = POSTS_DIR / f"{date_str}-{slug}.md"

    # ensure image_path is URL used in frontmatter (local path -> /assets/images/posts/...)
    if image_path:
        if image_path.startswith("http"):
            image_url = image_path
        else:
            # image_path is local filesystem path; ensure filename only
            image_url = f"/assets/images/posts/{Path(image_path).name}"
    else:
        image_url = "/assets/images/default.png"

    frontmatter = {
        "title": title,
        "date": full_date_str,
        "layout": "post",
        "image": image_url,
        "description": f"{title} — практическая статья об ИИ",
        "tags": ["ИИ", "технологии"]
    }

    # Write YAML frontmatter simple
    fm_lines = ["---"]
    for k, v in frontmatter.items():
        # ensure proper quoting
        fm_lines.append(f"{k}: \"{v}\"")
    fm_lines.append("---\n")
    content = "\n".join(fm_lines) + body

    filename.write_text(content, encoding="utf-8")
    log.info("Post saved: %s", filename)
    return filename

# -------------------- Telegram --------------------
def send_to_telegram(title, teaser, image_path):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log.warning("Telegram not configured, skipping send")
        return

    caption = f"<b>{title}</b>\n\n{teaser}\n\n<i>Читать:</i> {SITE_URL}"

    # if image_path is a URL -> download temporary; if local path -> open
    tmpfile = None
    try:
        if image_path and image_path.startswith("http"):
            r = requests.get(image_path, timeout=30)
            if r.ok:
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                tmp.write(r.content)
                tmp.close()
                tmpfile = tmp.name
                send_path = tmpfile
            else:
                log.warning("Failed to download image for Telegram, status %s", r.status_code)
                send_path = None
        else:
            send_path = image_path

        files = {}
        if send_path and os.path.exists(send_path):
            files = {"photo": open(send_path, "rb")}
        data = {"chat_id": TELEGRAM_CHAT_ID, "caption": caption, "parse_mode": "HTML"}

        resp = requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto", data=data, files=files, timeout=60)
        if files:
            files["photo"].close()
        if resp.ok:
            log.info("Telegram: sent")
        else:
            log.warning("Telegram returned %s: %s", resp.status_code, resp.text)
    except Exception as e:
        log.exception("Telegram send failed: %s", e)
    finally:
        if tmpfile:
            try:
                os.unlink(tmpfile)
            except Exception:
                pass

# -------------------- MAIN --------------------
def main():
    log.info("=== START ===")
    try:
        topic = get_trending_topic()
        log.info("Тема дня: %s", topic)

        title = generate_title(topic)
        log.info("Title: %s", title)

        body = generate_body(title)
        log.info("Body length: %d", len(body))

        image = generate_image(title)
        log.info("Image path: %s", image)

        post_file = save_post(title, body, image)

        teaser = " ".join(body.split()[:40]) + "..."
        send_to_telegram(title, teaser, image)

        log.info("=== DONE ===")
    except Exception as e:
        log.exception("Critical error: %s", e)

if __name__ == "__main__":
    main()
