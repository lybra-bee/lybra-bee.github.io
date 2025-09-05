import json
import os
from pathlib import Path

def load_template(template_name):
    templates = {
        'base.html': '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{title}}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; background: #f8f9fa; }
        .container { max-width: 1200px; margin: 0 auto; padding: 0 20px; }
        
        /* Header */
        .main-header { background: #2c3e50; color: white; padding: 1rem 0; position: sticky; top: 0; z-index: 1000; }
        .navbar { display: flex; justify-content: space-between; align-items: center; max-width: 1200px; margin: 0 auto; padding: 0 20px; }
        .nav-brand a { color: white; text-decoration: none; font-size: 1.5rem; font-weight: bold; }
        .nav-menu { display: flex; list-style: none; gap: 2rem; }
        .nav-menu a { color: white; text-decoration: none; transition: color 0.3s ease; }
        .nav-menu a:hover { color: #3498db; }
        
        /* Hero */
        .hero { text-align: center; padding: 4rem 0; background: linear-gradient(135deg, #2c3e50, #3498db); color: white; margin-bottom: 3rem; border-radius: 10px; }
        .hero h1 { font-size: 3rem; margin-bottom: 1rem; }
        .hero p { font-size: 1.2rem; opacity: 0.9; }
        
        /* Articles */
        .articles-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem; margin: 2rem 0; }
        .article-card { background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); transition: transform 0.3s ease; }
        .article-card:hover { transform: translateY(-5px); }
        .article-image { width: 100%; height: 200px; object-fit: cover; }
        .article-content { padding: 1.5rem; }
        .article-content h3 { color: #2c3e50; margin-bottom: 0.5rem; }
        .article-content p { color: #666; margin-bottom: 1rem; }
        .read-more { display: inline-block; padding: 0.5rem 1rem; background: #3498db; color: white; text-decoration: none; border-radius: 5px; border: none; cursor: pointer; transition: background 0.3s ease; }
        .read-more:hover { background: #2c3e50; }
        
        /* Gallery */
        .gallery { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 1.5rem; margin: 2rem 0; }
        .gallery-item { position: relative; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); transition: transform 0.3s ease; }
        .gallery-item:hover { transform: scale(1.05); }
        .gallery-image { width: 100%; height: 200px; object-fit: cover; transition: transform 0.3s ease; }
        .gallery-item:hover .gallery-image { transform: scale(1.1); }
        .image-overlay { position: absolute; bottom: 0; left: 0; right: 0; background: rgba(0,0,0,0.7); color: white; padding: 1rem; text-align: center; transform: translateY(100%); transition: transform 0.3s ease; }
        .gallery-item:hover .image-overlay { transform: translateY(0); }
        
        /* Footer */
        .main-footer { background: #2c3e50; color: white; padding: 2rem 0; margin-top: 4rem; }
        .footer-content { max-width: 1200px; margin: 0 auto; padding: 0 20px; text-align: center; }
        
        /* Responsive */
        @media (max-width: 768px) {
            .nav-menu { display: none; }
            .hero h1 { font-size: 2rem; }
            .articles-grid { grid-template-columns: 1fr; }
            .gallery { grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); }
        }
    </style>
</head>
<body>
    <header class="main-header">
        <nav class="navbar">
            <div class="nav-brand">
                <a href="index.html">Мой блог</a>
            </div>
            <ul class="nav-menu">
                <li><a href="index.html">Главная</a></li>
                <li><a href="articles.html">Статьи</a></li>
                <li><a href="gallery.html">Галерея</a></li>
            </ul>
        </nav>
    </header>
    
    <main class="container">
        {{content}}
    </main>
    
    <footer class="main-footer">
        <div class="footer-content">
            <p>&copy; 2024 Мой блог. Все права защищены.</p>
        </div>
    </footer>

    <script>
    function showArticle(id) {
        const articleContent = {
            'welcome-to-my-blog': {
                title: 'Добро пожаловать в мой блог',
                content: '<h2>Добро пожаловать!</h2><p>Это первая статья в моём блоге...</p>'
            },
            'web-development-tips': {
                title: 'Советы по веб-разработке', 
                content: '<h2>Советы для разработчиков</h2><p>Полезные рекомендации...</p>'
            },
            'css-tricks': {
                title: 'Полезные трюки CSS',
                content: '<h2>CSS трюки</h2><p>Интересные приёмы работы с CSS...</p>'
            }
        };
        
        const article = articleContent[id];
        if (article) {
            const modal = document.createElement('div');
            modal.style = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.8);display:flex;justify-content:center;align-items:center;z-index:1000;';
            modal.innerHTML = `
                <div style="background:white;padding:2rem;border-radius:10px;max-width:600px;max-height:80vh;overflow-y:auto;position:relative;">
                    <span style="position:absolute;top:1rem;right:1rem;font-size:2rem;cursor:pointer;" onclick="this.parentElement.parentElement.remove()">&times;</span>
                    <h2>${article.title}</h2>
                    <div>${article.content}</div>
                </div>
            `;
            document.body.appendChild(modal);
        }
    }
    </script>
</body>
</html>''',
        
        'index.html': '''
        <section class="hero">
            <h1>Добро пожаловать в мой блог</h1>
            <p>Здесь я делюсь своими мыслями и идеями о веб-разработке</p>
        </section>
        
        <section class="featured-articles">
            <h2>Последняя статья</h2>
            <div class="articles-grid">
                {{latest_article}}
            </div>
        </section>
        ''',
        
        'articles.html': '''
        <h1>Все статьи</h1>
        <div class="articles-grid">
            {{articles}}
        </div>
        ''',
        
        'gallery.html': '''
        <h1>Галерея изображений</h1>
        <div class="gallery">
            {{gallery}}
        </div>
        '''
    }
    return templates.get(template_name, '')

def load_articles_data():
    try:
        if os.path.exists('data/articles.json'):
            with open('data/articles.json', 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {'articles': [], 'images': []}

def generate_index_html(articles):
    template = load_template('base.html')
    content = load_template('index.html')
    
    latest_article = articles[0] if articles else None
    
    articles_html = ''
    if latest_article:
        articles_html = f'''
        <div class="article-card">
            <img src="assets/images/posts/{latest_article['image']}" 
                 alt="{latest_article['title']}" 
                 class="article-image"
                 onerror="this.style.display='none'">
            <div class="article-content">
                <h3>{latest_article['title']}</h3>
                <p>{latest_article['excerpt']}</p>
                <p><small>Опубликовано: {latest_article['date']}</small></p>
                <button class="read-more" onclick="showArticle('{latest_article['id']}')">
                    Читать далее
                </button>
            </div>
        </div>
        '''
    else:
        articles_html = '<p style="text-align: center; padding: 2rem;">Пока нет статей. Статьи появятся после генерации.</p>'
    
    content = content.replace('{{latest_article}}', articles_html)
    return template.replace('{{content}}', content).replace('{{title}}', 'Главная - Мой блог')

def generate_articles_html(articles):
    template = load_template('base.html')
    content = load_template('articles.html')
    
    articles_html = ''
    for article in articles:
        articles_html += f'''
        <div class="article-card">
            <img src="assets/images/posts/{article['image']}" 
                 alt="{article['title']}" 
                 class="article-image"
                 onerror="this.style.display='none'">
            <div class="article-content">
                <h3>{article['title']}</h3>
                <p>{article['excerpt']}</p>
                <p><small>Опубликовано: {article['date']}</small></p>
                <button class="read-more" onclick="showArticle('{article['id']}')">
                    Читать далее
                </button>
            </div>
        </div>
        '''
    
    if not articles_html:
        articles_html = '<p style="text-align: center; padding: 2rem;">Пока нет статей. Статьи появятся после генерации.</p>'
    
    content = content.replace('{{articles}}', articles_html)
    return template.replace('{{content}}', content).replace('{{title}}', 'Статьи - Мой блог')

def generate_gallery_html(images):
    template = load_template('base.html')
    content = load_template('gallery.html')
    
    gallery_html = ''
    for image in images:
        name = image.replace('.jpg', '').replace('.png', '').replace('.jpeg', '').replace('.gif', '').replace('.webp', '')
        name = name.replace('-', ' ').title()
        
        gallery_html += f'''
        <div class="gallery-item">
            <img src="assets/images/posts/{image}" 
                 alt="{name}" 
                 class="gallery-image"
                 onerror="this.style.display='none'">
            <div class="image-overlay">{name}</div>
        </div>
        '''
    
    if not gallery_html:
        gallery_html = '<p style="text-align: center; padding: 2rem;">Пока нет изображений. Изображения появятся после генерации.</p>'
    
    content = content.replace('{{gallery}}', gallery_html)
    return template.replace('{{content}}', content).replace('{{title}}', 'Галерея - Мой блог')

def main():
    print("🚀 Starting site build...")
    
    # Create necessary directories
    os.makedirs('assets/images/posts', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    
    # Load data
    data = load_articles_data()
    articles = data.get('articles', [])
    images = data.get('images', [])
    
    print(f"📊 Found: {len(articles)} articles, {len(images)} images")
    
    # Generate HTML files
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(generate_index_html(articles))
        print("✅ Created index.html")
    
    with open('articles.html', 'w', encoding='utf-8') as f:
        f.write(generate_articles_html(articles))
        print("✅ Created articles.html")
    
    with open('gallery.html', 'w', encoding='utf-8') as f:
        f.write(generate_gallery_html(images))
        print("✅ Created gallery.html")
    
    # Create empty data file if not exists
    if not os.path.exists('data/articles.json'):
        with open('data/articles.json', 'w', encoding='utf-8') as f:
            json.dump({'articles': [], 'images': []}, f, indent=2)
        print("✅ Created empty data/articles.json")
    
    print("🎉 Site built successfully!")

if __name__ == '__main__':
    main()
