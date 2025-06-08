from flask import Flask, request, redirect, render_template, session
from markupsafe import escape
import sqlite3


app = Flask(__name__)
app.secret_key = 'insecure_secret_key'  # ⚠️ Insecure on purpose for CW2

# Setup database
conn = sqlite3.connect('car_rental.db', check_same_thread=False)
cursor = conn.cursor()

# Add this line temporarily:
#cursor.execute("ALTER TABLE bookings ADD COLUMN date TEXT")

# Your existing table creation lines...
cursor.execute("CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS bookings (id INTEGER PRIMARY KEY AUTOINCREMENT, car TEXT, user TEXT)")
#conn.execute("INSERT OR IGNORE INTO users VALUES ('admin', 'admin123')")
conn.commit()

# Dummy car list
car_list = [
    {"id": 1, "name": "Toyota Camry"},
    {"id": 2, "name": "Honda Civic"},
    {"id": 3, "name": "Ford Mustang"},
    {"id": 4, "name": "BMW 3 Series"},
    {"id": 5, "name": "Tesla Model 3"},
    {"id": 6, "name": "Mazda CX-5"}
]

@app.route('/')
def home():
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # ✅ SAFE: Use parameterized query
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        result = cursor.fetchone()

        if result:
            session['username'] = username
            return redirect('/cars')
        else:
            msg = "Invalid credentials"
    return render_template('login.html', msg=msg)

@app.route('/cars')
def cars():
    if 'username' not in session:
        return redirect('/login')
    search = request.args.get('search', '')
    filtered = [c for c in car_list if search.lower() in c["name"].lower()]
    return render_template('cars.html', cars=filtered)

@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # 🔥 Vulnerable to SQL Injection (on purpose)
        try:
            conn.execute(f"INSERT INTO users (username, password) VALUES ('{username}', '{password}')")
            conn.commit()
            msg = "Registration successful. You can now log in."
        except:
            msg = "Registration failed. User may already exist."
    return render_template('register.html', msg=msg)


@app.route('/book/<int:car_id>', methods=['GET', 'POST'])
def book(car_id):
    if 'username' not in session:
        return redirect('/login')

    car = next((c for c in car_list if c["id"] == car_id), None)
    if not car:
        return "Car not found"

    if request.method == 'POST':
        booking_date = request.form['date']

        # ✅ Check if the user already booked this car on that date
        existing = conn.execute("SELECT * FROM bookings WHERE car = ? AND user = ? AND date = ?",
                                (car["name"], session['username'], booking_date)).fetchone()
        if existing:
            return f"You have already booked {car['name']} on {booking_date}."

        conn.execute("INSERT INTO bookings (car, user, date) VALUES (?, ?, ?)",
                     (car["name"], session['username'], booking_date))
        conn.commit()
        return f"You booked {car['name']} on {booking_date}!"

    return render_template('book.html', car=car)



@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    msg = ''
    if request.method == 'POST':
        comment = escape(request.form['comment'])  # ✅ Sanitize input
        msg = comment
    return render_template('feedback.html', msg=msg)

@app.route('/my_bookings')
def my_bookings():
    if 'username' not in session:
        return redirect('/login')

    cursor = conn.execute("SELECT car, date FROM bookings WHERE user = ?", (session['username'],))
    bookings = cursor.fetchall()
    return render_template('my_bookings.html', bookings=bookings)

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'username' not in session or session['username'] != 'admin':
        return redirect('/login')

    cursor = conn.execute("SELECT car, COUNT(*) as count FROM bookings GROUP BY car")
    stats = cursor.fetchall()
    return render_template('admin_dashboard.html', stats=stats)



@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
