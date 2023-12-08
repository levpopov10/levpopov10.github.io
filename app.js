 const isIos = () => {
           const userAgent = window.navigator.userAgent.toLowerCase();
           return /iphone|ipad|ipod/.test( userAgent );
       };
       // Проверяем, открыто ли приложение отдельно или в браузере
       const isInStandaloneMode = () => ('standalone' in window.navigator) && (window.navigator.standalone);



       // Если приложение открыто на iOS и в браузере, то предлагаем установить
       if (isIos() && !isInStandaloneMode()) {
           this.setState({ isShown: true }); // На примере React
       }

var counterDisplay = document.createElement('div');
counterDisplay.style.position = 'absolute';
counterDisplay.style.top = '10px';
counterDisplay.style.right = '10px';
counterDisplay.style.fontSize = '24px';

function start(){
  document.querySelectorAll('body *').forEach(function(element) {
      element.remove();
  });
  
  var counter = 0;
  var img = document.createElement('img');
  img.src = 'img.png';
  img.style.position = 'absolute';
  img.style.width = "100px";

  var windowWidth = window.innerWidth;
  var windowHeight = window.innerHeight;

  var maxX = windowWidth - 150; 
  var maxY = windowHeight - 150;
  var randomX = Math.floor(Math.random() * maxX);
  var randomY = Math.floor(Math.random() * maxY);
  
  img.style.left = randomX + 'px';
  img.style.top = randomY + 'px';

  var exitButton = document.createElement('button');
  exitButton.innerHTML = "Exit";
  exitButton.style.position = 'fixed';
  exitButton.style.top = '50px';
  exitButton.style.right = '10px';
  exitButton.classList.add("btn", "btn-danger");
  exitButton.addEventListener('click', function() {
    window.location.href = "https://www.google.com/";
  });

  document.body.appendChild(counterDisplay);
  document.body.appendChild(exitButton);
  document.body.appendChild(img);

  img.addEventListener('click', function() {
    var newX = Math.floor(Math.random() * maxX);
    var newY = Math.floor(Math.random() * maxY);
    img.style.left = newX + 'px';
    img.style.top = newY + 'px';
    counter++;
    counterDisplay.innerHTML = 'Score: '+counter;
  });
}
