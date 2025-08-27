// Простые частицы на фоне hero
const canvas = document.createElement("canvas");
document.querySelector(".hero").appendChild(canvas);
canvas.width = window.innerWidth;
canvas.height = document.querySelector(".hero").offsetHeight;
const ctx = canvas.getContext("2d");

let particlesArray = [];
const particleCount = 50;

class Particle {
    constructor(){
        this.x = Math.random() * canvas.width;
        this.y = Math.random() * canvas.height;
        this.size = Math.random() * 3 + 1;
        this.speedX = Math.random() * 1 - 0.5;
        this.speedY = Math.random() * 1 - 0.5;
    }
    update(){
        this.x += this.speedX;
        this.y += this.speedY;
        if(this.x < 0 || this.x > canvas.width) this.speedX *= -1;
        if(this.y < 0 || this.y > canvas.height) this.speedY *= -1;
    }
    draw(){
        ctx.fillStyle = "rgba(255,255,255,0.6)";
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI*2);
        ctx.fill();
    }
}

function init(){
    particlesArray = [];
    for(let i=0;i<particleCount;i++){
        particlesArray.push(new Particle());
    }
}

function animate(){
    ctx.clearRect(0,0,canvas.width,canvas.height);
    particlesArray.forEach(p => {p.update(); p.draw();});
    requestAnimationFrame(animate);
}

init();
animate();
window.addEventListener("resize", ()=> {
    canvas.width = window.innerWidth;
    canvas.height = document.querySelector(".hero").offsetHeight;
    init();
});
