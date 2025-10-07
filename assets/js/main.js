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
  const modalElement = document.getElementById('galleryModal');
  const modalDialog = document.querySelector('#galleryModal .modal-dialog');

  if (galleryItems && modalImage && modalElement && modalDialog) {
    galleryItems.forEach(item => {
      item.addEventListener('click', function() {
        const largeSrc = this.getAttribute('data-large-src') || this.src;
        if (largeSrc) {
          modalImage.src = largeSrc;
          console.log('Modal image set to:', largeSrc);

          const img = new Image();
          img.src = largeSrc;
          img.onload = function() {
            const width = img.naturalWidth;
            const height = img.naturalHeight;
            console.log('Image dimensions:', width, 'x', height);
            modalDialog.style.maxWidth = `${Math.min(width, window.innerWidth * 0.9)}px`;
            modalDialog.style.maxHeight = `${Math.min(height, window.innerHeight * 0.8)}px`;
          };
        } else {
          console.warn('data-large-src and src are missing for image:', this.src);
        }
        const modal = new bootstrap.Modal(modalElement, {
          keyboard: true,
          backdrop: true
        });
        modal.show();
      });
    });

    // Очистка после полного закрытия модального окна
    modalElement.addEventListener('hidden.bs.modal', function() {
      modalImage.src = '';
      modalDialog.style.maxWidth = '';
      modalDialog.style.maxHeight = '';
      console.log('Modal fully cleared');
      const modal = bootstrap.Modal.getInstance(modalElement);
      if (modal) {
        modal.dispose();
        console.log('Modal disposed');
      }
    });
  } else {
    console.warn('Gallery items, modal image, or modal element not found');
  }
});
