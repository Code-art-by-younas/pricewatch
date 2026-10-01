"""PriceWatch - main CLI.

Commands:
    python app.py init              # products.json se watchlist load karo
    python app.py check             # sab products ki price check karo + alerts
    python app.py list              # watched products dikhao
    python app.py add               # naya product add karo
    python app.py history <id>      # kisi product ki price history
"""
import argparse
import json

import database
import scraper
import alerter


def cmd_init(_):
    database.init_db()
    with open("products.json", encoding="utf-8") as f:
        items = json.load(f)
    for p in items:
        pid = database.add_product(p["name"], p["url"],
                                   p.get("selector"), p.get("target_price"))
        print(f"  + [#{pid}] {p['name']} (target Rs.{p.get('target_price')})")
    print("Watchlist ready. Ab chalao:  python app.py check")


def cmd_check(_):
    database.init_db()
    products = database.get_products()
    if not products:
        print("Koi product nahi. Pehle chalao:  python app.py init")
        return
    for p in products:
        try:
            price = scraper.fetch_price(p["url"], p["selector"])
        except Exception as e:  # noqa: BLE001 - user ko saaf message chahiye
            print(f"  ✗ {p['name']}: fail ({e})")
            continue
        prev = database.get_last_price(p["id"])
        database.save_price(p["id"], price)
        trend = ""
        if prev is not None:
            if price < prev:
                trend = f"  📉 Rs.{prev:,.2f} se kam hui"
            elif price > prev:
                trend = f"  📈 Rs.{prev:,.2f} se barhi"
        print(f"  ✓ {p['name']}: Rs.{price:,.2f}{trend}")
        alerter.check_and_alert(p, price)


def cmd_list(_):
    database.init_db()
    for p in database.get_products():
        last = database.get_last_price(p["id"])
        last_s = f"Rs.{last:,.2f}" if last else "abhi check nahi hui"
        print(f"  [#{p['id']}] {p['name']} | target Rs.{p['target_price']} | last: {last_s}")


def cmd_add(args):
    database.init_db()
    pid = database.add_product(args.name, args.url, args.selector, args.target)
    print(f"Add ho gaya [#{pid}]: {args.name}")


def cmd_history(args):
    rows = database.get_history(args.id)
    if not rows:
        print("Is product ki koi history nahi.")
        return
    print(f"  Price history [#{args.id}]:")
    for r in rows:
        print(f"    {r['checked_at']}  ->  Rs.{r['price']:,.2f}")


def main():
    ap = argparse.ArgumentParser(description="PriceWatch - price monitoring")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init").set_defaults(fn=cmd_init)
    sub.add_parser("check").set_defaults(fn=cmd_check)
    sub.add_parser("list").set_defaults(fn=cmd_list)

    a = sub.add_parser("add")
    a.add_argument("--name", required=True)
    a.add_argument("--url", required=True)
    a.add_argument("--selector", default=None, help="CSS selector, masalan .price")
    a.add_argument("--target", type=float, default=None, help="target price")
    a.set_defaults(fn=cmd_add)

    h = sub.add_parser("history")
    h.add_argument("id", type=int)
    h.set_defaults(fn=cmd_history)

    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
