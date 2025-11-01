// js/search.js
document.addEventListener('DOMContentLoaded', async () => {
    // Allow anonymous searches by default. If a token exists we'll send it
    // in the Authorization header inside fetchAPI; don't block the UI here.
    const token = localStorage.getItem('token');

    const searchInput = document.getElementById('search-input');
    const resultsGrid = document.getElementById('results-grid');
    const initialMessage = document.getElementById('initial-message');

    // --- Hàm gọi API chung ---
    async function fetchAPI(url, options = {}) {
        // Generic fetch helper with Authorization header and JSON handling
        const token = localStorage.getItem('token');
        const defaultOptions = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        };

        const opts = Object.assign({}, defaultOptions, options || {});

        // Add Authorization header when token is available
        if (token) {
            opts.headers = Object.assign({}, opts.headers, {
                Authorization: `Bearer ${token}`
            });
        }

        try {
            const resp = await fetch(url, opts);
            if (resp.status === 401) {
                // Unauthorized - token invalid/expired
                localStorage.removeItem('token');
                throw new Error('Unauthorized. Please login again.');
            }
            const text = await resp.text();
            // Try parse JSON, fallback to raw text
            try {
                return text ? JSON.parse(text) : null;
            } catch (e) {
                return text;
            }
        } catch (error) {
            console.error('API fetch error:', error);
            throw error;
        }
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
                const BACKEND = 'http://localhost:8010';
                const results = await fetchAPI(`${BACKEND}/search?q=${encodeURIComponent(query)}`); // Sử dụng endpoint từ backend
            displayProducts(results); 
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

        // Note: vendor/logo removed — we only show name, price and link to seller.

        products.forEach(product => {
             // Validate data (optional but recommended)
             const name = product.name || '';
             const price = typeof product.price === 'number' ? product.price.toLocaleString('vi-VN') + ' ₫' : (product.price || 'N/A');
             // vendor field intentionally ignored — don't display logo/caption to keep UI clean
             const link = product.url || product.link || '#';
             const bestDeal = product.bestDeal || false;

             // Render product card WITHOUT product image to save space and avoid layout issues.
             // Ensure price has bottom margin and the button sits below it to avoid overlap.
             resultsGrid.innerHTML += `
                <div class="st-container" style="padding: 12px; box-sizing: border-box;">
                    ${bestDeal ? '<span style="color: green; font-weight: bold; display: block; margin-bottom: 5px;">⭐ Rẻ nhất!</span>' : ''}
                    <h4 style="margin: 8px 0 6px 0;">${name}</h4>
                    <!-- vendor/logo intentionally omitted -->
                    <p style="font-size: 1.25rem; font-weight: bold; color: var(--primary-color); margin: 6px 0 12px 0;">
                        ${price}
                    </p>
                    <div style="clear:both;">
                        <a href="${link}" target="_blank" class="btn" style="display:block; width: 100%; text-align: center; margin-top: 6px; padding: 10px 8px; box-sizing: border-box;">Đến nơi bán</a>
                    </div>
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
    // Add a search button for users who prefer clicking
    let searchButton = document.getElementById('search-button');
    if (!searchButton) {
        searchButton = document.createElement('button');
        searchButton.id = 'search-button';
        searchButton.textContent = 'Tìm';
        searchButton.className = 'btn';
        searchButton.style.marginLeft = '8px';
        searchInput.insertAdjacentElement('afterend', searchButton);
    }
    searchButton.addEventListener('click', () => performSearch(searchInput.value));
    // Optional: Thêm nút search hoặc tìm khi gõ xong
});