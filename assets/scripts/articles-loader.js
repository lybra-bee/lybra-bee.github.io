// assets/scripts/articles-loader.js

const ARTICLES_DATA_URL = 'data/articles.json';

async function fetchArticlesData() {
    try {
        const response = await fetch(ARTICLES_DATA_URL);
        if (!response.ok) throw new Error('Failed to fetch articles data');
        return await response.json();
    } catch (error) {
        console.error('Error loading articles data:', error);
        return { articles: [], images: [] };
    }
}

// Загрузка последней статьи на главную
async function loadLatestArticle() {
    const container = document.getElementById('latest-article');
    if (!container) return;

    container.innerHTML = '<div class="loading">Загрузка...</div>';

    try {
        const data = await fetchArticlesData();
        const latestArticle = data.articles[0];

        if (latestArticle) {
            container.innerHTML = createArticleCard(latestArticle);
        } else {
            container.innerHTML = '<div class="no-articles">Статьи не найдены</div>';
        }
    } catch (error) {
        container.innerHTML = '<div class="error">Ошибка загрузки статьи</div>';
    }
}

// Загрузка всех статей
async function loadAllArticles() {
    const container = document.getElementById('all-articles');
    if (!container) return;

    container.innerHTML = '<div class="loading">Загрузка статей...</div>';

    try {
        const data = await fetchArticlesData();
        
        if (data.articles.length > 0) {
            container.innerHTML = data.articles.map(article => 
                createArticleCard(article)
            ).join('');
        } else {
            container.innerHTML = '<div class="no-articles">Статьи не найдены</div>';
        }
    } catch (error) {
        container.innerHTML = '<div class="error">Ошибка загрузки статей</div>';
    }
}

// Создание карточки статьи
function createArticleCard(article) {
    const imagePath = article.image ? `assets/images/posts/${article.image}` : '';
    
    return `
        <div class="article-card" data-article-id="${article.id}">
            ${imagePath ? `
                <img src="${imagePath}" 
                     alt="${article.title}" 
                     class="article-image"
                     onerror="this.style.display='none'">
            ` : ''}
            <div class="article-content">
                <h3>${article.title}</h3>
                <p>${article.excerpt}</p>
                <p><small>Опубликовано: ${article.date}</small></p>
                <button class="read-more" onclick="showArticle('${article.id}')">
                    Читать далее
                </button>
            </div>
        </div>
    `;
}

// Показ полной статьи
async function showArticle(articleId) {
    try {
        const data = await fetchArticlesData();
        const article = data.articles.find(a => a.id === articleId);
        
        if (!article) {
            alert('Статья не найдена');
            return;
        }

        // Создаем модальное окно для статьи
        const modal = document.createElement('div');
        modal.className = 'article-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <span class="close-modal" onclick="closeModal()">&times;</span>
                ${article.image ? `
                    <img src="assets/images/posts/${article.image}" 
                         alt="${article.title}" 
                         class="modal-image"
                         onerror="this.style.display='none'">
                ` : ''}
                <h2>${article.title}</h2>
                <p><small>Опубликовано: ${article.date}</small></p>
                <div class="article-full-content">
                    ${article.content ? marked.parse(article.content) : '<p>Содержание недоступно</p>'}
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        document.body.style.overflow = 'hidden';
    } catch (error) {
        alert('Ошибка загрузки статьи');
    }
}

// Закрытие модального окна
function closeModal() {
    const modal = document.querySelector('.article-modal');
    if (modal) {
        modal.remove();
        document.body.style.overflow = 'auto';
    }
}

// Закрытие по клику вне контента
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('article-modal')) {
        closeModal();
    }
});
