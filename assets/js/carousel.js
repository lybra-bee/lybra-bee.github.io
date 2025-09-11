document.addEventListener("DOMContentLoaded", function() {
  const carousels = document.querySelectorAll(".carousel");
  carousels.forEach(carousel => {
    let index = 0;
    const items = carousel.querySelectorAll(".carousel-item");
    if(items.length === 0) return;
    items.forEach(item => item.style.display = "none");
    items[index].style.display = "block";

    setInterval(() => {
      items[index].style.display = "none";
      index = (index + 1) % items.length;
      items[index].style.display = "block";
    }, 3000);
  });
});
