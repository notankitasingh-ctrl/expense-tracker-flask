from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret123"

# ---------- DATABASE ----------
def init_db():
    conn = sqlite3.connect("expenses.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        amount REAL,
        category TEXT,
        date TEXT,
        user_id INTEGER
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------- LOGIN ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("expenses.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()

        if user:
            session["user_id"] = user[0]
            session["username"] = user[1]
            return redirect("/")
        else:
            return "Invalid credentials"

    return render_template("login.html")

# ---------- SIGNUP ----------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("expenses.db")
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("signup.html")

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------- HOME ----------
@app.route("/")
def index():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]
    category = request.args.get("category")
    search = request.args.get("search")

    conn = sqlite3.connect("expenses.db")
    c = conn.cursor()

    query = "SELECT * FROM expenses WHERE user_id=?"
    params = [user_id]

    if category and category != "All":
        query += " AND category=?"
        params.append(category)

    if search:
        query += " AND name LIKE ?"
        params.append(f"%{search}%")

    c.execute(query, params)
    data = c.fetchall()
    conn.close()

    total = sum(row[2] for row in data)

    # ---------- CATEGORY CHART ----------
    category_data = {}
    for row in data:
        category_data[row[3]] = category_data.get(row[3], 0) + row[2]

    labels = list(category_data.keys())
    values = list(category_data.values())

    # ---------- MONTHLY CHART ----------
    monthly_data = {}
    for row in data:
        month = row[4][:7]  # YYYY-MM
        monthly_data[month] = monthly_data.get(month, 0) + row[2]

    months = list(monthly_data.keys())
    month_values = list(monthly_data.values())

    return render_template(
        "index.html",
        expenses=data,
        total=total,
        labels=labels,
        values=values,
        months=months,
        month_values=month_values,
        username=session.get("username")
    )

# ---------- ADD ----------
@app.route("/add", methods=["POST"])
def add():
    if "user_id" not in session:
        return redirect("/login")

    name = request.form["name"]
    amount = request.form["amount"]
    category = request.form["category"]
    date = datetime.now().strftime("%Y-%m-%d")
    user_id = session["user_id"]

    conn = sqlite3.connect("expenses.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO expenses (name, amount, category, date, user_id) VALUES (?, ?, ?, ?, ?)",
        (name, amount, category, date, user_id)
    )
    conn.commit()
    conn.close()

    return redirect("/")

# ---------- DELETE ----------
@app.route("/delete/<int:id>")
def delete(id):
    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("expenses.db")
    c = conn.cursor()
    c.execute("DELETE FROM expenses WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/")

# ---------- EDIT ----------
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("expenses.db")
    c = conn.cursor()

    if request.method == "POST":
        name = request.form["name"]
        amount = request.form["amount"]
        category = request.form["category"]
        date = datetime.now().strftime("%Y-%m-%d")

        c.execute("""
            UPDATE expenses 
            SET name=?, amount=?, category=?, date=? 
            WHERE id=?
        """, (name, amount, category, date, id))

        conn.commit()
        conn.close()
        return redirect("/")

    c.execute("SELECT * FROM expenses WHERE id=?", (id,))
    expense = c.fetchone()
    conn.close()

    return render_template("edit.html", expense=expense)

# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True)