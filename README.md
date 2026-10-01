# PriceWatch — Live Price Monitoring Website

Kisi bhi **real product** ki live price track karo. Price tumhare **target se
kam** ho to foran **🔥 alert** milega. Price history SQLite database mein save
hoti hai, khoobsurat chart ke saath.

**Stack:** Python, Flask, `requests`, `BeautifulSoup`, SQLite
**Khaas baat:** CSS selector likhne ki zaroorat nahi — website **JSON-LD
structured data** se price khud dhoond leti hai (OLX Pakistan par live tested ✅).

## PyCharm mein setup (Windows)

1. ZIP extract karo, PyCharm mein **Open** karo (folder select karo).
2. Neeche **Terminal** kholo:
   ```
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

## Website chalao

```
python web.py
```

Browser mein kholo: **http://127.0.0.1:5000**

- 📊 **Dashboard** — live stats + product cards: price, target, 📉📈 trend, 🔥 TARGET HIT badge
- ➕ **Add Product** — naam + product URL + target price (selector khaali chhoro!)
- ⟳ **Check Now / Check All** — ek click par taaza live price
- 📊 **Details** — animated price history chart (target line ke saath) + change table
- 🗑️ **Delete** — product aur uski history hatao

## CLI version (optional)

```
python app.py check       # sab products ki price check karo + alerts
python app.py list        # watched products dekho
python app.py history 1   # product #1 ki price history
python app.py add --name "X" --url "https://..." --target 1500
```

## Interview mein kya batana hai

1. *"Live price monitoring website hai — Flask + web scraping."*
2. *"JSON-LD structured data se price auto-detect hoti hai — selector ki zaroorat nahi."*
3. *"SQLite mein price history, target hit par alert badges, Chart.js se animated charts."*
4. Demo: OLX ka real product add karke **Check Now** dabao — live price!
