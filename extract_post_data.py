import os
import glob
import yaml

posts_dir = '_posts'
post_files = sorted(glob.glob(f"{posts_dir}/*.md"), reverse=True)
if not post_files:
    print("No posts found")
    exit(1)

latest_post = post_files[0]
with open(latest_post, 'r', encoding='utf-8') as f:
    content = f.read()
    front_matter = yaml.safe_load(content.split('---')[1])

title = front_matter.get('title', 'No title')
date = front_matter.get('date', '2025-10-22').split(' ')[0]
slug = front_matter.get('slug', '')
if not slug:
    slug = title.lower().replace(' ', '-')  # Простая замена пробелов на дефисы
    slug = slug.replace('---', '-')  # Удаление лишних дефисов
post_num = front_matter.get('image', '').split('post-')[-1].split('.')[0] if front_matter.get('image') else '1'
teaser = front_matter.get('description', 'Тизер недоступен: проверьте содержимое статьи.')

os.environ['TITLE'] = title
os.environ['DATE'] = date.replace('-', '/')
os.environ['SLUG'] = slug
os.environ['POST_NUM'] = post_num
os.environ['TEASER'] = teaser

print(f"Extracted: TITLE={title}, DATE={date}, SLUG={slug}, POST_NUM={post_num}, TEASER={teaser}")
