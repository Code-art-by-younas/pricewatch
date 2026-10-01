"""PriceWatch Web Dashboard - Flask web UI.

Khaas baat: scraper.py / database.py / alerter.py dobara likhe baghair
reuse ho rahe hain - sirf ye web layer nayi hai (CLI wala core same).
"""
import os

from flask import Flask, render_template, request, redirect, url_for, flash

import database
import scraper
import alerter

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "pricewatch-dev-key")


def card_data(p):
    hist = database.get_history(p["id"])
    last = hist[-1]["price"] if hist else None
    trend = hist[-1]["price"] - hist[-2]["price"] if len(hist) >= 2 else 0
    alert = bool(p["target_price"] and last is not None
                 and last <= p["target_price"])
    return {"product": p, "last": last, "trend": trend,
            "alert": alert, "checks": len(hist)}


@app.route("/")
def dashboard():
    database.init_db()
    cards = [card_data(p) for p in database.get_products()]
    stats = {
        "products": len(cards),
        "alerts": sum(1 for c in cards if c["alert"]),
        "checks": sum(c["checks"] for c in cards),
    }
    return render_template("dashboard.html", cards=cards, stats=stats)


@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        url = request.form.get("url", "").strip()
        selector = request.form.get("selector", "").strip() or None
        target = request.form.get("target_price", "").strip()
        try:
            target = float(target) if target else None
        except ValueError:
            flash("Target price number mein likho.")
            return render_template("add.html")
        if not name or not url:
            flash("Naam aur URL zaroori hain.")
            return render_template("add.html")
        database.init_db()
        database.add_product(name, url, selector, target)
        flash(f"'{name}' add ho gaya.")
        return redirect(url_for("dashboard"))
    return render_template("add.html")


@app.route("/product/<int:pid>")
def detail(pid):
    database.init_db()
    products = {p["id"]: p for p in database.get_products()}
    if pid not in products:
        return "Product nahi mila", 404
    p = products[pid]
    return render_template("detail.html", product=p,
                           history=database.get_history(pid),
                           card=card_data(p))


def do_check(pid):
    """Ek product ki price check karo. (ok, message) wapas karta hai."""
    products = {p["id"]: p for p in database.get_products()}
    p = products.get(pid)
    if not p:
        return False, "Product nahi mila."
    try:
        price = scraper.fetch_price(p["url"], p["selector"])
    except Exception as e:  # noqa: BLE001 - user ko saaf message chahiye
        return False, f"{p['name']}: {e}"
    database.save_price(pid, price)
    fired = alerter.check_and_alert(p, price)
    return True, f"{p['name']}: Rs.{price:,.2f}" + ("  \U0001f525 ALERT!" if fired else "")


@app.route("/check/<int:pid>")
def check_one(pid):
    database.init_db()
    ok, msg = do_check(pid)
    flash(("✓ " if ok else "✗ ") + msg)
    return redirect(url_for("detail", pid=pid))


@app.route("/check-all")
def check_all():
    database.init_db()
    for p in database.get_products():
        ok, msg = do_check(p["id"])
        flash(("✓ " if ok else "✗ ") + msg)
    return redirect(url_for("dashboard"))


@app.route("/delete/<int:pid>", methods=["POST"])
def delete(pid):
    database.init_db()
    database.delete_product(pid)
    flash("Product delete ho gaya.")
    return redirect(url_for("dashboard"))


@app.route("/api/auto-check")
def auto_check():
    """Bahir wala cron (cron-job.org) har kuch minute baad is URL ko
    hit karega taake prices khud check hon. ?key= zaroori hai taake
    koi ajnabi trigger na kar sake (Render par CRON_KEY env var lagao)."""
    key = request.args.get("key", "")
    cron_key = os.environ.get("CRON_KEY") or app.secret_key
    if not cron_key or key != cron_key:
        return {"ok": False, "error": "ghalat ya missing key"}, 403
    database.init_db()
    results = []
    for p in database.get_products():
        ok, msg = do_check(p["id"])
        results.append({"name": p["name"], "ok": ok, "message": msg})
    return {"ok": True, "checked": len(results), "results": results}


if __name__ == "__main__":
    database.init_db()
    app.run(debug=True, port=5000)
