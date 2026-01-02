from flask import Flask, render_template, request, redirect, url_for, flash, make_response
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import sqlite3
import bcrypt
import pandas as pd
from datetime import datetime, timedelta
import io

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change for production

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id, username, role, staff_role, shop_id):
        self.id = id
        self.username = username
        self.role = role
        self.staff_role = staff_role
        self.shop_id = shop_id
def get_db():
    conn = sqlite3.connect('garage_system.db')
    conn.row_factory = sqlite3.Row
    return conn
def init_tables():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shops (
                shop_id SERIAL PRIMARY KEY,
                shop_name TEXT UNIQUE,
                contact_email TEXT,
                contact_phone TEXT,
                address TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                shop_id INTEGER REFERENCES shops(shop_id),
                username TEXT UNIQUE,
                password TEXT,
                role TEXT CHECK(role IN ('Customer', 'Staff')),
                email TEXT,
                phone TEXT,
                staff_role TEXT CHECK(staff_role IN (NULL, 'Mechanic', 'Admin'))
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vehicles (
                id SERIAL PRIMARY KEY,
                shop_id INTEGER REFERENCES shops(shop_id),
                owner TEXT,
                model TEXT,
                plate_number TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id SERIAL PRIMARY KEY,
                shop_id INTEGER REFERENCES shops(shop_id),
                owner TEXT,
                vehicle TEXT,
                service TEXT,
                status TEXT DEFAULT 'Pending',
                date TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS spare_parts (
                id SERIAL PRIMARY KEY,
                shop_id INTEGER REFERENCES shops(shop_id),
                part_name TEXT,
                price REAL,
                stock INTEGER
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                id SERIAL PRIMARY KEY,
                shop_id INTEGER REFERENCES shops(shop_id),
                owner TEXT,
                service TEXT,
                amount REAL,
                status TEXT DEFAULT 'Unpaid'
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id SERIAL PRIMARY KEY,
                shop_id INTEGER REFERENCES shops(shop_id),
                customer TEXT,
                mechanic TEXT,
                rating INTEGER,
                comments TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id SERIAL PRIMARY KEY,
                shop_id INTEGER REFERENCES shops(shop_id),
                staff_username TEXT,
                action TEXT,
                timestamp TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parts_usage (
                id SERIAL PRIMARY KEY,
                shop_id INTEGER REFERENCES shops(shop_id),
                appointment_id INTEGER,
                part_id INTEGER,
                quantity INTEGER
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id SERIAL PRIMARY KEY,
                shop_id INTEGER REFERENCES shops(shop_id),
                invoice_id INTEGER,
                customer TEXT,
                amount REAL,
                method TEXT CHECK(method IN ('Cash', 'Mobile Money', 'Bank Card')),
                transaction_id TEXT,
                timestamp TEXT
            )
        """)
        # Indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_shops_name ON shops (shop_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_shop ON users (shop_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_vehicles_shop ON vehicles (shop_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_appointments_shop ON appointments (shop_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_spare_parts_shop ON spare_parts (shop_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_shop ON invoices (shop_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_shop ON feedback (shop_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_shop ON logs (shop_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_parts_usage_shop ON parts_usage (shop_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_payments_shop ON payments (shop_id)")
        # Initial shop (for testing)
        cursor.execute("INSERT INTO shops (shop_name, contact_email, contact_phone, address) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
                       ('Downtown AutoFix', 'downtown@autofixpro.com', '0712345678', '123 Nairobi St'))
        # Initial spare parts for shop_id=1
        initial_parts = [
            ("Toyota Oil Filter", 12.99 * 129, 50),
            ("Lexus Brake Pads", 45.99 * 129, 30),
            ("Land Rover Air Filter", 29.99 * 129, 40),
            ("BMW Spark Plug", 15.99 * 129, 60),
            ("Mercedes Oil Filter", 13.99 * 129, 45),
            ("Nissan Brake Disc", 65.99 * 129, 25),
            ("Honda Timing Belt", 39.99 * 129, 20),
        ]
        cursor.execute("SELECT shop_id FROM shops WHERE shop_name = %s", ('Downtown AutoFix',))
        shop_id = cursor.fetchone()[0]
        for part_name, price, stock in initial_parts:
            cursor.execute("INSERT INTO spare_parts (shop_id, part_name, price, stock) VALUES (%s, %s, %s, %s)", (shop_id, part_name, price, stock))
        conn.commit()

@login_manager.user_loader
def load_user(user_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, role, staff_role, shop_id FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if user:
            return User(user['id'], user['username'], user['role'], user['staff_role'], user['shop_id'])
        return None

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(stored, provided):
    return bcrypt.checkpw(provided.encode('utf-8'), stored.encode('utf-8'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        role = request.form['role'].strip()
        email = request.form['email'].strip()
        phone = request.form['phone'].strip()
        staff_role = request.form.get('staff_role', '').strip() or None
        shop_id = int(request.form['shop_id'])
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO users (shop_id, username, password, role, email, phone, staff_role) VALUES (?, ?, ?, ?, ?, ?, ?)",
                              (shop_id, username, hashed_password.decode('utf-8'), role, email, phone, staff_role))
                conn.commit()
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists!', 'error')
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT shop_id, shop_name FROM shops")
        shops = cursor.fetchall()
    return render_template('register.html', shops=shops)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, password, role, staff_role, shop_id FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                user_obj = User(user['id'], user['username'], user['role'], user['staff_role'], user['shop_id'])
                login_user(user_obj)
                return redirect(url_for('dashboard'))
            flash('Invalid username or password!', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out!', 'success')
    return redirect(url_for('index'))
@app.route('/dashboard')
@login_required
def dashboard():
    upcoming = []
    if current_user.role == 'Customer':
        today = datetime.now().date()
        end_date = today + timedelta(days=7)
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, vehicle, service, date FROM appointments WHERE shop_id=? AND owner=? AND date BETWEEN ? AND ? AND status='Pending'",
                          (current_user.shop_id, current_user.username, today.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))
            upcoming = cursor.fetchall()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT shop_name FROM shops WHERE shop_id = ?", (current_user.shop_id,))
        shop_name = cursor.fetchone()['shop_name']
    return render_template('dashboard.html', role=current_user.role, staff_role=current_user.staff_role, upcoming=upcoming, shop_name=shop_name)
@app.route('/register_vehicle', methods=['GET', 'POST'])
@login_required
def register_vehicle():
    if current_user.role != 'Customer':
        flash('Access denied!', 'error')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        model = request.form['model'].strip()
        plate = request.form['plate'].strip()
        if not model or not plate:
            flash('All fields required!', 'error')
            return redirect(url_for('register_vehicle'))
        with get_db() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO vehicles (owner, model, plate_number) VALUES (?, ?, ?)", (current_user.username, model, plate))
                conn.commit()
                flash('Vehicle registered!', 'success')
                return redirect(url_for('dashboard'))
            except sqlite3.IntegrityError:
                flash('Plate number already exists!', 'error')
    return render_template('register_vehicle.html')

@app.route('/book_appointment', methods=['GET', 'POST'])
@login_required
def book_appointment():
    if current_user.role != 'Customer':
        flash('Access denied!', 'error')
        return redirect(url_for('dashboard'))
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT plate_number FROM vehicles WHERE owner=?", (current_user.username,))
        vehicles = [row['plate_number'] for row in cursor.fetchall()]
    if not vehicles:
        flash('Register a vehicle first!', 'error')
        return redirect(url_for('register_vehicle'))
    if request.method == 'POST':
        vehicle = request.form['vehicle']
        service = request.form['service'].strip()
        date = request.form['date']
        if not service or not date:
            flash('All fields required!', 'error')
            return redirect(url_for('book_appointment'))
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO appointments (owner, vehicle, service, date) VALUES (?, ?, ?, ?)", (current_user.username, vehicle, service, date))
            conn.commit()
            flash('Appointment booked!', 'success')
            return redirect(url_for('dashboard'))
    return render_template('book_appointment.html', vehicles=vehicles)

@app.route('/track_repairs')
@login_required
def track_repairs():
    if current_user.role != 'Customer':
        flash('Access denied!', 'error')
        return redirect(url_for('dashboard'))
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, vehicle, service, status, date FROM appointments WHERE owner=?", (current_user.username,))
        repairs = cursor.fetchall()
    return render_template('track_repairs.html', repairs=repairs)

@app.route('/view_spare_parts')
@login_required
def view_spare_parts():
    brand = request.args.get('brand', 'All')
    sort = request.args.get('sort', 'Name')
    query = "SELECT part_name, price, stock FROM spare_parts"
    params = []
    if brand != 'All':
        query += " WHERE part_name LIKE ?"
        params.append(f"%{brand}%")
    if sort == 'Price':
        query += " ORDER BY price"
    elif sort == 'Stock':
        query += " ORDER BY stock"
    else:
        query += " ORDER BY part_name"
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        parts = cursor.fetchall()
    brands = ["All", "Toyota", "Lexus", "Land Rover", "BMW", "Mercedes", "Nissan", "Honda"]
    brand_logos = {
        "All": "https://img.icons8.com/ios/50/car--v1.png",
        "Toyota": "https://img.icons8.com/color/48/toyota.png",
        "Lexus": "https://img.icons8.com/color/48/lexus.png",
        "Land Rover": "https://img.icons8.com/color/48/land-rover.png",
        "BMW": "https://img.icons8.com/color/48/bmw.png",
        "Mercedes": "https://img.icons8.com/color/48/mercedes.png",
        "Nissan": "https://img.icons8.com/color/48/nissan.png",
        "Honda": "https://img.icons8.com/color/48/honda.png"
    }
    return render_template('view_spare_parts.html', parts=parts, brands=brands, selected_brand=brand, selected_sort=sort, brand_logos=brand_logos)

@app.route('/view_recommendations')
@login_required
def view_recommendations():
    if current_user.role != 'Customer':
        flash('Access denied!', 'error')
        return redirect(url_for('dashboard'))
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT model FROM vehicles WHERE owner=?", (current_user.username,))
        vehicles = [row['model'] for row in cursor.fetchall()]
    if not vehicles:
        flash('Register a vehicle to see recommendations!', 'error')
        return redirect(url_for('dashboard'))
    model = vehicles[0].split()[0]  # Get brand
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT part_name, price, stock FROM spare_parts WHERE part_name LIKE ?", (f"%{model}%",))
        parts = cursor.fetchall()
    return render_template('view_recommendations.html', parts=parts, model=model)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if current_user.role != 'Customer':
        flash('Access denied!', 'error')
        return redirect(url_for('dashboard'))
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT email, phone FROM users WHERE username=?", (current_user.username,))
        user_data = cursor.fetchone()
        email, phone = user_data['email'], user_data['phone']
        cursor.execute("SELECT id, service, status, date FROM appointments WHERE owner=?", (current_user.username,))
        appointments = cursor.fetchall()
        cursor.execute("SELECT id, service, amount, status FROM invoices WHERE owner=?", (current_user.username,))
        invoices = cursor.fetchall()
    if request.method == 'POST':
        new_email = request.form['email'].strip()
        new_phone = request.form['phone'].strip()
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET email=?, phone=? WHERE username=?", (new_email, new_phone, current_user.username))
            conn.commit()
            flash('Profile updated!', 'success')
            return redirect(url_for('profile'))
    return render_template('profile.html', email=email, phone=phone, appointments=appointments, invoices=invoices)

@app.route('/export_history')
@login_required
def export_history():
    if current_user.role != 'Customer':
        flash('Access denied!', 'error')
        return redirect(url_for('dashboard'))
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, service, status, date FROM appointments WHERE owner=?", (current_user.username,))
        apps = cursor.fetchall()
        app_df = pd.DataFrame(apps, columns=["ID", "Service", "Status", "Date"])
        cursor.execute("SELECT id, service, amount, status FROM invoices WHERE owner=?", (current_user.username,))
        invs = cursor.fetchall()
        inv_df = pd.DataFrame(invs, columns=["ID", "Service", "Amount (KES)", "Status"])
    output = io.StringIO()
    app_df.to_csv(output, index=False)
    output.write("\n")
    inv_df.to_csv(output, index=False)
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = f"attachment; filename=service_history_{current_user.username}_{datetime.now().strftime('%Y%m%d')}.csv"
    response.headers["Content-type"] = "text/csv"
    return response

@app.route('/view_mechanic_ratings')
@login_required
def view_mechanic_ratings():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT mechanic, AVG(rating) as avg_rating FROM feedback GROUP BY mechanic")
        ratings = cursor.fetchall()
    return render_template('view_mechanic_ratings.html', ratings=ratings)

@app.route('/view_invoices')
@login_required
def view_invoices():
    if current_user.role != 'Customer':
        flash('Access denied!', 'error')
        return redirect(url_for('dashboard'))
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, service, amount, status FROM invoices WHERE owner=?", (current_user.username,))
        invoices = cursor.fetchall()
    return render_template('view_invoices.html', invoices=invoices)

@app.route('/pay_invoice', methods=['GET', 'POST'])
@login_required
def pay_invoice():
    if current_user.role != 'Customer':
        flash('Access denied!', 'error')
        return redirect(url_for('dashboard'))
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, service, amount, status FROM invoices WHERE owner=? AND status='Unpaid'", (current_user.username,))
        invoices = cursor.fetchall()
    if request.method == 'POST':
        inv_id = request.form['inv_id']
        method = request.form['method']
        pay_amount = float(request.form['pay_amount'])
        trans_id = request.form.get('trans_id', '').strip()
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT amount FROM invoices WHERE id=?", (inv_id,))
            inv_amount = cursor.fetchone()['amount']
            if pay_amount < inv_amount:
                flash(f"Payment amount (KES {pay_amount:.2f}) must be at least KES {inv_amount:.2f}!", 'error')
                return redirect(url_for('pay_invoice'))
            if method in ['Mobile Money', 'Bank Card'] and not trans_id:
                flash('Transaction ID required for Mobile Money or Bank Card!', 'error')
                return redirect(url_for('pay_invoice'))
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("UPDATE invoices SET status='Paid' WHERE id=?", (inv_id,))
            cursor.execute("INSERT INTO payments (invoice_id, customer, amount, method, transaction_id, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                           (inv_id, current_user.username, pay_amount, method, trans_id or None, timestamp))
            conn.commit()
            flash('Payment recorded!', 'success')
            return redirect(url_for('dashboard'))
    return render_template('pay_invoice.html', invoices=invoices)

@app.route('/feedback', methods=['GET', 'POST'])
@login_required
def feedback():
    if current_user.role != 'Customer':
        flash('Access denied!', 'error')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        mechanic = request.form['mechanic'].strip()
        rating = int(request.form['rating'])
        comments = request.form['comments'].strip()
        if not 1 <= rating <= 5:
            flash('Rating must be 1-5!', 'error')
            return redirect(url_for('feedback'))
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO feedback (customer, mechanic, rating, comments) VALUES (?, ?, ?, ?)", 
                           (current_user.username, mechanic, rating, comments))
            conn.commit()
            flash('Feedback submitted!', 'success')
            return redirect(url_for('dashboard'))
    return render_template('feedback.html')

@app.route('/view_appointments')
@login_required
def view_appointments():
    if current_user.role != 'Staff':
        flash('Access denied!', 'error')
        return redirect(url_for('dashboard'))
    date = request.args.get('date', datetime.now().date().strftime("%Y-%m-%d"))
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, owner, vehicle, service, status FROM appointments WHERE shop_id=? AND date=?", (current_user.shop_id, date))
        appointments = cursor.fetchall()
    return render_template('view_appointments.html', appointments=appointments, date=date)
@app.route('/update_repair_status', methods=['GET', 'POST'])
@login_required
def update_repair_status():
    if current_user.role != 'Staff':
        flash('Access denied!', 'error')
        return redirect(url_for('dashboard'))
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM appointments WHERE shop_id=?", (current_user.shop_id,))
        app_ids = [row['id'] for row in cursor.fetchall()]
        cursor.execute("SELECT id, part_name, stock FROM spare_parts WHERE shop_id=?", (current_user.shop_id,))
        parts = cursor.fetchall()
    if request.method == 'POST':
        app_id = int(request.form['app_id'])
        status = request.form['status'].strip()
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE appointments SET status=? WHERE shop_id=? AND id=?", (status, current_user.shop_id, app_id))
            if status == 'Completed':
                amount = float(request.form['amount'])
                cursor.execute("SELECT owner, service FROM appointments WHERE shop_id=? AND id=?", (current_user.shop_id, app_id))
                owner, service = cursor.fetchone()
                cursor.execute("INSERT INTO invoices (shop_id, owner, service, amount) VALUES (?, ?, ?, ?)", (current_user.shop_id, owner, service, amount))
                for part in parts:
                    quantity = int(request.form.get(f'part_{part["id"]}', 0))
                    if quantity > 0:
                        cursor.execute("INSERT INTO parts_usage (shop_id, appointment_id, part_id, quantity) VALUES (?, ?, ?, ?)", 
                                      (current_user.shop_id, app_id, part['id'], quantity))
                        cursor.execute("UPDATE spare_parts SET stock = stock - ? WHERE shop_id=? AND id=?", (quantity, current_user.shop_id, part['id']))
            cursor.execute("INSERT INTO logs (shop_id, staff_username, action, timestamp) VALUES (?, ?, ?, ?)",
                          (current_user.shop_id, current_user.username, f"Updated appointment {app_id} to {status}", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            flash('Status updated!', 'success')
            return redirect(url_for('view_appointments'))
    return render_template('update_repair_status.html', app_ids=app_ids, parts=parts)

@app.route('/manage_spare_parts', methods=['GET', 'POST'])
@login_required
def manage_spare_parts():
    if current_user.role != 'Staff' or current_user.staff_role != 'Admin':
        flash('Access denied!', 'error')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        action = request.form['action']
        if action == 'add':
            name = request.form['name'].strip()
            price = float(request.form['price'])
            stock = int(request.form['stock'])
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO spare_parts (part_name, price, stock) VALUES (?, ?, ?)", (name, price, stock))
                conn.commit()
                flash('Part added!', 'success')
        elif action == 'edit':
            part_id = int(request.form['part_id'])
            name = request.form['name'].strip()
            price = float(request.form['price'])
            stock = int(request.form['stock'])
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE spare_parts SET part_name=?, price=?, stock=? WHERE id=?", (name, price, stock, part_id))
                conn.commit()
                flash('Part updated!', 'success')
        elif action == 'delete':
            part_id = int(request.form['part_id'])
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM spare_parts WHERE id=?", (part_id,))
                conn.commit()
                flash('Part deleted!', 'success')
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, part_name, price, stock FROM spare_parts")
        parts = cursor.fetchall()
    return render_template('manage_spare_parts.html', parts=parts)

@app.route('/generate_reports', methods=['GET', 'POST'])
@login_required
def generate_reports():
    if current_user.role != 'Staff' or current_user.staff_role != 'Admin':
        flash('Access denied!', 'error')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, owner, vehicle, service, status, date FROM appointments WHERE date BETWEEN ? AND ?", (start_date, end_date))
            apps = cursor.fetchall()
            app_df = pd.DataFrame(apps, columns=["ID", "Owner", "Vehicle", "Service", "Status", "Date"])
            cursor.execute("SELECT id, owner, service, amount, status FROM invoices WHERE EXISTS (SELECT 1 FROM appointments WHERE appointments.owner=invoices.owner AND appointments.date BETWEEN ? AND ?)", (start_date, end_date))
            invs = cursor.fetchall()
            inv_df = pd.DataFrame(invs, columns=["ID", "Owner", "Service", "Amount (KES)", "Status"])
            output = io.StringIO()
            app_df.to_csv(output, index=False)
            output.write("\n")
            inv_df.to_csv(output, index=False)
            response = make_response(output.getvalue())
            response.headers["Content-Disposition"] = f"attachment; filename=garage_report_{start_date}_to_{end_date}.csv"
            response.headers["Content-type"] = "text/csv"
            return response
    return render_template('generate_reports.html')

@app.route('/view_logs')
@login_required
def view_logs():
    if current_user.role != 'Staff' or current_user.staff_role != 'Admin':
        flash('Access denied!', 'error')
        return redirect(url_for('dashboard'))
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, staff_username, action, timestamp FROM logs")
        logs = cursor.fetchall()
    return render_template('view_logs.html', logs=logs)

@app.route('/view_feedback')
@login_required
def view_feedback():
    if current_user.role != 'Staff':
        flash('Access denied!', 'error')
        return redirect(url_for('dashboard'))
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT customer, mechanic, rating, comments FROM feedback")
        feedback = cursor.fetchall()
    return render_template('view_feedback.html', feedback=feedback)

@app.route('/performance_dashboard')
@login_required
def performance_dashboard():
    if current_user.role != 'Staff' or current_user.staff_role != 'Admin':
        flash('Access denied!', 'error')
        return redirect(url_for('dashboard'))
    with get_db() as conn:
        cursor = conn.cursor()
        # Completed appointments per mechanic
        cursor.execute("""
            SELECT u.username, COUNT(a.id) as completed
            FROM users u
            LEFT JOIN appointments a ON u.username = a.owner AND a.status = 'Completed'
            WHERE u.role = 'Staff' AND u.staff_role = 'Mechanic'
            GROUP BY u.username
        """)
        completions = cursor.fetchall()
        # Average ratings
        cursor.execute("SELECT mechanic, AVG(rating) as avg_rating FROM feedback GROUP BY mechanic")
        ratings = cursor.fetchall()
    return render_template('performance_dashboard.html', completions=completions, ratings=ratings)

@app.route('/view_payments')
@login_required
def view_payments():
    if current_user.role != 'Staff' or current_user.staff_role != 'Admin':
        flash('Access denied!', 'error')
        return redirect(url_for('dashboard'))
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, invoice_id, customer, amount, method, transaction_id, timestamp FROM payments")
        payments = cursor.fetchall()
    return render_template('view_payments.html', payments=payments)

@app.route('/manage_shops', methods=['GET', 'POST'])
@login_required
def manage_shops():
    if current_user.role != 'Staff' or current_user.staff_role != 'Admin':
        flash('Access denied! Super-admin only.', 'error')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        shop_name = request.form['shop_name'].strip()
        contact_email = request.form['contact_email'].strip()
        contact_phone = request.form['contact_phone'].strip()
        address = request.form['address'].strip()
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO shops (shop_name, contact_email, contact_phone, address) VALUES (?, ?, ?, ?)",
                          (shop_name, contact_email, contact_phone, address))
            conn.commit()
            flash('Shop added!', 'success')
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT shop_id, shop_name, contact_email, contact_phone, address FROM shops")
        shops = cursor.fetchall()
    return render_template('manage_shops.html', shops=shops)

if __name__ == '__main__':
    app.run(debug=True)