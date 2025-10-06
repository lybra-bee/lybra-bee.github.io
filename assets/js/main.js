document.addEventListener('DOMContentLoaded', function() {
  // Анимация бегущей строки
  const textContainer = document.querySelector('.spread-text');
  if (textContainer) {
    const letters = Array.from(textContainer.querySelectorAll('span'));
    const midX = textContainer.offsetWidth / 2;

    letters.forEach(span => {
      const rect = span.getBoundingClientRect();
      const containerRect = textContainer.getBoundingClientRect();
      const finalX = rect.left - containerRect.left;
      span.dataset.finalX = finalX;
      span.style.transform = `translateX(${midX - finalX}px)`;
      span.style.opacity = 0;
    });

    let pairIndex = 0;

    function animatePair() {
      if (pairIndex >= Math.ceil(letters.length / 2)) {
        setTimeout(resetAnimation, 1500);
        return;
      }

      const left = letters[pairIndex];
      const right = letters[letters.length - 1 - pairIndex];

      [left, right].forEach(span => {
        if (span) {
          span.style.transition = 'transform 0.6s ease, opacity 0.3s ease';
          span.style.opacity = 1;
          span.style.transform = `translateX(0)`;
        }
      });

      pairIndex++;
      setTimeout(animatePair, 200);
    }

    function resetAnimation() {
      letters.forEach(span => {
        const finalX = span.dataset.finalX;
        span.style.transition = 'none';
        span.style.transform = `translateX(${midX - finalX}px)`;
        span.style.opacity = 0;
      });
      pairIndex = 0;
      setTimeout(animatePair, 300);
    }

    animatePair();
  }

  // Модальное окно галереи
  const galleryItems = document.querySelectorAll('.gallery-item img');
  const modalImage = document.getElementById('modalImage');
  if (galleryItems && modalImage) {
    galleryItems.forEach(item => {
      item.addEventListener('click', function() {
        modalImage.src = this.dataset.src;
        const modal = new bootstrap.Modal(document.getElementById('galleryModal'), {
          keyboard: true,
          backdrop: 'static'
        });
        modal.show();
      });
    });
  } else {
    console.warn('Gallery items or modal image not found');
  }
});
