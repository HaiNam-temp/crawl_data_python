import sqlite3
import hashlib

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

conn = sqlite3.connect('chatbot_database.db')
cursor = conn.cursor()

# Cập nhật tài khoản admin hiện tại
admin_password_hash = hash_password("admin")
cursor.execute('''
    UPDATE users 
    SET is_admin = 1, 
        password_hash = ?,
        email = 'admin@example.com'
    WHERE username = 'admin'
''', (admin_password_hash,))

conn.commit()

# Kiểm tra lại
cursor.execute('SELECT username, email, is_admin FROM users WHERE username = ?', ('admin',))
result = cursor.fetchone()

print('✅ Đã cập nhật tài khoản admin:')
print(f'   Username: {result[0]}')
print(f'   Email: {result[1]}')
print(f'   is_admin: {result[2]} (1 = Admin)')
print(f'   Password: admin')

conn.close()
