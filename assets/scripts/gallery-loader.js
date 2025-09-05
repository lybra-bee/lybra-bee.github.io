// Предполагаемый список изображений (замените на реальные названия)
const imageList = [
    'welcome-to-my-blog.jpg',
    'web-development-tips.jpg',
    'css-tricks.jpg',
    'javascript-basics.jpg',
    'responsive-design.jpg'
];

async function loadGalleryImages() {
    const gallery = document.getElementById('image-gallery');
    
    if (!gallery) return;
    
    try {
        // В реальном проекте здесь может быть запрос к API
        // для получения списка изображений
        const images = imageList;
        
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
        
    } catch (error) {
        console.error('Error loading gallery images:', error);
        gallery.innerHTML = '<p>Ошибка загрузки изображений</p>';
    }
}
