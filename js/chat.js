// js/chat.js
document.addEventListener('DOMContentLoaded', async () => {
    const token = localStorage.getItem('token');
    if (!token) return;

    const historyList = document.getElementById('chat-history-list');
    const messagesContainer = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('chat-send-btn');
    const newChatBtn = document.getElementById('new-chat-btn');

    let currentChatId = localStorage.getItem('current_chat_id') ? parseInt(localStorage.getItem('current_chat_id'), 10) : null;

    // --- Hàm gọi API chung ---
    async function fetchAPI(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            }
        };
        const mergedOptions = { ...defaultOptions, ...options };
        // Đảm bảo headers được merge đúng cách
        mergedOptions.headers = { ...defaultOptions.headers, ...(options.headers || {}) };
         // Xóa Content-Type cho GET hoặc khi không có body
         if (!mergedOptions.body && mergedOptions.method !== 'POST' && mergedOptions.method !== 'PUT' && mergedOptions.method !== 'PATCH') {
             delete mergedOptions.headers['Content-Type'];
         }

        try {
            const response = await fetch(url, mergedOptions);
            if (!response.ok) {
                if (response.status === 401) { logoutUser(); } // Gọi hàm logout từ global.js
                const errorText = await response.text();
                console.error("API Error:", response.status, errorText);
                throw new Error(`API Error ${response.status}: ${errorText || response.statusText}`); // Throw error để catch xử lý
            }
             if (response.headers.get("content-length") === "0" || response.status === 204) {
                 return {}; // Trả về object rỗng cho No Content
             }
            return await response.json();
        } catch (error) {
            console.error("Fetch Error:", error);
            throw error; // Re-throw để hàm gọi xử lý
        }
    }

    // --- Hàm tải lịch sử chat ---
    async function loadChatHistory() {
        historyList.innerHTML = 'Đang tải...';
        try {
            // *** API LẤY CONVERSATIONS: /conversations/ (GET) ***
            const conversations = await fetchAPI('/conversations/');
            historyList.innerHTML = '';
            if (conversations && Array.isArray(conversations) && conversations.length > 0) {
                conversations.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp)); // Sắp xếp theo timestamp từ API
                conversations.forEach(conv => {
                    const item = document.createElement('div');
                    item.className = 'chat-history-item';
                    item.textContent = conv.title;
                    item.dataset.chatId = conv.id;
                    if (conv.id === currentChatId) item.classList.add('active');

                    item.addEventListener('click', () => {
                         if (currentChatId === conv.id) return; // Không làm gì nếu click vào chat đang active
                        currentChatId = conv.id;
                        localStorage.setItem('current_chat_id', currentChatId);
                        loadChatMessages(); // Tải messages mới
                        // Cập nhật active class
                        document.querySelectorAll('.chat-history-item').forEach(el => el.classList.remove('active'));
                        item.classList.add('active');
                    });
                    historyList.appendChild(item);
                });
            } else {
                 historyList.innerHTML = '<p style="font-size: 0.9em; color: #888;">Chưa có trò chuyện nào.</p>';
            }
        } catch (error) {
            historyList.innerHTML = '<p style="font-size: 0.9em; color: red;">Lỗi tải lịch sử.</p>';
        }
    }

    // --- Hàm tải tin nhắn ---
    async function loadChatMessages() {
        messagesContainer.innerHTML = '';
        if (currentChatId) {
            messagesContainer.innerHTML = '<div class="message bot"><div class="text">Đang tải tin nhắn...</div></div>';
            try {
                // *** API LẤY MESSAGES: /conversations/{id}/messages (GET) ***
                const messages = await fetchAPI(`/conversations/${currentChatId}/messages`);
                messagesContainer.innerHTML = '';
                if (messages && Array.isArray(messages)) {
                    messages.forEach(msg => addMessageToUI(msg.role, msg.content));
                } else {
                    addMessageToUI('bot', 'Chưa có tin nhắn nào.');
                }
            } catch (error) {
                 messagesContainer.innerHTML = '';
                 addMessageToUI('bot', 'Lỗi tải tin nhắn.');
            }
        } else {
            addMessageToUI('bot', 'Xin chào! Bạn muốn tìm sản phẩm nào hôm nay?');
        }
        // Cuộn xuống cuối sau khi render
        setTimeout(() => { messagesContainer.scrollTop = messagesContainer.scrollHeight; }, 0);
    }

     // --- Hàm thêm tin nhắn vào UI ---
    function addMessageToUI(role, content) {
        const formattedContent = content.replace(/\n/g, '<br>');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        messageDiv.innerHTML = `<div class="text">${formattedContent}</div>`;
        messagesContainer.appendChild(messageDiv);
        // Cuộn xuống cuối
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }


    // --- Hàm Gửi tin nhắn ---
    async function sendMessage() {
        const userText = chatInput.value.trim();
        if (userText === '') return;

        const originalChatId = currentChatId; // Lưu lại ID trước khi gửi
        addMessageToUI('user', userText); // Hiển thị ngay
        chatInput.value = '';
        chatInput.disabled = true;
        sendBtn.disabled = true;

        let tempChatId = currentChatId;
        let isNewChat = false;

        try {
             if (tempChatId === null) {
                 isNewChat = true;
                 messagesContainer.innerHTML = ''; // Xóa chào mừng
                 addMessageToUI('user', userText); // Hiển thị lại user msg
                 const title = userText.length > 30 ? userText.substring(0, 30) + '...' : userText;
                 // *** API TẠO CONVERSATION MỚI: /conversations/ (POST) ***
                 const newConvData = await fetchAPI('/conversations/', {
                     method: 'POST',
                     body: JSON.stringify({ title: title }) // Backend cần schema ConversationCreate(title: str)
                 });
                 if (newConvData && newConvData.id) {
                     tempChatId = newConvData.id;
                     currentChatId = tempChatId;
                     localStorage.setItem('current_chat_id', currentChatId);
                     // Không load lại history ngay, để tránh nháy màn hình, chỉ thêm vào UI
                     const newItem = document.createElement('div');
                     newItem.className = 'chat-history-item active'; // Thêm active ngay
                     newItem.textContent = newConvData.title;
                     newItem.dataset.chatId = newConvData.id;
                      newItem.addEventListener('click', () => { /* ... (gắn listener như trong loadChatHistory) ... */ });
                     // Xóa thông báo "chưa có" nếu có
                      const noHistoryMsg = historyList.querySelector('p');
                      if (noHistoryMsg) noHistoryMsg.remove();
                     // Thêm vào đầu danh sách
                     historyList.insertBefore(newItem, historyList.firstChild);
                      // Bỏ active của item cũ (nếu có)
                      document.querySelectorAll('.chat-history-item:not([data-chat-id="'+newItem.dataset.chatId+'"])')
                          .forEach(el => el.classList.remove('active'));

                 } else { throw new Error("Không thể tạo cuộc trò chuyện mới."); }
             }

             // *** API GỬI MESSAGE & NHẬN PHẢN HỒI: /conversations/{id}/chat (POST) ***
             const botResponseData = await fetchAPI(`/conversations/${tempChatId}/chat`, {
                 method: 'POST',
                 body: JSON.stringify({ role: 'user', content: userText }) // Gửi tin nhắn user
             });

             if (botResponseData && botResponseData.content && botResponseData.role === 'assistant') { // API trả về tin nhắn bot { role: 'assistant', content: '...' }
                 addMessageToUI('bot', botResponseData.content);
             } else {
                  console.warn("API did not return expected bot response.", botResponseData);
                  addMessageToUI('bot', 'Lỗi khi nhận phản hồi từ Bot.');
             }

        } catch (error) {
            console.error("Send message error:", error);
            addMessageToUI('bot', `Đã xảy ra lỗi: ${error.message}`);
            // Rollback nếu tạo chat mới thất bại
            if (isNewChat && currentChatId !== originalChatId) {
                localStorage.removeItem('current_chat_id');
                currentChatId = null;
                // Xóa item mới thêm khỏi UI
                 const failedItem = historyList.querySelector(`[data-chat-id="${tempChatId}"]`);
                 if (failedItem) failedItem.remove();
                 // Load lại state cũ (tin nhắn chào mừng)
                 loadChatMessages();
            }
        } finally {
             chatInput.disabled = false;
             sendBtn.disabled = false;
             chatInput.focus();
        }
    }

    // --- Nút Chat mới ---
    newChatBtn.addEventListener('click', () => {
        if (currentChatId === null) return; // Đã là chat mới rồi
        currentChatId = null;
        localStorage.removeItem('current_chat_id');
        loadChatMessages();
        document.querySelectorAll('.chat-history-item').forEach(el => el.classList.remove('active'));
    });

    // --- Gán sự kiện ---
    sendBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') sendMessage(); });

    // --- Khởi chạy ---
    await loadChatHistory();
    await loadChatMessages();
});