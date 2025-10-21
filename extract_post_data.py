import glob
import yaml
import os
import re
from translit import translit  # Для транслитерации slug

# Находим последний пост
post_files = sorted(glob.glob('_posts/*.md'), reverse=True)
if not post_files:
    print('::error::No posts found in _posts/')
    exit(1)

# Выводим имя файла для отладки
print(f'Found post file: {post_files[0]}')

# Читаем файл
with open(post_files[0], 'r', encoding='utf-8') as f:
    content = f.read()
    print(f'File content (first 200 chars): {content[:200]}...')

# Извлекаем front-matter
try:
    parts = content.split('---')
    if len(parts) < 3:
        print('::error::Invalid post structure: missing second ---')
        exit(1)
    front_matter = parts[1]
    data = yaml.safe_load(front_matter) or {}
except IndexError:
    print('::error::Invalid YAML front-matter')
    exit(1)
except yaml.YAMLError as e:
    print(f'::error::YAML parsing error: {str(e)}')
    exit(1)

# Извлекаем метаданные
title = data.get('title', 'Без заголовка')
date = data.get('date', '2025/01/01').split(' ')[0].replace('-', '/')
slug = post_files[0].split('/')[-1].split('-', 3)[-1].replace('.md', '') if '-' in post_files[0] else 'no-slug'
# Транслитерация slug для английского URL
slug = translit(slug, 'ru', reversed=True)  # ru to en, reversed for slug-like format
slug = re.sub(r'\s+', '-', slug.lower()).strip('-')  # Заменяем пробелы на дефисы
post_num = data.get('image', '').split('-')[-1].replace('.png', '') if 'image' in data else '1'

# Извлекаем тело поста
body = parts[2].strip() if len(parts) > 2 else ''
print(f'Raw body (first 200 chars): {body[:200]}...')

# Очищаем тело от Markdown и заголовков
body = re.sub(r'^#{1,}\s*.*$', '', body, flags=re.MULTILINE).strip()  # Удаляем заголовки
body = re.sub(r'\*{1,2}(.*?)\*{1,2}', r'\1', body)  # Удаляем **жирный** текст
body = re.sub(r'\n\s*\n', ' ', body).strip()  # Удаляем лишние переносы строк
print(f'Cleaned body (first 200 chars): {body[:200]}...')

# Извлекаем первые 50 слов
words = [w for w in body.split() if w][:50]
print(f'Words (first 10): {words[:10]}...')

# Формируем тизер
teaser = ' '.join(words) + ('...' if len(words) == 50 else '') if words else 'Тизер недоступен: проверьте содержимое статьи.'
print(f'Teaser: {teaser}')

# Экспортируем переменные в $GITHUB_ENV
with open(os.environ['GITHUB_ENV'], 'a', encoding='utf-8') as f:
    f.write(f'TITLE={title}\n')
    f.write(f'DATE={date}\n')
    f.write(f'SLUG={slug}\n')
    f.write(f'POST_NUM={post_num}\n')
    f.write(f'TEASER={teaser}\n')

# Финальный вывод
print(f'Title: {title}, Date: {date}, Slug: {slug}, Post Num: {post_num}, Teaser: {teaser}')
