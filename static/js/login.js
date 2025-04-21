
document.addEventListener('DOMContentLoaded', function () {
    // Alternar entre login y registro
    const loginBtn = document.getElementById('loginBtn');
    const registerBtn = document.getElementById('registerBtn');
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');

    function activateTab(tab) {
        if (tab === 'login') {
            loginBtn.classList.add('active');
            loginBtn.setAttribute('aria-selected', 'true');
            loginBtn.tabIndex = 0;
            registerBtn.classList.remove('active');
            registerBtn.setAttribute('aria-selected', 'false');
            registerBtn.tabIndex = -1;
            loginForm.hidden = false;
            registerForm.hidden = true;
        } else {
            registerBtn.classList.add('active');
            registerBtn.setAttribute('aria-selected', 'true');
            registerBtn.tabIndex = 0;
            loginBtn.classList.remove('active');
            loginBtn.setAttribute('aria-selected', 'false');
            loginBtn.tabIndex = -1;
            registerForm.hidden = false;
            loginForm.hidden = true;
        }
    }

    loginBtn.addEventListener('click', () => activateTab('login'));
    registerBtn.addEventListener('click', () => activateTab('register'));

    // Hacer desaparecer los mensajes flash después de 3 segundos
    const flashMessages = document.querySelectorAll('#flashMessages .alert');
    flashMessages.forEach((message) => {
        setTimeout(() => {
            message.style.opacity = 0;  // Hacemos que desaparezca
            message.style.transition = "opacity 1s";  // Transición suave
        }, 3000);  // 3000 milisegundos = 3 segundos
    });
});
