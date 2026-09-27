"""
Finds stocks where one analyst (or a small minority) breaks from the rest of the
Street, and writes data/analyst_mismatch.json for analysts.html.

Three kinds of mismatch are flagged:
  lone_bull   consensus is Hold/Sell but 1-2 analysts (and <=20%) rate it Buy
  lone_bear   consensus is Buy but 1-2 analysts (and <=20%) rate it Sell
  breakaway   a firm's rating or price target in the last 120 days breaks from
              consensus (Buy vs non-Buy consensus, or target >=25% above/below the mean)

Two more fields feed the weekly brief:
  path_50     at least one analyst target implies >=50% upside from today's price
              (the Street high, or a dissenting firm's target): the "50% possible" gate
  novel       never picked, or last picked more than NOVEL_DAYS ago

Runs weekly in GitHub Actions (writes through the contents API when GITHUB_TOKEN
is set), or locally (writes the file directly).
"""
import json, math
from datetime import datetime, timedelta, timezone
import yfinance as yf
from ghpub import put_file

OUT_PATH    = "data/analyst_mismatch.json"
LOOKBACK    = timedelta(days=120)
TARGET_GAP  = 0.25          # firm target this far from the mean counts as a break
MIN_COVER   = 5             # need at least this many analysts for "lone" calls
PATH_MIN    = 50.0          # minimum upside (%) some analyst must see for a "50% path"
NOVEL_DAYS  = 180           # a ticker picked within this window is not novel

BULL = {"buy", "strong buy", "outperform", "overweight", "positive", "accumulate",
        "market outperform", "sector outperform", "top pick", "add", "conviction buy",
        "speculative buy", "moderate buy"}
BEAR = {"sell", "strong sell", "underperform", "underweight", "negative", "reduce",
        "market underperform", "sector underperform", "moderate sell"}

def grade_side(g):
    g = (g or "").strip().lower()
    if g in BULL: return "bull"
    if g in BEAR: return "bear"
    return "hold" if g else None

def num(v):
    try:
        v = float(v)
        return None if math.isnan(v) else v
    except (TypeError, ValueError):
        return None

def load_universe():
    """Returns ({ticker: group}, {ticker: pick history summary})."""
    tickers, history = {}, {}
    picks = json.load(open("data/picks.json"))
    for p in sorted(picks, key=lambda x: x["date"]):
        t = p["ticker"]
        tickers.setdefault(t, p.get("theme", ""))
        h = history.setdefault(t, {"times_picked": 0, "last_picked": None, "last_pick_return": None})
        h["times_picked"] += 1
        h["last_picked"] = p["date"]
        h["last_pick_return"] = p.get("pct_chg")
    wl = json.load(open("data/watchlist.json"))
    for group, ts in wl.items():
        if group.startswith("_"): continue
        for t in ts: tickers.setdefault(t, group)
    return tickers, history

def scan(ticker, group, hist=None):
    t = yf.Ticker(ticker)
    rec = t.recommendations
    if rec is None or rec.empty: return None
    cur = rec[rec["period"] == "0m"]
    row = (cur if not cur.empty else rec).iloc[0]
    sb, b, h, s, ss = (int(row.get(k, 0) or 0) for k in ("strongBuy", "buy", "hold", "sell", "strongSell"))
    bulls, bears, n = sb + b, s + ss, sb + b + h + s + ss
    if n == 0: return None
    consensus = max((("bull", bulls), ("hold", h), ("bear", bears)), key=lambda x: x[1])[0]

    info   = t.info or {}
    price  = num(info.get("currentPrice") or info.get("regularMarketPrice"))
    pt     = t.analyst_price_targets or {}
    tmean, thigh, tlow = num(pt.get("mean")), num(pt.get("high")), num(pt.get("low"))

    flags = []
    if n >= MIN_COVER and consensus != "bull" and 1 <= bulls <= 2 and bulls / n <= 0.2:
        flags.append("lone_bull")
    if n >= MIN_COVER and consensus == "bull" and 1 <= bears <= 2 and bears / n <= 0.2:
        flags.append("lone_bear")

    breaks = []
    ud = t.upgrades_downgrades
    if ud is not None and not ud.empty:
        since = datetime.now(timezone.utc).replace(tzinfo=None) - LOOKBACK
        seen  = set()
        for when, r in ud.sort_index(ascending=False).iterrows():
            if when.to_pydatetime() < since: break
            firm = r.get("Firm")
            if not firm or firm in seen: continue      # latest call per firm only
            seen.add(firm)
            side   = grade_side(r.get("ToGrade"))
            ftgt   = num(r.get("currentPriceTarget"))
            gap    = (ftgt / tmean - 1) if (ftgt and tmean) else None
            reason = []
            if side == "bull" and consensus != "bull": reason.append("bullish vs consensus")
            if side == "bear" and consensus != "bear": reason.append("bearish vs consensus")
            if gap is not None and abs(gap) >= TARGET_GAP:
                reason.append(f"target {gap:+.0%} vs mean")
            if reason:
                breaks.append({
                    "date": when.strftime("%Y-%m-%d"), "firm": firm,
                    "from": r.get("FromGrade") or "", "to": r.get("ToGrade") or "",
                    "action": r.get("Action") or "", "side": side,
                    "target": ftgt, "prior_target": num(r.get("priorPriceTarget")),
                    "target_vs_mean": round(gap * 100, 1) if gap is not None else None,
                    "upside": round((ftgt / price - 1) * 100, 1) if (ftgt and price) else None,
                    "why": ", ".join(reason),
                })
    if breaks: flags.append("breakaway")
    if not flags: return None

    # 50% path: does anyone on the Street see 50%+ from here? (Street high, or a dissenter.)
    path_50, path_why = False, None
    up_high = (thigh / price - 1) * 100 if (thigh and price) else None
    if up_high is not None and up_high >= PATH_MIN:
        path_50, path_why = True, f"Street high target {money(thigh)} is {up_high:+.0f}%"
    else:
        best = max((b for b in breaks if b["upside"] is not None), key=lambda b: b["upside"], default=None)
        if best and best["upside"] >= PATH_MIN:
            path_50, path_why = True, f"{best['firm']} target {money(best['target'])} is {best['upside']:+.0f}%"

    hist = hist or {"times_picked": 0, "last_picked": None, "last_pick_return": None}
    novel = True
    if hist["last_picked"]:
        age = (datetime.now(timezone.utc).date() - datetime.strptime(hist["last_picked"], "%Y-%m-%d").date()).days
        novel = age > NOVEL_DAYS

    # Conviction score: rewards a lonely, recent, far-from-consensus call.
    score = 0.0
    if "lone_bull" in flags or "lone_bear" in flags: score += 3 + (2 if min(bulls, bears) == 1 else 0)
    if breaks:
        score += 2 + min(len(breaks), 3)
        gaps = [abs(x["target_vs_mean"]) for x in breaks if x["target_vs_mean"] is not None]
        if gaps: score += min(max(gaps) / 25, 4)
    return {
        "ticker": ticker, "name": info.get("shortName") or ticker, "group": group,
        "price": price, "mktcap": num(info.get("marketCap")),
        "counts": {"strong_buy": sb, "buy": b, "hold": h, "sell": s, "strong_sell": ss},
        "n": n, "consensus": consensus,
        "target_mean": tmean, "target_high": thigh, "target_low": tlow,
        "upside_mean": round((tmean / price - 1) * 100, 1) if (tmean and price) else None,
        "upside_high": round((thigh / price - 1) * 100, 1) if (thigh and price) else None,
        "downside_low": round((tlow / price - 1) * 100, 1) if (tlow and price) else None,
        "flags": flags, "breaks": breaks[:5], "score": round(score, 1),
        "path_50": path_50, "path_50_why": path_why,
        "novel": novel, **hist,
    }

def money(v):
    return f"${v:,.2f}" if v else "—"

if __name__ == "__main__":
    universe, history = load_universe()
    rows, errors = [], []
    for tk, group in sorted(universe.items()):
        try:
            r = scan(tk, group, history.get(tk))
            if r:
                rows.append(r)
                print(f"  {tk}: {','.join(r['flags'])} score {r['score']}"
                      f"{' 50%path' if r['path_50'] else ''}{' new' if r['novel'] else ''}")
        except Exception as e:
            errors.append(tk)
            print(f"  {tk} error: {e}")
    rows.sort(key=lambda r: r["score"], reverse=True)
    payload = {"generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
               "scanned": len(universe), "errors": errors, "rows": rows}
    put_file(OUT_PATH, json.dumps(payload, indent=2).encode(), f"Analyst mismatch scan {payload['generated']}")
    cands = [r["ticker"] for r in rows if r["path_50"] and r["novel"]]
    print(f"Done: {len(rows)} mismatches from {len(universe)} tickers; candidates: {', '.join(cands) or 'none'}")
