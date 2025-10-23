import os
import glob
import yaml
import sys
import re
from datetime import datetime
from transliterate import translit

posts_dir = '_posts'
post_files = glob.glob(f"{posts_dir}/*.md")
if not post_files:
    print("::error::No posts found in _posts/")
    sys.exit(1)

# Сортировка по дате из front-matter или имени файла
def get_post_date(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            parts = content.split('---')
            if len(parts) < 3:
                return datetime.min
            front_matter = yaml.safe_load(parts[1])
            date_str = front_matter.get('date', '')
            if date_str:
                return datetime.strptime(str(date_str).split(' ')[0], '%Y-%m-%d')
    except Exception as e:
        print(f"::warning::Error parsing date in {file_path}: {str(e)}")
    filename = os.path.basename(file_path)
    date_part = filename[:8]
    try:
        return datetime.strptime(date_part, '%Y%m%d')
    except ValueError:
        return datetime.min

post_files = sorted(post_files, key=get_post_date, reverse=True)
print(f"Found posts: {post_files}")
latest_post = post_files[0]
print(f"Processing latest post: {latest_post}")

try:
    with open(latest_post, 'r', encoding='utf-8') as f:
        content = f.read()
        parts = content.split('---')
        if len(parts) < 3:
            print(f"::error::Invalid front-matter in {latest_post}: missing '---' delimiters")
            sys.exit(1)
        front_matter = yaml.safe_load(parts[1])
        if not isinstance(front_matter, dict):
            print(f"::error::Failed to parse front-matter in {latest_post}: invalid YAML")
            sys.exit(1)
        print(f"Front-matter: {front_matter}")

    title = front_matter.get('title', '')
    if not title:
        print(f"::error::Missing or empty 'title' in {latest_post}")
        sys.exit(1)

    date = front_matter.get('date', '')
    if not date:
        print(f"::error::Missing or empty 'date' in {latest_post}")
        sys.exit(1)
    date = str(date).split(' ')[0]

    filename = os.path.basename(latest_post)
    slug_from_file = filename[11:].rsplit('.', 1)[0] if filename.startswith(date.replace('-', '') + '-') else ''
    slug = front_matter.get('slug', slug_from_file)
    if not slug:
        slug = translit(title.lower(), 'ru', reversed=True)
        slug = re.sub(r'[^a-z0-9-]', '-', slug).strip('-').replace('--', '-')
        print(f"::warning::Generated slug from title: {slug}")

    image = front_matter.get('image', '')
    if not image or image.strip() == '':
        print(f"::warning::Missing or empty 'image' in {latest_post}, using default")
        image = 'https://lybra-ai.ru/assets/images/default.png'
    else:
        # Если image - относительный путь, добавляем базовый URL
        if not image.startswith('http'):
            image = f"https://lybra-ai.ru/assets/images/posts/{image.lstrip('/')}"
        print(f"Image URL from front-matter: {image}")

    teaser = front_matter.get('description', '')
    if not teaser or teaser.strip() == '' or teaser.lower().strip() == title.lower().strip():
        print(f"::warning::'description' missing, empty, or matches 'title' in {latest_post}, using default")
        teaser = "Читайте новую статью о трендах ИИ 2025 года на нашем сайте!"

    with open(os.environ.get('GITHUB_ENV', '/dev/null'), 'a', encoding='utf-8') as env_file:
        env_file.write(f"TITLE={title}\n")
        env_file.write(f"DATE={date.replace('-', '/')}\n")
        env_file.write(f"SLUG={slug}\n")
        env_file.write(f"IMAGE_URL={image}\n")
        env_file.write(f"TEASER={teaser}\n")

    print(f"Extracted: TITLE={title}, DATE={date.replace('-', '/')}, SLUG={slug}, IMAGE_URL={image}, TEASER={teaser}")

except Exception as e:
    print(f"::error::Error processing {latest_post}: {str(e)}")
    sys.exit(1)
