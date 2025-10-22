import os
import glob
import yaml
import sys

posts_dir = '_posts'
post_files = sorted(glob.glob(f"{posts_dir}/*.md"), reverse=True)
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
            print(f"::error::Invalid front-matter in {latest_post}")
            sys.exit(1)
        front_matter = yaml.safe_load(parts[1])
        if not front_matter:
            print(f"::error::Failed to parse front-matter in {latest_post}")
            sys.exit(1)

    title = front_matter.get('title', 'No title')
    date = front_matter.get('date', '2025-10-22').split(' ')[0]
    slug = front_matter.get('slug', '')
    if not slug:
        slug = title.lower().replace(' ', '-').replace('---', '-')
    image = front_matter.get('image', '')
    post_num = image.split('post-')[-1].split('.')[0] if image and 'post-' in image else '1'
    teaser = front_matter.get('description', 'Тизер недоступен: проверьте содержимое статьи.')

    os.environ['TITLE'] = title
    os.environ['DATE'] = date.replace('-', '/')
    os.environ['SLUG'] = slug
    os.environ['POST_NUM'] = post_num
    os.environ['TEASER'] = teaser

    print(f"Extracted: TITLE={title}, DATE={date}, SLUG={slug}, POST_NUM={post_num}, TEASER={teaser}")

except Exception as e:
    print(f"::error::Error processing {latest_post}: {str(e)}")
    sys.exit(1)
