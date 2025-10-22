import os
import glob
import yaml
import sys
import re

posts_dir = '_posts'
post_files = sorted(glob.glob(f"{posts_dir}/*.md"), key=os.path.getmtime, reverse=True)
if not post_files:
    print("::error::No posts found in _posts/")
    sys.exit(1)

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

    title = front_matter.get('title', '')
    if not title:
        print(f"::error::Missing or empty 'title' in {latest_post}")
        sys.exit(1)

    date = front_matter.get('date', '')
    if not date:
        print(f"::error::Missing or empty 'date' in {latest_post}")
        sys.exit(1)
    date = str(date).split(' ')[0]  # Extract YYYY-MM-DD

    slug = front_matter.get('slug', '')
    if not slug:
        slug = re.sub(r'[^a-z0-9а-я-]', '-', title.lower()).strip('-').replace('--', '-')
        print(f"::warning::Generated slug: {slug}")

    image = front_matter.get('image', '')
    post_num = ''
    if image and 'post-' in image:
        post_num = image.split('post-')[-1].split('.')[0]
    else:
        print(f"::error::Missing or invalid 'image' in {latest_post}")
        sys.exit(1)

    teaser = front_matter.get('description', '')
    if not teaser:
        print(f"::warning::Missing or empty 'description' in {latest_post}, using default")
        teaser = "Тизер недоступен: проверьте содержимое статьи."

    # Запись переменных в $GITHUB_ENV
    with open(os.environ.get('GITHUB_ENV', '/dev/null'), 'a', encoding='utf-8') as env_file:
        env_file.write(f"TITLE={title}\n")
        env_file.write(f"DATE={date.replace('-', '/')}\n")
        env_file.write(f"SLUG={slug}\n")
        env_file.write(f"POST_NUM={post_num}\n")
        env_file.write(f"TEASER={teaser}\n")

    print(f"Extracted: TITLE={title}, DATE={date.replace('-', '/')}, SLUG={slug}, POST_NUM={post_num}, TEASER={teaser}")

except Exception as e:
    print(f"::error::Error processing {latest_post}: {str(e)}")
    sys.exit(1)
