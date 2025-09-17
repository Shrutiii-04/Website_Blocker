document.getElementById('registrationForm').addEventListener('submit', function(event) {
    var username = document.getElementById('username').value;
    var email = document.getElementById('email').value;
    var password = document.getElementById('password').value;
    var error = '';

    if (!username) {
        error = 'Username is required.';
    } else if (!email) {
        error = 'Email is required.';
    } else if (!password) {
        error = 'Password is required.';
    }

    if (error) {
        event.preventDefault();
        alert(error);
    }
});
