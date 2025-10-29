import sqlite3

conn = sqlite3.connect('chatbot_database.db')
cursor = conn.cursor()

# Kiểm tra tài khoản admin
cursor.execute('SELECT username, email, is_admin, created_at FROM users WHERE username = ?', ('admin',))
result = cursor.fetchone()

if result:
    print('✅ Tài khoản admin ĐÃ TỒN TẠI:')
    print(f'   Username: {result[0]}')
    print(f'   Email: {result[1]}')
    print(f'   is_admin: {result[2]}')
    print(f'   created_at: {result[3]}')
else:
    print('❌ Tài khoản admin CHƯA TỒN TẠI')
    print('Server sẽ tự động tạo khi khởi động lần đầu')

# Liệt kê tất cả users
cursor.execute('SELECT username, is_admin FROM users')
all_users = cursor.fetchall()
print(f'\n📋 Tất cả users trong database ({len(all_users)}):\n')
for user in all_users:
    role = '👑 Admin' if user[1] else '👤 User'
    print(f'   - {user[0]}: {role}')

conn.close()
