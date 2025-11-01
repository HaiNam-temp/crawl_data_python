// js/admin.js
document.addEventListener('DOMContentLoaded', async () => {
    const token = localStorage.getItem('token');

    // Nếu không có token thì logout
    if (!token) {
        if (typeof logoutUser === 'function') logoutUser();
        else window.location.href = 'login.html';
        return;
    }

    const platformList = document.getElementById('platform-list');
    const form = document.getElementById('new-platform-form');
    const usersList = document.getElementById('users-list');
    const statUsers = document.getElementById('stat-users');
    const statConversations = document.getElementById('stat-conversations');
    const statMessages = document.getElementById('stat-messages');
    const statPlatforms = document.getElementById('stat-platforms');

    // --- Hàm gọi API chung (dùng token từ localStorage) ---
    async function fetchAPI(url, options = {}) {
        const baseURL = 'http://localhost:8010';
        const fullURL = url.startsWith('http') ? url : baseURL + url;

        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            }
        };
        const mergedOptions = { ...defaultOptions, ...options };
        // Ensure headers are merged correctly
        mergedOptions.headers = { ...defaultOptions.headers, ...(options.headers || {}) };

        // Remove Content-Type for GET-like requests without body
        if (!mergedOptions.body && mergedOptions.method !== 'POST' && mergedOptions.method !== 'PUT' && mergedOptions.method !== 'PATCH') {
            delete mergedOptions.headers['Content-Type'];
        }

        try {
            const response = await fetch(fullURL, mergedOptions);
            if (!response.ok) {
                if (response.status === 401) {
                    // Token invalid or expired - try to logout user if helper exists
                    if (typeof logoutUser === 'function') logoutUser();
                }
                const errorText = await response.text();
                console.error('API Error:', response.status, errorText);
                throw new Error(`API Error ${response.status}: ${errorText || response.statusText}`);
            }

            if (response.headers.get('content-length') === '0' || response.status === 204) {
                return {};
            }

            return await response.json();
        } catch (error) {
            console.error('Fetch Error:', error);
            throw error;
        }
    }

    // Verify current user & role from backend (don't rely on possibly stale localStorage)
    let currentRole = localStorage.getItem('role');
    try {
        const me = await fetchAPI('/users/me');
        currentRole = me.is_admin ? 'admin' : 'user';
        localStorage.setItem('role', currentRole);
    } catch (e) {
        console.error('Failed to verify current user:', e);
        // If verification fails (e.g., 401), force logout
        if (typeof logoutUser === 'function') logoutUser(); else window.location.href = 'login.html';
        return;
    }

    // If not admin, show access denied and stop
    if (currentRole !== 'admin') {
        const main = document.querySelector('.main-content');
        if (main) {
            main.innerHTML = '<h2>Lỗi truy cập ⛔</h2><p>Bạn không có quyền truy cập trang này.</p><a href="index.html">Về trang chủ</a>';
        }
        return;
    }

    // --- Tải danh sách users (admin) ---
    async function loadUsers() {
        usersList.innerHTML = 'Đang tải...';
        try {
            const users = await fetchAPI('/admin/users/');
            usersList.innerHTML = '';
            if (users && Array.isArray(users) && users.length > 0) {
                const table = document.createElement('table');
                table.style.width = '100%';
                table.style.borderCollapse = 'collapse';
                table.innerHTML = `
                    <thead>
                        <tr style="background: #f3f4f6; text-align: left;">
                            <th style="padding: 10px; border: 1px solid #ddd;">Username</th>
                            <th style="padding: 10px; border: 1px solid #ddd;">Email</th>
                            <th style="padding: 10px; border: 1px solid #ddd;">Quyền</th>
                            <th style="padding: 10px; border: 1px solid #ddd;">Ngày tạo</th>
                            <th style="padding: 10px; border: 1px solid #ddd;">Hành động</th>
                        </tr>
                    </thead>
                    <tbody id="users-table-body"></tbody>
                `;
                usersList.appendChild(table);
                
                const tbody = document.getElementById('users-table-body');
                users.forEach(user => {
                    const row = document.createElement('tr');
                    const date = new Date(user.created_at);
                    row.innerHTML = `
                        <td style="padding: 10px; border: 1px solid #ddd;">${user.username}</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">${user.email}</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">
                            <span style="padding: 3px 8px; border-radius: 4px; background: ${user.is_admin ? '#fee2e2' : '#e0f2fe'}; color: ${user.is_admin ? '#991b1b' : '#075985'};">
                                ${user.is_admin ? '👑 Admin' : '👤 User'}
                            </span>
                        </td>
                        <td style="padding: 10px; border: 1px solid #ddd;">${date.toLocaleDateString('vi-VN')}</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">
                            ${user.is_admin ? '<em style="color: #999;">Không thể xóa</em>' : `<button class="btn-delete-user" data-user-id="${user.id}" data-username="${user.username}" style="padding: 5px 10px; background: #dc2626; color: white; border: none; border-radius: 4px; cursor: pointer;">Xóa</button>`}
                        </td>
                    `;
                    tbody.appendChild(row);
                });

                // Gán sự kiện xóa user
                document.querySelectorAll('.btn-delete-user').forEach(btn => {
                    btn.addEventListener('click', async (e) => {
                        const userId = e.target.dataset.userId;
                        const username = e.target.dataset.username;
                        if (confirm(`Bạn có chắc muốn xóa user "${username}"? Tất cả conversations và messages của user này cũng sẽ bị xóa.`)) {
                            try {
                                await fetchAPI(`/admin/users/${userId}`, { method: 'DELETE' });
                                alert(`Đã xóa user: ${username}`);
                                await loadUsers();
                                await loadStats(); // Cập nhật thống kê
                            } catch (error) {
                                alert(`Xóa user thất bại: ${error.message}`);
                            }
                        }
                    });
                });
            } else {
                usersList.innerHTML = '<p>Chưa có người dùng nào.</p>';
            }
        } catch (error) {
            usersList.innerHTML = `<p style="color: red;">Lỗi tải danh sách users: ${error.message}</p>`;
        }
    }

    // --- Tải thống kê hệ thống (admin) ---
    async function loadStats() {
        try {
            const stats = await fetchAPI('/admin/stats');
            if (statUsers) statUsers.textContent = stats.total_users ?? '-';
            if (statConversations) statConversations.textContent = stats.total_conversations ?? '-';
            if (statMessages) statMessages.textContent = stats.total_messages ?? '-';
            if (statPlatforms) statPlatforms.textContent = stats.total_platforms ?? '-';
        } catch (error) {
            console.error('Failed to load stats', error);
            // Optionally show an inline error near stats container
        }
    }

    // --- Tải danh sách platform ---
    async function loadPlatforms() {
        if (!platformList) return;
        platformList.innerHTML = 'Đang tải...';
        try {
            // *** API LẤY PLATFORMS: /platforms/ (GET) ***
            const platforms = await fetchAPI('/platforms/'); // Sử dụng endpoint từ backend
            platformList.innerHTML = '';
                if (platforms && Array.isArray(platforms) && platforms.length > 0) { // Backend returns [{id, name, url, status, created_at}]
                    platforms.forEach(p => {
                        platformList.innerHTML += `
                            <div style="border: 1px solid #ddd; padding: 15px; border-radius: 8px; text-align: center;">
                                <img src="${p.logo_url || 'Image/iconSearch.png'}" alt="${p.name}" style="width: 40px; height: 40px; object-fit: contain; margin-bottom: 10px;">
                                <strong style="display: block; margin-bottom: 5px;">${p.name}</strong>
                                <p style="font-size: 0.9em; color: #666;">Status: ${p.status}</p>
                                <p><a href="${p.url}" target="_blank" class="btn btn-secondary btn-sm">Truy cập ↗</a></p>
                            </div>
                        `;
                });
            } else {
                 platformList.innerHTML = '<p>Chưa có nền tảng nào.</p>';
            }
        } catch (error) {
             platformList.innerHTML = `<p style="color: red;">Lỗi tải danh sách: ${error.message}</p>`;
        }
    }

    // --- Thêm platform mới ---
    if (form) {
        form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const nameInput = document.getElementById('platform-name');
        const urlInput = document.getElementById('platform-url');

        const newPlatform = {
            name: nameInput.value.trim(),
            url: urlInput.value.trim(),
            status: 'active' // Backend expects { name, url, status }
        };

        if (!newPlatform.name || !newPlatform.url) {
            alert("Tên và URL là bắt buộc.");
            return;
        }

        try {
            // *** API THÊM PLATFORM: /platforms/ (POST) ***
            await fetchAPI('/platforms/', { // Sử dụng endpoint từ backend
                method: 'POST',
                body: JSON.stringify(newPlatform) // Schema PlatformCreate
            });

            await loadPlatforms(); // Tải lại danh sách
            form.reset();
            alert(`Đã thêm nền tảng: ${newPlatform.name}`);
       } catch (error) {
           alert(`Thêm nền tảng thất bại: ${error.message}`);
       }
    });
    }

    // Khởi chạy
    // Load admin-specific data
    await Promise.all([
        loadStats(),
        loadUsers(),
        // loadPlatforms only if the platform UI exists
        (async () => { if (platformList) await loadPlatforms(); })()
    ]);
});