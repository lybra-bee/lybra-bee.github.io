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

  // Проверяем, не инициализирован ли скрипт повторно
  if (modalElement && modalElement.dataset.initialized) {
    console.warn('Modal script already initialized, skipping');
    return;
  }

  if (galleryItems && modalImage && modalElement && modalDialog) {
    modalElement.dataset.initialized = 'true'; // Отмечаем, что скрипт инициализирован
    let lastFocusedElement = null; // Сохраняем элемент, вызвавший модальное окно

    const modalOpenHandler = function() {
      try {
        lastFocusedElement = document.activeElement; // Сохраняем элемент с фокусом
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
          img.onerror = function() {
            console.error('Failed to load image:', largeSrc);
          };

          const modal = new bootstrap.Modal(modalElement, {
            keyboard: true,
            backdrop: true,
            focus: false // Отключаем автоматический фокус Bootstrap
          });
          modal.show();

          // Устанавливаем фокус на модальное окно вручную
          setTimeout(() => {
            const closeButton = modalElement.querySelector('.btn-close');
            if (closeButton) {
              closeButton.focus();
              console.log('Focus set to close button');
            }
          }, 100);
        } else {
          console.warn('data-large-src and src are missing for image:', this.src);
        }
      } catch (error) {
        console.error('Error opening modal:', error);
      }
    };

    galleryItems.forEach(item => {
      item.setAttribute('tabindex', '0'); // Делаем превью доступным для фокуса
      item.removeEventListener('click', modalOpenHandler); // Удаляем старый обработчик
      item.addEventListener('click', modalOpenHandler); // Добавляем новый
    });

    // Очистка после полного закрытия модального окна
    const modalHiddenHandler = function() {
      try {
        modalImage.src = '';
        if (modalDialog) {
          modalDialog.style.maxWidth = '';
          modalDialog.style.maxHeight = '';
        }
        console.log('Modal fully cleared');

        // Возвращаем фокус на последний элемент
        if (lastFocusedElement && lastFocusedElement !== document.body) {
          setTimeout(() => {
            lastFocusedElement.focus();
            console.log('Focus returned to:', lastFocusedElement);
          }, 500); // Увеличена задержка для завершения анимации
        } else {
          console.warn('No valid lastFocusedElement, focus not returned');
        }
      } catch (error) {
        console.error('Error in hidden.bs.modal:', error);
      }
    };

    // Добавляем одноразовый обработчик
    modalElement.removeEventListener('hidden.bs.modal', modalHiddenHandler);
    modalElement.addEventListener('hidden.bs.modal', modalHiddenHandler, { once: true });
  } else {
    console.error('Gallery items, modal image, or modal element not found:', {
      galleryItems: !!galleryItems,
      modalImage: !!modalImage,
      modalElement: !!modalElement,
      modalDialog: !!modalDialog
    });
  }
});
