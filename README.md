# StockPicker — Daily Picks Tracker

**Live site:** https://edwardphill.github.io/stockpicker/

A fully automated daily stock recommendation system that scores a dynamic universe of high-growth tickers across seven thematic sectors, generates a bull/bear analysis using Claude AI, and publishes results to this tracker.

---

## What It Does

Each morning the pipeline:

1. **Builds a dynamic universe** — seeds + Finviz screener + peer expansion across 7 themes
2. **Scores every ticker** against 8 quantitative signals (see below)
3. **Selects the highest-scoring ticker** not picked in the last 2 days
4. **Generates a bull/bear report** using Claude AI as a senior equity analyst vs. a skeptical risk analyst
5. **Emails the report** to a distribution list
6. **Publishes the pick** to this GitHub Pages tracker

---

## Scoring Signals

Every ticker is scored on a path-to-50%-return framework. Each signal asks: does this create a credible mechanism for a 50%+ move in 12 months?

| Signal | Points | Logic |
|--------|--------|-------|
| Analyst consensus target ≥50% upside | +5 | Core gate — validates the path exists |
| Analyst consensus target 25–49% upside | +3 | Partial confidence in path |
| Insider buy in last 30 days | +4 | Executives putting own capital in before catalyst |
| Earnings/catalyst within 21 days | +3 | Binary event = asymmetric outcome |
| Volume >2x average | +3 | Smart money moving early |
| Revenue growth accelerating QoQ | +2 | Inflection point = re-rating event |
| Short interest >15% + catalyst | +2 | Squeeze accelerant |
| Institutional 13D/13G filed in 90 days | +2 | Someone crossed 5% — meaningful for smaller caps |
| Polymarket prediction market aligned | +2 | Real-money crowd wisdom on theme |
| No analyst coverage | -2 | Can't validate 50% path without a target |

**Conviction tiers:**
- **Strong Buy** — analyst upside ≥50% AND ≥3 signals fired
- **Buy** — analyst upside ≥25% OR ≥3 signals fired
- **Watch** — below Buy threshold

---

## Themes Covered

| Theme | Focus |
|-------|-------|
| Industrial AI / Robotics | Semiconductors, automation, edge compute |
| Defense Tech / Dual-Use | Drone, C2, surveillance, space defense |
| Nuclear / Next-Gen Energy | SMRs, uranium miners, grid-scale power |
| Cybersecurity | Zero-trust, SIEM, endpoint, cloud security |
| Space / Satellite | Launch, LEO comms, Earth observation |
| Biotech / Life Sciences | Clinical-stage, FDA catalysts, genomics |
| Quantum / Emerging Tech | Quantum hardware, photonics, AI chips |
| AI Infrastructure / Fiber | Second-order AI buildout: optical interconnect, fiber and cabling, memory, networking (seeds: GLW, COHR, LITE, CIEN, AAOI, FN, CRDO, ALAB, ANET, MU, META) |

---

## Bull / Bear Analyst Framework

### Bull Analyst (Claude — Senior Equity Analyst)
Tasked with answering one question: **Does this stock have a credible path to 50%+ in 12 months?**

Report sections:
- **The 50% Path** — specific re-rating mechanism, not gradual growth
- **Catalysts & Timeline** — concrete events with dates and estimated price impact
- **Trade Setup** — entry, price target, stop loss, position sizing
- **Financial Highlights** — revenue growth, P/E, margins, debt/equity, momentum
- **What Has to Go Right** — 2–3 must-happen conditions
- **What Kills the Thesis** — specific invalidation triggers

### Bear Analyst (Claude — Skeptical Risk Analyst)
Stress-tests the bull case point by point. Not a perma-bear — rigorous and specific.

Report sections:
- **Is the 50% Path Realistic?** — base rate of the cited mechanism actually occurring
- **What the Bull Got Wrong** — specific rebuttals, not generic risk factors
- **The Real Risks** — 2–3 scenarios that make this -30% instead of +50%
- **Verdict** — one of: BUY WITH CONVICTION / BUY BUT SIZE SMALL / WAIT / PASS

---

## Data Sources

| Source | Used For |
|--------|----------|
| Yahoo Finance (yfinance) | Prices, fundamentals, insider transactions, earnings calendar |
| Finviz Screener | Dynamic universe expansion by sector/industry |
| Finnhub | Company news |
| FRED (St. Louis Fed) | VIX, 10Y Treasury yield (macro regime) |
| SEC EDGAR | 13D/13G filings (5%+ ownership disclosures), 13F hedge fund holdings |
| Polymarket | Real-money prediction market sentiment by theme |
| Reddit | Retail attention signal (informational only, does not affect score) |

---

## Weekly Cadence (in this repo)

| When (UTC) | Job | Output |
|------------|-----|--------|
| Monday 12:15 | `analyst-mismatch.yml` → `scripts/analyst_mismatch.py` | `data/analyst_mismatch.json`, shown on the Analyst Mismatch tab |
| Tuesday 12:30 | `weekly-brief.yml` → `scripts/weekly_brief.py` | `reports/weekly/<date>.html` (+ `latest.html`), emailed when the `MAIL_USERNAME`, `MAIL_PASSWORD` and `MAIL_TO` secrets are set |
| Every 30 min, market hours | `refresh-prices.yml` | current prices in `data/picks.json` |
| Weekdays 21:45 | `portfolio-sim.yml` → `scripts/portfolio_sim.py` | `data/portfolio.json`: hold vs -5% stop vs -10% stop vs v2 exits, replayed on daily closes (the Stop Rules tab) |

The brief's candidates are **new names** (not picked in the last 180 days) where **at least one analyst sees a 50%+ path** from today's price, ranked by how far they break from the Street. There is no cap on upside. Extra tickers to scan live in `data/watchlist.json`.

The full proposed rule set for the pick pipeline (one pick a week, 50%-in-6-months gate, novelty, exits) is in [`docs/selection-rules.md`](docs/selection-rules.md).

---

## For Agents

Everything on the site is derived from small JSON files, and the pages render them with JavaScript, so an agent should read the data, not the pages:

- **Start at [`llms.txt`](https://edwardphill.github.io/stockpicker/llms.txt)**: what the site is, key numbers, every data file with its schema and freshness.
- [`data/summary.json`](https://edwardphill.github.io/stockpicker/data/summary.json) has the computed stats (win rates, averages, top and bottom stocks, this week's candidates, stop-rule results).
- `data/picks.json`, `data/analyst_mismatch.json`, `data/portfolio.json` and `data/cases.json` are the sources; each has a JSON Schema in `data/schema/` and a markdown mirror next to it (`data/picks.md` etc.).
- `data/index.json` is the manifest; `sitemap.xml` and `robots.txt` point at all of it.
- [`AGENTS.md`](AGENTS.md) explains the repo layout for coding agents.
- **Counting agent visits:** GitHub Pages has no logs and agents run no JavaScript, so [`tracker/`](tracker/) holds a Cloudflare Worker that serves the same files through a logged proxy (one command to deploy, free tier). Once the `AGENT_BASE` variable points at it, the agent-facing links above route through it, and `scripts/agent_visits.py` pulls the counts into `data/agent_visits.json`.

Design: one entry point, plain formats (JSON, Markdown, static HTML for the brief), explicit units and conventions, stated freshness, a summary file so nothing has to be recomputed, and stable paths. The derived files are rebuilt by `scripts/build_agent_views.py` at the end of every workflow.

---

## Performance Tracking

Every pick is logged with:
- Entry price, analyst target, implied upside at entry
- Market cap, VIX, 10Y yield, risk regime at time of pick
- All signals that fired
- Current price and % gain/loss (updated each script run)

The live tracker is at: **https://edwardphill.github.io/stockpicker/**

---

## Disclaimer

This is a personal research tool. Not financial advice. All picks are generated algorithmically and reviewed by AI — not a licensed financial advisor. Do your own due diligence before making any investment decisions.
