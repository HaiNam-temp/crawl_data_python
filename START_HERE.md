# 🚀 Hướng dẫn khởi chạy PriceComp - Sophie Chatbot

## ✅ Đã hoàn thành
- ✅ Backend API (FastAPI) - Port 8010
- ✅ Frontend (HTML/CSS/JS)
- ✅ Database SQLite
- ✅ Chatbot integration
- ✅ Authentication & Authorization

## 📋 Cách chạy ứng dụng

### Bước 1: Khởi động Backend Server
```powershell
# Đang chạy tại terminal uvicorn
python main.py
```
Server đang chạy tại: **http://localhost:8010**

### Bước 2: Mở Frontend
Mở file HTML trực tiếp trong trình duyệt:

**Cách 1: Click đúp vào file**
- Mở file `login.html` bằng trình duyệt (Chrome, Edge, Firefox)

**Cách 2: Dùng Live Server (Khuyến nghị)**
```powershell
# Cài đặt http-server nếu chưa có
npm install -g http-server

# Chạy từ thư mục gốc
http-server -p 3000
```
Sau đó truy cập: **http://localhost:3000/login.html**

**Cách 3: Dùng Python HTTP Server**
```powershell
# Mở terminal mới (không phải terminal đang chạy uvicorn)
python -m http.server 3000
```
Sau đó truy cập: **http://localhost:3000/login.html**

## 🔐 Tạo tài khoản đầu tiên

1. Truy cập **login.html**
2. Chuyển sang tab **"Đăng ký"**
3. Nhập:
   - Tên đăng nhập: `admin`
   - Email: `admin@example.com`
   - Mật khẩu: `admin123`
   - Xác nhận mật khẩu: `admin123`
4. Click **"Đăng ký"**
5. Chuyển sang tab **"Đăng nhập"** và đăng nhập

## 📁 Các trang có sẵn

- **login.html** - Đăng nhập/Đăng ký
- **index.html** - Trang chủ
- **chat.html** - Chat với Sophie AI
- **search.html** - Tìm kiếm sản phẩm
- **admin.html** - Quản lý platforms (Admin only)
- **setting.html** - Cài đặt

## 🔧 Cấu hình đã sẵn sàng

### Backend API Endpoints:
- `POST /token` - Đăng nhập
- `POST /users/` - Đăng ký
- `GET /users/me` - Lấy thông tin user
- `GET /conversations/` - Danh sách conversations
- `POST /conversations/` - Tạo conversation mới
- `GET /conversations/{id}/messages` - Lấy tin nhắn
- `POST /conversations/{id}/chat` - Gửi tin nhắn
- `GET /platforms/` - Danh sách platforms
- `POST /platforms/` - Thêm platform (admin)

### Frontend đã kết nối:
- ✅ `js/login.js` → Backend Auth
- ✅ `js/chat.js` → Backend Chat API
- ✅ `js/global.js` → User info & Sidebar
- ✅ `js/admin.js` → Platform management

## 🎯 Luồng sử dụng

1. **Đăng ký/Đăng nhập** (login.html)
2. **Trang chủ** (index.html) - Xem tổng quan
3. **Chat với AI** (chat.html) - Hỏi về sản phẩm, so sánh giá
4. **Tìm kiếm** (search.html) - Tìm sản phẩm cụ thể
5. **Admin** (admin.html) - Quản lý platforms nếu là admin

## 🐛 Xử lý lỗi thường gặp

### Lỗi CORS
Nếu gặp lỗi CORS khi fetch API:
- ✅ Backend đã cấu hình CORS middleware
- Đảm bảo backend đang chạy trên port 8010
- JS files đã được cập nhật với URL: `http://localhost:8010`

### Lỗi 401 Unauthorized
- Token hết hạn → Đăng nhập lại
- Token không hợp lệ → Xóa localStorage và đăng nhập lại

### Database không tạo
- File `chatbot_database.db` đã được tạo tự động
- Nếu thiếu, chạy lại `python main.py`

## 📦 Dependencies cần thiết

Đã có trong `requirements.txt`:
```
fastapi
uvicorn
pydantic
python-dotenv
PyJWT
python-multipart
sqlite3 (built-in)
```

Cài thêm nếu thiếu:
```powershell
pip install PyJWT python-multipart
```

## 🎉 Hoàn thành!

Backend và Frontend đã được kết nối hoàn chỉnh. Bạn có thể:
- ✅ Đăng ký/Đăng nhập
- ✅ Chat với Sophie AI
- ✅ Tìm kiếm sản phẩm từ Tiki
- ✅ So sánh giá sản phẩm
- ✅ Quản lý conversations
- ✅ Admin quản lý platforms

## 📞 API Documentation

Sau khi chạy server, truy cập:
- **Swagger UI**: http://localhost:8010/docs
- **ReDoc**: http://localhost:8010/redoc
