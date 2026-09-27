"""
Builds the weekly brief from Monday's analyst mismatch scan and sends it out.

  1. Reads data/analyst_mismatch.json (written by scripts/analyst_mismatch.py).
  2. Ranks this week's candidates: new names (not picked in 180 days) where at
     least one analyst sees a 50%+ path, by mismatch score. No cap on upside.
  3. Writes reports/weekly/<date>.html and reports/weekly/latest.html.
  4. Emails the brief when MAIL_USERNAME, MAIL_PASSWORD and MAIL_TO are set
     (Gmail app password by default; SMTP_HOST / SMTP_PORT override). Without
     them it only publishes the page.

Runs Tuesdays in GitHub Actions, or locally (python scripts/weekly_brief.py).
"""
import html, json, os, smtplib, sys
from datetime import datetime, timezone
from email.message import EmailMessage
from email.utils import formataddr
from ghpub import put_file

SITE       = "https://edwardphill.github.io/stockpicker"
DATA_PATH  = "data/analyst_mismatch.json"
OUT_DIR    = "reports/weekly"
TOP_N      = 5      # candidates in the headline table
CHART_URL  = "https://www.tradingview.com/chart/?symbol={t}"

def money(v):
    return f"${v:,.2f}" if v else "—"

def pct(v, digits=0):
    if v is None:
        return "—"
    return f"{v:+.{digits}f}%"

def color(v):
    if v is None: return "#555"
    return "#15803d" if v > 0 else ("#b91c1c" if v < 0 else "#555")

def rank(rows):
    cands = [r for r in rows if r.get("path_50") and r.get("novel")]
    cands.sort(key=lambda r: r["score"], reverse=True)
    return cands

def best_bull_call(r):
    calls = [b for b in r.get("breaks", []) if b.get("side") == "bull" and b.get("upside") is not None]
    return max(calls, key=lambda b: b["upside"], default=None)

# ── HTML (inline styles: it doubles as the email body) ─────────────────────
def row_html(r, i):
    e = html.escape
    c = r["counts"]
    call = best_bull_call(r)
    call_txt = (f"{e(call['firm'])}: {e(call['to'])}, PT {money(call['target'])} ({pct(call['upside'])})"
                if call else e(r.get("path_50_why") or ""))
    tags = " · ".join(f for f in [
        "Lone bull" if "lone_bull" in r["flags"] else "",
        "Lone bear" if "lone_bear" in r["flags"] else "",
        "Breakaway" if "breakaway" in r["flags"] else ""] if f)
    bg = "#fbfaf6" if i % 2 else "#ffffff"
    return f"""
    <tr style="background:{bg}">
      <td style="padding:10px 8px;border-bottom:1px solid #e5e2d8;vertical-align:top;">
        <a href="{CHART_URL.format(t=e(r['ticker']))}" style="font-size:16px;font-weight:700;color:#0b5cad;text-decoration:none;">{e(r['ticker'])}</a>
        <div style="font-size:12px;color:#555;">{e(r['name'])}<br>{e(r['group'])}</div>
        <div style="font-size:12px;color:#9a5200;margin-top:4px;">{tags}</div>
      </td>
      <td style="padding:10px 8px;border-bottom:1px solid #e5e2d8;vertical-align:top;white-space:nowrap;">{money(r['price'])}</td>
      <td style="padding:10px 8px;border-bottom:1px solid #e5e2d8;vertical-align:top;white-space:nowrap;">
        <span style="font-weight:700;color:{'#15803d' if r['consensus']=='bull' else ('#b91c1c' if r['consensus']=='bear' else '#555')}">{r['consensus'].upper()}</span>
        <div style="font-size:12px;color:#555;">{c['strong_buy']+c['buy']} buy · {c['hold']} hold · {c['sell']+c['strong_sell']} sell</div>
      </td>
      <td style="padding:10px 8px;border-bottom:1px solid #e5e2d8;vertical-align:top;white-space:nowrap;">
        <div><span style="color:{color(r['upside_high'])};font-weight:700;">{pct(r['upside_high'])}</span> <span style="color:#555;font-size:12px;">high {money(r['target_high'])}</span></div>
        <div><span style="color:{color(r['upside_mean'])};">{pct(r['upside_mean'])}</span> <span style="color:#555;font-size:12px;">mean {money(r['target_mean'])}</span></div>
        <div><span style="color:{color(r['downside_low'])};">{pct(r['downside_low'])}</span> <span style="color:#555;font-size:12px;">low {money(r['target_low'])}</span></div>
      </td>
      <td style="padding:10px 8px;border-bottom:1px solid #e5e2d8;vertical-align:top;font-size:13px;">{call_txt}</td>
      <td style="padding:10px 8px;border-bottom:1px solid #e5e2d8;vertical-align:top;font-weight:700;color:#9a5200;">{r['score']:.1f}</td>
    </tr>"""

def build_html(data, cands, when):
    e = html.escape
    rows = data["rows"]
    head = """<tr style="background:#ffb03b;color:#000;font-size:12px;text-transform:uppercase;letter-spacing:.5px;">
      <th style="padding:8px;text-align:left;">Stock</th><th style="padding:8px;text-align:left;">Price</th>
      <th style="padding:8px;text-align:left;">Street</th><th style="padding:8px;text-align:left;">Targets</th>
      <th style="padding:8px;text-align:left;">The dissenting call</th><th style="padding:8px;text-align:left;">Score</th></tr>"""
    top = cands[:TOP_N]
    top_html = ("".join(row_html(r, i) for i, r in enumerate(top)) if top else
                '<tr><td colspan="6" style="padding:16px 8px;color:#555;">No new name cleared the 50% gate this week.</td></tr>')
    rest = [r for r in rows if r not in top]
    rest_html = "".join(f"""<tr>
        <td style="padding:6px 8px;border-bottom:1px solid #eee;"><a href="{CHART_URL.format(t=e(r['ticker']))}" style="color:#0b5cad;font-weight:700;text-decoration:none;">{e(r['ticker'])}</a> <span style="color:#555;font-size:12px;">{e(r['group'])}</span></td>
        <td style="padding:6px 8px;border-bottom:1px solid #eee;font-size:12px;color:#555;">{' · '.join(f.replace('_',' ') for f in r['flags'])}{' · 50% path' if r.get('path_50') else ''}{'' if r.get('novel') else f" · picked {r.get('times_picked')}× (last {r.get('last_picked')})"}</td>
        <td style="padding:6px 8px;border-bottom:1px solid #eee;white-space:nowrap;color:{color(r['upside_high'])};">{pct(r['upside_high'])} <span style="color:#555;font-size:12px;">high</span></td>
        <td style="padding:6px 8px;border-bottom:1px solid #eee;color:#9a5200;font-weight:700;">{r['score']:.1f}</td></tr>"""
        for r in rest)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>StockPicker — Weekly Brief {when}</title></head>
<body style="margin:0;background:#f3f1ea;font-family:'IBM Plex Mono',Consolas,Menlo,monospace;color:#1c1c1c;font-size:14px;line-height:1.4;">
<div style="max-width:960px;margin:0 auto;background:#fff;">
  <div style="background:#ffb03b;padding:12px 16px;">
    <div style="font-size:16px;font-weight:700;letter-spacing:1px;">STOCK<span style="font-weight:400;">PICKER</span> <span style="background:#000;color:#ffb03b;padding:0 6px;font-size:12px;">WEEKLY</span></div>
    <div style="font-size:12px;">Brief for the week of {when} · scan {e(data['generated'])} · {data['scanned']} stocks</div>
  </div>
  <div style="padding:16px;">
    <h2 style="margin:0 0 4px;font-size:16px;color:#9a5200;text-transform:uppercase;letter-spacing:.5px;">This week's candidates</h2>
    <p style="margin:0 0 12px;color:#555;font-size:13px;">New names (not picked in 180 days) where at least one analyst sees a 50%+ path, ranked by how far they break from the Street. No cap on upside.</p>
    <div style="overflow-x:auto;"><table style="width:100%;border-collapse:collapse;">{head}{top_html}</table></div>

    <h2 style="margin:24px 0 4px;font-size:14px;color:#9a5200;text-transform:uppercase;letter-spacing:.5px;">Every mismatch this week ({len(rest)} more)</h2>
    <div style="overflow-x:auto;"><table style="width:100%;border-collapse:collapse;font-size:13px;">{rest_html}</table></div>

    <p style="margin:20px 0 0;font-size:12px;color:#555;">
      Full detail: <a href="{SITE}/analysts.html" style="color:#0b5cad;">{SITE}/analysts.html</a> · Tracker: <a href="{SITE}/" style="color:#0b5cad;">{SITE}/</a><br>
      Ratings via Yahoo Finance. Analyst targets are 12-month; treat a 50% path as a lead to check, not a signal. Not financial advice.
    </p>
  </div>
</div>
</body></html>"""

def send_email(subject, body_html):
    user, pw, to = os.environ.get("MAIL_USERNAME"), os.environ.get("MAIL_PASSWORD"), os.environ.get("MAIL_TO")
    if not (user and pw and to):
        print("Email skipped: set MAIL_USERNAME, MAIL_PASSWORD and MAIL_TO secrets to send it.")
        return False
    host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("SMTP_PORT", "465"))
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = formataddr(("StockPicker", os.environ.get("MAIL_FROM", user)))
    msg["To"] = ", ".join(a.strip() for a in to.split(",") if a.strip())
    msg.set_content("This brief is HTML. Open it in a mail client that shows HTML, or read it at " + SITE + "/reports/weekly/latest.html")
    msg.add_alternative(body_html, subtype="html")
    with smtplib.SMTP_SSL(host, port, timeout=30) as s:
        s.login(user, pw)
        s.send_message(msg)
    print(f"Emailed to {msg['To']}")
    return True

if __name__ == "__main__":
    try:
        data = json.load(open(DATA_PATH))
    except FileNotFoundError:
        sys.exit(f"{DATA_PATH} not found: run scripts/analyst_mismatch.py first")
    when  = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    cands = rank(data["rows"])
    page  = build_html(data, cands, when).encode()
    put_file(f"{OUT_DIR}/{when}.html", page, f"Weekly brief {when}")
    put_file(f"{OUT_DIR}/latest.html", page, f"Weekly brief {when} (latest)")
    print(f"Published {OUT_DIR}/{when}.html; candidates: {', '.join(r['ticker'] for r in cands) or 'none'}")
    subject = f"StockPicker weekly: {', '.join(r['ticker'] for r in cands[:TOP_N]) or 'no new candidates'} ({when})"
    send_email(subject, build_html(data, cands, when))
