"""
Fetches current prices for all open picks and updates data/picks.json in the
checkout. The workflow commits the result (and the rebuilt agent views).
"""
import json
from datetime import datetime, timezone
import yfinance as yf

PATH  = "data/picks.json"
picks = json.load(open(PATH))
now   = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

for pick in picks:
    if pick.get("status", "Open") != "Open":
        continue
    t = pick["ticker"]
    try:
        fi    = yf.Ticker(t).fast_info
        price = float(getattr(fi, "last_price", 0) or 0)
        if price == 0:
            info  = yf.Ticker(t).info
            price = float(info.get("regularMarketPrice") or info.get("currentPrice") or 0)
        if price > 0:
            entry = pick.get("entry_price", 0)
            pct   = ((price - entry) / entry * 100) if entry else 0
            pick["cur_price"]         = round(price, 2)
            pick["pct_chg"]           = round(pct, 2)
            pick["last_price_update"] = now
            print(f"  {t}: ${price:.2f} ({pct:+.1f}%)")
        else:
            print(f"  {t}: no price returned")
    except Exception as e:
        print(f"  {t} error: {e}")

with open(PATH, "w") as f:
    json.dump(picks, f, indent=2)
print(f"Done — {now}")
