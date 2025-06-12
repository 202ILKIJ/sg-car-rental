from flask import Flask, request, redirect, render_template, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'insecure_secret_key'  # ⚠️ For demo only


# --- Helper function for DB connection ---
def get_db_connection():
    conn = sqlite3.connect('car_rental.db')
    conn.row_factory = sqlite3.Row
    return conn


# Dummy car list
car_list = [
    {"id": 1, "name": "Toyota Camry"},
    {"id": 2, "name": "Honda Civic"},
    {"id": 3, "name": "Ford Mustang"},
    {"id": 4, "name": "BMW 3 Series"},
    {"id": 5, "name": "Tesla Model 3"},
    {"id": 6, "name": "Mazda CX-5"}
]

# --- Temporary table setup ---
with get_db_connection() as conn:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            car TEXT,
            user TEXT,
            date TEXT
        )
    """)
    conn.commit()


@app.route('/')
def home():
    return redirect('/login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['username'] = username
            return redirect('/cars')
        else:
            msg = "Invalid credentials"

    return render_template('login.html', msg=msg)


@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_pw = generate_password_hash(password)

        try:
            conn = get_db_connection()
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))
            conn.commit()
            conn.close()
            msg = "Registration successful. You can now log in."
        except:
            msg = "Registration failed. User may already exist."

    return render_template('register.html', msg=msg)


@app.route('/cars')
def cars():
    if 'username' not in session:
        return redirect('/login')

    search = request.args.get('search', '')
    filtered = [c for c in car_list if search.lower() in c['name'].lower()]
    return render_template('cars.html', cars=filtered)


@app.route('/book/<int:car_id>', methods=['GET', 'POST'])
def book(car_id):
    if 'username' not in session:
        return redirect('/login')

    car = next((c for c in car_list if c["id"] == car_id), None)
    if not car:
        return "Car not found"

    if request.method == 'POST':
        booking_date = request.form['date']
        conn = get_db_connection()
        conn.execute("INSERT INTO bookings (car, user, date) VALUES (?, ?, ?)",
                     (car["name"], session['username'], booking_date))
        conn.commit()
        conn.close()
        return render_template("booking_confirmation.html", car=car["name"], date=booking_date)

    return render_template('book.html', car=car)


@app.route('/my_bookings')
def my_bookings():
    if 'username' not in session:
        return redirect('/login')

    conn = get_db_connection()
    cursor = conn.execute("SELECT car, date FROM bookings WHERE user = ?", (session['username'],))
    bookings = cursor.fetchall()
    conn.close()
    return render_template('my_bookings.html', bookings=bookings)


@app.route('/admin_dashboard')
def admin_dashboard():
    if 'username' not in session or session['username'] != 'admin':
        return redirect('/login')

    conn = get_db_connection()
    stats = conn.execute("SELECT car, COUNT(*) as count FROM bookings GROUP BY car").fetchall()
    conn.close()
    return render_template('admin_dashboard.html', stats=stats)


@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    msg = ''
    if request.method == 'POST':
        comment = request.form['comment']
        msg = comment  # Rendered with autoescape ON
    return render_template('feedback.html', msg=msg)


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
