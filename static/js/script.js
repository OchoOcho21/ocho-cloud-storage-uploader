function showRegisterForm() {
  document.getElementById('loginForm').style.display = 'none';
  document.getElementById('registerForm').style.display = 'block';
  document.getElementById('loginStatus').textContent = '';
}

function showLoginForm() {
  document.getElementById('registerForm').style.display = 'none';
  document.getElementById('loginForm').style.display = 'block';
  document.getElementById('registerStatus').textContent = '';
}

function login() {
  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;
  
  if (!email || !password) {
    document.getElementById('loginStatus').textContent = 'Please enter both email and password';
    document.getElementById('loginStatus').className = 'mt-3 text-center text-danger';
    return;
  }

  fetch('/login', {
    method: 'POST',
    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
    body: `email=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      window.location.href = '/dashboard';
    } else {
      document.getElementById('loginStatus').textContent = data.msg || 'Login failed';
      document.getElementById('loginStatus').className = 'mt-3 text-center text-danger';
    }
  })
  .catch(error => {
    console.error('Error:', error);
    document.getElementById('loginStatus').textContent = 'An error occurred during login';
    document.getElementById('loginStatus').className = 'mt-3 text-center text-danger';
  });
}

function register() {
  const email = document.getElementById('regEmail').value;
  const password = document.getElementById('regPassword').value;
  const confirmPassword = document.getElementById('confirmPassword').value;
  
  if (!email || !password || !confirmPassword) {
    document.getElementById('registerStatus').textContent = 'Please fill in all fields';
    document.getElementById('registerStatus').className = 'mt-3 text-center text-danger';
    return;
  }
  
  if (password !== confirmPassword) {
    document.getElementById('registerStatus').textContent = 'Passwords do not match';
    document.getElementById('registerStatus').className = 'mt-3 text-center text-danger';
    return;
  }
  
  if (password.length < 8) {
    document.getElementById('registerStatus').textContent = 'Password must be at least 8 characters';
    document.getElementById('registerStatus').className = 'mt-3 text-center text-danger';
    return;
  }

  fetch('/register', {
    method: 'POST',
    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
    body: `email=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      document.getElementById('registerStatus').textContent = 'Registration successful! Please login';
      document.getElementById('registerStatus').className = 'mt-3 text-center text-success';
      showLoginForm();
    } else {
      document.getElementById('registerStatus').textContent = data.msg || 'Registration failed';
      document.getElementById('registerStatus').className = 'mt-3 text-center text-danger';
    }
  })
  .catch(error => {
    console.error('Error:', error);
    document.getElementById('registerStatus').textContent = 'An error occurred during registration';
    document.getElementById('registerStatus').className = 'mt-3 text-center text-danger';
  });
}

function formatBytes(bytes, decimals = 2) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}
