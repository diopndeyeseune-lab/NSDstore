function toggleMenu() {
    document.getElementById('menu-lateral').classList.toggle('ouvert');
    document.getElementById('overlay').classList.toggle('ouvert');
}

document.getElementById('btn-menu').addEventListener('click', toggleMenu);
document.getElementById('btn-fermer-menu').addEventListener('click', toggleMenu);
document.getElementById('overlay').addEventListener('click', toggleMenu);

document.getElementById('btn-recherche').addEventListener('click', function () {
    document.getElementById('recherche-globale').classList.toggle('ouvert');
});

document.querySelectorAll('input[type="password"]').forEach(function (input) {
    const wrapper = document.createElement('div');
    wrapper.className = 'password-wrapper';
    input.parentNode.insertBefore(wrapper, input);
    wrapper.appendChild(input);

    const toggle = document.createElement('button');
    toggle.type = 'button';
    toggle.className = 'password-toggle';
    toggle.setAttribute('aria-label', 'Afficher le mot de passe');
    toggle.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7z"/><circle cx="12" cy="12" r="3"/></svg>';
    wrapper.appendChild(toggle);

    toggle.addEventListener('click', function () {
        input.type = input.type === 'password' ? 'text' : 'password';
    });
});
