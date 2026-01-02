import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk
from tkcalendar import Calendar
import bcrypt
import pandas as pd
from datetime import datetime, timedelta

class GarageApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Offline Garage Management System")
        self.conn = sqlite3.connect("garage_system.db")
        self.cursor = self.conn.cursor()
        self.init_tables()
        tk.Label(root, text="Welcome to Garage System", font=("Arial", 16)).pack()
        tk.Button(root, text="Register", command=self.register_window).pack()
        tk.Button(root, text="Login", command=self.login_window).pack()
        self.root.protocol("WM_DELETE_WINDOW", self.close_app)

    def init_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                role TEXT CHECK(role IN ('Customer', 'Staff')),
                email TEXT,
                phone TEXT,
                staff_role TEXT CHECK(staff_role IN (NULL, 'Mechanic', 'Admin'))
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS vehicles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner TEXT,
                model TEXT,
                plate_number TEXT UNIQUE
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner TEXT,
                vehicle TEXT,
                service TEXT,
                status TEXT DEFAULT 'Pending',
                date TEXT
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS spare_parts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                part_name TEXT,
                price REAL,
                stock INTEGER
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner TEXT,
                service TEXT,
                amount REAL,
                status TEXT DEFAULT 'Unpaid'
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer TEXT,
                mechanic TEXT,
                rating INTEGER,
                comments TEXT
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                staff_username TEXT,
                action TEXT,
                timestamp TEXT
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS parts_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                appointment_id INTEGER,
                part_id INTEGER,
                quantity INTEGER
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER,
                customer TEXT,
                amount REAL,
                method TEXT CHECK(method IN ('Cash', 'Mobile Money', 'Bank Card')),
                transaction_id TEXT,
                timestamp TEXT
            )
        """)
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_spare_parts_name ON spare_parts (part_name)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_appointments_owner ON appointments (owner)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_owner ON invoices (owner)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_parts_usage_appointment ON parts_usage (appointment_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_payments_invoice ON payments (invoice_id)")
        self.cursor.execute("SELECT COUNT(*) FROM spare_parts")
        if self.cursor.fetchone()[0] == 0:
            # Prices converted from USD to KES (1 USD = 129 KES)
            initial_parts = [
                ("Toyota Oil Filter", 12.99 * 129, 50),
                ("Toyota Air Filter", 25.50 * 129, 30),
                ("Toyota Front Brake Pads", 45.00 * 129, 20),
                ("Toyota Spark Plugs Set (4)", 35.00 * 129, 15),
                ("Toyota Serpentine Belt", 28.99 * 129, 10),
                ("Toyota Battery (Group 35)", 120.00 * 129, 5),
                ("Toyota Wiper Blades (Pair)", 22.50 * 129, 25),
                ("Lexus Oil Filter", 18.99 * 129, 40),
                ("Lexus Cabin Air Filter", 32.00 * 129, 25),
                ("Lexus Rear Brake Pads", 60.00 * 129, 15),
                ("Lexus Timing Belt Kit", 150.00 * 129, 8),
                ("Lexus Drive Belt", 35.50 * 129, 12),
                ("Lexus AGM Battery", 180.00 * 129, 4),
                ("Lexus Windshield Wipers", 28.00 * 129, 20),
                ("Land Rover Oil Filter", 15.99 * 129, 35),
                ("Land Rover Engine Air Filter", 28.00 * 129, 20),
                ("Land Rover Brake Rotor (Front)", 85.00 * 129, 10),
                ("Land Rover Fuel Filter", 40.00 * 129, 15),
                ("Land Rover Accessory Belt", 32.99 * 129, 8),
                ("Land Rover Battery (Group 49)", 140.00 * 129, 6),
                ("Land Rover Wiper Refills", 18.50 * 129, 30),
                ("BMW Oil Filter Kit", 22.50 * 129, 30),
                ("BMW Cabin Filter", 35.00 * 129, 25),
                ("BMW Brake Pads (Front)", 70.00 * 129, 12),
                ("BMW Spark Plugs (6)", 50.00 * 129, 10),
                ("BMW Serpentine Belt", 45.00 * 129, 8),
                ("BMW Battery (AGM H8)", 220.00 * 129, 3),
                ("BMW Aero Wiper Blades", 40.00 * 129, 15),
                ("Mercedes Oil Filter", 20.99 * 129, 35),
                ("Mercedes Air Filter", 30.00 * 129, 20),
                ("Mercedes Brake Pads (Rear)", 65.00 * 129, 15),
                ("Mercedes Water Pump", 120.00 * 129, 5),
                ("Mercedes V-Belt", 38.00 * 129, 10),
                ("Mercedes Battery (Group 94R)", 190.00 * 129, 4),
                ("Mercedes Wiper Blades", 35.50 * 129, 18),
                ("Nissan Oil Filter", 11.99 * 129, 45),
                ("Nissan Air Filter", 22.00 * 129, 35),
                ("Nissan Brake Pads (Front)", 40.00 * 129, 25),
                ("Nissan Spark Plugs Set", 30.00 * 129, 20),
                ("Nissan Timing Chain", 80.00 * 129, 7),
                ("Nissan Battery (Group 24)", 110.00 * 129, 6),
                ("Nissan Wiper Blades", 20.00 * 129, 28),
                ("Honda Oil Filter", 10.99 * 129, 50),
                ("Honda Cabin Air Filter", 20.50 * 129, 30),
                ("Honda Rear Brake Pads", 38.00 * 129, 22),
                ("Honda Ignition Coils (4)", 45.00 * 129, 12),
                ("Honda Fan Belt", 25.99 * 129, 15),
                ("Honda Battery (Group 51R)", 100.00 * 129, 5),
                ("Honda Windshield Wipers", 18.00 * 129, 25),
            ]
            for part_name, price, stock in initial_parts:
                self.cursor.execute("INSERT INTO spare_parts (part_name, price, stock) VALUES (?, ?, ?)", (part_name, price, stock))
        self.conn.commit()

    def close_app(self):
        self.conn.close()
        self.root.destroy()

    def hash_password(self, password):
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, stored_password, provided_password):
        return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password.encode('utf-8'))

    def log_action(self, staff_username, action):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute("INSERT INTO logs (staff_username, action, timestamp) VALUES (?, ?, ?)", 
                           (staff_username, action, timestamp))
        self.conn.commit()

    def register_window(self):
        reg_win = tk.Toplevel(self.root)
        reg_win.title("Register User")
        tk.Label(reg_win, text="Username").pack()
        username_entry = tk.Entry(reg_win)
        username_entry.pack()
        tk.Label(reg_win, text="Password").pack()
        password_entry = tk.Entry(reg_win, show="*")
        password_entry.pack()
        tk.Label(reg_win, text="Email").pack()
        email_entry = tk.Entry(reg_win)
        email_entry.pack()
        tk.Label(reg_win, text="Phone").pack()
        phone_entry = tk.Entry(reg_win)
        phone_entry.pack()
        tk.Label(reg_win, text="Role (Customer/Staff)").pack()
        role_entry = tk.Entry(reg_win)
        role_entry.pack()
        tk.Label(reg_win, text="Staff Role (Mechanic/Admin, if Staff)").pack()
        staff_role_entry = tk.Entry(reg_win)
        staff_role_entry.pack()

        def register():
            username = username_entry.get().strip()
            password = self.hash_password(password_entry.get())
            email = email_entry.get().strip()
            phone = phone_entry.get().strip()
            role = role_entry.get().strip().capitalize()
            staff_role = staff_role_entry.get().strip().capitalize() or None
            if not username or not password or not role:
                messagebox.showerror("Error", "Username, password, and role required!")
                return
            if role not in ['Customer', 'Staff']:
                messagebox.showerror("Error", "Invalid role! Must be 'Customer' or 'Staff'.")
                return
            if role == 'Staff' and staff_role not in ['Mechanic', 'Admin', None]:
                messagebox.showerror("Error", "Invalid staff role! Must be 'Mechanic' or 'Admin'.")
                return
            if role == 'Customer':
                staff_role = None
            try:
                self.cursor.execute("INSERT INTO users (username, password, email, phone, role, staff_role) VALUES (?, ?, ?, ?, ?, ?)", 
                                   (username, password, email, phone, role, staff_role))
                self.conn.commit()
                messagebox.showinfo("Success", "Registration Complete!")
                reg_win.destroy()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Username already exists!")

        tk.Button(reg_win, text="Register", command=register).pack()

    def login_window(self):
        login_win = tk.Toplevel(self.root)
        login_win.title("Login")
        tk.Label(login_win, text="Username").pack()
        username_entry = tk.Entry(login_win)
        username_entry.pack()
        tk.Label(login_win, text="Password").pack()
        password_entry = tk.Entry(login_win, show="*")
        password_entry.pack()

        def login():
            username = username_entry.get().strip()
            provided_password = password_entry.get()
            self.cursor.execute("SELECT password, role, staff_role FROM users WHERE username=?", (username,))
            user = self.cursor.fetchone()
            if user and self.check_password(user[0], provided_password):
                role, staff_role = user[1], user[2]
                messagebox.showinfo("Success", f"Welcome {username} ({role}{', ' + staff_role if staff_role else ''})!")
                self.dashboard_window(username, role, staff_role)
                login_win.destroy()
            else:
                messagebox.showerror("Error", "Invalid Credentials")

        tk.Button(login_win, text="Login", command=login).pack()

    def dashboard_window(self, username, role, staff_role):
        dashboard = tk.Toplevel(self.root)
        dashboard.title("Dashboard")
        tk.Label(dashboard, text=f"Welcome {username} ({role}{', ' + staff_role if staff_role else ''})", font=("Arial", 14)).pack()
        if role == "Customer":
            tk.Button(dashboard, text="Register Vehicle", command=lambda: self.register_vehicle(username)).pack()
            tk.Button(dashboard, text="Book Appointment", command=lambda: self.book_appointment(username)).pack()
            tk.Button(dashboard, text="Track Repairs", command=lambda: self.track_repairs(username)).pack()
            tk.Button(dashboard, text="View Spare Parts", command=self.view_spare_parts).pack()
            tk.Button(dashboard, text="Provide Feedback", command=lambda: self.feedback_window(username)).pack()
            tk.Button(dashboard, text="View Invoices", command=lambda: self.view_invoices(username)).pack()
            tk.Button(dashboard, text="Pay Invoice", command=lambda: self.pay_invoice(username)).pack()
            tk.Button(dashboard, text="View Recommendations", command=lambda: self.view_recommendations(username)).pack()
            tk.Button(dashboard, text="My Profile", command=lambda: self.profile_window(username)).pack()
            tk.Button(dashboard, text="View Mechanic Ratings", command=lambda: self.view_mechanic_ratings()).pack()
            # Appointment Reminders
            tk.Label(dashboard, text="Upcoming Appointments", font=("Arial", 12, "bold")).pack()
            tree = ttk.Treeview(dashboard, columns=("ID", "Vehicle", "Service", "Date"), show="headings")
            tree.heading("ID", text="ID")
            tree.heading("Vehicle", text="Vehicle")
            tree.heading("Service", text="Service")
            tree.heading("Date", text="Date")
            today = datetime.now().date()
            end_date = today + timedelta(days=7)
            self.cursor.execute("SELECT id, vehicle, service, date FROM appointments WHERE owner=? AND date BETWEEN ? AND ? AND status='Pending'",
                              (username, today.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))
            for id_, veh, serv, date in self.cursor.fetchall():
                # Highlight if date is tomorrow
                tag = "urgent" if (datetime.strptime(date, "%Y-%m-%d").date() - today).days == 1 else ""
                tree.insert("", "end", values=(id_, veh, serv, date), tags=(tag,))
            tree.tag_configure("urgent", background="yellow")
            tree.pack()
        elif role == "Staff":
            tk.Button(dashboard, text="View Appointments", command=self.view_appointments).pack()
            tk.Button(dashboard, text="Update Repair Status", command=lambda: self.update_repair_status(username, staff_role)).pack()
            if staff_role == "Admin":
                tk.Button(dashboard, text="Manage Spare Parts", command=lambda: self.manage_spare_parts(username)).pack()
                tk.Button(dashboard, text="Generate Reports", command=self.generate_reports).pack()
                tk.Button(dashboard, text="View Logs", command=self.view_logs).pack()
                tk.Button(dashboard, text="Performance Dashboard", command=self.performance_dashboard).pack()
                tk.Button(dashboard, text="View Payments", command=self.view_payments).pack()
            tk.Button(dashboard, text="View Feedback", command=self.view_feedback).pack()
        tk.Button(dashboard, text="Logout", command=dashboard.destroy).pack()

    def register_vehicle(self, username):
        veh_win = tk.Toplevel(self.root)
        veh_win.title("Register Vehicle")
        tk.Label(veh_win, text="Model").pack()
        model_entry = tk.Entry(veh_win)
        model_entry.pack()
        tk.Label(veh_win, text="Plate Number").pack()
        plate_entry = tk.Entry(veh_win)
        plate_entry.pack()

        def register_veh():
            model = model_entry.get().strip()
            plate = plate_entry.get().strip()
            if not model or not plate:
                messagebox.showerror("Error", "All fields required!")
                return
            try:
                self.cursor.execute("INSERT INTO vehicles (owner, model, plate_number) VALUES (?, ?, ?)", (username, model, plate))
                self.conn.commit()
                messagebox.showinfo("Success", "Vehicle registered!")
                veh_win.destroy()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Plate number already exists!")

        tk.Button(veh_win, text="Register", command=register_veh).pack()

    def book_appointment(self, username):
        app_win = tk.Toplevel(self.root)
        app_win.title("Book Appointment")
        self.cursor.execute("SELECT plate_number FROM vehicles WHERE owner=?", (username,))
        vehicles = [row[0] for row in self.cursor.fetchall()]
        if not vehicles:
            messagebox.showerror("Error", "Register a vehicle first!")
            app_win.destroy()
            return
        tk.Label(app_win, text="Vehicle Plate").pack()
        vehicle_var = tk.StringVar(app_win)
        vehicle_var.set(vehicles[0])
        tk.OptionMenu(app_win, vehicle_var, *vehicles).pack()
        tk.Label(app_win, text="Service Required").pack()
        service_entry = tk.Entry(app_win)
        service_entry.pack()
        tk.Label(app_win, text="Date").pack()
        date_cal = Calendar(app_win, selectmode="day", date_pattern="yyyy-mm-dd")
        date_cal.pack()

        def book():
            vehicle = vehicle_var.get()
            service = service_entry.get().strip()
            date = date_cal.get_date()
            if not service:
                messagebox.showerror("Error", "Service required!")
                return
            try:
                if datetime.strptime(date, "%Y-%m-%d").date() < datetime.now().date():
                    messagebox.showerror("Error", "Cannot book appointments in the past!")
                    return
            except ValueError:
                messagebox.showerror("Error", "Invalid date format!")
                return
            self.cursor.execute("INSERT INTO appointments (owner, vehicle, service, date) VALUES (?, ?, ?, ?)", 
                              (username, vehicle, service, date))
            self.conn.commit()
            messagebox.showinfo("Success", "Appointment booked!")
            app_win.destroy()

        tk.Button(app_win, text="Book", command=book).pack()

    def track_repairs(self, username):
        self.cursor.execute("SELECT id, vehicle, service, status, date FROM appointments WHERE owner=?", (username,))
        repairs = self.cursor.fetchall()
        if repairs:
            repair_win = tk.Toplevel(self.root)
            repair_win.title("Repair Status")
            tree = ttk.Treeview(repair_win, columns=("ID", "Vehicle", "Service", "Status", "Date"), show="headings")
            tree.heading("ID", text="ID")
            tree.heading("Vehicle", text="Vehicle")
            tree.heading("Service", text="Service")
            tree.heading("Status", text="Status")
            tree.heading("Date", text="Date")
            for id_, veh, serv, stat, date in repairs:
                tree.insert("", "end", values=(id_, veh, serv, stat, date))
            tree.pack()
            def cancel_appointment():
                selected = tree.selection()
                if not selected:
                    messagebox.showerror("Error", "Select an appointment to cancel!")
                    return
                app_id = tree.item(selected[0])['values'][0]
                if messagebox.askyesno("Confirm", "Cancel this appointment?"):
                    self.cursor.execute("DELETE FROM appointments WHERE id=?", (app_id,))
                    self.conn.commit()
                    messagebox.showinfo("Success", "Appointment canceled!")
                    for item in tree.get_children():
                        tree.delete(item)
                    self.cursor.execute("SELECT id, vehicle, service, status, date FROM appointments WHERE owner=?", (username,))
                    for id_, veh, serv, stat, date in self.cursor.fetchall():
                        tree.insert("", "end", values=(id_, veh, serv, stat, date))
            tk.Button(repair_win, text="Cancel Selected Appointment", command=cancel_appointment).pack()
        else:
            messagebox.showinfo("Info", "No repair history found.")

    def view_spare_parts(self):
        parts_win = tk.Toplevel(self.root)
        parts_win.title("Spare Parts")
        tk.Label(parts_win, text="Filter by Brand").pack()
        brand_var = tk.StringVar(parts_win)
        brand_var.set("All")
        brands = ["All", "Toyota", "Lexus", "Land Rover", "BMW", "Mercedes", "Nissan", "Honda"]
        tk.OptionMenu(parts_win, brand_var, *brands).pack()
        tk.Label(parts_win, text="Sort by").pack()
        sort_var = tk.StringVar(parts_win)
        sort_var.set("Name")
        tk.OptionMenu(parts_win, sort_var, "Name", "Price", "Stock").pack()

        def update_parts():
            for item in tree.get_children():
                tree.delete(item)
            query = "SELECT part_name, price, stock FROM spare_parts"
            params = []
            if brand_var.get() != "All":
                query += " WHERE part_name LIKE ?"
                params.append(f"%{brand_var.get()}%")
            if sort_var.get() == "Price":
                query += " ORDER BY price"
            elif sort_var.get() == "Stock":
                query += " ORDER BY stock"
            else:
                query += " ORDER BY part_name"
            self.cursor.execute(query, params)
            parts = self.cursor.fetchall()
            for name, price, stock in parts:
                tree.insert("", "end", values=(name, f"KES {price:.2f}", stock))

        tk.Button(parts_win, text="Apply Filter/Sort", command=update_parts).pack()
        tree = ttk.Treeview(parts_win, columns=("Name", "Price", "Stock"), show="headings")
        tree.heading("Name", text="Name")
        tree.heading("Price", text="Price (KES)")
        tree.heading("Stock", text="Stock")
        update_parts()
        tree.pack()

    def view_recommendations(self, username):
        self.cursor.execute("SELECT model FROM vehicles WHERE owner=?", (username,))
        vehicles = [row[0] for row in self.cursor.fetchall()]
        if not vehicles:
            messagebox.showinfo("Info", "Register a vehicle to see recommendations!")
            return
        model = vehicles[0].split()[0]  # Get brand (e.g., "Toyota" from "Toyota Corolla")
        self.cursor.execute("SELECT part_name, price, stock FROM spare_parts WHERE part_name LIKE ?", (f"%{model}%",))
        parts = self.cursor.fetchall()
        if parts:
            rec_win = tk.Toplevel(self.root)
            rec_win.title("Recommended Parts")
            tk.Label(rec_win, text=f"Recommended Parts for {model}").pack()
            tree = ttk.Treeview(rec_win, columns=("Name", "Price", "Stock"), show="headings")
            tree.heading("Name", text="Name")
            tree.heading("Price", text="Price (KES)")
            tree.heading("Stock", text="Stock")
            for name, price, stock in parts:
                tree.insert("", "end", values=(name, f"KES {price:.2f}", stock))
            tree.pack()
        else:
            messagebox.showinfo("Info", f"No parts found for {model}!")

    def profile_window(self, username):
        prof_win = tk.Toplevel(self.root)
        prof_win.title("My Profile")
        tk.Label(prof_win, text="Update Contact Info").pack()
        tk.Label(prof_win, text="Email").pack()
        email_entry = tk.Entry(prof_win)
        email_entry.pack()
        tk.Label(prof_win, text="Phone").pack()
        phone_entry = tk.Entry(prof_win)
        phone_entry.pack()
        self.cursor.execute("SELECT email, phone FROM users WHERE username=?", (username,))
        email, phone = self.cursor.fetchone()
        email_entry.insert(0, email or "")
        phone_entry.insert(0, phone or "")

        def update_profile():
            new_email = email_entry.get().strip()
            new_phone = phone_entry.get().strip()
            self.cursor.execute("UPDATE users SET email=?, phone=? WHERE username=?", (new_email, new_phone, username))
            self.conn.commit()
            messagebox.showinfo("Success", "Profile updated!")
            prof_win.destroy()

        tk.Button(prof_win, text="Update", command=update_profile).pack()
        tk.Label(prof_win, text="Service History").pack()
        tree = ttk.Treeview(prof_win, columns=("ID", "Service", "Status", "Date"), show="headings")
        tree.heading("ID", text="ID")
        tree.heading("Service", text="Service")
        tree.heading("Status", text="Status")
        tree.heading("Date", text="Date")
        self.cursor.execute("SELECT id, service, status, date FROM appointments WHERE owner=?", (username,))
        for id_, serv, stat, date in self.cursor.fetchall():
            tree.insert("", "end", values=(id_, serv, stat, date))
        tree.pack()
        tk.Label(prof_win, text="Invoices").pack()
        inv_tree = ttk.Treeview(prof_win, columns=("ID", "Service", "Amount", "Status"), show="headings")
        inv_tree.heading("ID", text="ID")
        inv_tree.heading("Service", text="Service")
        inv_tree.heading("Amount", text="Amount (KES)")
        inv_tree.heading("Status", text="Status")
        self.cursor.execute("SELECT id, service, amount, status FROM invoices WHERE owner=?", (username,))
        for id_, serv, amt, stat in self.cursor.fetchall():
            inv_tree.insert("", "end", values=(id_, serv, f"KES {amt:.2f}", stat))
        inv_tree.pack()

        def export_history():
            self.cursor.execute("SELECT id, service, status, date FROM appointments WHERE owner=?", (username,))
            apps = self.cursor.fetchall()
            app_df = pd.DataFrame(apps, columns=["ID", "Service", "Status", "Date"])
            self.cursor.execute("SELECT id, service, amount, status FROM invoices WHERE owner=?", (username,))
            invs = self.cursor.fetchall()
            inv_df = pd.DataFrame(invs, columns=["ID", "Service", "Amount (KES)", "Status"])
            filename = f"service_history_{username}_{datetime.now().strftime('%Y%m%d')}.csv"
            app_df.to_csv(filename, mode='w', index=False)
            inv_df.to_csv(filename, mode='a', index=False)
            messagebox.showinfo("Success", f"History exported to {filename}")

        tk.Button(prof_win, text="Export History", command=export_history).pack()

    def view_mechanic_ratings(self):
        self.cursor.execute("SELECT mechanic, AVG(rating) as avg_rating FROM feedback GROUP BY mechanic")
        ratings = self.cursor.fetchall()
        if ratings:
            rate_win = tk.Toplevel(self.root)
            rate_win.title("Mechanic Ratings")
            tree = ttk.Treeview(rate_win, columns=("Mechanic", "Average Rating"), show="headings")
            tree.heading("Mechanic", text="Mechanic")
            tree.heading("Average Rating", text="Average Rating")
            for mech, avg_rate in ratings:
                tree.insert("", "end", values=(mech, f"{avg_rate:.1f}"))
            tree.pack()
        else:
            messagebox.showinfo("Info", "No feedback available.")

    def view_invoices(self, username):
        self.cursor.execute("SELECT id, service, amount, status FROM invoices WHERE owner=?", (username,))
        invoices = self.cursor.fetchall()
        if invoices:
            inv_win = tk.Toplevel(self.root)
            inv_win.title("Your Invoices")
            tree = ttk.Treeview(inv_win, columns=("ID", "Service", "Amount", "Status"), show="headings")
            tree.heading("ID", text="ID")
            tree.heading("Service", text="Service")
            tree.heading("Amount", text="Amount (KES)")
            tree.heading("Status", text="Status")
            for id_, serv, amt, stat in invoices:
                tree.insert("", "end", values=(id_, serv, f"KES {amt:.2f}", stat))
            tree.pack()
        else:
            messagebox.showinfo("Info", "No invoices found.")

    def pay_invoice(self, username):
        self.cursor.execute("SELECT id, service, amount, status FROM invoices WHERE owner=? AND status='Unpaid'", (username,))
        invoices = self.cursor.fetchall()
        if invoices:
            pay_win = tk.Toplevel(self.root)
            pay_win.title("Pay Invoice")
            tree = ttk.Treeview(pay_win, columns=("ID", "Service", "Amount", "Status"), show="headings")
            tree.heading("ID", text="ID")
            tree.heading("Service", text="Service")
            tree.heading("Amount", text="Amount (KES)")
            tree.heading("Status", text="Status")
            for id_, serv, amt, stat in invoices:
                tree.insert("", "end", values=(id_, serv, f"KES {amt:.2f}", stat))
            tree.pack()
            tk.Label(pay_win, text="Payment Method").pack()
            method_var = tk.StringVar(pay_win)
            method_var.set("Cash")
            tk.OptionMenu(pay_win, method_var, "Cash", "Mobile Money", "Bank Card").pack()
            tk.Label(pay_win, text="Payment Amount (KES)").pack()
            amount_entry = tk.Entry(pay_win)
            amount_entry.pack()
            tk.Label(pay_win, text="Transaction ID (Optional for Cash)").pack()
            trans_id_entry = tk.Entry(pay_win)
            trans_id_entry.pack()

            def pay_selected():
                selected = tree.selection()
                if not selected:
                    messagebox.showerror("Error", "Select an invoice to pay!")
                    return
                inv_id, _, inv_amount, _ = tree.item(selected[0])['values']
                method = method_var.get()
                try:
                    pay_amount = float(amount_entry.get().strip())
                    if pay_amount < inv_amount:
                        messagebox.showerror("Error", f"Payment amount (KES {pay_amount:.2f}) must be at least KES {inv_amount:.2f}!")
                        return
                except ValueError:
                    messagebox.showerror("Error", "Invalid payment amount!")
                    return
                trans_id = trans_id_entry.get().strip()
                if method in ["Mobile Money", "Bank Card"] and not trans_id:
                    messagebox.showerror("Error", "Transaction ID required for Mobile Money or Bank Card!")
                    return
                if messagebox.askyesno("Confirm", f"Pay KES {pay_amount:.2f} for invoice {inv_id} via {method}?"):
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.cursor.execute("UPDATE invoices SET status='Paid' WHERE id=?", (inv_id,))
                    self.cursor.execute("INSERT INTO payments (invoice_id, customer, amount, method, transaction_id, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                                      (inv_id, username, pay_amount, method, trans_id or None, timestamp))
                    self.conn.commit()
                    self.log_action(username, f"Paid invoice {inv_id} via {method}, amount KES {pay_amount:.2f}")
                    messagebox.showinfo("Success", "Payment recorded!")
                    self.feedback_window(username)  # Prompt for feedback after payment
                    for item in tree.get_children():
                        tree.delete(item)
                    self.cursor.execute("SELECT id, service, amount, status FROM invoices WHERE owner=? AND status='Unpaid'", (username,))
                    for id_, serv, amt, stat in self.cursor.fetchall():
                        tree.insert("", "end", values=(id_, serv, f"KES {amt:.2f}", stat))
                    if not tree.get_children():
                        messagebox.showinfo("Info", "No unpaid invoices left!")
                        pay_win.destroy()

            tk.Button(pay_win, text="Record Payment", command=pay_selected).pack()
        else:
            messagebox.showinfo("Info", "No unpaid invoices found.")

    def feedback_window(self, username):
        feedback_win = tk.Toplevel(self.root)
        feedback_win.title("Submit Feedback")
        tk.Label(feedback_win, text="Mechanic Name").pack()
        mechanic_entry = tk.Entry(feedback_win)
        mechanic_entry.pack()
        tk.Label(feedback_win, text="Rating (1-5)").pack()
        rating_entry = tk.Entry(feedback_win)
        rating_entry.pack()
        tk.Label(feedback_win, text="Comments").pack()
        comments_entry = tk.Entry(feedback_win)
        comments_entry.pack()

        def submit_feedback():
            mechanic = mechanic_entry.get().strip()
            try:
                rating = int(rating_entry.get().strip())
                if not 1 <= rating <= 5:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Rating must be 1-5!")
                return
            comments = comments_entry.get().strip()
            self.cursor.execute("INSERT INTO feedback (customer, mechanic, rating, comments) VALUES (?, ?, ?, ?)", 
                              (username, mechanic, rating, comments))
            self.conn.commit()
            messagebox.showinfo("Success", "Feedback submitted!")
            feedback_win.destroy()

        tk.Button(feedback_win, text="Submit", command=submit_feedback).pack()

    def view_appointments(self):
        app_win = tk.Toplevel(self.root)
        app_win.title("Appointments")
        tk.Label(app_win, text="Select Date").pack()
        cal = Calendar(app_win, selectmode="day", date_pattern="yyyy-mm-dd")
        cal.pack()

        def show_appointments():
            selected_date = cal.get_date()
            for item in tree.get_children():
                tree.delete(item)
            self.cursor.execute("SELECT id, owner, vehicle, service, status FROM appointments WHERE date=?", (selected_date,))
            for id_, own, veh, serv, stat in self.cursor.fetchall():
                tree.insert("", "end", values=(id_, own, veh, serv, stat))

        tk.Button(app_win, text="Show Appointments", command=show_appointments).pack()
        tree = ttk.Treeview(app_win, columns=("ID", "Owner", "Vehicle", "Service", "Status"), show="headings")
        tree.heading("ID", text="ID")
        tree.heading("Owner", text="Owner")
        tree.heading("Vehicle", text="Vehicle")
        tree.heading("Service", text="Service")
        tree.heading("Status", text="Status")
        tree.pack()

    def update_repair_status(self, username, staff_role):
        up_win = tk.Toplevel(self.root)
        up_win.title("Update Repair Status")
        tk.Label(up_win, text="Appointment ID").pack()
        id_entry = tk.Entry(up_win)
        id_entry.pack()
        tk.Label(up_win, text="New Status (e.g., In Progress, Completed)").pack()
        status_entry = tk.Entry(up_win)
        status_entry.pack()
        tk.Label(up_win, text="Invoice Amount in KES (if Completed)").pack()
        amount_entry = tk.Entry(up_win)
        amount_entry.pack()
        tk.Label(up_win, text="Spare Parts Used (if Completed)").pack()
        parts_tree = ttk.Treeview(up_win, columns=("ID", "Name", "Quantity"), show="headings")
        parts_tree.heading("ID", text="ID")
        parts_tree.heading("Name", text="Name")
        parts_tree.heading("Quantity", text="Quantity")
        self.cursor.execute("SELECT id, part_name, stock FROM spare_parts WHERE stock > 0")
        parts = self.cursor.fetchall()
        for id_, name, stock in parts:
            parts_tree.insert("", "end", values=(id_, name, 0))
        parts_tree.pack()

        def update():
            try:
                app_id = int(id_entry.get().strip())
            except ValueError:
                messagebox.showerror("Error", "Invalid ID!")
                return
            status = status_entry.get().strip()
            if not status:
                messagebox.showerror("Error", "Status required!")
                return
            # Collect parts used
            parts_used = []
            total_parts_cost = 0
            for item in parts_tree.get_children():
                part_id, _, qty = parts_tree.item(item)['values']
                try:
                    qty = int(qty)
                    if qty < 0:
                        raise ValueError
                except ValueError:
                    messagebox.showerror("Error", f"Invalid quantity for part ID {part_id}!")
                    return
                if qty > 0:
                    self.cursor.execute("SELECT stock, price FROM spare_parts WHERE id=?", (part_id,))
                    stock, price = self.cursor.fetchone()
                    if qty > stock:
                        messagebox.showerror("Error", f"Not enough stock for part ID {part_id}!")
                        return
                    parts_used.append((app_id, part_id, qty))
                    total_parts_cost += price * qty
            self.cursor.execute("UPDATE appointments SET status=? WHERE id=?", (status, app_id))
            if status == "Completed":
                try:
                    amount = float(amount_entry.get().strip())
                    if amount < 0:
                        messagebox.showerror("Error", "Amount cannot be negative!")
                        return
                    amount += total_parts_cost  # Add parts cost to invoice
                except ValueError:
                    messagebox.showerror("Error", "Invalid amount!")
                    return
                self.cursor.execute("SELECT owner, service FROM appointments WHERE id=?", (app_id,))
                result = self.cursor.fetchone()
                if result:
                    owner, service = result
                    self.cursor.execute("INSERT INTO invoices (owner, service, amount) VALUES (?, ?, ?)", (owner, service, amount))
                    # Update stock and log parts usage
                    for app_id, part_id, qty in parts_used:
                        self.cursor.execute("UPDATE spare_parts SET stock = stock - ? WHERE id=?", (qty, part_id))
                        self.cursor.execute("INSERT INTO parts_usage (appointment_id, part_id, quantity) VALUES (?, ?, ?)", 
                                          (app_id, part_id, qty))
                    self.conn.commit()
                    self.log_action(username, f"Updated appointment {app_id} to status {status}, used parts: {parts_used}")
                else:
                    messagebox.showerror("Error", "Invalid appointment ID!")
                    return
            else:
                self.conn.commit()
                self.log_action(username, f"Updated appointment {app_id} to status {status}")
            messagebox.showinfo("Success", "Status updated!")
            up_win.destroy()

        def edit_quantity(event):
            selected = parts_tree.selection()
            if not selected:
                return
            part_id = parts_tree.item(selected[0])['values'][0]
            qty_win = tk.Toplevel(up_win)
            qty_win.title("Set Quantity")
            tk.Label(qty_win, text="Quantity").pack()
            qty_entry = tk.Entry(qty_win)
            qty_entry.pack()
            def save_qty():
                try:
                    qty = int(qty_entry.get().strip())
                    if qty < 0:
                        messagebox.showerror("Error", "Invalid quantity!")
                        return
                except ValueError:
                    messagebox.showerror("Error", "Invalid quantity!")
                    return
                parts_tree.item(selected, values=(part_id, parts_tree.item(selected)['values'][1], qty))
                qty_win.destroy()
            tk.Button(qty_win, text="Save", command=save_qty).pack()

        parts_tree.bind("<Double-1>", edit_quantity)
        tk.Button(up_win, text="Update", command=update).pack()

    def manage_spare_parts(self, username):
        man_win = tk.Toplevel(self.root)
        man_win.title("Manage Spare Parts")
        tk.Label(man_win, text="Part Name").pack()
        name_entry = tk.Entry(man_win)
        name_entry.pack()
        tk.Label(man_win, text="Price (KES)").pack()
        price_entry = tk.Entry(man_win)
        price_entry.pack()
        tk.Label(man_win, text="Stock").pack()
        stock_entry = tk.Entry(man_win)
        stock_entry.pack()

        def add_part():
            name = name_entry.get().strip()
            try:
                price = float(price_entry.get().strip())
                stock = int(stock_entry.get().strip())
                if price < 0 or stock < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Price and stock must be non-negative numbers!")
                return
            self.cursor.execute("INSERT INTO spare_parts (part_name, price, stock) VALUES (?, ?, ?)", (name, price, stock))
            self.conn.commit()
            self.log_action(username, f"Added part {name}")
            messagebox.showinfo("Success", "Part added!")
            update_table()

        tk.Button(man_win, text="Add Part", command=add_part).pack()
        tk.Label(man_win, text="Low Stock Alerts (Stock < 5)", fg="red").pack()

        tree = ttk.Treeview(man_win, columns=("ID", "Name", "Price", "Stock"), show="headings")
        tree.heading("ID", text="ID")
        tree.heading("Name", text="Name")
        tree.heading("Price", text="Price (KES)")
        tree.heading("Stock", text="Stock")
        tree.pack()

        def update_table():
            for item in tree.get_children():
                tree.delete(item)
            self.cursor.execute("SELECT id, part_name, price, stock FROM spare_parts")
            low_stock = []
            for id_, name, price, stock in self.cursor.fetchall():
                tree.insert("", "end", values=(id_, name, f"KES {price:.2f}", stock))
                if stock < 5:
                    low_stock.append(name)
            if low_stock:
                messagebox.showwarning("Low Stock Alert", f"Re-order parts: {', '.join(low_stock)}")

        def edit_part():
            selected = tree.selection()
            if not selected:
                messagebox.showerror("Error", "Select a part to edit!")
                return
            part_id = tree.item(selected[0])['values'][0]
            edit_win = tk.Toplevel(man_win)
            edit_win.title("Edit Part")
            tk.Label(edit_win, text="Part Name").pack()
            name_entry = tk.Entry(edit_win)
            name_entry.pack()
            tk.Label(edit_win, text="Price (KES)").pack()
            price_entry = tk.Entry(edit_win)
            price_entry.pack()
            tk.Label(edit_win, text="Stock").pack()
            stock_entry = tk.Entry(edit_win)
            stock_entry.pack()
            self.cursor.execute("SELECT part_name, price, stock FROM spare_parts WHERE id=?", (part_id,))
            name, price, stock = self.cursor.fetchone()
            name_entry.insert(0, name)
            price_entry.insert(0, price)
            stock_entry.insert(0, stock)
            def save_edit():
                try:
                    new_price = float(price_entry.get().strip())
                    new_stock = int(stock_entry.get().strip())
                    if new_price < 0 or new_stock < 0:
                        raise ValueError
                except ValueError:
                    messagebox.showerror("Error", "Price and stock must be non-negative numbers!")
                    return
                new_name = name_entry.get().strip()
                self.cursor.execute("UPDATE spare_parts SET part_name=?, price=?, stock=? WHERE id=?", 
                                  (new_name, new_price, new_stock, part_id))
                self.conn.commit()
                self.log_action(username, f"Edited part {new_name}")
                messagebox.showinfo("Success", "Part updated!")
                update_table()
                edit_win.destroy()
            tk.Button(edit_win, text="Save", command=save_edit).pack()

        def delete_part():
            selected = tree.selection()
            if not selected:
                messagebox.showerror("Error", "Select a part to delete!")
                return
            part_id = tree.item(selected[0])['values'][0]
            self.cursor.execute("SELECT part_name FROM spare_parts WHERE id=?", (part_id,))
            part_name = self.cursor.fetchone()[0]
            if messagebox.askyesno("Confirm", "Delete this part?"):
                self.cursor.execute("DELETE FROM spare_parts WHERE id=?", (part_id,))
                self.conn.commit()
                self.log_action(username, f"Deleted part {part_name}")
                messagebox.showinfo("Success", "Part deleted!")
                update_table()

        tk.Button(man_win, text="Edit Selected Part", command=edit_part).pack()
        tk.Button(man_win, text="Delete Selected Part", command=delete_part).pack()
        update_table()

    def generate_reports(self):
        rep_win = tk.Toplevel(self.root)
        rep_win.title("Generate Reports")
        tk.Label(rep_win, text="Start Date").pack()
        start_cal = Calendar(rep_win, selectmode="day", date_pattern="yyyy-mm-dd")
        start_cal.pack()
        tk.Label(rep_win, text="End Date").pack()
        end_cal = Calendar(rep_win, selectmode="day", date_pattern="yyyy-mm-dd")
        end_cal.pack()

        def export_report():
            start_date = start_cal.get_date()
            end_date = end_cal.get_date()
            # Appointments report
            self.cursor.execute("SELECT id, owner, vehicle, service, status, date FROM appointments WHERE date BETWEEN ? AND ?", 
                              (start_date, end_date))
            apps = self.cursor.fetchall()
            app_df = pd.DataFrame(apps, columns=["ID", "Owner", "Vehicle", "Service", "Status", "Date"])
            # Invoices report
            self.cursor.execute("SELECT id, owner, service, amount, status FROM invoices WHERE EXISTS (SELECT 1 FROM appointments WHERE appointments.owner=invoices.owner AND appointments.date BETWEEN ? AND ?)", 
                              (start_date, end_date))
            invs = self.cursor.fetchall()
            inv_df = pd.DataFrame(invs, columns=["ID", "Owner", "Service", "Amount (KES)", "Status"])
            # Payments report
            self.cursor.execute("SELECT id, invoice_id, customer, amount, method, transaction_id, timestamp FROM payments WHERE timestamp BETWEEN ? AND ?",
                              (start_date, end_date))
            pays = self.cursor.fetchall()
            pay_df = pd.DataFrame(pays, columns=["ID", "Invoice ID", "Customer", "Amount (KES)", "Method", "Transaction ID", "Timestamp"])
            # Export to CSV
            filename = f"garage_report_{start_date}_to_{end_date}.csv"
            app_df.to_csv(filename, mode='w', index=False)
            inv_df.to_csv(filename, mode='a', index=False)
            pay_df.to_csv(filename, mode='a', index=False)
            messagebox.showinfo("Success", f"Report saved as {filename}")

        tk.Button(rep_win, text="Export Report", command=export_report).pack()

    def performance_dashboard(self):
        perf_win = tk.Toplevel(self.root)
        perf_win.title("Performance Dashboard")
        tk.Label(perf_win, text="Mechanic Performance", font=("Arial", 12, "bold")).pack()
        # Completed appointments per mechanic
        self.cursor.execute("""
            SELECT u.username, COUNT(a.id) as completed
            FROM users u
            LEFT JOIN appointments a ON u.username = a.owner AND a.status = 'Completed'
            WHERE u.role = 'Staff' AND u.staff_role = 'Mechanic'
            GROUP BY u.username
        """)
        completions = self.cursor.fetchall()
        tk.Label(perf_win, text="Completed Appointments").pack()
        comp_tree = ttk.Treeview(perf_win, columns=("Mechanic", "Completed"), show="headings")
        comp_tree.heading("Mechanic", text="Mechanic")
        comp_tree.heading("Completed", text="Completed Appointments")
        for mech, count in completions:
            comp_tree.insert("", "end", values=(mech, count))
        comp_tree.pack()
        # Average ratings
        self.cursor.execute("SELECT mechanic, AVG(rating) as avg_rating FROM feedback GROUP BY mechanic")
        ratings = self.cursor.fetchall()
        tk.Label(perf_win, text="Average Ratings").pack()
        rate_tree = ttk.Treeview(perf_win, columns=("Mechanic", "Average Rating"), show="headings")
        rate_tree.heading("Mechanic", text="Mechanic")
        rate_tree.heading("Average Rating", text="Average Rating")
        for mech, avg_rate in ratings:
            rate_tree.insert("", "end", values=(mech, f"{avg_rate:.1f}"))
        rate_tree.pack()

    def view_payments(self):
        self.cursor.execute("SELECT id, invoice_id, customer, amount, method, transaction_id, timestamp FROM payments")
        payments = self.cursor.fetchall()
        if payments:
            pay_win = tk.Toplevel(self.root)
            pay_win.title("Payment History")
            tree = ttk.Treeview(pay_win, columns=("ID", "Invoice ID", "Customer", "Amount", "Method", "Transaction ID", "Timestamp"), show="headings")
            tree.heading("ID", text="ID")
            tree.heading("Invoice ID", text="Invoice ID")
            tree.heading("Customer", text="Customer")
            tree.heading("Amount", text="Amount (KES)")
            tree.heading("Method", text="Method")
            tree.heading("Transaction ID", text="Transaction ID")
            tree.heading("Timestamp", text="Timestamp")
            for id_, inv_id, cust, amt, meth, trans_id, time in payments:
                tree.insert("", "end", values=(id_, inv_id, cust, f"KES {amt:.2f}", meth, trans_id or "N/A", time))
            tree.pack()
        else:
            messagebox.showinfo("Info", "No payments recorded.")

    def view_logs(self):
        self.cursor.execute("SELECT id, staff_username, action, timestamp FROM logs")
        logs = self.cursor.fetchall()
        if logs:
            log_win = tk.Toplevel(self.root)
            log_win.title("Audit Logs")
            tree = ttk.Treeview(log_win, columns=("ID", "Staff", "Action", "Timestamp"), show="headings")
            tree.heading("ID", text="ID")
            tree.heading("Staff", text="Staff")
            tree.heading("Action", text="Action")
            tree.heading("Timestamp", text="Timestamp")
            for id_, staff, action, time in logs:
                tree.insert("", "end", values=(id_, staff, action, time))
            tree.pack()
        else:
            messagebox.showinfo("Info", "No logs available.")

    def view_feedback(self):
        self.cursor.execute("SELECT customer, mechanic, rating, comments FROM feedback")
        feeds = self.cursor.fetchall()
        if feeds:
            feed_win = tk.Toplevel(self.root)
            feed_win.title("Feedback")
            tree = ttk.Treeview(feed_win, columns=("Customer", "Mechanic", "Rating", "Comments"), show="headings")
            tree.heading("Customer", text="Customer")
            tree.heading("Mechanic", text="Mechanic")
            tree.heading("Rating", text="Rating")
            tree.heading("Comments", text="Comments")
            for cust, mech, rate, comm in feeds:
                tree.insert("", "end", values=(cust, mech, rate, comm))
            tree.pack()
        else:
            messagebox.showinfo("Info", "No feedback.")

if __name__ == "__main__":
    root = tk.Tk()
    app = GarageApp(root)
    root.mainloop()
    # To run: cd C:\Users\A-C-T\Desktop\Python projects
    # pip install bcrypt pandas tkcalendar
    # python garage_4.py
    # Ian Mugambi - Admin pass - 18895
    # Bob - Client pass - 123
    # Alice - Mechanic pass 123