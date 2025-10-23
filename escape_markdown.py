import os
import re

def escape_markdownv2(text):
    # Экранируем специальные символы MarkdownV2
    special_chars = r'[_*[\]()~`>#+-=|{}.!-]'
    return re.sub(special_chars, r'\\\g<0>', text)

title = os.environ.get('TITLE', '')
teaser = os.environ.get('TEASER', '')
if not teaser:
    teaser = 'Читайте новую статью о трендах ИИ 2025 года на нашем сайте!'
teaser = teaser[:200]

title_escaped = escape_markdownv2(title)
teaser_escaped = escape_markdownv2(teaser)

# Экранируем хэштеги
hashtags = '#ИИ #Тренды2025 #LybraAI'
hashtags_escaped = escape_markdownv2(hashtags)

# Проверяем экранирование
print(f"Raw TITLE: {title}")
print(f"Escaped TITLE: {title_escaped}")
print(f"Raw TEASER: {teaser}")
print(f"Escaped TEASER: {teaser_escaped}")
print(f"Raw HASHTAGS: {hashtags}")
print(f"Escaped HASHTAGS: {hashtags_escaped}")

message = f'📢 *Новый пост*: \"{title_escaped}\"\\n\\n*Краткий тизер*: {teaser_escaped}\\n\\n[Читать на сайте
