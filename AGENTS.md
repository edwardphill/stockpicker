# AGENTS.md

Notes for coding agents working in this repository.

## What this is

A GitHub Pages site (https://edwardphill.github.io/stockpicker/) that tracks algorithmic stock picks.
There is no build step and no framework: static HTML pages render small JSON files with vanilla JavaScript.
GitHub Actions refresh the data and commit the results.

The pick pipeline itself (`stock_alert.py`: universe, scoring, the Claude bull/bear reports, email) is
**not in this repo**. It writes `data/picks.json` and `reports/<TICKER>-<date>.html` from elsewhere.

## Layout

| Path | What |
|------|------|
| `index.html` | Picks tracker (one row per stock, every pick behind an expander) |
| `analysts.html` | Analyst mismatch scan |
| `portfolio.html` | Stop-rule simulation |
| `cases.html` | Case studies of the best picks |
| `reports/weekly/latest.html` | Tuesday weekly brief (static, also the email body) |
| `assets/terminal.css`, `assets/theme.js` | Shared theme (dark terminal by default, light toggle) |
| `data/picks.json` | Source of truth for picks (written by the pipeline, prices refreshed here) |
| `data/analyst_mismatch.json` | Monday scan output |
| `data/portfolio.json` | Stop-rule simulation output |
| `data/watchlist.json` | Extra tickers to scan, grouped by theme |
| `data/summary.json`, `data/*.md`, `data/index.json`, `llms.txt`, `sitemap.xml` | Derived agent-readable views; never edit by hand |
| `data/schema/*.schema.json` | JSON Schema for each data file |
| `scripts/` | The jobs (see below) |
| `docs/selection-rules.md` | The v2 selection rules for the pipeline |
| `tracker/` | Cloudflare Worker that proxies the site and logs every request (agent visit tracking); deployed by hand with wrangler |

## Jobs

| Script | Workflow | When |
|--------|----------|------|
| `scripts/refresh_prices.py` | `refresh-prices.yml` | every 30 min in market hours |
| `scripts/analyst_mismatch.py` | `analyst-mismatch.yml` | Mondays 12:15 UTC |
| `scripts/weekly_brief.py` | `weekly-brief.yml` | Tuesdays 12:30 UTC (emails when `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_TO` secrets exist) |
| `scripts/portfolio_sim.py` | `portfolio-sim.yml` | weekdays 21:45 UTC |
| `scripts/build_agent_views.py` | every workflow, last step | after any data change |
| `scripts/agent_visits.py` | `portfolio-sim.yml` | daily; no-op until `CF_ACCOUNT_ID` and `CF_API_TOKEN` secrets exist |

Every workflow ends with `python scripts/build_agent_views.py` and a commit. Scripts read and write the
checkout; they take no arguments and expect the repo root as the working directory.

## Working here

- Run any script locally with `python3 scripts/<name>.py` from the repo root (`pip install yfinance` for the
  three that fetch prices). Yahoo Finance may be unreachable from sandboxes; mock `yfinance.Ticker` to test.
- After changing a data file or a script that writes one, run `scripts/build_agent_views.py` so the derived
  files stay in sync, and commit them together.
- Pages are plain HTML + JS. Keep new text at 12px or larger, use the CSS variables in `assets/terminal.css`,
  and add any new page to the tab bar on every page and to `PAGES` in `scripts/build_agent_views.py`.
- `CHART_URL` (TradingView) is defined at the top of each page's script; change it in all of them together.
- Dates are ISO, timestamps UTC, prices USD, percentages plain numbers.
- Not financial advice; keep the disclaimer in the footer of every page.
