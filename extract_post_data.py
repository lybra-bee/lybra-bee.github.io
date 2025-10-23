import os
import glob
import yaml
import sys
import re
from datetime import datetime
from transliterate import translit

BASE_URL = "https://lybra-ai.ru"  # ✅ Исправлен домен

posts_dir = '_posts'
post_files = glob.glob(f"{posts_dir}/*.md")
if not post_files:
    print("::error::No posts found in _posts/")
    sys.exit(1)

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

    title = front_matter.get('title', '').strip()
    if not title:
        print(f"::error::Missing or empty 'title' in {latest_post}")
        sys.exit(1)

    date = str(front_matter.get('date', '')).split(' ')[0]
    if not date:
        print(f"::error::Missing or empty 'date' in {latest_post}")
        sys.exit(1)

    filename = os.path.basename(latest_post)
    slug_from_file = filename[11:].rsplit('.', 1)[0] if filename.startswith(date.replace('-', '') + '-') else ''
    slug = front_matter.get('slug', slug_from_file)
    if not slug:
        slug = translit(title.lower(), 'ru', reversed=True)
        slug = re.sub(r'[^a-z0-9-]', '-', slug).strip('-').replace('--', '-')
        print(f"::warning::Generated slug from title: {slug}")

    image = front_matter.get('image', '').strip()
    if not image:
        print(f"::warning::Missing or empty 'image' in {latest_post}, using default")
        image = f"{BASE_URL}/assets/images/default.png"
    else:
        clean_image = image.lstrip('/')
        if not clean_image.startswith('http'):
            if clean_image.startswith('assets/images/posts/'):
                image = f"{BASE_URL}/{clean_image}"
            else:
                image = f"{BASE_URL}/assets/images/posts/{clean_image}"
        print(f"Image URL resolved to: {image}")

    teaser = front_matter.get('description', '').strip()
    # ✅ Проверяем, чтобы description не совпадал с title, но без излишнего затирания
    if not teaser or teaser.strip() == '' or teaser.strip() == title.strip():
        print(f"::warning::'description' missing or matches title in {latest_post}, using fallback")
        teaser = "Читайте новую статью о трендах ИИ 2025 года на нашем сайте!"

    # ✅ Убираем только типовой префикс, не все слова
    teaser = re.sub(r'^[Уу]рок о трендах ИИ 2025 года\s*:\s*', '', teaser).strip()

    with open(os.environ.get('GITHUB_ENV', '/dev/null'), 'a', encoding='utf-8') as env_file:
        env_file.write(f"TITLE={title}\n")
        env_file.write(f"DATE={date}\n")
        env_file.write(f"SLUG={slug}\n")
        env_file.write(f"IMAGE_URL={image}\n")
        env_file.write(f"TEASER={teaser}\n")

    print(f"✅ Extracted data:\nTITLE={title}\nDATE={date}\nSLUG={slug}\nIMAGE_URL={image}\nTEASER={teaser}")

except Exception as e:
    print(f"::error::Error processing {latest_post}: {str(e)}")
    sys.exit(1)
