class ArticlesCarousel {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.articles = [];
        this.currentIndex = 0;
    }
    
    async loadArticles() {
        try {
            const response = await fetch('../data/articles.json');
            this.articles = await response.json();
            this.render();
        } catch (error) {
            console.error('Error loading articles for carousel:', error);
            this.container.innerHTML = '<p>Ошибка загрузки статей</p>';
        }
    }
    
    render() {
        if (this.articles.length === 0) {
            this.container.innerHTML = '<p>Статьи не найдены</p>';
            return;
        }
        
        this.container.innerHTML = `
            <div class="carousel">
                <div class="carousel-inner" style="transform: translateX(-${this.currentIndex * 100}%)">
                    ${this.articles.map(article => `
                        <div class="carousel-item">
                            <img src="../assets/images/posts/${article.image}" 
                                 alt="${article.title}" 
                                 class="carousel-image"
                                 onerror="this.style.display='none'">
                            <div class="carousel-content">
                                <h3>${article.title}</h3>
                                <p>${article.excerpt}</p>
                                <a href="articles.html#${article.id}" class="read-more">Читать далее</a>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
            <div class="carousel-nav">
                <button class="carousel-btn" onclick="carousel.prev()">← Назад</button>
                <span class="carousel-indicator">${this.currentIndex + 1} / ${this.articles.length}</span>
                <button class="carousel-btn" onclick="carousel.next()">Вперед →</button>
            </div>
        `;
    }
    
    next() {
        this.currentIndex = (this.currentIndex + 1) % this.articles.length;
        this.render();
    }
    
    prev() {
        this.currentIndex = (this.currentIndex - 1 + this.articles.length) % this.articles.length;
        this.render();
    }
}

// Глобальная переменная для карусели
let carousel;
