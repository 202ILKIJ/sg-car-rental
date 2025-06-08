import sqlite3

def inspect_users():
    try:
        conn = sqlite3.connect('car_rental.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        print("=== Users Table ===")
        for row in rows:
            print(row)
        conn.close()
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    inspect_users()
