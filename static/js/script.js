// script.js

const menuBtn = document.getElementById("menu-btn");
const navLinks = document.querySelector(".nav-links");

menuBtn.addEventListener("click", () => {
  navLinks.classList.toggle("active");
});

// Fake Add To Cart Alert

const cartButtons = document.querySelectorAll(".product-card button");

cartButtons.forEach(button => {

  button.addEventListener("click", () => {
    alert("Product added to cart!");
  });

});

let seconds = 0;
let timerInterval;

function startTimer() {
    clearInterval(timerInterval);
    timerInterval = setInterval(() => {
        seconds++;
        let min = Math.floor(seconds / 60);
        let sec = seconds % 60;

        document.getElementById("timer").innerText =
            `${String(min).padStart(2, '0')}:${String(sec).padStart(2, '0')}`;
    }, 1000);
}

let progress = 0;

function increaseProgress() {
    if (progress < 100) {
        progress += 10;
        document.getElementById("plancheBar").style.width = progress + "%";
    }
}


const elements = document.querySelectorAll('.fade');

window.addEventListener('scroll', () => {
    elements.forEach(el => {
        const position = el.getBoundingClientRect().top;
        const screenHeight = window.innerHeight;

        if (position < screenHeight - 50) {
            el.classList.add('show');
        }
    });
});

function saveProgress(){
    let pushups=
    document.getElementById("pushups").value;
    localStorage.setItems(
    "pushups",
    pushups
    );
    alert("Progress Saved!");
}

// Dark Mode

function darkMode(){
    document.body.classList.toggle("dark");
}

// Workout Timer

let time = 60;

setInterval(()=>{
    document.getElementById("timer").innerHTML=time;
    time--;
},1000);