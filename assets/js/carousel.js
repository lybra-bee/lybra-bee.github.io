const track = document.querySelector(".carousel-track");
const prevBtn = document.querySelector(".carousel-btn.prev");
const nextBtn = document.querySelector(".carousel-btn.next");

let index = 0;

nextBtn.addEventListener("click", () => {
  index++;
  if (index >= track.children.length) index = 0;
  track.style.transform = `translateX(-${index * 320}px)`;
});

prevBtn.addEventListener("click", () => {
  index--;
  if (index < 0) index = track.children.length - 1;
  track.style.transform = `translateX(-${index * 320}px)`;
});
