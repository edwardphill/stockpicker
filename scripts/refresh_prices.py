"""
Fetches current prices for all open picks and updates data/picks.json.
Runs inside GitHub Actions on a schedule.
"""
import json, base64, os, urllib.request
from datetime import datetime
import yfinance as yf

TOKEN = os.environ["GITHUB_TOKEN"]
OWNER, REPO = "edwardphill", "stockpicker"
API = f"https://api.github.com/repos/{OWNER}/{REPO}/contents"
H = {
    "Authorization": f"token {TOKEN}",
    "Accept":        "application/vnd.github.v3+json",
    "Content-Type":  "application/json",
    "User-Agent":    "PriceRefresh/1.0",
}

def gh_get(path):
    req = urllib.request.Request(f"{API}/{path}", headers=H)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

def gh_put(path, content_bytes, message, sha):
    body = {"message": message, "content": base64.b64encode(content_bytes).decode(), "sha": sha}
    req = urllib.request.Request(f"{API}/{path}", data=json.dumps(body).encode(), headers=H, method="PUT")
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

resp  = gh_get("data/picks.json")
sha   = resp["sha"]
picks = json.loads(base64.b64decode(resp["content"]))
now   = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

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

gh_put("data/picks.json", json.dumps(picks, indent=2).encode(), f"Refresh prices {now}", sha)
print(f"Done — {now}")
