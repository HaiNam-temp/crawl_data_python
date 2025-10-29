// js/search.js
document.addEventListener('DOMContentLoaded', async () => {
    const token = localStorage.getItem('token');
    if (!token) return; // Auth.js nên xử lý

    const searchInput = document.getElementById('search-input');
    const resultsGrid = document.getElementById('results-grid');
    const initialMessage = document.getElementById('initial-message');

    // --- Hàm gọi API chung ---
    async function fetchAPI(url, options = {}) {
        /* ... (copy hàm fetchAPI từ chat.js) ... */
        const defaultOptions = { /*...*/ }; /*...*/
        try { /*...*/ } catch (error) { /*...*/ }
    }

    // --- Hàm tìm kiếm (API) ---
    async function performSearch(query) {
        if (initialMessage) initialMessage.style.display = 'none';
        resultsGrid.innerHTML = '<p>Đang tìm kiếm...</p>';
        query = query.trim();
        if (!query) {
            resultsGrid.innerHTML = '';
            if(initialMessage) initialMessage.style.display = 'block';
            return;
        }

        try {
            // *** API SEARCH: /search/?q=... (GET) ***
            const results = await fetchAPI(`/search/?q=${encodeURIComponent(query)}`); // Sử dụng endpoint từ backend
            displayProducts(results); // Expects List[ProductSchema]
        } catch(error){
             resultsGrid.innerHTML = `<p style="color: red;">Lỗi khi tìm kiếm: ${error.message}</p>`;
        }
    }

    // --- Hàm hiển thị ---
    function displayProducts(products) {
        resultsGrid.innerHTML = ''; // Xóa thông báo loading/lỗi cũ
        if (!products || !Array.isArray(products) || products.length === 0) {
            resultsGrid.innerHTML = '<p>Không tìm thấy sản phẩm nào khớp với tìm kiếm của bạn.</p>';
            return;
        }

        // Hardcode logo URLs hoặc lấy từ API /platforms/ nếu cần
        const vendorLogos = {
            tiki: "https://salt.tikicdn.com/ts/upload/e4/49/6c/270be9859abd5f5ec5071da65fab0a94.png",
            shopee: "https://deo.shopeemobile.com/shopee/shopee-pcmall-live-sg/assets/6c502a2641457578b0d5f5153b53dd5d.png",
            // Thêm các vendor khác nếu có
        };

        products.forEach(product => {
             // Validate data (optional but recommended)
             const name = product.name || 'N/A';
             const price = typeof product.price === 'number' ? product.price.toLocaleString('vi-VN') + ' ₫' : 'N/A';
             const image = product.image || 'Image/iconSearch.png'; // Placeholder
             const vendor = product.vendor || 'N/A';
             const link = product.link || '#';
             const bestDeal = product.bestDeal || false;

             resultsGrid.innerHTML += `
                <div class="st-container">
                    ${bestDeal ? '<span style="color: green; font-weight: bold; display: block; margin-bottom: 5px;">⭐ Rẻ nhất!</span>' : ''}
                    <img src="${image}" alt="${name}" loading="lazy">
                    <h4>${name}</h4>
                    <img src="${vendorLogos[vendor] || ''}" alt="${vendor}" class="vendor-logo">
                    <span style="font-size: 0.9rem; text-transform: capitalize;">${vendor}</span>
                    <p style="font-size: 1.25rem; font-weight: bold; color: var(--primary-color); margin-top: 5px;">
                        ${price}
                    </p>
                    <a href="${link}" target="_blank" class="btn" style="width: 100%; text-align: center; margin-top: 10px;">Đến nơi bán</a>
                </div>
            `;
        });
    }

    // --- Gán sự kiện ---
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            performSearch(searchInput.value);
        }
    });
    // Optional: Thêm nút search hoặc tìm khi gõ xong
});