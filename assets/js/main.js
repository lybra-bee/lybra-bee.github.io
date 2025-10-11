document.addEventListener('DOMContentLoaded', function() {
  // Анимация бегущей строки - СЛУЧАЙНЫЕ ПОЗИЦИИ
  const textContainer = document.querySelector('.spread-text');
  if (textContainer) {
    const letters = Array.from(textContainer.querySelectorAll('span'));
    
    // Сохраняем исходные позиции букв
    const originalPositions = letters.map(span => {
      const rect = span.getBoundingClientRect();
      const containerRect = textContainer.getBoundingClientRect();
      return {
        left: rect.left - containerRect.left,
        top: rect.top - containerRect.top,
        width: rect.width,
        height: rect.height
      };
    });

    function startAnimation() {
      // Размещаем буквы в случайных позициях
      placeLettersRandomly();
      
      // Запускаем анимацию полета к своим местам
      setTimeout(flyToPositions, 100);
    }

    function placeLettersRandomly() {
      const containerRect = textContainer.getBoundingClientRect();
      
      letters.forEach((span, index) => {
        // Случайные координаты в пределах видимой области
        const randomX = Math.random() * (window.innerWidth - 100);
        const randomY = Math.random() * (window.innerHeight - 50);
        
        // Вычисляем смещение от случайной точки к целевой позиции
        const targetLeft = originalPositions[index].left;
        const targetTop = originalPositions[index].top;
        
        const offsetX = randomX - targetLeft;
        const offsetY = randomY - targetTop;
        
        span.style.transition = 'none';
        span.style.transform = `translate(${offsetX}px, ${offsetY}px)`;
        span.style.opacity = '0';
        span.style.zIndex = '1000';
        span.style.willChange = 'transform, opacity';
      });
    }

    function flyToPositions() {
      let currentIndex = 0;
      
      function animateNextLetter() {
        if (currentIndex >= letters.length) {
          // Анимация завершена, перезапускаем через 4 секунды
          setTimeout(startAnimation, 4000);
          return;
        }

        const span = letters[currentIndex];
        
        // Случайная задержка для каждого письма (0-300ms)
        const randomDelay = Math.random() * 300;
        
        setTimeout(() => {
          span.style.transition = 'transform 1.2s cubic-bezier(0.2, 0.8, 0.3, 1), opacity 0.8s ease';
          span.style.transform = 'translate(0, 0)';
          span.style.opacity = '1';
        }, randomDelay);

        currentIndex++;
        setTimeout(animateNextLetter, 150); // Задержка между запуском анимаций
      }

      animateNextLetter();
    }

    // Запускаем анимацию
    startAnimation();
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
