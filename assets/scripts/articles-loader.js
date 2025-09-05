// assets/scripts/articles-loader.js

// Предполагаемый список статей (в реальности нужно получать через GitHub API)
const articlesData = [
    {
        id: 'welcome-to-my-blog',
        title: 'Добро пожаловать в мой блог',
        excerpt: 'Первая статья в моем новом блоге о веб-разработке и дизайне.',
        date: '2024-01-15',
        image: 'welcome-to-my-blog.jpg',
        content: 'Полное содержание статьи...'
    },
    {
        id: 'web-development-tips',
        title: 'Советы по веб-разработке',
        excerpt: 'Полезные советы и лучшие практики для начинающих разработчиков.',
        date: '2024-01-20',
        image: 'web-development-tips.jpg',
        content: 'Полное содержание статьи...'
    },
    {
        id: 'css-tricks',
        title: 'Полезные трюки CSS',
        excerpt: 'Интересные приемы и техники работы с CSS для современных интерфейсов.',
        date: '2024-01-25',
        image: 'css-tricks.jpg',
        content: 'Полное содержание статьи...'
    }
];

// Загрузка последней статьи на главную
async function loadLatestArticle() {
    const container = document.getElementById('latest-article');
    if (!container) return;

    // Сортируем статьи по дате и берем последнюю
    const sortedArticles = [...articlesData].sort((a, b) => 
        new Date(b.date) - new Date(a.date)
    );
    const latestArticle = sortedArticles[0];

    container.innerHTML = createArticleCard(latestArticle);
}

// Загрузка всех статей
async function loadAllArticles() {
    const container = document.getElementById('all-articles');
    if (!container) return;

    // Сортируем статьи по дате (новые сначала)
    const sortedArticles = [...articlesData].sort((a, b) => 
        new Date(b.date) - new Date(a.date)
    );

    container.innerHTML = sortedArticles.map(article => 
        createArticleCard(article)
    ).join('');
}

// Создание карточки статьи
function createArticleCard(article) {
    return `
        <div class="article-card">
            <img src="assets/images/posts/${article.image}" 
                 alt="${article.title}" 
                 class="article-image"
                 onerror="this.style.display='none'">
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
function showArticle(articleId) {
    const article = articlesData.find(a => a.id === articleId);
    if (!article) return;

    // Создаем модальное окно для статьи
    const modal = document.createElement('div');
    modal.className = 'article-modal';
    modal.innerHTML = `
        <div class="modal-content">
            <span class="close-modal" onclick="closeModal()">&times;</span>
            <img src="assets/images/posts/${article.image}" 
                 alt="${article.title}" 
                 class="modal-image"
                 onerror="this.style.display='none'">
            <h2>${article.title}</h2>
            <p><small>Опубликовано: ${article.date}</small></p>
            <div class="article-full-content">
                ${article.content}
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    document.body.style.overflow = 'hidden';
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
