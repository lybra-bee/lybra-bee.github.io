// assets/scripts/gallery-loader.js

document.addEventListener('DOMContentLoaded', function() {
    loadGalleryImages();
});

async function loadGalleryImages() {
    const gallery = document.getElementById('image-gallery');
    if (!gallery) return;

    // Список всех изображений из папки posts
    const images = [
        'welcome-to-my-blog.jpg',
        'web-development-tips.jpg', 
        'css-tricks.jpg'
        // Добавьте сюда все ваши изображения
    ];

    gallery.innerHTML = images.map(image => {
        const imageName = image.replace('.jpg', '').replace(/-/g, ' ');
        return `
            <div class="gallery-item">
                <img src="assets/images/posts/${image}" 
                     alt="${imageName}" 
                     class="gallery-image"
                     onerror="this.style.display='none'">
                <div class="image-overlay">
                    ${imageName}
                </div>
            </div>
        `;
    }).join('');
}
