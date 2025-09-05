// Функция для загрузки компонентов
async function loadComponent(componentId, componentPath) {
    try {
        const response = await fetch(componentPath);
        const html = await response.text();
        document.getElementById(componentId).innerHTML = html;
    } catch (error) {
        console.error('Error loading component:', error);
    }
}

// Функция для загрузки статей
async function loadArticles() {
    try {
        const response = await fetch('../data/articles.json');
        const articles = await response.json();
        return articles;
    } catch (error) {
        console.error('Error loading articles:', error);
        return [];
    }
}

// Функция для загрузки избранных статей
async function loadFeaturedArticles(limit = 3) {
    const articles = await loadArticles();
    const featuredArticles = articles.slice(0, limit);
    const container = document.getElementById('featured-articles');
    
    if (container && featuredArticles.length > 0) {
        container.innerHTML = featuredArticles.map(article => `
            <div class="article-card">
                <img src="assets/images/posts/${article.image}" 
                     alt="${article.title}" 
                     class="article-image"
                     onerror="this.style.display='none'">
                <div class="article-content">
                    <h3>${article.title}</h3>
                    <p>${article.excerpt}</p>
                    <a href="articles.html#${article.id}" class="read-more">Читать далее</a>
                </div>
            </div>
        `).join('');
    }
}

// Функция для загрузки всех статей
async function loadAllArticles() {
    const articles = await loadArticles();
    const container = document.getElementById('all-articles');
    
    if (container && articles.length > 0) {
        container.innerHTML = articles.map(article => `
            <div class="article-card">
                <img src="assets/images/posts/${article.image}" 
                     alt="${article.title}" 
                     class="article-image"
                     onerror="this.style.display='none'">
                <div class="article-content">
                    <h3>${article.title}</h3>
                    <p>${article.excerpt}</p>
                    <p><small>Опубликовано: ${article.date}</small></p>
                    <a href="articles.html#${article.id}" class="read-more">Читать далее</a>
                </div>
            </div>
        `).join('');
    }
}

// Обработчик для мобильного меню
document.addEventListener('click', function(e) {
    if (e.target.closest('.hamburger')) {
        const navMenu = document.querySelector('.nav-menu');
        navMenu.style.display = navMenu.style.display === 'flex' ? 'none' : 'flex';
    }
});
