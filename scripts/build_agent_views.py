"""
Builds the agent-readable layer of the site from the data files. Run after any
data change (each workflow does), and locally with `python scripts/build_agent_views.py`.

Writes:
  llms.txt              what the site is, where the data lives, how fresh it is
  robots.txt, sitemap.xml
  data/index.json       manifest of every data file with its schema and freshness
  data/summary.json     the numbers an agent would otherwise have to compute
  data/picks.md         picks by stock and every pick, as markdown tables
  data/analysts.md      the latest analyst mismatch scan as markdown
  data/cases.json/.md   case studies of the best picks (thesis at the time vs outcome)
  data/portfolio.md     stop-rule comparison as markdown (when data/portfolio.json exists)

Everything here is derived: data/picks.json, data/analyst_mismatch.json and
data/portfolio.json are the sources of truth.
"""
import html, json, os, re
from collections import defaultdict
from datetime import datetime, timezone

SITE     = "https://edwardphill.github.io/stockpicker"
NOW      = datetime.now(timezone.utc)
NOW_STR  = NOW.strftime("%Y-%m-%d %H:%M UTC")
TOP_N    = 5
CASES_N  = 4

def load(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return default

def write(path, text):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        f.write(text if text.endswith("\n") else text + "\n")

def money(v):
    return f"${v:,.2f}" if v else "—"

def pct(v, digits=1):
    return "—" if v is None else f"{v:+.{digits}f}%"

def mktcap(v):
    if not v: return "—"
    if v >= 1e12: return f"${v/1e12:.2f}T"
    if v >= 1e9:  return f"${v/1e9:.1f}B"
    return f"${v/1e6:.0f}M"

def days_since(d):
    return (NOW.date() - datetime.strptime(d, "%Y-%m-%d").date()).days

def upside(target, price):
    return round((target - price) / price * 100, 1) if (target and price) else None

# ── Picks ────────────────────────────────────────────────────────────────────
def group_by_stock(picks):
    """One row per ticker: return since the first pick, like the Picks page."""
    by = defaultdict(list)
    for p in picks:
        by[p["ticker"]].append(p)
    rows = []
    for t, lst in by.items():
        lst.sort(key=lambda p: p["date"])
        first, latest = lst[0], lst[-1]
        priced = next((p for p in reversed(lst) if p.get("cur_price")), latest)
        cur = priced.get("cur_price") or 0
        ret = round((cur - first["entry_price"]) / first["entry_price"] * 100, 2) if (cur and first["entry_price"]) else first.get("pct_chg", 0)
        rows.append({
            "ticker": t, "theme": latest.get("theme") or first.get("theme", ""),
            "conviction": max(lst, key=lambda p: {"Strong Buy": 2, "Buy": 1}.get(p["conviction"], 0))["conviction"],
            "first_picked": first["date"], "last_picked": latest["date"], "times_picked": len(lst),
            "entry_price": first["entry_price"], "current_price": cur, "return_pct": ret,
            "analyst_target": latest.get("analyst_target"),
            "target_upside_pct": upside(latest.get("analyst_target"), cur),
            "status": "Open" if any((p.get("status") or "Open") == "Open" for p in lst) else "Closed",
            "report_url": first.get("report_url"),
            "picks": lst,
        })
    rows.sort(key=lambda r: r["return_pct"], reverse=True)
    return rows

def stats(rets):
    n = len(rets)
    if not n: return {}
    s = sorted(rets)
    return {"count": n,
            "win_rate_pct": round(sum(1 for r in rets if r > 0) / n * 100, 1),
            "avg_return_pct": round(sum(rets) / n, 2),
            "median_return_pct": round(s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2, 2),
            "avg_return_with_10pct_stop": round(sum(max(r, -10) for r in rets) / n, 2)}

def build_summary(picks, stocks, analysts, portfolio, cases):
    price_dates = sorted((p.get("last_price_update") or p["date"]) for p in picks)
    themes = defaultdict(list)
    for r in stocks:
        themes[r["theme"]].append(r)
    brief = {"tickers": [r["ticker"] for r in stocks[:TOP_N]]}
    return {
        "schema": f"{SITE}/data/schema/summary.schema.json",
        "generated": NOW_STR,
        "site": SITE,
        "prices_as_of": price_dates[-1] if price_dates else None,
        "counts": {"stocks": len(stocks), "picks": len(picks),
                   "first_pick": min(p["date"] for p in picks) if picks else None,
                   "last_pick": max(p["date"] for p in picks) if picks else None,
                   "open_positions": sum(1 for p in picks if (p.get("status") or "Open") == "Open")},
        "by_stock": stats([r["return_pct"] for r in stocks]),
        "by_pick": stats([p.get("pct_chg") or 0 for p in picks]),
        "top": [{k: r[k] for k in ("ticker", "theme", "first_picked", "entry_price", "current_price", "return_pct", "times_picked")} for r in stocks[:TOP_N]],
        "bottom": [{k: r[k] for k in ("ticker", "theme", "first_picked", "entry_price", "current_price", "return_pct", "times_picked")} for r in stocks[-TOP_N:][::-1]],
        "themes": {t: {"stocks": len(rs), "picks": sum(r["times_picked"] for r in rs),
                       "avg_return_pct": round(sum(r["return_pct"] for r in rs) / len(rs), 2)} for t, rs in sorted(themes.items())},
        "analyst_mismatch": ({
            "scan": analysts["generated"], "scanned": analysts["scanned"], "mismatches": len(analysts["rows"]),
            "candidate_rule": "new name (not picked in 180 days) and at least one analyst target >= 50% above price; ranked by mismatch score",
            "candidates": [{"ticker": r["ticker"], "group": r["group"], "score": r["score"], "upside_high_pct": r.get("upside_high"),
                            "why": r.get("path_50_why")} for r in analysts["rows"] if r.get("path_50") and r.get("novel")],
        } if analysts else None),
        "portfolio": ({"generated": portfolio["generated"], "rules": portfolio["rules"]} if portfolio else None),
        "case_studies": [c["ticker"] for c in cases],
        "cadence": {
            "prices": "every 30 minutes, US market hours (refresh-prices.yml)",
            "analyst_mismatch": "Mondays 12:15 UTC (analyst-mismatch.yml)",
            "weekly_brief": "Tuesdays 12:30 UTC (weekly-brief.yml)",
            "portfolio": "weekdays 21:45 UTC after the close (portfolio-sim.yml)",
        },
        "disclaimer": "Personal research tool. Picks are generated algorithmically and reviewed by AI. Not financial advice.",
    }

def picks_md(picks, stocks, summary):
    out = [f"# StockPicker picks", "",
           f"Prices as of {summary['prices_as_of']}. {summary['counts']['stocks']} stocks, {summary['counts']['picks']} picks "
           f"({summary['counts']['first_pick']} to {summary['counts']['last_pick']}). "
           f"By stock: {summary['by_stock'].get('win_rate_pct')}% win rate, {pct(summary['by_stock'].get('avg_return_pct'))} average return since first pick. "
           f"Source: [picks.json]({SITE}/data/picks.json). Not financial advice.", "",
           "## By stock (return since the first pick)", "",
           "| Stock | Theme | Conviction | First picked | Entry | Now | Return | Target upside | Picked |",
           "|---|---|---|---|---:|---:|---:|---:|---:|"]
    for r in stocks:
        out.append(f"| {r['ticker']} | {r['theme']} | {r['conviction']} | {r['first_picked']} | {money(r['entry_price'])} | {money(r['current_price'])} | "
                   f"{pct(r['return_pct'])} | {pct(r['target_upside_pct'])} | {r['times_picked']}× |")
    out += ["", "## Every pick", "",
            "| Date | Ticker | Conviction | Entry | Now | Return | Analyst target | Upside @ pick | Mkt cap | VIX | Signals | Report |",
            "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|"]
    for p in sorted(picks, key=lambda p: p["date"], reverse=True):
        sig = ", ".join(s.replace("_", " ") for s in p.get("signals", []))
        rep = f"[report]({p['report_url']})" if p.get("report_url") else ""
        out.append(f"| {p['date']} | {p['ticker']} | {p['conviction']} | {money(p['entry_price'])} | {money(p.get('cur_price'))} | {pct(p.get('pct_chg'))} | "
                   f"{money(p.get('analyst_target'))} | {pct(p.get('implied_upside_at_entry'))} | {mktcap(p.get('mktcap'))} | {p.get('vix_at_entry', '—')} | {sig} | {rep} |")
    return "\n".join(out)

# ── Analyst mismatch ─────────────────────────────────────────────────────────
def analysts_md(a):
    rows = a["rows"]
    out = [f"# Analyst mismatch scan", "",
           f"Scan {a['generated']}: {a['scanned']} stocks scanned, {len(rows)} mismatches. "
           "Lone bull = consensus Hold/Sell with only 1–2 analysts at Buy; lone bear = the reverse; breakaway = a firm's rating or "
           "target in the last 120 days sits against consensus or 25%+ from the mean target. 50% path = some analyst target is 50%+ above price. "
           "New = not picked in 180 days. Candidates for the weekly brief are rows that are both. "
           f"Source: [analyst_mismatch.json]({SITE}/data/analyst_mismatch.json). Ratings via Yahoo Finance.", "",
           "| Ticker | Name | Group | Flags | Price | Consensus (buy/hold/sell) | Mean target | Street high | Street low | 50% path | New | Score |",
           "|---|---|---|---|---:|---|---:|---:|---:|---|---|---:|"]
    for r in rows:
        c = r["counts"]
        flags = ", ".join(f.replace("_", " ") for f in r["flags"])
        new = "yes" if r.get("novel") else f"picked {r.get('times_picked')}× (last {r.get('last_picked')})"
        out.append(f"| {r['ticker']} | {r['name']} | {r['group']} | {flags} | {money(r['price'])} | {r['consensus']} ({c['strong_buy']+c['buy']}/{c['hold']}/{c['sell']+c['strong_sell']}) | "
                   f"{pct(r.get('upside_mean'), 0)} | {pct(r.get('upside_high'), 0)} | {pct(r.get('downside_low'), 0)} | "
                   f"{'yes: ' + r['path_50_why'] if r.get('path_50') else 'no'} | {new} | {r['score']} |")
    out += ["", "## Dissenting calls", ""]
    for r in rows:
        if not r["breaks"]: continue
        out.append(f"- **{r['ticker']}**: " + "; ".join(
            f"{b['firm']} {b['date']} {b['from'] + ' → ' if b['from'] and b['from'] != b['to'] else ''}{b['to']}"
            f"{', PT ' + money(b['target']) if b.get('target') else ''} ({b['why']})" for b in r["breaks"]))
    return "\n".join(out)

# ── Case studies ─────────────────────────────────────────────────────────────
def strip(s):
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s))).strip()

def sections(report_html):
    """{heading: text} for each <h3> in the report, split by the bull/bear column."""
    out = {}
    for side, col in (("bull", "bull-hdr"), ("bear", "bear-hdr")):
        m = re.search(rf'<div class="col-hdr {col}".*?</div>(.*?)(?=<div class="col"|</body>)', report_html, re.S)
        if not m: continue
        body = m.group(1)
        parts = re.split(r"<h3[^>]*>(.*?)</h3>", body, flags=re.S)
        for i in range(1, len(parts) - 1, 2):
            out[(side, strip(parts[i]))] = strip(parts[i + 1])
    return out

def first_sentences(text, n=2, limit=420):
    sents = re.split(r"(?<=[.!?])\s+", text)
    s = " ".join(sents[:n])
    return s if len(s) <= limit else s[:limit].rsplit(" ", 1)[0] + "…"

def report_path(p):
    return f"reports/{p['ticker']}-{p['date']}.html"

def build_cases(stocks, portfolio):
    port = {(x["ticker"], x["date"]): x for x in (portfolio or {}).get("picks", [])}
    cases = []
    for r in stocks[:CASES_N]:
        first = r["picks"][0]
        path = report_path(first)
        secs = sections(open(path).read()) if os.path.exists(path) else {}
        pp = port.get((r["ticker"], first["date"]), {})
        rules = pp.get("rules", {})
        lessons = []
        if first.get("implied_upside_at_entry") is not None and first["implied_upside_at_entry"] < 50:
            lessons.append(f"Consensus analyst upside at the pick was {pct(first['implied_upside_at_entry'])}, under 50%, so a gate on the consensus target would have skipped it; the gate has to accept a single analyst's 50% path.")
        if rules.get("stop_5", {}).get("reason") == "stop" and r["return_pct"] > 0:
            lessons.append(f"A -5% stop would have sold it on {rules['stop_5']['exit_date']} at {pct(rules['stop_5']['return_pct'])}; the worst close on the way was {pct(pp.get('max_drawdown_pct'))}.")
        elif rules.get("stop_10", {}).get("reason") == "stop" and r["return_pct"] > 0:
            lessons.append(f"A -10% stop would have sold it on {rules['stop_10']['exit_date']}; the worst close on the way was {pct(pp.get('max_drawdown_pct'))}.")
        elif pp.get("max_drawdown_pct") is not None:
            lessons.append(f"Never closed more than {pct(pp['max_drawdown_pct'])} below entry, so neither stop would have triggered.")
        if r["times_picked"] > 1:
            lessons.append(f"Picked {r['times_picked']} times; the repeats added exposure to the same name rather than a new idea.")
        cases.append({
            "ticker": r["ticker"], "theme": r["theme"], "first_picked": first["date"], "times_picked": r["times_picked"],
            "conviction": first["conviction"], "entry_price": first["entry_price"], "current_price": r["current_price"],
            "return_pct": r["return_pct"], "days_held": days_since(first["date"]),
            "analyst_target_at_pick": first.get("analyst_target"), "analyst_upside_at_pick_pct": first.get("implied_upside_at_entry"),
            "signals": first.get("signals", []), "signal_values": first.get("signal_values", {}),
            "macro_at_pick": {"vix": first.get("vix_at_entry"), "yield_10y": first.get("yield_10y_at_entry"), "risk_on": first.get("risk_on_at_entry")},
            "mktcap_at_pick": first.get("mktcap"),
            "report_url": first.get("report_url") or f"{SITE}/{path}",
            "thesis": first_sentences(secs.get(("bull", "Investment Thesis")) or secs.get(("bull", "The 50% Path"), "")),
            "catalysts": first_sentences(secs.get(("bull", "Catalysts")) or secs.get(("bull", "Catalysts & Timeline"), ""), 2),
            "bear_verdict": first_sentences(secs.get(("bear", "Verdict")) or secs.get(("bear", "Bear Case Thesis")) or secs.get(("bear", "Is the 50% Path Realistic?"), ""), 2),
            "path": {"max_drawdown_pct": pp.get("max_drawdown_pct"), "max_runup_pct": pp.get("max_runup_pct"),
                     "stop_5": rules.get("stop_5"), "stop_10": rules.get("stop_10")} if pp else None,
            "lessons": lessons,
        })
    return cases

def cases_md(cases):
    out = ["# Case studies: the best picks so far", "",
           f"Built {NOW_STR} from the tracker's top {len(cases)} stocks by return since first pick. "
           "Each shows what the system saw at the time (signals, analyst target, macro), what the AI bull and bear reports argued, and what happened. "
           f"Source: [cases.json]({SITE}/data/cases.json).", ""]
    for c in cases:
        out += [f"## {c['ticker']} · {pct(c['return_pct'])} since {c['first_picked']}", "",
                f"- Theme: {c['theme']} · Conviction: {c['conviction']} · Picked {c['times_picked']}×",
                f"- Entry {money(c['entry_price'])} → now {money(c['current_price'])} over {c['days_held']} days",
                f"- Analyst target at pick: {money(c['analyst_target_at_pick'])} ({pct(c['analyst_upside_at_pick_pct'])} upside)",
                f"- Signals: {', '.join(s.replace('_', ' ') for s in c['signals']) or '—'}",
                f"- Macro: VIX {c['macro_at_pick']['vix']}, 10Y {c['macro_at_pick']['yield_10y']}%, {'risk on' if c['macro_at_pick']['risk_on'] else 'risk off'} · Market cap {mktcap(c['mktcap_at_pick'])}"]
        if c["path"]:
            out.append(f"- Path: worst close {pct(c['path']['max_drawdown_pct'])}, best close {pct(c['path']['max_runup_pct'])} vs entry")
        if c["thesis"]:   out += ["", f"**Bull thesis then:** {c['thesis']}"]
        if c["catalysts"]: out += ["", f"**Catalysts cited:** {c['catalysts']}"]
        if c["bear_verdict"]: out += ["", f"**Bear verdict then:** {c['bear_verdict']}"]
        if c["lessons"]: out += ["", "**Takeaways:**"] + [f"- {l}" for l in c["lessons"]]
        out += ["", f"[Full bull/bear report]({c['report_url']})", ""]
    return "\n".join(out)

# ── Portfolio ────────────────────────────────────────────────────────────────
def portfolio_md(p):
    out = [f"# Stop-rule comparison", "",
           f"Simulated {p['generated']} on daily closes from each pick date, ${p['stake']:,} per pick, {len(p['picks'])} picks. "
           "Rules: " + "; ".join(f"{k}: {v['description']}" for k, v in p["rules"].items()) + ". "
           f"Source: [portfolio.json]({SITE}/data/portfolio.json).", "",
           "| Rule | Ending value | Total return | Win rate | Avg return | Stopped out | Stopped-out winners |",
           "|---|---:|---:|---:|---:|---:|---:|"]
    for k, v in p["rules"].items():
        out.append(f"| {v['label']} | {money(v['ending_value'])} | {pct(v['total_return_pct'])} | {v['win_rate_pct']}% | {pct(v['avg_return_pct'])} | {v['stopped_out']} | {v['stopped_out_winners']} |")
    out += ["", "## Per pick", "", "| Date | Ticker | Entry | Now | Hold | Worst close | Best close | " + " | ".join(v['label'] for v in p["rules"].values() if v["key"] != "hold") + " |",
            "|---|---|---:|---:|---:|---:|---:|" + "---:|" * (len(p["rules"]) - 1)]
    for x in p["picks"]:
        cells = []
        for k, v in p["rules"].items():
            if k == "hold": continue
            rr = x["rules"].get(k)
            cells.append("—" if not rr else f"{pct(rr['return_pct'])}{' (' + rr['reason'] + ' ' + rr['exit_date'] + ')' if rr['reason'] != 'open' else ''}")
        out.append(f"| {x['date']} | {x['ticker']} | {money(x['entry_price'])} | {money(x['last_price'])} | {pct(x['hold_return_pct'])} | {pct(x['max_drawdown_pct'])} | {pct(x['max_runup_pct'])} | " + " | ".join(cells) + " |")
    return "\n".join(out)

# ── llms.txt, manifest, robots, sitemap ──────────────────────────────────────
FILES = [
    ("data/summary.json", "application/json", "Computed stats: counts, win rates, average returns, top and bottom stocks, this week's analyst-mismatch candidates, stop-rule results. Read this first.", "summary"),
    ("data/picks.json", "application/json", "Every pick: date, ticker, theme, conviction, entry and current price, return, analyst target, signals, macro at entry, report URL.", "picks"),
    ("data/picks.md", "text/markdown", "picks.json as two markdown tables (by stock, every pick).", None),
    ("data/analyst_mismatch.json", "application/json", "Latest Monday scan: stocks where one analyst breaks from consensus, with rating counts, targets, dissenting calls, 50% path and novelty flags.", "analyst_mismatch"),
    ("data/analysts.md", "text/markdown", "analyst_mismatch.json as a markdown table plus the dissenting calls.", None),
    ("data/portfolio.json", "application/json", "Stop-rule simulation on daily closes: hold vs -5% stop vs -10% stop vs the v2 exit rule, per pick and in total.", "portfolio"),
    ("data/portfolio.md", "text/markdown", "portfolio.json as markdown tables.", None),
    ("data/cases.json", "application/json", "Case studies of the best picks: the setup, the bull and bear arguments at the time, the path since, takeaways.", "cases"),
    ("data/cases.md", "text/markdown", "cases.json as prose.", None),
    ("data/watchlist.json", "application/json", "Extra tickers scanned for analyst mismatch, grouped by theme.", None),
    ("reports/weekly/latest.html", "text/html", "The latest Tuesday weekly brief (static HTML, no JavaScript needed).", None),
    ("docs/selection-rules.md", "text/markdown", "The v2 selection rules: one pick a week, a 50%-in-6-months gate with no upside cap, novelty, exits.", None),
]
PAGES = [("index.html", "Picks tracker"), ("analysts.html", "Analyst mismatch"), ("portfolio.html", "Stop-rule comparison"),
         ("cases.html", "Case studies"), ("reports/weekly/latest.html", "Weekly brief")]

def freshness(path, summary, analysts, portfolio):
    if path.startswith("data/picks"): return summary["prices_as_of"]
    if path.startswith("data/analyst") and analysts: return analysts["generated"]
    if path.startswith("data/portfolio") and portfolio: return portfolio["generated"]
    return NOW_STR

def build_index(summary, analysts, portfolio):
    files = []
    for path, ctype, desc, schema in FILES:
        if not os.path.exists(path): continue
        files.append({"path": path, "url": f"{SITE}/{path}", "content_type": ctype, "description": desc,
                      "updated": freshness(path, summary, analysts, portfolio),
                      "schema": f"{SITE}/data/schema/{schema}.schema.json" if schema else None})
    return {"schema": "stockpicker.index/1", "site": SITE, "generated": NOW_STR,
            "pages": [{"path": p, "url": f"{SITE}/{p}", "title": t} for p, t in PAGES],
            "files": files, "cadence": summary["cadence"], "disclaimer": summary["disclaimer"]}

def llms_txt(summary, analysts, portfolio, cases):
    c, bs = summary["counts"], summary["by_stock"]
    lines = ["# StockPicker", "",
             "> A personal stock-picking tracker. An automated pipeline scores a universe of high-growth tickers across "
             "thematic sectors (AI/robotics, defense, nuclear, cybersecurity, space, biotech, quantum, AI infrastructure/fiber), "
             "picks names with a credible path to a 50% gain, writes an AI bull/bear report for each, and tracks the result. "
             "Every number on the site comes from small JSON files listed below; the HTML pages render those files with "
             "JavaScript, so fetch the JSON or the markdown mirrors instead of the pages. Not financial advice.", "",
             f"Key facts as of {summary['prices_as_of']}: {c['stocks']} stocks picked in {c['picks']} picks between {c['first_pick']} and {c['last_pick']}; "
             f"by stock the win rate is {bs.get('win_rate_pct')}% and the average return since first pick is {pct(bs.get('avg_return_pct'))} "
             f"(best {summary['top'][0]['ticker']} {pct(summary['top'][0]['return_pct'])}, worst {summary['bottom'][0]['ticker']} {pct(summary['bottom'][0]['return_pct'])})."]
    if analysts:
        cands = summary["analyst_mismatch"]["candidates"]
        lines.append(f"Latest analyst-mismatch scan {analysts['generated']}: {len(analysts['rows'])} mismatches; this week's candidates "
                     f"(new names with a 50% path): {', '.join(x['ticker'] for x in cands) or 'none'}.")
    if portfolio:
        r = portfolio["rules"]
        lines.append("Stop-rule simulation (" + portfolio["generated"] + "): " + "; ".join(f"{v['label']} {pct(v['total_return_pct'])}" for v in r.values()) + ".")
    lines += ["", "## Data (fetch these)", ""]
    for path, ctype, desc, schema in FILES:
        if os.path.exists(path):
            lines.append(f"- [{path}]({SITE}/{path}): {desc}" + (f" Schema: {SITE}/data/schema/{schema}.schema.json" if schema else ""))
    lines += ["", f"- [data/index.json]({SITE}/data/index.json): manifest of the files above with freshness timestamps.", "",
              "## Pages (JavaScript-rendered, for people)", ""]
    lines += [f"- [{t}]({SITE}/{p})" for p, t in PAGES]
    lines += ["", "## Method", "",
              f"- [docs/selection-rules.md]({SITE}/docs/selection-rules.md): how picks are (and will be) selected: one pick a week, a hard 50%-in-6-months gate with no cap on upside, novelty, exits.",
              f"- [README.md]({SITE}/README.md): the scoring signals, themes, data sources and the bull/bear report format.",
              "- Analyst mismatch: lone bull = consensus Hold/Sell with 1–2 analysts at Buy; lone bear = the reverse; breakaway = a firm's rating or target in the last 120 days against consensus or 25%+ from the mean target. Ratings via Yahoo Finance, which can lag a day or two.",
              "", "## Freshness", ""]
    lines += [f"- {k.replace('_', ' ')}: {v}" for k, v in summary["cadence"].items()]
    lines += ["", "## Conventions", "",
              "- Dates are ISO (YYYY-MM-DD); timestamps are UTC. Prices are USD. Percentages are plain numbers (12.5 means +12.5%).",
              "- `return_pct` on a pick is (current − entry) / entry; by stock it is measured from the first pick of that stock.",
              "- `status` is Open for every pick until the pipeline records exits; the -10% stop in `avg_return_with_10pct_stop` is a cap on losses, not a traded rule. `data/portfolio.json` is the path-based simulation.",
              "- Repository: https://github.com/edwardphill/stockpicker (AGENTS.md describes the layout for coding agents).",
              "", f"Generated {NOW_STR} by scripts/build_agent_views.py."]
    return "\n".join(lines)

def sitemap(summary):
    urls = [f"{SITE}/{p}" for p, _ in PAGES] + [f"{SITE}/{p}" for p, *_ in FILES if os.path.exists(p)] + [f"{SITE}/llms.txt", f"{SITE}/data/index.json"]
    body = "".join(f"  <url><loc>{html.escape(u)}</loc><lastmod>{NOW.strftime('%Y-%m-%d')}</lastmod></url>\n" for u in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{body}</urlset>'

if __name__ == "__main__":
    picks     = load("data/picks.json", [])
    analysts  = load("data/analyst_mismatch.json")
    portfolio = load("data/portfolio.json")
    stocks    = group_by_stock(picks)
    cases     = build_cases(stocks, portfolio)
    summary   = build_summary(picks, stocks, analysts, portfolio, cases)

    write("data/summary.json", json.dumps(summary, indent=2))
    write("data/picks.md", picks_md(picks, stocks, summary))
    write("data/cases.json", json.dumps({"schema": f"{SITE}/data/schema/cases.schema.json", "generated": NOW_STR, "cases": cases}, indent=2))
    write("data/cases.md", cases_md(cases))
    if analysts:  write("data/analysts.md", analysts_md(analysts))
    if portfolio: write("data/portfolio.md", portfolio_md(portfolio))
    write("data/index.json", json.dumps(build_index(summary, analysts, portfolio), indent=2))
    write("llms.txt", llms_txt(summary, analysts, portfolio, cases))
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n# Machine-readable entry point: {SITE}/llms.txt")
    write("sitemap.xml", sitemap(summary))
    print(f"Built agent views: {len(stocks)} stocks, {len(picks)} picks, {len(cases)} cases, "
          f"{'analysts ' if analysts else ''}{'portfolio' if portfolio else ''}")
