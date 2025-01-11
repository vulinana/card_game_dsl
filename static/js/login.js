const form = document.getElementById('loginForm');
const apiUrl = window.location.hostname === 'localhost'
    ? 'http://127.0.0.1:8080/'
    : 'https://card-game-dsl.onrender.com/';

form.addEventListener('submit', async (event) => {
    event.preventDefault();

    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    try {
        const response = await fetch(apiUrl + 'login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });

        const result = await response.json();
        if (response.ok) {
            localStorage.setItem('email', result.email);
            window.location.href = '/index'
        } else {
            document.getElementById('message').textContent = `${result.message}`;
        }
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('message').textContent = 'An error occurred during login.';
    }
});
