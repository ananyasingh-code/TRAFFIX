
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import random
from functools import wraps

app = Flask(__name__)
app.secret_key = "traffix_dev_secret_change_later"

# Database Setup
def init_db():
    conn = sqlite3.connect("traffix.db")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location TEXT NOT NULL,
            issue_type TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT DEFAULT 'Pending'
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    admin = conn.execute(
        "SELECT id FROM users WHERE email = ?",
        ("admin@traffix.com",)
    ).fetchone()

    if admin is None:
        conn.execute("""
            INSERT INTO users (username, email, password, role)
            VALUES (?, ?, ?, ?)
        """, (
            "Admin",
            "admin@traffix.com",
            generate_password_hash("Admin@123"),
            "admin"
        ))

    conn.commit()
    conn.close()

# Login Protection
def login_required(role):

    def decorator(function):

        @wraps(function)
        def wrapper(*args, **kwargs):

            if "user_id" not in session or session.get("role") != role:
                flash("Please log in to access this page.")
                return redirect(url_for(f"{role}_login"))

            return function(*args, **kwargs)

        return wrapper

    return decorator


    # TRAFFIC SIMULATION ENGINE

def calculate_density(vehicle_count):

    if vehicle_count <= 10:
        return "Low"

    elif vehicle_count <= 25:
        return "Moderate"

    else:
        return "High"

    # Generate Traffic for Four Directions

def simulate_traffic():

    traffic = {}

    directions = ["North", "South", "East", "West"]

    for direction in directions:

        vehicles = random.randint(1, 40)

        density = calculate_density(vehicles)

        traffic[direction] = {
            "vehicles": vehicles,
            "density": density,
            "green_time": calculate_signal_time(density)
        }

    return traffic

# Calculate Adaptive Signal Timing

def calculate_signal_time(density):

    if density == "Low":
        return 15

    elif density == "Moderate":
        return 30

    else:
        return 45

    # Select Direction with Highest Traffic

def select_next_green(traffic):

    next_direction = max(
        traffic,
        key=lambda direction: traffic[direction]["vehicles"]
    )

    return next_direction

# Home Page
@app.route("/")
def home():
    return render_template("index.html")


# User Login
@app.route("/user/login", methods=["GET", "POST"])
def user_login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        conn = sqlite3.connect("traffix.db")
        conn.row_factory = sqlite3.Row

        user = conn.execute(
            "SELECT * FROM users WHERE email = ? AND role = ?",
            (email, "user")
        ).fetchone()

        conn.close()

        if user and check_password_hash(user["password"], password):

            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]

            return redirect(url_for("user_dashboard"))

        flash("Invalid user email or password.")

    return render_template("user_login.html")

# User Registration
@app.route("/user/register", methods=["GET", "POST"])
def user_register():

    if request.method == "POST":

        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        if not username or not email or not password:
            flash("Please fill in all fields.")
            return redirect(url_for("user_register"))

        if len(password) < 8:
            flash("Password must contain at least 8 characters.")
            return redirect(url_for("user_register"))

        conn = sqlite3.connect("traffix.db")

        existing_user = conn.execute(
            "SELECT id FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        if existing_user:
            conn.close()
            flash("An account with this email already exists.")
            return redirect(url_for("user_register"))

        conn.execute("""
            INSERT INTO users (username, email, password, role)
            VALUES (?, ?, ?, ?)
        """, (
            username,
            email,
            generate_password_hash(password),
            "user"
        ))

        conn.commit()
        conn.close()

        flash("Registration successful! Please log in.")
        return redirect(url_for("user_login"))

    return render_template("user_register.html")


# User Dashboard
@app.route("/user/dashboard")
@login_required("user")
def user_dashboard():

    traffic = simulate_traffic()

    next_green = select_next_green(traffic)

    green_duration = traffic[next_green]["green_time"]

    return render_template(
        "user_dashboard.html",
        traffic=traffic,
        next_green=next_green,
        green_duration=green_duration
    )

# Traffic Simulation Page
@app.route("/simulation")
def simulation():

    traffic = simulate_traffic()

    next_green = select_next_green(traffic)

    green_duration = traffic[next_green]["green_time"]

    return render_template(
        "simulation.html",
        traffic=traffic,
        next_green=next_green,
        green_duration=green_duration
    )


# Traffic Data API
@app.route("/api/traffic")
def traffic_api():

    traffic = simulate_traffic()

    next_green = select_next_green(traffic)

    green_duration = traffic[next_green]["green_time"]

    return jsonify({
        "traffic": traffic,
        "next_green": next_green,
        "green_duration": green_duration
    })


# Submit Traffic Report
@app.route("/submit-report", methods=["POST"])
@login_required("user")
def submit_report():

    location = request.form.get("location")
    issue_type = request.form.get("issue_type")
    description = request.form.get("description")

    conn = sqlite3.connect("traffix.db")

    conn.execute("""
        INSERT INTO reports (location, issue_type, description)
        VALUES (?, ?, ?)
    """, (location, issue_type, description))

    conn.commit()
    conn.close()

    return redirect(url_for("user_dashboard"))


# Admin Login
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        conn = sqlite3.connect("traffix.db")
        conn.row_factory = sqlite3.Row

        admin = conn.execute(
            "SELECT * FROM users WHERE email = ? AND role = ?",
            (email, "admin")
        ).fetchone()

        conn.close()

        if admin and check_password_hash(admin["password"], password):

            session["user_id"] = admin["id"]
            session["username"] = admin["username"]
            session["role"] = admin["role"]

            return redirect(url_for("admin_dashboard"))

        flash("Invalid admin email or password.")

    return render_template("admin_login.html")


# Admin Dashboard
@app.route("/admin/dashboard")
@login_required("admin")
def admin_dashboard():

    traffic = simulate_traffic()

    next_green = select_next_green(traffic)

    green_duration = traffic[next_green]["green_time"]

    conn = sqlite3.connect("traffix.db")
    conn.row_factory = sqlite3.Row

    reports = conn.execute(
        "SELECT * FROM reports ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return render_template(
        "admin_dashboard.html",
        reports=reports,
        traffic=traffic,
        next_green=next_green,
        green_duration=green_duration
    )


# Update Report Status
@app.route("/update-report/<int:report_id>", methods=["POST"])
@login_required("admin")
def update_report(report_id):

    status = request.form.get("status")

    if status not in ["Pending", "Resolved"]:
        return "Invalid status", 400

    conn = sqlite3.connect("traffix.db")

    conn.execute(
        "UPDATE reports SET status = ? WHERE id = ?",
        (status, report_id)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("admin_dashboard"))

# Logout
@app.route("/logout")
def logout():

    session.clear()

    flash("You have been logged out successfully.")

    return redirect(url_for("home"))

init_db()

if __name__ == "__main__":
    
    app.run(debug=True)