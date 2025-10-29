import streamlit as st

# Cấu hình cơ bản cho toàn bộ ứng dụng
st.set_page_config(
    page_title="PriceComp",
    page_icon="Image/iconChat.png", # Icon trên tab trình duyệt
    layout="wide"
)


st.title("Chào mừng đến với PriceComp")
st.markdown(
    "Đây là dự án demo một ứng dụng so sánh giá"
)
st.markdown(
    "Vui lòng sử dụng thanh điều hướng (sidebar) bên trái để truy cập các chức năng chính của web."
)

st.sidebar.success("Vui lòng chọn một trang ở trên để bắt đầu.")

st.divider() # Thêm một đường kẻ ngang

# Sử dụng st.columns để chia bố cục cho đẹp mắt
col1, col2 = st.columns(2)

with col1:

    icon_col, title_col = st.columns([0.15, 0.85], gap="small")
    with icon_col:
        # Sử dụng đường dẫn ảnh mới của bạn
        st.image("Image/iconSearch.png") 
    with title_col:
        st.subheader("Trang chủ Tìm kiếm")

    st.markdown(
        """
        Đây là trang tìm kiếm sản phẩm chính.
        
        - **Cách dùng:** Gõ tên sản phẩm (ví dụ: 'Iphone 17 ProMax') vào ô tìm kiếm và nhấn Enter.
        - **Kết quả:** Các sản phẩm tìm thấy sẽ được hiển thị dưới dạng lưới, kèm giá và link sản phẩm.
        """
    )

with col2:
    # --- CŨNG ĐƯỢC CẬP NHẬT CHO ĐỒNG BỘ ---
    # Tạo 2 cột con: 1 cho icon, 1 cho tiêu đề
    icon_col, title_col = st.columns([0.15, 0.85], gap="small")
    with icon_col:
        # Sử dụng icon chat bạn đã cung cấp trước đó
        st.image("Image/iconChat.png") 
    with title_col:
        st.subheader("Trợ lý Chatbot")

    st.markdown(
        """
        Đây là giao diện chatbot thông minh.
        
        - **Cách dùng:** Bạn có thể hỏi bằng ngôn ngữ tự nhiên (ví dụ: 'tìm giúp tôi tai nghe baseus').
        - **Tính năng đặc biệt:** Lịch sử trò chuyện của bạn sẽ được **lưu vĩnh viễn**.
        """
    )

st.info(
    "💡 **Mẹo:** Bạn có thể F5 (tải lại) trang Chatbot, cuộc hội thoại vẫn sẽ được giữ nguyên!"
)