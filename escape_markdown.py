#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
escape_markdown.py

Подготавливает безопасное для Telegram MarkdownV2 сообщение из TITLE и TEASER,
формирует ссылку на статью (если доступны DATE и SLUG) и сохраняет
TITLE_ESCAPED, TEASER_ESCAPED и MESSAGE в GITHUB_ENV для использования в GitHub Actions.

Использование (в Actions можно просто вызвать без аргументов, если TITLE/TEASER заданы в окружении):
  python escape_markdown.py
или
  python escape_markdown.py "Заголовок" "Краткий тизер"
"""

import os
import re
import sys
from datetime import datetime

# --- Функция экранирования для Telegram MarkdownV2 ---
def escape_markdown_v2(text: str) -> str:
    if text is None:
        return ""
    # Символы, которые надо экранировать в MarkdownV2
    # Telegram: _ * [ ] ( ) ~ ` > # + - = | { } . !
    special = r'[_*\[\]\(\)~`>#+\-=|{}\.!]'
    return re.sub(special, lambda m: '\\' + m.group(0), str(text))

# --- Построение URL статьи из DATE и SLUG (если доступны) ---
def build_post_url(date_raw: str, slug: str) -> str:
    site = "https://lybra-ai.ru"
    if not slug:
        return site
    if not date_raw:
        # нет даты — просто вернём сайт/slug
        return f"{site.rstrip('/')}/{slug.strip('/')}/"
    date = date_raw.strip()
    # Поддерживаем форматы: YYYY-MM-DD, YYYY/MM/DD, YYYYMMDD
    try:
        if "/" in date:
            # возможно уже YYYY/MM/DD
            parts = date.split("/")
            if len(parts[0]) == 4:
                yyyy = parts[0]
                mm = parts[1] if len(parts) > 1 else "01"
                dd = parts[2] if len(parts) > 2 else "01"
                return f"{site}/{yyyy}/{mm}/{dd}/{slug}.html"
        if "-" in date:
            # YYYY-MM-DD
            parts = date.split("-")
            yyyy, mm, dd = parts[0], parts[1] if len(parts) > 1 else "01", parts[2] if len(parts) > 2 else "01"
            return f"{site}/{yyyy}/{mm}/{dd}/{slug}.html"
        if len(date) == 8 and date.isdigit():
            # YYYYMMDD
            yyyy = date[0:4]; mm = date[4:6]; dd = date[6:8]
            return f"{site}/{yyyy}/{mm}/{dd}/{slug}.html"
    except Exception:
        pass
    # fallback
    return f"{site.rstrip('/')}/{slug.strip('/')}/"

def write_to_github_env(key: str, value: str):
    github_env = os.environ.get("GITHUB_ENV")
    if not github_env:
        # Если GITHUB_ENV не задан (например запуск локально), просто выводим предупреждение
        print(f"::warning::GITHUB_ENV not set, cannot write {key} to GitHub Actions environment")
        return
    # Открываем и добавляем
    with open(github_env, "a", encoding="utf-8") as f:
        f.write(f"{key}={value}\n")

def write_multiline_to_github_env(key: str, value: str):
    github_env = os.environ.get("GITHUB_ENV")
    if not github_env:
        print(f"::warning::GITHUB_ENV not set, cannot write multiline {key} to GitHub Actions environment")
        return
    with open(github_env, "a", encoding="utf-8") as f:
        f.write(f"{key}<<EOF\n")
        f.write(value + "\n")
        f.write("EOF\n")

def main():
    # Сначала пробуем взять из окружения (workflow extract_post_data.py должен установить их)
    title = os.environ.get("TITLE", "").strip()
    teaser = os.environ.get("TEASER", "").strip()
    date_env = os.environ.get("DATE", "").strip()  # может быть '2025-08-03' или '2025/08/03'
    slug = os.environ.get("SLUG", "").strip()

    # Если не переданы через окружение — попытка взять из аргументов
    if not title and len(sys.argv) > 1:
        title = sys.argv[1].strip()
    if not teaser and len(sys.argv) > 2:
        teaser = sys.argv[2].strip()

    # Если тизер всё ещё пуст — запасной текст
    if not teaser:
        teaser = "Читайте новую статью о трендах ИИ 2025 года на нашем сайте!"

    # Ограничиваем тизер до 200 символов (по желанию)
    teaser = teaser.strip()[:200]

    # Формируем URL поста (если возможно)
    post_url = build_post_url(date_env, slug)

    # Экранируем для MarkdownV2
    title_escaped = escape_markdown_v2(title)
    teaser_escaped = escape_markdown_v2(teaser)
    url_escaped = escape_markdown_v2(post_url)

    # Составляем сообщение в формате MarkdownV2
    # Пример:
    # 📢 *Новый пост*: "Заголовок"
    # 🔗 [Читать статью](https://...)
    # #ИИ #Тренды2025
    hashtags = "#ИИ #Тренды2025 #LybraAI"
    hashtags_escaped = escape_markdown_v2(hashtags)

    message_lines = [
        f"📢 *Новый пост*: \"{title_escaped}\"",
        "",
        f"*Краткий тизер*: {teaser_escaped}",
        "",
        f"[Читать статью]({post_url})",
        "",
        hashtags_escaped
    ]
    message = "\n".join(message_lines)

    # Проверка длины (Telegram лимит 4096)
    if len(message) > 4096:
        print(f"::warning::Message length {len(message)} > 4096. Truncating teaser.")
        # оставляем заголовок и сокращённый тизер
        allowed = 4096 - (len("\n\n📢 *Новый пост*: \"\"") + len(title_escaped) + 50)
        teaser_trunc = teaser_escaped[:max(0, allowed)]
        message_lines = [
            f"📢 *Новый пост*: \"{title_escaped}\"",
            "",
            f"*Краткий тизер*: {teaser_trunc}…",
            "",
            f"[Читать статью]({post_url})",
            "",
            hashtags_escaped
        ]
        message = "\n".join(message_lines)

    # Пишем в GITHUB_ENV
    # TITLE_ESCAPED и TEASER_ESCAPED для дальнейших шагов
    write_to_github_env("TITLE_ESCAPED", title_escaped)
    write_to_github_env("TEASER_ESCAPED", teaser_escaped)
    # MESSAGE — многострочная переменная
    write_multiline_to_github_env("MESSAGE", message)

    # Для удобства — печатаем результат в лог
    print("Prepared message:")
    print("-----")
    print(message)
    print("-----")
    print(f"Post URL: {post_url}")
    print(f"TITLE_ESCAPED: {title_escaped}")
    print(f"TEASER_ESCAPED: {teaser_escaped}")

if __name__ == "__main__":
    main()
