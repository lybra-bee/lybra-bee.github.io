document.addEventListener('DOMContentLoaded', function() {
  // Анимация бегущей строки - ИСПРАВЛЕННАЯ ВЕРСИЯ
  const textContainer = document.querySelector('.spread-text');
  if (textContainer) {
    const letters = Array.from(textContainer.querySelectorAll('span'));
    const containerRect = textContainer.getBoundingClientRect();
    const containerCenterX = containerRect.left + containerRect.width / 2;

    // Функция для сброса позиций букв в центр
    function resetLettersToCenter() {
      letters.forEach(span => {
        const rect = span.getBoundingClientRect();
        const letterCenterX = rect.left + rect.width / 2;
        const offsetX = containerCenterX - letterCenterX;
        
        // Сохраняем исходную позицию для анимации
        if (!span.dataset.originalTransform) {
          span.dataset.originalTransform = window.getComputedStyle(span).transform;
        }
        
        span.style.transition = 'none';
        span.style.transform = `translateX(${offsetX}px)`;
        span.style.opacity = '0';
      });
    }

    // Функция для анимации букв попарно из центра
    function animateLettersFromCenter() {
      let pairIndex = 0;
      const totalPairs = Math.ceil(letters.length / 2);

      function animateNextPair() {
        if (pairIndex >= totalPairs) {
          // Анимация завершена, перезапускаем через 2 секунды
          setTimeout(() => {
            resetLettersToCenter();
            setTimeout(animateLettersFromCenter, 100);
          }, 2000);
          return;
        }

        const leftIndex = pairIndex;
        const rightIndex = letters.length - 1 - pairIndex;

        const leftLetter = letters[leftIndex];
        const rightLetter = letters[rightIndex];

        // Анимируем левую букву
        if (leftLetter) {
          leftLetter.style.transition = 'transform 0.6s ease-out, opacity 0.4s ease';
          leftLetter.style.transform = leftLetter.dataset.originalTransform || 'translateX(0)';
          leftLetter.style.opacity = '1';
        }

        // Анимируем правую букву (если это не та же самая буква для нечетного количества)
        if (rightLetter && rightIndex !== leftIndex) {
          rightLetter.style.transition = 'transform 0.6s ease-out, opacity 0.4s ease';
          rightLetter.style.transform = rightLetter.dataset.originalTransform || 'translateX(0)';
          rightLetter.style.opacity = '1';
        }

        pairIndex++;
        setTimeout(animateNextPair, 150);
      }

      animateNextPair();
    }

    // Запускаем анимацию
    resetLettersToCenter();
    setTimeout(animateLettersFromCenter, 100);
  }

  // Модальное окно галереи (ваш существующий код)
  const galleryItems = document.querySelectorAll('.gallery-item img');
  const modalImage = document.getElementById('modalImage');
  const modalElement = document.getElementById('galleryModal');
  const modalDialog = document.querySelector('#galleryModal .modal-dialog');

  if (modalElement && modalElement.dataset.initialized) {
    console.warn('Modal script already initialized, skipping');
    return;
  }

  if (galleryItems && modalImage && modalElement && modalDialog) {
    modalElement.dataset.initialized = 'true';
    let lastFocusedElement = null;

    const modalOpenHandler = function() {
      try {
        lastFocusedElement = document.activeElement;
        const largeSrc = this.getAttribute('data-large-src') || this.src;
        if (largeSrc) {
          modalImage.src = largeSrc;

          const img = new Image();
          img.src = largeSrc;
          img.onload = function() {
            const width = img.naturalWidth;
            const height = img.naturalHeight;
            modalDialog.style.maxWidth = `${Math.min(width, window.innerWidth * 0.9)}px`;
            modalDialog.style.maxHeight = `${Math.min(height, window.innerHeight * 0.8)}px`;
          };
          img.onerror = function() {
            console.error('Failed to load image:', largeSrc);
          };

          const modal = new bootstrap.Modal(modalElement, {
            keyboard: true,
            backdrop: true,
            focus: false
          });
          modal.show();
        } else {
          console.warn('data-large-src and src are missing for image:', this.src);
        }
      } catch (error) {
        console.error('Error opening modal:', error);
      }
    };

    galleryItems.forEach(item => {
      item.setAttribute('tabindex', '0');
      item.removeEventListener('click', modalOpenHandler);
      item.addEventListener('click', modalOpenHandler);
    });

    const modalHiddenHandler = function() {
      try {
        modalImage.src = '';
        if (modalDialog) {
          modalDialog.style.maxWidth = '';
          modalDialog.style.maxHeight = '';
        }

        if (lastFocusedElement && lastFocusedElement !== document.body) {
          setTimeout(() => {
            lastFocusedElement.focus();
          }, 600);
        } else {
          console.warn('No valid lastFocusedElement, focus not returned');
        }
      } catch (error) {
        console.error('Error in hidden.bs.modal:', error);
      }
    };

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
