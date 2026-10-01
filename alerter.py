"""PriceWatch - alerts: target se kam price par khabar (console + optional email)."""
import os
import smtplib
from email.message import EmailMessage


def load_env(path=".env"):
    """Chhota .env loader (koi extra dependency nahi)."""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def send_email(subject, body):
    to_addr = os.environ.get("ALERT_EMAIL")
    if not to_addr:
        return False
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = os.environ.get("SMTP_USER", "pricewatch@localhost")
    msg["To"] = to_addr
    msg.set_content(body)
    with smtplib.SMTP(os.environ.get("SMTP_HOST", "localhost"),
                      int(os.environ.get("SMTP_PORT", "25"))) as s:
        user = os.environ.get("SMTP_USER")
        if user:
            s.login(user, os.environ.get("SMTP_PASS", ""))
        s.send_message(msg)
    return True


def check_and_alert(product, price):
    """Target hit hua? Alert dikhao (+ email agar .env mein set ho)."""
    target = product.get("target_price")
    if target and price <= target:
        print(f"\n   \U0001f525 PRICE ALERT: '{product['name']}' sirf Rs.{price:,.2f} "
              f"(tumhara target: Rs.{target:,.2f})")
        print(f"   Link: {product['url']}")
        load_env()
        if send_email(f"Price drop: {product['name']}",
                      f"{product['name']} is now Rs.{price:,.2f}\n{product['url']}"):
            print("   Email alert bhej diya.")
        return True
    return False
