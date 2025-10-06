// Анимация бегущей строки
document.addEventListener('DOMContentLoaded', function() {
  const textContainer = document.querySelector('.spread-text');
  if (textContainer) {
    const letters = Array.from(textContainer.querySelectorAll('span'));
    const midX = textContainer.offsetWidth / 2;

    // Сохраняем конечные позиции
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

  // Переключение тёмной темы
  const toggle = document.getElementById('dark-mode-toggle');
  if (toggle) {
    toggle.addEventListener('click', function() {
      document.body.classList.toggle('dark-mode');
      this.textContent = document.body.classList.contains('dark-mode') ? 'Светлая тема' : 'Темная тема';
      localStorage.setItem('darkMode', document.body.classList.contains('dark-mode'));
    });

    const savedTheme = localStorage.getItem('darkMode');
    if (savedTheme === 'true') {
      document.body.classList.add('dark-mode');
      toggle.textContent = 'Светлая тема';
    }
  }
});
document.getElementById('dark-mode-toggle').addEventListener('click', () => {
  document.body.classList.toggle('dark-mode');
  localStorage.setItem('darkMode', document.body.classList.contains('dark-mode'));
});

if (localStorage.getItem('darkMode') === 'true') {
  document.body.classList.add('dark-mode');
}
