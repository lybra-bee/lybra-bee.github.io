import os
import json
import frontmatter
from datetime import datetime
from pathlib import Path

def get_articles_data():
    articles = []
    posts_dir = Path('content/posts')
    
    if posts_dir.exists():
        for file_path in posts_dir.glob('*.md'):
            with open(file_path, 'r', encoding='utf-8') as f:
                post = frontmatter.load(f)
                
                article = {
                    'id': file_path.stem,
                    'title': post.get('title', 'Без названия'),
                    'excerpt': post.get('excerpt', ''),
                    'date': post.get('date', '2024-01-01'),
                    'image': post.get('image', ''),
                    'content': post.content
                }
                articles.append(article)
    
    # Сортируем по дате (новые сначала)
    articles.sort(key=lambda x: x['date'], reverse=True)
    return articles

def get_images_list():
    images_dir = Path('assets/images/posts')
    images = []
    
    if images_dir.exists():
        for file_path in images_dir.glob('*.*'):
            if file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                images.append(file_path.name)
    
    return images

def main():
    # Создаем папку data если её нет
    Path('data').mkdir(exist_ok=True)
    
    # Генерируем данные статей
    articles = get_articles_data()
    images = get_images_list()
    
    data = {
        'articles': articles,
        'images': images,
        'generated_at': datetime.now().isoformat()
    }
    
    with open('data/articles.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Generated data for {len(articles)} articles and {len(images)} images")

if __name__ == '__main__':
    main()
