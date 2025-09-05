// assets/scripts/gallery-loader.js
document.addEventListener('DOMContentLoaded', function() {
    loadGalleryImages();
});

async function loadGalleryImages() {
    const gallery = document.getElementById('image-gallery');
    
    if (!gallery) return;
    
    // Список изображений из папки assets/images/posts/
    const images = [
        'welcome-to-my-blog.jpg',
        'web-development-tips.jpg', 
        'css-tricks.jpg'
    ];
    
    gallery.innerHTML = '';
    
    images.forEach(image => {
        const imageName = image.replace('.jpg', '').replace(/-/g, ' ');
        const imageElement = document.createElement('div');
        imageElement.className = 'gallery-item';
        imageElement.innerHTML = `
            <img src="assets/images/posts/${image}" 
                 alt="${imageName}" 
                 class="gallery-image"
                 onerror="this.style.display='none'">
            <div class="image-overlay">
                ${imageName}
            </div>
        `;
        gallery.appendChild(imageElement);
    });
}
