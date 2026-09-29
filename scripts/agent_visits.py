"""
Pulls agent-visit counts from the Cloudflare Analytics Engine dataset written by
tracker/src/worker.js and writes data/agent_visits.json.

Needs CF_ACCOUNT_ID and CF_API_TOKEN (Account Analytics: Read). Without them it
exits quietly so the workflow step is a no-op until the tracker is deployed.
"""
import json, os, sys, urllib.request
from collections import defaultdict
from datetime import datetime, timezone

DATASET  = "stockpicker_agent_visits"
OUT_PATH = "data/agent_visits.json"
DAYS     = 30

QUERY = f"""
SELECT toStartOfInterval(timestamp, INTERVAL '1' DAY) AS day,
       blob2 AS class, blob3 AS bot, blob1 AS path, blob5 AS country,
       SUM(_sample_interval) AS hits
FROM {DATASET}
WHERE timestamp > NOW() - INTERVAL '{DAYS}' DAY
GROUP BY day, class, bot, path, country
ORDER BY day
"""

def fetch_rows(account, token):
    req = urllib.request.Request(
        f"https://api.cloudflare.com/client/v4/accounts/{account}/analytics_engine/sql",
        data=QUERY.encode(), method="POST",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "text/plain"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())["data"]

def summarize(rows):
    by = {k: defaultdict(float) for k in ("class", "bot", "path", "country", "day")}
    daily = defaultdict(lambda: defaultdict(float))
    for r in rows:
        hits = float(r["hits"])
        by["class"][r["class"]] += hits
        by["bot"][r["bot"] or "(unnamed)"] += hits
        by["path"][r["path"]] += hits
        by["country"][r["country"] or "?"] += hits
        day = str(r["day"])[:10]
        by["day"][day] += hits
        daily[day][r["class"]] += hits
    top = lambda d, n=15: [{"key": k, "hits": int(v)} for k, v in sorted(d.items(), key=lambda kv: -kv[1])[:n]]
    total = int(sum(by["class"].values()))
    return {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "window_days": DAYS, "total": total,
        "agents": int(by["class"].get("ai-bot", 0) + by["class"].get("script", 0)),
        "by_class": top(by["class"]), "by_bot": top(by["bot"]), "by_path": top(by["path"], 25),
        "by_country": top(by["country"]),
        "daily": [{"day": d, **{k: int(v) for k, v in c.items()}} for d, c in sorted(daily.items())],
        "source": "Cloudflare Analytics Engine via tracker/src/worker.js; counts are sampled estimates",
    }

if __name__ == "__main__":
    account, token = os.environ.get("CF_ACCOUNT_ID"), os.environ.get("CF_API_TOKEN")
    if not (account and token):
        print("Agent visits skipped: set CF_ACCOUNT_ID and CF_API_TOKEN once the tracker is deployed.")
        sys.exit(0)
    summary = summarize(fetch_rows(account, token))
    with open(OUT_PATH, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Agent visits: {summary['total']} requests in {DAYS} days, {summary['agents']} from agents")
