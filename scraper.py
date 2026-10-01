"""PriceWatch - scraper: web page ya JSON API se price nikalna."""
import json
import re
import requests
from bs4 import BeautifulSoup

HEADERS = {
    # Real browser jaisa header taake sites block na karen
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) PriceWatch/1.0"
}


def parse_price(text):
    """'Rs. 1,299.00' -> 1299.0 | '$19.99' -> 19.99 | 'PKR 2500' -> 2500.0"""
    # Pehle digit se shuru hone wala number-group dhoondo
    # (taake 'Rs.' jaisay prefix ke dots price mein na ghusein)
    m = re.search(r"\d[\d,]*(\.\d+)?", text)
    if not m:
        raise ValueError(f"koi price nahi mili: {text!r}")
    return float(m.group(0).replace(",", ""))


def find_jsonld_price(data):
    """JSON-LD structured data mein price dhoondo (offers.price waghera)."""
    if isinstance(data, dict):
        offers = data.get("offers")
        if isinstance(offers, dict) and "price" in offers:
            return offers["price"]
        if isinstance(offers, list):
            for o in offers:
                if isinstance(o, dict) and "price" in o:
                    return o["price"]
        if "price" in data and isinstance(data["price"], (int, float, str)):
            return data["price"]
        for v in data.values():
            r = find_jsonld_price(v)
            if r is not None:
                return r
    elif isinstance(data, list):
        for v in data:
            r = find_jsonld_price(v)
            if r is not None:
                return r
    return None


def walk_json_path(data, path):
    """'bitcoin.usd' -> data['bitcoin']['usd'] (JSON mein dot-path)."""
    cur = data
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        elif isinstance(cur, list) and part.isdigit() \
                and int(part) < len(cur):
            cur = cur[int(part)]
        else:
            raise ValueError(
                f"JSON path '{path}' mein '{part}' nahi mila")
    return cur


def fetch_price(url, selector=None):
    """URL kholo, price nikalo.

    JSON API ho (CoinGecko jaisi) to selector ko dot-path samjho,
    warna tarteeb: selector -> JSON-LD -> price class.
    """
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()

    # 0. JSON API response (CoinGecko waghera): selector = JSON dot-path
    ctype = resp.headers.get("Content-Type", "")
    if "json" in ctype:
        data = resp.json()
        if not selector:
            raise ValueError(
                "API URL ke liye selector mein JSON path do "
                "(jaise 'bitcoin.usd')")
        value = walk_json_path(data, selector)
        return float(str(value).replace(",", ""))

    soup = BeautifulSoup(resp.text, "html.parser")

    # 1. Selector diya ho to wahi
    if selector:
        el = soup.select_one(selector)
        if not el:
            raise ValueError(f"selector '{selector}' page par nahi mila")
        return parse_price(el.get_text())

    # 2. JSON-LD structured data (real sites ka sab se reliable tareeqa)
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except (ValueError, TypeError):
            continue
        price = find_jsonld_price(data)
        if price is not None:
            return float(str(price).replace(",", ""))

    # 3. Aakhri koshish: class/id mein 'price' likha ho
    el = soup.find(class_=re.compile("price", re.I)) or \
        soup.find(id=re.compile("price", re.I))
    if el:
        return parse_price(el.get_text())

    raise ValueError("price nahi mili (site block kar rahi ho gi ya selector do)")
