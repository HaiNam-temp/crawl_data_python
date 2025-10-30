// js/admin.js
document.addEventListener('DOMContentLoaded', async () => {
    const token = localStorage.getItem('token');
    const role = localStorage.getItem('role');

    // Kiểm tra quyền Admin
    if (role !== 'admin') {
         document.querySelector('.main-content').innerHTML =
            '<h2>Lỗi truy cập ⛔</h2><p>Bạn không có quyền truy cập trang này.</p><a href="index.html">Về trang chủ</a>';
        return; // Dừng thực thi nếu không phải admin
    }

    const platformList = document.getElementById('platform-list');
    const form = document.getElementById('new-platform-form');

    // --- Hàm gọi API chung ---
    async function fetchAPI(url, options = {}) {
        /* ... (copy hàm fetchAPI từ chat.js) ... */
        const defaultOptions = { /*...*/ }; /*...*/
        try { /*...*/ } catch (error) { /*...*/ }
    }

    // --- Tải danh sách platform ---
    async function loadPlatforms() {
        platformList.innerHTML = 'Đang tải...';
        try {
            // *** API LẤY PLATFORMS: /platforms/ (GET) ***
            const platforms = await fetchAPI('/platforms/'); // Sử dụng endpoint từ backend
            platformList.innerHTML = '';
            if (platforms && Array.isArray(platforms) && platforms.length > 0) { // Expects [{id, name, url, logo_url}]
                platforms.forEach(p => {
                    platformList.innerHTML += `
                        <div style="border: 1px solid #ddd; padding: 15px; border-radius: 8px; text-align: center;">
                            <img src="${p.logo_url || 'Image/iconSearch.png'}" alt="${p.name}" style="width: 40px; height: 40px; object-fit: contain; margin-bottom: 10px;">
                            <strong style="display: block; margin-bottom: 5px;">${p.name}</strong>
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
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const nameInput = document.getElementById('platform-name');
        const urlInput = document.getElementById('platform-url');
        const logoInput = document.getElementById('platform-logo');

        const newPlatform = {
            name: nameInput.value.trim(),
            url: urlInput.value.trim(),
            logo_url: logoInput.value.trim() || null // Gửi null nếu trống
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

    // Khởi chạy
    await loadPlatforms();
});