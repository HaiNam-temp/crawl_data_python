"""
Simple HTTP Server to serve frontend files
Run this in a separate terminal while main.py (backend) is running
"""
import http.server
import socketserver
import os

PORT = 3000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print("=" * 60)
        print(f"🌐 Frontend Server đang chạy tại: http://localhost:{PORT}")
        print("=" * 60)
        print(f"📱 Mở các trang sau:")
        print(f"   - Đăng nhập:  http://localhost:{PORT}/login.html")
        print(f"   - Trang chủ:  http://localhost:{PORT}/index.html")
        print(f"   - Chat AI:    http://localhost:{PORT}/chat.html")
        print(f"   - Tìm kiếm:   http://localhost:{PORT}/search.html")
        print(f"   - Admin:      http://localhost:{PORT}/admin.html")
        print("=" * 60)
        print("✅ Backend API: http://localhost:8010")
        print("📚 API Docs:    http://localhost:8010/docs")
        print("=" * 60)
        print("Nhấn Ctrl+C để dừng server")
        print()
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n🛑 Server đã dừng!")
