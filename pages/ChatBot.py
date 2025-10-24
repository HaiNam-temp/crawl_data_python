import datetime
import streamlit as st
import sqlite3
from data import search_products # Bot cũng cần biết tìm kiếm
from logger_config import get_logger

logger = get_logger(__name__)
from logger_config import get_logger


logger = get_logger(__name__)

# --- 1. THIẾT LẬP CƠ SỞ DỮ LIỆU (SQLITE) ---

DB_FILE = "chat_history.db"

def get_db_connection():
    """Tạo và trả về một kết nối đến DB SQLite."""
    conn = sqlite3.connect(DB_FILE)
    # Cài đặt này để kết quả trả về có thể truy cập bằng tên cột (như dict)
    conn.row_factory = sqlite3.Row 
    return conn

def init_db():
    """Khởi tạo CSDL và bảng 'messages' nếu nó chưa tồn tại."""
    conn = get_db_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
    finally:
        conn.close()

def load_messages_from_db():
    """Tải tất cả tin nhắn từ CSDL, sắp xếp theo thời gian."""
    conn = get_db_connection()
    try:
        cursor = conn.execute("SELECT role, content FROM messages ORDER BY timestamp ASC")
        # Chuyển đổi kết quả (sqlite3.Row) thành list[dict] chuẩn
        messages = [{"role": row["role"], "content": row["content"]} for row in cursor.fetchall()]
        
        # Nếu không có tin nhắn nào, thêm tin nhắn chào mừng
        if not messages:
            messages.append(
                {"role": "assistant", "content": "Xin chào! Tôi là Trợ lý So Sánh Giá. Bạn cần tìm sản phẩm nào?"}
            )
        return messages
    finally:
        conn.close()

def save_message_to_db(role, content):
    """Lưu một tin nhắn mới (của user hoặc assistant) vào CSDL."""
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO messages (role, content) VALUES (?, ?)",
            (role, content)
        )
        conn.commit()
    finally:
        conn.close()

# --- 2. LOGIC CỦA BOT (Giữ nguyên) ---

def generate_bot_response(user_input):
    logger.info(f"User query: {user_input}")
    try:
        from chatbot import process_user_query

        # process_user_query returns a string response ready to show in UI
        return process_user_query(user_input)
    except Exception:
        # Fallback: simple local heuristic bot when the full chatbot isn't
        # available (e.g., missing dependencies in the environment).
        query = user_input.lower()
        bot_reply = "Xin lỗi, tôi chưa hiểu ý bạn. Bạn có thể hỏi cụ thể hơn về tên sản phẩm được không?"

        if "iphone 15" in query:
            products = search_products("iphone 15")
            if products:
                bot_reply = "Tôi tìm thấy các sản phẩm iPhone 15 sau:\n\n"
                for p in products:
                    bot_reply += f"- {p['name']} tại {p['vendor']}\n  Giá: {p['price']:,} ₫\n\n"
            else:
                bot_reply = "Rất tiếc, tôi không tìm thấy sản phẩm iPhone 15 nào."

        elif "tai nghe" in query or "baseus" in query:
            products = search_products("baseus")
            if products:
                bot_reply = "Tôi tìm thấy các tai nghe Baseus sau:\n\n"
                for p in products:
                    bot_reply += f"- {p['name']} tại {p['vendor']}\n  Giá: {p['price']:,} ₫\n\n"
            else:
                bot_reply = "Rất tiếc, tôi không tìm thấy tai nghe Baseus nào."

        elif "chào" in query or "hello" in query:
            bot_reply = "Chào bạn, tôi là Trợ lý Giá cả. Bạn cần tìm gì nào?"

        return bot_reply

# --- 3. GIAO DIỆN CHAT STREAMLIT ---

# Khởi tạo CSDL ngay khi bắt đầu
init_db()

# --- Quản lý Lịch sử Chat ---
# Chỉ tải từ DB 1 LẦN DUY NHẤT khi session_state "messages" chưa tồn tại
# (Tức là khi người dùng mới mở tab)
if "messages" not in st.session_state:
    st.session_state.messages = load_messages_from_db()

# --- Thiết lập tiêu đề trang ---
st.title("Trợ lý So Sánh Giá 💬")

# --- Hiển thị các tin nhắn cũ ---
# Luôn hiển thị từ session_state (vì nó đã được tải từ DB)
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Khung nhập liệu (Xử lý tin nhắn mới) ---
if prompt := st.chat_input("Nhập câu hỏi của bạn..."):
    # 1. Thêm tin nhắn USER vào session_state (để hiển thị) và DB (để lưu)
    logger.info("Received prompt from user: %r", prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    save_message_to_db("user", prompt)
    
    # Hiển thị tin nhắn user ngay lập tức
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Tạo và hiển thị phản hồi của BOT
    # (Thêm hiệu ứng "Đang suy nghĩ..." cho chuyên nghiệp)
    with st.chat_message("assistant"):
        with st.spinner("Đang suy nghĩ..."):
            try:
                bot_response = generate_bot_response(prompt)
                logger.info("Bot response generated (len=%d)", len(bot_response) if bot_response else 0)
            except Exception as e:
                logger.error("Error generating bot response: %s", str(e))
                bot_response = "Xin lỗi, đã có lỗi khi tạo phản hồi."
        st.markdown(bot_response)
    
    # 3. Thêm tin nhắn BOT vào session_state (để hiển thị) và DB (để lưu)
    st.session_state.messages.append({"role": "assistant", "content": bot_response})
    save_message_to_db("assistant", bot_response)