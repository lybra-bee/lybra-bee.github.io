import os
import re

def escape_markdownv2(text):
    special_chars = r'[_*[]()~`>#+-=|{}.!]'
    return re.sub(special_chars, r'\\g<0>', text)

title = os.environ.get('TITLE', '')
teaser = os.environ.get('TEASER', '')
if not teaser:
    teaser = 'Читайте новую статью о трендах ИИ 2025 года на нашем сайте!'
teaser = teaser[:200]

title_escaped = escape_markdownv2(title)
teaser_escaped = escape_markdownv2(teaser)

hashtags = '#ИИ #Тренды2025 #LybraAI'
hashtags_escaped = escape_markdownv2(hashtags)

print(f"Raw TITLE: {title}")
print(f"Escaped TITLE: {title_escaped}")
print(f"Raw TEASER: {teaser}")
print(f"Escaped TEASER: {teaser_escaped}")
print(f"Raw HASHTAGS: {hashtags}")
print(f"Escaped HASHTAGS: {hashtags_escaped}")

message = '📢 *Новый пост*: "' + title_escaped + '"

*Краткий тизер*: ' + teaser_escaped + '

[Читать на сайте](https://lybra-ai.ru)

' + hashtags_escaped

if len(message) > 4096:
    print(f"::error::Message length ({len(message)}) exceeds Telegram limit of 4096 characters")
    exit(1)

with open(os.environ['GITHUB_ENV'], 'a', encoding='utf-8') as f:
    f.write('TITLE_ESCAPED=' + title_escaped + '
')
    f.write('TEASER_ESCAPED=' + teaser_escaped + '
')
    f.write('MESSAGE<<EOF
')
    f.write(message + '
')
    f.write('EOF
')

print(f"Prepared message: {message}")
