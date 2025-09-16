# from flask import Flask, render_template, request, redirect, flash, session, send_from_directory, jsonify
# import sqlite3
# import os
# from werkzeug.utils import secure_filename
# from werkzeug.security import generate_password_hash, check_password_hash
# import plotly.graph_objects as go
# import plotly.io as py

# # =====================================================
# #  NFT Minting imports (COMMENTED OUT FOR NOW)
# # =====================================================
# # from web3 import Web3
# # from dotenv import load_dotenv
# # import json

# # # Load environment variables
# # load_dotenv()

# # # Web3 setup
# # w3 = Web3(Web3.HTTPProvider(os.getenv("WEB3_PROVIDER")))
# # private_key = os.getenv("PRIVATE_KEY")
# # wallet_address = os.getenv("WALLET_ADDRESS")
# # contract_address = os.getenv("CONTRACT_ADDRESS")

# # with open("nft_abi.json") as f:
# #     abi = json.load(f)

# # contract = w3.eth.contract(address=contract_address, abi=abi)

# # def mint_trade_nft(to_address, token_uri):
# #     nonce = w3.eth.get_transaction_count(wallet_address)
# #     txn = contract.functions.safeMint(to_address, token_uri).build_transaction({
# #         'from': wallet_address,
# #         'nonce': nonce,
# #         'gas': 300000,
# #         'gasPrice': w3.to_wei('50', 'gwei')
# #     })
# #     signed_txn = w3.eth.account.sign_transaction(txn, private_key=private_key)
# #     tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
# #     return w3.to_hex(tx_hash)

# # =====================================================
# #  Flask Setup
# # =====================================================
# app = Flask(__name__)
# app.secret_key = os.urandom(24)

# UPLOAD_FOLDER = 'static/uploads'
# ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# def allowed_file(filename):
#     return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# def init_db():
#     conn = sqlite3.connect("database.db")
#     cursor = conn.cursor()
#     cursor.execute('''CREATE TABLE IF NOT EXISTS users (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         username TEXT,
#         email TEXT UNIQUE,
#         password TEXT
#     )''')
#     cursor.execute('''CREATE TABLE IF NOT EXISTS trades (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         user_id INTEGER,
#         pair TEXT,
#         result TEXT,
#         entry FLOAT,
#         exit FLOAT,
#         notes TEXT,
#         screenshot TEXT,
#         date TEXT,
#         FOREIGN KEY(user_id) REFERENCES users(id)
#     )''')
#     conn.commit()
#     conn.close()


# @app.context_processor
# def inject_user():
#     return dict(session=session)


# @app.route('/')
# def home():
#     return render_template("base.html")


# @app.route('/register', methods=["GET", "POST"])
# def register():
#     if request.method == "POST":
#         username = request.form["username"]
#         email = request.form["email"]
#         password = request.form["password"]
#         hashed_password = generate_password_hash(password)

#         conn = sqlite3.connect("database.db")
#         try:
#             conn.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
#                          (username, email, hashed_password))
#             conn.commit()
#             flash("Registration successful!", "success")
#             return redirect("/login")
#         except sqlite3.IntegrityError:
#             flash("Email already exists.", "danger")
#         finally:
#             conn.close()
#     return render_template("register.html")


# @app.route('/login', methods=["GET", "POST"])
# def login():
#     if request.method == "POST":
#         email = request.form["email"]
#         password = request.form["password"]

#         conn = sqlite3.connect("database.db")
#         cursor = conn.cursor()
#         cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
#         user = cursor.fetchone()
#         conn.close()

#         if user and check_password_hash(user[3], password):
#             session["user_id"] = user[0]
#             session["username"] = user[1]
#             flash("Login successful!", "success")
#             return redirect("/dashboard")
#         else:
#             flash("Invalid credentials.", "danger")
#     return render_template("login.html")


# @app.route('/dashboard')
# def dashboard():
#     if "user_id" not in session:
#         flash("You must log in first.", "warning")
#         return redirect("/login")

#     conn = sqlite3.connect("database.db")
#     cursor = conn.cursor()
#     cursor.execute("SELECT pair, result, entry, exit, notes, screenshot, date FROM trades WHERE user_id = ?", (session["user_id"],))
#     trades = cursor.fetchall()

#     win_loss = [1 if trade[1] == 'Win' else 0 for trade in trades]
#     win_count = win_loss.count(1)
#     loss_count = win_loss.count(0)

#     fig = go.Figure(data=[
#         go.Bar(name="Wins", x=["Wins"], y=[win_count], marker=dict(color="green")),
#         go.Bar(name="Losses", x=["Losses"], y=[loss_count], marker=dict(color="red"))
#     ])
#     fig.update_layout(
#         title="Your Performance (Win/Loss)",
#         xaxis_title="Outcome",
#         yaxis_title="Count",
#         barmode='group'
#     )

#     graph = py.to_html(fig, full_html=False)
#     conn.close()
#     return render_template("dashboard.html", trades=trades, graph=graph)


# @app.route('/log_trade', methods=["GET", "POST"])
# def log_trade():
#     if "user_id" not in session:
#         flash("You must log in first.", "warning")
#         return redirect("/login")

#     if request.method == "POST":
#         pair = request.form["pair"]
#         result = request.form["result"]
#         entry = float(request.form["entry"])
#         exit_price = float(request.form["exit"])
#         notes = request.form["notes"]
#         screenshot_filename = None
#         date = request.form["date"]

#         if "screenshot" in request.files:
#             file = request.files["screenshot"]
#             if file and allowed_file(file.filename):
#                 filename = secure_filename(file.filename)
#                 filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#                 file.save(filepath)
#                 screenshot_filename = filename

#         conn = sqlite3.connect("database.db")
#         conn.execute("INSERT INTO trades (user_id, pair, result, entry, exit, notes, screenshot, date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
#                      (session["user_id"], pair, result, entry, exit_price, notes, screenshot_filename, date))
#         conn.commit()
#         conn.close()

#         # NFT minting temporarily disabled
#         flash("Trade logged successfully!", "success")

#         return redirect("/dashboard")

#     return render_template("log_trade.html")


# @app.route('/api/trade_metadata/<pair>_<date>.json')
# def trade_metadata(pair, date):
#     conn = sqlite3.connect("database.db")
#     cursor = conn.cursor()
#     cursor.execute("SELECT pair, result, entry, exit, notes, screenshot, date FROM trades WHERE pair = ? AND date = ?", (pair, date))
#     trade = cursor.fetchone()
#     conn.close()

#     if not trade:
#         return jsonify({"error": "Trade not found"}), 404

#     metadata = {
#         "name": f"Trade: {trade[0]} ({trade[6]})",
#         "description": f"Result: {trade[1]}, Entry: {trade[2]}, Exit: {trade[3]}, Notes: {trade[4]}",
#         "image": f"https://yourdomain.com/uploads/{trade[5]}" if trade[5] else "",
#         "attributes": [
#             {"trait_type": "Pair", "value": trade[0]},
#             {"trait_type": "Result", "value": trade[1]},
#             {"trait_type": "Entry", "value": trade[2]},
#             {"trait_type": "Exit", "value": trade[3]},
#             {"trait_type": "Date", "value": trade[6]}
#         ]
#     }
#     return jsonify(metadata)


# @app.route('/logout', methods=["POST"])
# def logout():
#     session.clear()
#     flash("You have been logged out.", "info")
#     return redirect("/login")


# @app.route('/uploads/<filename>')
# def uploaded_file(filename):
#     return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# if __name__ == '__main__':
#     init_db()
#     app.run(debug=True)







from flask import Flask, render_template, request, redirect, flash, session, send_from_directory, jsonify
import sqlite3
import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import plotly.graph_objects as go
import plotly.io as py
from livereload import Server

# =====================================================
#  Flask Setup
# =====================================================
app = Flask(__name__)
app.secret_key = os.urandom(24)

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        email TEXT UNIQUE,
        password TEXT
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
    conn.close()


@app.context_processor
def inject_user():
    return dict(session=session)


@app.route('/')
def home():
    return render_template("index.html")


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
            flash("Registration successful!", "success")
            return redirect("/login")
        except sqlite3.IntegrityError:
            flash("Email already exists.", "danger")
        finally:
            conn.close()
    return render_template("register.html")


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


@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect("/login")


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    init_db()
    server = Server(app.wsgi_app)
    server.serve(debug=True, port=5000)  # this replaces app.run()

