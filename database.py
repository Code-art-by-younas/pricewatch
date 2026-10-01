"""PriceWatch - database layer (drop-in replacement, deploy-ready).

Locally (PyCharm): SQLite use hota hai - kuch naya install nahi karna,
tumhara purana pricewatch.db waisa ka waisa chalta rahega.

Deploy par (Render + Neon): DATABASE_URL env var set ho to
Postgres use hota hai - data restart par delete NAHI hoga.

Dono backends ke liye functions same hain:
init_db, add_product, get_products, save_price,
get_last_price, get_history, delete_product
"""
import os
import sqlite3
from datetime import datetime

DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    import psycopg2
    import psycopg2.extras
    BACKEND = "pg"
else:
    BACKEND = "sqlite"

DB_FILE = "pricewatch.db"


def get_conn():
    if BACKEND == "pg":
        return psycopg2.connect(
            DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # rows dict ki tarah access hon
    return conn


def _ph(sql):
    """sqlite3 ke '?' placeholders ko Postgres ke '%s' mein badlo."""
    return sql.replace("?", "%s") if BACKEND == "pg" else sql


def init_db():
    conn = get_conn()
    if BACKEND == "pg":
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                selector TEXT,
                target_price REAL
            );
            CREATE TABLE IF NOT EXISTS prices (
                id SERIAL PRIMARY KEY,
                product_id INTEGER NOT NULL REFERENCES products(id),
                price REAL NOT NULL,
                checked_at TEXT NOT NULL
            );
            """
        )
        cur.close()
    else:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                selector TEXT,          -- CSS selector jahan price likhi hai
                target_price REAL       -- is se kam ho to alert
            );
            CREATE TABLE IF NOT EXISTS prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                price REAL NOT NULL,
                checked_at TEXT NOT NULL,
                FOREIGN KEY (product_id) REFERENCES products(id)
            );
            """
        )
    conn.commit()
    conn.close()


def add_product(name, url, selector=None, target_price=None):
    conn = get_conn()
    cur = conn.cursor()
    if BACKEND == "pg":
        cur.execute(
            "INSERT INTO products (name, url, selector, target_price)"
            " VALUES (%s, %s, %s, %s) RETURNING id",
            (name, url, selector, target_price),
        )
        pid = cur.fetchone()["id"]
    else:
        cur.execute(
            "INSERT INTO products (name, url, selector, target_price)"
            " VALUES (?, ?, ?, ?)",
            (name, url, selector, target_price),
        )
        pid = cur.lastrowid
    conn.commit()
    cur.close()
    conn.close()
    return pid


def get_products():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products ORDER BY id")
    rows = [dict(r) for r in cur.fetchall()]
    cur.close()
    conn.close()
    return rows


def save_price(product_id, price):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        _ph("INSERT INTO prices (product_id, price, checked_at)"
            " VALUES (?, ?, ?)"),
        (product_id, price, datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()
    cur.close()
    conn.close()


def get_last_price(product_id):
    """Sab se recent check ki price (None agar kabhi check na hua ho)."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        _ph("SELECT price FROM prices WHERE product_id = ?"
            " ORDER BY id DESC LIMIT 1"),
        (product_id,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    return dict(row)["price"] if row else None


def get_history(product_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        _ph("SELECT price, checked_at FROM prices WHERE product_id = ?"
            " ORDER BY id"),
        (product_id,),
    )
    rows = [dict(r) for r in cur.fetchall()]
    cur.close()
    conn.close()
    return rows


def delete_product(product_id):
    """Product aur uski saari price history delete karo."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(_ph("DELETE FROM prices WHERE product_id = ?"), (product_id,))
    cur.execute(_ph("DELETE FROM products WHERE id = ?"), (product_id,))
    conn.commit()
    cur.close()
    conn.close()
