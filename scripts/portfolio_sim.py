"""
Stop-rule comparison on real price paths. For every pick, fetches daily closes
from the pick date and replays four exit rules:

  hold      never sell (what the tracker shows today)
  stop_5    sell at the first close 5% or more below entry
  stop_10   sell at the first close 10% or more below entry (the tracker's "managed" rule)
  v2        the proposed v2 exits: sell at -20%, at +50%, or after 6 months, whichever first

Each position is STAKE dollars. Closes, not intraday lows, so a stop that only
touched on a wick does not count. Writes data/portfolio.json.

Runs weekdays after the close in GitHub Actions, or locally.
"""
import json, math
from datetime import datetime, timedelta, timezone
import yfinance as yf

OUT_PATH = "data/portfolio.json"
STAKE    = 1000
RULES = {
    "hold":    {"label": "Hold",            "description": "never sell"},
    "stop_5":  {"label": "Stop -5%",        "description": "sell at the first close 5% or more below entry"},
    "stop_10": {"label": "Stop -10%",       "description": "sell at the first close 10% or more below entry (current managed rule)"},
    "v2":      {"label": "v2 exits",        "description": "sell at -20%, at +50%, or after 6 months, whichever comes first"},
}

def num(v):
    try:
        v = float(v)
        return None if math.isnan(v) else v
    except (TypeError, ValueError):
        return None

def closes_since(ticker, start):
    """[(date, close)] from `start` (inclusive) to today, or [] when Yahoo has nothing."""
    hist = yf.Ticker(ticker).history(start=start, auto_adjust=False)
    if hist is None or hist.empty:
        return []
    return [(d.strftime("%Y-%m-%d"), float(c)) for d, c in hist["Close"].items() if not math.isnan(c)]

def replay(entry, entry_date, path):
    """Returns {rule: {exit_date, exit_price, return_pct, reason}} for one pick."""
    def ret(price):
        return round((price - entry) / entry * 100, 2)
    last_date, last = path[-1]
    out = {"hold": {"exit_date": last_date, "exit_price": round(last, 2), "return_pct": ret(last), "reason": "open"}}
    six_months = (datetime.strptime(entry_date, "%Y-%m-%d") + timedelta(days=182)).strftime("%Y-%m-%d")
    for key, stop, take, deadline in (("stop_5", 0.95, None, None), ("stop_10", 0.90, None, None), ("v2", 0.80, 1.50, six_months)):
        exit_ = None
        for d, c in path:
            if c <= entry * stop:            exit_ = (d, c, "stop");   break
            if take and c >= entry * take:   exit_ = (d, c, "target"); break
            if deadline and d >= deadline:   exit_ = (d, c, "time");   break
        if exit_:
            out[key] = {"exit_date": exit_[0], "exit_price": round(exit_[1], 2), "return_pct": ret(exit_[1]), "reason": exit_[2]}
        else:
            out[key] = dict(out["hold"])
    return out

def simulate(picks, fetch=closes_since):
    rows, errors = [], []
    for p in sorted(picks, key=lambda p: (p["date"], p["ticker"])):
        entry = num(p.get("entry_price"))
        if not entry:
            continue
        try:
            path = fetch(p["ticker"], p["date"])
        except Exception as e:
            errors.append(f"{p['ticker']} {p['date']}: {e}")
            path = []
        if not path:
            # No history (delisted, bad symbol): fall back to the tracker's current price, hold only.
            cur = num(p.get("cur_price"))
            if not cur:
                continue
            path = [(p["date"], entry), (p.get("last_price_update", p["date"])[:10], cur)]
        rules = replay(entry, p["date"], path)
        closes = [c for _, c in path]
        rows.append({
            "date": p["date"], "ticker": p["ticker"], "theme": p.get("theme", ""),
            "entry_price": entry, "last_price": round(path[-1][1], 2), "last_date": path[-1][0],
            "days": (datetime.now(timezone.utc).date() - datetime.strptime(p["date"], "%Y-%m-%d").date()).days,
            "hold_return_pct": rules["hold"]["return_pct"],
            "max_drawdown_pct": round((min(closes) - entry) / entry * 100, 2),
            "max_runup_pct": round((max(closes) - entry) / entry * 100, 2),
            "closes": len(path), "rules": rules,
        })
    return rows, errors

def totals(rows):
    out = {}
    for key, meta in RULES.items():
        rets = [r["rules"][key]["return_pct"] for r in rows]
        n = len(rets) or 1
        stopped = [r for r in rows if r["rules"][key]["reason"] == "stop"]
        out[key] = {**meta, "key": key,
                    "positions": len(rets),
                    "ending_value": round(STAKE * sum(1 + x / 100 for x in rets), 2),
                    "total_return_pct": round(sum(rets) / n, 2),
                    "avg_return_pct": round(sum(rets) / n, 2),
                    "win_rate_pct": round(sum(1 for x in rets if x > 0) / n * 100, 1),
                    "stopped_out": len(stopped),
                    "stopped_out_winners": sum(1 for r in stopped if r["hold_return_pct"] > 0),
                    "exits": {reason: sum(1 for r in rows if r["rules"][key]["reason"] == reason) for reason in ("open", "stop", "target", "time")}}
    return out

if __name__ == "__main__":
    picks = json.load(open("data/picks.json"))
    rows, errors = simulate(picks)
    payload = {"schema": "https://edwardphill.github.io/stockpicker/data/schema/portfolio.schema.json",
               "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
               "stake": STAKE, "basis": "daily closes from the pick date; a stop needs a close at or below the level",
               "rules": totals(rows), "picks": rows, "errors": errors}
    with open(OUT_PATH, "w") as f:
        json.dump(payload, f, indent=2)
    for k, v in payload["rules"].items():
        print(f"  {v['label']:10} total {v['total_return_pct']:+.1f}%  win {v['win_rate_pct']}%  stopped {v['stopped_out']} (winners {v['stopped_out_winners']})")
    print(f"Done: {len(rows)} positions, {len(errors)} errors")
