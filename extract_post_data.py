import glob
import yaml
import os
import re

post_files = sorted(glob.glob('_posts/*.md'), reverse=True)
if not post_files:
  print('::error::No posts found in _posts/')
  exit(1)
with open(post_files[0], 'r', encoding='utf-8') as f:
  content = f.read()
  try:
    front_matter = content.split('---')[1]
    data = yaml.safe_load(front_matter) or {}
  except IndexError:
    print('::error::Invalid YAML front-matter')
    exit(1)
title = data.get('title', 'Без заголовка')
date = data.get('date', '2025/01/01').split(' ')[0].replace('-', '/')
slug = post_files[0].split('/')[-1].split('-', 3)[-1].replace('.md', '') if '-' in post_files[0] else 'no-slug'
post_num = data.get('image', '').split('-')[-1].replace('.png', '') if 'image' in data else '1'
body = content.split('---')[2].strip() if len(content.split('---')) > 2 else ''
body = re.sub(r'^#{1,}\s*.*$', '', body, flags=re.MULTILINE).strip()
body = re.sub(r'\*{1,2}(.*?)\*{1,2}', r'\1', body)
body = re.sub(r'\n\s*\n', ' ', body).strip()
words = ' '.join([w for w in body.split() if w]).split()[:50]
teaser = ' '.join(words) + ('...' if len(words) == 50 else '') if words else 'Тизер недоступен: проверьте содержимое статьи.'
os.environ['TITLE'] = title
os.environ['DATE'] = date
os.environ['SLUG'] = slug
os.environ['POST_NUM'] = post_num
os.environ['TEASER'] = teaser
print(f'Title: {title}, Date: {date}, Slug: {slug}, Post Num: {post_num}, Teaser: {teaser}')
