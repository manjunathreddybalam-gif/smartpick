from flask import Flask, render_template, request, jsonify, redirect, url_for, abort, session, render_template_string
import os
import hmac
import secrets
import sqlite3
from pathlib import Path
from urllib.parse import urlparse
from functools import wraps

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "smartpick.db"

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False
def admin_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not session.get("admin_logged_in"):
            if request.path.startswith("/api/"):
                return jsonify({"error": "Please log in as admin."}), 401
            return redirect(url_for("admin_login"))
        return view_func(*args, **kwargs)
    return wrapped_view


def get_csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]


def csrf_header_required():
    token = session.get("csrf_token", "")
    supplied = request.headers.get("X-CSRF-Token", "")
    return bool(token) and bool(supplied) and hmac.compare_digest(token, supplied)

app.secret_key = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE") == "1",
)

SAMPLE_PRODUCTS = [
    {
        "name": "Everyday Wireless Headphones", "category": "Electronics", "price": 2499,
        "rating": 4.4, "description": "Comfortable wireless headphones for music, classes and calls.",
        "features": "Bluetooth;Long battery life;Built-in microphone",
        "image_url": "https://images.unsplash.com/photo-1509330622396-9f3b5f4f0b9b?auto=format&fit=crop&w=900&q=85",
        "affiliate_url": "https://www.amazon.in/", "tag": "Best for everyday"
    },
    {
        "name": "Minimal Desk Lamp", "category": "Home & Furniture", "price": 1299,
        "rating": 4.2, "description": "A clean-looking lamp for a study table or work desk.",
        "features": "Compact design;Warm light;Easy to place",
        "image_url": "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?auto=format&fit=crop&w=900&q=85",
        "affiliate_url": "https://www.amazon.in/", "tag": "Study setup"
    },
    {
        "name": "Daily Carry Backpack", "category": "Fashion", "price": 1799,
        "rating": 4.3, "description": "A versatile backpack for college, commuting and short trips.",
        "features": "Multiple compartments;Lightweight;Everyday style",
        "image_url": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=900&q=85",
        "affiliate_url": "https://www.amazon.in/", "tag": "College pick"
    },
    {
        "name": "Insulated Water Bottle", "category": "Lifestyle", "price": 799,
        "rating": 4.1, "description": "Reusable bottle for carrying water during the day.",
        "features": "Reusable;Portable;Easy-grip shape",
        "image_url": "https://images.unsplash.com/photo-1602143407151-7111542de6e8?auto=format&fit=crop&w=900&q=85",
        "affiliate_url": "https://www.amazon.in/", "tag": "Budget pick"
    },
    {
        "name": "Mechanical Keyboard", "category": "Electronics", "price": 3499,
        "rating": 4.6, "description": "A desk-friendly keyboard for typing, coding and gaming.",
        "features": "Tactile keys;Wired connection;Compact layout",
        "image_url": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?auto=format&fit=crop&w=900&q=85",
        "affiliate_url": "https://www.amazon.in/", "tag": "For productivity"
    },
    {
        "name": "Ceramic Coffee Mug Set", "category": "Home & Furniture", "price": 999,
        "rating": 4.0, "description": "Simple ceramic mugs for a home coffee or tea corner.",
        "features": "Reusable;Minimal design;Set of two",
        "image_url": "https://images.unsplash.com/photo-1514228742587-6b1558fcca3d?auto=format&fit=crop&w=900&q=85",
        "affiliate_url": "https://www.amazon.in/", "tag": "Home favourite"
    }
]

def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with connect_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price REAL NOT NULL DEFAULT 0,
                rating REAL NOT NULL DEFAULT 0,
                description TEXT NOT NULL DEFAULT '',
                features TEXT NOT NULL DEFAULT '',
                image_url TEXT NOT NULL DEFAULT '',
                affiliate_url TEXT NOT NULL DEFAULT '',
                tag TEXT NOT NULL DEFAULT ''
            )
        """)
        count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        if count == 0:
            conn.executemany("""
                INSERT INTO products
                (name, category, price, rating, description, features, image_url, affiliate_url, tag)
                VALUES (:name, :category, :price, :rating, :description, :features, :image_url, :affiliate_url, :tag)
            """, SAMPLE_PRODUCTS)

def rows_to_dicts(rows):
    return [dict(row) for row in rows]

@app.route("/")
def home():
    return render_template("index.html")
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin_logged_in"):
        return redirect(url_for("admin"))

    error = ""

    if request.method == "POST":
        csrf_token = session.get("csrf_token", "")
        supplied_token = request.form.get("csrf_token", "")

        if not csrf_token or not supplied_token or not hmac.compare_digest(
            csrf_token, supplied_token
        ):
            abort(400, description="Invalid security token. Please refresh the page.")

        username = os.environ.get("ADMIN_USERNAME", "")
        password = os.environ.get("ADMIN_PASSWORD", "")

        submitted_username = request.form.get("username", "")
        submitted_password = request.form.get("password", "")

        if (
            username
            and password
            and hmac.compare_digest(submitted_username, username)
            and hmac.compare_digest(submitted_password, password)
        ):
            session.clear()
            session["admin_logged_in"] = True
            get_csrf_token()
            return redirect(url_for("admin"))

        error = "Incorrect username or password."

    token = get_csrf_token()

    return render_template_string("""
    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>SmartPick Admin Login</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 360px;
                margin: 60px auto;
                padding: 20px;
            }
            input, button {
                box-sizing: border-box;
                width: 100%;
                padding: 12px;
                margin: 8px 0;
            }
            button { cursor: pointer; }
            .error { color: #b00020; }
        </style>
    </head>
    <body>
        <h2>SmartPick Admin Login</h2>
        {% if error %}
            <p class="error">{{ error }}</p>
        {% endif %}
        <form method="post">
            <input type="hidden" name="csrf_token" value="{{ token }}">
            <label for="username">Username</label>
            <input id="username" name="username" required autocomplete="username">
            <label for="password">Password</label>
            <input id="password" name="password" type="password"
                   required autocomplete="current-password">
            <button type="submit">Log in</button>
        </form>
    </body>
    </html>
    """, error=error, token=token)
@app.get("/admin/csrf-token")
@admin_required
def admin_csrf_token():
    return jsonify({"csrf_token": get_csrf_token()})


@app.route("/admin")
@admin_required
def admin():
    return render_template("admin.html")

@app.get("/api/products")
def get_products():
    query = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    max_price = request.args.get("max_price", "").strip()
    sort = request.args.get("sort", "recommended")
    with connect_db() as conn:
        sql = "SELECT * FROM products WHERE 1=1"
        params = []
        if query:
            sql += " AND (name LIKE ? OR description LIKE ? OR category LIKE ? OR features LIKE ?)"
            like = f"%{query}%"
            params.extend([like, like, like, like])
        if category and category != "All":
            sql += " AND category = ?"
            params.append(category)
        if max_price:
            try:
                sql += " AND price <= ?"
                params.append(float(max_price))
            except ValueError:
                return jsonify({"error": "max_price must be a number"}), 400
        order_by = {
            "price_low": "price ASC",
            "price_high": "price DESC",
            "rating": "rating DESC",
            "recommended": "rating DESC, price ASC"
        }.get(sort, "rating DESC, price ASC")
        sql += f" ORDER BY {order_by}"
        products = rows_to_dicts(conn.execute(sql, params).fetchall())
        categories = [r["category"] for r in conn.execute(
            "SELECT DISTINCT category FROM products ORDER BY category"
        ).fetchall()]
    return jsonify({"products": products, "categories": categories})

@app.get("/api/products/<int:product_id>")
def get_product(product_id):
    with connect_db() as conn:
        row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if not row:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(dict(row))

def valid_http_url(value):
    if not value:
        return True
    parsed = urlparse(value)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)

@app.post("/api/products")
@admin_required
def add_product():
    if not csrf_header_required():
        return jsonify({"error": "Invalid or missing security token."}), 403

    data = request.get_json(silent=True) or request.form.to_dict()
    required = ["name", "category"]
    if any(not str(data.get(k, "")).strip() for k in required):
        return jsonify({"error": "Name and category are required."}), 400
    try:
        price = float(data.get("price", 0) or 0)
        rating = float(data.get("rating", 0) or 0)
    except (TypeError, ValueError):
        return jsonify({"error": "Price and rating must be numbers."}), 400
    if price < 0 or not 0 <= rating <= 5:
        return jsonify({"error": "Price must be >= 0 and rating must be between 0 and 5."}), 400
    image_url = str(data.get("image_url", "")).strip()
    affiliate_url = str(data.get("affiliate_url", "")).strip()
    if not valid_http_url(image_url) or not valid_http_url(affiliate_url):
        return jsonify({"error": "Image and affiliate URLs must start with http:// or https://."}), 400
    values = (
        str(data["name"]).strip(), str(data["category"]).strip(), price, rating,
        str(data.get("description", "")).strip(), str(data.get("features", "")).strip(),
        image_url, affiliate_url, str(data.get("tag", "")).strip()
    )
    with connect_db() as conn:
        cur = conn.execute("""
            INSERT INTO products
            (name, category, price, rating, description, features, image_url, affiliate_url, tag)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, values)
        product_id = cur.lastrowid
    return jsonify({"ok": True, "id": product_id}), 201

@app.put("/api/products/<int:product_id>")
@admin_required
def update_product(product_id):
    if not csrf_header_required():
        return jsonify({"error": "Invalid or missing security token."}), 403

    data = request.get_json(silent=True) or {}
    required = ["name", "category"]
    if any(not str(data.get(k, "")).strip() for k in required):
        return jsonify({"error": "Name and category are required."}), 400
    try:
        price = float(data.get("price", 0) or 0)
        rating = float(data.get("rating", 0) or 0)
    except (TypeError, ValueError):
        return jsonify({"error": "Price and rating must be numbers."}), 400
    image_url = str(data.get("image_url", "")).strip()
    affiliate_url = str(data.get("affiliate_url", "")).strip()
    if price < 0 or not 0 <= rating <= 5 or not valid_http_url(image_url) or not valid_http_url(affiliate_url):
        return jsonify({"error": "Check price, rating, image URL and affiliate URL."}), 400
    with connect_db() as conn:
        cur = conn.execute("""
            UPDATE products SET name=?, category=?, price=?, rating=?, description=?, features=?,
            image_url=?, affiliate_url=?, tag=? WHERE id=?
        """, (
            data["name"].strip(), data["category"].strip(), price, rating,
            str(data.get("description", "")).strip(), str(data.get("features", "")).strip(),
            image_url, affiliate_url, str(data.get("tag", "")).strip(), product_id
        ))
    if cur.rowcount == 0:
        return jsonify({"error": "Product not found."}), 404
    return jsonify({"ok": True})

@app.delete("/api/products/<int:product_id>")
@admin_required
def delete_product(product_id):
    if not csrf_header_required():
        return jsonify({"error": "Invalid or missing security token."}), 403

    with connect_db() as conn:
        cur = conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
    if cur.rowcount == 0:
        return jsonify({"error": "Product not found."}), 404
    return jsonify({"ok": True})

if __name__ == "__main__":
    init_db()
    app.run(debug=False)
