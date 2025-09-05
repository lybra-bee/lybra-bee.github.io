// assets/scripts/gallery-loader.js

const ARTICLES_DATA_URL = 'data/articles.json';

async function fetchGalleryData() {
    try {
        const response = await fetch(ARTICLES_DATA_URL);
        if (!response.ok) throw new Error('Failed to fetch gallery data');
        return await response.json();
    } catch (error) {
        console.error('Error loading gallery data:', error);
        return { images: [] };
    }
}

async function loadGalleryImages() {
    const gallery = document.getElementById('image-gallery');
    if (!gallery) return;

    gallery.innerHTML = '<div class="loading">Загрузка изображений...</div>';

    try {
        const data = await fetchGalleryData();
        
        if (data.images.length > 0) {
            gallery.innerHTML = data.images.map(image => {
                const imageName = image.replace(/\.[^/.]+$/, '').replace(/-/g, ' ');
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
        } else {
            gallery.innerHTML = '<div class="no-images">Изображения не найдены</div>';
        }
    } catch (error) {
        gallery.innerHTML = '<div class="error">Ошибка загрузки галереи</div>';
    }
}

document.addEventListener('DOMContentLoaded', loadGalleryImages);
