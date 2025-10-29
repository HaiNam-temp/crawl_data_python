// js/auth.js
(function() {
    const token = localStorage.getItem('token');
    const currentPage = window.location.pathname.split('/').pop();

    if (!token) {
        // Nếu không có token và không phải trang login, chuyển hướng về login
        if (currentPage !== 'login.html') {
            console.log("No token found, redirecting to login.");
            window.location.href = 'login.html';
        }
    } else {
        // Nếu có token và đang ở trang login, chuyển hướng vào trang chủ
        if (currentPage === 'login.html') {
            console.log("Token found, redirecting to index.");
            window.location.href = 'index.html'; // Chuyển đến trang chủ index.html
        }
    }
})();