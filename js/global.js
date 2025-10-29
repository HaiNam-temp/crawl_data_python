// js/global.js

// Hàm logout tách riêng
function logoutUser() {
    console.log("Logging out...");
    // Xóa thông tin user khỏi localStorage
    ['token', 'username', 'user_id', 'role', 'current_chat_id'].forEach(item => localStorage.removeItem(item));
    // Có thể gọi API /logout nếu backend có
    window.location.href = 'login.html';
}


document.addEventListener('DOMContentLoaded', async () => {
    const sidebarContainer = document.getElementById('sidebar-container');
    if (!sidebarContainer) return; // Không cần sidebar ở trang login

    const token = localStorage.getItem('token');
    if (!token) {
        logoutUser(); // Gọi logout nếu không có token (bảo vệ thêm)
        return;
    }

    let username = localStorage.getItem('username');
    let role = localStorage.getItem('role');
    let userId = localStorage.getItem('user_id');

    // Luôn kiểm tra/lấy thông tin user từ API mỗi khi tải trang có sidebar
    // để đảm bảo thông tin (đặc biệt là role) luôn mới nhất
    console.log("Fetching user info from API...");
    try {
        // *** API LẤY THÔNG TIN USER: /users/me (GET) ***
        const response = await fetch('http://localhost:8010/users/me', { // Sử dụng endpoint từ backend
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
            const userData = await response.json(); // Expects {id, username, email, is_admin}
            username = userData.username;
            role = userData.is_admin ? 'admin' : 'user'; // Backend trả về is_admin (boolean)
            userId = userData.id;
            // Cập nhật lại localStorage
            localStorage.setItem('username', username);
            localStorage.setItem('role', role);
            localStorage.setItem('user_id', userId);
            console.log("User info updated:", { username, role, userId });
        } else if (response.status === 401) { // Unauthorized - Token hết hạn hoặc không hợp lệ
            console.error("Token invalid or expired, logging out.");
            logoutUser();
            return; // Dừng render sidebar
        } else {
             throw new Error(`API error fetching user: ${response.status}`);
        }
    } catch (error) {
        console.error("Error fetching user info:", error);
        logoutUser(); // Đăng xuất nếu có lỗi
        return;
    }


    // --- Render Sidebar ---
    const currentPage = window.location.pathname.split('/').pop();

    // Xác định các link dựa trên trang hiện tại
    const isActive = (pageName) => currentPage === pageName ? 'active' : '';

    const navLinks = [
        { href: 'index.html', icon: '🏠', label: 'Trang chủ' },
        { href: 'search.html', icon: '🔍', label: 'Tìm kiếm sản phẩm' },
        { href: 'chat.html', icon: '💬', label: 'Trợ lý Chatbot' },
    ];

    const settingLink = { href: 'setting.html', icon: '⚙️', label: 'Cài đặt' };
    const adminLink = { href: 'admin.html', icon: '🔒', label: 'Trang Admin' };

    let navHtml = `
        <h3>Chào, ${username}!</h3>
        <button id="logout-btn" class="btn btn-secondary" style="width: 100%;">Đăng xuất</button>
        <hr>
        <div class="nav-links">
            ${navLinks.map(link => `<a href="${link.href}" class="nav-link ${isActive(link.href)}">${link.icon} ${link.label}</a>`).join('')}
        </div>
        <div class="sidebar-bottom">
            <a href="${settingLink.href}" class="nav-link ${isActive(settingLink.href)}">${settingLink.icon} ${settingLink.label}</a>
            ${role === 'admin' ? `<a href="${adminLink.href}" class="nav-link ${isActive(adminLink.href)}">${adminLink.icon} ${adminLink.label}</a>` : ''}
        </div>
    `;
    sidebarContainer.innerHTML = navHtml;

    // --- Gán sự kiện Logout ---
    document.getElementById('logout-btn').addEventListener('click', logoutUser);
});