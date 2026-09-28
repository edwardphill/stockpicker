# Agent visit tracker

GitHub Pages keeps no access logs, and agents that read `llms.txt` or the JSON never run
JavaScript, so a normal analytics tag never sees them. This Worker is a logged front door:
it serves the same files as the site (proxied from GitHub Pages, cached five minutes) and
writes one row per request to Cloudflare's Analytics Engine, JavaScript or not.

Each row: path, client class (`ai-bot`, `script`, `browser`, `other`), bot name (GPTBot,
ClaudeBot, PerplexityBot, python-requests, curl...), user agent, country, referer, accept
header, method, status. Links inside text responses are rewritten to the Worker's host, so an
agent that starts at `/llms.txt` stays on the logged host as it follows links.

## Deploy (once, about five minutes)

1. Create a free Cloudflare account at https://dash.cloudflare.com/sign-up.
2. From this folder:
   ```
   npx wrangler login
   npx wrangler deploy
   ```
   The last line prints the URL, e.g. `https://stockpicker-agents.<your-subdomain>.workers.dev`.
3. Check it: `curl -A "test-agent/1.0" https://stockpicker-agents.<your-subdomain>.workers.dev/llms.txt`.
4. In the GitHub repo, add a **repository variable** (Settings → Secrets and variables → Actions →
   Variables) named `AGENT_BASE` with that URL. From the next data refresh, the file links in
   `llms.txt` and `data/index.json` on the Pages site point at the Worker, so an agent that
   arrives through the canonical `llms.txt` is counted from its second request on.

## See the visits

- Cloudflare dashboard → Workers & Pages → `stockpicker-agents` → Analytics Engine, or run
  a query against the SQL API:
  ```sql
  SELECT blob2 AS class, blob3 AS bot, SUM(_sample_interval) AS hits
  FROM stockpicker_agent_visits
  WHERE timestamp > NOW() - INTERVAL '7' DAY
  GROUP BY class, bot ORDER BY hits DESC
  ```
- To show the counts on the site itself, create an API token (My Profile → API Tokens →
  Custom token → **Account Analytics: Read**) and add two repository secrets:
  `CF_ACCOUNT_ID` and `CF_API_TOKEN`. The daily portfolio workflow then runs
  `scripts/agent_visits.py`, which writes `data/agent_visits.json`; the summary and
  `llms.txt` pick it up on the next build.

## Coverage

The Worker sees every request that reaches it. Requests that go straight to
`edwardphill.github.io` bypass it. For full coverage, put a custom domain on Cloudflare
(free plan), point it at the Pages site, and route the Worker on that domain: then every
request to the site is logged, and Cloudflare's own dashboard adds a per-bot AI crawler
report on top.
