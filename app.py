from flask import Flask, render_template, request, redirect, flash, session, send_from_directory, jsonify, url_for
import sqlite3
import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import plotly.graph_objects as go
import plotly.io as py
from flask_mail import Mail, Message
import csv

# =====================================================
#  Flask Setup
# =====================================================
app = Flask(__name__)
app.secret_key = os.urandom(24)

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# =====================================================
#  Email Setup (Gmail SMTP)
# =====================================================
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = "emediongedoho1@gmail.com"     # your Gmail
app.config['MAIL_PASSWORD'] = "dxwajrsipzydmutp"             # your App password
app.config['MAIL_DEFAULT_SENDER'] = ("Elite Trader Journal", "emediongedoho1@gmail.com")
mail = Mail(app)

# =====================================================
#  Helpers
# =====================================================
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        email TEXT UNIQUE,
        password TEXT,
        is_admin INTEGER DEFAULT 0
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        pair TEXT,
        result TEXT,
        entry FLOAT,
        exit FLOAT,
        notes TEXT,
        screenshot TEXT,
        date TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    conn.commit()

    # ✅ Automatically create default admin if not exists
    cursor.execute("SELECT * FROM users WHERE is_admin=1")
    admin_exists = cursor.fetchone()
    if not admin_exists:
        hashed_password = generate_password_hash("admin123")  # default admin password
        cursor.execute("INSERT INTO users (username, email, password, is_admin) VALUES (?, ?, ?, ?)",
                       ("admin", "emediongedoho1@gmail.com", hashed_password, 1))
        conn.commit()
        

    conn.close()

@app.context_processor
def inject_user():
    return dict(session=session)

# =====================================================
#  Home
# =====================================================
@app.route('/')
def home():
    return render_template("index.html")

# =====================================================
#  Register
# =====================================================
@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        hashed_password = generate_password_hash(password)

        conn = sqlite3.connect("database.db")
        try:
            conn.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                         (username, email, hashed_password))
            conn.commit()
            conn.close()

            # Save email to CSV
            file_exists = os.path.isfile("emails.csv")
            with open("emails.csv", mode="a", newline="") as file:
                writer = csv.writer(file)
                if not file_exists:
                    writer.writerow(["Username", "Email"])
                writer.writerow([username, email])

            # Send welcome email
            msg_user = Message("Welcome to EliteTrader Journal!", recipients=[email])
            msg_user.html = f"""
            <h2>Welcome to EliteTrader Journal, {username}!</h2>

            <p>We’re thrilled to have you join our trading community! 🎉</p>

            <p>You’ve just taken a powerful step toward becoming a more disciplined, 
            consistent, and successful trader. With your new journal, you’ll be able to:</p>

            <ul>
            <li>✅ Track every trade with precision</li>
            <li>✅ Analyze your performance over time</li>
            <li>✅ Refine your strategy for better results</li>
            <li>✅ Stay accountable to your trading goals</li>
            </ul>

            <p>At <b>EliteTrader Journal</b>, we believe trading isn’t just about the markets 
            it’s about mastering yourself. Every note you take, every trade you review, and every
            lesson you record will bring you closer to trading excellence.</p>


            <p>Thank you for trusting us to be part of your trading growth. Here’s to sharper
            decisions and stronger results ahead! 🚀</p>

            <p>Trade smart,<br>
            The EliteTrader Journal Team</p>
            """
            mail.send(msg_user)

            # Notify admin
            msg_admin = Message(f"New Registration: {username}", recipients=[app.config['MAIL_USERNAME']])
            msg_admin.body = f"""
            Hello Admin,

            A new user has just registered on EliteTrader Journal.

            Username: {username}
            Email: {email}

            You can now review their account or welcome them if necessary.

            Best regards,
            Elite Trader Journal System
            """

            mail.send(msg_admin)

            flash("Registration successful! Check your email.", "success")
            return redirect("/login")

        except sqlite3.IntegrityError:
            flash("Email already exists.", "danger")
            conn.close()

    return render_template("register.html")

# =====================================================
#  Login
# =====================================================
@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email, password FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[3], password):
            session["user_id"] = user[0]
            session["username"] = user[1]
            flash("Login successful!", "success")
            return redirect("/dashboard")
        else:
            flash("Invalid credentials.", "danger")
    return render_template("login.html")

# =====================================================
#  Dashboard
# =====================================================
@app.route('/dashboard')
def dashboard():
    if "user_id" not in session:
        flash("You must log in first.", "warning")
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT pair, result, entry, exit, notes, screenshot, date FROM trades WHERE user_id = ?",
                   (session["user_id"],))
    trades = cursor.fetchall()

    win_loss = [1 if trade[1].lower() == 'win' else 0 for trade in trades]
    win_count = win_loss.count(1)
    loss_count = win_loss.count(0)

    fig = go.Figure(data=[
        go.Bar(name="Wins", x=["Wins"], y=[win_count], marker=dict(color="green")),
        go.Bar(name="Losses", x=["Losses"], y=[loss_count], marker=dict(color="red"))
    ])
    fig.update_layout(
        title="Your Performance (Win/Loss)",
        xaxis_title="Outcome",
        yaxis_title="Count",
        barmode='group'
    )

    graph = py.to_html(fig, full_html=False)
    conn.close()
    return render_template("dashboard.html", trades=trades, graph=graph)

# =====================================================
#  Log Trade
# =====================================================
@app.route('/log_trade', methods=["GET", "POST"])
def log_trade():
    if "user_id" not in session:
        flash("You must log in first.", "warning")
        return redirect("/login")

    if request.method == "POST":
        pair = request.form["pair"]
        result = request.form["result"]
        entry = float(request.form["entry"])
        exit_price = float(request.form["exit"])
        notes = request.form["notes"]
        screenshot_filename = None
        date = request.form["date"]

        if "screenshot" in request.files:
            file = request.files["screenshot"]
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                screenshot_filename = filename

        conn = sqlite3.connect("database.db")
        conn.execute("""INSERT INTO trades 
            (user_id, pair, result, entry, exit, notes, screenshot, date) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (session["user_id"], pair, result, entry, exit_price, notes, screenshot_filename, date))
        conn.commit()
        conn.close()

        flash("Trade logged successfully!", "success")
        return redirect("/dashboard")

    return render_template("log_trade.html")

# =====================================================
#  Trade Metadata API
# =====================================================
@app.route('/api/trade_metadata/<pair>_<date>.json')
def trade_metadata(pair, date):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT pair, result, entry, exit, notes, screenshot, date FROM trades WHERE pair = ? AND date = ?",
                   (pair, date))
    trade = cursor.fetchone()
    conn.close()

    if not trade:
        return jsonify({"error": "Trade not found"}), 404

    metadata = {
        "name": f"Trade: {trade[0]} ({trade[6]})",
        "description": f"Result: {trade[1]}, Entry: {trade[2]}, Exit: {trade[3]}, Notes: {trade[4]}",
        "image": f"/uploads/{trade[5]}" if trade[5] else "",
        "attributes": [
            {"trait_type": "Pair", "value": trade[0]},
            {"trait_type": "Result", "value": trade[1]},
            {"trait_type": "Entry", "value": trade[2]},
            {"trait_type": "Exit", "value": trade[3]},
            {"trait_type": "Date", "value": trade[6]}
        ]
    }
    return jsonify(metadata)

# =====================================================
#  Logout
# =====================================================
@app.route('/logout', methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect("/")

# =====================================================
#  Admin Login
# =====================================================
@app.route('/admin_login', methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email, password, is_admin FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[3], password) and user[4] == 1:
            session["admin_id"] = user[0]
            session["admin_username"] = user[1]
            flash("Admin login successful!", "success")
            # Redirect admin straight to bulk email page
            return redirect("/bulk_email")
        else:
            flash("Invalid admin credentials.", "danger")
    return render_template("admin_login.html")

# =====================================================
#  Bulk Email (Admin Only)
# =====================================================
@app.route('/bulk_email', methods=["GET", "POST"])
def bulk_email():
    if "admin_id" not in session:
        flash("You must log in as admin first.", "warning")
        return redirect("/admin_login")

    if request.method == "POST":
        subject = request.form["subject"]
        body = request.form["body"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM users")
        users = cursor.fetchall()
        conn.close()

        recipients = [u[0] for u in users]

        if recipients:
            msg = Message(subject, recipients=recipients)
            msg.html = body
            mail.send(msg)
            flash("Bulk email sent successfully ✅", "success")
        else:
            flash("No users found to send email.", "warning")

        return redirect("/bulk_email")

    return render_template("bulk_email.html")

# =====================================================
#  Admin Dashboard
# =====================================================
@app.route('/admin_dashboard')
def admin_dashboard():
    if "admin_id" not in session:
        flash("You must log in as admin first.", "warning")
        return redirect("/admin_login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, is_admin FROM users")
    users = cursor.fetchall()
    cursor.execute("SELECT * FROM trades")
    trades = cursor.fetchall()
    conn.close()

    return render_template("admin_dashboard.html", users=users, trades=trades)

# =====================================================
#  Admin Logout
# =====================================================
@app.route('/admin_logout', methods=["POST"])
def admin_logout():
    session.pop("admin_id", None)
    session.pop("admin_username", None)
    flash("Admin logged out.", "info")
    return redirect("/admin_login")

# =====================================================
#  Uploads
# =====================================================
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# =====================================================
#  Run App
# =====================================================
if __name__ == '__main__':
    init_db()  # This will create default admin if none exists
    app.run(debug=True)
