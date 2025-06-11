from werkzeug.security import generate_password_hash
import sqlite3

conn = sqlite3.connect('car_rental.db')
cursor = conn.cursor()

hashed_pw = generate_password_hash('admin123')
cursor.execute("UPDATE users SET password = ? WHERE username = 'admin'", (hashed_pw,))
conn.commit()
conn.close()