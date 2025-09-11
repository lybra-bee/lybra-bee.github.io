// Lightbox для галереи
document.addEventListener('DOMContentLoaded', () => {
    const lightbox = document.createElement('div');
    lightbox.classList.add('lightbox');
    document.body.appendChild(lightbox);

    lightbox.addEventListener('click', () => {
        lightbox.classList.remove('show');
        lightbox.innerHTML = '';
    });

    document.querySelectorAll('.carousel-item a').forEach(el => {
        el.addEventListener('click', e => {
            e.preventDefault();
            const img = document.createElement('img');
            img.src = el.href;
            lightbox.innerHTML = '';
            lightbox.appendChild(img);
            lightbox.classList.add('show');
        });
    });
});
