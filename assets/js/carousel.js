document.addEventListener('DOMContentLoaded', () => {
  const carousels = document.querySelectorAll('.carousel');

  carousels.forEach(carousel => {
    const track = carousel.querySelector('.carousel-track');
    const items = carousel.querySelectorAll('.carousel-item');
    let index = 0;
    let interval;

    const moveTo = (i) => {
      const width = items[0].offsetWidth + parseInt(getComputedStyle(items[0]).marginRight);
      track.style.transform = `translateX(-${i * width}px)`;
    }

    const next = () => {
      index = (index + 1) % items.length;
      moveTo(index);
    }

    const prev = () => {
      index = (index - 1 + items.length) % items.length;
      moveTo(index);
    }

    const startAuto = () => interval = setInterval(next, 3000);
    const stopAuto = () => clearInterval(interval);

    carousel.addEventListener('mouseenter', stopAuto);
    carousel.addEventListener('mouseleave', startAuto);

    const btnNext = carousel.querySelector('.carousel-btn.next');
    const btnPrev = carousel.querySelector('.carousel-btn.prev');

    if (btnNext) btnNext.addEventListener('click', next);
    if (btnPrev) btnPrev.addEventListener('click', prev);

    startAuto();
  });
});
