// js/setting.js
document.addEventListener('DOMContentLoaded', async () => {
    const token = localStorage.getItem('token');
    if (!token) return;

    const username = localStorage.getItem('username');
    document.getElementById('setting-username').textContent = `Tài khoản: ${username}`;

    // Remove unwanted sections if present: "Quản lý dữ liệu" and "Giao diện"
    // This makes the settings page hide those sections even if the HTML contains them.
    try {
        document.querySelectorAll('.setting-section').forEach(section => {
            const h3 = section.querySelector('h3');
            if (!h3) return;
            const txt = h3.textContent.trim();
            if (txt === 'Quản lý dữ liệu' || txt === 'Giao diện') {
                section.remove();
            }
        });
    } catch (e) {
        // ignore if DOM structure is different
        console.debug('setting.js: cleanup skipped', e);
    }

    const form = document.getElementById('change-password-form');
    const msgEl = document.getElementById('setting-msg');

     // --- Hàm gọi API chung ---
    async function fetchAPI(url, options = {}) {
        /* ... (copy hàm fetchAPI từ chat.js) ... */
        const defaultOptions = { /*...*/ }; /*...*/
        try { /*...*/ } catch (error) { /*...*/ }
    }


    // --- Đổi mật khẩu ---
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        msgEl.textContent = '';
        const newPassword = document.getElementById('new-password').value;
        const confirmPassword = document.getElementById('confirm-password').value;

        if (!newPassword) {
             msgEl.textContent = 'Vui lòng nhập mật khẩu mới.';
             msgEl.className = 'error-msg';
             return;
        }
        if (newPassword !== confirmPassword) {
            msgEl.textContent = 'Mật khẩu xác nhận không khớp.';
            msgEl.className = 'error-msg';
            return;
        }

        try {
            // *** GIẢ ĐỊNH API ĐỔI MẬT KHẨU: /users/me/password (PUT) ***
            // Bạn cần kiểm tra phương thức (PUT/PATCH) và body schema trong backend
            const response = await fetchAPI('/users/me/password', { // <-- KIỂM TRA LẠI ENDPOINT & METHOD
                method: 'PUT',
                body: JSON.stringify({ new_password: newPassword })
            });

            // Giả sử API trả về 200/204 khi thành công
             msgEl.textContent = 'Đổi mật khẩu thành công!';
             msgEl.className = 'success-msg';
             form.reset();
        } catch (error) {
             msgEl.textContent = `Đổi mật khẩu thất bại: ${error.message}`;
             msgEl.className = 'error-msg';
        }
    });

    // --- Xóa lịch sử ---
    document.getElementById('delete-history-btn').addEventListener('click', async () => {
        if (!confirm('Bạn có chắc chắn muốn xóa TOÀN BỘ lịch sử chat? Hành động này không thể hoàn tác.')) {
            return;
        }

        try {
            // *** API XÓA TẤT CẢ CONVERSATIONS: /conversations/ (DELETE) ***
            await fetchAPI('/conversations/', { // Sử dụng endpoint từ backend
                method: 'DELETE'
            });

            alert('Đã xóa toàn bộ lịch sử chat!');
            localStorage.removeItem('current_chat_id');
            // Nếu muốn cập nhật sidebar ngay lập tức trên trang setting,
            // bạn có thể thêm code xóa các item trong #chat-history-list ở sidebar chính (nếu nó tồn tại)
            // Hoặc đơn giản là thông báo và yêu cầu người dùng chuyển trang
        } catch (error) {
            console.error("Delete history error:", error);
            alert(`Xóa lịch sử thất bại: ${error.message}`);
        }
    });
});