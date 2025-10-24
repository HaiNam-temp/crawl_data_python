import streamlit as st
from data import search_products, vendorLogos # Import hàm và dữ liệu từ data.py

# --- Giao diện (Tương đương Header trong index.html) ---
st.title("PriceComp / So Sánh Giá")
st.write("Tìm kiếm sản phẩm, so sánh giá từ Shopee, Tiki, Lazada.")

# --- Thanh tìm kiếm (Tương đương search-container) ---
# `st.text_input` tạo ra một ô nhập liệu
query = st.text_input("Nhập tên sản phẩm bạn muốn tìm...", placeholder="Ví dụ: iPhone 15")

st.divider() # Thêm một đường kẻ ngang

# --- Khu vực kết quả (Tương đương results-grid) ---
if query:
    # 1. Gọi hàm tìm kiếm
    results = search_products(query)
    
    if not results:
        st.warning("Không tìm thấy sản phẩm nào.")
    else:
        # 2. Hiển thị kết quả
        # `st.columns(3)` tạo ra một lưới 3 cột
        cols = st.columns(3) 
        
        for i, product in enumerate(results):
            # `with cols[i % 3]:` -> chia sản phẩm vào 3 cột
            with cols[i % 3]:
                
                # `st.container()` tạo ra một "card"
                with st.container(border=True):
                    if product.get("bestDeal"):
                        st.success("Rẻ nhất!") # Tương đương best-deal-badge
                    
                    st.image(product["image"], use_column_width=True)
                    st.subheader(product["name"])
                    
                    # Hiển thị logo và tên vendor
                    st.image(vendorLogos[product["vendor"]], width=20)
                    st.caption(f"Nguồn: {product['vendor'].capitalize()}")
                    
                    # `st.metric` rất hợp để hiển thị giá
                    st.metric(label="Giá", value=f"{product['price']:,} ₫")
                    
                    # `st.link_button` tạo ra thẻ <a>
                    st.link_button("Đến nơi bán", product["link"], use_container_width=True)

else:
    # Tương đương initial-message
    st.info("Nhập từ khóa vào ô tìm kiếm để bắt đầu nhé! 🤖")