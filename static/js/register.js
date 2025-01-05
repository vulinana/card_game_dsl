const form = document.getElementById('loginForm');
const apiUrl = window.location.hostname === 'localhost'
    ? 'http://127.0.0.1:8080/'
    : 'https://web-production-84691.up.railway.app/';

form.addEventListener('submit', async (event) => {
    event.preventDefault();

    const username = document.getElementById('username').value
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const confirm_password = document.getElementById('confirmpassword').value

    if (password != confirm_password)
    {
        document.getElementById('message').textContent = "The passwords do not match!";
        return;
    }

    try {
        const response = await fetch(apiUrl + 'register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, email, password })
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
        document.getElementById('message').textContent = 'An error occurred during registration.';
    }
});
