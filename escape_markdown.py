import os
import re

def escape_markdownv2(text):
    # Экранируем все специальные символы MarkdownV2
    special_chars = r'[_*[\]()~`>#+-=|{}.!-]'
    return re.sub(special_chars, r'\\\g<0>', text)

title = os.environ.get('TITLE', '')
teaser = os.environ.get('TEASER', '')
if not teaser:
    teaser = 'Читайте новую статью о трендах ИИ 2025 года на нашем сайте!'
teaser = teaser[:200]

title_escaped = escape_markdownv2(title)
teaser_escaped = escape_markdownv2(teaser)

# Проверяем экранирование
print(f"Raw TITLE: {title}")
print(f"Escaped TITLE: {title_escaped}")
print(f"Raw TEASER: {teaser}")
print(f"Escaped TEASER: {teaser_escaped}")

message = f'📢 *Новый пост*: \"{title_escaped}\"\\n\\n*Краткий тизер*: {teaser_escaped}\\n\\n[Читать на сайте](https://lybra-ai.ru)\\n\\n#ИИ #Тренды2025 #LybraAI'

with open(os.environ['GITHUB_ENV'], 'a', encoding='utf-8') as f:
    f.write(f'TITLE_ESCAPED={title_escaped}\n')
    f.write(f'TEASER_ESCAPED={teaser_escaped}\n')
    f.write(f'MESSAGE={message}\n')

print(f"Prepared message: {message}")
