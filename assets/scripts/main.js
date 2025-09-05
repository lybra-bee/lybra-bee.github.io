// assets/scripts/main.js

document.addEventListener('DOMContentLoaded', function() {
    // Мобильное меню
    const hamburger = document.querySelector('.hamburger');
    const navMenu = document.querySelector('.nav-menu');
    
    if (hamburger && navMenu) {
        hamburger.addEventListener('click', function() {
            navMenu.style.display = navMenu.style.display === 'flex' ? 'none' : 'flex';
        });
    }
    
    // Обработка ошибок изображений
    document.querySelectorAll('img').forEach(img => {
        img.onerror = function() {
            this.style.display = 'none';
        };
    });
});

// Данные статей
const articlesData = {
    'welcome-to-my-blog': {
        title: 'Добро пожаловать в мой блог',
        date: '2024-01-15',
        image: 'welcome-to-my-blog.jpg',
        content: `
            <h2>Добро пожаловать!</h2>
            <p>Это моя первая статья в новом блоге. Здесь я буду делиться своими знаниями и опытом в веб-разработке.</p>
            
            <h3>О чем этот блог</h3>
            <p>В этом блоге я планирую освещать:</p>
            <ul>
                <li>Современные технологии веб-разработки</li>
                <li>Лучшие практики и паттерны</li>
                <li>Интересные кейсы и проекты</li>
                <li>Полезные инструменты и ресурсы</li>
            </ul>
            
            <h3>Планы на будущее</h3>
            <p>Я надеюсь, что этот блог станет полезным ресурсом для других разработчиков.</p>
        `
    },
    'web-development-tips': {
        title: 'Советы по веб-разработке',
        date: '2024-01-20',
        image: 'web-development-tips.jpg',
        content: `
            <h2>Советы по веб-разработке</h2>
            <p>В этой статье я поделюсь полезными советами для начинающих разработчиков.</p>
            
            <h3>Основные принципы</h3>
            <ol>
                <li>Пишите чистый и читаемый код</li>
                <li>Используйте систему контроля версий</li>
                <li>Тестируйте свой код</li>
                <li>Изучайте новые технологии</li>
            </ol>
            
            <h3>Рекомендации</h3>
            <p>Регулярно практикуйтесь и не бойтесь совершать ошибки - это часть процесса обучения.</p>
        `
    },
    'css-tricks': {
        title: 'Полезные трюки CSS',
        date: '2024-01-25',
        image: 'css-tricks.jpg',
        content: `
            <h2>Полезные трюки CSS</h2>
            <p>Несколько интересных приемов работы с CSS для создания современных интерфейсов.</p>
            
            <h3>Flexbox и Grid</h3>
            <p>Используйте современные методы верстки для создания адаптивных интерфейсов.</p>
            
            <h3>Анимации</h3>
            <p>CSS анимации могут сделать ваш сайт более живым и интерактивным.</p>
            
            <h3>Переменные CSS</h3>
            <p>Используйте CSS переменные для удобства поддержки кода.</p>
        `
    }
};

// Показ статьи
function showArticle(articleId) {
    const article = articlesData[articleId];
    if (!article) {
        alert('Статья не найдена');
        return;
    }

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

// Добавляем функции в глобальную область видимости
window.showArticle = showArticle;
window.closeModal = closeModal;
