// Анимация scroll reveal
document.addEventListener("DOMContentLoaded", function() {
    const cards = document.querySelectorAll(".glass-card, .article-card");
    const revealOnScroll = () => {
        const triggerBottom = window.innerHeight / 5 * 4;
        cards.forEach(card => {
            const cardTop = card.getBoundingClientRect().top;
            if(cardTop < triggerBottom){
                card.classList.add("show");
            } else {
                card.classList.remove("show");
            }
        });
    };
    window.addEventListener("scroll", revealOnScroll);
    revealOnScroll();
});
