// js/login.js
document.addEventListener('DOMContentLoaded', () => {
    // --- Chuyển tab ---
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            button.classList.add('active');
            document.getElementById(button.dataset.tab).classList.add('active');
        });
    });

    // --- Form Đăng ký ---
    const regForm = document.getElementById('register-form');
    const regMsg = document.getElementById('register-msg');
    regForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        regMsg.textContent = '';
        const username = document.getElementById('reg-username').value;
        const email = document.getElementById('reg-email').value;
        const password = document.getElementById('reg-password').value;
        const confirmPassword = document.getElementById('reg-confirm-password').value;

        if (password !== confirmPassword) {
            regMsg.textContent = 'Mật khẩu xác nhận không khớp.';
            regMsg.className = 'error-msg';
            return;
        }
        if (!username || !email || !password) {
             regMsg.textContent = 'Vui lòng nhập đủ thông tin.';
             regMsg.className = 'error-msg';
             return;
        }

        try {
            // *** API ĐĂNG KÝ: /users/ (POST) ***
            const response = await fetch('http://localhost:8010/users/', { // Sử dụng endpoint từ backend
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    username, 
                    email,
                    password 
                }) // Schema UserCreate
            });

            if (response.ok) {
                regMsg.textContent = 'Đăng ký thành công! Vui lòng chuyển qua tab Đăng nhập.';
                regMsg.className = 'success-msg';
                regForm.reset();
                 // Tự chuyển tab
                tabButtons.forEach(btn => btn.classList.remove('active'));
                tabContents.forEach(content => content.classList.remove('active'));
                document.querySelector('[data-tab="login"]').classList.add('active');
                document.getElementById('login').classList.add('active');
            } else {
                let errorText = 'Đăng ký thất bại.';
                try {
                    const errorData = await response.json();
                    errorText = errorData.detail || `Lỗi ${response.status}`;
                } catch (jsonError) {
                    errorText = `Lỗi ${response.status}: ${response.statusText}`;
                }
                regMsg.textContent = errorText;
                regMsg.className = 'error-msg';
            }
        } catch (error) {
            console.error('Register error:', error);
            regMsg.textContent = 'Đã xảy ra lỗi kết nối.';
            regMsg.className = 'error-msg';
        }
    });

    // --- Form Đăng nhập ---
    const loginForm = document.getElementById('login-form');
    const loginError = document.getElementById('login-error');
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        loginError.textContent = '';
        const username = document.getElementById('login-username').value;
        const password = document.getElementById('login-password').value;

         if (!username || !password) {
             loginError.textContent = 'Vui lòng nhập đủ tên và mật khẩu.';
             return;
        }

        try {
            // *** API ĐĂNG NHẬP: /token (POST - form data) ***
            const response = await fetch('http://localhost:8010/token', { // Sử dụng endpoint từ backend
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: new URLSearchParams({ username, password }) // Gửi dạng form data
            });

            if (response.ok) {
                const data = await response.json(); // Expects {"access_token": ..., "token_type": "bearer"}
                if (data.access_token) {
                    localStorage.setItem('token', data.access_token);
                    
                    // Lấy thông tin user để kiểm tra role
                    try {
                        const userResponse = await fetch('http://localhost:8010/users/me', {
                            headers: { 'Authorization': `Bearer ${data.access_token}` }
                        });
                        
                        if (userResponse.ok) {
                            const userData = await userResponse.json();
                            // Lưu thông tin user
                            localStorage.setItem('username', userData.username);
                            localStorage.setItem('user_id', userData.id);
                            localStorage.setItem('role', userData.is_admin ? 'admin' : 'user');
                            
                            // Redirect dựa trên role
                            if (userData.is_admin) {
                                window.location.href = 'admin.html'; // Admin đi trang admin
                            } else {
                                window.location.href = 'index.html'; // User bình thường đi trang chủ
                            }
                        } else {
                            // Nếu không lấy được user info, vẫn chuyển về index
                            window.location.href = 'index.html';
                        }
                    } catch (error) {
                        console.error('Error fetching user info:', error);
                        window.location.href = 'index.html';
                    }
                } else {
                    loginError.textContent = 'Phản hồi đăng nhập không hợp lệ.';
                }
            } else if (response.status === 401 || response.status === 400) { // Unauthorized or Bad Request
                 loginError.textContent = 'Tên đăng nhập hoặc mật khẩu không đúng.';
            }
             else {
                 loginError.textContent = `Lỗi ${response.status}: Đăng nhập thất bại.`;
            }
        } catch (error) {
            console.error('Login error:', error);
            loginError.textContent = 'Đã xảy ra lỗi kết nối.';
        }
    });
});